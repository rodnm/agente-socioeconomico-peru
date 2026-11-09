"""El dashboard como lo ve un usuario y la lógica que lo alimenta: corre con las salidas versionadas, une el mapa por
código y no falla cuando una salida opcional todavía no existe. Ninguna prueba usa internet ni escribe en el repo."""
import base64
import importlib.util
import json
import shutil
import sys
import tomllib
import urllib.request
from pathlib import Path

import httpx
import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

RAIZ = Path(__file__).resolve().parents[1]
APP = RAIZ / "dashboard" / "app.py"
INDICADORES = RAIZ / "salidas" / "indicadores.csv"
CONTRASTE = RAIZ / "salidas" / "ambitos_vs_referencia.csv"
GEOJSON_AMBITOS = RAIZ / "referencias" / "limites_ambitos_ign.geojson"
# Los 26 ámbitos del Cuadro III.1 del INEI con los códigos de la capa del IGN: sin el 15, que se desagrega
AMBITOS = sorted([f"{i:02d}" for i in range(1, 26) if i != 15] + ["1501", "15_resto"])


def cargar(nombre: str, ruta: Path):
    """Se carga por ruta: el pythonpath de pytest apunta a mcp/ y la raíz no debe ponerse delante del SDK `mcp`."""
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


logica = cargar("dashboard_logica", RAIZ / "dashboard" / "logica.py")


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
    """Copia el dashboard y su tema a una raíz temporal con las salidas dadas y, si se pide, los límites del IGN."""
    (destino / "dashboard").mkdir()
    for nombre in ("app.py", "logica.py"):
        shutil.copy(RAIZ / "dashboard" / nombre, destino / "dashboard" / nombre)
    shutil.copytree(RAIZ / ".streamlit", destino / ".streamlit")
    (destino / "salidas" / "bcrp").mkdir(parents=True)
    for nombre in salidas:
        shutil.copy(RAIZ / "salidas" / nombre, destino / "salidas" / nombre)
    if limites:
        (destino / "referencias").mkdir()
        shutil.copy(GEOJSON_AMBITOS, destino / "referencias" / GEOJSON_AMBITOS.name)
    return destino / "dashboard" / "app.py"


def graficos(app: AppTest) -> list[dict]:
    return [json.loads(g.proto.spec) for g in app.get("plotly_chart")]


def trazo(app: AppTest, nombre: str) -> dict:
    """El trazo con el nombre dado: las figuras no llevan título, que va en su tarjeta."""
    for spec in graficos(app):
        for t in spec["data"]:
            if t.get("name") == nombre:
                return t
    raise AssertionError(f"No hay un trazo llamado «{nombre}»")


def numeros(campo) -> list[float]:
    """Plotly guarda los arreglos numéricos en binario dentro del JSON de la figura."""
    if isinstance(campo, dict):
        return np.frombuffer(base64.b64decode(campo["bdata"]), dtype=campo["dtype"]).tolist()
    return list(campo)


def tabla_del_contraste(app: AppTest) -> pd.DataFrame:
    return next(d.value for d in app.dataframe if "IC 95 % del INEI" in d.value.columns)


def metricas(app: AppTest) -> dict:
    return {m.label: m for m in app.metric}


def correr(app_py: Path = APP) -> AppTest:
    return AppTest.from_file(str(app_py), default_timeout=60).run()


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


# ---------- la app ----------

def test_la_app_corre_con_las_salidas_versionadas(sin_logica_en_cache, sin_red):
    app = correr()

    assert not app.exception
    assert [t.label for t in app.tabs] == ["Pobreza · ENAHO", "Series del BCRP", "Evaluación del agente", "Consistencia"]
    nacional = metricas(app)["Pobreza monetaria nacional"]
    assert nacional.value == "27.6 %" and nacional.proto.delta == "-1.5 pp"
    assert metricas(app)["Residentes en la muestra"].proto.delta == "33 691 hogares encuestados"
    assert "ENAHO 2024 · INEI" in [c.value for c in app.caption]
    assert any("de 6.0 % en Ica a 45.0 % en Cajamarca" in m.value for m in app.markdown)


