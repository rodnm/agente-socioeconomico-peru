"""Datos y figuras del dashboard, aparte de Streamlit para poder probarlos.

Solo lee las salidas versionadas que dejan las herramientas del agente (salidas/ y evaluacion/): ninguna cifra se
escribe a mano ni se recalcula aquí. Las únicas cuentas son de presentación: la variación de un indicador frente al año
anterior y los conteos de la leyenda y del contraste. Las salidas opcionales que aún no existen se leen como tablas
vacías.
"""
import json
import unicodedata
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

RAIZ = Path(__file__).resolve().parents[1]
INDICADORES = RAIZ / "salidas" / "indicadores.csv"
CONTRASTE = RAIZ / "salidas" / "ambitos_vs_referencia.csv"
CONSISTENCIA = RAIZ / "salidas" / "consistencia.csv"
BCRP = RAIZ / "salidas" / "bcrp"
RESULTADOS = RAIZ / "evaluacion" / "resultados.csv"
ROBUSTEZ = RAIZ / "evaluacion" / "robustez_resultados.csv"
# Límites oficiales del IGN (COD-AB, OCHA HDX), versionados; los genera scripts/preparar_limites.py. Nunca se descargan.
GEOJSON_AMBITOS = RAIZ / "referencias" / "limites_ambitos_ign.geojson"
PREPARAR_LIMITES = "uv run scripts/preparar_limites.py"
MAPEAR = "uv run .claude/skills/mapeando-enaho/scripts/mapear.py"

# El análisis territorial usa los 26 ámbitos del Cuadro III.1 del INEI: Lima (15) se desagrega en Lima Metropolitana
# (provincia 1501) y Lima provincias, cada una con el código de la propiedad `codigo` de la capa de ámbitos. Se eligen
# por id, nunca por la etiqueta: pobreza_lima_metropolitana (dominio 8, con el Callao) no es un ámbito.
AMBITOS = 26
LIMA_DESAGREGADA = {"pobreza_lima_metropolitana_provincia": "1501", "pobreza_lima_provincias": "15_resto"}
LIMA_DEPARTAMENTO = "pobreza_dep_15"
# Las barras oscuras del ranking: Lima Metropolitana, Lima provincias y el Callao
LIMA_Y_CALLAO = {"1501", "15_resto", "07"}
# Una salida sin columna `anio` es de antes de la serie 2020-2024, cuando solo se procesaba 2024
ANIO_UNICO = 2024
# mapeando-enaho contrasta la ENAHO 2024 con el informe del INEI sobre 2024, con esta tolerancia en puntos: la réplica
# de una cifra que el INEI redondea a un decimal
ANIO_CONTRASTE, TOLERANCIA = 2024, 0.1

COLUMNAS_EVALUACION = ["id", "tipo", "modo", "pregunta", "verdad", "valor", "unidad", "tolerancia", "resultado",
                       "segundos", "turnos", "herramientas", "fuente", "error"]
COLUMNAS_ROBUSTEZ = ["id", "modo", "pedido", "conducta_esperada", "conducta_observada", "resultado", "segundos"]
COLUMNAS_CONSISTENCIA = ["fuente", "verificacion", "resultado", "detalle", "explicacion"]
COLUMNAS_CONTRASTE = ["codigo", "ambito", "pobreza_pct", "referencia_inei", "ic_inf", "ic_sup", "cv", "referencial",
                      "diferencia", "dentro_de_tolerancia"]
COLUMNAS_BCRP = ["archivo", "periodo", "fecha", "valor", "codigo", "nombre", "fuente"]

# Las configuraciones de evaluacion/evaluar.py, en el orden en que se comparan
MODOS = {"A": "A: herramientas estándar", "B": "B: con MCP y skills", "memoria": "Sin herramientas",
         "solo-mcp": "Solo MCP", "solo-skills": "Solo skills", "sin-propia": "B sin comparar_series"}
TIPOS = ["bcrp", "enaho", "mixta"]
KPIS = {"pobreza_nacional": "Pobreza monetaria nacional", "pobreza_area_urbana": "Pobreza urbana",
        "pobreza_area_rural": "Pobreza rural", "pobreza_extrema": "Pobreza extrema",
        "residentes_habituales": "Residentes en la muestra"}
ESTADOS = ["OK", "DIFERENCIA", "FALLA", "NO VERIFICABLE"]

# Paleta tierra del sistema visual, la misma de .streamlit/config.toml: los datos van de arena a terracota según la
# tasa y la interfaz usa neutros cálidos, para que el color solo signifique datos. Contraste revisado con WCAG: el texto
# llega a 4.5:1 y las barras y marcas a 3:1 sobre blanco.
TINTA, TEXTO_SECUNDARIO, TEXTO_ATENUADO = "#221D19", "#4A423B", "#6A6058"
FONDO, SUPERFICIE, BORDE, BORDE_CAMPO, ACENTO = "#F6F3EE", "#FFFFFF", "#E4DDD3", "#9A8F84", "#9A4317"
BARRA, BARRA_LIMA, REPLICA, INTERVALO = "#C46A35", "#6E2A0F", "#C0562A", "#F2D6BC"
REFERENCIA = TINTA
# Clases de pobreza del mapa y de su leyenda: (límite superior sin incluir, color, etiqueta)
CLASES = [(15, "#F6DDB8", "< 15 %"), (22, "#EDB27A", "15 a 22 %"), (28, "#DB8448", "22 a 28 %"),
          (35, "#B95A26", "28 a 35 %"), (float("inf"), "#7F3212", "35 % o más")]
