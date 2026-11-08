"""La skill informando-peru: el informe solo se escribe si cada cifra sale de un marcador resuelto.

    uv run pytest tests/test_informe.py

Las pruebas por consola usan indicadores de la ENAHO (salidas/indicadores.csv, versionado); la del BCRP llama al
servidor en proceso con la API simulada de conftest.py, así que ninguna necesita internet.
"""
import importlib.util
import subprocess
import sys
from pathlib import Path

from conftest import periodos

RAIZ = Path(__file__).resolve().parents[1]
SCRIPT = RAIZ / ".claude" / "skills" / "informando-peru" / "scripts" / "armar_informe.py"


def armar(tmp_path, borrador, *extra):
    (tmp_path / "borrador.md").write_text(borrador, encoding="utf-8")
    salida = tmp_path / "informe.md"
    r = subprocess.run([sys.executable, str(SCRIPT), "--borrador", str(tmp_path / "borrador.md"), "--salida",
                        str(salida), *extra], capture_output=True, text=True, encoding="utf-8", cwd=RAIZ)
    return r, salida


def test_resuelve_indicadores_y_agrega_trazabilidad(tmp_path):
    r, salida = armar(tmp_path, "La pobreza fue {{enaho.pobreza_nacional}} % entre "
                                "{{enaho.residentes_habituales|0}} residentes, con tolerancia {{lit:0.1 puntos}}.\n")
    assert r.returncode == 0, r.stderr
    texto = salida.read_text(encoding="utf-8")
    assert "La pobreza fue 27.6 % entre 108,664 residentes, con tolerancia 0.1 puntos." in texto
    assert "## Trazabilidad de las cifras" in texto and "## Referencias" in texto
    assert "factor07 × mieperho" in texto and "«0.1 puntos»" in texto


def test_referencias_en_formato_apa7(tmp_path):
    r, salida = armar(tmp_path, "La pobreza fue {{enaho.pobreza_nacional}} %.\n")
    assert r.returncode == 0, r.stderr
    texto = salida.read_text(encoding="utf-8")
    assert "Instituto Nacional de Estadística e Informática. (2025" in texto
    assert "Perú: Evolución de la Pobreza Monetaria 2015-2024" in texto


def test_rechaza_cifras_escritas_a_mano(tmp_path):
    r, salida = armar(tmp_path, "La pobreza fue 27.6 % y hubo 108,664 residentes en 2024.\n")
    assert r.returncode != 0
    assert "«27.6 %»" in r.stderr and "«108,664»" in r.stderr
    assert "2024" not in r.stderr.split("cifra escrita a mano")[-1]  # los años no son cifras
    assert not salida.exists()


def test_marcador_desconocido_no_se_inventa(tmp_path):
    r, salida = armar(tmp_path, "Dato: {{enaho.pobreza_en_narnia}}.\n")
    assert r.returncode != 0 and "marcador sin resolver" in r.stderr
    assert not salida.exists()
    r, salida = armar(tmp_path, "Dato: {{enaho.pobreza_en_narnia}}.\n", "--permitir-faltantes")
    texto = salida.read_text(encoding="utf-8")
    assert "[sin dato: KeyError" in texto and "### Datos no disponibles" in texto


def test_figura_citada_debe_existir(tmp_path):
    r, _ = armar(tmp_path, "![Mapa](no_existe.png)\n")
    assert r.returncode != 0 and "no_existe.png" in r.stderr


def test_resuelve_herramientas_del_bcrp_por_mcp(api):
    spec = importlib.util.spec_from_file_location("armar_informe", SCRIPT)
    armar_informe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(armar_informe)
    api.respuestas = [periodos(("Ene.2024", "3.0"), ("Jun.2024", "2.3"), ("Dic.2024", "1.97"))]
    marcador = "{{bcrp.resumen(codigo=PN01273PM, desde=2024-01, hasta=2024-12).ultimo.valor|2}}"
    reemplazos, traza, faltantes, _ = armar_informe.resolver(f"Inflación: {marcador} %.", False)
    assert faltantes == []
    assert reemplazos[marcador] == "1.97"
    assert traza[0][2].startswith("https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01273PM/json/2024-1/")
