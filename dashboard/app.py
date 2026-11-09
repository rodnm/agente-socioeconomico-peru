"""Tablero para explorar los resultados del agente. Desde la raíz del repo: uv run streamlit run dashboard/app.py

Solo lee salidas versionadas (salidas/ y evaluacion/), así que corre igual en Streamlit Community Cloud. El tema claro
y la paleta están en .streamlit/config.toml.
"""
from pathlib import Path

import pandas as pd
import streamlit as st

from logica import (ANIO_CONTRASTE, BCRP, CONSISTENCIA, CONTRASTE, GEOJSON_AMBITOS, ICONOS_ESTADO, INDICADORES, MAPEAR,
                    NOTA_REFERENCIAL, RESULTADOS, ROBUSTEZ, SUPERFICIE, TOLERANCIA, VISTAS_CONTRASTE, anios,
                    cargar_consistencia, cargar_contraste, cargar_evaluacion, cargar_geojson, cargar_indicadores,
                    cargar_robustez, catalogo_bcrp, conteo_consistencia, del_anio, estilar_estados, etiqueta_periodo,
                    figura_barras, figura_intervalos, figura_mapa, figura_modos, figura_ranking, figura_serie, filas,
                    filtrar_contraste, huella, kpis, leyenda_clases, leyenda_html, nacional, nota_lima, pie_enaho,
                    ponderado_por, resumen_contraste, resumen_evaluacion, resumen_pobreza, resumen_robustez,
                    series_bcrp, tabla_ambitos, tabla_contraste, unir_geometria)

st.set_page_config(page_title="Agente socioeconómico del Perú", page_icon=":material/insights:", layout="wide")
# Las tarjetas son contenedores con clave «tarjeta_…»: blancas sobre el fondo cálido del tema
st.html(f"<style>div[class*='st-key-tarjeta'] {{ background: {SUPERFICIE}; }}</style>")

CARGADORES = {"indicadores": lambda ruta: cargar_indicadores(ruta, anio=None), "contraste": cargar_contraste,
              "consistencia": cargar_consistencia, "evaluacion": cargar_evaluacion, "robustez": cargar_robustez,
              "bcrp": series_bcrp}
DESGLOSES = {"pobreza_area_": "Por área", "pobreza_sexo_": "Por sexo", "pobreza_edad_": "Por edad"}


@st.cache_data(show_spinner=False, max_entries=64)
def leer(cargador: str, ruta: str, version) -> pd.DataFrame:
    """Cada salida se lee una vez por versión: si el agente la reescribe, cambia su huella y se vuelve a leer."""
    return CARGADORES[cargador](Path(ruta))


def datos(cargador: str, ruta: Path) -> pd.DataFrame:
    return leer(cargador, str(ruta), huella(ruta))


@st.cache_resource(show_spinner="Cargando los límites del IGN…", ttl="1h")
def geometria(ruta: str, version) -> tuple[dict | None, str | None]:
    return cargar_geojson(Path(ruta))


def tarjeta(clave: str, titulo: str, subtitulo: str):
    """Una tarjeta blanca con su título y subtítulo; la figura que va dentro no repite el título."""
    contenedor = st.container(border=True, key=f"tarjeta_{clave}")
    contenedor.subheader(titulo, anchor=False)
    contenedor.caption(subtitulo)
    return contenedor


with st.container(horizontal=True, vertical_alignment="center"):
    st.markdown("**Agente socioeconómico del Perú**")
    st.space("stretch")
    st.caption("Fuentes oficiales: INEI · BCRP · SBS", width="content")
st.caption("El tablero solo lee las salidas que las herramientas del agente dejan en `salidas/` y `evaluacion/`: no "
           "consulta las fuentes ni recalcula cifras.")

tab_enaho, tab_bcrp, tab_evaluacion, tab_consistencia = st.tabs(
    ["Pobreza · ENAHO", "Series del BCRP", "Evaluación del agente", "Consistencia"])

# ---------- ENAHO ----------

