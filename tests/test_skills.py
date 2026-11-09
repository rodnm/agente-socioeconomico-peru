"""Las skills de la ENAHO probadas como las usa Claude: corriendo sus scripts.

    uv run pytest tests/test_skills.py

Cada script ubica la raíz del proyecto a partir de su propia ruta, así que basta copiarlo a una carpeta temporal
para probarlo aislado, sin tocar salidas/ del repo. Las pruebas que necesitan los microdatos se saltan si faltan
los zip en datos/ (se bajan con la skill descargando-enaho).
"""
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]
SKILLS = RAIZ / ".claude" / "skills"
ZIPS = [RAIZ / "datos" / "966-Modulo34.zip", RAIZ / "datos" / "966-Modulo02.zip"]
con_microdatos = pytest.mark.skipif(not all(z.is_file() for z in ZIPS), reason="faltan los zip de la ENAHO en datos/")


def copiar_proyecto(destino: Path, skills=("limpiando-enaho", "graficando-enaho", "mapeando-enaho"),
                    datos=False) -> Path:
    """Una raíz mínima: las skills pedidas, las referencias y, si se pide, los microdatos."""
    for skill in skills:
        shutil.copytree(SKILLS / skill, destino / ".claude" / "skills" / skill)
    shutil.copytree(RAIZ / "referencias", destino / "referencias")
    shutil.copytree(RAIZ / "scripts", destino / "scripts")
    if datos:
        (destino / "datos").mkdir()
        for archivo in ZIPS:
            shutil.copy(archivo, destino / "datos")
    return destino


def correr(raiz: Path, skill: str, script: str, *args: str) -> subprocess.CompletedProcess:
    ruta = raiz / ".claude" / "skills" / skill / "scripts" / script
    return subprocess.run([sys.executable, str(ruta), *args], capture_output=True, text=True, encoding="utf-8",
                          cwd=raiz)


def test_limpiar_rechaza_otro_anio(tmp_path):
    r = correr(copiar_proyecto(tmp_path), "limpiando-enaho", "limpiar.py", "--anio", "2019")
    assert r.returncode != 0
    assert "no soportado" in r.stderr


def test_limpiar_pide_descargar_si_faltan_los_zip(tmp_path):
    r = correr(copiar_proyecto(tmp_path), "limpiando-enaho", "limpiar.py")
    assert r.returncode != 0
    assert "descargando-enaho" in r.stderr


@pytest.mark.parametrize("skill,script", [("graficando-enaho", "graficar.py"), ("mapeando-enaho", "mapear.py")])
def test_graficos_y_mapa_piden_limpiar_primero(tmp_path, skill, script):
    raiz = copiar_proyecto(tmp_path)
    r = correr(raiz, skill, script)
    assert r.returncode != 0
    assert "limpiando-enaho" in r.stderr
    assert not (raiz / "figuras").exists() and not (raiz / "mapas").exists()


def test_indicadores_versionados_cumplen_las_validaciones():
    df = pd.read_csv(RAIZ / "salidas" / "indicadores.csv")
    if "anio" in df.columns:
        df = df[df["anio"] == 2024]
    tabla = df.set_index("id")
    assert abs(tabla.loc["pobreza_nacional", "valor"] - 27.6) <= 0.1
    assert tabla.loc["residentes_habituales", "valor"] == 108_664
    assert tabla.loc["departamentos", "valor"] == 25
    assert tabla.index.str.startswith("pobreza_dep_").sum() == 25
    assert abs(tabla.loc["pobreza_area_urbana", "valor"] - 24.8) <= 0.1
    assert abs(tabla.loc["pobreza_area_rural", "valor"] - 39.3) <= 0.1
    assert "pobreza_lima_metropolitana_provincia" in tabla.index
    assert "pobreza_lima_provincias" in tabla.index
    validacion = (RAIZ / "salidas" / "validacion.txt").read_text(encoding="utf-8")
    assert "FALLA" not in validacion


