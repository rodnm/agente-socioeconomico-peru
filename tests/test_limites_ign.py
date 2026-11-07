"""Pruebas de la capa oficial de límites departamentales y provinciales del IGN (H1 y H8)."""

import importlib.util
import json
import zipfile
from pathlib import Path

import pytest
import geopandas as gpd
from shapely.ops import unary_union

RAIZ = Path(__file__).resolve().parents[1]
LIMITES_DEP = RAIZ / "referencias" / "limites_departamentales_ign.geojson"
LIMITES_AMBITOS = RAIZ / "referencias" / "limites_ambitos_ign.geojson"


def test_limites_departamentales_25_unidades():
    """H1: La capa departamental contiene exactamente 25 unidades (01-25) y Callao (07)."""
    assert LIMITES_DEP.is_file(), f"Falta el archivo {LIMITES_DEP}"
    gdf = gpd.read_file(LIMITES_DEP)
    assert len(gdf) == 25, f"Se esperaban 25 departamentos, se encontraron {len(gdf)}"

    codigos = set(gdf["ccdd"].astype(str).str.zfill(2))
    esperados = {f"{i:02d}" for i in range(1, 26)}
    assert codigos == esperados, f"Diferencia de códigos: {codigos ^ esperados}"

    # Compatibilidad con consigna del curso: FIRST_IDDP como alias de ccdd
    assert "FIRST_IDDP" in gdf.columns, "Falta la columna FIRST_IDDP para compatibilidad"
    assert (gdf["FIRST_IDDP"].astype(str).str.zfill(2) == gdf["ccdd"].astype(str).str.zfill(2)).all()

    # Callao presente
    callao = gdf[gdf["ccdd"] == "07"]
    assert len(callao) == 1
    assert not callao.geometry.iloc[0].is_empty
    assert callao.geometry.iloc[0].is_valid


def test_limites_ambitos_26_unidades_separacion_lima():
    """H8: La capa de ámbitos separa Lima Metropolitana (1501) de Lima provincias y reconstruye el depto 15."""
    assert LIMITES_AMBITOS.is_file(), f"Falta el archivo {LIMITES_AMBITOS}"
    gdf_amb = gpd.read_file(LIMITES_AMBITOS)
    assert len(gdf_amb) == 26, f"Se esperaban 26 ámbitos, se encontraron {len(gdf_amb)}"

    codigos = set(gdf_amb["codigo"].astype(str))
    assert "1501" in codigos, "Falta Lima Metropolitana (1501)"
    assert ("15_resto" in codigos or "15P" in codigos), "Falta Lima provincias"

    # Geometría: la unión de Lima Metropolitana y Lima provincias reconstruye el departamento 15
    geom_metro = gdf_amb[gdf_amb["codigo"] == "1501"].geometry.iloc[0]
    geom_resto = gdf_amb[gdf_amb["codigo"].isin(["15_resto", "15P"])].geometry.iloc[0]
    union_lima = unary_union([geom_metro, geom_resto])

    gdf_dep = gpd.read_file(LIMITES_DEP)
    geom_dep15 = gdf_dep[gdf_dep["ccdd"] == "15"].geometry.iloc[0]

    diff_area = geom_dep15.symmetric_difference(union_lima).area
    assert diff_area / geom_dep15.area < 1e-4, f"La unión difiere del departamento 15: {diff_area}"


def test_descargar_no_usa_geojson_externo():
    """descargar.py deja de descargar el GeoJSON externo del curso."""
    ruta_descargar = RAIZ / ".claude" / "skills" / "descargando-enaho" / "scripts" / "descargar.py"
    contenido = ruta_descargar.read_text(encoding="utf-8")
    assert "peru_departamental_simple.geojson" not in contenido


def test_mapas_generados_existen_y_validos():
    """Verifica que ambos mapas (25 departamentos y 26 ámbitos) existan y sean imágenes PNG válidas."""
    mapa_dep = RAIZ / "mapas" / "pobreza_departamento.png"
    mapa_ambitos = RAIZ / "mapas" / "pobreza_ambitos.png"
    assert mapa_dep.is_file() and mapa_dep.stat().st_size > 10000
    assert mapa_ambitos.is_file() and mapa_ambitos.stat().st_size > 10000


# --- preparar_limites.py con un zip falso: comprobaciones de procedencia y de códigos ---

CRS84 = "urn:ogc:def:crs:OGC:1.3:CRS84"


def cargar_preparar():
    ruta = RAIZ / "scripts" / "preparar_limites.py"
    especificacion = importlib.util.spec_from_file_location("preparar_limites", ruta)
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    return modulo


