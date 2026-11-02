"""Contrasta los resultados de distintas herramientas entre sí y escribe salidas/consistencia.md.

    uv run .claude/skills/verificando-consistencia/scripts/verificar.py [--anio-bcrp 2024]

Resultados posibles: OK (coinciden dentro de la tolerancia), DIFERENCIA (no coinciden, por una razón conocida que se
explica), FALLA (no coinciden y no debería pasar) y NO VERIFICABLE (la fuente no respondió). Sale con error solo si
hay alguna FALLA.
"""
import argparse
import asyncio
import re
import sys
from pathlib import Path

import pandas as pd
from fastmcp import Client

RAIZ = Path(__file__).resolve().parents[4]
SALIDAS = RAIZ / "salidas"
INFORME = RAIZ / "informes" / "informe_final.md"
BORRADOR = RAIZ / "informes" / "borrador.md"
ARMAR = RAIZ / ".claude" / "skills" / "informando-peru" / "scripts" / "armar_informe.py"
IPC_INDICE, IPC_12_MESES = "PN01270PM", "PN01273PM"  # IPC de Lima Metropolitana: índice y variación a 12 meses
TOLERANCIA_ENAHO = 0.1      # puntos porcentuales, la del enunciado
TOLERANCIA_RECALCULO = 0.05  # puntos: el índice se publica con 2 decimales y la variación sale del índice sin redondear


class Registro:
    def __init__(self):
        self.filas = []

    def agregar(self, fuente, verificacion, resultado, detalle, explicacion=""):
        self.filas.append({"fuente": fuente, "verificacion": verificacion, "resultado": resultado,
                           "detalle": detalle, "explicacion": explicacion})

    def comparar(self, fuente, verificacion, a, b, tolerancia, si_difiere="FALLA", explicacion=""):
        diferencia = abs(a - b)
        resultado = "OK" if diferencia <= tolerancia else si_difiere
        detalle = f"{a:.2f} frente a {b:.2f} (diferencia {diferencia:.2f}; tolerancia {tolerancia})"
        self.agregar(fuente, verificacion, resultado, detalle, explicacion if resultado != "OK" else "")


def verificar_enaho(reg):
    indicadores = SALIDAS / "indicadores.csv"
    if not indicadores.is_file():
        reg.agregar("ENAHO", "Indicadores procesados", "NO VERIFICABLE", "falta salidas/indicadores.csv",
                    "Corre la skill limpiando-enaho.")
        return
    t = pd.read_csv(indicadores).set_index("id")["valor"]
    reg.comparar("ENAHO", "Pobreza nacional: peso de hogar frente a peso de persona", t["pobreza_nacional"],
                 t["pobreza_nacional_personas"], TOLERANCIA_ENAHO, "DIFERENCIA",
                 "Dos ponderadores distintos: factor07 × mieperho reproduce la cifra oficial del INEI.")
    validacion = (SALIDAS / "validacion.txt").read_text(encoding="utf-8") if (SALIDAS / "validacion.txt").is_file() else ""
    fallas = [l for l in validacion.splitlines() if l.startswith("FALLA")]
    reg.agregar("ENAHO", "Validaciones de limpiando-enaho", "FALLA" if fallas or not validacion else "OK",
                f"{validacion.count(chr(10) + 'OK')} comprobaciones OK, {len(fallas)} fallas" if validacion
                else "falta salidas/validacion.txt")
    urbana, rural, nacional = t["pobreza_area_urbana"], t["pobreza_area_rural"], t["pobreza_nacional"]
    reg.agregar("ENAHO", "La tasa nacional queda entre la urbana y la rural",
                "OK" if min(urbana, rural) <= nacional <= max(urbana, rural) else "FALLA",
                f"urbana {urbana:.2f}, nacional {nacional:.2f}, rural {rural:.2f}")

    departamentos = t[t.index.str.startswith("pobreza_dep_")].rename(lambda i: i[-2:])
    referencia = pd.read_csv(RAIZ / "referencias" / "pobreza_departamento_2024.csv",
                             dtype={"ccdd": str}).set_index("ccdd")["pobreza_pct"]
    alejados = (departamentos - referencia).abs().loc[lambda d: d > TOLERANCIA_ENAHO]
    reg.agregar("ENAHO", "Departamentos de limpiando-enaho frente a la referencia de la sesión 16",
                "OK" if alejados.empty and len(departamentos) == 25 else "FALLA",
                f"{len(departamentos)} departamentos; {len(alejados)} fuera de ±{TOLERANCIA_ENAHO}")
    mapa = SALIDAS / "mapa_vs_referencia.csv"
    if mapa.is_file():
        delmapa = pd.read_csv(mapa, dtype={"ccdd": str}).set_index("ccdd")["pobreza_pct"]
        distintos = (delmapa - departamentos.round(2)).abs().loc[lambda d: d > 0.005]
        reg.agregar("ENAHO", "Mapa (mapeando-enaho) frente a indicadores (limpiando-enaho)",
                    "OK" if distintos.empty and len(delmapa) == 25 else "FALLA",
                    f"{len(delmapa)} unidades en el mapa; {len(distintos)} con cifra distinta")
    else:
        reg.agregar("ENAHO", "Mapa frente a indicadores", "NO VERIFICABLE", "falta salidas/mapa_vs_referencia.csv",
                    "Corre la skill mapeando-enaho.")


