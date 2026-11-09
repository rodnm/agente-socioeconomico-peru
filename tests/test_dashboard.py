"""El dashboard como lo ve un usuario y la lógica que lo alimenta: corre con las salidas versionadas, une el mapa por
código y no falla cuando una salida opcional todavía no existe. Ninguna prueba usa internet ni escribe en el repo."""
import importlib.util
import json
import shutil
import sys
import tomllib
import urllib.request
from pathlib import Path

import httpx
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

RAIZ = Path(__file__).resolve().parents[1]
APP = RAIZ / "dashboard" / "app.py"
INDICADORES = RAIZ / "salidas" / "indicadores.csv"
GEOJSON_AMBITOS = RAIZ / "referencias" / "limites_ambitos_ign.geojson"
# Los 26 ámbitos del Cuadro III.1 del INEI con los códigos de la capa del IGN: sin el 15, que se desagrega
AMBITOS = sorted([f"{i:02d}" for i in range(1, 26) if i != 15] + ["1501", "15_resto"])
SIN_CIFRA = "sin cifra publicada por el INEI"

# Se carga por ruta: el pythonpath de pytest apunta a mcp/ y la raíz no debe ponerse delante del SDK `mcp`
_spec = importlib.util.spec_from_file_location("dashboard_logica", RAIZ / "dashboard" / "logica.py")
logica = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(logica)


def geo_falso(nombres: dict[str, str] | None = None, codigos: list[str] = AMBITOS) -> dict:
    """Un GeoJSON mínimo con los códigos dados; los nombres se pueden cruzar para comprobar que se une por código."""
    nombres = nombres or {}
    cuadro = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"codigo": c, "nombre": nombres.get(c, f"Ámbito {c}")}, "geometry": cuadro}
        for c in codigos]}


def grupo(id_indicador: str) -> str:
    """La etiqueta que limpiando-enaho dejó para un id en 2024: las pruebas no fijan el texto de las etiquetas."""
    ind = logica.cargar_indicadores()
    return ind.loc[ind["id"] == id_indicador, "grupo"].iat[0]


def raiz_temporal(destino: Path, salidas: tuple[str, ...] = ("indicadores.csv",), limites: bool = True) -> Path:
    """Copia el dashboard a una raíz temporal con las salidas dadas y, si se pide, los límites del IGN."""
    (destino / "dashboard").mkdir()
    for nombre in ("app.py", "logica.py"):
        shutil.copy(RAIZ / "dashboard" / nombre, destino / "dashboard" / nombre)
    (destino / "salidas" / "bcrp").mkdir(parents=True)
    for nombre in salidas:
        shutil.copy(RAIZ / "salidas" / nombre, destino / "salidas" / nombre)
    if limites:
        (destino / "referencias").mkdir()
        shutil.copy(GEOJSON_AMBITOS, destino / "referencias" / GEOJSON_AMBITOS.name)
    return destino / "dashboard" / "app.py"


def trazo(app: AppTest, tipo: str, titulo: str) -> dict:
    """El primer trazo de tipo dado del gráfico cuyo título contiene el texto dado."""
    for grafico in app.get("plotly_chart"):
        spec = json.loads(grafico.proto.spec)
        if spec["data"][0]["type"] == tipo and titulo in spec["layout"]["title"]["text"]:
            return spec["data"][0]
    raise AssertionError(f"No hay un gráfico {tipo} titulado «{titulo}»")


@pytest.fixture
def sin_logica_en_cache():
    """app.py importa `logica` por nombre: sin esto, una copia del dashboard reusaría el módulo de otra raíz."""
    sys.modules.pop("logica", None)
    yield
    sys.modules.pop("logica", None)


@pytest.fixture
def sin_red(monkeypatch):
    """Hace fallar la prueba si algo intenta descargar por httpx o urllib."""
    def prohibido(*args, **kwargs):
        raise AssertionError(f"El dashboard intentó usar la red: {args[:2]}")
    monkeypatch.setattr(httpx, "get", prohibido)
    monkeypatch.setattr(httpx.Client, "send", prohibido)
    monkeypatch.setattr(urllib.request, "urlopen", prohibido)


def comparacion_con_lima_sin_cifra(ruta: Path, tolerancia_lima: str) -> None:
    """Como la escribe mapeando-enaho: Lima (15) sin referencia del INEI; el resto con su cifra del Cuadro III.1."""
    ruta.write_text("ccdd,departamento,pobreza_pct,referencia_inei,diferencia,dentro_de_tolerancia\n"
                    "07,CALLAO,33.86,33.9,0.04,True\n"
                    f"15,LIMA,27.07,,,{tolerancia_lima}\n"
                    "16,LORETO,43.2,43.0,0.2,False\n", encoding="utf-8")


