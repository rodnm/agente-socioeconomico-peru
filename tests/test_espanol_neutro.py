"""Pruebas de español neutro en los artefactos redactados del proyecto.

Verifica que el README, la documentación, los módulos y los informes
no contengan formas de voseo ni regionalismos rioplatenses (S20).
"""
import re
from pathlib import Path
import pytest

PATRON_VOSEO = re.compile(
    r"\b("
    r"vos|"
    r"querés|tenés|podés|hacés|hacé|sabés|creés|"
    r"decime|avisame|fijate|acordate|probá|dejá|poné|tomá|seguí|leé|leés|andá|mirá|"
    r"indicás|referís|preferís"
    r")\b",
    re.IGNORECASE,
)


def buscar_voseo_en_texto(texto: str) -> list[str]:
    """Encuentra coincidencias de voseo en un texto."""
    return [m.group(0) for m in PATRON_VOSEO.finditer(texto)]


def test_detector_detecta_voseo():
    """El detector debe identificar formas de voseo."""
    coincidencias = buscar_voseo_en_texto("Si querés decime qué pensás y hacé eso")
    palabras = [c.lower() for c in coincidencias]
    assert "querés" in palabras
    assert "decime" in palabras
    assert "hacé" in palabras


def test_artefactos_redactados_no_tienen_voseo():
    """Ningún artefacto redactado del proyecto debe contener voseo."""
    raiz = Path(__file__).resolve().parent.parent

    archivos_a_revisar = [
        raiz / "README.md",
        raiz / "CLAUDE.md",
    ]
    # Carpetas de documentación y código propio
    carpetas = [
        raiz / ".claude" / "skills",
        raiz / "mcp",
        raiz / "scripts",
        raiz / "informes",
    ]
    for c in carpetas:
        if c.exists():
            for p in c.rglob("*"):
                if p.is_file() and p.suffix in (".md", ".py", ".txt"):
                    archivos_a_revisar.append(p)

    # Archivos markdown de evaluación
    carpeta_eval = raiz / "evaluacion"
    if carpeta_eval.exists():
        for p in carpeta_eval.glob("*.md"):
            archivos_a_revisar.append(p)

    hallazgos = []
    for path in archivos_a_revisar:
        contenido = path.read_text(encoding="utf-8", errors="ignore")
        coincidencias = buscar_voseo_en_texto(contenido)
        if coincidencias:
            hallazgos.append(f"{path.relative_to(raiz)}: {', '.join(set(coincidencias))}")

    assert not hallazgos, "Se encontraron formas de voseo en:\n" + "\n".join(hallazgos)
