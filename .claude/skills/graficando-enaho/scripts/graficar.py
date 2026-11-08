"""Grafica la pobreza de la ENAHO 2024 por área, sexo, edad o departamento en figuras/."""

import argparse
import sys
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

RAIZ = Path(__file__).resolve().parents[4]
BASE = RAIZ / "salidas" / "personas_2024.parquet"
FIGURAS = RAIZ / "figuras"

LLAVES_HOGAR = ["conglome", "vivienda", "hogar"]

COLOR_BARRA = "#2a78d6"
COLOR_TEXTO = "#0b0b0b"
COLOR_SECUNDARIO = "#52514e"
COLOR_FONDO = "#fcfcfb"

GRUPOS_EDAD = [0, 15, 30, 45, 60, 200]
NOMBRES_EDAD = ["0 a 14 años", "15 a 29 años", "30 a 44 años", "45 a 59 años", "60 años y más"]
NOTA_HOGAR = "Ponderado por hogar con factor07 × mieperho."
NOTA_PERSONA = "Ponderado por persona con facpob07."


def tasa_por_grupo(tabla: pd.DataFrame, grupo: pd.Series, peso: str) -> pd.Series:
    ponderado = (tabla["pobre"] * tabla[peso]).groupby(grupo, observed=True).sum()
    return 100 * ponderado / tabla[peso].groupby(grupo, observed=True).sum()


def nacional(base: pd.DataFrame) -> float:
    hogares = base.drop_duplicates(LLAVES_HOGAR)
    return float(100 * (hogares["pobre"] * hogares["peso_hogar"]).sum() / hogares["peso_hogar"].sum())


def por_area(base: pd.DataFrame) -> pd.Series:
    # Como la cifra oficial: una fila por hogar, expandida a sus personas.
    hogares = base.drop_duplicates(LLAVES_HOGAR)
    area = hogares["urbano"].map({True: "Urbana", False: "Rural"})
    return tasa_por_grupo(hogares, area, "peso_hogar").sort_values(ascending=False)


def por_sexo(base: pd.DataFrame) -> pd.Series:
    sexo = base["p207"].map({1: "Hombres", 2: "Mujeres"})
    return tasa_por_grupo(base, sexo, "facpob07").sort_values(ascending=False)


def por_edad(base: pd.DataFrame) -> pd.Series:
    # Las edades conservan su orden natural.
    edad = pd.cut(base["p208a"], bins=GRUPOS_EDAD, right=False, labels=NOMBRES_EDAD)
    return tasa_por_grupo(base, edad, "facpob07")


def por_departamento(base: pd.DataFrame) -> pd.Series:
    # Como la cifra oficial: una fila por hogar. El nombre es solo para mostrar; el código lo fija limpiar.py.
    hogares = base.drop_duplicates(LLAVES_HOGAR)
    return tasa_por_grupo(hogares, hogares["departamento_nombre"], "peso_hogar").sort_values(ascending=False)


def titulo_area(t: pd.Series) -> str:
    return f"La pobreza rural ({t['Rural']:.1f} %) supera a la urbana ({t['Urbana']:.1f} %) en {t['Rural'] - t['Urbana']:.1f} puntos"


def titulo_sexo(t: pd.Series) -> str:
    brecha = abs(t["Mujeres"] - t["Hombres"])
    cifras = f"mujeres ({t['Mujeres']:.1f} %) y hombres ({t['Hombres']:.1f} %)"
    if brecha < 1:
        return f"La pobreza es similar entre {cifras}: {brecha:.1f} puntos de brecha"
    return f"La pobreza es mayor entre {t.idxmax().lower()}: {cifras}, {brecha:.1f} puntos de brecha"


def titulo_edad(t: pd.Series) -> str:
    return f"La pobreza es mayor entre {t.idxmax()} ({t.max():.1f} %) y menor entre {t.idxmin()} ({t.min():.1f} %)"


def titulo_departamento(t: pd.Series) -> str:
    return f"{t.idxmax()} ({t.max():.1f} %) y {t.idxmin()} ({t.min():.1f} %): los extremos de la pobreza departamental"


GRAFICOS = {
    "area": (por_area, "área de residencia", NOTA_HOGAR, titulo_area),
    "sexo": (por_sexo, "sexo", NOTA_PERSONA, titulo_sexo),
    "edad": (por_edad, "grupo de edad", NOTA_PERSONA, titulo_edad),
    "departamento": (por_departamento, "departamento", NOTA_HOGAR, titulo_departamento),
}


