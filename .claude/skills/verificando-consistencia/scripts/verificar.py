"""Contrasta los resultados de distintas herramientas entre sí y escribe salidas/consistencia.md.

    uv run .claude/skills/verificando-consistencia/scripts/verificar.py [--anio-bcrp 2024]

Resultados posibles: OK (coinciden dentro de la tolerancia), DIFERENCIA (no coinciden, por una razón conocida que se
explica), FALLA (no coinciden y no debería pasar) y NO VERIFICABLE (la fuente no respondió o no tiene datos del
periodo). La morosidad bancaria se contrasta en diciembre de 2020 a 2024, entre el BCRP y la SBS.
Sale con error solo si hay alguna FALLA.
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
# IPC de Lima Metropolitana: índice vigente (Dic.2021 = 100) y variación a 12 meses. El índice base 2009, PN01270PM,
# quedó descontinuado en diciembre de 2021.
IPC_INDICE, IPC_12_MESES = "PN38705PM", "PN01273PM"
SERIE_MOROSIDAD_BCRP = "PN07746EM"
ANIOS_MOROSIDAD = tuple(range(2020, 2025))  # diciembre de cada año
REFERENCIA_INEI = RAIZ / "referencias" / "inei_pobreza_2024.csv"
# Los dos ámbitos de Lima que publica el INEI (Cuadro III.1, p. 220) y su id en indicadores.csv.
AMBITOS_LIMA = {"1501": "pobreza_lima_metropolitana_provincia", "15_resto": "pobreza_lima_provincias"}
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
    t = pd.read_csv(indicadores)
    if "anio" in t.columns:
        t = t[t["anio"] == 2024]
    t = t.set_index("id")["valor"]
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
    # El INEI no publica una cifra del departamento 15 en conjunto: en su lugar se comparan Lima Metropolitana
    # (provincia 1501) y Lima provincias, que sí publica. La consigna de 25 departamentos se exige igual.
    ref = (pd.read_csv(REFERENCIA_INEI, dtype={"ccdd": str}).dropna(subset=["ccdd"])
           .set_index("ccdd")["valor"].astype(float))
    publicadas = ref[ref.index.str.fullmatch(r"\d{2}") & (ref.index != "15")]
    objetivo = pd.concat([publicadas, ref.reindex(list(AMBITOS_LIMA))])
    lima = pd.Series({codigo: t.get(id_) for codigo, id_ in AMBITOS_LIMA.items()}, dtype=float)
    replicadas = pd.concat([departamentos.drop("15", errors="ignore"), lima])
    diferencias = (replicadas.reindex(objetivo.index) - objetivo).abs()
    sin_par = diferencias.index[diferencias.isna()].tolist()
    alejados = diferencias.dropna().loc[lambda d: d > TOLERANCIA_ENAHO]
    completo = len(departamentos) == 25 and len(publicadas) == 24 and not sin_par
    reg.agregar("ENAHO", "Departamentos de limpiando-enaho frente al informe técnico del INEI",
                "OK" if alejados.empty and completo else "FALLA",
                f"{len(departamentos)} departamentos en indicadores.csv (consigna: 25); comparados con el INEI: "
                f"{len(publicadas)} departamentos, Lima Metropolitana y Lima provincias; "
                f"{len(alejados)} fuera de ±{TOLERANCIA_ENAHO}" + (f"; sin par: {', '.join(sin_par)}" if sin_par else "")
                + ". Lima (15) sin cifra publicada por el INEI para el departamento en conjunto")
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
        es_cobertura = "no tiene datos" in motivo
        explicacion = ("La serie no cubre ese periodo; revisa el código con buscar_series." if es_cobertura
                       else "El BCRP no respondió con datos.") + " No se estima nada en su lugar."
        for v in ("Inflación a 12 meses recalculada desde el índice", "resumen frente a serie"):
            reg.agregar("BCRP", v, "NO VERIFICABLE", motivo, explicacion)
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


async def _consultar_morosidad(anios):
    """La serie mensual PN07746EM del BCRP y un boletín B-2401 de la SBS por cada diciembre pedido."""
    sys.path.insert(0, str(RAIZ / "mcp"))
    from server import mcp
    async with Client(mcp) as c_bcrp:
        bcrp = (await c_bcrp.call_tool("serie", {
            "codigo": SERIE_MOROSIDAD_BCRP, "desde": f"{min(anios)}-12", "hasta": f"{max(anios)}-12"})).data

    import json
    config = json.loads((RAIZ / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]
    sbs = {}
    async with Client({"mcpServers": {"sbs": config["sbs"]}}) as c_sbs:
        for anio in anios:
            sbs[anio] = (await c_sbs.call_tool("indicadores", {
                "tipo_entidad": "bancos", "indicador": "morosidad", "periodo": f"{anio}-12"})).data
    return bcrp, sbs


def _total_sbs(respuesta) -> float | None:
    """El total del sistema bancario en una respuesta de sbs.indicadores, o None si no viene."""
    if not isinstance(respuesta, dict):
        return None
    indicadores = respuesta.get("indicadores") or []
    total = indicadores[0].get("total") if indicadores else respuesta.get("total")
    return float(total["valor"]) if total and total.get("valor") is not None else None


def verificar_morosidad(reg, anios=ANIOS_MOROSIDAD):
    """Contrasta la morosidad bancaria de cada diciembre entre el BCRP (PN07746EM) y la SBS (B-2401)."""
    verificacion = (f"Morosidad bancaria en diciembre de {min(anios)} a {max(anios)}: BCRP ({SERIE_MOROSIDAD_BCRP}) "
                    "frente a SBS (B-2401)")
    try:
        bcrp, sbs = asyncio.run(_consultar_morosidad(anios))
    except Exception as e:
        reg.agregar("BCRP / SBS", verificacion, "NO VERIFICABLE", str(e).splitlines()[0][:200],
                    "No se pudo consultar el BCRP o la SBS. No se estima nada en su lugar.")
        return
    del_bcrp = {d["periodo"]: float(d["valor"]) for d in bcrp.get("datos", []) if d.get("valor") is not None}
    pares, faltan_bcrp, faltan_sbs = {}, [], []
    for anio in anios:
        periodo = f"{anio}-12"
        total = _total_sbs(sbs.get(anio))
        if periodo not in del_bcrp:
            faltan_bcrp.append(periodo)
        if total is None:
            faltan_sbs.append(periodo)
        if periodo in del_bcrp and total is not None:
            pares[periodo] = (del_bcrp[periodo], total)
    if not pares:
        reg.agregar("BCRP / SBS", verificacion, "NO VERIFICABLE", "ningún diciembre con dato de las dos fuentes",
                    "No se estima nada en su lugar.")
        return
    diferencias = {p: abs(b - s) for p, (b, s) in pares.items()}
    peor = max(diferencias, key=diferencias.get)
    detalle = (f"{len(pares)} diciembres; diferencia absoluta máxima {diferencias[peor]:.2f} puntos en {peor}; "
               + "; ".join(f"{p}: BCRP {b:.2f} % frente a SBS {s:.2f} %" for p, (b, s) in pares.items()))
    if faltan_bcrp:
        detalle += f"; sin dato del BCRP: {', '.join(faltan_bcrp)}"
    if faltan_sbs:
        detalle += f"; sin dato de la SBS: {', '.join(faltan_sbs)}"
    reg.agregar("BCRP / SBS", verificacion, "DIFERENCIA", detalle,
                "Miden cosas distintas, así que no se espera que coincidan: la SBS publica en el B-2401 «Créditos "
                "Atrasados (criterio SBS) / Créditos Directos», y la serie PN07746EM del BCRP es «Cartera atrasada neta "
                "/ Colocaciones netas (%) - Empresas Bancarias». Antes de comparar cifras de morosidad hay que revisar "
                "esa definición, la cobertura y la fecha.")


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
    tabla.to_csv(SALIDAS / "consistencia.csv", index=False, encoding="utf-8")
    return conteo


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--anio-bcrp", type=int, default=2024,
                        help="Año de las series del IPC del BCRP que se contrastan. La morosidad BCRP-SBS se contrasta siempre en diciembre de 2020 a 2024.")
    parser.add_argument("--sin-bcrp", action="store_true", help="Omite las verificaciones que consultan al BCRP.")
    args = parser.parse_args()
    reg = Registro()
    verificar_enaho(reg)
    if not args.sin_bcrp:
        verificar_bcrp(reg, args.anio_bcrp)
        verificar_morosidad(reg)
    verificar_informe(reg)
    conteo = escribir(reg)
    print("salidas/consistencia.md: " + ", ".join(f"{k} {v}" for k, v in sorted(conteo.items())))
    if conteo.get("FALLA"):
        sys.exit(f"{conteo['FALLA']} verificaciones fallaron. Revisa salidas/consistencia.md.")


if __name__ == "__main__":
    main()