def test_la_pestana_de_pobreza_tiene_una_sola_nota_de_fuente_con_ambos_ponderadores(sin_logica_en_cache, sin_red):
    app = correr()

    notas = [c.value for c in app.caption if c.value.startswith("Fuente: INEI, Encuesta Nacional de Hogares")]

    assert len(notas) == 1
    assert "factor07 × mieperho (por hogar)" in notas[0] and "facpob07 (por persona)" in notas[0]
    assert "Ponderado por hogar · nacional 27.6 %" in [c.value for c in app.caption]


def test_las_figuras_no_repiten_el_titulo_de_su_tarjeta(sin_logica_en_cache, sin_red):
    app = correr()

    titulos = [spec["layout"].get("title", {}).get("text") for spec in graficos(app)]

    assert titulos and not any(titulos)
    assert {"Mapa por ámbito territorial", "Ranking por ámbito", "Por área", "Por sexo", "Por edad"} <= {
        s.value for s in app.subheader}


def test_la_app_muestra_los_26_ambitos_con_lima_desagregada(sin_logica_en_cache, sin_red):
    app = correr()

    barras = trazo(app, "ranking_ambitos")
    mapa = trazo(app, "mapa_ambitos")
    colores = dict(zip(barras["y"], barras["marker"]["color"]))

    assert not app.exception
    assert len(barras["y"]) == 26
    assert {grupo("pobreza_lima_metropolitana_provincia"), grupo("pobreza_lima_provincias")} <= set(barras["y"])
    assert grupo("pobreza_dep_15") not in barras["y"]
    assert sorted(mapa["locations"]) == AMBITOS
    assert mapa["featureidkey"] == "properties.codigo"
    # La barra oscura marca Lima y el Callao; † marca las cifras referenciales del INEI
    assert {colores[n] for n in ("Lima Metropolitana", "Lima provincias", "Callao")} == {logica.BARRA_LIMA}
    assert colores["Cusco"] == logica.BARRA
    assert {"Ica †", "Madre de Dios †", "Moquegua †"} <= set(barras["y"])
    assert logica.NOTA_REFERENCIAL in [c.value for c in app.caption]


def test_el_selector_de_anio_cambia_las_cifras_del_tablero(sin_logica_en_cache, sin_red):
    app = correr()
    app.segmented_control(key="anio").set_value(2020).run()
    ambitos_2020 = logica.tabla_ambitos(logica.cargar_indicadores(anio=2020)).sort_values("pobreza", ascending=False)

    barras = trazo(app, "ranking_ambitos")

    assert not app.exception
    assert metricas(app)["Pobreza monetaria nacional"].value == "30.1 %"
    assert not metricas(app)["Pobreza monetaria nacional"].proto.delta  # 2020 es el primer año de la serie
    assert numeros(barras["x"]) == pytest.approx(ambitos_2020["pobreza"].tolist())
    assert not any(n.endswith("†") for n in barras["y"])  # el CV del INEI es el de 2024
    assert "ENAHO 2020 · INEI" in [c.value for c in app.caption]
    assert any("(ENAHO) 2020" in c.value for c in app.caption)


def test_la_app_sin_limites_avisa_como_generarlos_y_no_descarga(tmp_path, sin_logica_en_cache, sin_red):
    app = correr(raiz_temporal(tmp_path, limites=False))

    assert not app.exception
    assert any("scripts/preparar_limites.py" in w.value for w in app.warning)
    assert len(trazo(app, "ranking_ambitos")["y"]) == 26  # sin mapa, las barras siguen


