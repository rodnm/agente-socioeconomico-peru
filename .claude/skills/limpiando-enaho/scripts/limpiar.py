"""Une los módulos 34 y 02 de la ENAHO (2020 a 2024) en una base de personas, la valida y calcula sus indicadores."""

import argparse
import io
import re
import sys
import zipfile
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[4]
DATOS = RAIZ / "datos"
SALIDAS = RAIZ / "salidas"
REFERENCIA_INEI = RAIZ / "referencias" / "inei_pobreza_2024.csv"

ANIO = 2024
CODIGOS_INEI = {
    2020: 737,
    2021: 759,
    2022: 784,
    2023: 906,
    2024: 966,
}

LLAVES_HOGAR = ["conglome", "vivienda", "hogar"]
LLAVES_PERSONA = LLAVES_HOGAR + ["codperso"]

COLUMNAS_SUMARIA = LLAVES_HOGAR + [
    "anio", "ubigeo", "dominio", "estrato", "pobreza", "mieperho", "factor07",
]
COLUMNAS_PERSONAS = LLAVES_PERSONA + ["p203", "p204", "p205", "p206", "p207", "p208a", "facpob07"]

# Largo fijo de cada código en la ENAHO. Si es menor, se perdieron ceros a la izquierda.
LARGO_CODIGOS = {"conglome": 6, "vivienda": 3, "hogar": 2, "codperso": 2, "ubigeo": 6}

# Metas oficiales transcritas del Informe Técnico del INEI (2025):
# Cuadro 3.1 (p. 64), Cuadro 3.4 (p. 72) y Anexo Cuadro 3.1 (p. 220).
METAS_HISTORICAS = {
    2020: {
        "nacional": 30.1, "urbana": 26.0, "rural": 45.7, "extrema": 5.1,
        "lima_metropolitana_provincia": 26.6, "lima_provincias": 26.5,
        "hogares": 34_490, "filas_mod02": 126_831, "residentes": 118_810,
        "cuadro_pobreza": "Cuadro 3.1", "pagina_pobreza": 64,
        "cuadro_extrema": "Cuadro 3.4", "pagina_extrema": 72,
        "cuadro_lima": "Anexo Cuadro 3.1", "pagina_lima": 220,
    },
    2021: {
        "nacional": 25.9, "urbana": 22.3, "rural": 39.7, "extrema": 4.1,
        "lima_metropolitana_provincia": 24.4, "lima_provincias": 26.4,
        "hogares": 34_245, "filas_mod02": 121_067, "residentes": 113_057,
        "cuadro_pobreza": "Cuadro 3.1", "pagina_pobreza": 64,
        "cuadro_extrema": "Cuadro 3.4", "pagina_extrema": 72,
        "cuadro_lima": "Anexo Cuadro 3.1", "pagina_lima": 220,
    },
    2022: {
        "nacional": 27.5, "urbana": 24.1, "rural": 41.1, "extrema": 5.0,
        "lima_metropolitana_provincia": 26.9, "lima_provincias": 22.9,
        "hogares": 34_213, "filas_mod02": 121_253, "residentes": 113_142,
        "cuadro_pobreza": "Cuadro 3.1", "pagina_pobreza": 64,
        "cuadro_extrema": "Cuadro 3.4", "pagina_extrema": 72,
        "cuadro_lima": "Anexo Cuadro 3.1", "pagina_lima": 220,
    },
    2023: {
        "nacional": 29.0, "urbana": 26.4, "rural": 39.8, "extrema": 5.7,
        "lima_metropolitana_provincia": 28.1, "lima_provincias": 26.1,
        "hogares": 33_886, "filas_mod02": 119_747, "residentes": 110_792,
        "cuadro_pobreza": "Cuadro 3.1", "pagina_pobreza": 64,
        "cuadro_extrema": "Cuadro 3.4", "pagina_extrema": 72,
        "cuadro_lima": "Anexo Cuadro 3.1", "pagina_lima": 220,
    },
    2024: {
        "nacional": 27.6, "urbana": 24.8, "rural": 39.3, "extrema": 5.5,
        "lima_metropolitana": 28.2, "lima_metropolitana_provincia": 27.6, "lima_provincias": 21.7,
        "hogares": 33_691, "filas_mod02": 117_721, "residentes": 108_664,
        "cuadro_pobreza": "Cuadro III.1", "pagina_pobreza": 219,
        "cuadro_extrema": "Cuadro III.4", "pagina_extrema": 72,
        "cuadro_lima": "Cuadro III.1", "pagina_lima": 220,
    },
}