# Escala fija de 0 a 50 % en todas las vistas de pobreza, para que se comparen entre sí
ESCALA = 50
# El mapa y el ranking van lado a lado con la misma altura
ALTO_TERRITORIAL = 700
MARCA_REFERENCIAL = " †"
NOTA_REFERENCIAL = "† Cifra referencial: el INEI informa un coeficiente de variación mayor que 15 %."
# Estados de Evaluación, Consistencia y del contraste: ícono y texto, nunca solo color, con fondo claro y texto oscuro
ESTILOS_ESTADO = {"coincide": ("#E3F1E7", "#1D5B33", "✓"), "diferencia": ("#FCF0D6", "#6E4500", "!"),
                  "falla": ("#FBE2DF", "#8A1F17", "✕"), "no verificable": ("#EEEAE4", "#4A423B", "–")}
ESTADO_DE = {"OK": "coincide", "acierta": "coincide", "cumple": "coincide", "Coincide": "coincide",
             "DIFERENCIA": "diferencia", "no sabe": "diferencia",
             "FALLA": "falla", "se equivoca": "falla", "no cumple": "falla", "Fuera de tolerancia": "falla",
             "NO VERIFICABLE": "no verificable", "error": "no verificable"}
ICONOS_ESTADO = {"OK": ":material/check_circle:", "DIFERENCIA": ":material/error:", "FALLA": ":material/cancel:",
                 "NO VERIFICABLE": ":material/remove_circle:"}
VISTAS_CONTRASTE = {"todos": "Todos", "fuera": "Fuera de tolerancia", "referenciales": "Referenciales"}
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


# ---------- lectura ----------

def _leer(ruta: Path, columnas: list[str], **opciones) -> pd.DataFrame:
    """Una salida: si todavía no existe o está vacía, una tabla vacía con sus columnas, no un error."""
    try:
        return pd.read_csv(ruta, encoding="utf-8", **opciones)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=columnas)


def huella(ruta: Path):
    """Cambia cuando el agente reescribe una salida, para que la caché del dashboard la vuelva a leer."""
    if ruta.is_dir():
        return tuple((r.name, r.stat().st_mtime_ns) for r in sorted(ruta.glob("*.csv")))
    return ruta.stat().st_mtime_ns if ruta.exists() else 0


def del_anio(ind: pd.DataFrame, anio: int | None) -> pd.DataFrame:
    """Los indicadores de un año. Una salida sin columna `anio` es de un solo año y se devuelve completa."""
    if "anio" in ind.columns and anio is not None:
        return ind[ind["anio"] == anio].reset_index(drop=True)
    return ind


def anios(ind: pd.DataFrame) -> list[int]:
    """Los años de la encuesta presentes, en orden."""
    if "anio" not in ind.columns:
        return [ANIO_UNICO]
    return sorted(int(a) for a in ind["anio"].dropna().unique())


def cargar_indicadores(ruta: Path = INDICADORES, anio: int | None = 2024) -> pd.DataFrame:
    """Los indicadores del año dado (2024 por defecto; todos con None)."""
    df = _leer(ruta, ["anio", "id", "indicador", "grupo", "valor", "unidad", "ponderador", "n_muestral", "fuente"],
               dtype={"id": str})
    return del_anio(df, anio)


def cargar_contraste(ruta: Path = CONTRASTE) -> pd.DataFrame:
    tabla = _leer(ruta, COLUMNAS_CONTRASTE, dtype={"codigo": str})
    for columna in ("referencial", "dentro_de_tolerancia"):
        tabla[columna] = tabla[columna].astype(str).str.strip().str.lower().eq("true")
    return tabla


def cargar_consistencia(ruta: Path = CONSISTENCIA) -> pd.DataFrame:
    return _leer(ruta, COLUMNAS_CONSISTENCIA, dtype=str, keep_default_na=False)


def cargar_evaluacion(ruta: Path = RESULTADOS) -> pd.DataFrame:
    return _leer(ruta, COLUMNAS_EVALUACION, dtype={"id": str, "modo": str, "tipo": str})


def cargar_robustez(ruta: Path = ROBUSTEZ) -> pd.DataFrame:
    return _leer(ruta, COLUMNAS_ROBUSTEZ, dtype={"id": str, "modo": str})


def _relativa(ruta: Path) -> str:
    try:
        return ruta.relative_to(RAIZ).as_posix()
    except ValueError:
        return ruta.as_posix()


def _area_con_signo(anillo: list) -> float:
    """Positiva si el anillo gira en sentido antihorario (fórmula del área de Gauss)."""
    return sum(x0 * y1 - x1 * y0 for (x0, y0, *_), (x1, y1, *_) in zip(anillo, anillo[1:]))


def _en_sentido(anillo: list, horario: bool) -> list:
    return anillo[::-1] if (_area_con_signo(anillo) > 0) == horario else anillo


