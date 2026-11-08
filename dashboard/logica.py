"""Datos y figuras del dashboard, aparte de Streamlit para poder probarlos.

Solo lee las salidas versionadas que dejan las herramientas del agente (salidas/ y evaluacion/): ninguna cifra se
escribe a mano ni se recalcula aquí. Las salidas opcionales que aún no existen se leen como tablas vacías.
"""
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

RAIZ = Path(__file__).resolve().parents[1]
INDICADORES = RAIZ / "salidas" / "indicadores.csv"
COMPARACION = RAIZ / "salidas" / "mapa_vs_referencia.csv"
CONSISTENCIA = RAIZ / "salidas" / "consistencia.csv"
BCRP = RAIZ / "salidas" / "bcrp"
RESULTADOS = RAIZ / "evaluacion" / "resultados.csv"
ROBUSTEZ = RAIZ / "evaluacion" / "robustez_resultados.csv"
# Límites oficiales del IGN (COD-AB, OCHA HDX), versionados; los genera scripts/preparar_limites.py. Nunca se descargan.
GEOJSON_AMBITOS = RAIZ / "referencias" / "limites_ambitos_ign.geojson"
PREPARAR_LIMITES = "uv run scripts/preparar_limites.py"

# El análisis territorial usa los 26 ámbitos del Cuadro III.1 del INEI: Lima (15) se desagrega en Lima Metropolitana
# (provincia 1501) y Lima provincias, cada una con el código de la propiedad `codigo` de la capa de ámbitos. Se eligen
# por id, nunca por la etiqueta: pobreza_lima_metropolitana (dominio 8, con el Callao) no es un ámbito.
AMBITOS = 26
LIMA_DESAGREGADA = {"pobreza_lima_metropolitana_provincia": "1501", "pobreza_lima_provincias": "15_resto"}
LIMA_DEPARTAMENTO = "pobreza_dep_15"

COLUMNAS_EVALUACION = ["id", "tipo", "modo", "pregunta", "verdad", "valor", "unidad", "tolerancia", "resultado",
                       "segundos", "turnos", "herramientas", "fuente", "error"]
COLUMNAS_ROBUSTEZ = ["id", "modo", "pedido", "conducta_esperada", "conducta_observada", "resultado", "segundos"]
COLUMNAS_CONSISTENCIA = ["fuente", "verificacion", "resultado", "detalle", "explicacion"]
COLUMNAS_COMPARACION = ["ccdd", "departamento", "pobreza_pct", "referencia_inei", "diferencia",
                        "dentro_de_tolerancia"]
SIN_REFERENCIA, NO_APLICA = "sin cifra publicada por el INEI", "no aplica"
COLUMNAS_BCRP = ["archivo", "periodo", "fecha", "valor", "codigo", "nombre", "fuente"]

# Las configuraciones de evaluacion/evaluar.py, en el orden en que se comparan
MODOS = {"A": "A: herramientas estándar", "B": "B: con MCP y skills", "memoria": "Sin herramientas",
         "solo-mcp": "Solo MCP", "solo-skills": "Solo skills", "sin-propia": "B sin comparar_series"}
TIPOS = ["bcrp", "enaho", "mixta"]
KPIS = {"pobreza_nacional": "Pobreza monetaria nacional", "pobreza_area_urbana": "Pobreza urbana",
        "pobreza_area_rural": "Pobreza rural", "pobreza_extrema": "Pobreza extrema",
        "residentes_habituales": "Residentes en la muestra"}
ESTADOS = ["OK", "DIFERENCIA", "FALLA", "NO VERIFICABLE"]

# Un solo tono, de claro a oscuro: el mismo azul del mapa de mapeando-enaho
AZULES = ["#cde2fb", "#6da7ec", "#256abf", "#0d366b"]
BARRA, REFERENCIA = "#256abf", "#52514e"
# Fondo claro y texto oscuro fijo para que la tabla se lea también en modo oscuro; el texto nombra el estado
COLORES_RESULTADO = {"OK": "#d7f0dd", "acierta": "#d7f0dd", "cumple": "#d7f0dd",
                     "DIFERENCIA": "#fdf0c4", "no sabe": "#fdf0c4",
                     "FALLA": "#f9d5d3", "se equivoca": "#f9d5d3", "no cumple": "#f9d5d3",
                     "NO VERIFICABLE": "#e8e8e6", "error": "#e8e8e6"}


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