TOLERANCIA = 0.1

# Nombres para mostrar; la unión con el mapa usa siempre el código, nunca el nombre.
DEPARTAMENTOS = {
    "01": "Amazonas", "02": "Áncash", "03": "Apurímac", "04": "Arequipa", "05": "Ayacucho", "06": "Cajamarca",
    "07": "Callao", "08": "Cusco", "09": "Huancavelica", "10": "Huánuco", "11": "Ica", "12": "Junín",
    "13": "La Libertad", "14": "Lambayeque", "15": "Lima", "16": "Loreto", "17": "Madre de Dios", "18": "Moquegua",
    "19": "Pasco", "20": "Piura", "21": "Puno", "22": "San Martín", "23": "Tacna", "24": "Tumbes", "25": "Ucayali",
}
GRUPOS_EDAD = [0, 15, 30, 45, 60, 200]
NOMBRES_EDAD = ["0 a 14 años", "15 a 29 años", "30 a 44 años", "45 a 59 años", "60 años y más"]
PESO_HOGAR = "factor07 × mieperho (por hogar)"
PESO_PERSONA = "facpob07 (por persona)"


def leer_dta(ruta_zip: Path, patron: str) -> pd.DataFrame:
    """Lee el único .dta del zip que coincide con patron, sin convertir códigos en categorías."""
    with zipfile.ZipFile(ruta_zip) as archivo:
        miembros = [n for n in archivo.namelist() if re.search(patron, n, re.IGNORECASE)]
        if len(miembros) != 1:
            sys.exit(f"Se esperaba un archivo {patron} en {ruta_zip.name}; hay {miembros}.")
        contenido = io.BytesIO(archivo.read(miembros[0]))
    return pd.read_stata(contenido, convert_categoricals=False)


def normalizar_columnas(tabla: pd.DataFrame) -> pd.DataFrame:
    """Pasa los nombres a minúscula. El del año llega con el byte de la Ñ roto: se ubica por patrón."""
    tabla = tabla.rename(columns=str.lower)
    return tabla.rename(columns=lambda c: "anio" if re.fullmatch(r"a[^a-z]{1,2}o", c) else c)


def llaves_a_texto(tabla: pd.DataFrame, columnas: list[str]) -> pd.DataFrame:
    return tabla.assign(**{c: tabla[c].astype(str).str.strip() for c in columnas})


def tasa(condicion: pd.Series, peso: pd.Series) -> float:
    return 100 * (condicion * peso).sum() / peso.sum()


class Validacion:
    """Junta las comprobaciones para escribirlas todas antes de decidir si se detiene."""

    def __init__(self) -> None:
        self.lineas: list[str] = []
        self.fallos = 0

    def registrar(self, nombre: str, correcto: bool, detalle: str) -> None:
        self.lineas.append(f"{'OK   ' if correcto else 'FALLA'} {nombre}: {detalle}")
        self.fallos += not correcto

    def igual(self, nombre: str, valor: int, esperado: int, nota: str = "") -> None:
        desc = f"{valor:,} (conteo en microdatos {nota})" if nota else f"{valor:,} (esperado {esperado:,})"
        self.registrar(nombre, valor == esperado, desc)

    def cifra(self, nombre: str, valor: float, esperado: float, ic_inf: float | None = None,
              ic_sup: float | None = None, cuadro: str = "", pagina: int | str = "", nota: str = "",
              tolerancia: float = TOLERANCIA) -> None:
        correcto = abs(valor - esperado) <= tolerancia
        meta_str = f"meta INEI {esperado} ± {tolerancia} %"
        if ic_inf is not None and ic_sup is not None and not pd.isna(ic_inf):
            meta_str += f", IC 95%: [{ic_inf:.1f}, {ic_sup:.1f}]"
        if cuadro and pagina and not pd.isna(pagina):
            meta_str += f", {cuadro}, p. {pagina}"
        if nota and not pd.isna(nota):
            meta_str += f" ({nota})"
        self.registrar(nombre, correcto, f"{valor:.2f} % ({meta_str})")