@con_microdatos
def test_limpiar_reproduce_los_indicadores_versionados(tmp_path):
    raiz = copiar_proyecto(tmp_path, skills=("limpiando-enaho",), datos=True)
    r = correr(raiz, "limpiando-enaho", "limpiar.py", "--anio", "2024")
    assert r.returncode == 0, r.stderr
    nuevos = pd.read_csv(raiz / "salidas" / "indicadores.csv")
    versionados = pd.read_csv(RAIZ / "salidas" / "indicadores.csv")
    if "anio" in versionados.columns:
        versionados = versionados[versionados["anio"] == 2024].reset_index(drop=True)
    if "anio" in nuevos.columns:
        nuevos = nuevos[nuevos["anio"] == 2024].reset_index(drop=True)
    pd.testing.assert_frame_equal(nuevos, versionados)


@con_microdatos
def test_limpiar_se_detiene_si_falla_una_validacion(tmp_path):
    # Una referencia alterada para Cusco debe detener el proceso sin escribir la base: nada de forzar cifras
    raiz = copiar_proyecto(tmp_path, skills=("limpiando-enaho",), datos=True)
    referencia = raiz / "referencias" / "inei_pobreza_2024.csv"
    tabla = pd.read_csv(referencia, dtype={"ccdd": str})
    tabla.loc[tabla["ccdd"] == "08", "valor"] = 50.0
    tabla.to_csv(referencia, index=False)
    r = correr(raiz, "limpiando-enaho", "limpiar.py", "--anio", "2024")
    assert r.returncode != 0
    assert "comprobaciones fallaron" in r.stderr
    assert "FALLA Pobreza en Cusco" in (raiz / "salidas" / "validacion.txt").read_text(encoding="utf-8")
    assert not (raiz / "salidas" / "personas_2024.parquet").exists()


@con_microdatos
def test_cadena_completa_limpiar_graficar_mapear(tmp_path):
    raiz = copiar_proyecto(tmp_path, datos=True)
    assert correr(raiz, "limpiando-enaho", "limpiar.py").returncode == 0
    g = correr(raiz, "graficando-enaho", "graficar.py", "--por", "departamento")
    m = correr(raiz, "mapeando-enaho", "mapear.py")
    assert g.returncode == 0 and m.returncode == 0, g.stderr + m.stderr
    assert (raiz / "figuras" / "pobreza_por_departamento.png").stat().st_size > 0
    assert "25 departamentos con dato" in m.stdout
    comparacion = pd.read_csv(raiz / "salidas" / "mapa_vs_referencia.csv", dtype={"ccdd": str}).set_index("ccdd")
    assert len(comparacion) == 25 and {"07", "15"} <= set(comparacion.index)  # Lima y Callao por separado
    assert comparacion.drop("15")["dentro_de_tolerancia"].astype(bool).all()
    assert comparacion.loc["15", "observacion"] == "sin cifra publicada por el INEI"
    ambitos = pd.read_csv(raiz / "salidas" / "ambitos_vs_referencia.csv", dtype={"codigo": str}).set_index("codigo")
    assert len(ambitos) == 26 and {"1501", "15_resto"} <= set(ambitos.index)
    assert ambitos["dentro_de_tolerancia"].all()


# --- Gráficos y mapas revisados sin microdatos: una base sintética reproduce las tasas publicadas por el INEI ---

REFERENCIA_INEI = RAIZ / "referencias" / "inei_pobreza_2024.csv"
LIMITES_DEP = RAIZ / "referencias" / "limites_departamentales_ign.geojson"
LIMITES_AMBITOS = RAIZ / "referencias" / "limites_ambitos_ign.geojson"
SERIE = {
    "pobreza_nacional": [30.1, 25.9, 27.5, 29.0, 27.6],
    "pobreza_area_rural": [45.7, 39.7, 41.1, 39.8, 39.3],
    "pobreza_area_urbana": [26.0, 22.3, 24.1, 26.4, 24.8],
    "pobreza_lima_metropolitana_provincia": [26.6, 24.4, 26.9, 28.1, 27.6],
    "pobreza_lima_provincias": [26.5, 26.4, 22.9, 26.2, 21.7],
}
NOMBRES_VIEJOS_DE_LIMA = ("Lima Metro\n", "Lima Prov", "Lima Provincias", "(prov.)")


def cargar(skill: str, script: str):
    """Importa el script de una skill como módulo, para llamar a sus funciones."""
    ruta = SKILLS / skill / "scripts" / script
    especificacion = importlib.util.spec_from_file_location(f"{skill.replace('-', '_')}_{ruta.stem}", ruta)
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    return modulo


