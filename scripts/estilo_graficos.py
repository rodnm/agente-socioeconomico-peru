"""Módulo de estilo gráfico compartido y diseño visual para el proyecto.

Aplica principios modernos de visualización de datos:
- Jerarquía tipográfica clara sin superposiciones (H6).
- Paleta sobria, accesible y balanceada.
- Ejes limpios sin bordes redundantes y con rejillas sutiles.
- Citas de fuente legibles y alineadas con la figura.
"""
import re
import textwrap
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# Paleta editorial sobria y accesible
COLOR_PRINCIPAL = "#1f4e79"     # Azul institucional BCRP / serie temporal
COLOR_BARRA = "#2563eb"          # Azul accesible para barras
COLOR_TEXTO = "#0f172a"          # Pizarra 900 para títulos y etiquetas principales
COLOR_SECUNDARIO = "#475569"     # Pizarra 600 para subtítulos, fuentes y ejes
COLOR_LINEA_GUIA = "#cbd5e1"     # Pizarra 300 para líneas de referencia
COLOR_REJILLA = "#e2e8f0"        # Pizarra 200 sutil para guías
COLOR_FONDO = "#ffffff"          # Fondo blanco limpio

# Paleta categórica en orden fijo (nunca se reordena ni se recicla), validada con el validador de la skill dataviz:
# separación para daltonismo ΔE >= 9.1 entre vecinos. Tres tonos tienen contraste < 3:1 con el fondo, por eso
# toda serie se acompaña de leyenda, marcador y cifras escritas en tinta.
PALETA_CATEGORICA = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4")

# Escala secuencial monocromática para mapas departamentales (0 % a >45 %)
ESCALA_MAPA = LinearSegmentedColormap.from_list(
    "pobreza_azules",
    ["#f0f7ff", "#bae6fd", "#38bdf8", "#0284c7", "#0369a1", "#082f49"],
)


def estilizar_ejes(ax: Any, horizontal: bool = False) -> None:
    """Elimina espinas innecesarias y aplica rejilla suave."""
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.spines["left"].set_color(COLOR_LINEA_GUIA)
    ax.spines["bottom"].set_color(COLOR_LINEA_GUIA)
    ax.tick_params(colors=COLOR_SECUNDARIO, labelsize=9)

    # Rejilla de línea fina y continua: una rejilla punteada se confunde con un umbral o una proyección.
    ax.grid(axis="x" if horizontal else "y", color=COLOR_REJILLA, linestyle="-", linewidth=0.6)
    ax.set_axisbelow(True)


ESPACIO_FIJO = " "  # espacio que el envoltorio no corta


def _sin_cortes_en_cifras(texto: str) -> str:
    """Une cada cifra con su unidad («21.7 %», «0.3 puntos», «26 ámbitos», «14 años») para que no queden en
    líneas distintas."""
    return re.sub(r"(\d)\s+(%|puntos\b|ámbitos\b|años\b)", rf"\1{ESPACIO_FIJO}\2", texto)


def _envolver(texto: str, ancho: int) -> list[str]:
    """Envuelve cada párrafo por separado, sin partir palabras con guion (fechas como 2024-12)."""
    lineas = []
    for parrafo in _sin_cortes_en_cifras(texto).split("\n"):
        lineas += textwrap.wrap(parrafo, width=ancho, break_on_hyphens=False) or [""]
    return lineas


def encabezado(
    fig: plt.Figure,
    ax: Any,
    titulo: str,
    subtitulo: str | None = None,
    fuente: str | None = None,
    alineacion_x: float = 0.03,
) -> dict[str, matplotlib.text.Text]:
    """Aplica título, subtítulo y fuente a nivel de figura garantizando cero superposiciones (H6).

    Ajusta dinámicamente los márgenes del eje de datos para reservar el espacio necesario según la cantidad de
    líneas del título, del subtítulo y de la fuente. La fuente admite varios párrafos separados por saltos de línea
    (por ejemplo, una nota al pie) y se envuelve al ancho de la figura.
    """
    alto_figura = fig.get_figheight()
    ancho_figura = fig.get_figwidth()

    # Envoltorio de texto proporcional al ancho
    ancho_caracteres_titulo = max(int(ancho_figura * 9), 50)
    ancho_caracteres_sub = max(int(ancho_figura * 11), 60)
    ancho_caracteres_fuente = max(int(ancho_figura * 14), 70)

    lineas_titulo = _envolver(titulo, ancho_caracteres_titulo)
    lineas_sub = _envolver(subtitulo, ancho_caracteres_sub) if subtitulo else []
    lineas_fuente = _envolver(fuente, ancho_caracteres_fuente) if fuente else []

    # Cálculo de alturas relativas en coordenadas de figura (0 a 1)
    # 72 puntos por pulgada; factor de interlineado 1.35
    h_linea_titulo = (12.5 * 1.35) / (72.0 * alto_figura)
    h_linea_sub = (9.5 * 1.35) / (72.0 * alto_figura)
    h_linea_fuente = (8.0 * 1.35) / (72.0 * alto_figura)

    y_titulo_top = 0.985
    y_titulo_bottom = y_titulo_top - len(lineas_titulo) * h_linea_titulo

    textos: dict[str, matplotlib.text.Text] = {}

    t_titulo = fig.text(
        alineacion_x,
        y_titulo_top,
        "\n".join(lineas_titulo),
        ha="left",
        va="top",
        color=COLOR_TEXTO,
        fontsize=12.5,
        fontweight="bold",
    )
    textos["titulo"] = t_titulo

    if lineas_sub:
        espacio_titulo_sub = 0.014
        y_sub_top = y_titulo_bottom - espacio_titulo_sub
        y_sub_bottom = y_sub_top - len(lineas_sub) * h_linea_sub

        t_sub = fig.text(
            alineacion_x,
            y_sub_top,
            "\n".join(lineas_sub),
            ha="left",
            va="top",
            color=COLOR_SECUNDARIO,
            fontsize=9.5,
        )
        textos["subtitulo"] = t_sub
        limite_superior_eje = y_sub_bottom - 0.025
    else:
        limite_superior_eje = y_titulo_bottom - 0.030

    y_fuente = 0.015
    if lineas_fuente:
        t_fuente = fig.text(
            alineacion_x,
            y_fuente,
            "\n".join(lineas_fuente),
            ha="left",
            va="bottom",
            color=COLOR_SECUNDARIO,
            fontsize=8.0,
        )
        textos["fuente"] = t_fuente
        limite_inferior_eje = y_fuente + len(lineas_fuente) * h_linea_fuente + 0.04
    else:
        limite_inferior_eje = 0.045

    # Restringe el área del eje para que no colisione con el encabezado ni con el pie
    fig.tight_layout(rect=(0.01, limite_inferior_eje, 0.99, max(limite_superior_eje, 0.2)))

    return textos
