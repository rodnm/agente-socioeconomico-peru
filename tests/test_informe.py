"""La skill informando-peru: el informe solo se escribe si cada cifra sale de un marcador resuelto.

    uv run pytest tests/test_informe.py

Las pruebas por consola usan indicadores de la ENAHO (salidas/indicadores.csv, versionado); la del BCRP llama al
servidor en proceso con la API simulada de conftest.py, así que ninguna necesita internet.
"""
import importlib.util
import json
import os
import subprocess
import sys
from datetime import date, datetime
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


def test_resuelve_indicadores_con_selector_de_anio(tmp_path):
    r, salida = armar(tmp_path, "La pobreza en 2020 fue {{enaho.pobreza_nacional:2020}} % y en 2024 fue {{enaho.pobreza_nacional}} %.\n")
    assert r.returncode == 0, r.stderr
    texto = salida.read_text(encoding="utf-8")
    assert "La pobreza en 2020 fue 30.1 % y en 2024 fue 27.6 %." in texto


def test_referencia_apa_del_informe_tecnico_del_inei(tmp_path):
    r, salida = armar(tmp_path, "La pobreza fue {{enaho.pobreza_nacional}} %.\n")
    assert r.returncode == 0, r.stderr
    texto = salida.read_text(encoding="utf-8")
    assert ("- Instituto Nacional de Estadística e Informática. (2025). *Perú: Evolución de la pobreza monetaria, "
            "2015-2024: Informe técnico*. https://cdn.www.gob.pe/uploads/document/file/8058556/"
            "6763186-peru-evolucion-de-la-pobreza-monetaria-2015-2024.pdf\n") in texto
    assert "Lima: INEI" not in texto and "**" not in texto.split("## Referencias")[1]


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


def cargar():
    spec = importlib.util.spec_from_file_location("armar_informe", SCRIPT)
    armar_informe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(armar_informe)
    return armar_informe


def con_fecha(ruta, anio, mes, dia):
    """Crea el archivo con esa fecha de modificación: la de descarga que se cita como «Recuperado el»."""
    ruta.write_bytes(b"zip")
    marca = datetime(anio, mes, dia, 12, 0).timestamp()
    os.utime(ruta, (marca, marca))


HOY = date(2026, 11, 5)


def test_referencia_apa_de_cada_serie_del_bcrp(api):
    armar_informe = cargar()
    api.respuestas = [periodos(("Ene.2024", "3.0"), ("Dic.2024", "1.97")), periodos(("Jun.2024", "2.3")),
                      periodos(("2024", "3.3"))]
    borrador = ("{{bcrp.resumen(codigo=PN01273PM, desde=2024-01, hasta=2024-12).ultimo.valor|2}} "
                "{{bcrp.resumen(codigo=PN01273PM, desde=2024-06, hasta=2024-06).ultimo.valor|2}} "
                "{{bcrp.resumen(codigo=PM04863AA, desde=2024, hasta=2024).ultimo.valor|1}}")
    *_, faltantes, _, fuentes = armar_informe.resolver_con_fuentes(borrador, False, hoy=HOY)
    assert faltantes == []
    entradas, avisos = armar_informe.referencias(fuentes, [])
    assert avisos == []
    assert entradas == [  # una entrada por serie, aunque se consulte dos veces; s. f. con letras por ser del mismo autor
        "Banco Central de Reserva del Perú. (s. f.-a). *Índice de precios Lima Metropolitana - IPC (var% 12 meses)* "
        "(Serie PN01273PM) [Conjunto de datos]. BCRPData. Recuperado el 5 de noviembre de 2026, de "
        "https://estadisticas.bcrp.gob.pe/estadisticas/series/mensuales/resultados/PN01273PM/html",
        "Banco Central de Reserva del Perú. (s. f.-b). *PBI anual - PBI (var%)* (Serie PM04863AA) [Conjunto de datos]. "
        "BCRPData. Recuperado el 5 de noviembre de 2026, de "
        "https://estadisticas.bcrp.gob.pe/estadisticas/series/anuales/resultados/PM04863AA/html",
    ]


