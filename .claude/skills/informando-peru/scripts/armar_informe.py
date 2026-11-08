"""Arma el informe final desde un borrador con marcadores: ninguna cifra se escribe a mano.

    uv run .claude/skills/informando-peru/scripts/armar_informe.py [--borrador B] [--salida S] [--permitir-faltantes]

Marcadores que reemplaza:
    {{enaho.pobreza_nacional}}            el valor de salidas/indicadores.csv (año 2024 por defecto)
    {{enaho.pobreza_nacional:2020}}       el valor de salidas/indicadores.csv para el año especificado
    {{enaho.residentes_habituales|0}}     con 0 decimales (los enteros llevan separador de miles)
    {{bcrp.resumen(codigo=PN01273PM, desde=2024-01, hasta=2024-12).ultimo.valor|2}}
    {{sbs.indicadores(...).campo[0].otro}} cualquier herramienta de un servidor de .mcp.json, y un campo de su respuesta
    {{lit:0.1 puntos}}                    una constante metodológica escrita a mano, declarada como tal

Cada valor sale de llamar de nuevo a la herramienta (el servidor del BCRP corre en proceso, el resto como los lanza
Claude Code desde .mcp.json). El script falla si queda un marcador sin resolver, si una figura citada no existe o si
la narrativa trae una cifra suelta: porcentajes, decimales o números de 3 o más dígitos que no son años.
"""
import argparse
import asyncio
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from fastmcp import Client

RAIZ = Path(__file__).resolve().parents[4]
INDICADORES = RAIZ / "salidas" / "indicadores.csv"
MARCADOR = re.compile(r"\{\{\s*(.+?)\s*\}\}")
LLAMADA = re.compile(r"^(\w+)\.(\w+)\((.*)\)((?:\.\w+|\[-?\d+\])*)$")
CIFRA_SUELTA = re.compile(
    r"\d+(?:[.,]\d+)?\s*%"                       # porcentajes
    r"|(?<![\w/.-])\d+[.,]\d+(?![\w/-])"         # decimales
    r"|(?<![\w/.-])\d{1,3}(?:,\d{3})+(?![\w/-])"  # miles con separador
    r"|(?<![\w/.,-])(?!(?:19|20)\d\d\b)\d{3,}(?![\w/.,-])")  # 3 o más dígitos que no son un año
REFERENCIAS_APA7 = {
    "bcrp": (
        "Banco Central de Reserva del Perú. (2025). *Estadísticas económicas: Series de inflación y actividad económica* "
        "[Servicio web de datos / API]. https://estadisticas.bcrp.gob.pe/estadisticas/series/api/"
    ),
    "enaho": (
        "Instituto Nacional de Estadística e Informática. (2025a). *Encuesta Nacional de Hogares sobre Condiciones de Vida "
        "y Pobreza 2024* [Microdatos, módulos 34 y 02]. https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/"
    ),
    "inei_pobreza": (
        "Instituto Nacional de Estadística e Informática. (2025b). *Perú: Evolución de la Pobreza Monetaria 2015-2024. "
        "Informe técnico*. Lima: INEI. "
        "https://cdn.www.gob.pe/uploads/document/file/8058556/6763186-peru-evolucion-de-la-pobreza-monetaria-2015-2024.pdf"
    ),
    "sbs": (
        "Superintendencia de Banca, Seguros y AFP. (2024). *Boletín Estadístico de Banca Múltiple y Cajas Municipales "
        "(Diciembre 2024)* [Boletines B-2401, C-1301 y B-2332]. https://intranet2.sbs.gob.pe/estadistica/financiera/"
    ),
}


def formatear(valor, decimales):
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        return str(valor)
    if decimales is None:
        decimales = 0 if float(valor).is_integer() and abs(valor) >= 100 else 1
    return f"{valor:,.{decimales}f}"


def separar_decimales(texto):
    """'expr|2' → ('expr', 2). Sin barra, None: lo decide formatear."""
    expr, _, dec = texto.rpartition("|") if re.search(r"\|\d+$", texto) else (texto, "", "")
    return expr.strip(), int(dec) if dec else None


def campo(dato, ruta):
    for nombre, indice in re.findall(r"\.(\w+)|\[(-?\d+)\]", ruta):
        dato = dato[int(indice)] if indice else dato[nombre]
    return dato


def argumentos(texto):
    """'codigo=PN01273PM, desde=2024-01' → {'codigo': 'PN01273PM', 'desde': '2024-01'} (los tipos los fija el esquema)."""
    pares = [p for p in re.split(r",(?![^\[]*\])", texto) if p.strip()]
    return {k.strip(): v.strip().strip("'\"") for k, v in (p.split("=", 1) for p in pares)}


def tipar(args, esquema):
    tipos = {k: v.get("type") for k, v in esquema.get("properties", {}).items()}
    conversores = {"integer": int, "number": float, "boolean": lambda v: v.lower() in ("true", "1", "si", "sí")}
    return {k: conversores[tipos[k]](v) if tipos.get(k) in conversores else v for k, v in args.items()}


