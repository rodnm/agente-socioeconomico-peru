"""Baja a datos/ los módulos 34 y 02 de la ENAHO (2020 a 2024)."""

import argparse
import os
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[4]
DATOS = RAIZ / "datos"

URL_INEI = "https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA"
MODULOS = ("34", "02")
CODIGOS_INEI = {
    2020: 737,
    2021: 759,
    2022: 784,
    2023: 906,
    2024: 966,
}

INTENTOS = 3
PAUSA_SEGUNDOS = 5
TIEMPO_LIMITE_SEGUNDOS = 300


def zip_valido(ruta: Path) -> bool:
    if not ruta.is_file() or ruta.stat().st_size == 0:
        return False
    try:
        with zipfile.ZipFile(ruta) as archivo:
            return archivo.testzip() is None and len(archivo.namelist()) > 0
    except zipfile.BadZipFile:
        return False


def descargar(url: str, destino: Path, es_valido) -> None:
    """Baja url a destino. Solo reemplaza destino cuando el archivo nuevo es válido."""
    if es_valido(destino):
        print(f"Ya estaba y es válido: {destino.name}")
        return

    temporal = destino.with_name(destino.name + ".part")
    pedido = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    ultimo_error = "el archivo bajado no es válido"

    for intento in range(1, INTENTOS + 1):
        print(f"Bajando {destino.name} (intento {intento} de {INTENTOS})")
        try:
            with urllib.request.urlopen(pedido, timeout=TIEMPO_LIMITE_SEGUNDOS) as respuesta:
                temporal.write_bytes(respuesta.read())
            if es_valido(temporal):
                os.replace(temporal, destino)
                print(f"Listo: {destino.name} ({destino.stat().st_size:,} bytes)")
                return
            ultimo_error = "el archivo bajado no es válido"
        except OSError as error:
            ultimo_error = str(error)
        temporal.unlink(missing_ok=True)
        if intento < INTENTOS:
            time.sleep(PAUSA_SEGUNDOS)

    sys.exit(f"No se pudo bajar {url}: {ultimo_error}")


def bajar_anio(anio: int) -> None:
    if anio not in CODIGOS_INEI:
        sys.exit(f"Año {anio} no soportado. Los años disponibles son: {list(CODIGOS_INEI.keys())}.")
    codigo = CODIGOS_INEI[anio]
    DATOS.mkdir(exist_ok=True)
    for modulo in MODULOS:
        nombre = f"{codigo}-Modulo{modulo}.zip"
        descargar(f"{URL_INEI}/{nombre}", DATOS / nombre, zip_valido)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    # Sin año, la skill activada sola pasa --anio vacío: const evita que eso falle.
    parser.add_argument("--anio", nargs="?", type=int, const=2024, default=2024,
                        help="Año de la ENAHO a descargar (2020 a 2024); sin valor, 2024")
    parser.add_argument("--todos", action="store_true", help="Descarga todos los años disponibles (2020 a 2024)")
    args = parser.parse_args()

    if args.todos:
        for anio in sorted(CODIGOS_INEI.keys()):
            bajar_anio(anio)
    else:
        bajar_anio(args.anio)


if __name__ == "__main__":
    main()
