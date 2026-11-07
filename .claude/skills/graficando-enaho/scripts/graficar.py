"""Grafica la pobreza de la ENAHO 2024 por área, sexo, edad o departamento, y la serie 2020-2024, en figuras/."""

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

RAIZ = Path(__file__).resolve().parents[4]
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))
import estilo_graficos
BASE = RAIZ / "salidas" / "personas_2024.parquet"
INDICADORES = RAIZ / "salidas" / "indicadores.csv"
REFERENCIA = RAIZ / "referencias" / "inei_pobreza_2024.csv"
FIGURAS = RAIZ / "figuras"
DESTINO_SERIE = FIGURAS / "pobreza_serie_2020_2024.png"

LLAVES_HOGAR = ["conglome", "vivienda", "hogar"]
# Lima se analiza desagregada; estos rótulos son los mismos en todos los gráficos y mapas.
LIMA_METROPOLITANA = "Lima Metropolitana"
LIMA_PROVINCIAS = "Lima provincias"
NOMBRES_LIMA = {"1501": LIMA_METROPOLITANA, "15_resto": LIMA_PROVINCIAS}
MARCA_REFERENCIAL = "*"

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
    # 26 ámbitos territoriales de análisis oficial (Cuadro III.1 del INEI):
    # 24 departamentos, Callao, Lima Metropolitana (provincia 1501) y Lima provincias.
    hogares = base.drop_duplicates(LLAVES_HOGAR).copy()

    def ambito(r):
        if r["departamento"] == "15":
            return LIMA_METROPOLITANA if str(r["ubigeo"])[:4] == "1501" else LIMA_PROVINCIAS
        return r["departamento_nombre"]

    ambitos = hogares.apply(ambito, axis=1)
    return tasa_por_grupo(hogares, ambitos, "peso_hogar").sort_values(ascending=False)


def referenciales(base: pd.DataFrame) -> list[str]:
    """Ámbitos cuya cifra el INEI publica como referencial (CV > 15 %): su estimación es menos precisa.

    Se leen de las columnas `cv` y `nota` de la tabla del INEI y se traducen, por código, a los nombres del gráfico.
    """
    if not REFERENCIA.is_file():
        return []
    tabla = pd.read_csv(REFERENCIA, dtype={"ccdd": str}).dropna(subset=["ccdd"])
    marcadas = (pd.to_numeric(tabla["cv"], errors="coerce") > 15) | tabla["nota"].fillna("").str.contains("referencial")
    nombres = base.drop_duplicates("departamento").set_index("departamento")["departamento_nombre"].to_dict()
    nombres |= NOMBRES_LIMA
    return sorted(nombres[c] for c in tabla.loc[marcadas, "ccdd"] if c in nombres)


def y_o_e(siguiente: str) -> str:
    """La conjunción copulativa: «e» ante el sonido i («Cajamarca e Ica»), «y» en el resto («y Huancavelica»)."""
    palabra = siguiente.lower()
    sonido_i = palabra.startswith(("i", "hi")) and not palabra.startswith(("ia", "ie", "io", "iu", "hia", "hie",
                                                                            "hio", "hiu"))
    return "e" if sonido_i else "y"


def enumerar(nombres: list[str]) -> str:
    """«A, B y C», con la conjunción que corresponde al último nombre."""
    if len(nombres) < 2:
        return "".join(nombres)
    return f"{', '.join(nombres[:-1])} {y_o_e(nombres[-1])} {nombres[-1]}"


def titulo_area(t: pd.Series) -> str:
    return f"La pobreza rural ({t['Rural']:.1f} %) supera a la urbana ({t['Urbana']:.1f} %) en {t['Rural'] - t['Urbana']:.1f} puntos"


def titulo_sexo(t: pd.Series) -> str:
    brecha = abs(t["Mujeres"] - t["Hombres"])
    cifras = f"mujeres ({t['Mujeres']:.1f} %) y hombres ({t['Hombres']:.1f} %)"
    if brecha < 1:
        return f"La pobreza es similar entre {cifras}: {brecha:.1f} puntos de brecha"
    return f"La pobreza es mayor entre {t.idxmax().lower()}: {cifras}, {brecha:.1f} puntos de brecha"


def titulo_edad(t: pd.Series) -> str:
    return (f"La pobreza es mayor en el grupo de {t.idxmax()} ({t.max():.1f} %) "
            f"y menor en el de {t.idxmin()} ({t.min():.1f} %)")