with tab_enaho:
    todos = datos("indicadores", INDICADORES)
    if todos.empty:
        st.error("Falta `salidas/indicadores.csv`. Lo escribe la skill limpiando-enaho.")
    else:
        disponibles = anios(todos)
        cabecera = st.container(horizontal=True, vertical_alignment="bottom", gap="large")
        texto, control = cabecera.container(), cabecera.container(width="content")
        anio = control.segmented_control("Año de la encuesta", disponibles, default=disponibles[-1], required=True,
                                         key="anio")
        ind = del_anio(todos, anio)
        try:
            ambitos, sin_ambitos = tabla_ambitos(ind), None
        except ValueError as error:  # una salida anterior sin Lima desagregada: se avisa en lugar de mostrar 24
            ambitos, sin_ambitos = None, str(error)
        texto.caption(f"ENAHO {anio} · INEI")
        texto.title("Pobreza monetaria en el Perú", anchor=False)
        if ambitos is not None:
            texto.markdown(resumen_pobreza(ind, ambitos, anio))

        with st.container(horizontal=True):
            for k in kpis(ind, todos):
                st.metric(k["etiqueta"], k["valor"], delta=k["variacion"], delta_color="off",
                          delta_arrow="auto" if k["detalle"] else "off", delta_description=k["detalle"],
                          chart_data=k["serie"], help=k["ayuda"], border=True)

        contraste = datos("contraste", CONTRASTE)
        referenciales = frozenset(contraste.loc[contraste["referencial"], "codigo"]) if anio == ANIO_CONTRASTE else frozenset()
        if ambitos is None:
            st.warning(sin_ambitos, icon=":material/warning:")
        else:
            mapa_col, ranking_col = st.columns(2, gap="medium")
            with mapa_col, tarjeta("mapa", "Mapa por ámbito territorial",
                                   "% de personas en pobreza monetaria. 26 ámbitos: Lima Metropolitana, Lima "
                                   "provincias y el Callao van por separado."):
                geo, aviso = geometria(str(GEOJSON_AMBITOS), huella(GEOJSON_AMBITOS))
                try:
                    if geo is None:
                        raise ValueError(aviso)
                    st.plotly_chart(figura_mapa(unir_geometria(geo, ambitos), geo), key="mapa",
                                    alt=f"Mapa de la pobreza monetaria por ámbito territorial del Perú en {anio}")
                    st.html(leyenda_html(leyenda_clases(ambitos)))
                except ValueError as error:  # sin límites o con una unión incompleta, el mapa se omite y el resto sigue
                    st.warning(f"{error}", icon=":material/map:")
            with ranking_col, tarjeta("ranking", "Ranking por ámbito",
                                      "De mayor a menor. La barra oscura marca Lima y el Callao."):
                st.plotly_chart(figura_ranking(ambitos, nacional(ind, ambitos["ponderador"].iat[0]), referenciales),
                                key="ambitos", alt=f"Barras de la pobreza monetaria por ámbito territorial en {anio}")
                if referenciales:
                    st.caption(NOTA_REFERENCIAL)

        grupos = {prefijo: filas(ind, prefijo) for prefijo in DESGLOSES}
        alto = 90 + 34 * max(len(g) for g in grupos.values())
        for columna, (prefijo, titulo) in zip(st.columns(len(DESGLOSES), gap="medium"), DESGLOSES.items()):
            grupo = grupos[prefijo]
            if grupo.empty:
                continue
            ponderador = grupo["ponderador"].iat[0]
            referencia = nacional(ind, ponderador)
            subtitulo = ponderado_por(ponderador) + (f" · nacional {referencia:.1f} %" if referencia is not None else "")
            with columna, tarjeta(prefijo.strip("_"), titulo, subtitulo):
                st.plotly_chart(figura_barras(grupo, "valor", referencia, alto), key=prefijo,
                                alt=f"Pobreza monetaria {titulo.lower()}, {anio}")
        st.caption(pie_enaho(ind, anio))

        # Contraste con el informe técnico del INEI: solo existe para 2024, el año del informe
        st.divider()
        st.caption("Validación · Cuadro III.1, páginas 219 y 220")
        st.header(f"Contraste con el informe técnico del INEI, {ANIO_CONTRASTE}", anchor=False)
        st.markdown(f"Cada ámbito replicado con la ENAHO {ANIO_CONTRASTE}, frente a la cifra que publica el INEI "
                    "(2025). Lima se contrasta separada en Lima Metropolitana y Lima provincias, como la publica el "
                    "INEI.")
        if contraste.empty:
            st.info(f"Todavía no hay `salidas/ambitos_vs_referencia.csv`. Lo escribe la skill mapeando-enaho "
                    f"(`{MAPEAR}`).")
        else:
            r = resumen_contraste(contraste)
            with st.container(horizontal=True):
                st.metric("Coinciden con la cifra publicada", f"{r['dentro']} de {r['total']}", border=True)
                st.metric("Diferencia máxima", f"{r['diferencia_maxima']:.2f} pp", delta=r["donde"],
                          delta_color="off", delta_arrow="off", border=True)
                st.metric("Tolerancia", f"± {TOLERANCIA} pp", border=True,
                          help="Réplica de una cifra que el INEI redondea a un decimal.")
                st.metric("Cifras referenciales del INEI", r["referenciales"], border=True,
                          help="Coeficiente de variación mayor que 15 %.")
            conteos = {"todos": r["total"], "fuera": r["fuera"], "referenciales": r["referenciales"]}
            with st.container(horizontal=True, vertical_alignment="bottom"):
                busqueda = st.text_input("Buscar ámbito", placeholder="Nombre o código", key="buscar_ambito",
                                         width=280)
                vista = st.segmented_control("Mostrar", list(VISTAS_CONTRASTE), default="todos", required=True,
                                             format_func=lambda v: f"{VISTAS_CONTRASTE[v]} ({conteos[v]})",
                                             key="vista_contraste")
            st.markdown(nota_lima(del_anio(todos, ANIO_CONTRASTE)))
            elegidos = filtrar_contraste(contraste, vista, busqueda)
            if elegidos.empty:
                st.info("Ningún ámbito cumple el filtro.")
            else:
                intervalos_col, tabla_col = st.columns([2, 3], gap="medium")
                with intervalos_col, tarjeta("intervalos", "Intervalo del INEI y réplica",
                                             "Banda: IC 95 % publicado. Anillo: cifra del INEI. Punto: réplica con "
                                             "la ENAHO. Escala de 0 a 50 %."):
                    st.plotly_chart(figura_intervalos(elegidos), key="intervalos",
                                    alt="Intervalo de confianza del INEI y réplica de la ENAHO por ámbito")
                with tabla_col:
                    st.dataframe(estilar_estados(tabla_contraste(elegidos), ["Estado"],
                                                 {"Réplica ENAHO (%)": "{:.2f}", "INEI publicado (%)": "{:.1f}",
                                                  "Diferencia (pp)": "{:.2f}"}),
                                 hide_index=True,
                                 alt="Pobreza por ámbito frente al Cuadro III.1 del INEI")
            st.caption("Fuente: INEI (2025), *Perú: Evolución de la pobreza monetaria 2015-2024*, informe técnico, "
                       "Cuadro III.1, páginas 219 y 220. Réplica: ENAHO 2024, módulos 34 y 02, ponderada por hogar "
                       "con la skill mapeando-enaho. Datos: `salidas/ambitos_vs_referencia.csv`.")