def cargar_indicadores(ruta: Path = INDICADORES, anio: int | None = 2024) -> pd.DataFrame:
    """Los indicadores del año dado (2024 por defecto). Una salida anterior sin columna `anio` es de un solo año y se
    devuelve completa."""
    df = _leer(ruta, ["anio", "id", "indicador", "grupo", "valor", "unidad", "ponderador", "n_muestral", "fuente"],
               dtype={"id": str})
    if "anio" in df.columns and anio is not None:
        df = df[df["anio"] == anio].reset_index(drop=True)
    return df


def cargar_comparacion(ruta: Path = COMPARACION) -> pd.DataFrame:
    return _leer(ruta, COLUMNAS_COMPARACION, dtype={"ccdd": str})


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


def cargar_geojson(ruta: Path = GEOJSON_AMBITOS) -> tuple[dict | None, str | None]:
    """Los límites del IGN versionados en referencias/. Nunca descarga nada ni lanza error: si el archivo falta o no
    se puede leer, devuelve el aviso para mostrar y el resto del tablero sigue."""
    try:
        return json.loads(ruta.read_text(encoding="utf-8")), None
    except FileNotFoundError:
        return None, (f"Falta `{_relativa(ruta)}`, con los límites oficiales del IGN. Se genera con "
                      f"`{PREPARAR_LIMITES}`. El mapa se omite.")
    except (OSError, ValueError) as error:
        return None, (f"No se pudo leer `{_relativa(ruta)}` ({error}). Se vuelve a generar con "
                      f"`{PREPARAR_LIMITES}`. El mapa se omite.")


def tabla_comparacion(comparacion: pd.DataFrame) -> pd.DataFrame:
    """El contraste del mapa con el Cuadro III.1 del INEI, listo para mostrar: un departamento sin cifra publicada
    (Lima, 15) lo dice en texto en lugar de quedar vacío, y su diferencia y tolerancia no aplican."""
    referencia = pd.to_numeric(comparacion["referencia_inei"], errors="coerce")
    diferencia = pd.to_numeric(comparacion["diferencia"], errors="coerce")
    dentro = comparacion["dentro_de_tolerancia"].astype(str).str.strip().str.lower().eq("true")
    con_cifra = referencia.notna()
    return pd.DataFrame({
        "ccdd": comparacion["ccdd"], "departamento": comparacion["departamento"],
        "pobreza_pct": pd.to_numeric(comparacion["pobreza_pct"], errors="coerce"),
        "referencia_inei": [f"{r:.1f}" if c else SIN_REFERENCIA for r, c in zip(referencia, con_cifra)],
        "diferencia": [f"{d:.2f}" if c and pd.notna(d) else NO_APLICA for d, c in zip(diferencia, con_cifra)],
        "dentro_de_tolerancia": [("Sí" if d else "No") if c else NO_APLICA for d, c in zip(dentro, con_cifra)]})


def resumen_comparacion(comparacion: pd.DataFrame) -> dict:
    """Cuántos departamentos tienen cifra del INEI, cuántos de ellos caen dentro de la tolerancia y cuáles no la
    tienen, como pares (código, nombre)."""
    con_cifra = pd.to_numeric(comparacion["referencia_inei"], errors="coerce").notna()
    dentro = comparacion["dentro_de_tolerancia"].astype(str).str.strip().str.lower().eq("true")
    sin_cifra = comparacion[~con_cifra]
    return {"con_referencia": int(con_cifra.sum()), "dentro": int((dentro & con_cifra).sum()),
            "sin_referencia": list(zip(sin_cifra["ccdd"].astype(str), sin_cifra["departamento"].astype(str)))}


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


def kpis(ind: pd.DataFrame) -> list[dict]:
    """Las cifras de cabecera, cada una con su id, ponderador, tamaño de muestra y fuente para citarla."""
    tarjetas = []
    for clave, etiqueta in KPIS.items():
        fila = ind[ind["id"] == clave]
        if fila.empty:
            continue
        f = fila.iloc[0]
        valor = f"{f['valor']:.1f} %" if str(f["unidad"]).startswith("%") else _miles(f["valor"])
        tarjetas.append({"id": clave, "etiqueta": etiqueta, "valor": valor,
                         "ayuda": f"`{clave}` · {f['unidad']} · ponderado: {f['ponderador']} · "
                                  f"n muestral {_miles(f['n_muestral'])} · {f['fuente']}"})
    return tarjetas


def _miles(numero: float) -> str:
    return f"{numero:,.0f}".replace(",", " ")


def pie_enaho(tabla: pd.DataFrame) -> str:
    ponderadores = " y ".join(tabla["ponderador"].drop_duplicates())
    return f"Fuente: INEI, ENAHO 2024. Ponderado con {ponderadores}. Datos: salidas/indicadores.csv (limpiando-enaho)."


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