def titulo_departamento(t: pd.Series) -> str:
    minimo = str(t.idxmin())
    return (f"{t.idxmax()} ({t.max():.1f} %) {y_o_e(minimo)} {minimo} ({t.min():.1f} %): "
            "los extremos de la pobreza territorial")


GRAFICOS = {
    "area": (por_area, "área de residencia", NOTA_HOGAR, titulo_area),
    "sexo": (por_sexo, "sexo", NOTA_PERSONA, titulo_sexo),
    "edad": (por_edad, "grupo de edad", NOTA_PERSONA, titulo_edad),
    "departamento": (por_departamento,
                     f"departamento, con Lima desagregada en {LIMA_METROPOLITANA} y {LIMA_PROVINCIAS}",
                     NOTA_HOGAR, titulo_departamento),
}


def nota_referenciales(marcados: list[str]) -> str:
    return (f"{MARCA_REFERENCIAL} Cifra referencial: el INEI informa un coeficiente de variación mayor que 15 % para "
            f"{enumerar(marcados)}, por lo que su estimación es menos precisa.")


def _cifras_fuera_de_la_linea(figura, eje, cifras, referencia: float) -> None:
    """Pasa adentro de su barra cada cifra que, escrita en la punta, caería sobre la línea del promedio nacional.

    Se mide con la figura ya compuesta: la cifra va afuera, en la punta, salvo que su caja cruce la línea; entonces
    va en blanco dentro del extremo de la barra, donde cabe con holgura porque esas barras superan los 20 puntos.
    """
    figura.canvas.draw()
    renderer = figura.canvas.get_renderer()
    x_linea = eje.transData.transform((referencia, 0))[0]
    for cifra in cifras:
        caja = cifra.get_window_extent(renderer)
        if caja.x0 <= x_linea <= caja.x1:
            cifra.xyann = (-4, 0)
            cifra.set_horizontalalignment("right")
            cifra.set_color(estilo_graficos.COLOR_FONDO)


def dibujar(tasas: pd.Series, tema: str, nota: str, titulo: str, destino: Path, referencia: float,
            marcados: list[str] | None = None) -> None:
    marcados = marcados or []
    horizontal = len(tasas) > 6  # muchas categorías: barras horizontales para que los nombres se lean
    figura, eje = plt.subplots(figsize=(8.2, 9.4) if horizontal else (7.6, 5.2), facecolor=estilo_graficos.COLOR_FONDO)
    eje.set_facecolor(estilo_graficos.COLOR_FONDO)
    etiqueta = "% de personas en pobreza"
    fuente = f"Fuente: INEI, ENAHO 2024 (módulos 34 y 02). {nota}"
    if horizontal:
        orden = tasas.sort_values()
        barras = eje.barh(range(len(orden)), orden.to_numpy(), height=0.68, color=estilo_graficos.COLOR_BARRA,
                          zorder=2)
        nombres = [f"{n}{MARCA_REFERENCIAL}" if n in marcados else str(n) for n in orden.index]
        eje.set_yticks(range(len(orden)), nombres, color=estilo_graficos.COLOR_TEXTO, fontsize=9.5)
        eje.set_ylim(-0.6, len(orden) + 0.2)
        eje.set_xlim(0, max(orden.max() * 1.12, 10))
        eje.set_xlabel(etiqueta, color=estilo_graficos.COLOR_SECUNDARIO, fontsize=9.5)
        # Promedio nacional: línea de referencia sobre las barras y debajo de las cifras.
        eje.axvline(referencia, color=estilo_graficos.COLOR_TEXTO, linewidth=1, linestyle=(0, (4, 3)), zorder=3)
        eje.text(referencia, len(orden) - 0.35, f" Nacional: {referencia:.1f} %", color=estilo_graficos.COLOR_TEXTO,
                 fontsize=8.5, fontweight="bold", va="bottom")
        if marcados:
            fuente += "\n" + nota_referenciales(marcados)
    else:
        barras = eje.bar(range(len(tasas)), tasas.to_numpy(), width=0.55, color=estilo_graficos.COLOR_BARRA)
        eje.set_xticks(range(len(tasas)), [str(n) for n in tasas.index], color=estilo_graficos.COLOR_TEXTO, fontsize=10.5)
        eje.set_ylim(0, max(tasas.max() * 1.18, 10))
        eje.set_ylabel(etiqueta, color=estilo_graficos.COLOR_SECUNDARIO, fontsize=9.5)

    cifras = eje.bar_label(barras, fmt="%.1f %%", padding=4, color=estilo_graficos.COLOR_TEXTO,
                           fontsize=8.5 if horizontal else 11, fontweight="bold", zorder=4)
    estilo_graficos.estilizar_ejes(eje, horizontal=horizontal)

    subtitulo = f"Pobreza monetaria por {tema}, Perú 2024 (% de personas)"
    estilo_graficos.encabezado(figura, eje, titulo=titulo, subtitulo=subtitulo, fuente=fuente)
    if horizontal:
        _cifras_fuera_de_la_linea(figura, eje, cifras, referencia)

    FIGURAS.mkdir(exist_ok=True)
    figura.savefig(destino, dpi=200, facecolor=estilo_graficos.COLOR_FONDO, metadata={"Software": None})
    plt.close(figura)