def test_la_app_muestra_el_contraste_de_26_ambitos_con_lima_separada(sin_logica_en_cache, sin_red):
    app = correr()

    tabla = tabla_del_contraste(app).set_index("Código")

    assert not app.exception
    assert sorted(tabla.index) == AMBITOS and "15" not in tabla.index
    assert tabla.loc["1501", ["Ámbito", "INEI publicado (%)", "IC 95 % del INEI", "Estado"]].tolist() == [
        "Lima Metropolitana", 27.6, "25.0 a 30.1", "Coincide"]
    assert tabla.loc["15_resto", ["Ámbito", "INEI publicado (%)"]].tolist() == ["Lima provincias", 21.7]
    assert tabla.loc["02", "Ámbito"] == "Áncash" and not tabla["Ámbito"].str.isupper().any()
    assert tabla.loc["17", "Nota"] == "Referencial · CV 19.5 %"
    assert metricas(app)["Coinciden con la cifra publicada"].value == "26 de 26"
    assert any("Lima (departamento 15)" in m.value and "réplica: 27.07 %" in m.value for m in app.markdown)
    assert len(trazo(app, "Réplica ENAHO")["y"]) == 26


def test_el_contraste_se_filtra_por_las_cifras_referenciales(sin_logica_en_cache, sin_red):
    app = correr()
    app.segmented_control(key="vista_contraste").set_value("referenciales").run()

    tabla = tabla_del_contraste(app)

    assert not app.exception
    assert sorted(tabla["Ámbito"]) == ["Ica", "Madre de Dios", "Moquegua"]
    assert len(trazo(app, "Réplica ENAHO")["y"]) == 3


def test_la_app_sin_el_contraste_por_ambitos_indica_como_generarlo(tmp_path, sin_logica_en_cache, sin_red):
    app = correr(raiz_temporal(tmp_path))

    assert not app.exception
    assert any("ambitos_vs_referencia.csv" in i.value and "mapear.py" in i.value for i in app.info)
    assert not any(n.endswith("†") for n in trazo(app, "ranking_ambitos")["y"])


def test_la_app_corre_con_indicadores_sin_columna_anio(tmp_path, sin_logica_en_cache, sin_red):
    app_py = raiz_temporal(tmp_path)
    ind = pd.read_csv(INDICADORES, dtype={"id": str})
    ind[ind["anio"] == 2024].drop(columns="anio").to_csv(tmp_path / "salidas" / "indicadores.csv", index=False)

    app = correr(app_py)

    assert not app.exception
    assert metricas(app)["Pobreza monetaria nacional"].value == "27.6 %"
    assert len(trazo(app, "ranking_ambitos")["y"]) == 26


def test_la_app_muestra_cada_pestana_cuando_sus_salidas_existen(tmp_path, sin_logica_en_cache, sin_red):
    """Una copia del dashboard en una raíz temporal con todas las salidas opcionales: nada se escribe en el repo."""
    raiz_temporal(tmp_path, salidas=("indicadores.csv", "ambitos_vs_referencia.csv"))
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

    app = correr(tmp_path / "dashboard" / "app.py")

    assert not app.exception
    assert not app.info and not app.warning
    titulos = {s.value for s in app.subheader}
    assert {"Tipo de cambio interbancario venta", "Aciertos por modo", "Tiempo promedio por modo"} <= titulos
    assert "Serie PD04638PD · ene 2025 a mar 2025 · 3 observaciones" in [c.value for c in app.caption]
    assert {m.label: m.value for m in app.metric}["OK"] == "2"
    assert {m.label: m.value for m in app.metric}["DIFERENCIA"] == "1"


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
    assert logica.anios(todos) == [2020, 2021, 2022, 2023, 2024]
    assert set(logica.cargar_indicadores()["anio"]) == {2024}


def test_cargar_indicadores_sin_columna_anio_devuelve_todas_las_filas(tmp_path):
    ind = pd.read_csv(INDICADORES, dtype={"id": str})
    ind[ind["anio"] == 2024].drop(columns="anio").to_csv(tmp_path / "indicadores.csv", index=False)

    sin_anio = logica.cargar_indicadores(tmp_path / "indicadores.csv")

    assert "anio" not in sin_anio.columns
    assert logica.anios(sin_anio) == [2024]
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


