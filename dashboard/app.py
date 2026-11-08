"""Tablero para explorar los resultados del agente. Desde la raíz del repo: uv run streamlit run dashboard/app.py

Solo lee salidas versionadas (salidas/ y evaluacion/), así que corre igual en Streamlit Community Cloud.
"""
from pathlib import Path

import pandas as pd
import streamlit as st

from logica import (BCRP, COMPARACION, CONSISTENCIA, GEOJSON, INDICADORES, RESULTADOS, ROBUSTEZ, cargar_comparacion,
                    cargar_consistencia, cargar_evaluacion, cargar_geojson, cargar_indicadores, cargar_robustez,
                    catalogo_bcrp, conteo_consistencia, estilo_resultado, figura_barras, figura_mapa, figura_modos,
                    figura_serie, filas, huella, kpis, nacional, pie_enaho, resumen_evaluacion, resumen_robustez,
                    series_bcrp, tabla_departamentos, unir_geometria)

st.set_page_config(page_title="Agente socioeconómico del Perú", layout="wide")

CARGADORES = {"indicadores": cargar_indicadores, "comparacion": cargar_comparacion, "consistencia": cargar_consistencia,
              "evaluacion": cargar_evaluacion, "robustez": cargar_robustez, "bcrp": series_bcrp}
DESGLOSES = {"pobreza_area_": "Pobreza monetaria por área, Perú 2024",
             "pobreza_sexo_": "Pobreza monetaria por sexo, Perú 2024",
             "pobreza_edad_": "Pobreza monetaria por edad, Perú 2024"}


@st.cache_data(show_spinner=False, max_entries=64)
def leer(cargador: str, ruta: str, version) -> pd.DataFrame:
    """Cada salida se lee una vez por versión: si el agente la reescribe, cambia su huella y se vuelve a leer."""
    return CARGADORES[cargador](Path(ruta))


def datos(cargador: str, ruta: Path) -> pd.DataFrame:
    return leer(cargador, str(ruta), huella(ruta))


@st.cache_resource(show_spinner="Cargando los límites departamentales…", ttl="1h")
def geometria(ruta: str, version) -> tuple[dict | None, str | None]:
    return cargar_geojson(Path(ruta))


st.title("Agente socioeconómico del Perú")
st.markdown("Explora los resultados que generó el agente de investigación. Cada cifra proviene de fuentes oficiales "
            "(el INEI con la ENAHO 2024, el BCRP y la SBS) procesadas por las herramientas del proyecto: las skills de "
            "la ENAHO y los servidores MCP. El tablero solo lee las salidas que esas herramientas dejan en `salidas/` "
            "y `evaluacion/`: no consulta las fuentes ni recalcula cifras.")

tab_enaho, tab_bcrp, tab_evaluacion, tab_consistencia = st.tabs(["ENAHO 2024", "BCRP", "Evaluación", "Consistencia"])

# ---------- ENAHO ----------

