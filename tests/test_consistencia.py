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
    assert all("HTML" in f["detalle"] and "no respondió" in f["explicacion"] for f in reg.filas)


def test_departamentos_frente_al_inei_excluyen_lima_15(verificar):
    # El INEI no publica una cifra para el departamento 15 en conjunto: se compara Lima Metropolitana y Lima
    # provincias en su lugar, y la consigna de 25 departamentos se sigue exigiendo en indicadores.csv.
    reg = verificar.Registro()
    verificar.verificar_enaho(reg)
    fila = next(f for f in reg.filas if "informe técnico del INEI" in f["verificacion"])
    assert fila["resultado"] == "OK"
    assert "25 departamentos en indicadores.csv" in fila["detalle"]
    assert "24 departamentos" in fila["detalle"] and "Lima Metropolitana" in fila["detalle"]
    assert "Lima (15) sin cifra publicada por el INEI" in fila["detalle"]


def test_departamentos_frente_al_inei_falla_si_falta_uno_de_los_25(verificar, tmp_path, monkeypatch):
    for archivo in ("indicadores.csv", "validacion.txt", "mapa_vs_referencia.csv"):
        shutil.copy(RAIZ / "salidas" / archivo, tmp_path / archivo)
    indicadores = (tmp_path / "indicadores.csv").read_text(encoding="utf-8").splitlines()
    sin_15 = [l for l in indicadores if not l.startswith("2024,pobreza_dep_15,")]
    (tmp_path / "indicadores.csv").write_text("\n".join(sin_15) + "\n", encoding="utf-8")
    monkeypatch.setattr(verificar, "SALIDAS", tmp_path)
    reg = verificar.Registro()
    verificar.verificar_enaho(reg)
    fila = next(f for f in reg.filas if "informe técnico del INEI" in f["verificacion"])
    assert fila["resultado"] == "FALLA" and "24 departamentos en indicadores.csv" in fila["detalle"]


def morosidad_falsa(bcrp, sbs):
    """Respuestas simuladas: la serie mensual del BCRP y un boletín B-2401 por diciembre."""
    datos = [{"periodo": f"{a}-{m:02d}", "valor": bcrp.get(a, 9.9) if m == 12 else 9.9}
             for a in range(2020, 2025) for m in range(1, 13)]
    boletines = {a: {"codigo": "B-2401", "periodo": f"{a}-12", "indicadores": [
        {"indicador": "Créditos Atrasados (criterio SBS) / Créditos Directos", "total": {"valor": v}}]}
        for a, v in sbs.items()}

    async def consultar(anios):
        return {"nombre": "Cartera atrasada neta / Colocaciones netas (%) - Empresas Bancarias", "datos": datos}, \
            {a: boletines[a] for a in anios if a in boletines}
    return consultar


def test_morosidad_compara_los_cinco_diciembres(verificar, monkeypatch):
    bcrp = {2020: 3.80, 2021: 3.70, 2022: 3.90, 2023: 4.00, 2024: 3.80}
    sbs = {2020: 3.80, 2021: 3.73, 2022: 3.85, 2023: 3.67, 2024: 3.75}
    monkeypatch.setattr(verificar, "_consultar_morosidad", morosidad_falsa(bcrp, sbs))
    reg = verificar.Registro()
    verificar.verificar_morosidad(reg)
    [fila] = [f for f in reg.filas if f["fuente"] == "BCRP / SBS"]
    assert fila["resultado"] == "DIFERENCIA"
    assert "5 diciembres" in fila["detalle"]
    assert all(f"{a}-12" in fila["detalle"] for a in range(2020, 2025))
    assert "diferencia absoluta máxima 0.33 puntos en 2023-12" in fila["detalle"]
    assert "9.9" not in fila["detalle"]  # solo diciembres
    assert "Créditos Atrasados (criterio SBS) / Créditos Directos" in fila["explicacion"]
    assert "Cartera atrasada neta / Colocaciones netas" in fila["explicacion"]


def test_morosidad_declara_los_diciembres_que_faltan(verificar, monkeypatch):
    bcrp = {a: 3.8 for a in range(2020, 2025)}
    sbs = {2020: 3.8, 2022: 3.8, 2023: 3.8, 2024: 3.8}
    monkeypatch.setattr(verificar, "_consultar_morosidad", morosidad_falsa(bcrp, sbs))
    reg = verificar.Registro()
    verificar.verificar_morosidad(reg)
    [fila] = [f for f in reg.filas if f["fuente"] == "BCRP / SBS"]
    assert fila["resultado"] == "DIFERENCIA"
    assert "4 diciembres" in fila["detalle"] and "sin dato de la SBS: 2021-12" in fila["detalle"]


def test_morosidad_sin_respuesta_no_se_estima(verificar, monkeypatch):
    async def caida(anios):
        raise RuntimeError("El BCRP respondió HTML")
    monkeypatch.setattr(verificar, "_consultar_morosidad", caida)
    reg = verificar.Registro()
    verificar.verificar_morosidad(reg)
    [fila] = [f for f in reg.filas if f["fuente"] == "BCRP / SBS"]
    assert fila["resultado"] == "NO VERIFICABLE" and "HTML" in fila["detalle"]