async def _bcrp(llamadas):
    sys.path.insert(0, str(RAIZ / "mcp"))
    from server import mcp
    async with Client(mcp) as c:
        return [(await c.call_tool(h, a)).data for h, a in llamadas]


def verificar_bcrp(reg, anio):
    desde, hasta = f"{anio}-01", f"{anio}-12"
    try:
        indice, publicada, serie, resumen = asyncio.run(_bcrp([
            ("serie", {"codigo": IPC_INDICE, "desde": f"{anio - 1}-01", "hasta": hasta}),
            ("serie", {"codigo": IPC_12_MESES, "desde": desde, "hasta": hasta}),
            ("serie", {"codigo": IPC_12_MESES, "desde": desde, "hasta": hasta}),
            ("resumen", {"codigo": IPC_12_MESES, "desde": desde, "hasta": hasta})]))
    except Exception as e:
        motivo = str(e).splitlines()[0][:200]
        for v in ("Inflación a 12 meses recalculada desde el índice", "resumen frente a serie"):
            reg.agregar("BCRP", v, "NO VERIFICABLE", motivo, "El BCRP no respondió: no se estima nada en su lugar.")
        return
    if "índice" not in indice["nombre"].lower() and "indice" not in indice["nombre"].lower():
        reg.agregar("BCRP", "Inflación a 12 meses recalculada desde el índice", "NO VERIFICABLE",
                    f"{IPC_INDICE} no es un índice: «{indice['nombre']}»", "Revisa el código con buscar_series.")
    else:
        i = pd.Series({d["periodo"]: d["valor"] for d in indice["datos"]})
        recalculada = (i / i.shift(12) - 1).mul(100).dropna()
        p = pd.Series({d["periodo"]: d["valor"] for d in publicada["datos"]})
        comunes = recalculada.index.intersection(p.index)
        diferencia = (recalculada[comunes] - p[comunes]).abs()
        peor = diferencia.idxmax() if len(diferencia) else None
        reg.agregar("BCRP", f"Inflación a 12 meses: recalculada desde {IPC_INDICE} frente a la publicada en {IPC_12_MESES}",
                    "OK" if len(comunes) and diferencia.max() <= TOLERANCIA_RECALCULO else
                    ("NO VERIFICABLE" if not len(comunes) else "DIFERENCIA"),
                    f"{len(comunes)} meses de {anio}; diferencia máxima {diferencia.max():.3f} puntos en {peor}"
                    if len(comunes) else "sin meses en común",
                    "El índice se publica redondeado; una diferencia mayor indicaría revisión de datos o un error de "
                    "alineación de periodos.")
    valores = pd.Series({d["periodo"]: d["valor"] for d in serie["datos"]})
    checks = {"promedio": (resumen["promedio"], valores.mean()), "máximo": (resumen["maximo"]["valor"], valores.max()),
              "mínimo": (resumen["minimo"]["valor"], valores.min()),
              "cambio": (resumen["cambio"], valores.iloc[-1] - valores.iloc[0])}
    distintos = {k: v for k, v in checks.items() if abs(v[0] - v[1]) > 1e-6}
    reg.agregar("BCRP", f"resumen frente a serie ({IPC_12_MESES}, {anio})", "OK" if not distintos else "FALLA",
                "promedio, máximo, mínimo y cambio coinciden" if not distintos else f"distintos: {distintos}")