def repartir(valores: list[float], separacion: float) -> list[float]:
    """Posiciones verticales para las etiquetas: lo más cerca posible de cada valor y a `separacion` como mínimo.

    Las etiquetas que chocarían forman un grupo centrado en el promedio de sus valores, sin cambiar su orden.
    """
    grupos = [[i] for i in sorted(range(len(valores)), key=valores.__getitem__)]

    def borde(grupo: list[int]) -> tuple[float, float]:
        centro = sum(valores[i] for i in grupo) / len(grupo)
        mitad = separacion * (len(grupo) - 1) / 2
        return centro - mitad, centro + mitad

    unidos = True
    while unidos:
        unidos = False
        for k in range(len(grupos) - 1):
            if borde(grupos[k])[1] + separacion > borde(grupos[k + 1])[0]:
                grupos[k] += grupos.pop(k + 1)
                unidos = True
                break
    posiciones = [0.0] * len(valores)
    for grupo in grupos:
        inicio = borde(grupo)[0]
        for j, i in enumerate(grupo):
            posiciones[i] = inicio + j * separacion
    return posiciones


def _rotular_extremos(eje, puntos: list[tuple], lado: str) -> None:
    """Escribe la cifra de cada serie junto a su primer o último punto, unida a él por una guía de su color.

    El texto va en tinta y la guía lleva el color de la serie: así las cifras cercanas no se superponen y cada una
    sigue asociada a su línea.
    """
    figura = eje.figure
    alto_puntos = eje.get_window_extent().height * 72 / figura.dpi
    y_min, y_max = eje.get_ylim()
    separacion = 12.5 * (y_max - y_min) / alto_puntos  # unas 12.5 pt entre líneas de texto de 8.5 pt
    posiciones = repartir([y for _, y, _ in puntos], separacion)
    signo = -1 if lado == "izquierda" else 1
    for (x, y, color), y_texto in zip(puntos, posiciones):
        eje.annotate(f"{y:.1f} %", xy=(x, y), xytext=(x + signo * 0.3, y_texto), textcoords="data",
                     ha="right" if signo < 0 else "left", va="center", fontsize=8.5, fontweight="bold",
                     color=estilo_graficos.COLOR_TEXTO,
                     arrowprops={"arrowstyle": "-", "color": color, "linewidth": 1.1, "shrinkA": 1.5, "shrinkB": 4.5})


