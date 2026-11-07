"""Pruebas de la serie 2020-2024 de ENAHO y SBS (H2, H3, H4)."""

from pathlib import Path
import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]
INDICADORES = RAIZ / "salidas" / "indicadores.csv"
FIGURA_SERIE = RAIZ / "figuras" / "pobreza_serie_2020_2024.png"


def test_indicadores_tiene_columna_anio():
    """indicadores.csv incorpora la columna anio con cobertura 2020-2024."""
    assert INDICADORES.is_file(), f"Falta {INDICADORES}"
    df = pd.read_csv(INDICADORES)
    assert "anio" in df.columns, "Falta la columna anio en indicadores.csv"
    anios_presentes = set(df["anio"].dropna().astype(int))
    assert {2020, 2021, 2022, 2023, 2024} <= anios_presentes, f"Años incompletos: {anios_presentes}"


def test_grafico_serie_2020_2024_generado():
    """El gráfico de la serie de pobreza 2020-2024 existe y es un PNG válido."""
    assert FIGURA_SERIE.is_file(), f"Falta la figura {FIGURA_SERIE}"
    assert FIGURA_SERIE.stat().st_size > 10000, "El archivo PNG está vacío o es muy pequeño"


def test_verificar_incluye_morosidad_sbs_bcrp():
    """verificar.py incorpora la comparación de morosidad BCRP-SBS como DIFERENCIA."""
    ruta_verificar = RAIZ / ".claude" / "skills" / "verificando-consistencia" / "scripts" / "verificar.py"
    contenido = ruta_verificar.read_text(encoding="utf-8")
    assert "PN07746EM" in contenido, "Falta la serie PN07746EM en verificar.py"
    assert "sbs" in contenido.lower(), "Falta la consulta a la SBS en verificar.py"


ZIPS_2024 = [RAIZ / "datos" / "966-Modulo34.zip", RAIZ / "datos" / "966-Modulo02.zip"]


@pytest.mark.skipif(not all(z.is_file() for z in ZIPS_2024), reason="faltan los zip de la ENAHO 2024 en datos/")
def test_limpiar_un_anio_conserva_los_demas_y_el_orden_de_generacion(tmp_path):
    """Correr un año reemplaza solo sus filas; el orden no depende de si ya existía indicadores.csv."""
    import shutil
    import subprocess
    import sys

    def preparar(destino):
        skill = RAIZ / ".claude" / "skills" / "limpiando-enaho"
        shutil.copytree(skill, destino / ".claude" / "skills" / "limpiando-enaho")
        shutil.copytree(RAIZ / "referencias", destino / "referencias")
        (destino / "datos").mkdir()
        for archivo in ZIPS_2024:
            shutil.copy(archivo, destino / "datos")
        return destino / ".claude" / "skills" / "limpiando-enaho" / "scripts" / "limpiar.py"

    def correr(script, raiz):
        r = subprocess.run([sys.executable, str(script), "--anio", "2024"], capture_output=True, text=True,
                           encoding="utf-8", cwd=raiz)
        assert r.returncode == 0, r.stderr
        return pd.read_csv(raiz / "salidas" / "indicadores.csv")

    limpio = correr(preparar(tmp_path / "limpio"), tmp_path / "limpio")
    con_previo = tmp_path / "con_previo"
    script = preparar(con_previo)
    (con_previo / "salidas").mkdir()
    previo = pd.read_csv(INDICADORES)
    previo.to_csv(con_previo / "salidas" / "indicadores.csv", index=False)
    resultado = correr(script, con_previo)

    otros = previo[previo["anio"] != 2024].reset_index(drop=True)
    pd.testing.assert_frame_equal(resultado[resultado["anio"] != 2024].reset_index(drop=True), otros)
    pd.testing.assert_frame_equal(resultado[resultado["anio"] == 2024].reset_index(drop=True), limpio)


def test_descargar_sin_anio_usa_2024_y_no_vuelve_a_bajar_un_zip_valido(tmp_path):
    """La skill pasa «--anio» vacío cuando no hay año: debe tomar 2024 y respetar los zip válidos, sin red."""
    import shutil
    import subprocess
    import sys
    import zipfile

    skill = RAIZ / ".claude" / "skills" / "descargando-enaho"
    shutil.copytree(skill, tmp_path / ".claude" / "skills" / "descargando-enaho")
    (tmp_path / "datos").mkdir()
    for modulo in ("34", "02"):
        with zipfile.ZipFile(tmp_path / "datos" / f"966-Modulo{modulo}.zip", "w") as z:
            z.writestr("leame.txt", "zip de prueba")
    script = tmp_path / ".claude" / "skills" / "descargando-enaho" / "scripts" / "descargar.py"
    r = subprocess.run([sys.executable, str(script), "--anio"], capture_output=True, text=True, encoding="utf-8",
                       cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    assert r.stdout.count("Ya estaba y es válido") == 2
    assert "966-Modulo34.zip" in r.stdout and "966-Modulo02.zip" in r.stdout