def boletin_sbs(llamadas):
    """Respuestas de sbs.indicadores con la forma real del MCP (B-2401), sin red."""
    def respuesta(periodo):
        anio = periodo[:4]
        return {"tipo_entidad": "bancos", "codigo": "B-2401", "titulo": "Indicadores Financieros por Empresa Bancaria",
                "periodo": periodo, "actualizado": "Thu, 20 Feb 2025 18:59:59 GMT",
                "fuente": f"https://intranet2.sbs.gob.pe/estadistica/financiera/{anio}/Diciembre/B-2401-di{anio}.XLS",
                "indicadores": [{"total": {"entidad": "Total Banca Múltiple", "valor": 3.75}}]}
    return {clave: respuesta(json.loads(clave[2])["periodo"]) for clave in llamadas}


def test_referencia_apa_de_cada_boletin_y_periodo_de_la_sbs(monkeypatch):
    armar_informe = cargar()

    async def falsa(llamadas):
        return boletin_sbs(llamadas)
    monkeypatch.setattr(armar_informe, "llamar_todo", falsa)
    borrador = ("{{sbs.indicadores(tipo_entidad=bancos, indicador=morosidad, periodo=2024-12).indicadores[0].total.valor|2}} "
                "{{sbs.indicadores(tipo_entidad=bancos, indicador=roe, periodo=2024-12).indicadores[0].total.valor|1}} "
                "{{sbs.indicadores(tipo_entidad=bancos, indicador=morosidad, periodo=2020-12).indicadores[0].total.valor|2}}")
    *_, faltantes, _, fuentes = armar_informe.resolver_con_fuentes(borrador, False, hoy=HOY)
    assert faltantes == []
    entradas, _ = armar_informe.referencias(fuentes, [])
    assert entradas == [  # el encabezado «actualizado» es una fecha de modificación, no de publicación: (s. f.)
        "Superintendencia de Banca, Seguros y AFP. (s. f.-a). *Indicadores Financieros por Empresa Bancaria al 31 de "
        "diciembre de 2020* (Boletín B-2401) [Conjunto de datos]. Recuperado el 5 de noviembre de 2026, de "
        "https://intranet2.sbs.gob.pe/estadistica/financiera/2020/Diciembre/B-2401-di2020.XLS",
        "Superintendencia de Banca, Seguros y AFP. (s. f.-b). *Indicadores Financieros por Empresa Bancaria al 31 de "
        "diciembre de 2024* (Boletín B-2401) [Conjunto de datos]. Recuperado el 5 de noviembre de 2026, de "
        "https://intranet2.sbs.gob.pe/estadistica/financiera/2024/Diciembre/B-2401-di2024.XLS",
    ]


def test_referencia_apa_de_los_microdatos_de_la_enaho_por_anio_y_modulo(tmp_path, monkeypatch):
    armar_informe = cargar()
    monkeypatch.setattr(armar_informe, "DATOS", tmp_path)
    con_fecha(tmp_path / "966-Modulo34.zip", 2026, 11, 2)  # los demás zip no están: sin fecha de descarga conocida
    borrador = "{{enaho.pobreza_nacional:2020}} {{enaho.pobreza_nacional}} {{enaho.pobreza_area_rural}}"
    *_, faltantes, _, fuentes = armar_informe.resolver_con_fuentes(borrador, False, hoy=HOY)
    assert faltantes == []
    entradas, _ = armar_informe.referencias(fuentes, [])
    enaho = "Instituto Nacional de Estadística e Informática. (s. f.-{}). *Encuesta Nacional de Hogares sobre Condiciones " \
            "de Vida y Pobreza {}: Módulo {}* (Código {}) [Conjunto de datos]. {}https://proyectos.inei.gob.pe/iinei/" \
            "srienaho/descarga/STATA/{}-Modulo{}.zip"
    miembros, sumarias = "02, Características de los miembros del hogar", "34, Sumarias (variables calculadas)"
    assert entradas[:4] == [
        enaho.format("a", 2020, miembros, 737, "", 737, "02"),
        enaho.format("b", 2020, sumarias, 737, "", 737, "34"),
        enaho.format("c", 2024, miembros, 966, "", 966, "02"),
        enaho.format("d", 2024, sumarias, 966, "Recuperado el 2 de noviembre de 2026, de ", 966, "34"),
    ]
    assert entradas[4].startswith("Instituto Nacional de Estadística e Informática. (2025). *Perú: Evolución")
    assert len(entradas) == 5


