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

Al final agrega la tabla de trazabilidad (la URL exacta de cada consulta) y las referencias en APA 7, armadas con los
metadatos de cada respuesta (referencias_apa.py): una entrada por serie del BCRP, por boletín y periodo de la SBS, por
año y módulo de la ENAHO, el informe técnico del INEI si se usa la ENAHO y los límites del IGN si se incluye un mapa
de mapas/. El sello indica el commit y advierte si hay cambios sin commitear que alimentan el informe.
"""
import argparse
import asyncio
import json
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd
from fastmcp import Client

sys.path.insert(0, str(Path(__file__).resolve().parent))
import referencias_apa  # noqa: E402

RAIZ = Path(__file__).resolve().parents[4]
INDICADORES = RAIZ / "salidas" / "indicadores.csv"
DATOS = RAIZ / "datos"  # los zip descargados: su fecha de modificación es la fecha en que se recuperaron
DESCARGAR_ENAHO = RAIZ / ".claude" / "skills" / "descargando-enaho" / "scripts" / "descargar.py"
ZIP_LIMITES_IGN = "per_admin_boundaries.geojson.zip"  # el que baja scripts/preparar_limites.py a datos/
MARCADOR = re.compile(r"\{\{\s*(.+?)\s*\}\}")
LLAMADA = re.compile(r"^(\w+)\.(\w+)\((.*)\)((?:\.\w+|\[-?\d+\])*)$")
CIFRA_SUELTA = re.compile(
    r"\d+(?:[.,]\d+)?\s*%"                       # porcentajes
    r"|(?<![\w/.-])\d+[.,]\d+(?![\w/-])"         # decimales
    r"|(?<![\w/.-])\d{1,3}(?:,\d{3})+(?![\w/-])"  # miles con separador
    r"|(?<![\w/.,-])(?!(?:19|20)\d\d\b)\d{3,}(?![\w/.,-])")  # 3 o más dígitos que no son un año


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


COPIA_GUARDADA = re.compile(r"copia guardada el (\d{4}-\d{2}-\d{2})")
MODULOS = re.compile(r"m[oó]dulos?\s+(\d+(?:\s*(?:,|y)\s*\d+)*)", re.I)


def registrar_fuentes(fuentes, servidor, herramienta, resultado, hoy):
    """Guarda en `fuentes` los metadatos de una respuesta para citarla, con una clave por identidad de la fuente:
    ("bcrp", código), ("sbs", boletín, periodo). Lo que no trae metadatos queda anotado para avisarlo."""
    if servidor == "bcrp" and isinstance(resultado, dict):
        aviso = COPIA_GUARDADA.search(str(resultado.get("aviso", "")))
        recuperado = date.fromisoformat(aviso.group(1)) if aviso else hoy  # copia vieja: se cita su fecha
        series = resultado.get("series") if isinstance(resultado.get("series"), list) else [resultado]
        for s in series:
            if isinstance(s, dict) and s.get("codigo") and s.get("nombre"):
                previa = fuentes.get(("bcrp", s["codigo"]), {}).get("recuperado", recuperado)
                fuentes[("bcrp", s["codigo"])] = {"tipo": "bcrp", "codigo": s["codigo"], "nombre": s["nombre"],
                                                  "frecuencia": s.get("frecuencia") or resultado.get("frecuencia"),
                                                  "recuperado": min(previa, recuperado)}
                continue
            fuentes[("sin_metadatos", servidor, herramienta)] = {"tipo": "sin_metadatos", "origen": f"{servidor}.{herramienta}"}
        return
    if servidor == "sbs" and isinstance(resultado, dict) and all(resultado.get(k) for k in ("codigo", "titulo", "periodo", "fuente")):
        clave = ("sbs", resultado["codigo"], resultado["periodo"])
        fuentes[clave] = {"tipo": "sbs", "recuperado": hoy, **{k: resultado[k] for k in ("codigo", "titulo", "periodo", "fuente")}}
        return
    fuentes[("sin_metadatos", servidor, herramienta)] = {"tipo": "sin_metadatos", "origen": f"{servidor}.{herramienta}"}


def registrar_enaho(fuentes, fila, expr):
    """Un indicador de la ENAHO cita los módulos y el año que declara su columna `fuente` en indicadores.csv."""
    texto = str(fila.get("fuente", ""))
    anio = int(fila["anio"]) if "anio" in fila.index else (int(m.group(1)) if (m := re.search(r"ENAHO (\d{4})", texto)) else None)
    modulos = re.findall(r"\d+", m.group(1)) if (m := MODULOS.search(texto)) else []
    if anio is None or not modulos:
        fuentes[("sin_metadatos", "enaho", expr)] = {"tipo": "sin_metadatos", "origen": f"enaho.{expr}"}
    for modulo in modulos:
        fuentes[("enaho", anio, f"{int(modulo):02d}")] = {"tipo": "enaho", "anio": anio, "modulo": f"{int(modulo):02d}"}


def resolver(borrador, permitir_faltantes):
    """(reemplazos, traza, faltantes, constantes): traza son tuplas (cifra, origen, fuente)."""
    return resolver_con_fuentes(borrador, permitir_faltantes)[:4]


def resolver_con_fuentes(borrador, permitir_faltantes, hoy=None):
    """Como resolver, más los metadatos de cada fuente consultada para armar las referencias. `hoy` es la fecha de
    recuperación de lo que se consulta en esta corrida."""
    hoy = hoy or date.today()
    fuentes = {}
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
                registrar_enaho(fuentes, fila, expr)
            elif m := LLAMADA.match(expr):
                servidor, herramienta, args, ruta = m.groups()
                resultado = resultados[(servidor, herramienta, json.dumps(argumentos(args), sort_keys=True))]
                if isinstance(resultado, Exception):
                    raise resultado
                valor = formatear(campo(resultado, ruta), decimales)
                origen, fuente = f"`{expr}`", fuente_de(resultado, servidor)
                registrar_fuentes(fuentes, servidor, herramienta, resultado, hoy)
            else:
                raise ValueError("marcador no reconocido")
        except Exception as e:
            motivo = f"{type(e).__name__}: {e}".splitlines()[0][:200]
            faltantes.append((expr, motivo))
            reemplazos[texto] = f"[sin dato: {motivo}]" if permitir_faltantes else texto
            continue
        reemplazos[texto] = valor
        traza.append((valor, origen, fuente))
    return reemplazos, traza, faltantes, constantes, fuentes


def cifras_sueltas(borrador):
    """Cifras escritas a mano en la narrativa: fuera de marcadores, código, enlaces y comentarios."""
    limpio = re.sub(r"```.*?```|`[^`]*`|<!--.*?-->|\]\([^)]*\)|https?://\S+", " ", borrador, flags=re.S)
    limpio = MARCADOR.sub(" ", limpio)
    sueltas = []
    for n, linea in enumerate(limpio.splitlines(), 1):
        sueltas += [(n, m.group(0).strip()) for m in CIFRA_SUELTA.finditer(linea)]
    return sueltas


def figuras_citadas(borrador):
    return re.findall(r"!\[[^\]]*\]\(([^)\s]+)\)", borrador)


def figuras_faltantes(borrador, carpeta):
    return [ruta for ruta in figuras_citadas(borrador) if not (carpeta / ruta).is_file()]


def fecha_de_archivo(ruta):
    """Fecha de modificación de un archivo descargado (la de su descarga), o None si no está."""
    return date.fromtimestamp(ruta.stat().st_mtime) if ruta.is_file() else None


def descarga_enaho():
    """Códigos de encuesta por año y URL base del INEI, los mismos que usa la skill descargando-enaho."""
    import importlib.util
    try:
        spec = importlib.util.spec_from_file_location("descargar_enaho", DESCARGAR_ENAHO)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return dict(modulo.CODIGOS_INEI), modulo.URL_INEI
    except (OSError, AttributeError, ImportError):
        return {}, None


def frecuencia_bcrp(codigo):
    """La frecuencia del catálogo del BCRP, para respuestas que no la traen (graficar_serie)."""
    sys.path.insert(0, str(RAIZ / "mcp"))
    from server import _ficha
    return _ficha(codigo)["frecuencia"]


def referencias(fuentes, figuras):
    """(entradas APA 7 ordenadas, avisos de fuentes sin metadatos suficientes para citarlas)."""
    refs, avisos = [], []
    codigos, url_inei = descarga_enaho() if any(f["tipo"] == "enaho" for f in fuentes.values()) else ({}, None)
    for f in fuentes.values():
        try:
            if f["tipo"] == "bcrp":
                frecuencia = f.get("frecuencia") or frecuencia_bcrp(f["codigo"])
                refs.append(referencias_apa.serie_bcrp(f["codigo"], f["nombre"], frecuencia, f["recuperado"]))
            elif f["tipo"] == "sbs":
                refs.append(referencias_apa.boletin_sbs(f["codigo"], f["titulo"], f["periodo"], f["fuente"],
                                                        f["recuperado"]))
            elif f["tipo"] == "enaho":
                if f["anio"] not in codigos or not url_inei:
                    raise KeyError(f"sin código de encuesta del INEI para la ENAHO {f['anio']}")
                archivo = f"{codigos[f['anio']]}-Modulo{f['modulo']}.zip"
                refs.append(referencias_apa.microdatos_enaho(f["anio"], codigos[f["anio"]], f["modulo"],
                                                             f"{url_inei}/{archivo}", fecha_de_archivo(DATOS / archivo)))
            else:
                avisos.append(f"`{f['origen']}`: su respuesta no trae metadatos para citarla.")
        except Exception as e:  # una fuente sin metadatos se avisa, no se completa de memoria
            avisos.append(f"`{f.get('codigo') or f.get('anio')}`: {type(e).__name__}: {e}".splitlines()[0][:200])
    if any(f["tipo"] == "enaho" for f in fuentes.values()):
        refs.append(referencias_apa.informe_pobreza_inei())  # de él salen las metas de validación de la ENAHO
    if any("mapas" in Path(ruta).parts for ruta in figuras):
        refs.append(referencias_apa.limites_ign(fecha_de_archivo(DATOS / ZIP_LIMITES_IGN)))
    return referencias_apa.lista_apa(refs), sorted(set(avisos))


def archivos_sin_commitear(raiz, borrador=None):
    """Archivos versionados con cambios sin commitear que alimentan el informe: todo menos informes/, salvo el
    borrador, que cuenta también si nunca se commiteó. None si git no pudo responder."""
    r = subprocess.run(["git", "status", "--porcelain=v1", "-z", "--untracked-files=no"], capture_output=True,
                       text=True, encoding="utf-8", cwd=raiz)
    if r.returncode != 0:
        return None
    rel = None
    if borrador is not None:
        try:
            rel = Path(borrador).resolve().relative_to(Path(raiz).resolve()).as_posix()
        except ValueError:
            rel = None  # un borrador fuera del repositorio no se puede reproducir desde un commit
    entradas, cambiados = r.stdout.split("\0"), []
    i = 0
    while i < len(entradas):
        entrada = entradas[i]
        i += 1
        if len(entrada) < 4:
            continue
        if entrada[0] in "RC":
            i += 1  # en un renombre, la ruta siguiente es la original
        ruta = entrada[3:]
        if not ruta.startswith("informes/") or ruta == rel:
            cambiados.append(ruta)
    if rel and Path(borrador).is_file() and subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", rel], capture_output=True, cwd=raiz).returncode != 0:
        cambiados.append(rel)
    return sorted(set(cambiados))


def sello_commit(raiz=RAIZ, borrador=None):
    """«el commit `abc1234`», y si hay cambios sin commitear que alimentan el informe, lo dice: ese commit solo no
    reproduce el informe."""
    r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=raiz)
    commit = r.stdout.strip() if r.returncode == 0 else ""
    if not commit:
        return "un árbol de trabajo sin commit identificable"
    cambiados = archivos_sin_commitear(raiz, borrador)
    if cambiados is None:
        return f"el commit `{commit}` (no se pudo comprobar si había cambios sin commitear)"
    if not cambiados:
        return f"el commit `{commit}`"
    n = len(cambiados)
    lista = ", ".join(f"`{c}`" for c in cambiados[:5]) + (f" y {n - 5} más" if n > 5 else "")
    return (f"el commit `{commit}`, con cambios sin commitear en {n} archivo{'s' if n != 1 else ''} ({lista}): "
            "ese commit por sí solo no reproduce el informe")


def anexos(traza, faltantes, constantes, borrador_rel, fuentes=None, figuras=(), sello=None):
    sello = sello or sello_commit()
    lineas = ["", "## Trazabilidad de las cifras", "",
              f"Cada cifra del informe se generó con `armar_informe.py` desde `{borrador_rel}` el "
              f"{datetime.now():%Y-%m-%d %H:%M}, sobre {sello}. Ninguna se escribió a mano.", "",
              "| # | Cifra | Origen | Fuente |", "|---|---|---|---|"]
    lineas += [f"| {i} | {v} | {o} | {f} |" for i, (v, o, f) in enumerate(traza, 1)]
    if constantes:
        lineas += ["", "Constantes metodológicas escritas a mano: " + "; ".join(f"«{c}»" for c in constantes) + "."]
    if faltantes:
        lineas += ["", "### Datos no disponibles", "", "Estas cifras no se pudieron obtener y no se estimaron:", ""]
        lineas += [f"- `{e}`: {m}" for e, m in faltantes]
    entradas, avisos = referencias(fuentes or {}, figuras)
    lineas += ["", "## Referencias", "",
               "Fuentes citadas, en formato APA 7. La URL exacta de cada consulta está en la tabla de trazabilidad.", ""]
    lineas += [f"- {e}" for e in entradas] or ["- No se citaron fuentes externas."]
    if avisos:
        lineas += ["", "Fuentes consultadas sin metadatos suficientes para una referencia completa:", ""]
        lineas += [f"- {a}" for a in avisos]
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
    reemplazos, traza, faltantes, constantes, fuentes = resolver_con_fuentes(borrador, args.permitir_faltantes)
    if not args.permitir_faltantes:
        errores += [f"marcador sin resolver {{{{{e}}}}}: {m}" for e, m in faltantes]
    if errores:
        sys.exit("No se escribió el informe:\n- " + "\n- ".join(errores))

    texto = MARCADOR.sub(lambda m: reemplazos[m.group(0)], borrador)
    try:
        borrador_rel = args.borrador.resolve().relative_to(RAIZ).as_posix()
    except ValueError:
        borrador_rel = args.borrador.name
    sello = sello_commit(RAIZ, args.borrador)  # antes de escribir: la salida no cuenta como cambio
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(texto.rstrip() + "\n" + anexos(traza, faltantes, constantes, borrador_rel, fuentes,
                                                         figuras_citadas(borrador), sello), encoding="utf-8")
    aviso = f"; {len(faltantes)} sin dato" if faltantes else ""
    print(f"{args.salida.name}: {len(traza)} cifras resueltas y trazadas{aviso}.")


if __name__ == "__main__":
    main()