def graficar_serie_pobreza(ruta_indicadores: Path = INDICADORES, destino: Path = DESTINO_SERIE) -> Path:
    """Genera la figura de evolución temporal 2020-2024 de pobreza por área y ámbito."""
    if not ruta_indicadores.is_file():
        sys.exit(f"Falta {ruta_indicadores.name} en salidas/. Créala primero con la skill limpiando-enaho.")
    df = pd.read_csv(ruta_indicadores)
    if "anio" not in df.columns:
        sys.exit(f"Falta la columna anio en {ruta_indicadores.name}.")

    figura, eje = plt.subplots(figsize=(8.5, 5.8), facecolor=estilo_graficos.COLOR_FONDO)
    eje.set_facecolor(estilo_graficos.COLOR_FONDO)

    # Colores en el orden fijo de la paleta categórica validada; línea, marcador y trazo distinguen además cada serie.
    paleta = estilo_graficos.PALETA_CATEGORICA
    series_config = [
        ("pobreza_nacional", "Nacional", paleta[0], 2.6, "-", "o"),
        ("pobreza_area_rural", "Rural", paleta[1], 2.0, "-", "s"),
        ("pobreza_area_urbana", "Urbana", paleta[2], 2.0, "-", "^"),
        ("pobreza_lima_metropolitana_provincia", LIMA_METROPOLITANA, paleta[3], 2.0, (0, (5, 2)), "D"),
        ("pobreza_lima_provincias", LIMA_PROVINCIAS, paleta[4], 2.0, (0, (5, 2)), "v"),
    ]

    anios = sorted(df["anio"].dropna().astype(int).unique())
    extremos = {"inicio": [], "fin": []}  # (valor, color) del primer y del último año de cada serie
    for id_serie, etiqueta, color, ancho, estilo_linea, marcador in series_config:
        sub = df[df["id"] == id_serie].sort_values("anio")
        if sub.empty:
            continue
        x = sub["anio"].to_numpy()
        y = sub["valor"].to_numpy()
        eje.plot(x, y, label=etiqueta, color=color, linewidth=ancho, linestyle=estilo_linea,
                 marker=marcador, markersize=6, markeredgecolor=estilo_graficos.COLOR_FONDO, markeredgewidth=1.2,
                 solid_capstyle="round", zorder=3)
        extremos["inicio"].append((x[0], y[0], color))
        extremos["fin"].append((x[-1], y[-1], color))

    valores = df.loc[df["id"].isin([s[0] for s in series_config]), "valor"]
    eje.set_xticks(anios)
    eje.set_xticklabels([str(a) for a in anios], color=estilo_graficos.COLOR_TEXTO, fontsize=10)
    eje.set_xlim(anios[0] - 0.8, anios[-1] + 0.8)  # espacio para las cifras de los extremos
    eje.set_ylabel("% de personas en pobreza", color=estilo_graficos.COLOR_SECUNDARIO, fontsize=9.5)
    eje.set_ylim(5 * ((valores.min() - 2) // 5), 5 * -((-valores.max() - 2) // 5))
    estilo_graficos.estilizar_ejes(eje, horizontal=False)
    eje.legend(loc="lower left", bbox_to_anchor=(0, 1.01), ncol=5, frameon=False, fontsize=9, handlelength=2.6,
               columnspacing=1.4, borderaxespad=0)

    nacional = df[df["id"] == "pobreza_nacional"].sort_values("anio")
    titulo = (f"La pobreza monetaria pasó de {nacional['valor'].iloc[0]:.1f} % en {nacional['anio'].iloc[0]} "
              f"a {nacional['valor'].iloc[-1]:.1f} % en {nacional['anio'].iloc[-1]}")
    subtitulo = (f"Pobreza monetaria nacional, por área de residencia y en {LIMA_METROPOLITANA} y {LIMA_PROVINCIAS}, "
                 f"Perú {anios[0]}-{anios[-1]} (% de personas)")
    fuente = "Fuente: INEI, ENAHO 2020-2024 (módulos 34 y 02). Ponderado por hogar con factor07 × mieperho."
    estilo_graficos.encabezado(figura, eje, titulo=titulo, subtitulo=subtitulo, fuente=fuente)
    # Las cifras se ubican con la figura ya compuesta, porque la separación mínima depende del alto final del eje.
    _rotular_extremos(eje, extremos["inicio"], lado="izquierda")
    _rotular_extremos(eje, extremos["fin"], lado="derecha")

    FIGURAS.mkdir(exist_ok=True)
    figura.savefig(destino, dpi=200, facecolor=estilo_graficos.COLOR_FONDO, metadata={"Software": None})
    plt.close(figura)
    return destino


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    opciones = sorted(list(GRAFICOS.keys()) + ["serie"])
    parser.add_argument("--por", choices=opciones, help="Sin este argumento hace todos los gráficos (incluyendo serie).")
    args = parser.parse_args()

    if args.por == "serie":
        dest = graficar_serie_pobreza()
        print(f"{dest.relative_to(RAIZ).as_posix()} (serie 2020-2024)")
        return

    if not BASE.is_file():
        sys.exit(f"Falta {BASE.name} en salidas/. Créala primero con la skill limpiando-enaho.")
    base = pd.read_parquet(BASE)
    referencia = nacional(base)

    for nombre in [args.por] if args.por else sorted(GRAFICOS):
        calcular, tema, nota, titular = GRAFICOS[nombre]
        tasas = calcular(base)
        destino = FIGURAS / f"pobreza_por_{nombre}.png"
        marcados = referenciales(base) if nombre == "departamento" else []
        dibujar(tasas, tema, nota, titular(tasas), destino, referencia, marcados)
        cifras = ", ".join(f"{grupo}: {valor:.1f} %" for grupo, valor in tasas.items())
        aviso = f"; cifras referenciales del INEI (CV > 15 %): {enumerar(marcados)}" if marcados else ""
        print(f"{destino.relative_to(RAIZ).as_posix()} ({cifras}{aviso})")
    if not args.por:
        dest_serie = graficar_serie_pobreza()
        print(f"{dest_serie.relative_to(RAIZ).as_posix()} (serie 2020-2024)")


if __name__ == "__main__":
    main()