def test_kpis_traen_la_serie_y_la_variacion_frente_al_anio_anterior():
    todos = logica.cargar_indicadores(anio=None)

    kpis = {k["id"]: k for k in logica.kpis(logica.del_anio(todos, 2024), todos)}
    primeros = {k["id"]: k for k in logica.kpis(logica.del_anio(todos, 2020), todos)}

    assert kpis["pobreza_nacional"]["serie"] == pytest.approx([30.13, 25.87, 27.52, 29.05, 27.58], abs=0.01)
    assert (kpis["pobreza_nacional"]["variacion"], kpis["pobreza_nacional"]["detalle"]) == ("-1.5 pp", "frente a 2023")
    assert kpis["residentes_habituales"]["variacion"] == "33 691 hogares encuestados"
    assert len(kpis["residentes_habituales"]["serie"]) == 5
    assert primeros["pobreza_nacional"]["serie"] is None and primeros["pobreza_nacional"]["variacion"] is None


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


def test_el_mapa_pinta_cinco_clases_de_0_a_50_por_ciento():
    tabla = logica.tabla_ambitos(logica.cargar_indicadores())
    figura = logica.figura_mapa(logica.unir_geometria(geo_falso(), tabla), geo_falso())
    escala = [(round(v, 4), c) for v, c in figura.layout.coloraxis.colorscale]

    assert (figura.layout.coloraxis.cmin, figura.layout.coloraxis.cmax) == (0, 50)
    assert figura.layout.coloraxis.showscale is False  # la leyenda por clases va bajo el mapa
    assert escala[:4] == [(0, "#F6DDB8"), (0.3, "#F6DDB8"), (0.3, "#EDB27A"), (0.44, "#EDB27A")]
    assert escala[-1] == (1, "#7F3212")
    assert len(figura.data[0].locations) == 26
    assert figura.data[0].featureidkey == "properties.codigo"  # plotly también asocia por código
    assert not figura.layout.title.text


def test_la_leyenda_cuenta_los_ambitos_de_cada_clase():
    leyenda = logica.leyenda_clases(logica.tabla_ambitos(logica.cargar_indicadores()))

    assert [(c["etiqueta"], c["ambitos"]) for c in leyenda] == [
        ("< 15 %", 4), ("15 a 22 %", 4), ("22 a 28 %", 8), ("28 a 35 %", 5), ("35 % o más", 5)]
    assert "8 ámbitos" in logica.leyenda_html(leyenda)


def test_las_barras_de_pobreza_usan_la_escala_fija_y_la_linea_nacional_con_borde():
    area = logica.filas(logica.cargar_indicadores(), "pobreza_area_")

    figura = logica.figura_barras(area, "valor", 27.6)
    borde, linea = figura.layout.shapes

    assert list(figura.layout.xaxis.range) == pytest.approx([0, 58])  # 0 a 50 % aunque el máximo sea 39.3, y las cifras
    assert list(figura.layout.xaxis.tickvals) == [0, 10, 20, 30, 40, 50]
    assert list(figura.data[1].text) == ["24.8", "39.3"] and figura.data[1].x[0] == pytest.approx(58)
    assert (borde.line.color, borde.line.width) == (logica.SUPERFICIE, 4.5)
    assert (linea.line.color, linea.line.dash, linea.x0) == (logica.TINTA, "dash", 27.6)
    assert figura.layout.annotations[0].text == "Nacional: 27.6 %"


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


# ---------- contraste con el INEI ----------

def test_resumen_contraste_cuenta_coincidencias_maximo_y_referenciales():
    resumen = logica.resumen_contraste(logica.cargar_contraste())

    assert (resumen["total"], resumen["dentro"], resumen["fuera"], resumen["referenciales"]) == (26, 26, 0, 3)
    assert resumen["diferencia_maxima"] == pytest.approx(0.05)
    assert "Amazonas" in resumen["donde"]


