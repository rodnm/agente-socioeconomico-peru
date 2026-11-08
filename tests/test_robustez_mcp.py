"""Robustez del servidor del BCRP frente a respuestas raras, sin depender de la red.

    uv run pytest tests/test_robustez_mcp.py

Se reemplaza la descarga por respuestas simuladas para cubrir lo que la API real hace a veces: devolver una página
HTML con código 200 (anti-bots o límite de consultas), marcar periodos como "n.d." o no tener datos en el rango.
Todo se prueba a través del cliente MCP, igual que en mcp/test_server.py.
"""
import asyncio
import os
import time

import pytest
from conftest import HTML, periodos
from fastmcp import Client
from fastmcp.exceptions import ToolError

import server


def llamar(herramienta, **args):
    async def con_cliente():
        async with Client(server.mcp) as c:
            return await c.call_tool(herramienta, args)
    return asyncio.run(con_cliente()).data


def test_pagina_html_persistente_da_un_error_claro(api):
    api.respuestas = [HTML]
    with pytest.raises(ToolError, match="El BCRP no respondió con datos.*HTML"):
        llamar("serie", codigo="PN01271PM", desde="2025-01", hasta="2025-03")
    assert len(api.pedidas) == 4  # el pedido y tres reintentos


def test_reintenta_tras_una_pagina_html(api):
    api.respuestas = [HTML, periodos(("Ene.2025", "0.21"), ("Feb.2025", "0.5"))]
    r = llamar("serie", codigo="PN01271PM", desde="2025-01", hasta="2025-02")
    assert [d["periodo"] for d in r["datos"]] == ["2025-01", "2025-02"]
    assert len(api.pedidas) == 2


def test_salta_los_nd_y_lee_setiembre(api):
    api.respuestas = [periodos(("Ago.2025", "0.1"), ("Set.2025", "n.d."), ("Oct.2025", "0.3"))]
    r = llamar("serie", codigo="PN01271PM", desde="2025-08", hasta="2025-10")
    assert r["datos"] == [{"periodo": "2025-08", "valor": 0.1}, {"periodo": "2025-10", "valor": 0.3}]
    api.respuestas = [periodos(("Set.2025", "0.2"))]
    assert llamar("serie", codigo="PN01273PM", desde="2025-09", hasta="2025-09")["datos"][0]["periodo"] == "2025-09"


def test_rango_sin_datos_lo_dice_en_vez_de_inventar(api):
    api.respuestas = [periodos(("Ene.2030", "n.d."))]
    with pytest.raises(ToolError, match="no tiene datos entre 2030-01 y 2030-03"):
        llamar("serie", codigo="PN01271PM", desde="2030-01", hasta="2030-03")


def test_usa_la_copia_vencida_y_lo_avisa_si_el_bcrp_no_responde(api):
    api.respuestas = [periodos(("Ene.2025", "0.21"))]
    llamar("serie", codigo="PN01271PM", desde="2025-01", hasta="2025-01")
    for archivo in (api_cache := server.CACHE).iterdir():
        hace_dos_dias = time.time() - 2 * 24 * 3600
        os.utime(archivo, (hace_dos_dias, hace_dos_dias))
    api.respuestas = [HTML]
    r = llamar("serie", codigo="PN01271PM", desde="2025-01", hasta="2025-01")
    assert r["datos"] == [{"periodo": "2025-01", "valor": 0.21}]
    assert "copia guardada" in r["aviso"]
    assert any(api_cache.iterdir())


def test_formatos_de_fecha_por_frecuencia(api):
    api.respuestas = [periodos(("01.Feb.26", "3.7"), ("27.Feb.26", "3.71"))]
    llamar("serie", codigo="PD04638PD", desde="2026-02", hasta="2026-02")
    assert api.pedidas[-1].endswith("/PD04638PD/json/2026-02-01/2026-02-28")
    api.respuestas = [periodos(("T1.25", "3.9"), ("T2.25", "2.8"))]
    r = llamar("serie", codigo="PN02526AQ", desde="2025-T1", hasta="2025-06")
    assert api.pedidas[-1].endswith("/PN02526AQ/json/2025-1/2025-2")
    assert [d["periodo"] for d in r["datos"]] == ["2025-T1", "2025-T2"]
    api.respuestas = [periodos(("2024", "3.3"))]
    assert llamar("serie", codigo="PM04863AA", desde="2024-05", hasta="2024")["datos"][0]["periodo"] == "2024"
    assert api.pedidas[-1].endswith("/PM04863AA/json/2024/2024")


def test_fecha_invalida_se_rechaza_sin_llamar_a_la_api(api):
    with pytest.raises(ToolError, match="no válida"):
        llamar("serie", codigo="PN01271PM", desde="enero 2025", hasta="2025-03")
    with pytest.raises(ToolError, match="el mes va de 01 a 12"):
        llamar("serie", codigo="PN01271PM", desde="2025-13", hasta="2025-14")
    assert api.pedidas == []


def test_busqueda_ambigua_devuelve_candidatos_y_la_absurda_ninguno(api):
    candidatos = llamar("buscar_series", texto="ipc")
    assert {c["codigo"] for c in candidatos} == {"PN01270PM", "PN38705PM", "PN01271PM", "PN01273PM"}
    assert llamar("buscar_series", texto="inflacion de narnia") == []


def test_comparar_con_pocos_periodos_comunes_da_error(api):
    api.respuestas = [periodos(("Ene.2025", "0.2"), ("Feb.2025", "0.3"))]
    with pytest.raises(ToolError, match="al menos 3"):
        llamar("comparar_series", codigo_a="PN01271PM", codigo_b="PN01273PM", desde="2025-01", hasta="2025-02")


def test_resumen_no_divide_por_cero(api):
    api.respuestas = [periodos(("Ene.2025", "0"), ("Feb.2025", "0.5"), ("Mar.2025", "0.2"))]
    r = llamar("resumen", codigo="PN01271PM", desde="2025-01", hasta="2025-03")
    assert r["variacion_pct"] is None
    assert r["cambio"] == pytest.approx(0.2)
    assert r["maximo"] == {"periodo": "2025-02", "valor": 0.5}


def test_graficar_guarda_el_png_y_cita_la_fuente(api):
    api.respuestas = [periodos(("Ene.2025", "1.9"), ("Feb.2025", "1.5"), ("Mar.2025", "1.3"))]
    r = llamar("graficar_serie", codigo="PN01273PM", desde="2025-01", hasta="2025-03")
    assert r["archivo"] == "figuras/bcrp_PN01273PM_2025-01_2025-03.png"
    assert (server.FIGURAS / "bcrp_PN01273PM_2025-01_2025-03.png").stat().st_size > 0
    assert r["fuente"].startswith("https://estadisticas.bcrp.gob.pe")
    datos = (server.RAIZ / "salidas" / "bcrp" / "PN01273PM_2025-01_2025-03.csv").read_text(encoding="utf-8")
    assert datos.splitlines()[0] == "periodo,valor,codigo,nombre,fuente" and "2025-03,1.3" in datos


def test_el_recurso_describe_la_serie(api):
    async def leer():
        async with Client(server.mcp) as c:
            return await c.read_resource("bcrp://serie/PN01273PM")
    contenido = asyncio.run(leer())[0].text
    assert "IPC (var% 12 meses)" in contenido and "Mensual" in contenido