def orientar_para_plotly(geo: dict) -> dict:
    """Una copia con los anillos exteriores en sentido horario y los huecos en antihorario, como los lee d3-geo, el
    motor de mapas de Plotly. Con el sentido de RFC 7946, el del archivo, d3-geo dibuja cada ámbito como el globo menos
    el polígono y el último en dibujarse tapa el resto."""
    def poligono(anillos: list) -> list:
        exterior, *huecos = anillos
        return [_en_sentido(exterior, horario=True)] + [_en_sentido(h, horario=False) for h in huecos]

    def geometria(g: dict) -> dict:
        if g["type"] == "Polygon":
            return {**g, "coordinates": poligono(g["coordinates"])}
        if g["type"] == "MultiPolygon":
            return {**g, "coordinates": [poligono(p) for p in g["coordinates"]]}
        return g

    return {**geo, "features": [{**f, "geometry": geometria(f["geometry"])} for f in geo["features"]]}


def cargar_geojson(ruta: Path = GEOJSON_AMBITOS) -> tuple[dict | None, str | None]:
    """Los límites del IGN versionados en referencias/, orientados para Plotly. Nunca descarga nada ni lanza error: si
    el archivo falta o no se puede leer, devuelve el aviso para mostrar y el resto del tablero sigue."""
    try:
        return orientar_para_plotly(json.loads(ruta.read_text(encoding="utf-8"))), None
    except FileNotFoundError:
        return None, (f"Falta `{_relativa(ruta)}`, con los límites oficiales del IGN. Se genera con "
                      f"`{PREPARAR_LIMITES}`. El mapa se omite.")
    except (OSError, ValueError) as error:
        return None, (f"No se pudo leer `{_relativa(ruta)}` ({error}). Se vuelve a generar con "
                      f"`{PREPARAR_LIMITES}`. El mapa se omite.")


# ---------- ENAHO ----------

def filas(ind: pd.DataFrame, prefijo: str) -> pd.DataFrame:
    """Los indicadores de un desglose (pobreza_area_, pobreza_sexo_, pobreza_edad_, pobreza_dep_), en su orden."""
    return ind[ind["id"].str.startswith(prefijo)].assign(valor=lambda t: t["valor"].astype(float),
                                                         nombre=lambda t: t["grupo"])


def tabla_ambitos(ind: pd.DataFrame) -> pd.DataFrame:
    """Los 26 ámbitos del análisis territorial: 24 departamentos, el Callao (07), Lima Metropolitana (1501) y Lima
    provincias (15_resto), con el código de la capa de ámbitos del IGN. El departamento 15 en conjunto queda fuera.
    Si la salida no trae a Lima desagregada (anterior a ese cambio), lo dice en lugar de mostrar 24 ámbitos."""
    elegidas = ind[(ind["id"].str.startswith("pobreza_dep_") & (ind["id"] != LIMA_DEPARTAMENTO)) |
                   ind["id"].isin(list(LIMA_DESAGREGADA))]
    codigo = elegidas["id"].map(LIMA_DESAGREGADA).fillna(elegidas["id"].str.removeprefix("pobreza_dep_"))
    tabla = pd.DataFrame({"codigo": codigo, "nombre": elegidas["grupo"], "pobreza": elegidas["valor"].astype(float),
                          "ponderador": elegidas["ponderador"]}).sort_values("codigo").reset_index(drop=True)
    if len(tabla) != AMBITOS or tabla["codigo"].duplicated().any():
        raise ValueError(f"Se esperaban {AMBITOS} ámbitos, con Lima desagregada en Lima Metropolitana y Lima "
                         f"provincias; `salidas/indicadores.csv` trae {len(tabla)}. Se regenera con la skill "
                         "limpiando-enaho.")
    return tabla


def nacional(ind: pd.DataFrame, ponderador: str) -> float | None:
    """La pobreza nacional ponderada igual que el desglose: por hogar para área y departamento, por persona para
    sexo y edad. Así la línea de referencia es comparable con las barras."""
    fila = ind[(ind["grupo"] == "Nacional") & (ind["indicador"] == "Pobreza monetaria") & (ind["ponderador"] == ponderador)]
    return float(fila["valor"].iat[0]) if len(fila) else None


def ponderado_por(ponderador: str) -> str:
    """«factor07 × mieperho (por hogar)» se lee «Ponderado por hogar»."""
    unidad = ponderador.partition("(")[2].rstrip(")")
    return f"Ponderado {unidad}" if unidad else f"Ponderado con {ponderador}"


def kpis(ind: pd.DataFrame, historia: pd.DataFrame | None = None) -> list[dict]:
    """Las cifras de cabecera del año de `ind`, cada una con su id, ponderador, tamaño de muestra y fuente para citarla.
    Con la historia de todos los años, también su serie desde el primer año y, en las tasas, la variación en puntos
    frente al año anterior que haya."""
    anio = int(ind["anio"].iat[0]) if "anio" in ind.columns and len(ind) else None
    con_historia = historia is not None and anio is not None and "anio" in historia.columns
    tarjetas = []
    for clave, etiqueta in KPIS.items():
        fila = ind[ind["id"] == clave]
        if fila.empty:
            continue
        f = fila.iloc[0]
        tasa = str(f["unidad"]).startswith("%")
        tarjeta = {"id": clave, "etiqueta": etiqueta, "valor": f"{f['valor']:.1f} %" if tasa else _miles(f["valor"]),
                   "ayuda": f"`{clave}` · {f['unidad']} · ponderado: {f['ponderador']} · "
                            f"n muestral {_miles(f['n_muestral'])} · {f['fuente']}",
                   "serie": None, "variacion": None, "detalle": None}
        if con_historia:
            serie = historia[(historia["id"] == clave) & (historia["anio"] <= anio)].sort_values("anio")
            if len(serie) > 1:
                tarjeta["serie"] = serie["valor"].astype(float).tolist()
                if tasa:
                    previo = serie.iloc[-2]
                    tarjeta["variacion"] = f"{float(f['valor']) - float(previo['valor']):+.1f} pp"
                    tarjeta["detalle"] = f"frente a {int(previo['anio'])}"
        if not tasa:
            hogares = ind.loc[ind["id"] == "hogares", "valor"]
            tarjeta["variacion"] = f"{_miles(hogares.iat[0])} hogares encuestados" if len(hogares) else None
        tarjetas.append(tarjeta)
    return tarjetas


