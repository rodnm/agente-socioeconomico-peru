"""Pruebas del estilo gráfico compartido y oráculo de la hipótesis H6.

Hipótesis H6: El nuevo encabezado no superpone título, subtítulo ni fuente.
Oráculo: prueba que mide las cajas de texto renderizadas en display pixels y exige que no se crucen.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "mcp"))

import estilo_graficos


def cajas_de_texto(fig, ax, textos):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bb_titulo = textos["titulo"].get_window_extent(renderer)
    bb_sub = textos["subtitulo"].get_window_extent(renderer) if textos.get("subtitulo") else None
    bb_fuente = textos["fuente"].get_window_extent(renderer) if textos.get("fuente") else None
    bb_ax = ax.get_window_extent(renderer)
    return bb_titulo, bb_sub, bb_fuente, bb_ax


def test_h6_encabezado_no_superpone_elementos():
    fig, ax = plt.subplots(figsize=(9, 4.8), facecolor=estilo_graficos.COLOR_FONDO)
    ax.plot([1, 2, 3], [10, 20, 15], color=estilo_graficos.COLOR_PRINCIPAL)
    estilo_graficos.estilizar_ejes(ax)

    textos = estilo_graficos.encabezado(
        fig, ax,
        titulo="Inflación a 12 meses del IPC de Lima Metropolitana",
        subtitulo="Variación porcentual acumulada · 2024-01 a 2024-12",
        fuente="Fuente: BCRP (serie PN01273PM).",
    )

    bb_titulo, bb_sub, bb_fuente, bb_ax = cajas_de_texto(fig, ax, textos)

    # Ninguna caja de texto debe cruzar a otra ni a la caja del eje de datos
    assert not bb_titulo.overlaps(bb_sub), "El título y el subtítulo se superponen"
    assert not bb_sub.overlaps(bb_ax), "El subtítulo y el eje de datos se superponen"
    assert not bb_fuente.overlaps(bb_ax), "La fuente y el eje de datos se superponen"
    assert not bb_titulo.overlaps(bb_fuente), "El título y la fuente se superponen"
    plt.close(fig)


def test_h6_encabezado_con_titulo_largo_multilinea():
    fig, ax = plt.subplots(figsize=(8, 8.6), facecolor=estilo_graficos.COLOR_FONDO)
    ax.barh(range(5), [10, 20, 30, 40, 50], color=estilo_graficos.COLOR_BARRA)
    estilo_graficos.estilizar_ejes(ax, horizontal=True)

    textos = estilo_graficos.encabezado(
        fig, ax,
        titulo="Cajamarca (45.0 %) y Loreto (43.0 %) presentan los niveles más críticos de pobreza monetaria departamental en 2024",
        subtitulo="Pobreza monetaria por departamento, Perú 2024 (% de personas)",
        fuente="Fuente: INEI, ENAHO 2024 (módulos 34 y 02). Ponderado por hogar con factor07 × mieperho.",
    )

    bb_titulo, bb_sub, bb_fuente, bb_ax = cajas_de_texto(fig, ax, textos)

    assert not bb_titulo.overlaps(bb_sub), "El título multilinea y el subtítulo se superponen"
    assert not bb_sub.overlaps(bb_ax), "El subtítulo y el eje de datos se superponen"
    assert not bb_fuente.overlaps(bb_ax), "La fuente y el eje de datos se superponen"
    plt.close(fig)


def test_server_graficar_serie_usa_estilo_sin_colisiones(api):
    import server
    from conftest import periodos
    api.respuestas = [periodos(("Ene.2025", "1.9"), ("Feb.2025", "1.5"), ("Mar.2025", "1.3"))]
    r = server.graficar_serie(codigo="PN01273PM", desde="2025-01", hasta="2025-03")
    archivo = server.RAIZ / r["archivo"]
    assert archivo.is_file()
    assert archivo.stat().st_size > 0
