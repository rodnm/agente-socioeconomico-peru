"""Hace los mapas de pobreza de la ENAHO 2024 en mapas/ con límites oficiales del IGN.

Genera dos mapas:
  - mapas/pobreza_departamento.png: los 25 departamentos que exige la consigna, con Lima como un solo departamento.
  - mapas/pobreza_ambitos.png: los 26 ámbitos territoriales del INEI, con Lima desagregada en Lima Metropolitana y
    Lima provincias.

Los límites salen solo de referencias/ (capas del IGN preparadas con scripts/preparar_limites.py): si faltan, el
script se detiene en lugar de usar otro archivo.
"""

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as efectos
import matplotlib.pyplot as plt
import pandas as pd

RAIZ = Path(__file__).resolve().parents[4]
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))
import estilo_graficos

BASE = RAIZ / "salidas" / "personas_2024.parquet"
GEOJSON_DEP = RAIZ / "referencias" / "limites_departamentales_ign.geojson"
GEOJSON_AMBITOS = RAIZ / "referencias" / "limites_ambitos_ign.geojson"

REFERENCIA = RAIZ / "referencias" / "inei_pobreza_2024.csv"
DESTINO_DEP = RAIZ / "mapas" / "pobreza_departamento.png"
DESTINO_AMBITOS = RAIZ / "mapas" / "pobreza_ambitos.png"
COMPARACION = RAIZ / "salidas" / "mapa_vs_referencia.csv"
CONTRASTE_AMBITOS = RAIZ / "salidas" / "ambitos_vs_referencia.csv"

LLAVES_HOGAR = ["conglome", "vivienda", "hogar"]
DEPARTAMENTOS = 25
AMBITOS = 26
TOLERANCIA = 0.1
# El INEI publica Lima Metropolitana y Lima provincias por separado, no el departamento de Lima en conjunto.
SIN_CIFRA_INEI = "sin cifra publicada por el INEI"
DEPARTAMENTOS_SIN_CIFRA = {"15"}
LIMA_METROPOLITANA = "Lima Metropolitana"
LIMA_PROVINCIAS = "Lima provincias"
MARCA_REFERENCIAL = "*"
ESCALA_MAXIMA = 45.0
HALO = [efectos.withStroke(linewidth=2.6, foreground=estilo_graficos.COLOR_FONDO)]


def exigir_limites() -> None:
    """Se detiene si falta alguna capa del IGN: no hay respaldo con otros límites."""
    faltan = [ruta.name for ruta in (GEOJSON_DEP, GEOJSON_AMBITOS) if not ruta.is_file()]
    if faltan:
        sys.exit(f"Faltan los límites oficiales del IGN en referencias/: {', '.join(faltan)}. Genéralos con "
                 "`uv run scripts/preparar_limites.py` (usa el zip de OCHA HDX registrado en referencias/README.md).")


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
    """Contrasta cada departamento con las cifras oficiales del INEI y deja la tabla en salidas/.

    El departamento de Lima (15) no se compara: el INEI no publica una cifra para él en conjunto, así que la tabla
    lo declara "sin cifra publicada por el INEI". Cualquier otro departamento sin cifra detiene el proceso, porque
    indicaría una tabla de referencia incompleta.
    """
    ref_df = pd.read_csv(REFERENCIA, dtype={"ccdd": str})
    publicadas = ref_df[ref_df["ccdd"].isin(mapa["departamento"]) & ~ref_df["ccdd"].isin(DEPARTAMENTOS_SIN_CIFRA)]
    ref_deps = publicadas.set_index("ccdd")["valor"].astype(float)
    calculada = mapa.set_index("departamento")["pobreza_pct"]
    faltan = sorted(set(calculada.index) - set(ref_deps.index) - DEPARTAMENTOS_SIN_CIFRA)
    if faltan:
        sys.exit(f"La tabla del INEI ({REFERENCIA.name}) no tiene cifra para estos departamentos: {faltan}.")
    diferencia = (calculada - ref_deps).abs()
    nom_col = "NOMBDEP" if "NOMBDEP" in mapa.columns else "nombre"
    tabla = pd.DataFrame({"departamento": mapa.set_index("departamento")[nom_col], "pobreza_pct": calculada.round(2),
                          "referencia_inei": ref_deps, "diferencia": diferencia.round(2)})
    tabla["dentro_de_tolerancia"] = (tabla["diferencia"] <= TOLERANCIA).where(tabla["referencia_inei"].notna())
    tabla["observacion"] = tabla["referencia_inei"].isna().map({True: SIN_CIFRA_INEI, False: ""})
    COMPARACION.parent.mkdir(exist_ok=True)
    tabla.rename_axis("ccdd").sort_index().to_csv(COMPARACION, encoding="utf-8")
    alejados = diferencia[diferencia > TOLERANCIA]
    if not alejados.empty:
        sys.exit(f"Estos departamentos difieren más de {TOLERANCIA} puntos de la referencia del INEI: {alejados.round(2).to_dict()}.")