def referencia_inei() -> pd.DataFrame:
    """Las filas territoriales de la tabla del INEI, sin el departamento 15, que el INEI no publica en conjunto."""
    tabla = pd.read_csv(REFERENCIA_INEI, dtype={"ccdd": str}).dropna(subset=["ccdd"])
    return tabla[tabla["ccdd"] != "15"]


def base_sintetica() -> pd.DataFrame:
    """Dos hogares por ámbito, con pesos que reproducen la tasa publicada por el INEI para ese ámbito."""
    filas = []
    for fila in referencia_inei().itertuples():
        departamento = fila.ccdd[:2]
        ubigeo = {"1501": "150101", "15_resto": "150201"}.get(fila.ccdd, f"{departamento}0101")
        nombre = "Lima" if departamento == "15" else fila.ambito
        for pobre, peso in ((True, fila.valor), (False, 100 - fila.valor)):
            filas.append({"conglome": f"{fila.ccdd}{int(pobre)}", "vivienda": "001", "hogar": "11", "pobre": pobre,
                          "peso_hogar": peso, "facpob07": peso, "departamento": departamento,
                          "departamento_nombre": nombre, "ubigeo": ubigeo, "urbano": True, "p207": 1.0, "p208a": 30.0})
    return pd.DataFrame(filas)


@pytest.fixture
def figuras_guardadas(monkeypatch):
    """Anota cada figura en lugar de escribirla: así se revisan sus textos sin tocar figuras/ ni mapas/ del repo."""
    from matplotlib.figure import Figure
    guardadas = []
    monkeypatch.setattr(Figure, "savefig", lambda self, *args, **kwargs: guardadas.append(self))
    return guardadas


def dibujada(figuras_guardadas):
    """La última figura, dibujada de nuevo: al cerrarla, pyplot le quita el lienzo que mide los textos."""
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    figura = figuras_guardadas[-1]
    FigureCanvasAgg(figura).draw()
    return figura


def textos_de(figura) -> str:
    return " ".join(t.get_text() for t in figura.texts).replace("\n", " ").replace(" ", " ")


def caja_del_texto(texto, renderer):
    """Solo las letras: en una anotación, get_window_extent incluye además la guía que la une a su punto."""
    from matplotlib.text import Text
    return Text.get_window_extent(texto, renderer)


def choques(textos, renderer) -> list:
    cajas = [(t.get_text(), caja_del_texto(t, renderer)) for t in textos]
    return [(a, b) for i, (a, caja_a) in enumerate(cajas) for b, caja_b in cajas[i + 1:] if caja_a.overlaps(caja_b)]


@pytest.fixture
def barras_de_ambitos(tmp_path, monkeypatch, figuras_guardadas):
    graficar = cargar("graficando-enaho", "graficar.py")
    base_sintetica().to_parquet(tmp_path / "personas_2024.parquet")
    monkeypatch.setattr(graficar, "BASE", tmp_path / "personas_2024.parquet")
    monkeypatch.setattr(sys, "argv", ["graficar.py", "--por", "departamento"])
    graficar.main()
    return dibujada(figuras_guardadas)


@pytest.fixture
def serie_2020_2024(tmp_path, figuras_guardadas):
    graficar = cargar("graficando-enaho", "graficar.py")
    filas = [{"anio": 2020 + i, "id": id_serie, "valor": valor}
             for id_serie, valores in SERIE.items() for i, valor in enumerate(valores)]
    pd.DataFrame(filas).to_csv(tmp_path / "indicadores.csv", index=False)
    graficar.graficar_serie_pobreza(tmp_path / "indicadores.csv", tmp_path / "serie.png")
    return dibujada(figuras_guardadas)


@pytest.fixture
def mapear():
    return cargar("mapeando-enaho", "mapear.py")


@pytest.fixture
def mapa_departamental(mapear, figuras_guardadas):
    import geopandas as gpd
    ref = referencia_inei()
    tasas = ref.loc[ref["ccdd"].str.len() == 2, ["ccdd", "valor"]].set_axis(["departamento", "pobreza_pct"], axis=1)
    tasas = pd.concat([tasas, pd.DataFrame([{"departamento": "15", "pobreza_pct": 24.65}])], ignore_index=True)
    mapear.dibujar_departamentos(mapear.unir_con_limites(tasas, gpd.read_file(LIMITES_DEP)))
    return dibujada(figuras_guardadas)