def _miles(numero: float) -> str:
    return f"{numero:,.0f}".replace(",", " ")


def resumen_pobreza(ind: pd.DataFrame, ambitos: pd.DataFrame, anio: int) -> str:
    """La frase de entrada de la página, con la tasa nacional y los ámbitos extremos del año."""
    orden = ambitos.sort_values("pobreza")
    bajo, alto = orden.iloc[0], orden.iloc[-1]
    tasa = ind.loc[ind["id"] == "pobreza_nacional", "valor"]
    texto = f"En {anio}, el {float(tasa.iat[0]):.1f} % de las personas vivía en pobreza monetaria. " if len(tasa) else ""
    return (texto + f"Entre ámbitos, la tasa va de {bajo['pobreza']:.1f} % en {bajo['nombre']} a "
                    f"{alto['pobreza']:.1f} % en {alto['nombre']}.")


def pie_enaho(ind: pd.DataFrame, anio: int) -> str:
    """La única nota de fuente de la sección, con el ponderador que trae la salida para cada desglose."""
    por_ponderador = {}
    for nombre, prefijo in (("área", "pobreza_area_"), ("ámbito", "pobreza_dep_"), ("sexo", "pobreza_sexo_"),
                            ("edad", "pobreza_edad_")):
        ponderador = ind.loc[ind["id"].str.startswith(prefijo), "ponderador"]
        if len(ponderador):
            por_ponderador.setdefault(ponderador.iat[0], []).append(nombre)
    ponderacion = "; ".join(f"{' y '.join(nombres)} con {p}" for p, nombres in por_ponderador.items())
    return (f"Fuente: INEI, Encuesta Nacional de Hogares (ENAHO) {anio}, módulos 34 y 02, procesados con la skill "
            f"limpiando-enaho. Ponderación: {ponderacion}. Límites: IGN, publicados en OCHA HDX (COD-AB). "
            "Datos: `salidas/indicadores.csv`.")


def unir_geometria(geo: dict, ambitos: pd.DataFrame) -> pd.DataFrame:
    """Une por código (propiedad `codigo` de la capa de ámbitos del IGN con el de tabla_ambitos), nunca por nombre, y
    exige los 26."""
    limites = pd.DataFrame({"codigo": [str(f["properties"].get("codigo", "")).zfill(2) for f in geo["features"]],
                            "nombre_mapa": [f["properties"].get("nombre", "") for f in geo["features"]]})
    unida = limites.merge(ambitos, on="codigo", how="outer", indicator=True)
    sueltos = sorted(unida.loc[unida["_merge"] != "both", "codigo"])
    if sueltos or len(unida) != AMBITOS or unida["codigo"].duplicated().any():
        raise ValueError(f"Se esperaban {AMBITOS} ámbitos unidos por código; se unieron "
                         f"{(unida['_merge'] == 'both').sum()}. Códigos sin pareja: {sueltos}.")
    return unida.drop(columns="_merge").sort_values("codigo").reset_index(drop=True)


def clase(valor: float) -> int:
    """La clase del mapa de una tasa: 0 para menos de 15 %, 4 para 35 % o más."""
    return next(i for i, (tope, _, _) in enumerate(CLASES) if valor < tope)


def leyenda_clases(ambitos: pd.DataFrame) -> list[dict]:
    """Cada clase del mapa con su color, su rango y cuántos ámbitos caen en ella."""
    cuenta = ambitos["pobreza"].map(clase).value_counts()
    return [{"color": color, "etiqueta": etiqueta, "ambitos": int(cuenta.get(i, 0))}
            for i, (_, color, etiqueta) in enumerate(CLASES)]


def leyenda_html(leyenda: list[dict]) -> str:
    muestras = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:6px;margin-right:16px;font-size:13px;'
        f'color:{TEXTO_SECUNDARIO}"><span style="width:12px;height:12px;border-radius:2px;background:{c["color"]};'
        f'box-shadow:inset 0 0 0 1px {BORDE_CAMPO}"></span>{c["etiqueta"]} · {c["ambitos"]} '
        f'{"ámbito" if c["ambitos"] == 1 else "ámbitos"}</span>' for c in leyenda)
    return f'<div style="display:flex;flex-wrap:wrap;row-gap:6px">{muestras}</div>'


def _tope(valores: pd.Series) -> float:
    return max(ESCALA, float(valores.max()))


