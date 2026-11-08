"""Hace el mapa de pobreza por departamento de la ENAHO 2024 en mapas/."""

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

RAIZ = Path(__file__).resolve().parents[4]
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))
import estilo_graficos
BASE = RAIZ / "salidas" / "personas_2024.parquet"
GEOJSON = RAIZ / "datos" / "peru_departamental_simple.geojson"
REFERENCIA = RAIZ / "referencias" / "inei_pobreza_2024.csv"
DESTINO = RAIZ / "mapas" / "pobreza_departamento.png"
COMPARACION = RAIZ / "salidas" / "mapa_vs_referencia.csv"

LLAVES_HOGAR = ["conglome", "vivienda", "hogar"]
DEPARTAMENTOS = 25
TOLERANCIA = 0.1

# Un solo tono, de claro a oscuro.
ESCALA = LinearSegmentedColormap.from_list("azules", ["#cde2fb", "#6da7ec", "#256abf", "#0d366b"])
COLOR_BORDE = "#fcfcfb"
COLOR_TEXTO = "#0b0b0b"
COLOR_SECUNDARIO = "#52514e"
COLOR_FONDO = "#fcfcfb"


def pobreza_por_departamento(base: pd.DataFrame) -> pd.DataFrame:
    # Como la cifra oficial: una fila por hogar, expandida a sus personas.
    hogares = base.drop_duplicates(LLAVES_HOGAR)
    ponderado = (hogares["pobre"] * hogares["peso_hogar"]).groupby(hogares["departamento"]).sum()
    tasas = 100 * ponderado / hogares["peso_hogar"].groupby(hogares["departamento"]).sum()
    return tasas.rename("pobreza_pct").rename_axis("departamento").reset_index()


