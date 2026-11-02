"""La skill verificando-consistencia detecta cuándo dos herramientas no coinciden.

    uv run pytest tests/test_consistencia.py

La parte de la ENAHO lee las salidas versionadas; la del BCRP usa la API simulada de conftest.py.
"""
import importlib.util
import shutil
from pathlib import Path

import pytest
from conftest import HTML, periodos

RAIZ = Path(__file__).resolve().parents[1]
SCRIPT = RAIZ / ".claude" / "skills" / "verificando-consistencia" / "scripts" / "verificar.py"
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Set", "Oct", "Nov", "Dic"]


@pytest.fixture
def verificar():
    spec = importlib.util.spec_from_file_location("verificar", SCRIPT)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def resultados(reg, fuente):
    return {f["verificacion"]: f["resultado"] for f in reg.filas if f["fuente"] == fuente}


def respuestas_ipc(alterar_mes=None):
    """24 meses de índice y los 12 de variación a 12 meses calculados con él, como los publicaría el BCRP."""
    nombres = [f"{m}.{a}" for a in (2023, 2024) for m in MESES]
    indice = [100 + 0.3 * i for i in range(24)]
    variacion = [round((indice[i + 12] / indice[i] - 1) * 100, 2) for i in range(12)]
    if alterar_mes is not None:
        variacion[alterar_mes] += 0.3
    return [periodos(*zip(nombres, map(str, indice))), periodos(*zip(nombres[12:], map(str, variacion)))]


def test_enaho_versionada_es_consistente(verificar, tmp_path):
    reg = verificar.Registro()
    verificar.verificar_enaho(reg)
    assert set(resultados(reg, "ENAHO").values()) == {"OK"}
    assert len(reg.filas) == 5


def test_detecta_un_mapa_que_no_coincide_con_los_indicadores(verificar, tmp_path, monkeypatch):
    for archivo in ("indicadores.csv", "validacion.txt", "mapa_vs_referencia.csv"):
        shutil.copy(RAIZ / "salidas" / archivo, tmp_path / archivo)
    mapa = (tmp_path / "mapa_vs_referencia.csv").read_text(encoding="utf-8")
    (tmp_path / "mapa_vs_referencia.csv").write_text(mapa.replace("08,CUSCO,18.5", "08,CUSCO,28.5", 1),
                                                     encoding="utf-8")
    monkeypatch.setattr(verificar, "SALIDAS", tmp_path)
    reg = verificar.Registro()
    verificar.verificar_enaho(reg)
    assert resultados(reg, "ENAHO")["Mapa (mapeando-enaho) frente a indicadores (limpiando-enaho)"] == "FALLA"


def test_bcrp_consistente(verificar, api):
    api.respuestas = respuestas_ipc()
    reg = verificar.Registro()
    verificar.verificar_bcrp(reg, 2024)
    assert set(resultados(reg, "BCRP").values()) == {"OK"}


def test_bcrp_detecta_una_variacion_que_no_sale_del_indice(verificar, api):
    api.respuestas = respuestas_ipc(alterar_mes=5)
    reg = verificar.Registro()
    verificar.verificar_bcrp(reg, 2024)
    fila = next(f for f in reg.filas if f["verificacion"].startswith("Inflación a 12 meses"))
    assert fila["resultado"] == "DIFERENCIA" and "2024-06" in fila["detalle"]


def test_bcrp_recalcula_con_el_indice_vigente(verificar, api):
    # PN01270PM (base 2009) se descontinuó en diciembre de 2021; el índice vigente es PN38705PM (base Dic.2021).
    api.respuestas = respuestas_ipc()
    reg = verificar.Registro()
    verificar.verificar_bcrp(reg, 2024)
    assert "/PN38705PM/" in api.pedidas[0]
    assert set(resultados(reg, "BCRP").values()) == {"OK"}


def test_bcrp_sin_datos_no_se_atribuye_a_una_caida(verificar, api):
    api.respuestas = [periodos()]
    reg = verificar.Registro()
    verificar.verificar_bcrp(reg, 2024)
    assert set(resultados(reg, "BCRP").values()) == {"NO VERIFICABLE"}
    assert all("no tiene datos" in f["detalle"] and "no respondió" not in f["explicacion"] for f in reg.filas)


def test_bcrp_caido_no_se_reemplaza_por_estimaciones(verificar, api):
    api.respuestas = [HTML]
    reg = verificar.Registro()
    verificar.verificar_bcrp(reg, 2024)
    assert set(resultados(reg, "BCRP").values()) == {"NO VERIFICABLE"}
    assert all("HTML" in f["detalle"] for f in reg.filas)