@pytest.fixture
def mapa_ambitos(mapear, figuras_guardadas):
    import geopandas as gpd
    tasas = referencia_inei()[["ccdd", "valor"]].set_axis(["codigo", "pobreza_pct"], axis=1)
    mapear.dibujar_ambitos(mapear.unir_ambitos_con_limites(tasas, gpd.read_file(LIMITES_AMBITOS)))
    return dibujada(figuras_guardadas)


def test_titulo_de_edad_se_lee_bien():
    graficar = cargar("graficando-enaho", "graficar.py")
    tasas = pd.Series({"0 a 14 años": 37.1, "15 a 29 años": 24.0, "30 a 44 años": 25.0, "45 a 59 años": 20.0,
                       "60 años y más": 18.0})
    titulo = graficar.titulo_edad(tasas)
    assert "de 0 a 14 años (37.1 %)" in titulo and "de 60 años y más (18.0 %)" in titulo
    assert "entre 0 a 14" not in titulo


def test_titulo_departamental_usa_e_ante_i():
    graficar = cargar("graficando-enaho", "graficar.py")
    titulo = graficar.titulo_departamento(pd.Series({"Cajamarca": 45.0, "Cusco": 18.5, "Ica": 6.0}))
    assert titulo.startswith("Cajamarca (45.0 %) e Ica (6.0 %)")


def test_serie_2020_2024_sin_etiquetas_superpuestas(serie_2020_2024):
    eje = serie_2020_2024.axes[0]
    renderer = serie_2020_2024.canvas.get_renderer()
    assert len(eje.texts) >= 5
    assert not choques(eje.texts, renderer)
    leyenda = eje.get_legend().get_window_extent(renderer)
    assert not [t.get_text() for t in eje.texts if caja_del_texto(t, renderer).overlaps(leyenda)]


def test_barras_de_ambitos_dicen_que_lima_va_desagregada(barras_de_ambitos):
    assert "por departamento, con Lima desagregada en Lima Metropolitana y Lima provincias" in textos_de(
        barras_de_ambitos)


def test_linea_nacional_no_cruza_las_cifras_de_las_barras(barras_de_ambitos):
    eje = barras_de_ambitos.axes[0]
    renderer = barras_de_ambitos.canvas.get_renderer()
    nacional = next(linea for linea in eje.get_lines() if len(set(linea.get_xdata())) == 1)
    x = eje.transData.transform((nacional.get_xdata()[0], 0))[0]
    cifras = [t for t in eje.texts if t.get_text().endswith("%") and "Nacional" not in t.get_text()]
    cruzadas = [t.get_text() for t in cifras if t.get_window_extent(renderer).x0 <= x <= t.get_window_extent(renderer).x1]
    assert len(cifras) == 26 and not cruzadas


def test_ambitos_referenciales_llevan_marca_y_nota(barras_de_ambitos, mapa_ambitos):
    # Ica, Madre de Dios y Moquegua tienen CV > 15 en la tabla del INEI: su cifra es referencial.
    etiquetas = {t.get_text() for t in barras_de_ambitos.axes[0].get_yticklabels()}
    assert {"Ica*", "Madre de Dios*", "Moquegua*"} <= etiquetas and sum(e.endswith("*") for e in etiquetas) == 3
    assert [t.get_text() for t in mapa_ambitos.axes[0].texts].count("*") == 3
    for figura in (barras_de_ambitos, mapa_ambitos):
        nota = textos_de(figura)
        assert "* Cifra referencial" in nota and all(n in nota for n in ("Ica", "Madre de Dios", "Moquegua"))


