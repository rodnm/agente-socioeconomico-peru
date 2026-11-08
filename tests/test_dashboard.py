"""El dashboard como lo ve un usuario y la lógica que lo alimenta: corre con las salidas versionadas, une el mapa por
código y no falla cuando una salida opcional todavía no existe. Ninguna prueba usa internet ni escribe en el repo."""
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

RAIZ = Path(__file__).resolve().parents[1]
APP = RAIZ / "dashboard" / "app.py"
GEOJSON = RAIZ / "referencias" / "limites_departamentales_ign.geojson"
CODIGOS = [f"{i:02d}" for i in range(1, 26)]

# Se carga por ruta: el pythonpath de pytest apunta a mcp/ y la raíz no debe ponerse delante del SDK `mcp`
_spec = importlib.util.spec_from_file_location("dashboard_logica", RAIZ / "dashboard" / "logica.py")
logica = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(logica)


def geo_falso(nombres: dict[str, str] | None = None, codigos: list[str] = CODIGOS) -> dict:
    """Un GeoJSON mínimo con los códigos dados; los nombres se pueden cruzar para comprobar que se une por código."""
    nombres = nombres or {}
    cuadro = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"FIRST_IDDP": c, "NOMBDEP": nombres.get(c, f"DEP {c}")}, "geometry": cuadro}
        for c in codigos]}


@pytest.fixture
def sin_logica_en_cache():
    """app.py importa `logica` por nombre: sin esto, una copia del dashboard reusaría el módulo de otra raíz."""
    sys.modules.pop("logica", None)
    yield
    sys.modules.pop("logica", None)


# ---------- la app ----------

def test_la_app_corre_con_las_salidas_versionadas(sin_logica_en_cache):
    app = AppTest.from_file(str(APP), default_timeout=60).run()

    assert not app.exception
    assert [t.label for t in app.tabs] == ["ENAHO 2024", "BCRP", "Evaluación", "Consistencia"]
    metricas = {m.label: m.value for m in app.metric}
    assert metricas["Pobreza monetaria nacional"] == "27.6 %"
    assert any(c.value.startswith("Fuente: INEI, ENAHO 2024. Ponderado con factor07 × mieperho") for c in app.caption)
    assert any(c.value.startswith("Fuente: INEI, ENAHO 2024. Ponderado con facpob07") for c in app.caption)


def test_la_app_muestra_cada_pestana_cuando_sus_salidas_existen(tmp_path, sin_logica_en_cache):
    """Una copia del dashboard en una raíz temporal con todas las salidas opcionales: nada se escribe en el repo."""
    (tmp_path / "dashboard").mkdir()
    for nombre in ("app.py", "logica.py"):
        shutil.copy(RAIZ / "dashboard" / nombre, tmp_path / "dashboard" / nombre)
    (tmp_path / "salidas" / "bcrp").mkdir(parents=True)
    for nombre in ("indicadores.csv", "mapa_vs_referencia.csv"):
        shutil.copy(RAIZ / "salidas" / nombre, tmp_path / "salidas" / nombre)
    (tmp_path / "datos").mkdir()
    if GEOJSON.exists():
        shutil.copy(GEOJSON, tmp_path / "datos" / GEOJSON.name)
    else:
        (tmp_path / "datos" / GEOJSON.name).write_text(json.dumps(geo_falso()), encoding="utf-8")
    pd.DataFrame({"periodo": ["2025-02", "2025-01", "2025-03"], "valor": [3.71, 3.75, 3.68],
                  "codigo": "PD04638PD", "nombre": "Tipo de cambio interbancario venta",
                  "fuente": "https://estadisticas.bcrp.gob.pe/x"}).to_csv(
        tmp_path / "salidas" / "bcrp" / "PD04638PD_2025-01_2025-03.csv", index=False)
    pd.DataFrame({"fuente": ["ENAHO", "ENAHO", "BCRP"], "verificacion": ["a", "b", "c"],
                  "resultado": ["OK", "OK", "DIFERENCIA"], "detalle": ["", "", ""], "explicacion": ["", "", ""]}).to_csv(
        tmp_path / "salidas" / "consistencia.csv", index=False)
    (tmp_path / "evaluacion").mkdir()
    evaluacion(tmp_path / "evaluacion" / "resultados.csv")
    pd.DataFrame({"id": ["r1", "r1", "r2"], "modo": ["A", "B", "A"], "pedido": ["x", "x", "y"],
                  "conducta_esperada": ["pide aclaración"] * 3, "conducta_observada": ["", "", ""],
                  "resultado": ["cumple", "cumple", "no cumple"], "segundos": [4, 5, 6]}).to_csv(
        tmp_path / "evaluacion" / "robustez_resultados.csv", index=False)

    app = AppTest.from_file(str(tmp_path / "dashboard" / "app.py"), default_timeout=60).run()

    assert not app.exception
    assert not app.info and not app.warning
    graficos = " ".join(g.proto.spec for g in app.get("plotly_chart"))
    assert "Tipo de cambio interbancario venta" in graficos and "Aciertos por modo" in graficos
    metricas = {m.label: m.value for m in app.metric}
    assert metricas["OK"] == "2" and metricas["DIFERENCIA"] == "1"