def _estilo(eje) -> None:
    for lado in ("top", "right", "left", "bottom"):
        eje.spines[lado].set_visible(False)
    eje.tick_params(length=0, colors=COLOR_SECUNDARIO, labelsize=9)


def dibujar(tasas: pd.Series, tema: str, nota: str, titulo: str, destino: Path, referencia: float) -> None:
    horizontal = len(tasas) > 6  # muchas categorías: barras horizontales para que los nombres se lean
    figura, eje = plt.subplots(figsize=(8, 8.6) if horizontal else (7.6, 5.2), facecolor=COLOR_FONDO)
    eje.set_facecolor(COLOR_FONDO)
    etiqueta = "% de personas en pobreza"
    if horizontal:
        orden = tasas.sort_values()
        barras = eje.barh(range(len(orden)), orden.to_numpy(), height=0.7, color=COLOR_BARRA)
        eje.set_yticks(range(len(orden)), [str(n) for n in orden.index], color=COLOR_TEXTO, fontsize=10)
        eje.set_xlim(0, orden.max() * 1.15)
        eje.set_xlabel(etiqueta, color=COLOR_SECUNDARIO, fontsize=10)
        eje.axvline(referencia, color=COLOR_SECUNDARIO, linewidth=1, linestyle="--", zorder=0)
        eje.text(referencia, len(orden) - 0.3, f" Nacional: {referencia:.1f} %", color=COLOR_TEXTO, fontsize=9)
    else:
        barras = eje.bar(range(len(tasas)), tasas.to_numpy(), width=0.62, color=COLOR_BARRA)
        eje.set_xticks(range(len(tasas)), [str(n) for n in tasas.index], color=COLOR_TEXTO, fontsize=11)
        eje.set_ylim(0, max(tasas.max() * 1.18, 10))
        eje.set_ylabel(etiqueta, color=COLOR_SECUNDARIO, fontsize=9)
    # El fondo de cada etiqueta tapa la línea del promedio nacional donde se cruzan
    eje.bar_label(barras, fmt="%.1f %%", padding=4, color=COLOR_TEXTO, fontsize=9 if horizontal else 12,
                  fontweight="bold", bbox={"facecolor": COLOR_FONDO, "edgecolor": "none", "pad": 0.6})
    _estilo(eje)

    # Posiciones en fracción de la figura, según su alto y las líneas que ocupa el título
    lineas = textwrap.wrap(titulo, 78 if horizontal else 66)
    renglon = 12.5 * 1.3 / 72 / figura.get_figheight()
    arriba = 0.985 if horizontal else 0.975
    debajo = arriba - len(lineas) * renglon - 0.01
    margen = debajo - 2.2 * renglon
    # figura.text y no suptitle: tight_layout reservaría otra vez el espacio del título
    figura.text(0.02, arriba, "\n".join(lineas), ha="left", va="top", color=COLOR_TEXTO, fontsize=12.5,
                fontweight="bold")
    figura.text(0.02, debajo, f"Pobreza monetaria por {tema}, Perú 2024 (% de personas)", va="top",
                color=COLOR_SECUNDARIO, fontsize=10)
    figura.text(0.02, 0.015, f"Fuente: INEI, ENAHO 2024 (módulos 34 y 02). {nota}", color=COLOR_SECUNDARIO,
                fontsize=8.5)
    figura.tight_layout(rect=(0, 0.035, 1, margen))

    FIGURAS.mkdir(exist_ok=True)
    figura.savefig(destino, dpi=200, facecolor=COLOR_FONDO, metadata={"Software": None})
    plt.close(figura)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--por", choices=sorted(GRAFICOS), help="Sin este argumento hace los cuatro gráficos.")
    args = parser.parse_args()

    if not BASE.is_file():
        sys.exit(f"Falta {BASE.name} en salidas/. Créala primero con la skill limpiando-enaho.")
    base = pd.read_parquet(BASE)
    referencia = nacional(base)

    for nombre in [args.por] if args.por else sorted(GRAFICOS):
        calcular, tema, nota, titular = GRAFICOS[nombre]
        tasas = calcular(base)
        destino = FIGURAS / f"pobreza_por_{nombre}.png"
        dibujar(tasas, tema, nota, titular(tasas), destino, referencia)
        cifras = ", ".join(f"{grupo}: {valor:.1f} %" for grupo, valor in tasas.items())
        print(f"{destino.relative_to(RAIZ).as_posix()} ({cifras})")


if __name__ == "__main__":
    main()
