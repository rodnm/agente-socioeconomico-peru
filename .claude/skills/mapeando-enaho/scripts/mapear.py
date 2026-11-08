"""Hace los mapas de pobreza de la ENAHO 2024 en mapas/ con límites oficiales del IGN.

Genera dos mapas:
  - mapas/pobreza_departamento.png: los 25 departamentos requeridos por la consigna.
  - mapas/pobreza_ambitos.png: los 26 ámbitos territoriales oficiales del INEI (con Lima desagregada).
"""

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

RAIZ = Path(__file__).resolve().parents[4]
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))
import estilo_graficos

BASE = RAIZ / "salidas" / "personas_2024.parquet"
GEOJSON_DEP_OFICIAL = RAIZ / "referencias" / "limites_departamentales_ign.geojson"
GEOJSON_DEP_LEGACY = RAIZ / "datos" / "peru_departamental_simple.geojson"
GEOJSON_AMBITOS = RAIZ / "referencias" / "limites_ambitos_ign.geojson"

REFERENCIA = RAIZ / "referencias" / "inei_pobreza_2024.csv"
DESTINO_DEP = RAIZ / "mapas" / "pobreza_departamento.png"
DESTINO_AMBITOS = RAIZ / "mapas" / "pobreza_ambitos.png"
COMPARACION = RAIZ / "salidas" / "mapa_vs_referencia.csv"

LLAVES_HOGAR = ["conglome", "vivienda", "hogar"]
DEPARTAMENTOS = 25
AMBITOS = 26
TOLERANCIA = 0.1


def ruta_geojson_departamental() -> Path:
    if GEOJSON_DEP_OFICIAL.is_file():
        return GEOJSON_DEP_OFICIAL
    if GEOJSON_DEP_LEGACY.is_file():
        return GEOJSON_DEP_LEGACY
    sys.exit(f"Falta el archivo de límites departamentales en {GEOJSON_DEP_OFICIAL} o {GEOJSON_DEP_LEGACY}.")


def pobreza_por_departamento(base: pd.DataFrame) -> pd.DataFrame:
    """Calcula la tasa de pobreza monetaria ponderada para los 25 departamentos."""
    hogares = base.drop_duplicates(LLAVES_HOGAR)
    ponderado = (hogares["pobre"] * hogares["peso_hogar"]).groupby(hogares["departamento"]).sum()
    tasas = 100 * ponderado / hogares["peso_hogar"].groupby(hogares["departamento"]).sum()
    return tasas.rename("pobreza_pct").rename_axis("departamento").reset_index()


def pobreza_por_ambitos(base: pd.DataFrame) -> pd.DataFrame:
    """Calcula la tasa de pobreza para 26 ámbitos: 24 departamentos, Callao, Lima Metropolitana y Lima provincias."""
    hogares = base.drop_duplicates(LLAVES_HOGAR).copy()

    def asignar_codigo(r):
        dep = str(r["departamento"]).zfill(2)
        if dep == "15":
            return "1501" if str(r["ubigeo"])[:4] == "1501" else "15_resto"
        return dep

    hogares["codigo"] = hogares.apply(asignar_codigo, axis=1)
    ponderado = (hogares["pobre"] * hogares["peso_hogar"]).groupby(hogares["codigo"]).sum()
    tasas = 100 * ponderado / hogares["peso_hogar"].groupby(hogares["codigo"]).sum()
    return tasas.rename("pobreza_pct").rename_axis("codigo").reset_index()