def validar(sumaria: pd.DataFrame, modulo02: pd.DataFrame, personas: pd.DataFrame,
            base: pd.DataFrame, anio: int) -> Validacion:
    v = Validacion()
    metas = METAS_HISTORICAS.get(anio, {})
    hogares_esperados = metas.get("hogares", len(sumaria))
    filas_mod02_esperadas = metas.get("filas_mod02", len(modulo02))
    residentes_esperados = metas.get("residentes", len(personas))

    v.igual("Hogares en la sumaria", len(sumaria), hogares_esperados, f"sumaria-{anio}.dta")
    v.igual("Filas del módulo 02", len(modulo02), filas_mod02_esperadas, f"enaho01-{anio}-200.dta")
    v.igual("Residentes habituales", len(personas), residentes_esperados, f"enaho01-{anio}-200.dta con filtro habitual")
    v.igual("Llaves de hogar repetidas", int(sumaria.duplicated(LLAVES_HOGAR).sum()), 0)
    v.igual("Llaves de persona repetidas", int(personas.duplicated(LLAVES_PERSONA).sum()), 0)
    v.igual("Filas de la base tras la unión", len(base), len(personas))
    v.igual("Personas sin hogar en la sumaria", int(base["pobreza"].isna().sum()), 0)
    for columna, largo in LARGO_CODIGOS.items():
        v.igual(f"Códigos {columna} sin {largo} caracteres", int((base[columna].str.len() != largo).sum()), 0)

    # La pobreza oficial se calcula por hogar: factor07 × mieperho expande cada hogar a sus personas.
    hogares = base.drop_duplicates(LLAVES_HOGAR)
    v.igual("Hogares en la base", len(hogares), hogares_esperados, "base de hogares")
    peso = hogares["peso_hogar"]

    pob_nac = metas.get("nacional", 27.6)
    cuadro_pob = metas.get("cuadro_pobreza", "Cuadro 3.1")
    pag_pob = metas.get("pagina_pobreza", 64)
    v.cifra("Pobreza nacional (hogares, factor07 × mieperho)", tasa(hogares["pobre"], peso), pob_nac,
            cuadro=cuadro_pob, pagina=pag_pob)
    tol_facpob = 0.1 if anio == 2024 else 0.2
    v.cifra("Pobreza nacional (personas, facpob07)", tasa(base["pobre"], base["facpob07"]), pob_nac,
            cuadro=cuadro_pob, pagina=pag_pob, nota="ponderador facpob07", tolerancia=tol_facpob)

    pob_ext = metas.get("extrema", 5.5)
    cuadro_ext = metas.get("cuadro_extrema", "Cuadro 3.4")
    pag_ext = metas.get("pagina_extrema", 72)
    v.cifra("Pobreza extrema", tasa(hogares["pobreza"] == 1, peso), pob_ext,
            cuadro=cuadro_ext, pagina=pag_ext)

    pob_urb = metas.get("urbana", 24.8)
    v.cifra("Pobreza urbana", tasa(hogares["pobre"][hogares["urbano"]], peso[hogares["urbano"]]), pob_urb,
            cuadro=cuadro_pob, pagina=pag_pob)

    pob_rur = metas.get("rural", 39.3)
    v.cifra("Pobreza rural", tasa(hogares["pobre"][~hogares["urbano"]], peso[~hogares["urbano"]]), pob_rur,
            cuadro=cuadro_pob, pagina=pag_pob)

    cuadro_lima = metas.get("cuadro_lima", "Anexo Cuadro 3.1")
    pag_lima = metas.get("pagina_lima", 220)
    if "lima_metropolitana" in metas:
        lima_callao = hogares["dominio"] == 8
        v.cifra("Pobreza en Lima Metropolitana con Callao", tasa(hogares["pobre"][lima_callao], peso[lima_callao]),
                metas["lima_metropolitana"], cuadro="Cuadro III.1", pagina=219, nota="dominio 8")

    es_1501 = hogares["ubigeo"].str.startswith("1501")
    if "lima_metropolitana_provincia" in metas:
        v.cifra("Pobreza en Lima Metropolitana (provincia 1501)", tasa(hogares["pobre"][es_1501], peso[es_1501]),
                metas["lima_metropolitana_provincia"], cuadro=cuadro_lima, pagina=pag_lima)

    es_15_resto = (hogares["departamento"] == "15") & (~es_1501)
    if "lima_provincias" in metas:
        v.cifra("Pobreza en Lima provincias", tasa(hogares["pobre"][es_15_resto], peso[es_15_resto]),
                metas["lima_provincias"], cuadro=cuadro_lima, pagina=pag_lima)

    if anio == 2024 and REFERENCIA_INEI.is_file():
        ref = pd.read_csv(REFERENCIA_INEI, dtype={"ccdd": str})
        for fila in ref.itertuples():
            if not fila.ccdd or pd.isna(fila.ccdd):
                continue
            if fila.ccdd in ("1501", "15_resto"):
                continue  # ya evaluadas arriba
            elif fila.ccdd == "15":
                de_aqui = hogares["departamento"] == "15"
                nombre_val = "Pobreza en LIMA (departamento completo, consigna)"
            else:
                de_aqui = hogares["departamento"] == fila.ccdd
                nombre_val = f"Pobreza en {fila.ambito}"

            if de_aqui.any():
                ic_inf = float(fila.ic_inf) if not pd.isna(fila.ic_inf) else None
                ic_sup = float(fila.ic_sup) if not pd.isna(fila.ic_sup) else None
                cuadro = str(fila.cuadro) if not pd.isna(fila.cuadro) else ""
                pagina = str(int(float(fila.pagina))) if str(fila.pagina).replace(".", "", 1).isdigit() else str(fila.pagina)
                nota = str(fila.nota) if not pd.isna(fila.nota) else ""
                v.cifra(nombre_val, tasa(hogares["pobre"][de_aqui], peso[de_aqui]), float(fila.valor),
                        ic_inf, ic_sup, cuadro, pagina, nota)
            else:
                v.registrar(nombre_val, False, "sin hogares en la base")

    v.igual("Departamentos con hogares", hogares["departamento"].nunique(), len(DEPARTAMENTOS), "consigna de 25 departamentos")
    return v