# ---------- la app ----------

def test_la_app_corre_con_las_salidas_versionadas(sin_logica_en_cache, sin_red):
    app = AppTest.from_file(str(APP), default_timeout=60).run()

    assert not app.exception
    assert [t.label for t in app.tabs] == ["ENAHO 2024", "BCRP", "Evaluación", "Consistencia"]
    metricas = {m.label: m.value for m in app.metric}
    assert metricas["Pobreza monetaria nacional"] == "27.6 %"
    assert any(c.value.startswith("Fuente: INEI, ENAHO 2024. Ponderado con factor07 × mieperho") for c in app.caption)
    assert any(c.value.startswith("Fuente: INEI, ENAHO 2024. Ponderado con facpob07") for c in app.caption)


def test_la_app_muestra_los_26_ambitos_con_lima_desagregada(sin_logica_en_cache, sin_red):
    app = AppTest.from_file(str(APP), default_timeout=60).run()

    barras = trazo(app, "bar", "por ámbito")
    mapa = trazo(app, "choropleth", "por ámbito")

    assert not app.exception
    assert len(barras["y"]) == 26
    assert {grupo("pobreza_lima_metropolitana_provincia"), grupo("pobreza_lima_provincias")} <= set(barras["y"])
    assert grupo("pobreza_dep_15") not in barras["y"]
    assert sorted(mapa["locations"]) == AMBITOS
    assert mapa["featureidkey"] == "properties.codigo"


def test_la_app_sin_limites_avisa_como_generarlos_y_no_descarga(tmp_path, sin_logica_en_cache, sin_red):
    app = AppTest.from_file(str(raiz_temporal(tmp_path, limites=False)), default_timeout=60).run()

    assert not app.exception
    assert any("scripts/preparar_limites.py" in w.value for w in app.warning)
    assert len(trazo(app, "bar", "por ámbito")["y"]) == 26  # sin mapa, las barras siguen


@pytest.mark.parametrize("tolerancia_lima", ["", "False"])
def test_la_app_muestra_lima_sin_cifra_del_inei_en_el_contraste(tmp_path, sin_logica_en_cache, sin_red,
                                                                 tolerancia_lima):
    app_py = raiz_temporal(tmp_path)
    comparacion_con_lima_sin_cifra(tmp_path / "salidas" / "mapa_vs_referencia.csv", tolerancia_lima)

    app = AppTest.from_file(str(app_py), default_timeout=60).run()
    contraste = next(e for e in app.expander if "INEI" in e.label)
    tabla = contraste.dataframe[0].value.set_index("ccdd")

    assert not app.exception
    assert "Cuadro III.1" in contraste.label and "sesión 16" not in contraste.label
    assert f"LIMA (15): {SIN_CIFRA}" in contraste.markdown[0].value
    assert "1 de 2 departamentos con cifra publicada por el INEI" in contraste.markdown[0].value
    assert tabla.loc["15", "referencia_inei"] == SIN_CIFRA
    assert not tabla.isna().any().any()
    assert not tabla.astype(str).isin(["nan", "NaN", "None", "<NA>"]).any().any()


def test_la_app_corre_con_indicadores_sin_columna_anio(tmp_path, sin_logica_en_cache, sin_red):
    app_py = raiz_temporal(tmp_path)
    ind = pd.read_csv(INDICADORES, dtype={"id": str})
    ind[ind["anio"] == 2024].drop(columns="anio").to_csv(tmp_path / "salidas" / "indicadores.csv", index=False)

    app = AppTest.from_file(str(app_py), default_timeout=60).run()

    assert not app.exception
    assert {m.label: m.value for m in app.metric}["Pobreza monetaria nacional"] == "27.6 %"
    assert len(trazo(app, "bar", "por ámbito")["y"]) == 26


def test_la_app_muestra_cada_pestana_cuando_sus_salidas_existen(tmp_path, sin_logica_en_cache, sin_red):
    """Una copia del dashboard en una raíz temporal con todas las salidas opcionales: nada se escribe en el repo."""
    raiz_temporal(tmp_path, salidas=("indicadores.csv", "mapa_vs_referencia.csv"))
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

def test_tabla_ambitos_tiene_26_con_lima_desagregada_y_sin_el_departamento_15():
    tabla = logica.tabla_ambitos(logica.cargar_indicadores()).set_index("codigo")

    assert tabla.index.tolist() == AMBITOS
    assert "15" not in tabla.index
    assert tabla.loc["1501", "pobreza"] == pytest.approx(27.5845)  # Lima Metropolitana sin el Callao
    assert tabla.loc["15_resto", "pobreza"] == pytest.approx(21.7156)
    assert tabla.loc["07", "pobreza"] == pytest.approx(33.8599)