def _escala_por_clases(tope: float) -> list:
    """Escala de colores en escalones: cada clase tiene un solo color entre sus límites, de 0 al tope."""
    cortes = [0] + [limite for limite, _, _ in CLASES[:-1]] + [tope]
    escala = []
    for desde, hasta, (_, color, _) in zip(cortes, cortes[1:], CLASES):
        escala += [[desde / tope, color], [hasta / tope, color]]
    return escala


def _lienzo(figura: go.Figure, alto: int, **diseno) -> go.Figure:
    """Lo común a todas las figuras: sin título, que va en la tarjeta; punto decimal y espacio de miles, como el resto
    del proyecto; fondo transparente sobre la tarjeta y texto en los tonos de la paleta."""
    figura.update_layout(**{"height": alto, "separators": ". ", "showlegend": False,
                            "paper_bgcolor": "rgba(0,0,0,0)", "plot_bgcolor": "rgba(0,0,0,0)",
                            "font": {"color": TEXTO_SECUNDARIO}, "margin": {"l": 0, "r": 24, "t": 28, "b": 0},
                            **diseno})
    return figura


def _eje_de_pobreza(figura: go.Figure, tope: float, desde: float = 0, cifras: bool = False) -> None:
    """El eje de 0 al tope (50 %); con `cifras`, deja a la derecha una columna para el valor de cada barra."""
    figura.update_xaxes(range=[desde, tope * (1.16 if cifras else 1.06)], tickvals=list(range(0, int(tope) + 1, 10)),
                        title="% de personas", gridcolor=BORDE, zeroline=False)
    figura.update_yaxes(title=None, autorange="reversed")


def _cifras(figura: go.Figure, y: list, valores: pd.Series, tope: float) -> None:
    """El valor de cada barra en una columna alineada a la derecha, lejos de la línea nacional que lo taparía."""
    figura.add_scatter(x=[tope * 1.16] * len(valores), y=y, mode="text", name="cifras", hoverinfo="skip",
                       text=[f"{v:.1f}" for v in valores], textposition="middle left", cliponaxis=False,
                       textfont={"color": TINTA})


def _linea_nacional(figura: go.Figure, valor: float) -> None:
    """La referencia nacional: línea punteada en tinta sobre un borde blanco, para que se lea sobre las barras
    oscuras. El rótulo va en el margen superior, sobre el área de barras, para no cruzar la primera."""
    figura.add_vline(x=valor, line_color=SUPERFICIE, line_width=4.5, layer="above")
    figura.add_vline(x=valor, line_dash="dash", line_color=REFERENCIA, line_width=1.5, layer="above",
                     annotation_text=f"Nacional: {valor:.1f} %", annotation_position="top right", annotation_xshift=4,
                     annotation_yanchor="bottom", annotation_font_color=TINTA)


def _encuadre(geo: dict, margen: float = 0.3) -> tuple[list[float], list[float]]:
    """Longitudes y latitudes extremas de la capa: el cuadro del mapa toma su proporción, no la 2:1 del mundo, y el
    Perú llena la tarjeta."""
    puntos = [punto for f in geo["features"]
              for anillos in ([f["geometry"]["coordinates"]] if f["geometry"]["type"] == "Polygon"
                              else f["geometry"]["coordinates"])
              for anillo in anillos for punto in anillo]
    lon, lat = [p[0] for p in puntos], [p[1] for p in puntos]
    return [min(lon) - margen, max(lon) + margen], [min(lat) - margen, max(lat) + margen]


def figura_mapa(unida: pd.DataFrame, geo: dict) -> go.Figure:
    tope = _tope(unida["pobreza"])
    figura = px.choropleth(unida, geojson=geo, locations="codigo", featureidkey="properties.codigo", color="pobreza",
                           color_continuous_scale=_escala_por_clases(tope), range_color=(0, tope),
                           hover_name="nombre", hover_data={"codigo": True, "pobreza": ":.1f"},
                           labels={"pobreza": "% de personas", "codigo": "Código"})
    longitudes, latitudes = _encuadre(geo)
    figura.update_geos(visible=False, bgcolor="rgba(0,0,0,0)", lonaxis_range=longitudes, lataxis_range=latitudes)
    figura.update_traces(marker_line_color=SUPERFICIE, marker_line_width=0.8, name="mapa_ambitos")
    return _lienzo(figura, ALTO_TERRITORIAL, coloraxis_showscale=False, margin={"l": 0, "r": 0, "t": 0, "b": 0})


def figura_ranking(ambitos: pd.DataFrame, referencia: float | None = None,
                   referenciales: frozenset[str] = frozenset()) -> go.Figure:
    """Los ámbitos de mayor a menor pobreza. La barra oscura marca Lima y el Callao, el cuadrado repite la clase del
    mapa y † marca las cifras que el INEI publica como referenciales."""
    tabla = ambitos.sort_values("pobreza", ascending=False)
    nombres = (tabla["nombre"] + tabla["codigo"].isin(referenciales).map({True: MARCA_REFERENCIAL, False: ""})).tolist()
    tope = _tope(tabla["pobreza"])
    figura = go.Figure(go.Bar(x=tabla["pobreza"], y=nombres, orientation="h", name="ranking_ambitos",
                              marker_color=tabla["codigo"].isin(LIMA_Y_CALLAO).map({True: BARRA_LIMA, False: BARRA}).tolist(),
                              hovertemplate="%{y}: %{x:.1f} %<extra></extra>"))
    figura.add_scatter(x=[-0.04 * tope] * len(tabla), y=nombres, mode="markers", name="clase", hoverinfo="skip",
                       marker={"symbol": "square", "size": 10, "line": {"color": BORDE_CAMPO, "width": 0.5},
                               "color": [CLASES[clase(v)][1] for v in tabla["pobreza"]]})
    _cifras(figura, nombres, tabla["pobreza"], tope)
    if referencia is not None:
        _linea_nacional(figura, referencia)
    _eje_de_pobreza(figura, tope, desde=-0.08 * tope, cifras=True)
    return _lienzo(figura, ALTO_TERRITORIAL, bargap=0.3)