def comprobar_ambitos(mapa: gpd.GeoDataFrame) -> None:
    """Contrasta los 26 ámbitos con el Cuadro III.1 del INEI, que publica Lima Metropolitana (1501) y Lima provincias
    por separado, y deja en salidas/ la tabla con el intervalo de confianza al 95 % y el coeficiente de variación
    publicados. Un ámbito sin cifra del INEI detiene el proceso antes de escribir; uno fuera de la tolerancia, después,
    para poder revisar la tabla."""
    ref = pd.read_csv(REFERENCIA, dtype={"ccdd": str}).dropna(subset=["ccdd"]).set_index("ccdd")
    calculada = mapa.set_index("codigo")["pobreza_pct"].sort_index()
    faltan = sorted(set(calculada.index) - set(ref.index))
    if faltan:
        sys.exit(f"La tabla del INEI ({REFERENCIA.name}) no tiene cifra para estos ámbitos: {faltan}.")
    ref = ref.loc[calculada.index]
    diferencia = (calculada - ref["valor"]).abs()
    marcados = {codigo for codigo, _ in referenciales()}
    tabla = pd.DataFrame({"ambito": ref["ambito"], "pobreza_pct": calculada.round(2), "referencia_inei": ref["valor"],
                          "ic_inf": ref["ic_inf"], "ic_sup": ref["ic_sup"], "cv": ref["cv"],
                          "referencial": calculada.index.isin(list(marcados)), "diferencia": diferencia.round(2)})
    tabla["dentro_de_tolerancia"] = tabla["diferencia"] <= TOLERANCIA
    CONTRASTE_AMBITOS.parent.mkdir(exist_ok=True)
    tabla.rename_axis("codigo").to_csv(CONTRASTE_AMBITOS, encoding="utf-8")
    alejados = diferencia[diferencia > TOLERANCIA]
    if not alejados.empty:
        sys.exit(f"Estos ámbitos difieren más de {TOLERANCIA} puntos de la referencia del INEI: {alejados.round(2).to_dict()}.")


def referenciales() -> list[tuple[str, str]]:
    """(código, nombre) de los ámbitos que el INEI publica como referenciales: CV > 15 % o nota "referencial"."""
    tabla = pd.read_csv(REFERENCIA, dtype={"ccdd": str}).dropna(subset=["ccdd"])
    marcadas = (pd.to_numeric(tabla["cv"], errors="coerce") > 15) | tabla["nota"].fillna("").str.contains("referencial")
    return sorted(zip(tabla.loc[marcadas, "ccdd"], tabla.loc[marcadas, "ambito"]), key=lambda par: par[1])


def nota_referenciales(nombres: list[str]) -> str:
    lista = f"{', '.join(nombres[:-1])} y {nombres[-1]}" if len(nombres) > 1 else "".join(nombres)
    return (f"{MARCA_REFERENCIAL} Cifra referencial: el INEI informa un coeficiente de variación mayor que 15 % para "
            f"{lista}, por lo que su estimación es menos precisa.")


