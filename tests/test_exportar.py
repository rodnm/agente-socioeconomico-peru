"""El exportador de evidencias resume qué herramientas usó el agente y en qué orden.

    uv run pytest tests/test_exportar.py
"""
import importlib.util
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