def test_filtrar_contraste_por_vista_y_por_busqueda_sin_tildes():
    contraste = logica.cargar_contraste()
    fuera = contraste.assign(dentro_de_tolerancia=contraste["codigo"].eq("08").map({True: False, False: True}))

    assert logica.filtrar_contraste(contraste, "todos", "ancash")["ambito"].tolist() == ["Áncash"]
    assert logica.filtrar_contraste(contraste, "todos", "LIMA")["codigo"].tolist() == ["1501", "15_resto"]
    assert logica.filtrar_contraste(contraste, "todos", "1501")["ambito"].tolist() == ["Lima Metropolitana"]
    assert logica.filtrar_contraste(contraste, "referenciales", "ica")["codigo"].tolist() == ["11"]
    assert logica.filtrar_contraste(fuera, "fuera")["ambito"].tolist() == ["Cusco"]
    assert logica.filtrar_contraste(contraste, "fuera").empty


def test_la_tolerancia_del_dashboard_es_la_de_mapeando_enaho():
    mapear = cargar("mapear_para_dashboard", RAIZ / ".claude" / "skills" / "mapeando-enaho" / "scripts" / "mapear.py")

    assert logica.TOLERANCIA == mapear.TOLERANCIA


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


@pytest.mark.parametrize("periodo, etiqueta", [("2025", "2025"), ("2025-T2", "T2 2025"), ("2024-01", "ene 2024"),
                                               ("2024-12", "dic 2024"), ("2026-10-02", "2 oct 2026")])
def test_etiqueta_periodo_en_espanol(periodo, etiqueta):
    assert logica.etiqueta_periodo(periodo) == etiqueta


def serie_bcrp(tmp_path: Path, periodos: list[str]) -> pd.DataFrame:
    pd.DataFrame({"periodo": periodos, "valor": range(len(periodos)), "codigo": "PN", "nombre": "x",
                  "fuente": "u"}).to_csv(tmp_path / "PN.csv", index=False)
    return logica.series_bcrp(tmp_path)


def test_la_serie_mensual_marca_cada_enero_en_espanol(tmp_path):
    figura = logica.figura_serie(serie_bcrp(tmp_path, [f"{a}-{m:02d}" for a in (2023, 2024, 2025) for m in range(1, 13)]))

    assert list(figura.layout.xaxis.ticktext) == ["ene 2023", "ene 2024", "ene 2025"]
    assert figura.data[0].mode == "lines" and figura.data[0].customdata[1] == "feb 2023"
    assert not figura.layout.title.text


def test_la_serie_anual_lleva_marcadores(tmp_path):
    figura = logica.figura_serie(serie_bcrp(tmp_path, ["2022", "2023", "2024"]))

    assert figura.data[0].mode == "lines+markers"
    assert list(figura.layout.xaxis.ticktext) == ["2022", "2023", "2024"]


# ---------- estados ----------

def test_los_estados_llevan_icono_y_texto_sobre_fondo_claro():
    assert logica.estilo_resultado("OK") == "background-color: #E3F1E7; color: #1D5B33"
    assert logica.estilo_resultado("se equivoca") == "background-color: #FBE2DF; color: #8A1F17"
    assert logica.estilo_resultado("otro") == "" and logica.estilo_resultado(float("nan")) == ""
    assert [logica.con_icono(v) for v in ("OK", "DIFERENCIA", "FALLA", "NO VERIFICABLE", "Coincide")] == [
        "✓ OK", "! DIFERENCIA", "✕ FALLA", "– NO VERIFICABLE", "✓ Coincide"]
    assert logica.con_icono(float("nan")) == "" and logica.con_icono("otro") == "otro"


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
              "contraste": logica.cargar_contraste(tmp_path / "no.csv"),
              "bcrp sin carpeta": logica.series_bcrp(tmp_path / "no_existe"),
              "bcrp carpeta vacía": logica.series_bcrp(tmp_path / "bcrp_vacia")}

    assert all(t.empty for t in tablas.values())
    assert "resultado" in tablas["consistencia"].columns and "modo" in tablas["evaluacion"].columns
    assert {"codigo", "referencial", "dentro_de_tolerancia"} <= set(tablas["contraste"].columns)
    assert {"periodo", "valor", "fecha", "archivo"} <= set(tablas["bcrp sin carpeta"].columns)