def cliente(servidor):
    """El del BCRP en proceso, con el mismo código que sirve el MCP; los demás, como los lanza Claude Code."""
    if servidor == "bcrp":
        sys.path.insert(0, str(RAIZ / "mcp"))
        from server import mcp
        return Client(mcp)
    config = json.loads((RAIZ / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]
    if servidor not in config:
        raise KeyError(f"el servidor {servidor!r} no está en .mcp.json")
    return Client({"mcpServers": {servidor: config[servidor]}})


async def llamar_todo(llamadas):
    """{(servidor, herramienta, args_json): resultado o excepción}, con una conexión por servidor."""
    resultados = {}
    for servidor in sorted({s for s, _, _ in llamadas}):
        try:
            async with cliente(servidor) as c:
                esquemas = {t.name: t.input_schema for t in await c.list_tools()}
                for clave in [k for k in llamadas if k[0] == servidor]:
                    _, herramienta, args_json = clave
                    try:
                        args = tipar(json.loads(args_json), esquemas.get(herramienta, {}))
                        resultados[clave] = (await c.call_tool(herramienta, args)).data
                    except Exception as e:  # el error se informa en el marcador, no se oculta
                        resultados[clave] = e
        except Exception as e:
            resultados |= {k: e for k in llamadas if k[0] == servidor}
    return resultados


def fuente_de(resultado, servidor):
    if isinstance(resultado, dict):
        for clave in ("fuente", "url", "fuentes"):
            if resultado.get(clave):
                valor = resultado[clave]
                return ", ".join(valor) if isinstance(valor, list) else str(valor)
    return f"servidor MCP {servidor}"


def resolver(borrador, permitir_faltantes):
    indicadores = pd.read_csv(INDICADORES) if INDICADORES.is_file() else None
    marcadores = [(m.group(0), *separar_decimales(m.group(1))) for m in MARCADOR.finditer(borrador)]
    llamadas = {}
    for _, expr, _ in marcadores:
        if (m := LLAMADA.match(expr)) and m.group(1) != "enaho":
            llamadas[(m.group(1), m.group(2), json.dumps(argumentos(m.group(3)), sort_keys=True))] = None
    resultados = asyncio.run(llamar_todo(llamadas)) if llamadas else {}

    reemplazos, traza, faltantes, constantes = {}, [], [], []
    for texto, expr, decimales in marcadores:
        if texto in reemplazos:
            continue
        try:
            if expr.startswith("lit:"):
                reemplazos[texto] = expr[4:].strip()
                constantes.append(expr[4:].strip())
                continue
            if expr.startswith("enaho.") or expr.startswith("enaho:"):
                if indicadores is None:
                    raise FileNotFoundError("falta salidas/indicadores.csv: corre la skill limpiando-enaho")
                resto = expr.removeprefix("enaho.").removeprefix("enaho:")
                if ":" in resto:
                    id_ind, anio_str = resto.split(":", 1)
                    anio_sel = int(anio_str.strip())
                else:
                    id_ind, anio_sel = resto, 2024

                if "anio" in indicadores.columns:
                    sub_ind = indicadores[(indicadores["anio"] == anio_sel) & (indicadores["id"] == id_ind)]
                    if sub_ind.empty:
                        raise KeyError(f"no se encontró el id {id_ind!r} para el año {anio_sel} en indicadores.csv")
                    fila = sub_ind.iloc[0]
                else:
                    fila = indicadores.set_index("id").loc[id_ind]

                valor = formatear(float(fila["valor"]), decimales)
                origen = f"`{expr}`: {fila['indicador']}, {fila['grupo']} ({fila['unidad']})"
                fuente = f"salidas/indicadores.csv; ponderador {fila['ponderador']}; n = {int(fila['n_muestral']):,}"
            elif m := LLAMADA.match(expr):
                servidor, herramienta, args, ruta = m.groups()
                resultado = resultados[(servidor, herramienta, json.dumps(argumentos(args), sort_keys=True))]
                if isinstance(resultado, Exception):
                    raise resultado
                valor = formatear(campo(resultado, ruta), decimales)
                origen, fuente = f"`{expr}`", fuente_de(resultado, servidor)
            else:
                raise ValueError("marcador no reconocido")
        except Exception as e:
            motivo = f"{type(e).__name__}: {e}".splitlines()[0][:200]
            faltantes.append((expr, motivo))
            reemplazos[texto] = f"[sin dato: {motivo}]" if permitir_faltantes else texto
            continue
        reemplazos[texto] = valor
        traza.append((valor, origen, fuente))
    return reemplazos, traza, faltantes, constantes


def cifras_sueltas(borrador):
    """Cifras escritas a mano en la narrativa: fuera de marcadores, código, enlaces y comentarios."""
    limpio = re.sub(r"```.*?```|`[^`]*`|<!--.*?-->|\]\([^)]*\)|https?://\S+", " ", borrador, flags=re.S)
    limpio = MARCADOR.sub(" ", limpio)
    sueltas = []
    for n, linea in enumerate(limpio.splitlines(), 1):
        sueltas += [(n, m.group(0).strip()) for m in CIFRA_SUELTA.finditer(linea)]
    return sueltas


def figuras_faltantes(borrador, carpeta):
    return [ruta for ruta in re.findall(r"!\[[^\]]*\]\(([^)\s]+)\)", borrador) if not (carpeta / ruta).is_file()]


def commit_actual():
    r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=RAIZ)
    return r.stdout.strip() or "sin commit"