def test_lima_se_rotula_igual_en_graficos_y_mapas(barras_de_ambitos, serie_2020_2024, mapa_ambitos):
    barras = [t.get_text() for t in barras_de_ambitos.axes[0].get_yticklabels()]
    leyenda = [t.get_text() for t in serie_2020_2024.axes[0].get_legend().get_texts()]
    recuadro = [t.get_text() for t in mapa_ambitos.axes[0].child_axes[0].texts]
    for nombre in ("Lima Metropolitana", "Lima provincias"):
        assert nombre in barras and nombre in leyenda
        assert any(t.startswith(nombre + "\n") for t in recuadro)
    todos = "|".join(barras + leyenda + recuadro)
    assert not [viejo for viejo in NOMBRES_VIEJOS_DE_LIMA if viejo in todos]


def test_recuadro_sin_rotulos_de_ejes_en_ingles(mapa_departamental, mapa_ambitos):
    for figura in (mapa_departamental, mapa_ambitos):
        recuadro = figura.axes[0].child_axes[0]
        assert recuadro.get_xlabel() == "" and recuadro.get_ylabel() == ""


def test_rotulos_del_recuadro_no_se_superponen(mapa_departamental, mapa_ambitos):
    for figura in (mapa_departamental, mapa_ambitos):
        recuadro = figura.axes[0].child_axes[0]
        assert len(recuadro.texts) >= 2
        assert not choques(recuadro.texts, figura.canvas.get_renderer())


def test_callao_se_lee_sobre_su_relleno(mapa_departamental, mapa_ambitos):
    from matplotlib.colors import to_rgb
    for figura in (mapa_departamental, mapa_ambitos):
        callao = next(t for t in figura.axes[0].child_axes[0].texts if t.get_text().startswith("Callao"))
        rojo, verde, azul = to_rgb(callao.get_color())
        assert 0.2126 * rojo + 0.7152 * verde + 0.0722 * azul < 0.3, "Callao debe ir en tinta oscura"
        assert callao.get_path_effects(), "Callao necesita un halo claro para leerse sobre cualquier relleno"


def test_mapa_departamental_se_rotula_como_el_de_la_consigna(mapa_departamental):
    textos = textos_de(mapa_departamental)
    assert "consigna" in textos and "Lima como un solo departamento" in textos


@pytest.mark.parametrize("faltante", ["limites_departamentales_ign.geojson", "limites_ambitos_ign.geojson"])
def test_mapa_exige_los_limites_del_ign_sin_respaldo_al_geojson_del_curso(tmp_path, faltante):
    raiz = copiar_proyecto(tmp_path)
    (raiz / "datos").mkdir()
    shutil.copy(LIMITES_DEP, raiz / "datos" / "peru_departamental_simple.geojson")  # el respaldo que ya no se usa
    (raiz / "referencias" / faltante).unlink()
    (raiz / "salidas").mkdir()
    base_sintetica().to_parquet(raiz / "salidas" / "personas_2024.parquet")
    r = correr(raiz, "mapeando-enaho", "mapear.py")
    assert r.returncode != 0
    assert faltante in r.stderr and "scripts/preparar_limites.py" in r.stderr
    assert not (raiz / "mapas").exists()


@pytest.mark.parametrize("con_fila_15", [False, True])
def test_comparacion_declara_que_lima_no_tiene_cifra_del_inei(tmp_path, monkeypatch, mapear, con_fila_15):
    ref = pd.read_csv(REFERENCIA_INEI, dtype={"ccdd": str})
    ref = ref[ref["ccdd"] != "15"]
    if con_fila_15:  # la fila calculada que la tabla tenía antes: tampoco se compara con ella
        ref = pd.concat([ref, pd.DataFrame([{"ambito": "Lima (departamento completo)", "ccdd": "15", "valor": 27.1}])])
    ref.to_csv(tmp_path / "inei.csv", index=False)
    monkeypatch.setattr(mapear, "REFERENCIA", tmp_path / "inei.csv")
    monkeypatch.setattr(mapear, "COMPARACION", tmp_path / "mapa_vs_referencia.csv")
    deps = referencia_inei().loc[lambda t: t["ccdd"].str.len() == 2]
    mapa = pd.DataFrame({"departamento": deps["ccdd"], "NOMBDEP": deps["ambito"].str.upper(), "pobreza_pct": deps["valor"]})
    mapa = pd.concat([mapa, pd.DataFrame([{"departamento": "15", "NOMBDEP": "LIMA", "pobreza_pct": 24.65}])])
    mapear.comprobar_referencia(mapa)
    tabla = pd.read_csv(tmp_path / "mapa_vs_referencia.csv", dtype={"ccdd": str}).set_index("ccdd")
    assert len(tabla) == 25
    assert tabla.loc["15", "observacion"] == "sin cifra publicada por el INEI"
    assert pd.isna(tabla.loc["15", "referencia_inei"]) and pd.isna(tabla.loc["15", "diferencia"])
    assert tabla.drop("15")["dentro_de_tolerancia"].astype(bool).all()


