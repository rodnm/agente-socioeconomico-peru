"""Resume las corridas de evaluar.py en tablas reproducibles: evaluacion/metricas.md.

    uv run evaluacion/analizar.py

Lee resultados.csv (preguntas con respuesta numérica) y, si existe, robustez_resultados.csv. Todas las cifras de
comparacion.md y ablacion.md salen de estas tablas.
"""
import sys
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).resolve().parent
ORDEN_MODOS = ["A", "B", "memoria", "solo-mcp", "solo-skills", "sin-propia"]
RESULTADOS = ["acierta", "se equivoca", "no sabe", "error"]
FAMILIAS = {"MCP": "mcp__", "Skill": "Skill:", "Web": ("WebSearch", "WebFetch"), "Bash": "Bash"}


def _modos(df):
    presentes = list(dict.fromkeys(df["modo"]))
    return [m for m in ORDEN_MODOS if m in presentes] + [m for m in presentes if m not in ORDEN_MODOS]


def resumen_por_modo(df):
    t = df.groupby("modo")["resultado"].value_counts().unstack(fill_value=0).reindex(columns=RESULTADOS, fill_value=0)
    t["segundos promedio"] = df.groupby("modo")["segundos"].mean().round(1)
    t["turnos promedio"] = df.groupby("modo")["turnos"].mean().round(1)
    t["costo total USD"] = df.groupby("modo")["costo_usd"].sum().round(2)
    return t.reindex(_modos(df))


def por_tipo(df):
    aciertos = df.assign(acierta=df["resultado"].eq("acierta")).groupby(["tipo", "modo"])["acierta"]
    t = (aciertos.sum().astype(int).astype(str) + " de " + aciertos.size().astype(str)).unstack()
    return t.reindex(columns=_modos(df))


def matriz(df):
    celda = df["resultado"] + df["valor"].map(lambda v: "" if pd.isna(v) else f" ({v:g})")
    return df.assign(celda=celda).pivot(index="id", columns="modo", values="celda").reindex(
        index=list(dict.fromkeys(df["id"])), columns=_modos(df))


def cambios(df, base, otro):
    """Preguntas que pasan a acertar (mejoran) o dejan de acertar (empeoran) al ir de `base` a `otro`."""
    r = df.pivot(index="id", columns="modo", values="resultado").reindex(list(dict.fromkeys(df["id"])))
    mejoran = r.index[(r[base] != "acierta") & (r[otro] == "acierta")].tolist()
    empeoran = r.index[(r[base] == "acierta") & (r[otro] != "acierta")].tolist()
    return mejoran, empeoran


def uso_de_herramientas(df):
    herramientas = df["herramientas"].fillna("").astype(str)
    t = pd.DataFrame({familia: herramientas.map(lambda h, p=prefijos: any(
        x.startswith(p) for x in h.split(";") if x)) for familia, prefijos in FAMILIAS.items()})
    t["modo"] = df["modo"]
    return t.groupby("modo").sum().astype(int).reindex(_modos(df))


def robustez_por_modo(r):
    t = r.groupby("modo")["resultado"].value_counts().unstack(fill_value=0).reindex(
        columns=["cumple", "no cumple"], fill_value=0)
    return t.reindex(_modos(r))


def _celda(v):
    if isinstance(v, tuple):
        return " · ".join(map(str, v))
    if pd.isna(v):
        return ""
    return str(int(v)) if isinstance(v, float) and v.is_integer() else str(v)


def tabla_md(t, indice=""):
    cabecera = [indice or (t.index.name or "")] + [str(c) for c in t.columns]
    filas = [[_celda(i)] + [_celda(v) for v in fila] for i, fila in zip(t.index, t.values)]
    return "\n".join(["| " + " | ".join(cabecera) + " |", "|" + "---|" * len(cabecera)]
                     + ["| " + " | ".join(f) + " |" for f in filas])


def escribir(resultados_csv, robustez_csv, destino):
    df = pd.read_csv(resultados_csv)
    partes = ["# Métricas de la evaluación", "",
              f"Generado por `evaluacion/analizar.py` a partir de `{Path(resultados_csv).name}`. "
              "Cada fila de las corridas es una sesión nueva de `claude -p` con el mismo modelo.", "",
              "## Aciertos por modo", "", tabla_md(resumen_por_modo(df), "modo"), "",
              "## Aciertos por tipo de pregunta", "", tabla_md(por_tipo(df), "tipo"), "",
              "## Resultado de cada pregunta", "", "Entre paréntesis, el valor que respondió el agente.", "",
              tabla_md(matriz(df), "pregunta"), "",
              "## Cambios frente al Modo A", ""]
    for modo in [m for m in _modos(df) if m != "A"] if "A" in set(df["modo"]) else []:
        mejoran, empeoran = cambios(df, "A", modo)
        partes.append(f"- **{modo}**: mejoran {', '.join(mejoran) or 'ninguna'}; empeoran {', '.join(empeoran) or 'ninguna'}.")
    partes += ["", "## Uso de herramientas", "",
               "Corridas de cada modo que usaron al menos una herramienta de cada familia.", "",
               tabla_md(uso_de_herramientas(df), "modo"), "",
               "## Interpretación de las mixtas", "",
               "`lenguaje_causal` marca palabras que afirman causas; la revisión con el criterio de preguntas.csv es manual.",
               ""]
    mixtas = df[df["tipo"] == "mixta"].set_index(["id", "modo"])
    columnas = [c for c in ("resultado", "lenguaje_causal", "interpretacion") if c in mixtas.columns]
    partes += [tabla_md(mixtas[columnas].astype(str).apply(lambda s: s.str.slice(0, 240)), "pregunta y modo"), ""]
    if Path(robustez_csv).is_file():
        r = pd.read_csv(robustez_csv)
        partes += ["## Robustez", "", tabla_md(robustez_por_modo(r), "modo"), "",
                   tabla_md(r.pivot(index="id", columns="modo", values="conducta_observada").reindex(
                       index=list(dict.fromkeys(r["id"])), columns=_modos(r)), "pedido"), ""]
    destino = Path(destino)
    destino.write_text("\n".join(partes), encoding="utf-8")
    return destino


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    destino = escribir(AQUI / "resultados.csv", AQUI / "robustez_resultados.csv", AQUI / "metricas.md")
    print(destino.relative_to(AQUI.parent).as_posix())


if __name__ == "__main__":
    main()