def anexos(traza, faltantes, constantes, borrador_rel):
    lineas = ["", "## Trazabilidad de las cifras", "",
              f"Cada cifra del informe se generó con `armar_informe.py` desde `{borrador_rel}` el "
              f"{datetime.now():%Y-%m-%d %H:%M}, sobre el commit `{commit_actual()}`. Ninguna se escribió a mano.", "",
              "| # | Cifra | Origen | Fuente |", "|---|---|---|---|"]
    lineas += [f"| {i} | {v} | {o} | {f} |" for i, (v, o, f) in enumerate(traza, 1)]
    if constantes:
        lineas += ["", "Constantes metodológicas escritas a mano: " + "; ".join(f"«{c}»" for c in constantes) + "."]
    if faltantes:
        lineas += ["", "### Datos no disponibles", "", "Estas cifras no se pudieron obtener y no se estimaron:", ""]
        lineas += [f"- `{e}`: {m}" for e, m in faltantes]
    # Construir referencias bibliográficas en formato APA 7ma edición
    usadas = set()
    for _, origen, fuente in traza:
        origen_l = origen.lower()
        fuente_l = fuente.lower()
        if "enaho" in origen_l or "indicadores.csv" in fuente_l:
            usadas.add("enaho")
            usadas.add("inei_pobreza")
        if "bcrp" in origen_l or "bcrp" in fuente_l:
            usadas.add("bcrp")
        if "sbs" in origen_l or "sbs" in fuente_l:
            usadas.add("sbs")

    citas_apa = [REFERENCIAS_APA7[k] for k in sorted(usadas) if k in REFERENCIAS_APA7]
    if not citas_apa:
        citas_apa = [REFERENCIAS_APA7["enaho"], REFERENCIAS_APA7["inei_pobreza"]]

    lineas += ["", "## Referencias", "", "### Fuentes oficiales consultadas (norma APA 7ma edición)", ""]
    lineas += [f"- {cita}" for cita in citas_apa]
    lineas += [
        "",
        "### Trazabilidad y procesamiento de código",
        "",
        "- Procesamiento de microdatos: `.claude/skills/limpiando-enaho/scripts/limpiar.py` → `salidas/indicadores.csv`, "
        "`salidas/validacion.txt`.",
        "- Servidor MCP del BCRP: `mcp/server.py`; servidores SBS y Fetch en `.mcp.json`.",
    ]
    return "\n".join(lineas) + "\n"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--borrador", type=Path, default=RAIZ / "informes" / "borrador.md")
    parser.add_argument("--salida", type=Path, default=RAIZ / "informes" / "informe_final.md")
    parser.add_argument("--permitir-faltantes", action="store_true",
                        help="Escribe el informe aunque falten datos, marcándolos y listándolos como no disponibles.")
    args = parser.parse_args()
    if not args.borrador.is_file():
        sys.exit(f"No existe el borrador {args.borrador}. Escríbelo con la plantilla de la skill informando-peru.")
    borrador = args.borrador.read_text(encoding="utf-8")

    errores = [f"línea {n}: cifra escrita a mano «{c}»; reemplázala por un marcador" for n, c in cifras_sueltas(borrador)]
    errores += [f"figura citada que no existe: {f}" for f in figuras_faltantes(borrador, args.salida.parent)]
    reemplazos, traza, faltantes, constantes = resolver(borrador, args.permitir_faltantes)
    if not args.permitir_faltantes:
        errores += [f"marcador sin resolver {{{{{e}}}}}: {m}" for e, m in faltantes]
    if errores:
        sys.exit("No se escribió el informe:\n- " + "\n- ".join(errores))

    texto = MARCADOR.sub(lambda m: reemplazos[m.group(0)], borrador)
    try:
        borrador_rel = args.borrador.resolve().relative_to(RAIZ).as_posix()
    except ValueError:
        borrador_rel = args.borrador.name
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(texto.rstrip() + "\n" + anexos(traza, faltantes, constantes, borrador_rel), encoding="utf-8")
    aviso = f"; {len(faltantes)} sin dato" if faltantes else ""
    print(f"{args.salida.name}: {len(traza)} cifras resueltas y trazadas{aviso}.")


if __name__ == "__main__":
    main()
