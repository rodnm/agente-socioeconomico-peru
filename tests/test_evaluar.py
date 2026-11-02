"""La lógica del experimento: cómo se califica, qué herramientas se cuentan y qué ve cada modo.

    uv run pytest tests/test_evaluar.py
"""
import importlib.util
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("evaluar", RAIZ / "evaluacion" / "evaluar.py")
evaluar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluar)


@pytest.mark.parametrize("fila,esperado", [
    ({"valor": 27.55, "verdad": 27.6, "tolerancia": 0.1}, "acierta"),
    ({"valor": 27.8, "verdad": 27.6, "tolerancia": 0.1}, "se equivoca"),
    ({"valor": None, "verdad": 27.6, "tolerancia": 0.1}, "no sabe"),
    ({"valor": None, "verdad": 27.6, "tolerancia": 0.1, "error": "tiempo agotado"}, "error"),
    ({"valor": 1.97, "valor_2": 24.8, "verdad": 1.97, "verdad_2": 24.8, "tolerancia": 0.01, "tolerancia_2": 0.1},
     "acierta"),
    ({"valor": 1.97, "valor_2": 30.0, "verdad": 1.97, "verdad_2": 24.8, "tolerancia": 0.01, "tolerancia_2": 0.1},
     "se equivoca"),
    ({"valor": 1.97, "valor_2": None, "verdad": 1.97, "verdad_2": 24.8, "tolerancia": 0.01, "tolerancia_2": 0.1},
     "no sabe"),
])
def test_calificar(fila, esperado):
    assert evaluar.calificar({"verdad_2": None, **fila}) == esperado


def test_herramientas_usadas_en_orden_sin_repetir_ni_contar_la_respuesta():
    eventos = [{"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Skill", "input": {"skill": "limpiando-enaho"}},
        {"type": "tool_use", "name": "mcp__bcrp__resumen", "input": {}}]}},
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "mcp__bcrp__resumen", "input": {}},
            {"type": "tool_use", "name": "StructuredOutput", "input": {}}]}}]
    assert evaluar.herramientas_usadas(eventos) == ["Skill:limpiando-enaho", "mcp__bcrp__resumen"]


@pytest.mark.parametrize("copia", ["crudos", "proyecto", "proyecto-sin-skills"])
def test_ningun_modo_ve_las_respuestas_esperadas(tmp_path, copia):
    evaluar.preparar(copia, tmp_path)
    assert not (tmp_path / "evaluacion").exists() and not (tmp_path / ".git").exists()
    assert (tmp_path / ".claude" / "skills").exists() == (copia == "proyecto")
    if copia == "crudos":
        assert not (tmp_path / "salidas").exists() and not (tmp_path / "CLAUDE.md").exists()


def test_lenguaje_causal():
    assert evaluar.lenguaje_causal("La inflación provocó más pobreza")
    assert not evaluar.lenguaje_causal("Ambas cifras describen asociaciones de distinto nivel de agregación")


AVISO_CONFIANZA = ("Ignoring 3 permissions.allow entries from .claude/settings.json: this workspace has not been "
                   "trusted. Run Claude Code interactively here once and accept the trust dialog.\n")


@pytest.mark.parametrize("codigo,stderr,esperado", [
    (1, AVISO_CONFIANZA, "claude -p salió con código 1"),
    (1, AVISO_CONFIANZA + "Error: usage limit reached\n", "Error: usage limit reached"),
    (0, AVISO_CONFIANZA, ""),
])
def test_el_error_no_es_el_aviso_de_confianza(codigo, stderr, esperado):
    # El aviso sale en todas las copias temporales; si se guardara como error, ocultaría la causa real.
    assert evaluar.motivo_de_error(codigo, stderr) == esperado