def unir_con_limites(tasas: pd.DataFrame, limites: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Une por código (FIRST_IDDP o ccdd), nunca por nombre, y exige los 25 departamentos con dato."""
    col_llave = "FIRST_IDDP" if "FIRST_IDDP" in limites.columns else "ccdd"
    limites = limites.assign(departamento=limites[col_llave].astype(str).str.zfill(2))
    mapa = limites.merge(tasas, on="departamento", how="outer", validate="1:1", indicator=True)
    sueltos = mapa.loc[mapa["_merge"] != "both", "departamento"].tolist()
    if sueltos:
        sys.exit(f"Estos códigos no se unieron entre la base y el GeoJSON: {sueltos}.")
    if len(mapa) != DEPARTAMENTOS or mapa["pobreza_pct"].isna().any():
        sys.exit(f"Se esperaban {DEPARTAMENTOS} departamentos con dato; hay {mapa['pobreza_pct'].notna().sum()}.")
    return mapa


def unir_ambitos_con_limites(tasas: pd.DataFrame, limites: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Une los 26 ámbitos por código."""
    limites = limites.assign(codigo=limites["codigo"].astype(str))
    mapa = limites.merge(tasas, on="codigo", how="outer", validate="1:1", indicator=True)
    sueltos = mapa.loc[mapa["_merge"] != "both", "codigo"].tolist()
    if sueltos:
        sys.exit(f"Estos códigos no se unieron en la capa de ámbitos: {sueltos}.")
    if len(mapa) != AMBITOS or mapa["pobreza_pct"].isna().any():
        sys.exit(f"Se esperaban {AMBITOS} ámbitos con dato; hay {mapa['pobreza_pct'].notna().sum()}.")
    return mapa


def comprobar_referencia(mapa: gpd.GeoDataFrame) -> None:
    """Contrasta cada departamento con las cifras oficiales del INEI y deja la tabla en salidas/."""
    ref_df = pd.read_csv(REFERENCIA, dtype={"ccdd": str})
    ref_deps = ref_df[ref_df["ccdd"].isin(mapa["departamento"])].set_index("ccdd")["valor"].astype(float)
    calculada = mapa.set_index("departamento")["pobreza_pct"]
    diferencia = (calculada - ref_deps).abs()
    nom_col = "NOMBDEP" if "NOMBDEP" in mapa.columns else "nombre"
    tabla = pd.DataFrame({"departamento": mapa.set_index("departamento")[nom_col], "pobreza_pct": calculada.round(2),
                          "referencia_inei": ref_deps, "diferencia": diferencia.round(2)})
    tabla["dentro_de_tolerancia"] = tabla["diferencia"] <= TOLERANCIA
    COMPARACION.parent.mkdir(exist_ok=True)
    tabla.rename_axis("ccdd").sort_index().to_csv(COMPARACION, encoding="utf-8")
    alejados = diferencia[diferencia > TOLERANCIA]
    if not alejados.empty:
        sys.exit(f"Estos departamentos difieren más de {TOLERANCIA} puntos de la referencia del INEI: {alejados.round(2).to_dict()}.")


def dibujar_departamentos(mapa: gpd.GeoDataFrame) -> None:
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
    inset_ax.set_ylim(-13.2, -11.3)
    inset_ax.set_xticks([])
    inset_ax.set_yticks([])
    inset_ax.set_title("Detalle: Lima y Callao", fontsize=8.5, color=estilo_graficos.COLOR_TEXTO, fontweight="bold", pad=3)
    for s in inset_ax.spines.values():
        s.set_color(estilo_graficos.COLOR_LINEA_GUIA)
        s.set_linewidth(0.8)

    callao_p = mapa.loc[mapa["departamento"] == "07", "pobreza_pct"].iloc[0]
    lima_p = mapa.loc[mapa["departamento"] == "15", "pobreza_pct"].iloc[0]
    inset_ax.text(-77.15, -12.05, f"Callao\n{callao_p:.1f} %", fontsize=7.5, color="#ffffff", fontweight="bold", ha="center", va="center")
    inset_ax.text(-76.55, -11.9, f"Lima\n{lima_p:.1f} %", fontsize=7.5, color=estilo_graficos.COLOR_TEXTO, fontweight="bold", ha="center", va="center")

    nom_col = "NOMBDEP" if "NOMBDEP" in mapa.columns else "nombre"
    alto, bajo = mapa.loc[mapa["pobreza_pct"].idxmax()], mapa.loc[mapa["pobreza_pct"].idxmin()]
    titulo = "Pobreza monetaria por departamento, Perú 2024"
    subtitulo = (f"Va de {bajo['pobreza_pct']:.1f} % en {str(bajo[nom_col]).title()} a {alto['pobreza_pct']:.1f} % en "
                 f"{str(alto[nom_col]).title()}. Lima y Callao se muestran por separado.")
    fuente = "Fuente: INEI, ENAHO 2024. Límites oficiales del IGN (COD-AB, CC BY-IGO)."
    estilo_graficos.encabezado(figura, eje, titulo=titulo, subtitulo=subtitulo, fuente=fuente)

    DESTINO_DEP.parent.mkdir(exist_ok=True)
    figura.savefig(DESTINO_DEP, dpi=200, facecolor=estilo_graficos.COLOR_FONDO, metadata={"Software": None})
    plt.close(figura)


def dibujar_ambitos(mapa: gpd.GeoDataFrame) -> None:
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

    # Recuadro ampliado para Lima Metropolitana, Lima provincias y Callao
    inset_ax = eje.inset_axes([0.03, 0.15, 0.35, 0.35], facecolor="#f8fafc")
    lima_callao = mapa[mapa["codigo"].isin(["07", "1501", "15_resto"])]
    lima_callao.plot(
        column="pobreza_pct", ax=inset_ax, cmap=estilo_graficos.ESCALA_MAPA, vmin=0, vmax=45.0,
        edgecolor="#ffffff", linewidth=1.2,
    )
    inset_ax.set_xlim(-77.8, -75.8)
    inset_ax.set_ylim(-13.2, -11.3)
    inset_ax.set_xticks([])
    inset_ax.set_yticks([])
    inset_ax.set_title("Detalle: Lima y Callao", fontsize=8.5, color=estilo_graficos.COLOR_TEXTO, fontweight="bold", pad=3)
    for s in inset_ax.spines.values():
        s.set_color(estilo_graficos.COLOR_LINEA_GUIA)
        s.set_linewidth(0.8)

    callao_p = mapa.loc[mapa["codigo"] == "07", "pobreza_pct"].iloc[0]
    metro_p = mapa.loc[mapa["codigo"] == "1501", "pobreza_pct"].iloc[0]
    provs_p = mapa.loc[mapa["codigo"] == "15_resto", "pobreza_pct"].iloc[0]

    inset_ax.text(-77.15, -12.05, f"Callao\n{callao_p:.1f} %", fontsize=7.0, color="#ffffff", fontweight="bold", ha="center", va="center")
    inset_ax.text(-76.95, -12.05, f"Lima Metro\n{metro_p:.1f} %", fontsize=6.8, color="#ffffff", fontweight="bold", ha="center", va="center")
    inset_ax.text(-76.35, -11.75, f"Lima Prov.\n{provs_p:.1f} %", fontsize=6.8, color=estilo_graficos.COLOR_TEXTO, fontweight="bold", ha="center", va="center")

    titulo = "Pobreza monetaria por ámbito territorial, Perú 2024"
    subtitulo = (f"26 ámbitos oficiales del INEI: Lima Metropolitana ({metro_p:.1f} %) y Lima provincias "
                 f"({provs_p:.1f} %) analizadas por separado.")
    fuente = "Fuente: INEI, ENAHO 2024 (Cuadro III.1). Límites oficiales del IGN (COD-AB, CC BY-IGO)."
    estilo_graficos.encabezado(figura, eje, titulo=titulo, subtitulo=subtitulo, fuente=fuente)

    DESTINO_AMBITOS.parent.mkdir(exist_ok=True)
    figura.savefig(DESTINO_AMBITOS, dpi=200, facecolor=estilo_graficos.COLOR_FONDO, metadata={"Software": None})
    plt.close(figura)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    if not BASE.is_file():
        sys.exit(f"Falta {BASE.name} en salidas/. Créala con la skill limpiando-enaho.")

    ruta_geojson = ruta_geojson_departamental()
    df_base = pd.read_parquet(BASE)

    # 1. Mapa departamental (25 departamentos)
    mapa_dep = unir_con_limites(pobreza_por_departamento(df_base), gpd.read_file(ruta_geojson))
    comprobar_referencia(mapa_dep)
    dibujar_departamentos(mapa_dep)

    ordenado = mapa_dep.sort_values("pobreza_pct", ascending=False)
    extremos = pd.concat([ordenado.head(3), ordenado.tail(3)])
    nom_col = "NOMBDEP" if "NOMBDEP" in mapa_dep.columns else "nombre"
    cifras = ", ".join(f"{getattr(fila, nom_col)}: {fila.pobreza_pct:.1f} %" for fila in extremos.itertuples())
    print(f"{DESTINO_DEP.relative_to(RAIZ).as_posix()} ({DEPARTAMENTOS} departamentos con dato; {cifras})")

    # 2. Mapa por ámbitos territoriales (26 ámbitos, Lima desagregada)
    if GEOJSON_AMBITOS.is_file():
        mapa_ambitos = unir_ambitos_con_limites(pobreza_por_ambitos(df_base), gpd.read_file(GEOJSON_AMBITOS))
        dibujar_ambitos(mapa_ambitos)
        print(f"{DESTINO_AMBITOS.relative_to(RAIZ).as_posix()} ({AMBITOS} ámbitos territoriales con dato)")


if __name__ == "__main__":
    main()