def test_referencia_apa_de_los_limites_del_ign_solo_si_hay_mapa(tmp_path, monkeypatch):
    armar_informe = cargar()
    monkeypatch.setattr(armar_informe, "DATOS", tmp_path)
    con_fecha(tmp_path / "per_admin_boundaries.geojson.zip", 2026, 11, 5)
    entradas, _ = armar_informe.referencias({}, ["../figuras/pobreza_por_area.png", "../mapas/pobreza_departamento.png"])
    assert entradas == [
        "Instituto Geográfico Nacional. (2020). *Peru - Subnational administrative boundaries* (Versión v01) "
        "[Conjunto de datos]. OCHA Field Information Services Section; Humanitarian Data Exchange. Recuperado el 5 de "
        "noviembre de 2026, de https://data.humdata.org/dataset/cod-ab-per"]
    assert armar_informe.referencias({}, ["../figuras/pobreza_por_area.png"]) == ([], [])


def git(repo, *args):
    return subprocess.run(["git", "-c", "user.name=Prueba", "-c", "user.email=prueba@example.com", "-c",
                           "commit.gpgsign=false", *args], cwd=repo, capture_output=True, text=True, check=True).stdout


def test_sello_de_commit_advierte_cambios_sin_commitear(tmp_path):
    armar_informe = cargar()
    for carpeta in ("salidas", "informes"):
        (tmp_path / carpeta).mkdir()
    (tmp_path / "salidas" / "indicadores.csv").write_text("a\n", encoding="utf-8")
    (tmp_path / "informes" / "informe_final.md").write_text("v1\n", encoding="utf-8")
    git(tmp_path, "init", "-q")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "--no-verify", "-m", "base")
    sha = git(tmp_path, "rev-parse", "--short", "HEAD").strip()
    borrador = tmp_path / "informes" / "borrador.md"
    assert armar_informe.sello_commit(tmp_path) == f"el commit `{sha}`"

    (tmp_path / "informes" / "informe_final.md").write_text("v2\n", encoding="utf-8")  # la salida no cuenta
    assert armar_informe.sello_commit(tmp_path) == f"el commit `{sha}`"

    borrador.write_text("borrador nuevo\n", encoding="utf-8")  # un borrador sin commitear sí alimenta el informe
    assert "con cambios sin commitear en 1 archivo" in armar_informe.sello_commit(tmp_path, borrador)

    (tmp_path / "salidas" / "indicadores.csv").write_text("b\n", encoding="utf-8")
    sello = armar_informe.sello_commit(tmp_path)
    assert sello.startswith(f"el commit `{sha}`, con cambios sin commitear en 1 archivo")
    assert "no reproduce" in sello


def test_resuelve_herramientas_del_bcrp_por_mcp(api):
    armar_informe = cargar()
    api.respuestas = [periodos(("Ene.2024", "3.0"), ("Jun.2024", "2.3"), ("Dic.2024", "1.97"))]
    marcador = "{{bcrp.resumen(codigo=PN01273PM, desde=2024-01, hasta=2024-12).ultimo.valor|2}}"
    reemplazos, traza, faltantes, _ = armar_informe.resolver(f"Inflación: {marcador} %.", False)
    assert faltantes == []
    assert reemplazos[marcador] == "1.97"
    assert traza[0][2].startswith("https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01273PM/json/2024-1/")
