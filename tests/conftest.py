"""Un BCRP simulado, compartido por las pruebas que no deben depender de la red."""
import httpx
import pytest

import server

CATALOGO_FALSO = (
    "Código de serie;Categoría de serie;Grupo de serie;Nombre de serie;Frecuencia;Fecha de actualización;"
    "Fecha de inicio\n"
    "PN01270PM;Precios;Índice de precios Lima Metropolitana;IPC (índice 2009 = 100) (descontinuada);Mensual;"
    "2022-04-07;Ene.1949\n"
    "PN38705PM;Precios;Índice de precios Lima Metropolitana;IPC (índice Dic.2021 = 100);Mensual;2026-10-01;Ene.1991\n"
    "PN01271PM;Precios;Índice de precios Lima Metropolitana;IPC (var% mensual);Mensual;2026-10-01;Ene.1950\n"
    "PN01273PM;Precios;Índice de precios Lima Metropolitana;IPC (var% 12 meses);Mensual;2026-10-01;Ene.1950\n"
    "PD04638PD;Tipo de cambio;Tipo de cambio nominal;Interbancario venta;Diaria;2026-10-01;01.Ene.97\n"
    "PN02526AQ;PBI;PBI trimestral;PBI (var%);Trimestral;2026-08-01;T1.80\n"
    "PM04863AA;PBI;PBI anual;PBI (var%);Anual;2026-05-01;1951\n"
)
HTML = "<!DOCTYPE html><html><head><title>Pardon Our Interruption</title></head></html>"


def periodos(*pares):
    """Una respuesta de la API con los periodos y valores dados, como texto."""
    return {"config": {}, "periods": [{"name": n, "values": [v]} for n, v in pares]}


@pytest.fixture
def api(tmp_path, monkeypatch):
    """Un BCRP simulado: cada URL pedida se anota y se responde con lo que la prueba ponga en `respuestas`."""
    (tmp_path / "catalogo.csv").write_text(CATALOGO_FALSO, encoding="utf-8")
    monkeypatch.setattr(server, "CATALOGO", tmp_path / "catalogo.csv")
    monkeypatch.setattr(server, "CACHE", tmp_path / "cache")
    monkeypatch.setattr(server, "FIGURAS", tmp_path / "figuras")
    monkeypatch.setattr(server, "RAIZ", tmp_path)
    monkeypatch.setattr(server, "ESPERAS", (0, 0, 0))
    server.catalogo.cache_clear()

    class Falsa:
        def __init__(self):
            self.pedidas: list[str] = []
            self.respuestas: list = []  # se consumen en orden; la última se repite

        def get(self, url, **_):
            self.pedidas.append(url)
            cuerpo = self.respuestas.pop(0) if len(self.respuestas) > 1 else self.respuestas[0]
            texto = cuerpo if isinstance(cuerpo, str) else None
            return httpx.Response(200, request=httpx.Request("GET", url), text=texto,
                                  json=None if texto else cuerpo)

    falsa = Falsa()
    monkeypatch.setattr(server.httpx, "get", falsa.get)
    yield falsa
    server.catalogo.cache_clear()