def _mapa_base(mapa: gpd.GeoDataFrame):
    """Figura con el mapa coropleta y su barra de colores (0 a 45 % o más)."""
    figura, eje = plt.subplots(figsize=(7.6, 9.0), facecolor=estilo_graficos.COLOR_FONDO)
    eje.set_facecolor(estilo_graficos.COLOR_FONDO)
    mapa.plot(
        column="pobreza_pct", ax=eje, cmap=estilo_graficos.ESCALA_MAPA, vmin=0, vmax=ESCALA_MAXIMA,
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
    return figura, eje


def _recuadro_lima(eje, partes: gpd.GeoDataFrame, rotulos: list[tuple[str, float, tuple, bool]]) -> None:
    """Recuadro ampliado de Lima y Callao, con cada rótulo en tinta oscura y halo claro.

    rotulos: (nombre, valor, posición del texto en grados, si lleva guía hasta su polígono). Los rótulos con guía
    van sobre el mar, donde no tapan ningún polígono. Los ejes no llevan rótulos: geopandas los pone en inglés.
    """
    recuadro = eje.inset_axes([-0.15, 0.06, 0.36, 0.36], facecolor="#f8fafc")  # sobre el mar, sin tapar el mapa
    partes.plot(column="pobreza_pct", ax=recuadro, cmap=estilo_graficos.ESCALA_MAPA, vmin=0, vmax=ESCALA_MAXIMA,
                edgecolor="#ffffff", linewidth=1.2)
    recuadro.set_xlim(-77.8, -75.8)
    recuadro.set_ylim(-13.2, -11.3)
    recuadro.set_xticks([])
    recuadro.set_yticks([])
    recuadro.set_xlabel("")
    recuadro.set_ylabel("")
    recuadro.set_title("Detalle: Lima y Callao", fontsize=8.5, color=estilo_graficos.COLOR_TEXTO, fontweight="bold",
                       pad=3)
    for borde in recuadro.spines.values():
        borde.set_color(estilo_graficos.COLOR_LINEA_GUIA)
        borde.set_linewidth(0.8)

    for (nombre, valor, posicion, con_guia), punto in zip(rotulos, partes.geometry.representative_point()):
        guia = {"arrowstyle": "-", "color": estilo_graficos.COLOR_TEXTO, "linewidth": 0.7, "shrinkA": 2,
                "shrinkB": 1} if con_guia else None
        recuadro.annotate(f"{nombre}\n{valor:.1f} %", xy=(punto.x, punto.y), xytext=posicion, textcoords="data",
                          ha="left" if con_guia else "center", va="center", fontsize=7.5, fontweight="bold",
                          color=estilo_graficos.COLOR_TEXTO, path_effects=HALO, arrowprops=guia)


def _guardar(figura, destino: Path) -> None:
    destino.parent.mkdir(exist_ok=True)
    figura.savefig(destino, dpi=200, facecolor=estilo_graficos.COLOR_FONDO, metadata={"Software": None})
    plt.close(figura)


def dibujar_departamentos(mapa: gpd.GeoDataFrame) -> None:
    figura, eje = _mapa_base(mapa)
    por_codigo = mapa.set_index("departamento")
    partes = mapa[mapa["departamento"].isin(["07", "15"])].set_index("departamento").loc[["07", "15"]]
    _recuadro_lima(eje, partes, [
        ("Callao", por_codigo.loc["07", "pobreza_pct"], (-77.74, -11.6), True),
        ("Lima", por_codigo.loc["15", "pobreza_pct"], (-76.3, -12.6), False),
    ])

    nom_col = "NOMBDEP" if "NOMBDEP" in mapa.columns else "nombre"
    alto, bajo = mapa.loc[mapa["pobreza_pct"].idxmax()], mapa.loc[mapa["pobreza_pct"].idxmin()]
    titulo = "Pobreza monetaria por departamento, Perú 2024"
    subtitulo = (f"Mapa que exige la consigna: 25 departamentos, con Lima como un solo departamento y Callao por "
                 f"separado. Va de {bajo['pobreza_pct']:.1f} % en {str(bajo[nom_col]).title()} a "
                 f"{alto['pobreza_pct']:.1f} % en {str(alto[nom_col]).title()}.")
    fuente = ("Fuente: INEI, ENAHO 2024. Límites oficiales del IGN (COD-AB, CC BY-IGO).\n"
              f"La cifra del departamento de Lima es un cálculo propio con los microdatos: el INEI publica "
              f"{LIMA_METROPOLITANA} y {LIMA_PROVINCIAS} por separado.")
    estilo_graficos.encabezado(figura, eje, titulo=titulo, subtitulo=subtitulo, fuente=fuente)
    _guardar(figura, DESTINO_DEP)


def dibujar_ambitos(mapa: gpd.GeoDataFrame) -> None:
    figura, eje = _mapa_base(mapa)
    por_codigo = mapa.set_index("codigo")
    partes = mapa[mapa["codigo"].isin(["07", "1501", "15_resto"])].set_index("codigo").loc[["07", "1501", "15_resto"]]
    metro_p, provs_p = por_codigo.loc["1501", "pobreza_pct"], por_codigo.loc["15_resto", "pobreza_pct"]
    _recuadro_lima(eje, partes, [
        ("Callao", por_codigo.loc["07", "pobreza_pct"], (-77.74, -11.6), True),
        (LIMA_METROPOLITANA, metro_p, (-77.74, -12.85), True),
        (LIMA_PROVINCIAS, provs_p, (-76.2, -12.4), False),
    ])

    # Marca de las cifras referenciales del INEI sobre su ámbito, explicada en la nota al pie.
    marcados = [(c, n) for c, n in referenciales() if c in por_codigo.index]
    for codigo, _ in marcados:
        punto = por_codigo.loc[codigo, "geometry"].representative_point()
        eje.text(punto.x, punto.y, MARCA_REFERENCIAL, ha="center", va="center", fontsize=14, fontweight="bold",
                 color=estilo_graficos.COLOR_TEXTO, path_effects=HALO)

    titulo = "Pobreza monetaria por ámbito territorial, Perú 2024"
    subtitulo = (f"26 ámbitos del INEI, con Lima desagregada: {LIMA_METROPOLITANA} ({metro_p:.1f} %) y "
                 f"{LIMA_PROVINCIAS} ({provs_p:.1f} %) se analizan por separado.")
    fuente = ("Fuente: elaboración propia con microdatos de la ENAHO 2024 (INEI), contrastada con el Cuadro III.1 del informe "
              "técnico del INEI. Límites oficiales del IGN (COD-AB, CC BY-IGO).")
    if marcados:
        fuente += "\n" + nota_referenciales([n for _, n in marcados])
    estilo_graficos.encabezado(figura, eje, titulo=titulo, subtitulo=subtitulo, fuente=fuente)
    _guardar(figura, DESTINO_AMBITOS)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    if not BASE.is_file():
        sys.exit(f"Falta {BASE.name} en salidas/. Créala con la skill limpiando-enaho.")
    exigir_limites()
    df_base = pd.read_parquet(BASE)

    # 1. Mapa departamental (25 departamentos), el que exige la consigna
    mapa_dep = unir_con_limites(pobreza_por_departamento(df_base), gpd.read_file(GEOJSON_DEP))
    comprobar_referencia(mapa_dep)
    dibujar_departamentos(mapa_dep)

    ordenado = mapa_dep.sort_values("pobreza_pct", ascending=False)
    extremos = pd.concat([ordenado.head(3), ordenado.tail(3)])
    nom_col = "NOMBDEP" if "NOMBDEP" in mapa_dep.columns else "nombre"
    cifras = ", ".join(f"{getattr(fila, nom_col)}: {fila.pobreza_pct:.1f} %" for fila in extremos.itertuples())
    print(f"{DESTINO_DEP.relative_to(RAIZ).as_posix()} ({DEPARTAMENTOS} departamentos con dato; {cifras})")

    # 2. Mapa por ámbitos territoriales (26 ámbitos, Lima desagregada), el del análisis
    mapa_ambitos = unir_ambitos_con_limites(pobreza_por_ambitos(df_base), gpd.read_file(GEOJSON_AMBITOS))
    comprobar_ambitos(mapa_ambitos)
    dibujar_ambitos(mapa_ambitos)
    print(f"{DESTINO_AMBITOS.relative_to(RAIZ).as_posix()} ({AMBITOS} ámbitos territoriales con dato)")


if __name__ == "__main__":
    main()