def indicadores(base: pd.DataFrame, anio: int) -> pd.DataFrame:
    """Los indicadores ponderados que leen los gráficos, el mapa, el informe y el dashboard.

    Las tasas de pobreza nacionales, por área y por departamento van por hogar, como la cifra oficial; las de sexo
    y edad, por persona, porque son atributos de cada persona. n_muestral cuenta los registros detrás de cada cifra.
    """
    hogares = base.drop_duplicates(LLAVES_HOGAR)
    filas = []

    def agregar(id_, indicador, grupo, valor, unidad, ponderador, n):
        filas.append({"anio": int(anio), "id": id_, "indicador": indicador, "grupo": grupo,
                      "valor": round(float(valor), 4), "unidad": unidad, "ponderador": ponderador,
                      "n_muestral": int(n)})

    def pobreza(id_, indicador, grupo, tabla, filtro, peso_col, ponderador, condicion="pobre"):
        t = tabla[filtro]
        cumple = t["pobreza"] == 1 if condicion == "extrema" else t["pobre"]
        agregar(id_, indicador, grupo, tasa(cumple, t[peso_col]), "% de personas", ponderador, len(t))

    todos_h, todos_p = pd.Series(True, index=hogares.index), pd.Series(True, index=base.index)
    pobreza("pobreza_nacional", "Pobreza monetaria", "Nacional", hogares, todos_h, "peso_hogar", PESO_HOGAR)
    pobreza("pobreza_nacional_personas", "Pobreza monetaria", "Nacional", base, todos_p, "facpob07", PESO_PERSONA)
    pobreza("pobreza_extrema", "Pobreza extrema", "Nacional", hogares, todos_h, "peso_hogar", PESO_HOGAR, "extrema")
    pobreza("pobreza_area_urbana", "Pobreza monetaria", "Urbana", hogares, hogares["urbano"], "peso_hogar", PESO_HOGAR)
    pobreza("pobreza_area_rural", "Pobreza monetaria", "Rural", hogares, ~hogares["urbano"], "peso_hogar", PESO_HOGAR)
    pobreza("pobreza_lima_metropolitana", "Pobreza monetaria", "Lima Metropolitana", hogares,
            hogares["dominio"] == 8, "peso_hogar", PESO_HOGAR)
    pobreza("pobreza_lima_metropolitana_provincia", "Pobreza monetaria", "Lima Metropolitana (provincia)", hogares,
            hogares["ubigeo"].str.startswith("1501"), "peso_hogar", PESO_HOGAR)
    pobreza("pobreza_lima_provincias", "Pobreza monetaria", "Lima provincias", hogares,
            (hogares["departamento"] == "15") & (~hogares["ubigeo"].str.startswith("1501")), "peso_hogar", PESO_HOGAR)
    for codigo, nombre in DEPARTAMENTOS.items():
        pobreza(f"pobreza_dep_{codigo}", "Pobreza monetaria", nombre, hogares, hogares["departamento"] == codigo,
                "peso_hogar", PESO_HOGAR)
    for codigo, nombre in {1: "Hombres", 2: "Mujeres"}.items():
        pobreza(f"pobreza_sexo_{nombre.lower()}", "Pobreza monetaria", nombre, base, base["p207"] == codigo,
                "facpob07", PESO_PERSONA)
    edades = pd.cut(base["p208a"], bins=GRUPOS_EDAD, right=False, labels=NOMBRES_EDAD)
    for nombre in NOMBRES_EDAD:
        id_ = "pobreza_edad_" + "_".join(nombre.replace(" años", "").replace(" y más", "_mas").split(" a "))
        pobreza(id_, "Pobreza monetaria", nombre, base, edades == nombre, "facpob07", PESO_PERSONA)
    agregar("residentes_habituales", "Residentes habituales", "Nacional", len(base), "personas en la muestra",
            "sin ponderar", len(base))
    agregar("hogares", "Hogares", "Nacional", len(hogares), "hogares en la muestra", "sin ponderar", len(hogares))
    agregar("poblacion_expandida", "Población estimada", "Nacional", base["facpob07"].sum(), "personas",
            PESO_PERSONA, len(base))
    agregar("departamentos", "Unidades territoriales", "Nacional", hogares["departamento"].nunique(),
            "departamentos", "sin ponderar", len(hogares))
    return pd.DataFrame(filas).assign(fuente=f"INEI, ENAHO {anio}, módulos 34 y 02; limpiando-enaho/limpiar.py")