with tab_enaho:
    ind = datos("indicadores", INDICADORES)
    if ind.empty:
        st.error("Falta `salidas/indicadores.csv`. Lo escribe la skill limpiando-enaho.")
    else:
        with st.container(horizontal=True):
            for k in kpis(ind):
                st.metric(k["etiqueta"], k["valor"], help=k["ayuda"], border=True)
        departamentos, tabla = filas(ind, "pobreza_dep_"), tabla_departamentos(ind)
        mapa_col, barras_col = st.columns(2, gap="large")
        with mapa_col:
            geo, aviso = geometria(str(GEOJSON), huella(GEOJSON))
            try:
                if geo is None:
                    raise ValueError(aviso)
                st.plotly_chart(figura_mapa(unir_geometria(geo, tabla), geo), key="mapa",
                                alt="Mapa de la pobreza monetaria por departamento del Perú en 2024")
                st.caption(pie_enaho(departamentos) + " Unión por código de departamento, con Lima y Callao aparte.")
            except ValueError as error:  # sin límites o con una unión incompleta, el mapa se omite y el resto sigue
                st.warning(f"{error}", icon=":material/map:")
        with barras_col:
            st.plotly_chart(figura_barras(tabla, "pobreza", "Pobreza monetaria por departamento, Perú 2024",
                                          nacional(ind, departamentos["ponderador"].iat[0]), ordenar=True),
                            key="departamentos", alt="Barras de la pobreza monetaria por departamento en 2024")
            st.caption(pie_enaho(departamentos) + " La línea punteada es la pobreza nacional.")
        for columna, (prefijo, titulo) in zip(st.columns(len(DESGLOSES), gap="large"), DESGLOSES.items()):
            grupo = filas(ind, prefijo)
            if grupo.empty:
                continue
            with columna:
                st.plotly_chart(figura_barras(grupo, "valor", titulo, nacional(ind, grupo["ponderador"].iat[0])),
                                key=prefijo, alt=titulo)
                st.caption(pie_enaho(grupo))
        comparacion = datos("comparacion", COMPARACION)
        if not comparacion.empty:
            with st.expander("Contraste del mapa con la referencia del curso (sesión 16)"):
                dentro = int(comparacion["dentro_de_tolerancia"].astype(str).eq("True").sum())
                st.markdown(f"{dentro} de {len(comparacion)} departamentos coinciden con la referencia dentro de la "
                            "tolerancia de mapeando-enaho. Fuente: `salidas/mapa_vs_referencia.csv`.")
                st.dataframe(comparacion, hide_index=True, alt="Pobreza por departamento frente a la referencia",
                             column_config={"ccdd": "Código", "departamento": "Departamento",
                                            "pobreza_pct": st.column_config.NumberColumn("Pobreza (%)", format="%.2f"),
                                            "referencia_sesion16": st.column_config.NumberColumn("Referencia (%)",
                                                                                                 format="%.2f"),
                                            "diferencia": st.column_config.NumberColumn("Diferencia", format="%.2f"),
                                            "dentro_de_tolerancia": "Dentro de la tolerancia"})

# ---------- BCRP ----------

with tab_bcrp:
    series = datos("bcrp", BCRP)
    if series.empty:
        st.info("Todavía no hay series guardadas. Cada vez que el agente usa `graficar_serie` del servidor MCP del "
                "BCRP, deja los datos graficados en `salidas/bcrp/` y aparecen aquí.")
    else:
        catalogo = catalogo_bcrp(series).set_index("archivo")
        archivo = st.selectbox("Serie guardada", catalogo.index.tolist(), key="serie",
                               format_func=lambda a: f"{catalogo.at[a, 'nombre']} ({catalogo.at[a, 'codigo']}, "
                                                     f"{catalogo.at[a, 'desde']} a {catalogo.at[a, 'hasta']})")
        serie, ficha = series[series["archivo"] == archivo], catalogo.loc[archivo]
        st.plotly_chart(figura_serie(serie), key="grafico_serie", alt=f"Serie del BCRP {ficha['nombre']}")
        st.caption(f"Fuente: BCRP, serie {ficha['codigo']}, {ficha['desde']} a {ficha['hasta']} "
                   f"({ficha['n']} observaciones). {ficha['fuente']}")
        with st.expander("Ver los datos"):
            st.dataframe(serie[["periodo", "valor"]], hide_index=True, alt=f"Datos de la serie {ficha['codigo']}")

# ---------- evaluación ----------

ETIQUETAS_TASAS = {"etiqueta": "Modo", "tipo": "Tipo", "preguntas": "Preguntas", "aciertos": "Aciertos",
                   "acierto_pct": st.column_config.NumberColumn("Aciertos (%)", format="%.0f"),
                   "casos": "Casos", "cumple": "Cumple",
                   "cumple_pct": st.column_config.NumberColumn("Cumple (%)", format="%.0f"),
                   "segundos_promedio": st.column_config.NumberColumn("Segundos promedio", format="%.1f")}

