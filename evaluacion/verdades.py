"""Calcula las respuestas esperadas de las preguntas del BCRP sin pasar por el servidor MCP.

    uv run evaluacion/verdades.py           # imprime las verdades y las guarda en evaluacion/verdades_bcrp.json

Es un cálculo independiente: pide los datos crudos a la API pública del BCRP con httpx y los resume con pandas, sin
importar mcp/server.py. Así, si el servidor tuviera un error de fechas o de periodos, la evaluación lo detectaría en
lugar de heredarlo. Las verdades de la ENAHO vienen de cifras publicadas por el INEI y de la referencia de la
sesión 16; están en preguntas.csv con su fuente.
"""
import json
import sys
import time
from pathlib import Path

import httpx
import pandas as pd

AQUI = Path(__file__).parent
API = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"
# id de la pregunta → (código, desde, hasta en el formato de la API, operación sobre los valores)
CONSULTAS = {
    "b1": ("PN01273PM", "2024-12", "2024-12", "ultimo"),      # inflación a 12 meses de Lima, diciembre de 2024
    "b2": ("PD04638PD", "2024-01-01", "2024-12-31", "promedio"),  # tipo de cambio interbancario venta, promedio 2024
    "b3": ("PN01271PM", "2025-3", "2025-3", "ultimo"),          # variación mensual del IPC de Lima, marzo de 2025
    "b4": ("PN01273PM", "2026-9", "2026-9", "ultimo"),          # inflación a 12 meses de Lima, setiembre de 2026
    "m1": ("PN01273PM", "2024-12", "2024-12", "ultimo"),      # parte BCRP de la pregunta mixta 1
    "m2": ("PD04638PD", "2024-01-01", "2024-12-31", "promedio"),  # parte BCRP de la pregunta mixta 2
}


def valores(codigo, desde, hasta):
    url = f"{API}/{codigo}/json/{desde}/{hasta}"
    for espera in (0, 3, 10, 30):
        time.sleep(espera)
        r = httpx.get(url, timeout=120, follow_redirects=True)
        try:
            periodos = r.json()["periods"]
        except ValueError:
            continue  # página HTML: anti-bots o límite de consultas
        return url, [float(p["values"][0]) for p in periodos if p["values"][0] not in ("n.d.", "")]
    sys.exit(f"El BCRP no respondió con datos para {url}; no se calcula ninguna verdad.")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    verdades = {}
    for id_, (codigo, desde, hasta, operacion) in CONSULTAS.items():
        url, datos = valores(codigo, desde, hasta)
        serie = pd.Series(datos)
        verdades[id_] = {"codigo": codigo, "url": url, "n": len(serie), "operacion": operacion,
                         "valor": round(float(serie.iloc[-1] if operacion == "ultimo" else serie.mean()), 4)}
        print(f"{id_}: {verdades[id_]['valor']} ({codigo}, {operacion} de {len(serie)} datos) {url}")
    (AQUI / "verdades_bcrp.json").write_text(json.dumps(verdades, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
