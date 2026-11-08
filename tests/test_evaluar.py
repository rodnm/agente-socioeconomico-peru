"""La lógica del experimento: cómo se califica, qué herramientas se cuentan, qué ve cada modo y cómo se aísla.

    uv run pytest tests/test_evaluar.py
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
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


@pytest.mark.parametrize("copia", ["crudos", "proyecto", "crudos-con-mcp", "proyecto-sin-mcp"])
def test_ningun_modo_ve_las_respuestas_esperadas(tmp_path, copia):
    evaluar.preparar(copia, tmp_path)
    assert not (tmp_path / "evaluacion").exists() and not (tmp_path / ".git").exists()
    assert (tmp_path / ".claude" / "skills").exists() == (copia in ("proyecto", "proyecto-sin-mcp"))
    if copia.startswith("crudos"):
        assert not (tmp_path / "salidas").exists() and not (tmp_path / "CLAUDE.md").exists()


def test_solo_mcp_es_el_modo_a_mas_el_servidor(tmp_path):
    # Sin las salidas de las skills, ni las figuras, ni la referencia de la sesión 16 (que trae la respuesta de e3).
    evaluar.preparar("crudos-con-mcp", tmp_path)
    assert sorted(p.name for p in tmp_path.iterdir()) == [".mcp.json", "datos", "mcp", "pyproject.toml", "scripts",
                                                          "uv.lock"]
    assert (tmp_path / "mcp" / "server.py").is_file()
    # De scripts/ solo va el estilo de los gráficos, que el servidor importa; nada de exportar evidencias ni límites.
    assert [p.name for p in (tmp_path / "scripts").iterdir()] == ["estilo_graficos.py"]


def test_el_servidor_del_bcrp_arranca_en_la_copia_solo_mcp(tmp_path):
    # En la evaluación v2, la copia no traía scripts/estilo_graficos.py y el servidor no arrancaba: solo-mcp se quedó
    # sin BCRP sin que nada fallara.
    evaluar.preparar("crudos-con-mcp", tmp_path)
    r = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, 'mcp'); import server"],
                       cwd=tmp_path, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-600:]


def test_sin_mcp_tampoco_tiene_el_codigo_del_servidor(tmp_path):
    # Las herramientas son funciones de Python: con mcp/server.py a mano, Bash puede llamarlas sin el protocolo MCP.
    evaluar.preparar("proyecto-sin-mcp", tmp_path)
    assert not (tmp_path / "mcp").exists() and not (tmp_path / ".mcp.json").exists()
    assert (tmp_path / "salidas" / "indicadores.csv").is_file()


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


# Aislamiento de la configuración del usuario (evaluación v2, hipótesis H7). Ninguna prueba llama a claude -p: un
# subprocess.run simulado registra el comando, el entorno y la carpeta que habría recibido.
RESULTADO_SIMULADO = json.dumps({"type": "result", "structured_output": {"valor": 1.0, "fuente": "prueba"},
                                 "num_turns": 1, "total_cost_usd": 0.0}) + "\n"
MODOS_CON_CLAUDE_MD = {"B", "solo-skills", "sin-propia"}


def llamada_simulada(monkeypatch, modo, robustez=False):
    vista = {}

    def run_simulado(cmd, **kw):
        carpeta = Path(kw["cwd"])
        vista.update(cmd=cmd, env=kw["env"], archivos=sorted(p.name for p in carpeta.iterdir()))
        return subprocess.CompletedProcess(cmd, 0, stdout=RESULTADO_SIMULADO, stderr="")

    monkeypatch.setattr(evaluar.subprocess, "run", run_simulado)
    monkeypatch.delenv("CLAUDE_CODE_DISABLE_CLAUDE_MDS", raising=False)
    vista["respuesta"] = evaluar.preguntar("¿Pregunta de prueba?", modo, "sonnet", robustez)
    return vista


def valor_de(cmd, opcion):
    return cmd[cmd.index(opcion) + 1]


@pytest.mark.parametrize("modo", list(evaluar.MODOS))
def test_ningun_modo_lee_los_claude_md_del_usuario(monkeypatch, modo):
    vista = llamada_simulada(monkeypatch, modo)
    assert vista["env"]["CLAUDE_CODE_DISABLE_CLAUDE_MDS"] == "1"
    assert "CLAUDE_CODE_DISABLE_CLAUDE_MDS" not in os.environ  # solo el proceso hijo cambia de entorno


@pytest.mark.parametrize("modo", list(evaluar.MODOS))
def test_ningun_modo_lee_la_configuracion_del_usuario(monkeypatch, modo):
    cmd = llamada_simulada(monkeypatch, modo)["cmd"]
    assert valor_de(cmd, "--setting-sources") == "project,local"
    assert "--strict-mcp-config" in cmd


@pytest.mark.parametrize("modo", list(evaluar.MODOS))
def test_las_reglas_del_proyecto_llegan_solo_a_los_modos_que_las_copian(monkeypatch, modo):
    # La variable apaga también el CLAUDE.md del proyecto: los modos que lo copian lo reciben como prompt de sistema.
    vista = llamada_simulada(monkeypatch, modo)
    assert ("CLAUDE.md" in vista["archivos"]) == (modo in MODOS_CON_CLAUDE_MD)
    if modo in MODOS_CON_CLAUDE_MD:
        assert vista["cmd"].count("--append-system-prompt") == 1
        assert valor_de(vista["cmd"], "--append-system-prompt") == (RAIZ / "CLAUDE.md").read_text(encoding="utf-8")
    else:
        assert "--append-system-prompt" not in vista["cmd"]


@pytest.mark.parametrize("robustez", [False, True])
@pytest.mark.parametrize("modo", list(evaluar.MODOS))
def test_el_comando_anterior_sigue_igual(monkeypatch, modo, robustez):
    # El aislamiento solo agrega argumentos al final: modelo, esquema, herramientas y MCP siguen como en la v1.
    vista = llamada_simulada(monkeypatch, modo, robustez)
    esquema, instruccion = ((evaluar.ESQUEMA_ROBUSTEZ, evaluar.INSTRUCCION_ROBUSTEZ) if robustez
                            else (evaluar.ESQUEMA, evaluar.INSTRUCCION))
    anterior = ["claude", "-p", instruccion + "¿Pregunta de prueba?", "--output-format", "stream-json", "--verbose",
                "--json-schema", json.dumps(esquema), "--no-session-persistence", "--model", "sonnet",
                "--strict-mcp-config", *evaluar.MODOS[modo][1]]
    assert vista["cmd"][:len(anterior)] == anterior
    assert vista["env"]["UV_PROJECT_ENVIRONMENT"] == str(RAIZ / ".venv")
    assert vista["respuesta"]["valor"] == 1.0 and vista["respuesta"]["error"] == ""


def test_el_modo_a_sigue_sin_claude_md_ni_mcp_ni_referencias(monkeypatch):
    assert llamada_simulada(monkeypatch, "A")["archivos"] == ["datos"]


COLUMNAS_PREGUNTAS = ["id", "tipo", "pregunta", "verdad", "verdad_2", "unidad", "tolerancia", "tolerancia_2", "modo",
                      "valor", "fuente", "segundos", "turnos", "costo_usd", "herramientas", "error", "resultado",
                      "lenguaje_causal"]
COLUMNAS_ROBUSTEZ = ["id", "modo", "pedido", "conducta_esperada", "conducta_observada", "supuesto", "respuesta",
                     "herramientas", "segundos", "resultado", "error"]


@pytest.mark.parametrize("robustez", [False, True])
def test_cada_fila_registra_el_aislamiento(tmp_path, monkeypatch, robustez):
    # Distingue las filas de la v2 de las de la v1, que corrieron con la configuración del usuario.
    (tmp_path / "evaluacion").mkdir()
    if robustez:
        pd.DataFrame([{"id": "r1", "pedido": "¿Pedido?", "conducta_esperada": "responde"}]).to_csv(
            tmp_path / "evaluacion" / "robustez.csv", index=False)
    else:
        pd.DataFrame([{"id": "b1", "tipo": "bcrp", "pregunta": "¿Pregunta?", "verdad": 1.0, "verdad_2": None,
                       "unidad": "%", "tolerancia": 0.1, "tolerancia_2": None}]).to_csv(
            tmp_path / "evaluacion" / "preguntas.csv", index=False)
    respuesta = ({"conducta": "responde", "respuesta": "texto"} if robustez else {"valor": 1.0, "fuente": "prueba"})
    monkeypatch.setattr(evaluar, "RAIZ", tmp_path)
    monkeypatch.setattr(evaluar, "AQUI", tmp_path / "evaluacion")
    monkeypatch.setattr(evaluar, "preguntar", lambda *a: {**respuesta, "segundos": 1.0, "turnos": 1,
                                                          "costo_usd": 0.0, "herramientas": "", "error": ""})
    monkeypatch.setattr(sys, "argv", ["evaluar.py", "--modos", "A", "B", *(["--robustez"] if robustez else [])])
    evaluar.main()
    res = pd.read_csv(tmp_path / "evaluacion" / ("robustez_resultados.csv" if robustez else "resultados.csv"))
    assert list(res.columns) == [*(COLUMNAS_ROBUSTEZ if robustez else COLUMNAS_PREGUNTAS), "aislamiento"]
    assert res["aislamiento"].tolist() == ["claude_md_desactivado+setting_sources_project_local"] * 2