def test_tabla_ambitos_se_guia_por_el_id_y_no_por_la_etiqueta():
    ind = logica.cargar_indicadores()
    etiquetas = {"pobreza_lima_metropolitana": "Lima Metropolitana y Callao",
                 "pobreza_lima_metropolitana_provincia": "Lima Metropolitana", "pobreza_lima_provincias": "Lima provincias"}
    ind["grupo"] = ind["id"].map(etiquetas).fillna(ind["grupo"])

    tabla = logica.tabla_ambitos(ind).set_index("codigo")

    assert tabla.loc[["1501", "15_resto"], "nombre"].tolist() == ["Lima Metropolitana", "Lima provincias"]
    # El dominio 8 (Lima Metropolitana con el Callao, 28.2 %) no es un ámbito
    assert "Lima Metropolitana y Callao" not in tabla["nombre"].tolist()
    assert not tabla["pobreza"].round(4).eq(28.2117).any()


def test_tabla_ambitos_rechaza_salidas_sin_lima_desagregada():
    ind = logica.cargar_indicadores()

    with pytest.raises(ValueError, match="26"):
        logica.tabla_ambitos(ind[ind["id"] != "pobreza_lima_provincias"])


def test_cargar_indicadores_filtra_2024_por_defecto():
    todos = logica.cargar_indicadores(anio=None)

    assert set(todos["anio"]) == {2020, 2021, 2022, 2023, 2024}
    assert set(logica.cargar_indicadores()["anio"]) == {2024}


def test_cargar_indicadores_sin_columna_anio_devuelve_todas_las_filas(tmp_path):
    ind = pd.read_csv(INDICADORES, dtype={"id": str})
    ind[ind["anio"] == 2024].drop(columns="anio").to_csv(tmp_path / "indicadores.csv", index=False)

    sin_anio = logica.cargar_indicadores(tmp_path / "indicadores.csv")

    assert "anio" not in sin_anio.columns
    assert sin_anio["id"].tolist() == logica.cargar_indicadores()["id"].tolist()
    assert logica.kpis(sin_anio) == logica.kpis(logica.cargar_indicadores())


def test_kpis_traen_valor_y_fuente():
    kpis = {k["etiqueta"]: k for k in logica.kpis(logica.cargar_indicadores())}

    assert list(kpis) == ["Pobreza monetaria nacional", "Pobreza urbana", "Pobreza rural", "Pobreza extrema",
                          "Residentes en la muestra"]
    assert kpis["Pobreza monetaria nacional"]["valor"] == "27.6 %"
    assert kpis["Residentes en la muestra"]["valor"] == "108 664"
    assert "pobreza_nacional" in kpis["Pobreza monetaria nacional"]["ayuda"]
    assert "ENAHO 2024" in kpis["Pobreza monetaria nacional"]["ayuda"]


def test_unir_geometria_une_los_26_ambitos_de_la_capa_del_ign():
    geo = json.loads(GEOJSON_AMBITOS.read_text(encoding="utf-8"))
    unida = logica.unir_geometria(geo, logica.tabla_ambitos(logica.cargar_indicadores())).set_index("codigo")

    assert sorted(unida.index) == AMBITOS
    assert unida.loc["1501", "pobreza"] == pytest.approx(27.5845)
    assert unida.loc["15_resto", "pobreza"] == pytest.approx(21.7156)
    assert unida.loc["07", "pobreza"] == pytest.approx(33.8599)


def test_unir_geometria_une_por_codigo_y_no_por_nombre():
    tabla = logica.tabla_ambitos(logica.cargar_indicadores())
    cruzado = geo_falso({"07": "Lima Metropolitana", "1501": "Callao"})  # nombres intercambiados, códigos correctos

    unida = logica.unir_geometria(cruzado, tabla).set_index("codigo")

    # La figura con código 07 recibe la pobreza del Callao aunque su nombre diga Lima Metropolitana
    assert unida.loc["07", ["nombre_mapa", "pobreza"]].tolist() == ["Lima Metropolitana", pytest.approx(33.8599)]
    assert unida.loc["1501", ["nombre_mapa", "pobreza"]].tolist() == ["Callao", pytest.approx(27.5845)]


def test_unir_geometria_rechaza_si_no_se_unen_los_26():
    tabla = logica.tabla_ambitos(logica.cargar_indicadores())

    with pytest.raises(ValueError, match="26"):
        logica.unir_geometria(geo_falso(codigos=AMBITOS[:25]), tabla)


