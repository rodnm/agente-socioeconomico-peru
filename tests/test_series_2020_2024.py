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