with tab_evaluacion:
    resultados = datos("evaluacion", RESULTADOS)
    if resultados.empty:
        st.info("Todavía no hay resultados de la evaluación. Los produce `uv run evaluacion/evaluar.py`, que hace las "
                "mismas preguntas en cada configuración (Modo A sin MCP ni skills, Modo B con ellos y la ablación) y "
                "escribe `evaluacion/resultados.csv`.")
    else:
        resumen = resumen_evaluacion(resultados)
        por_modo = resumen["por_modo"]
        izquierda, derecha = st.columns(2, gap="large")
        izquierda.plotly_chart(figura_modos(por_modo, "acierto_pct", "Aciertos por modo (% de preguntas)",
                                            [f"{p:.0f} % ({a} de {n})" for p, a, n in
                                             zip(por_modo["acierto_pct"], por_modo["aciertos"], por_modo["preguntas"])],
                                            tope=110), key="aciertos", alt="Porcentaje de aciertos por modo")
        derecha.plotly_chart(figura_modos(por_modo, "segundos_promedio", "Tiempo promedio por modo (segundos)",
                                          [f"{s:.0f} s" for s in por_modo["segundos_promedio"]]),
                             key="tiempos", alt="Segundos promedio por respuesta en cada modo")
        st.caption("Fuente: `evaluacion/resultados.csv`, escrito por `evaluacion/evaluar.py`. Acierta si cada cifra "
                   "pedida cae dentro de su tolerancia; «no sabe» y «error» cuentan como no acierto.")
        st.subheader("Por tipo de pregunta")
        st.dataframe(resumen["por_tipo"], hide_index=True, column_order=["tipo", "modo", "preguntas", "aciertos",
                                                                         "acierto_pct", "segundos_promedio"],
                     column_config=ETIQUETAS_TASAS | {"modo": "Modo"}, alt="Aciertos y tiempo por tipo y modo")
        st.subheader("Resultado de cada pregunta")
        pregunta = resumen["por_pregunta"]
        modos = [c for c in pregunta.columns if c not in ("id", "pregunta")]
        st.dataframe(pregunta.style.map(estilo_resultado, subset=modos), hide_index=True,
                     column_config={"id": "Pregunta", "pregunta": "Texto"}, alt="Resultado de cada pregunta por modo")

    st.subheader("Robustez ante pedidos ambiguos o imposibles")
    robustez = datos("robustez", ROBUSTEZ)
    if robustez.empty:
        st.info("Todavía no hay resultados de robustez. Los produce `uv run evaluacion/evaluar.py --robustez`, que "
                "escribe `evaluacion/robustez_resultados.csv`.")
    else:
        st.dataframe(resumen_robustez(robustez), hide_index=True, column_config=ETIQUETAS_TASAS,
                     column_order=["etiqueta", "casos", "cumple", "cumple_pct", "segundos_promedio"],
                     alt="Casos que cumplen la conducta esperada por modo")
        st.dataframe(robustez.style.map(estilo_resultado, subset=["resultado"]), hide_index=True,
                     column_order=["id", "modo", "pedido", "conducta_esperada", "conducta_observada", "resultado"],
                     column_config={"id": "Caso", "modo": "Modo", "pedido": "Pedido",
                                    "conducta_esperada": "Conducta esperada", "conducta_observada": "Conducta observada",
                                    "resultado": "Resultado"}, alt="Detalle de cada caso de robustez")
        st.caption("Fuente: `evaluacion/robustez_resultados.csv`, escrito por `evaluacion/evaluar.py --robustez`.")

# ---------- consistencia ----------

with tab_consistencia:
    consistencia = datos("consistencia", CONSISTENCIA)
    if consistencia.empty:
        st.info("Todavía no hay `salidas/consistencia.csv`. Lo escribe la skill verificando-consistencia "
                "(`uv run .claude/skills/verificando-consistencia/scripts/verificar.py`), que contrasta la ENAHO, el "
                "BCRP y el informe entre sí.")
    else:
        with st.container(horizontal=True):
            for estado, n in conteo_consistencia(consistencia).items():
                st.metric(estado, n, border=True)
        st.dataframe(consistencia.style.map(estilo_resultado, subset=["resultado"]), hide_index=True,
                     column_config={"fuente": "Fuente", "verificacion": "Verificación", "resultado": "Resultado",
                                    "detalle": "Detalle", "explicacion": "Explicación"},
                     alt="Verificaciones de consistencia entre herramientas")
        st.caption("Fuente: `salidas/consistencia.csv`, escrito por la skill verificando-consistencia.")