def test_el_mapa_usa_una_escala_que_parte_de_cero_titulada_en_porcentaje():
    tabla = logica.tabla_ambitos(logica.cargar_indicadores())
    figura = logica.figura_mapa(logica.unir_geometria(geo_falso(), tabla), geo_falso())

    assert figura.layout.coloraxis.cmin == 0
    assert figura.layout.coloraxis.colorbar.title.text == "% de personas"
    assert len(figura.data[0].locations) == 26
    assert figura.data[0].featureidkey == "properties.codigo"  # plotly también asocia por código


def test_cargar_geojson_sin_archivo_indica_preparar_limites_sin_usar_la_red(tmp_path, sin_red):
    geo, aviso = logica.cargar_geojson(tmp_path / "no.geojson")

    assert geo is None
    assert "scripts/preparar_limites.py" in aviso and "mapa" in aviso


def test_cargar_geojson_lee_el_archivo_local(tmp_path, sin_red):
    (tmp_path / "ambitos.geojson").write_text(json.dumps(geo_falso()), encoding="utf-8")

    geo, aviso = logica.cargar_geojson(tmp_path / "ambitos.geojson")

    assert aviso is None and len(geo["features"]) == 26


def area_con_signo(anillo: list) -> float:
    """Positiva si el anillo gira en sentido antihorario (fórmula del área de Gauss)."""
    return sum(x0 * y1 - x1 * y0 for (x0, y0, *_), (x1, y1, *_) in zip(anillo, anillo[1:]))


def poligonos(geometria: dict) -> list:
    return [geometria["coordinates"]] if geometria["type"] == "Polygon" else geometria["coordinates"]


def test_cargar_geojson_deja_los_anillos_exteriores_en_sentido_horario_para_plotly():
    """d3-geo (Plotly) lee un anillo exterior antihorario como el globo menos el polígono: así el mapa mostraba solo
    Ucayali sobre un fondo de su color. El archivo versionado sigue en el sentido de RFC 7946."""
    crudo = json.loads(GEOJSON_AMBITOS.read_text(encoding="utf-8"))
    geo, aviso = logica.cargar_geojson()

    assert aviso is None
    assert any(area_con_signo(p[0]) > 0 for f in crudo["features"] for p in poligonos(f["geometry"]))
    for f in geo["features"]:
        for exterior, *huecos in poligonos(f["geometry"]):
            assert area_con_signo(exterior) < 0, f["properties"]["codigo"]
            assert all(area_con_signo(h) > 0 for h in huecos), f["properties"]["codigo"]
    assert json.loads(GEOJSON_AMBITOS.read_text(encoding="utf-8")) == crudo  # el archivo no cambia


def test_el_tema_claro_fijo_usa_la_paleta_tierra_de_las_figuras():
    tema = tomllib.loads((RAIZ / ".streamlit" / "config.toml").read_text(encoding="utf-8"))["theme"]

    assert tema["base"] == "light"
    assert (tema["primaryColor"], tema["backgroundColor"], tema["textColor"]) == (logica.ACENTO, logica.FONDO,
                                                                                 logica.TINTA)
    assert logica.BARRA == "#C46A35" and logica.REFERENCIA == logica.TINTA
    assert [color for _, color, _ in logica.CLASES] == ["#F6DDB8", "#EDB27A", "#DB8448", "#B95A26", "#7F3212"]


def test_el_dashboard_lee_los_limites_del_ign_y_no_la_copia_del_curso():
    assert logica.GEOJSON_AMBITOS == GEOJSON_AMBITOS
    for archivo in (APP, RAIZ / "dashboard" / "logica.py"):
        codigo = archivo.read_text(encoding="utf-8")
        assert "raw.githubusercontent.com" not in codigo and "peru_departamental_simple" not in codigo


@pytest.mark.parametrize("tolerancia_lima", ["", "False"])
def test_tabla_comparacion_rotula_lima_sin_cifra_del_inei(tmp_path, tolerancia_lima):
    comparacion_con_lima_sin_cifra(tmp_path / "comparacion.csv", tolerancia_lima)
    comparacion = logica.cargar_comparacion(tmp_path / "comparacion.csv")

    tabla = logica.tabla_comparacion(comparacion).set_index("ccdd")
    resumen = logica.resumen_comparacion(comparacion)

    assert tabla.loc["15", ["referencia_inei", "diferencia", "dentro_de_tolerancia"]].tolist() == [
        SIN_CIFRA, "no aplica", "no aplica"]
    assert tabla.loc["07", ["referencia_inei", "diferencia", "dentro_de_tolerancia"]].tolist() == ["33.9", "0.04", "Sí"]
    assert tabla.loc["16", "dentro_de_tolerancia"] == "No"
    assert not tabla.isna().any().any()
    assert resumen == {"con_referencia": 2, "dentro": 1, "sin_referencia": [("15", "LIMA")]}


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