def figura_mapa(unida: pd.DataFrame, geo: dict) -> go.Figure:
    figura = px.choropleth(unida, geojson=geo, locations="codigo", featureidkey="properties.codigo", color="pobreza",
                           color_continuous_scale=AZULES, range_color=(0, unida["pobreza"].max()),
                           hover_name="nombre", hover_data={"codigo": True, "pobreza": ":.1f"},
                           labels={"pobreza": "% de personas", "codigo": "Código"})
    figura.update_geos(fitbounds="locations", visible=False)
    figura.update_traces(marker_line_color="#fcfcfb", marker_line_width=0.8)
    figura.update_layout(title="Pobreza monetaria por ámbito territorial, Perú 2024", height=620,
                         margin={"l": 0, "r": 0, "t": 48, "b": 0},
                         coloraxis_colorbar={"title": {"text": "% de personas"}, "ticksuffix": " %"})
    return figura


def figura_barras(tabla: pd.DataFrame, columna: str, titulo: str, referencia: float | None = None,
                  ordenar: bool = False) -> go.Figure:
    """Barras horizontales en % de personas; con referencia, una línea punteada con el valor nacional."""
    if ordenar:
        tabla = tabla.sort_values(columna, ascending=False)
    figura = go.Figure(go.Bar(x=tabla[columna], y=tabla["nombre"], orientation="h", marker_color=BARRA,
                              text=[f"{v:.1f} %" for v in tabla[columna]], textposition="outside", cliponaxis=False,
                              hovertemplate="%{y}: %{x:.1f} %<extra></extra>"))
    if referencia is not None:
        figura.add_vline(x=referencia, line_dash="dash", line_color=REFERENCIA, line_width=1.5,
                         annotation_text=f"Nacional: {referencia:.1f} %", annotation_position="top")
    tope = max(tabla[columna].max(), referencia or 0)
    figura.update_layout(title=titulo, height=110 + 30 * len(tabla), showlegend=False,
                         margin={"l": 0, "r": 16, "t": 64, "b": 0},
                         xaxis={"title": "% de personas", "range": [0, tope * 1.18]},
                         yaxis={"title": None, "autorange": "reversed"})
    return figura


# ---------- BCRP ----------

def fecha_periodo(periodo: str) -> pd.Timestamp:
    """El primer día de un periodo del BCRP: "2025" (anual), "2025-T1" (trimestral), "2025-01" (mensual) o
    "2025-01-15" (diario)."""
    if "-T" in periodo:
        anio, trimestre = periodo.split("-T")
        return pd.Timestamp(int(anio), 3 * int(trimestre) - 2, 1)
    return pd.Timestamp(periodo if len(periodo) > 4 else f"{periodo}-01-01")


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
    figura = go.Figure(go.Scatter(x=serie["fecha"], y=serie["valor"], mode="lines", line={"color": BARRA, "width": 2},
                                  customdata=serie["periodo"], hovertemplate="%{customdata}: %{y:,.2f}<extra></extra>"))
    if serie["valor"].min() < 0 < serie["valor"].max():
        figura.add_hline(y=0, line_color=REFERENCIA, line_width=1)
    figura.update_layout(title=serie["nombre"].iat[0], height=440, showlegend=False,
                         margin={"l": 0, "r": 16, "t": 56, "b": 0}, xaxis_title=None, yaxis_title=None)
    return figura


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


def figura_modos(por_modo: pd.DataFrame, columna: str, titulo: str, textos: list[str], tope: float | None = None) -> go.Figure:
    figura = go.Figure(go.Bar(x=por_modo["etiqueta"], y=por_modo[columna], marker_color=BARRA, text=textos,
                              textposition="outside", cliponaxis=False, hovertemplate="%{x}: %{text}<extra></extra>"))
    figura.update_layout(title=titulo, height=380, showlegend=False, margin={"l": 0, "r": 0, "t": 56, "b": 0},
                         xaxis_title=None, yaxis={"title": None, "range": [0, tope or por_modo[columna].max() * 1.2]})
    return figura


def conteo_consistencia(tabla: pd.DataFrame) -> dict[str, int]:
    """Cuántas verificaciones hay en cada estado, en el orden de verificar.py y luego cualquier otro."""
    conteo = tabla["resultado"].value_counts().to_dict()
    return {e: int(conteo.pop(e, 0)) for e in ESTADOS} | {e: int(n) for e, n in sorted(conteo.items())}


def estilo_resultado(valor) -> str:
    color = COLORES_RESULTADO.get(valor)
    return f"background-color: {color}; color: #0b0b0b" if color else ""