def unir_con_limites(tasas: pd.DataFrame, limites: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Une por código, nunca por nombre, y exige los 25 departamentos con dato."""
    limites = limites.assign(departamento=limites["FIRST_IDDP"].astype(str))
    mapa = limites.merge(tasas, on="departamento", how="outer", validate="1:1", indicator=True)
    sueltos = mapa.loc[mapa["_merge"] != "both", "departamento"].tolist()
    if sueltos:
        sys.exit(f"Estos códigos no se unieron entre la base y el GeoJSON: {sueltos}.")
    if len(mapa) != DEPARTAMENTOS or mapa["pobreza_pct"].isna().any():
        sys.exit(f"Se esperaban {DEPARTAMENTOS} departamentos con dato; hay {mapa['pobreza_pct'].notna().sum()}.")
    return mapa


def comprobar_referencia(mapa: gpd.GeoDataFrame) -> None:
    """Contrasta cada departamento con las cifras oficiales del INEI y deja la tabla en salidas/."""
    ref_df = pd.read_csv(REFERENCIA, dtype={"ccdd": str})
    ref_deps = ref_df[ref_df["ccdd"].isin(mapa["departamento"])].set_index("ccdd")["valor"].astype(float)
    calculada = mapa.set_index("departamento")["pobreza_pct"]
    diferencia = (calculada - ref_deps).abs()
    tabla = pd.DataFrame({"departamento": mapa.set_index("departamento")["NOMBDEP"], "pobreza_pct": calculada.round(2),
                          "referencia_inei": ref_deps, "diferencia": diferencia.round(2)})
    tabla["dentro_de_tolerancia"] = tabla["diferencia"] <= TOLERANCIA
    COMPARACION.parent.mkdir(exist_ok=True)
    tabla.rename_axis("ccdd").sort_index().to_csv(COMPARACION, encoding="utf-8")
    alejados = diferencia[diferencia > TOLERANCIA]
    if not alejados.empty:
        sys.exit(f"Estos departamentos difieren más de {TOLERANCIA} puntos de la referencia del INEI: {alejados.round(2).to_dict()}.")


def dibujar(mapa: gpd.GeoDataFrame) -> None:
    figura, eje = plt.subplots(figsize=(7.6, 9.0), facecolor=estilo_graficos.COLOR_FONDO)
    eje.set_facecolor(estilo_graficos.COLOR_FONDO)
    mapa.plot(
        column="pobreza_pct", ax=eje, cmap=estilo_graficos.ESCALA_MAPA, vmin=0, vmax=45.0,
        edgecolor="#ffffff", linewidth=0.8, legend=True,
        legend_kwds={"label": "% de personas en pobreza", "shrink": 0.45, "aspect": 20, "pad": 0.02},
    )
    eje.set_axis_off()

    barra = figura.axes[-1]
    barra.set_yticks([0, 10, 20, 30, 40, 45])
    barra.set_yticklabels(["0 %", "10 %", "20 %", "30 %", "40 %", "45 %"])
    barra.tick_params(colors=estilo_graficos.COLOR_SECUNDARIO, labelsize=8.5, length=0)
    barra.yaxis.label.set_color(estilo_graficos.COLOR_SECUNDARIO)
    for borde in barra.spines.values():
        borde.set_visible(False)

    # Recuadro ampliado para Lima y Callao
    inset_ax = eje.inset_axes([0.03, 0.15, 0.35, 0.35], facecolor="#f8fafc")
    lima_callao = mapa[mapa["departamento"].isin(["07", "15"])]
    lima_callao.plot(
        column="pobreza_pct", ax=inset_ax, cmap=estilo_graficos.ESCALA_MAPA, vmin=0, vmax=45.0,
        edgecolor="#ffffff", linewidth=1.2,
    )
    inset_ax.set_xlim(-77.8, -75.8)
    inset_ax.set_ylim(-13.0, -11.3)
    inset_ax.set_xticks([])
    inset_ax.set_yticks([])
    inset_ax.set_title("Detalle: Lima y Callao", fontsize=8.5, color=estilo_graficos.COLOR_TEXTO, fontweight="bold", pad=3)
    for s in inset_ax.spines.values():
        s.set_color(estilo_graficos.COLOR_LINEA_GUIA)
        s.set_linewidth(0.8)

    callao_p = mapa.loc[mapa["departamento"] == "07", "pobreza_pct"].iloc[0]
    lima_p = mapa.loc[mapa["departamento"] == "15", "pobreza_pct"].iloc[0]
    inset_ax.text(-77.15, -12.05, f"Callao\n{callao_p:.1f} %", fontsize=7.5, color="#ffffff", fontweight="bold", ha="center", va="center")
    inset_ax.text(-76.6, -11.9, f"Lima\n{lima_p:.1f} %", fontsize=7.5, color=estilo_graficos.COLOR_TEXTO, fontweight="bold", ha="center", va="center")

    alto, bajo = mapa.loc[mapa["pobreza_pct"].idxmax()], mapa.loc[mapa["pobreza_pct"].idxmin()]
    titulo = "Pobreza monetaria por departamento, Perú 2024"
    subtitulo = (f"Va de {bajo['pobreza_pct']:.1f} % en {bajo['NOMBDEP'].title()} a {alto['pobreza_pct']:.1f} % en "
                 f"{alto['NOMBDEP'].title()}. Lima y Callao se muestran por separado.")
    fuente = "Fuente: INEI, ENAHO 2024. Ponderado por hogar con factor07 × mieperho."
    estilo_graficos.encabezado(figura, eje, titulo=titulo, subtitulo=subtitulo, fuente=fuente)

    DESTINO.parent.mkdir(exist_ok=True)
    figura.savefig(DESTINO, dpi=200, facecolor=estilo_graficos.COLOR_FONDO, metadata={"Software": None})
    plt.close(figura)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    if not BASE.is_file():
        sys.exit(f"Falta {BASE.name} en salidas/. Créala con la skill limpiando-enaho.")
    if not GEOJSON.is_file():
        sys.exit(f"Falta {GEOJSON.name} en datos/. Bájalo con la skill descargando-enaho.")

    mapa = unir_con_limites(pobreza_por_departamento(pd.read_parquet(BASE)), gpd.read_file(GEOJSON))
    comprobar_referencia(mapa)
    dibujar(mapa)

    ordenado = mapa.sort_values("pobreza_pct", ascending=False)
    extremos = pd.concat([ordenado.head(3), ordenado.tail(3)])
    cifras = ", ".join(f"{fila.NOMBDEP}: {fila.pobreza_pct:.1f} %" for fila in extremos.itertuples())
    print(f"{DESTINO.relative_to(RAIZ).as_posix()} ({DEPARTAMENTOS} departamentos con dato; {cifras})")


if __name__ == "__main__":
    main()
