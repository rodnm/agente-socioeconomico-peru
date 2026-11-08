"""Procesa y simplifica las capas cartográficas oficiales del IGN (vía OCHA HDX COD-AB).

Genera:
  - referencias/limites_departamentales_ign.geojson (25 departamentos, con FIRST_IDDP como alias de ccdd)
  - referencias/limites_ambitos_ign.geojson (26 ámbitos territoriales: 24 departamentos, Callao,
    Lima Metropolitana provincia 1501 y Lima provincias)
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import geopandas as gpd
from shapely.geometry import shape
from shapely.ops import unary_union

RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "datos"
REFERENCIAS = RAIZ / "referencias"
DESTINO_DEP = REFERENCIAS / "limites_departamentales_ign.geojson"
DESTINO_AMBITOS = REFERENCIAS / "limites_ambitos_ign.geojson"

URL_HDX = (
    "https://data.humdata.org/dataset/54fc7f4d-f4c0-4892-91f6-2fe7c1ecf363/"
    "resource/63647792-0951-40d2-a30e-4a0e60f7a176/download/per_admin_boundaries.geojson.zip"
)
ZIP_LOCAL = DATOS / "per_admin_boundaries.geojson.zip"
TOLERANCIA_SIMPLIFICACION = 0.004


def sha256_archivo(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        while bloque := f.read(65536):
            h.update(bloque)
    return h.hexdigest()


def obtener_zip(ruta_zip: Path | None) -> Path:
    if ruta_zip and ruta_zip.is_file():
        return ruta_zip
    if ZIP_LOCAL.is_file():
        return ZIP_LOCAL

    # Intento de descarga automática
    DATOS.mkdir(exist_ok=True)
    print(f"Descargando límites oficiales desde OCHA HDX...")
    try:
        # Intentar con curl.exe si está disponible (evita bloqueo WAF de HDX)
        res = subprocess.run(
            ["curl.exe", "-s", "-L", "-o", str(ZIP_LOCAL), URL_HDX],
            capture_output=True,
            timeout=180,
        )
        if res.returncode == 0 and ZIP_LOCAL.is_file() and ZIP_LOCAL.stat().st_size > 1000000:
            return ZIP_LOCAL
    except Exception:
        pass

    # Intentar con urllib
    try:
        pedido = urllib.request.Request(URL_HDX, headers={"User-Agent": "curl/8.4.0"})
        with urllib.request.urlopen(pedido, timeout=180) as resp:
            contenido = resp.read()
            if len(contenido) > 1000000:
                ZIP_LOCAL.write_bytes(contenido)
                return ZIP_LOCAL
    except Exception as e:
        pass

    sys.exit(
        "No se pudo descargar automáticamente el archivo de límites oficiales desde HDX.\n"
        f"Por favor descargue per_admin_boundaries.geojson.zip desde {URL_HDX} "
        f"y guárdelo en {DATOS.as_posix()}, o ejecute:\n"
        f"python scripts/preparar_limites.py --zip <ruta_al_zip>"
    )


def procesar_capas(archivo_zip: Path) -> None:
    print(f"Leyendo archivo zip: {archivo_zip.name}")
    hash_zip = sha256_archivo(archivo_zip)
    print(f"SHA-256 del zip: {hash_zip}")

    with zipfile.ZipFile(archivo_zip, "r") as z:
        archivos = z.namelist()
        if "per_admin1.geojson" not in archivos or "per_admin2.geojson" not in archivos:
            sys.exit("El archivo zip no contiene las capas per_admin1.geojson y per_admin2.geojson requeridas.")

        with z.open("per_admin1.geojson") as f1:
            data1 = json.load(f1)
        with z.open("per_admin2.geojson") as f2:
            data2 = json.load(f2)

    # 2. Capa de 26 ámbitos (H8: Lima Metropolitana provincia 1501 y Lima provincias)
    lima_metro_geom = None
    lima_provs_geoms = []
    for feat in data2["features"]:
        props = feat["properties"]
        pcode = props.get("adm2_pcode", "")
        if pcode == "PE1501":
            lima_metro_geom = shape(feat["geometry"]).simplify(TOLERANCIA_SIMPLIFICACION, preserve_topology=True)
        elif pcode.startswith("PE15"):
            lima_provs_geoms.append(shape(feat["geometry"]))

    if not lima_metro_geom or not lima_provs_geoms:
        sys.exit("Error: no se encontraron las provincias de Lima en la capa per_admin2.geojson")

    lima_provincias_geom = unary_union(lima_provs_geoms).simplify(TOLERANCIA_SIMPLIFICACION, preserve_topology=True)

    # 1. Capa de 25 departamentos
    features_25 = []
    for feat in data1["features"]:
        props = feat["properties"]
        ccdd = props["adm1_pcode"].replace("PE", "").zfill(2)
        nombre = props.get("adm1_name") or props.get("adm1_ref_name", "")
        if ccdd == "15":
            # Garantiza correspondencia geométrica exacta con la unión de ámbitos
            geom = unary_union([lima_metro_geom, lima_provincias_geom])
        else:
            geom = shape(feat["geometry"]).simplify(TOLERANCIA_SIMPLIFICACION, preserve_topology=True)
        features_25.append({
            "ccdd": ccdd,
            "FIRST_IDDP": ccdd,  # Alias de compatibilidad con la consigna del curso
            "NOMBDEP": nombre.upper(),
            "nombre": nombre,
            "geometry": geom,
        })

    gdf_25 = gpd.GeoDataFrame(features_25, crs="EPSG:4326").sort_values("ccdd").reset_index(drop=True)

    features_26 = []
    for idx, row in gdf_25.iterrows():
        if row["ccdd"] != "15":
            features_26.append({
                "codigo": row["ccdd"],
                "FIRST_IDDP": row["ccdd"],
                "nombre": row["nombre"],
                "tipo": "departamento" if row["ccdd"] != "07" else "provincia_constitucional",
                "geometry": row["geometry"],
            })
        else:
            features_26.append({
                "codigo": "1501",
                "FIRST_IDDP": "1501",
                "nombre": "Lima Metropolitana (provincia)",
                "tipo": "provincia",
                "geometry": lima_metro_geom,
            })
            features_26.append({
                "codigo": "15_resto",
                "FIRST_IDDP": "15P",
                "nombre": "Lima provincias",
                "tipo": "resto_departamento",
                "geometry": lima_provincias_geom,
            })

    gdf_26 = gpd.GeoDataFrame(features_26, crs="EPSG:4326").reset_index(drop=True)
    if len(gdf_26) != 26:
        sys.exit(f"Error: se esperaban 26 ámbitos, hay {len(gdf_26)}")

    # Escritura de archivos GeoJSON
    REFERENCIAS.mkdir(exist_ok=True)
    DESTINO_DEP.write_text(gdf_25.to_json(drop_id=True), encoding="utf-8")
    print(f"Escrito: {DESTINO_DEP.relative_to(RAIZ).as_posix()} ({len(gdf_25)} entidades, {DESTINO_DEP.stat().st_size:,} bytes)")

    DESTINO_AMBITOS.write_text(gdf_26.to_json(drop_id=True), encoding="utf-8")
    print(f"Escrito: {DESTINO_AMBITOS.relative_to(RAIZ).as_posix()} ({len(gdf_26)} entidades, {DESTINO_AMBITOS.stat().st_size:,} bytes)")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, default=None, help="Ruta a per_admin_boundaries.geojson.zip")
    args = parser.parse_args()

    zip_file = obtener_zip(args.zip)
    procesar_capas(zip_file)


if __name__ == "__main__":
    main()