def procesar_un_anio(anio: int) -> tuple[pd.DataFrame, pd.DataFrame, Validacion]:
    """Carga, une, valida y calcula indicadores para un año específico."""
    codigo_inei = CODIGOS_INEI[anio]
    zip_sumaria = DATOS / f"{codigo_inei}-Modulo34.zip"
    zip_personas = DATOS / f"{codigo_inei}-Modulo02.zip"
    for ruta in (zip_sumaria, zip_personas):
        if not ruta.is_file():
            sys.exit(f"Falta {ruta.name} en datos/. Bájalo con la skill descargando-enaho.")

    # 1. Leer y 2. normalizar.
    sumaria = normalizar_columnas(leer_dta(zip_sumaria, rf"(^|/)sumaria-{anio}\.dta$"))[COLUMNAS_SUMARIA]
    modulo02 = normalizar_columnas(leer_dta(zip_personas, rf"(^|/)enaho01-{anio}-200\.dta$"))[COLUMNAS_PERSONAS]
    sumaria = llaves_a_texto(sumaria, LLAVES_HOGAR + ["ubigeo"])
    modulo02 = llaves_a_texto(modulo02, LLAVES_PERSONA)

    # 3. Filtrar a los residentes habituales.
    es_residente = ((modulo02["p204"] == 1) & (modulo02["p205"] == 2)) | (
        (modulo02["p204"] == 2) & (modulo02["p206"] == 1)
    )
    personas = modulo02[es_residente]

    # 4. Unir.
    base = personas.merge(sumaria, on=LLAVES_HOGAR, how="left", validate="m:1")

    # 5. Construir.
    base["departamento"] = base["ubigeo"].str[:2]
    base["departamento_nombre"] = base["departamento"].map(DEPARTAMENTOS)
    base["urbano"] = base["estrato"] <= 5
    base["pobre"] = base["pobreza"] <= 2
    base["peso_hogar"] = base["factor07"] * base["mieperho"]

    # 6. Validar.
    resultado = validar(sumaria, modulo02, personas, base, anio)
    return base, indicadores(base, anio), resultado


