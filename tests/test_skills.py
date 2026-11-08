"""Las skills de la ENAHO probadas como las usa Claude: corriendo sus scripts.

    uv run pytest tests/test_skills.py

Cada script ubica la raíz del proyecto a partir de su propia ruta, así que basta copiarlo a una carpeta temporal
para probarlo aislado, sin tocar salidas/ del repo. Las pruebas que necesitan los microdatos se saltan si faltan
los zip en datos/ (se bajan con la skill descargando-enaho).
"""
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
    if datos:
        (destino / "datos").mkdir()
        for archivo in ZIPS + [RAIZ / "datos" / "peru_departamental_simple.geojson"]:
            shutil.copy(archivo, destino / "datos")
    return destino


def correr(raiz: Path, skill: str, script: str, *args: str) -> subprocess.CompletedProcess:
    ruta = raiz / ".claude" / "skills" / skill / "scripts" / script
    return subprocess.run([sys.executable, str(ruta), *args], capture_output=True, text=True, encoding="utf-8",
                          cwd=raiz)


def test_limpiar_rechaza_otro_anio(tmp_path):
    r = correr(copiar_proyecto(tmp_path), "limpiando-enaho", "limpiar.py", "--anio", "2023")
    assert r.returncode != 0
    assert "solo valida la ENAHO 2024" in r.stderr


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
    tabla = pd.read_csv(RAIZ / "salidas" / "indicadores.csv").set_index("id")
    assert abs(tabla.loc["pobreza_nacional", "valor"] - 27.6) <= 0.1
    assert tabla.loc["residentes_habituales", "valor"] == 108_664
    assert tabla.loc["departamentos", "valor"] == 25
    assert tabla.index.str.startswith("pobreza_dep_").sum() == 25
    assert abs(tabla.loc["pobreza_area_urbana", "valor"] - 24.8) <= 0.1
    assert abs(tabla.loc["pobreza_area_rural", "valor"] - 39.3) <= 0.1
    validacion = (RAIZ / "salidas" / "validacion.txt").read_text(encoding="utf-8")
    assert "FALLA" not in validacion


@con_microdatos
def test_limpiar_reproduce_los_indicadores_versionados(tmp_path):
    raiz = copiar_proyecto(tmp_path, skills=("limpiando-enaho",), datos=True)
    r = correr(raiz, "limpiando-enaho", "limpiar.py", "--anio", "2024")
    assert r.returncode == 0, r.stderr
    nuevos = pd.read_csv(raiz / "salidas" / "indicadores.csv")
    versionados = pd.read_csv(RAIZ / "salidas" / "indicadores.csv")
    pd.testing.assert_frame_equal(nuevos, versionados)


@con_microdatos
def test_limpiar_se_detiene_si_falla_una_validacion(tmp_path):
    # Una referencia alterada para Cusco debe detener el proceso sin escribir la base: nada de forzar cifras
    raiz = copiar_proyecto(tmp_path, skills=("limpiando-enaho",), datos=True)
    referencia = raiz / "referencias" / "pobreza_departamento_2024.csv"
    tabla = pd.read_csv(referencia, dtype={"ccdd": str})
    tabla.loc[tabla["ccdd"] == "08", "pobreza_pct"] = 50.0
    tabla.to_csv(referencia, index=False)
    r = correr(raiz, "limpiando-enaho", "limpiar.py", "--anio", "2024")
    assert r.returncode != 0
    assert "comprobaciones fallaron" in r.stderr
    assert "FALLA Pobreza en CUSCO" in (raiz / "salidas" / "validacion.txt").read_text(encoding="utf-8")
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
    comparacion = pd.read_csv(raiz / "salidas" / "mapa_vs_referencia.csv", dtype={"ccdd": str})
    assert len(comparacion) == 25 and comparacion["dentro_de_tolerancia"].all()
    assert {"07", "15"} <= set(comparacion["ccdd"])  # Lima y Callao por separado