def figura_barras(tabla: pd.DataFrame, columna: str, referencia: float | None = None,
                  alto: int | None = None) -> go.Figure:
    """Barras horizontales en % de personas, en la escala fija; con referencia, la línea nacional."""
    alto = alto or 90 + 34 * len(tabla)
    tope = _tope(tabla[columna])
    figura = go.Figure(go.Bar(x=tabla[columna], y=tabla["nombre"], orientation="h", marker_color=BARRA,
                              name=columna, hovertemplate="%{y}: %{x:.1f} %<extra></extra>"))
    _cifras(figura, tabla["nombre"].tolist(), tabla[columna], tope)
    if referencia is not None:
        _linea_nacional(figura, referencia)
    _eje_de_pobreza(figura, tope, cifras=True)
    # El mismo grosor de barra en todas las tarjetas, aunque tengan distinto número de grupos
    return _lienzo(figura, alto, bargap=max(0.15, 1 - 22 / ((alto - 70) / len(tabla))))


# ---------- contraste con el INEI ----------

def resumen_contraste(contraste: pd.DataFrame) -> dict:
    """Cuántos ámbitos coinciden, la mayor diferencia y dónde, y cuántas cifras del INEI son referenciales."""
    maxima = float(contraste["diferencia"].max())
    return {"total": len(contraste), "dentro": int(contraste["dentro_de_tolerancia"].sum()),
            "fuera": int((~contraste["dentro_de_tolerancia"]).sum()),
            "referenciales": int(contraste["referencial"].sum()), "diferencia_maxima": maxima,
            "donde": " y ".join(contraste.loc[contraste["diferencia"] == maxima, "ambito"])}