def actualizar_indicadores_csv(nuevos_indicadores: pd.DataFrame) -> None:
    SALIDAS.mkdir(exist_ok=True)
    ruta = SALIDAS / "indicadores.csv"
    if ruta.is_file():
        existente = pd.read_csv(ruta)
        if "anio" in existente.columns:
            anios_nuevos = set(nuevos_indicadores["anio"])
            existente = existente[~existente["anio"].isin(anios_nuevos)]
            consolidado = pd.concat([existente, nuevos_indicadores], ignore_index=True)
            consolidado = consolidado.sort_values(["anio", "id"]).reset_index(drop=True)
        else:
            consolidado = nuevos_indicadores
    else:
        consolidado = nuevos_indicadores
    consolidado.to_csv(ruta, index=False, encoding="utf-8")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    # Sin año, la skill activada sola pasa --anio vacío: const evita que eso falle.
    parser.add_argument("--anio", nargs="?", type=int, const=ANIO, default=ANIO)
    parser.add_argument("--todos", action="store_true", help="Procesa todos los años disponibles (2020 a 2024)")
    args = parser.parse_args()

    if args.todos:
        anios_a_procesar = sorted(CODIGOS_INEI.keys())
    else:
        if args.anio not in CODIGOS_INEI:
            sys.exit(f"Año {args.anio} no soportado. Los años disponibles son: {sorted(CODIGOS_INEI.keys())}.")
        anios_a_procesar = [args.anio]

    SALIDAS.mkdir(exist_ok=True)
    ruta_validacion = SALIDAS / "validacion.txt"

    todas_tablas = []
    lineas_validacion = []
    total_fallos = 0

    for anio in anios_a_procesar:
        base, tabla_ind, valid = procesar_un_anio(anio)
        lineas_validacion.append(f"Validación de la ENAHO {anio} contra las cifras oficiales del INEI (Informe Técnico 2025)\n")
        lineas_validacion.extend(valid.lineas)
        lineas_validacion.append("")
        total_fallos += valid.fallos

        if valid.fallos:
            # Escribir validacion.txt antes de salir para diagnóstico
            ruta_validacion.write_text("\n".join(lineas_validacion) + "\n", encoding="utf-8")
            sys.exit(f"{valid.fallos} comprobaciones fallaron en {anio}. Revisa salidas/validacion.txt.")

        # Guardar la base parquet del año
        base.to_parquet(SALIDAS / f"personas_{anio}.parquet", index=False)
        todas_tablas.append(tabla_ind)
        nacional = tabla_ind.set_index("id").loc["pobreza_nacional", "valor"]
        print(f"Año {anio} listo: {len(base):,} personas en salidas/personas_{anio}.parquet; pobreza nacional {nacional:.2f} %.")

    # Guardar validacion.txt
    ruta_validacion.write_text("\n".join(lineas_validacion) + "\n", encoding="utf-8")

    # Actualizar o escribir salidas/indicadores.csv
    actualizar_indicadores_csv(pd.concat(todas_tablas, ignore_index=True))
    print(f"salidas/indicadores.csv actualizado con éxito para años: {anios_a_procesar}.")


if __name__ == "__main__":
    main()