def cuadrado(x: float, y: float) -> dict:
    return {"type": "Polygon", "coordinates": [[[x, y], [x + 1, y], [x + 1, y + 1], [x, y + 1], [x, y]]]}


def zip_falso(ruta: Path, codigos=None, crs: str = CRS84) -> Path:
    """Un zip con la forma del de OCHA HDX: 25 departamentos y dos provincias de Lima, como cuadrados."""
    codigos = codigos or [f"{i:02d}" for i in range(1, 26)]
    sistema = {"type": "name", "properties": {"name": crs}}
    adm1 = {"type": "FeatureCollection", "crs": sistema, "features": [
        {"type": "Feature", "properties": {"adm1_pcode": f"PE{c}", "adm1_name": f"Departamento {c}"},
         "geometry": cuadrado(2.0 * i, 0)} for i, c in enumerate(codigos)]}
    adm2 = {"type": "FeatureCollection", "crs": sistema, "features": [
        {"type": "Feature", "properties": {"adm2_pcode": "PE1501"}, "geometry": cuadrado(0, 10)},
        {"type": "Feature", "properties": {"adm2_pcode": "PE1502"}, "geometry": cuadrado(1, 10)}]}
    with zipfile.ZipFile(ruta, "w") as z:
        z.writestr("per_admin1.geojson", json.dumps(adm1))
        z.writestr("per_admin2.geojson", json.dumps(adm2))
    return ruta


@pytest.fixture
def preparar(tmp_path, monkeypatch):
    """El script con sus salidas redirigidas a una carpeta temporal."""
    modulo = cargar_preparar()
    monkeypatch.setattr(modulo, "RAIZ", tmp_path)
    monkeypatch.setattr(modulo, "REFERENCIAS", tmp_path / "referencias")
    monkeypatch.setattr(modulo, "DESTINO_DEP", tmp_path / "referencias" / "departamentos.geojson")
    monkeypatch.setattr(modulo, "DESTINO_AMBITOS", tmp_path / "referencias" / "ambitos.geojson")
    return modulo


def aceptar_hash(preparar, monkeypatch, archivo: Path) -> Path:
    monkeypatch.setattr(preparar, "SHA256_ESPERADO", preparar.sha256_archivo(archivo), raising=False)
    return archivo


def test_sha256_fijado_coincide_con_referencias_readme():
    fijado = cargar_preparar().SHA256_ESPERADO
    assert len(fijado) == 64 and fijado in (RAIZ / "referencias" / "README.md").read_text(encoding="utf-8")


def test_preparar_limites_rechaza_un_zip_con_otro_sha256(preparar, tmp_path):
    with pytest.raises(SystemExit, match="SHA-256"):
        preparar.procesar_capas(zip_falso(tmp_path / "otro.zip"))
    assert not (tmp_path / "referencias").exists()


def test_preparar_limites_rechaza_otro_sistema_de_referencia(preparar, tmp_path, monkeypatch):
    archivo = aceptar_hash(preparar, monkeypatch, zip_falso(tmp_path / "utm.zip", crs="urn:ogc:def:crs:EPSG::32718"))
    with pytest.raises(SystemExit, match="CRS84"):
        preparar.procesar_capas(archivo)
    assert not (tmp_path / "referencias").exists()


def test_preparar_limites_exige_los_codigos_01_a_25_uno_a_uno(preparar, tmp_path, monkeypatch):
    repetido = [f"{i:02d}" for i in range(1, 25)] + ["24"]  # 24 dos veces y falta 25
    archivo = aceptar_hash(preparar, monkeypatch, zip_falso(tmp_path / "repetido.zip", codigos=repetido))
    with pytest.raises(SystemExit, match="01 a 25"):
        preparar.procesar_capas(archivo)
    assert not (tmp_path / "referencias").exists()


def test_preparar_limites_first_iddp_de_las_dos_partes_de_lima_es_15(preparar, tmp_path, monkeypatch):
    preparar.procesar_capas(aceptar_hash(preparar, monkeypatch, zip_falso(tmp_path / "bueno.zip")))
    ambitos = gpd.read_file(tmp_path / "referencias" / "ambitos.geojson")
    lima = ambitos[ambitos["codigo"].isin(["1501", "15_resto"])].set_index("codigo")
    assert sorted(lima.index) == ["1501", "15_resto"]
    assert (lima["FIRST_IDDP"] == "15").all()
    assert list(lima.loc[["1501", "15_resto"], "nombre"]) == ["Lima Metropolitana", "Lima provincias"]
    resto = ambitos[~ambitos["codigo"].isin(["1501", "15_resto"])]
    assert len(resto) == 24 and (resto["FIRST_IDDP"] == resto["codigo"]).all()