def mapa_de_ambitos(desvio: dict[str, float] | None = None) -> pd.DataFrame:
    """Los 26 ámbitos como los deja unir_ambitos_con_limites, cada uno a 0.04 puntos de la cifra del INEI salvo los
    desvíos dados; los nombres en mayúsculas, como en la capa del IGN."""
    ref = referencia_inei()
    tasas = ref["valor"] + 0.04 + ref["ccdd"].map(desvio or {}).fillna(0)
    return pd.DataFrame({"codigo": ref["ccdd"], "nombre": ref["ambito"].str.upper(), "pobreza_pct": tasas})


def test_contraste_por_ambitos_separa_lima_y_trae_el_intervalo_del_inei(tmp_path, monkeypatch, mapear):
    monkeypatch.setattr(mapear, "CONTRASTE_AMBITOS", tmp_path / "ambitos_vs_referencia.csv")

    mapear.comprobar_ambitos(mapa_de_ambitos())
    tabla = pd.read_csv(tmp_path / "ambitos_vs_referencia.csv", dtype={"codigo": str})

    assert tabla["codigo"].tolist() == sorted(referencia_inei()["ccdd"])  # 26, en orden de código
    assert len(tabla) == 26 and "15" not in tabla["codigo"].tolist()
    tabla = tabla.set_index("codigo")
    assert tabla.loc["1501", ["ambito", "referencia_inei", "ic_inf", "ic_sup", "cv"]].tolist() == [
        "Lima Metropolitana", 27.6, 25.0, 30.1, 4.7]
    assert tabla.loc["15_resto", ["ambito", "referencia_inei", "ic_inf", "ic_sup"]].tolist() == [
        "Lima provincias", 21.7, 18.3, 25.1]
    assert tabla.loc["1501", "pobreza_pct"] == pytest.approx(27.64)
    assert tabla.loc["02", "ambito"] == "Áncash"  # el nombre del INEI, con tilde, no el de la capa
    assert tabla["diferencia"].eq(0.04).all() and tabla["dentro_de_tolerancia"].all()
    assert sorted(tabla.index[tabla["referencial"]]) == ["11", "17", "18"]  # CV mayor que 15 %


def test_contraste_por_ambitos_se_detiene_si_un_ambito_se_aleja_del_inei(tmp_path, monkeypatch, mapear):
    monkeypatch.setattr(mapear, "CONTRASTE_AMBITOS", tmp_path / "ambitos_vs_referencia.csv")

    with pytest.raises(SystemExit, match="1501"):
        mapear.comprobar_ambitos(mapa_de_ambitos({"1501": 0.5}))
    tabla = pd.read_csv(tmp_path / "ambitos_vs_referencia.csv", dtype={"codigo": str}).set_index("codigo")
    assert not tabla.loc["1501", "dentro_de_tolerancia"]  # la tabla queda escrita para revisarla
    assert tabla.drop("1501")["dentro_de_tolerancia"].all()


def test_contraste_por_ambitos_se_detiene_si_un_ambito_no_tiene_cifra_del_inei(tmp_path, monkeypatch, mapear):
    ref = pd.read_csv(REFERENCIA_INEI, dtype={"ccdd": str})
    ref[ref["ccdd"] != "15_resto"].to_csv(tmp_path / "inei.csv", index=False)
    monkeypatch.setattr(mapear, "REFERENCIA", tmp_path / "inei.csv")
    monkeypatch.setattr(mapear, "CONTRASTE_AMBITOS", tmp_path / "ambitos_vs_referencia.csv")

    with pytest.raises(SystemExit, match="15_resto"):
        mapear.comprobar_ambitos(mapa_de_ambitos())
    assert not (tmp_path / "ambitos_vs_referencia.csv").exists()
