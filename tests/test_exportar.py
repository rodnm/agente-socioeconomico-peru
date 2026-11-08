"""El exportador de evidencias resume qué herramientas usó el agente y en qué orden.

    uv run pytest tests/test_exportar.py
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "exportar_evidencias.py"


@pytest.fixture
def exportar():
    spec = importlib.util.spec_from_file_location("exportar_evidencias", SCRIPT)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def uso(nombre, **entrada):
    return {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": nombre, "input": entrada}]}}


EVENTOS = [
    {"type": "user", "message": {"content": "Haz el informe."}},
    uso("Skill", skill="informando-peru"),
    uso("mcp__bcrp__resumen", codigo="PN01273PM", desde="2024-01", hasta="2024-12"),
    uso("Bash", command="uv run limpiar.py --anio 2024\necho listo"),
    uso("mcp__sbs__indicadores", tipo_entidad="bancos"),
    uso("Skill", skill="verificando-consistencia"),
    uso("mcp__bcrp__serie", codigo="PN01273PM"),
    uso("StructuredOutput", valor=1),
    {"type": "assistant", "message": {"content": [{"type": "text", "text": "Listo."}]}},
]


def test_linea_de_tiempo_lista_las_herramientas_en_orden(exportar):
    md = exportar.a_markdown(EVENTOS, "Corrida")
    assert "## Línea de tiempo" in md
    assert "Servidores MCP: `bcrp`, `sbs` · Skills: `informando-peru`, `verificando-consistencia` · 6 llamadas" in md
    pasos = ["1. Skill `informando-peru`", "2. MCP `bcrp.resumen`", "3. Bash `uv run limpiar.py --anio 2024`",
             "4. MCP `sbs.indicadores`", "5. Skill `verificando-consistencia`", "6. MCP `bcrp.serie`"]
    posiciones = [md.index(p) for p in pasos]
    assert posiciones == sorted(posiciones)
    assert "StructuredOutput" not in md.split("## Línea de tiempo")[1].split("## 1.")[0]


def test_sin_herramientas_no_hay_linea_de_tiempo(exportar):
    md = exportar.a_markdown(EVENTOS[:1] + EVENTOS[-1:], "Charla")
    assert "Línea de tiempo" not in md


def test_la_transcripcion_sigue_completa(exportar):
    md = exportar.a_markdown(EVENTOS, "Corrida")
    assert "## 1. Pedido" in md and "Haz el informe." in md and "**Claude:**" in md and "Listo." in md
    assert md.count("**Herramienta:**") == 7


def test_lo_que_genera_claude_code_no_figura_como_pedido(exportar):
    eventos = [
        {"type": "user", "timestamp": "2026-11-02T16:57:02Z", "message": {"content": (
            "This session is being continued from a previous conversation that ran out of context. Resumen.")}},
        {"type": "user", "message": {"content": "[Usage limit reached; a short grace allowance remains.]"}},
        {"type": "user", "timestamp": "2026-11-02T23:10:31Z", "message": {"content": "continua"}},
    ]
    md = exportar.a_markdown(eventos, "Sesión")
    assert md.count(". Pedido") == 1 and "## 1. Pedido · 2026-11-02 23:10:31 UTC" in md
    assert "Resumen automático" in md and "Usage limit" not in md


def test_el_texto_pegado_cuenta_como_pedido(exportar):
    eventos = [{"type": "user", "timestamp": "2026-11-05T05:00:00Z", "message": {"content": (
        '\n\n<pasted_content id="ab12">\nPropuesta de preguntas.\n</pasted_content id="ab12">')}}]
    md = exportar.a_markdown(eventos, "Sesión")
    assert "## 1. Pedido · 2026-11-05 05:00:00 UTC" in md and "*Texto pegado:*\n\nPropuesta de preguntas." in md
    assert "pasted_content" not in md and "ab12" not in md


def test_un_correo_cortado_por_el_limite_igual_se_oculta(exportar):
    relleno = "x" * (exportar.LIMITE_RESULTADO - 10)
    eventos = [{"type": "user", "message": {"content": [
        {"type": "tool_result", "content": f"{relleno} autora@ejemplo.com y más texto"}]}}]
    md = exportar.a_markdown(eventos, "Sesión")
    assert "autora" not in md and "ejemplo" not in md  # el reemplazo puede quedar cortado; el correo no asoma


def test_oculta_tambien_los_textos_indicados(exportar):
    eventos = [{"type": "user", "message": {"content": "Busca IlusionX en los archivos."}},
               uso("Bash", command="grep -n ilusionx evidencias_ia/")]
    md = exportar.a_markdown(eventos, "Sesión", extra=("ilusionx",))
    assert "ilusionx" not in md.lower() and md.count("[OCULTO]") == 3  # pedido, línea de tiempo y argumentos


def test_un_texto_vacio_para_ocultar_no_cambia_nada(exportar):
    assert exportar.a_markdown(EVENTOS, "Corrida", extra=("",)) == exportar.a_markdown(EVENTOS, "Corrida")


def test_la_opcion_ocultar_se_puede_repetir(tmp_path):
    origen, destino = tmp_path / "sesion.jsonl", tmp_path / "sesion.md"
    origen.write_text(json.dumps({"type": "user", "message": {"content": "Ana Pérez y apz99 revisaron."}}) + "\n",
                      encoding="utf-8")
    subprocess.run([sys.executable, str(SCRIPT), str(origen), str(destino), "--ocultar", "ana pérez",
                    "--ocultar", "APZ99"], check=True, capture_output=True)
    md = destino.read_text(encoding="utf-8")
    assert "Ana" not in md and "apz99" not in md and md.count("[OCULTO]") == 2


def test_los_recordatorios_del_sistema_siguen_fuera(exportar):
    eventos = [{"type": "user", "message": {"content": "<system-reminder>Contexto interno.</system-reminder>"}},
               {"type": "user", "message": {"content": "continua"}}]
    md = exportar.a_markdown(eventos, "Sesión")
    assert md.count(". Pedido") == 1 and "Contexto interno" not in md


def paso(indice, tipo, fuente="MODEL", **campos):
    return {"step_index": indice, "source": fuente, "type": tipo, "status": "DONE",
            "created_at": f"2026-11-05T18:27:{indice:02d}Z", **campos}


ANTIGRAVITY = [
    paso(0, "USER_INPUT", "USER_EXPLICIT", content=(
        "<USER_REQUEST>\nEjecuta la fase 0 del plan.\n</USER_REQUEST>\n<ADDITIONAL_METADATA>\n"
        "The current local time is: 2026-11-05T13:27:00-05:00.\n</ADDITIONAL_METADATA>")),
    paso(1, "PLANNER_RESPONSE", thinking="Pienso en privado.", tool_calls=[
        {"name": "run_command", "args": {"CommandLine": r"uv run pytest C:\Users\Persona\repo\tests -q"}},
        {"name": "call_mcp_tool", "args": {"ServerName": "engram", "ToolName": "mem_save", "Arguments": {}}}]),
    paso(2, "GENERIC", content="Created At: 2026-11-05T13:27:02-05:00\n192 passed; revisado por apz99"),
    paso(3, "SYSTEM_MESSAGE", "SYSTEM", content=(
        "The following is a <SYSTEM_MESSAGE> not actually sent by the user.\n<SYSTEM_MESSAGE>\n[Message] aviso"
        "\n</SYSTEM_MESSAGE>")),
    paso(4, "CHECKPOINT", "SYSTEM", content="# Resuming from a compaction\n\nResumen de lo anterior."),
    paso(5, "PLANNER_RESPONSE", content="Fase 0 terminada."),
]


def exportar_antigravity(tmp_path, *opciones):
    """Escribe la sesión en dos fragmentos que cortan un registro a la mitad, como lo hace Antigravity."""
    sesion = tmp_path / "d5f5693e"
    fragmentos = sesion / ".system_generated" / "logs" / "chunks" / "transcript_full"
    fragmentos.mkdir(parents=True)
    texto = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in ANTIGRAVITY)
    corte = texto.index("192 passed")
    (fragmentos / "00000000.jsonl").write_text(texto[:corte], encoding="utf-8")
    (fragmentos / "00000001.jsonl").write_text(texto[corte:], encoding="utf-8")
    destino = tmp_path / "gemini.md"
    r = subprocess.run([sys.executable, str(SCRIPT), str(sesion), str(destino), *opciones],
                       capture_output=True, text=True, encoding="utf-8")
    return r, destino


def test_una_sesion_de_antigravity_se_exporta_desde_su_carpeta(tmp_path):
    r, destino = exportar_antigravity(tmp_path, "--ocultar", "apz99")
    assert r.returncode == 0, r.stderr
    assert "6 registros exportados" in r.stdout
    md = destino.read_text(encoding="utf-8")
    assert "## 1. Pedido · 2026-11-05 18:27:00 UTC" in md and "Ejecuta la fase 0 del plan." in md
    assert "USER_REQUEST" not in md and "ADDITIONAL_METADATA" not in md
    assert "**Gemini:**" in md and "Fase 0 terminada." in md and "**Claude:**" not in md
    assert "**Herramienta:** `run_command`" in md and "192 passed" in md  # el registro cortado se unió
    assert "Servidores MCP: `engram` · Skills: ninguno · 2 llamadas" in md
    assert "1. run_command `uv run pytest ~\\repo\\tests -q`" in md and "2. MCP `engram.mem_save`" in md
    assert "Persona" not in md and "apz99" not in md and "Pienso en privado" not in md


def test_antigravity_pliega_las_compactaciones_y_los_mensajes_del_sistema(tmp_path):
    md = exportar_antigravity(tmp_path)[1].read_text(encoding="utf-8")
    assert md.count(". Pedido") == 1
    assert "<summary>Resumen automático de la parte anterior de la sesión (Antigravity compactó el contexto)" in md
    assert "<summary>Mensaje del sistema de Antigravity</summary>" in md