# ---------- BCRP ----------

with tab_bcrp:
    series = datos("bcrp", BCRP)
    if series.empty:
        st.info("Todavía no hay series guardadas. Cada vez que el agente usa `graficar_serie` del servidor MCP del "
                "BCRP, deja los datos graficados en `salidas/bcrp/` y aparecen aquí.")
    else:
        catalogo = catalogo_bcrp(series).set_index("archivo")

        def rango(a: str) -> str:
            return f"{etiqueta_periodo(catalogo.at[a, 'desde'])} a {etiqueta_periodo(catalogo.at[a, 'hasta'])}"

        archivo = st.selectbox("Serie guardada", catalogo.index.tolist(), key="serie",
                               format_func=lambda a: f"{catalogo.at[a, 'nombre']} ({catalogo.at[a, 'codigo']}, {rango(a)})")
        serie, ficha = series[series["archivo"] == archivo], catalogo.loc[archivo]
        with tarjeta("serie", ficha["nombre"], f"Serie {ficha['codigo']} · {rango(archivo)} · {ficha['n']} observaciones"):
            st.plotly_chart(figura_serie(serie), key="grafico_serie", alt=f"Serie del BCRP {ficha['nombre']}")
            with st.expander("Ver los datos"):
                st.dataframe(serie[["periodo", "valor"]], hide_index=True, alt=f"Datos de la serie {ficha['codigo']}")
        st.caption(f"Fuente: BCRP, BCRPData, serie {ficha['codigo']}. Consulta: {ficha['fuente']}")

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
        izquierda, derecha = st.columns(2, gap="medium")
        with izquierda, tarjeta("aciertos", "Aciertos por modo", "% de preguntas respondidas dentro de la tolerancia"):
            st.plotly_chart(figura_modos(por_modo, "acierto_pct",
                                         [f"{p:.0f} % ({a} de {n})" for p, a, n in
                                          zip(por_modo["acierto_pct"], por_modo["aciertos"], por_modo["preguntas"])],
                                         tope=110), key="aciertos", alt="Porcentaje de aciertos por modo")
        with derecha, tarjeta("tiempos", "Tiempo promedio por modo", "Segundos por respuesta"):
            st.plotly_chart(figura_modos(por_modo, "segundos_promedio", [f"{s:.0f} s" for s in por_modo["segundos_promedio"]]),
                            key="tiempos", alt="Segundos promedio por respuesta en cada modo")
        st.subheader("Por tipo de pregunta", anchor=False)
        st.dataframe(resumen["por_tipo"], hide_index=True, column_order=["tipo", "modo", "preguntas", "aciertos",
                                                                         "acierto_pct", "segundos_promedio"],
                     column_config=ETIQUETAS_TASAS | {"modo": "Modo"}, alt="Aciertos y tiempo por tipo y modo")
        st.subheader("Resultado de cada pregunta", anchor=False)
        pregunta = resumen["por_pregunta"]
        modos = [c for c in pregunta.columns if c not in ("id", "pregunta")]
        st.dataframe(estilar_estados(pregunta, modos), hide_index=True,
                     column_config={"id": "Pregunta", "pregunta": "Texto"}, alt="Resultado de cada pregunta por modo")
        st.caption("Fuente: `evaluacion/resultados.csv`, escrito por `evaluacion/evaluar.py`. Acierta si cada cifra "
                   "pedida cae dentro de su tolerancia; «no sabe» y «error» cuentan como no acierto.")

    st.subheader("Robustez ante pedidos ambiguos o imposibles", anchor=False)
    robustez = datos("robustez", ROBUSTEZ)
    if robustez.empty:
        st.info("Todavía no hay resultados de robustez. Los produce `uv run evaluacion/evaluar.py --robustez`, que "
                "escribe `evaluacion/robustez_resultados.csv`.")
    else:
        st.dataframe(resumen_robustez(robustez), hide_index=True, column_config=ETIQUETAS_TASAS,
                     column_order=["etiqueta", "casos", "cumple", "cumple_pct", "segundos_promedio"],
                     alt="Casos que cumplen la conducta esperada por modo")
        st.dataframe(estilar_estados(robustez, ["resultado"]), hide_index=True,
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
                st.metric(estado, n, border=True, icon=ICONOS_ESTADO.get(estado))
        st.dataframe(estilar_estados(consistencia, ["resultado"]), hide_index=True,
                     column_config={"fuente": "Fuente", "verificacion": "Verificación", "resultado": "Resultado",
                                    "detalle": "Detalle", "explicacion": "Explicación"},
                     alt="Verificaciones de consistencia entre herramientas")
        st.caption("Fuente: `salidas/consistencia.csv`, escrito por la skill verificando-consistencia.")