def _sin_tildes(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", str(texto)) if not unicodedata.combining(c)).casefold()


def filtrar_contraste(contraste: pd.DataFrame, vista: str = "todos", busqueda: str = "") -> pd.DataFrame:
    """Los ámbitos de una vista (todos, fuera de tolerancia o referenciales) cuyo nombre o código contiene la
    búsqueda, sin distinguir tildes ni mayúsculas."""
    elegidos = {"todos": pd.Series(True, index=contraste.index), "fuera": ~contraste["dentro_de_tolerancia"],
                "referenciales": contraste["referencial"]}[vista]
    buscado = busqueda.strip()
    if buscado:
        elegidos = elegidos & (contraste["ambito"].map(_sin_tildes).str.contains(_sin_tildes(buscado), regex=False) |
                               contraste["codigo"].str.contains(buscado, regex=False))
    return contraste[elegidos].reset_index(drop=True)


def tabla_contraste(contraste: pd.DataFrame) -> pd.DataFrame:
    """El contraste listo para mostrar: nombres del INEI con tildes, el intervalo como texto y el estado en palabras."""
    return pd.DataFrame({
        "Código": contraste["codigo"], "Ámbito": contraste["ambito"],
        "Réplica ENAHO (%)": contraste["pobreza_pct"], "INEI publicado (%)": contraste["referencia_inei"],
        "IC 95 % del INEI": [f"{a:.1f} a {b:.1f}" for a, b in zip(contraste["ic_inf"], contraste["ic_sup"])],
        "Diferencia (pp)": contraste["diferencia"],
        "Estado": contraste["dentro_de_tolerancia"].map({True: "Coincide", False: "Fuera de tolerancia"}),
        "Nota": [f"Referencial · CV {cv:.1f} %" if r else "" for r, cv in zip(contraste["referencial"], contraste["cv"])]})


def nota_lima(ind: pd.DataFrame) -> str:
    """Por qué el departamento de Lima no está en el contraste, con su réplica de la ENAHO."""
    fila = ind.loc[ind["id"] == LIMA_DEPARTAMENTO, "valor"]
    replica = f" (réplica: {float(fila.iat[0]):.2f} %)" if len(fila) else ""
    return (f"**Lima (departamento 15).** El INEI no publica una cifra para el departamento en conjunto{replica}. Se "
            "contrasta por ámbito: Lima Metropolitana es la provincia de Lima (1501, 43 distritos), sin el Callao, y "
            "Lima provincias son las otras nueve provincias del departamento.")


def figura_intervalos(contraste: pd.DataFrame) -> go.Figure:
    """Banda: intervalo de confianza al 95 % que publica el INEI. Anillo: su cifra. Punto: la réplica con la ENAHO."""
    y = contraste["ambito"].tolist()
    figura = go.Figure(go.Bar(y=y, x=contraste["ic_sup"] - contraste["ic_inf"], base=contraste["ic_inf"],
                              orientation="h", marker_color=INTERVALO, name="IC 95 % del INEI",
                              customdata=contraste[["ic_inf", "ic_sup"]],
                              hovertemplate="%{y}: IC 95 % de %{customdata[0]:.1f} a %{customdata[1]:.1f} %"
                                            "<extra></extra>"))
    figura.add_scatter(y=y, x=contraste["referencia_inei"], mode="markers", name="Cifra del INEI",
                       marker={"symbol": "circle-open", "size": 11, "color": TINTA, "line": {"width": 2}},
                       hovertemplate="%{y}: INEI %{x:.1f} %<extra></extra>")
    figura.add_scatter(y=y, x=contraste["pobreza_pct"], mode="markers", name="Réplica ENAHO",
                       marker={"size": 7, "color": REPLICA}, hovertemplate="%{y}: réplica %{x:.2f} %<extra></extra>")
    _eje_de_pobreza(figura, _tope(contraste["ic_sup"]))
    return _lienzo(figura, 90 + 26 * len(contraste), showlegend=True, bargap=0.45,
                   legend={"orientation": "h", "x": 0, "y": 1, "yanchor": "bottom"},
                   margin={"l": 0, "r": 24, "t": 36, "b": 0})


# ---------- BCRP ----------

def fecha_periodo(periodo: str) -> pd.Timestamp:
    """El primer día de un periodo del BCRP: "2025" (anual), "2025-T1" (trimestral), "2025-01" (mensual) o
    "2025-01-15" (diario)."""
    if "-T" in periodo:
        anio, trimestre = periodo.split("-T")
        return pd.Timestamp(int(anio), 3 * int(trimestre) - 2, 1)
    return pd.Timestamp(periodo if len(periodo) > 4 else f"{periodo}-01-01")


def etiqueta_periodo(periodo: str, con_dia: bool = True) -> str:
    """Un periodo del BCRP en español: «2025», «T1 2025», «ene 2025» o «2 oct 2026» (sin el día, «oct 2026»)."""
    if "-T" in periodo:
        anio, trimestre = periodo.split("-T")
        return f"T{trimestre} {anio}"
    if len(periodo) == 4:
        return periodo
    fecha = fecha_periodo(periodo)
    mes = f"{MESES[fecha.month - 1]} {fecha.year}"
    return f"{fecha.day} {mes}" if len(periodo) > 7 and con_dia else mes


def _marcas_eje(serie: pd.DataFrame, maximo: int = 8) -> tuple[list, list[str]]:
    """Las marcas del eje de tiempo con etiquetas en español: en una serie mensual o diaria de varios años, la primera
    observación de cada año; si no, marcas repartidas. Nunca más de `maximo`."""
    fechas, periodos = serie["fecha"].tolist(), serie["periodo"].tolist()
    if len(periodos[0]) >= 7 and fechas[-1].year > fechas[0].year:
        indices = [i for i, f in enumerate(fechas) if i == 0 or f.year != fechas[i - 1].year]
        indices = indices[::-(-len(indices) // maximo)]
    else:
        n = min(len(fechas), maximo)
        indices = sorted({round(i * (len(fechas) - 1) / max(n - 1, 1)) for i in range(n)})
    return [fechas[i] for i in indices], [etiqueta_periodo(periodos[i], con_dia=False) for i in indices]


def series_bcrp(carpeta: Path = BCRP) -> pd.DataFrame:
    """Las series que graficó el agente con graficar_serie, una por archivo, con los periodos en orden de calendario."""
    leidas = [(r.stem, _leer(r, COLUMNAS_BCRP, dtype={"periodo": str, "codigo": str})) for r in sorted(carpeta.glob("*.csv"))]
    tablas = [t.assign(archivo=archivo) for archivo, t in leidas if not t.empty]
    if not tablas:
        return pd.DataFrame(columns=COLUMNAS_BCRP)
    tabla = pd.concat(tablas, ignore_index=True)
    tabla["valor"] = pd.to_numeric(tabla["valor"], errors="coerce")
    tabla["fecha"] = tabla["periodo"].map(fecha_periodo)
    return tabla.sort_values(["archivo", "fecha"], kind="stable").reset_index(drop=True)[COLUMNAS_BCRP]


def catalogo_bcrp(tabla: pd.DataFrame) -> pd.DataFrame:
    """Una fila por archivo guardado: código, nombre, primer y último periodo y la URL consultada."""
    return (tabla.groupby("archivo", sort=True)
            .agg(codigo=("codigo", "first"), nombre=("nombre", "first"), desde=("periodo", "first"),
                 hasta=("periodo", "last"), n=("periodo", "size"), fuente=("fuente", "first"))
            .reset_index())


def figura_serie(serie: pd.DataFrame) -> go.Figure:
    """La serie en el tiempo, con fechas en español; las anuales llevan un marcador en cada año."""
    anual = len(serie["periodo"].iat[0]) == 4
    figura = go.Figure(go.Scatter(x=serie["fecha"], y=serie["valor"], mode="lines+markers" if anual else "lines",
                                  name="serie", line={"color": BARRA, "width": 2}, marker={"size": 7, "color": BARRA},
                                  customdata=serie["periodo"].map(etiqueta_periodo),
                                  hovertemplate="%{customdata}: %{y:,.2f}<extra></extra>"))
    if serie["valor"].min() < 0 < serie["valor"].max():
        figura.add_hline(y=0, line_color=REFERENCIA, line_width=1)
    marcas, etiquetas = _marcas_eje(serie)
    figura.update_xaxes(title=None, tickvals=marcas, ticktext=etiquetas, gridcolor=BORDE)
    figura.update_yaxes(title=None, gridcolor=BORDE)
    return _lienzo(figura, 440, margin={"l": 0, "r": 16, "t": 16, "b": 0})


# ---------- evaluación ----------

def _en_orden(columna: pd.Series, orden: list[str]) -> pd.Categorical:
    """Categorías en el orden fijo dado y, después, las que no estén en él, alfabéticamente."""
    presentes = columna.dropna().unique().tolist()
    return pd.Categorical(columna, categories=[c for c in orden if c in presentes] +
                          sorted(c for c in presentes if c not in orden))


def _tasas(tabla: pd.DataFrame, por: list[str], exito: str, nombres: tuple[str, str, str]) -> pd.DataFrame:
    casos, logrados, pct = nombres
    datos = tabla.assign(logrado=tabla["resultado"].eq(exito),
                         segundos=pd.to_numeric(tabla["segundos"], errors="coerce"),
                         modo=_en_orden(tabla["modo"], list(MODOS)))
    if "tipo" in por:
        datos["tipo"] = _en_orden(datos["tipo"], TIPOS)
    r = (datos.groupby(por, observed=True)
         .agg(**{casos: ("resultado", "size"), logrados: ("logrado", "sum"), "segundos_promedio": ("segundos", "mean")})
         .reset_index())
    r[pct] = 100 * r[logrados] / r[casos]
    for c in por:
        r[c] = r[c].astype(str)
    return r


def resumen_evaluacion(tabla: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Aciertos y segundos promedio por modo y por tipo de pregunta y modo, y el resultado de cada pregunta en cada
    modo. Un acierto es la etiqueta "acierta" de evaluar.py; "no sabe" y "error" cuentan como no acierto."""
    nombres = ("preguntas", "aciertos", "acierto_pct")
    por_modo = _tasas(tabla, ["modo"], "acierta", nombres)
    por_modo.insert(1, "etiqueta", por_modo["modo"].map(lambda m: MODOS.get(m, m)))
    pregunta = (tabla.assign(modo=_en_orden(tabla["modo"], list(MODOS)))
                .pivot_table(index=["id", "pregunta"], columns="modo", values="resultado", aggfunc="first",
                             observed=True, sort=False)
                .reset_index())
    pregunta.columns = [str(c) for c in pregunta.columns]
    return {"por_modo": por_modo, "por_tipo": _tasas(tabla, ["tipo", "modo"], "acierta", nombres),
            "por_pregunta": pregunta}


def resumen_robustez(tabla: pd.DataFrame) -> pd.DataFrame:
    """Casos que cumplen la conducta esperada (pedir aclaración, declarar el límite) por modo."""
    resumen = _tasas(tabla, ["modo"], "cumple", ("casos", "cumple", "cumple_pct"))
    resumen.insert(1, "etiqueta", resumen["modo"].map(lambda m: MODOS.get(m, m)))
    return resumen


def figura_modos(por_modo: pd.DataFrame, columna: str, textos: list[str], tope: float | None = None) -> go.Figure:
    figura = go.Figure(go.Bar(x=por_modo["etiqueta"], y=por_modo[columna], marker_color=BARRA, text=textos,
                              name=columna, textposition="outside", cliponaxis=False,
                              hovertemplate="%{x}: %{text}<extra></extra>"))
    figura.update_xaxes(title=None)
    figura.update_yaxes(title=None, range=[0, tope or por_modo[columna].max() * 1.2], gridcolor=BORDE)
    return _lienzo(figura, 380, margin={"l": 0, "r": 0, "t": 16, "b": 0})


def conteo_consistencia(tabla: pd.DataFrame) -> dict[str, int]:
    """Cuántas verificaciones hay en cada estado, en el orden de verificar.py y luego cualquier otro."""
    conteo = tabla["resultado"].value_counts().to_dict()
    return {e: int(conteo.pop(e, 0)) for e in ESTADOS} | {e: int(n) for e, n in sorted(conteo.items())}


def estilo_resultado(valor) -> str:
    estado = ESTADO_DE.get(valor) if isinstance(valor, str) else None
    if estado is None:
        return ""
    fondo, texto, _ = ESTILOS_ESTADO[estado]
    return f"background-color: {fondo}; color: {texto}"


def con_icono(valor) -> str:
    """El estado con su ícono delante («✓ OK»); una celda vacía, como una pregunta que un modo no respondió, queda
    vacía."""
    if not isinstance(valor, str):
        return ""
    estado = ESTADO_DE.get(valor)
    return f"{ESTILOS_ESTADO[estado][2]} {valor}" if estado else valor


def estilar_estados(tabla: pd.DataFrame, columnas: list[str], formatos: dict | None = None):
    """La tabla con las columnas de estado en sus colores y con ícono; `formatos` fija los decimales de las demás."""
    return (tabla.style.map(estilo_resultado, subset=columnas).format(con_icono, subset=columnas)
            .format(formatos or {}))