# ---------- ENAHO ----------

def test_tabla_departamentos_tiene_los_25_con_codigo_de_dos_digitos():
    tabla = logica.tabla_departamentos(logica.cargar_indicadores())

    assert len(tabla) == 25
    assert tabla["ccdd"].tolist() == CODIGOS
    assert tabla.set_index("ccdd").loc["15", "nombre"] == "Lima"
    assert tabla.set_index("ccdd").loc["07", "nombre"] == "Callao"


def test_kpis_traen_valor_y_fuente():
    kpis = {k["etiqueta"]: k for k in logica.kpis(logica.cargar_indicadores())}

    assert list(kpis) == ["Pobreza monetaria nacional", "Pobreza urbana", "Pobreza rural", "Pobreza extrema",
                          "Residentes en la muestra"]
    assert kpis["Pobreza monetaria nacional"]["valor"] == "27.6 %"
    assert kpis["Residentes en la muestra"]["valor"] == "108 664"
    assert "pobreza_nacional" in kpis["Pobreza monetaria nacional"]["ayuda"]
    assert "ENAHO 2024" in kpis["Pobreza monetaria nacional"]["ayuda"]


@pytest.mark.skipif(not GEOJSON.exists(), reason="falta datos/peru_departamental_simple.geojson (lo baja descargando-enaho)")
def test_unir_geometria_une_los_25_codigos_con_lima_y_callao_separados():
    geo = json.loads(GEOJSON.read_text(encoding="utf-8"))
    unida = logica.unir_geometria(geo, logica.tabla_departamentos(logica.cargar_indicadores())).set_index("ccdd")

    assert sorted(unida.index) == CODIGOS
    assert unida.loc["15", "pobreza"] == pytest.approx(27.0689)
    assert unida.loc["07", "pobreza"] == pytest.approx(33.8599)


def test_unir_geometria_une_por_codigo_y_no_por_nombre():
    tabla = logica.tabla_departamentos(logica.cargar_indicadores())
    cruzado = geo_falso({"07": "LIMA", "15": "CALLAO"})  # nombres intercambiados, códigos correctos

    unida = logica.unir_geometria(cruzado, tabla).set_index("ccdd")

    # La figura con código 07 recibe la pobreza del Callao aunque su nombre diga Lima
    assert unida.loc["07", ["nombre_mapa", "pobreza"]].tolist() == ["LIMA", pytest.approx(33.8599)]
    assert unida.loc["15", ["nombre_mapa", "pobreza"]].tolist() == ["CALLAO", pytest.approx(27.0689)]


def test_unir_geometria_rechaza_si_no_se_unen_los_25():
    tabla = logica.tabla_departamentos(logica.cargar_indicadores())

    with pytest.raises(ValueError, match="25"):
        logica.unir_geometria(geo_falso(codigos=CODIGOS[:24]), tabla)


def test_el_mapa_usa_una_escala_que_parte_de_cero_titulada_en_porcentaje():
    tabla = logica.tabla_departamentos(logica.cargar_indicadores())
    figura = logica.figura_mapa(logica.unir_geometria(geo_falso(), tabla), geo_falso())

    assert figura.layout.coloraxis.cmin == 0
    assert figura.layout.coloraxis.colorbar.title.text == "% de personas"
    assert len(figura.data[0].locations) == 25
    assert figura.data[0].featureidkey == "properties.FIRST_IDDP"  # plotly también asocia por código


def test_cargar_geojson_sin_archivo_ni_red_avisa_sin_fallar(tmp_path):
    geo, aviso = logica.cargar_geojson(tmp_path / "no.geojson", "http://127.0.0.1:9/peru.geojson")

    assert geo is None
    assert "mapa" in aviso


def test_cargar_geojson_prefiere_el_archivo_local(tmp_path):
    (tmp_path / "peru.geojson").write_text(json.dumps(geo_falso()), encoding="utf-8")

    geo, aviso = logica.cargar_geojson(tmp_path / "peru.geojson", "http://127.0.0.1:9/peru.geojson")

    assert aviso is None and len(geo["features"]) == 25


# ---------- BCRP ----------

