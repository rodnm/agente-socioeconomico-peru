"""Pruebas de la capa oficial de límites departamentales y provinciales del IGN (H1 y H8)."""

from pathlib import Path
import json
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