def verificar_informe(reg):
    if not (INFORME.is_file() and BORRADOR.is_file()):
        reg.agregar("Informe", "Cifras del informe frente a sus fuentes", "NO VERIFICABLE",
                    "falta informes/borrador.md o informes/informe_final.md", "Usa la skill informando-peru.")
        return
    import importlib.util
    spec = importlib.util.spec_from_file_location("armar_informe", ARMAR)
    armar = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(armar)
    _, traza, faltantes, _ = armar.resolver(BORRADOR.read_text(encoding="utf-8"), True)
    informe = INFORME.read_text(encoding="utf-8")
    publicadas = re.findall(r"^\| \d+ \| (.+?) \| (.+?) \|", informe, flags=re.M)
    actuales = [(v, o) for v, o, _ in traza]
    distintas = [(o, p, a) for (p, o), (a, _) in zip(publicadas, actuales) if p != a]
    resultado = "OK" if not distintas and len(publicadas) == len(actuales) and not faltantes else (
        "NO VERIFICABLE" if faltantes else "DIFERENCIA")
    reg.agregar("Informe", "Cifras del informe frente a una nueva consulta a las herramientas", resultado,
                f"{len(actuales)} cifras resueltas de nuevo; {len(distintas)} distintas; {len(faltantes)} sin dato",
                "Si difieren, la fuente revisó sus datos o la caché quedó vieja: vuelve a armar el informe."
                if distintas else ("Hay fuentes que no respondieron." if faltantes else ""))


def escribir(reg):
    tabla = pd.DataFrame(reg.filas)
    conteo = tabla["resultado"].value_counts().to_dict()
    lineas = ["# Consistencia entre herramientas", "",
              "Generado por `verificando-consistencia/scripts/verificar.py`. " +
              ", ".join(f"{k}: {v}" for k, v in sorted(conteo.items())) + ".", "",
              "| Fuente | Verificación | Resultado | Detalle | Explicación |", "|---|---|---|---|---|"]
    lineas += [f"| {f.fuente} | {f.verificacion} | **{f.resultado}** | {f.detalle} | {f.explicacion} |"
               for f in tabla.itertuples()]
    SALIDAS.mkdir(exist_ok=True)
    (SALIDAS / "consistencia.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return conteo


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--anio-bcrp", type=int, default=2024, help="Año de las series del BCRP que se contrastan.")
    parser.add_argument("--sin-bcrp", action="store_true", help="Omite las verificaciones que consultan al BCRP.")
    args = parser.parse_args()
    reg = Registro()
    verificar_enaho(reg)
    if not args.sin_bcrp:
        verificar_bcrp(reg, args.anio_bcrp)
    verificar_informe(reg)
    conteo = escribir(reg)
    print("salidas/consistencia.md: " + ", ".join(f"{k} {v}" for k, v in sorted(conteo.items())))
    if conteo.get("FALLA"):
        sys.exit(f"{conteo['FALLA']} verificaciones fallaron. Revisa salidas/consistencia.md.")


if __name__ == "__main__":
    main()