def test_series_bcrp_ordena_los_periodos_de_cada_frecuencia(tmp_path):
    for archivo, periodos in {"PN_m.csv": ["2025-03", "2025-01", "2025-02"], "PN_t.csv": ["2025-T2", "2024-T4", "2025-T1"],
                              "PM_a.csv": ["2025", "2023", "2024"], "PD_d.csv": ["2026-10-02", "2026-10-01"]}.items():
        pd.DataFrame({"periodo": periodos, "valor": range(len(periodos)), "codigo": archivo[:2], "nombre": "x",
                      "fuente": "u"}).to_csv(tmp_path / archivo, index=False)

    tabla = logica.series_bcrp(tmp_path)
    orden = {a: g["periodo"].tolist() for a, g in tabla.groupby("archivo")}

    assert orden == {"PN_m": ["2025-01", "2025-02", "2025-03"], "PN_t": ["2024-T4", "2025-T1", "2025-T2"],
                     "PM_a": ["2023", "2024", "2025"], "PD_d": ["2026-10-01", "2026-10-02"]}
    assert tabla.loc[tabla["periodo"] == "2025-T2", "fecha"].iat[0] == pd.Timestamp(2025, 4, 1)


# ---------- evaluación ----------

def evaluacion(ruta: Path) -> None:
    pd.DataFrame({
        "id": ["p1", "p2", "p3", "p1", "p2"], "tipo": ["bcrp", "enaho", "enaho", "bcrp", "enaho"],
        "modo": ["A", "A", "A", "B", "B"], "pregunta": ["¿1?", "¿2?", "¿3?", "¿1?", "¿2?"],
        "verdad": [1, 2, 3, 1, 2], "valor": [1, 9, None, 1, 2], "unidad": "%", "tolerancia": 0.1,
        "resultado": ["acierta", "se equivoca", "no sabe", "acierta", "acierta"], "segundos": [10, 20, 30, 5, 15],
        "turnos": 1, "herramientas": ["", "", "", "serie", "Skill;Bash"], "fuente": "", "error": ""}).to_csv(ruta, index=False)


def test_resumen_evaluacion_cuenta_aciertos_y_promedia_segundos(tmp_path):
    evaluacion(tmp_path / "resultados.csv")

    resumen = logica.resumen_evaluacion(logica.cargar_evaluacion(tmp_path / "resultados.csv"))
    por_modo = resumen["por_modo"].set_index("modo")
    por_tipo = resumen["por_tipo"].set_index(["tipo", "modo"])
    pregunta = resumen["por_pregunta"].set_index("id")

    assert por_modo.index.tolist() == ["A", "B"]
    assert por_modo.loc["A", ["preguntas", "aciertos"]].tolist() == [3, 1]
    assert por_modo.loc["A", "acierto_pct"] == pytest.approx(100 / 3)
    assert por_modo.loc["A", "segundos_promedio"] == pytest.approx(20)
    assert por_modo.loc["B", "acierto_pct"] == pytest.approx(100)
    assert por_modo.loc["B", "segundos_promedio"] == pytest.approx(10)
    assert por_tipo.loc[("enaho", "A"), "acierto_pct"] == pytest.approx(0)
    assert por_tipo.loc[("enaho", "B"), "segundos_promedio"] == pytest.approx(15)
    assert pregunta.loc["p2", "A"] == "se equivoca" and pregunta.loc["p2", "B"] == "acierta"
    assert pd.isna(pregunta.loc["p3", "B"])


def test_resumen_robustez_cuenta_lo_que_cumple_por_modo():
    tabla = pd.DataFrame({"id": ["r1", "r2", "r1", "r2"], "modo": ["B", "B", "A", "A"],
                          "resultado": ["cumple", "cumple", "cumple", "no cumple"], "segundos": [1, 2, 3, 4]})

    resumen = logica.resumen_robustez(tabla).set_index("modo")

    assert resumen.index.tolist() == ["A", "B"]
    assert resumen.loc["A", ["casos", "cumple"]].tolist() == [2, 1]
    assert resumen.loc["A", "cumple_pct"] == pytest.approx(50)
    assert resumen.loc["B", "cumple_pct"] == pytest.approx(100)


# ---------- salidas opcionales ----------

def test_los_cargadores_devuelven_tablas_vacias_si_falta_el_archivo(tmp_path):
    (tmp_path / "bcrp_vacia").mkdir()
    (tmp_path / "vacio.csv").write_text("", encoding="utf-8")

    tablas = {"evaluacion": logica.cargar_evaluacion(tmp_path / "no.csv"),
              "robustez": logica.cargar_robustez(tmp_path / "no.csv"),
              "consistencia": logica.cargar_consistencia(tmp_path / "no.csv"),
              "consistencia vacía": logica.cargar_consistencia(tmp_path / "vacio.csv"),
              "comparación": logica.cargar_comparacion(tmp_path / "no.csv"),
              "bcrp sin carpeta": logica.series_bcrp(tmp_path / "no_existe"),
              "bcrp carpeta vacía": logica.series_bcrp(tmp_path / "bcrp_vacia")}

    assert all(t.empty for t in tablas.values())
    assert "resultado" in tablas["consistencia"].columns and "modo" in tablas["evaluacion"].columns
    assert {"periodo", "valor", "fecha", "archivo"} <= set(tablas["bcrp sin carpeta"].columns)
