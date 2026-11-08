"""analizar.py resume resultados.csv y robustez_resultados.csv en tablas reproducibles.

    uv run pytest tests/test_analizar.py
"""
import importlib.util
from pathlib import Path

import pandas as pd
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "evaluacion" / "analizar.py"


@pytest.fixture
def analizar():
    spec = importlib.util.spec_from_file_location("analizar", SCRIPT)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def fila(id_, tipo, modo, resultado, segundos=10.0, costo=0.1, herramientas="", causal=False):
    return {"id": id_, "tipo": tipo, "modo": modo, "resultado": resultado, "segundos": segundos, "turnos": 3,
            "costo_usd": costo, "herramientas": herramientas, "valor": 1.0, "lenguaje_causal": causal}


@pytest.fixture
def resultados():
    return pd.DataFrame([
        fila("b1", "bcrp", "A", "acierta", 20, 0.2, "WebSearch"),
        fila("b1", "bcrp", "B", "acierta", 30, 0.3, "mcp__bcrp__buscar_series;mcp__bcrp__serie"),
        fila("e1", "enaho", "A", "se equivoca", 100, 0.9, "Bash"),
        fila("e1", "enaho", "B", "acierta", 40, 0.4, "Skill:limpiando-enaho;Bash"),
        fila("m1", "mixta", "A", "no sabe", 60, 0.5, "WebSearch;Bash", causal=True),
        fila("m1", "mixta", "B", "error", 900, None, ""),
    ])


def test_resumen_por_modo(analizar, resultados):
    t = analizar.resumen_por_modo(resultados)
    assert t.loc["A", "acierta"] == 1 and t.loc["A", "se equivoca"] == 1 and t.loc["A", "no sabe"] == 1
    assert t.loc["B", "acierta"] == 2 and t.loc["B", "error"] == 1
    assert t.loc["A", "segundos promedio"] == 60.0 and t.loc["B", "costo total USD"] == 0.7


def test_cambios_entre_modos(analizar, resultados):
    mejoran, empeoran = analizar.cambios(resultados, "A", "B")
    assert mejoran == ["e1"] and empeoran == []
    mejoran, empeoran = analizar.cambios(resultados, "B", "A")
    assert mejoran == [] and empeoran == ["e1"]


def test_uso_de_herramientas(analizar, resultados):
    t = analizar.uso_de_herramientas(resultados)
    assert t.loc["B", "MCP"] == 1 and t.loc["B", "Skill"] == 1 and t.loc["A", "Web"] == 2 and t.loc["A", "Bash"] == 2


def test_robustez_por_modo(analizar):
    r = pd.DataFrame([{"id": "r1", "modo": "A", "resultado": "cumple"}, {"id": "r2", "modo": "A", "resultado": "no cumple"},
                      {"id": "r1", "modo": "B", "resultado": "cumple"}, {"id": "r2", "modo": "B", "resultado": "cumple"}])
    t = analizar.robustez_por_modo(r)
    assert t.loc["A", "cumple"] == 1 and t.loc["B", "cumple"] == 2


def test_escribe_metricas_con_todas_las_secciones(analizar, resultados, tmp_path):
    resultados.to_csv(tmp_path / "resultados.csv", index=False)
    destino = analizar.escribir(tmp_path / "resultados.csv", tmp_path / "no_existe.csv", tmp_path / "metricas.md")
    texto = destino.read_text(encoding="utf-8")
    for seccion in ("## Aciertos por modo", "## Aciertos por tipo de pregunta", "## Resultado de cada pregunta",
                    "## Cambios frente al Modo A", "## Uso de herramientas", "## Interpretación de las mixtas"):
        assert seccion in texto
    assert "Robustez" not in texto  # sin corridas de robustez, no inventa la sección
    assert "| A | 1 | 1 | 1 | 0 | 60 | 3 | 1.6 |" in texto  # conteos enteros, sin «1.0»
    assert "| m1 · A | no sabe | True |" in texto
