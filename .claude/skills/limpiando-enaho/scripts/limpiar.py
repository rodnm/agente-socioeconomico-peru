"""Une los módulos 34 y 02 de la ENAHO (2020 a 2024) en una base de personas, la valida y calcula sus indicadores."""

import argparse
import io
import re
import sys
import zipfile
from pathlib import Path
from typing import NamedTuple

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

INFORME_INEI = ("INEI (2025), Perú: Evolución de la pobreza monetaria, 2015-2024. Informe técnico; "
                "páginas impresas del PDF con SHA-256 ed964c41c963f0ac5ce11b1713680ec93519838b9db0cd8fa139e6bb922d6c73")


class Meta(NamedTuple):
    """Una cifra publicada por el INEI y el lugar del informe donde se lee."""
    valor: float
    cuadro: str
    pagina: int
    ic_inf: float | None = None
    ic_sup: float | None = None
    nota: str = ""


# Ubicación de cada meta en el informe técnico del INEI (2025), verificada contra el texto del PDF; la página
# impresa es la del visor menos 2. Los dos cuadros traen la serie 2015-2024 completa, pero el intervalo de confianza
# al 95 % y el coeficiente de variación solo se publican para 2024.
UBICACION_INEI = {
    "nacional": ("Cuadro III.1", 219),
    "urbana": ("Cuadro III.1", 219),
    "rural": ("Cuadro III.1", 219),
    "lima_metropolitana_callao": ("Cuadro III.1", 219),  # dominio 8: Lima Metropolitana y el Callao
    "lima_metropolitana": ("Cuadro III.1", 220),         # provincia 1501, «Lima Metropolitana 1/»
    "lima_provincias": ("Cuadro III.1", 220),            # resto del departamento 15, «Lima 2/»
    "extrema": ("Cuadro III.4", 223),
}

# Columnas 2020 a 2023 de esos cuadros. Las metas de 2024, con su IC y su CV, se leen de la tabla
# referencias/inei_pobreza_2024.csv, transcrita de los mismos cuadros.
METAS_INEI = {
    2020: {"nacional": 30.1, "urbana": 26.0, "rural": 45.7, "extrema": 5.1,
           "lima_metropolitana_callao": 27.5, "lima_metropolitana": 26.6, "lima_provincias": 26.5},
    2021: {"nacional": 25.9, "urbana": 22.3, "rural": 39.7, "extrema": 4.1,
           "lima_metropolitana_callao": 24.9, "lima_metropolitana": 24.4, "lima_provincias": 26.4},
    2022: {"nacional": 27.5, "urbana": 24.1, "rural": 41.1, "extrema": 5.0,
           "lima_metropolitana_callao": 27.3, "lima_metropolitana": 26.9, "lima_provincias": 22.9},
    2023: {"nacional": 29.0, "urbana": 26.4, "rural": 39.8, "extrema": 5.7,
           "lima_metropolitana_callao": 28.7, "lima_metropolitana": 28.1, "lima_provincias": 26.1},
}
# Fila de referencias/inei_pobreza_2024.csv (columna ambito) que da cada meta de 2024.
FILAS_REFERENCIA_2024 = {
    "nacional": "Nacional", "urbana": "Urbana", "rural": "Rural", "extrema": "Pobreza extrema",
    "lima_metropolitana_callao": "Lima Metropolitana con Callao", "lima_metropolitana": "Lima Metropolitana",
    "lima_provincias": "Lima provincias",
}

# Conteos de filas de los archivos .dta del INEI, leídos de los zip de cada año. No son cifras publicadas: sirven
# para detectar un archivo distinto o incompleto, o un filtro de residentes que cambió. Los 108,664 residentes
# de 2024 son, además, la cifra que pide la consigna del curso.
CONTEOS_ARCHIVOS_INEI = {
    2020: {"hogares": 34_490, "filas_mod02": 126_831, "residentes": 118_810},
    2021: {"hogares": 34_245, "filas_mod02": 121_067, "residentes": 113_057},
    2022: {"hogares": 34_213, "filas_mod02": 121_253, "residentes": 113_142},
    2023: {"hogares": 33_886, "filas_mod02": 119_747, "residentes": 110_792},
    2024: {"hogares": 33_691, "filas_mod02": 117_721, "residentes": 108_664},
}
AVISO_CONTEO = "conteo del archivo del INEI, no es una cifra publicada"

# El INEI publica las tasas con un decimal. Replicar su método con los mismos microdatos debe dar una cifra que
# redondee a la publicada; 0.1 puntos es el margen que fija la consigna para esa réplica. No es una prueba
# estadística: la incertidumbre de muestreo la dan los intervalos de confianza del INEI, que se informan en 2024.
TOLERANCIA = 0.1
# La pobreza oficial se pondera por hogar (factor07 × mieperho). La línea con facpob07, el factor de cada persona,
# es solo un contraste de sensibilidad con otro ponderador, no una réplica del método oficial. Sus diferencias
# frente a la cifra publicada, en puntos, son 0.09 (2020), 0.16 (2021), 0.02 (2022), 0.02 (2023) y 0.07 (2024):
# 2021 supera 0.1, así que el contraste usa 0.2 de 2020 a 2023; 2024 conserva el 0.1 de la consigna.
TOLERANCIA_FACPOB07 = 0.2


def tolerancia_facpob07(anio: int) -> float:
    return TOLERANCIA if anio == ANIO else TOLERANCIA_FACPOB07

# Nombres para mostrar; la unión con el mapa usa siempre el código, nunca el nombre.
DEPARTAMENTOS = {
    "01": "Amazonas", "02": "Áncash", "03": "Apurímac", "04": "Arequipa", "05": "Ayacucho", "06": "Cajamarca",
    "07": "Callao", "08": "Cusco", "09": "Huancavelica", "10": "Huánuco", "11": "Ica", "12": "Junín",
    "13": "La Libertad", "14": "Lambayeque", "15": "Lima", "16": "Loreto", "17": "Madre de Dios", "18": "Moquegua",
    "19": "Pasco", "20": "Piura", "21": "Puno", "22": "San Martín", "23": "Tacna", "24": "Tumbes", "25": "Ucayali",
}
GRUPOS_EDAD = [0, 15, 30, 45, 60, 200]
NOMBRES_EDAD = ["0 a 14 años", "15 a 29 años", "30 a 44 años", "45 a 59 años", "60 años y más"]
# El mismo peso en los cinco años: factor07 × mieperho reproduce las cifras publicadas por el INEI en cada uno.
# La sumaria de 2020 y de 2021 solo trae factor07. El módulo 02 de 2020 trae además factor_p («factor de expansión
# anual - tipo presencial»), con valor solo en 63,866 de sus 126,831 filas; no se usa. El de 2021 no lo trae.
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

    def nota(self, texto: str) -> None:
        """Una aclaración que no es una comprobación: no cuenta como OK ni como FALLA."""
        self.lineas.append(f"NOTA  {texto}")

    def igual(self, nombre: str, valor: int, esperado: int, aviso: str = "") -> None:
        self.registrar(nombre, valor == esperado, f"{valor:,} (esperado {esperado:,}{'; ' + aviso if aviso else ''})")

    def cifra(self, nombre: str, valor: float, meta: Meta, tolerancia: float = TOLERANCIA, aviso: str = "") -> None:
        detalle = f"meta INEI {meta.valor} ± {tolerancia} %"
        if meta.ic_inf is not None and meta.ic_sup is not None:
            detalle += f", IC 95 %: [{meta.ic_inf:.1f}, {meta.ic_sup:.1f}]"
        detalle += f", {meta.cuadro}, p. {meta.pagina}"
        detalle += "".join(f"; {texto}" for texto in (meta.nota, aviso) if texto)
        self.registrar(nombre, abs(valor - meta.valor) <= tolerancia, f"{valor:.2f} % ({detalle})")


def _opcional(valor) -> float | None:
    return None if pd.isna(valor) else float(valor)


def leer_referencia_2024(ruta: Path = REFERENCIA_INEI) -> pd.DataFrame:
    if not ruta.is_file():
        sys.exit(f"Falta {ruta.name} en referencias/: sin las cifras publicadas por el INEI no hay contra qué validar.")
    return pd.read_csv(ruta, dtype={"ccdd": str})


def meta_de_fila(fila) -> Meta:
    nota = "" if pd.isna(fila.nota) else str(fila.nota)
    return Meta(float(fila.valor), str(fila.cuadro), int(fila.pagina), _opcional(fila.ic_inf), _opcional(fila.ic_sup),
                nota)


def metas_del_anio(anio: int, ruta_referencia: Path = REFERENCIA_INEI) -> dict[str, Meta]:
    """Las cifras publicadas por el INEI contra las que se valida el año, con su cuadro y su página."""
    if anio in METAS_INEI:
        return {clave: Meta(valor, *UBICACION_INEI[clave]) for clave, valor in METAS_INEI[anio].items()}
    tabla = leer_referencia_2024(ruta_referencia).set_index("ambito")
    faltan = [ambito for ambito in FILAS_REFERENCIA_2024.values() if ambito not in tabla.index]
    if faltan:
        sys.exit(f"Faltan las filas {faltan} en {ruta_referencia.name}.")
    return {clave: meta_de_fila(tabla.loc[[ambito]].iloc[0]) for clave, ambito in FILAS_REFERENCIA_2024.items()}


def validar(sumaria: pd.DataFrame, modulo02: pd.DataFrame, personas: pd.DataFrame,
            base: pd.DataFrame, anio: int) -> Validacion:
    v = Validacion()
    conteos = CONTEOS_ARCHIVOS_INEI[anio]
    metas = metas_del_anio(anio)

    v.igual("Hogares en la sumaria", len(sumaria), conteos["hogares"], f"sumaria-{anio}.dta, {AVISO_CONTEO}")
    v.igual("Filas del módulo 02", len(modulo02), conteos["filas_mod02"], f"enaho01-{anio}-200.dta, {AVISO_CONTEO}")
    v.igual("Residentes habituales", len(personas), conteos["residentes"],
            f"enaho01-{anio}-200.dta con el filtro de residentes, {AVISO_CONTEO}")
    v.igual("Llaves de hogar repetidas", int(sumaria.duplicated(LLAVES_HOGAR).sum()), 0)
    v.igual("Llaves de persona repetidas", int(personas.duplicated(LLAVES_PERSONA).sum()), 0)
    v.igual("Filas de la base tras la unión", len(base), len(personas))
    v.igual("Personas sin hogar en la sumaria", int(base["pobreza"].isna().sum()), 0)
    for columna, largo in LARGO_CODIGOS.items():
        v.igual(f"Códigos {columna} sin {largo} caracteres", int((base[columna].str.len() != largo).sum()), 0)

    # La pobreza oficial se calcula por hogar: factor07 × mieperho expande cada hogar a sus personas.
    hogares = base.drop_duplicates(LLAVES_HOGAR)
    v.igual("Hogares en la base", len(hogares), conteos["hogares"])
    peso = hogares["peso_hogar"]

    def pobreza_de(filtro: pd.Series, condicion: str = "pobre") -> float:
        cumple = hogares["pobreza"] == 1 if condicion == "extrema" else hogares["pobre"]
        return tasa(cumple[filtro], peso[filtro])

    todos = pd.Series(True, index=hogares.index)
    es_1501 = hogares["ubigeo"].str.startswith("1501")
    v.cifra("Pobreza nacional (hogares, factor07 × mieperho)", pobreza_de(todos), metas["nacional"])
    v.cifra("Pobreza nacional (personas, facpob07)", tasa(base["pobre"], base["facpob07"]), metas["nacional"],
            tolerancia_facpob07(anio), "contraste con otro ponderador, no es el método oficial")
    v.cifra("Pobreza extrema", pobreza_de(todos, "extrema"), metas["extrema"])
    v.cifra("Pobreza urbana", pobreza_de(hogares["urbano"]), metas["urbana"])
    v.cifra("Pobreza rural", pobreza_de(~hogares["urbano"]), metas["rural"])
    v.cifra("Pobreza en Lima Metropolitana y Callao (dominio 8)", pobreza_de(hogares["dominio"] == 8),
            metas["lima_metropolitana_callao"])
    v.cifra("Pobreza en Lima Metropolitana (provincia 1501)", pobreza_de(es_1501), metas["lima_metropolitana"])
    v.cifra("Pobreza en Lima provincias", pobreza_de((hogares["departamento"] == "15") & ~es_1501),
            metas["lima_provincias"])

    if anio == 2024:
        # Los departamentos del Cuadro III.1 (p. 220). El INEI publica Lima Metropolitana y Lima provincias, que se
        # validan arriba, pero no una cifra del departamento 15 en conjunto: no hay contra qué validarlo.
        tabla = leer_referencia_2024()
        departamentos = tabla[tabla["ccdd"].fillna("").str.fullmatch(r"\d{2}")]
        for fila in departamentos.itertuples():
            nombre = f"Pobreza en {fila.ambito}"
            de_aqui = hogares["departamento"] == fila.ccdd
            if de_aqui.any():
                v.cifra(nombre, pobreza_de(de_aqui), meta_de_fila(fila))
            else:
                v.registrar(nombre, False, "sin hogares en la base")
        v.igual("Departamentos con cifra publicada por el INEI en la referencia",
                departamentos["ccdd"].nunique(), len(DEPARTAMENTOS) - 1, "los 25 menos Lima (15)")
        v.nota("Lima, departamento 15: sin cifra publicada por el INEI para el departamento en conjunto. Se validan "
               "por separado Lima Metropolitana (provincia 1501) y Lima provincias, como las publica el Cuadro III.1.")

    v.igual("Departamentos con hogares", hogares["departamento"].nunique(), len(DEPARTAMENTOS),
            "consigna: 25 códigos territoriales")
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
    # Tres ámbitos de Lima con nombres distintos: el dominio 8 incluye el Callao; la provincia 1501, no.
    pobreza("pobreza_lima_metropolitana", "Pobreza monetaria", "Lima Metropolitana y Callao", hogares,
            hogares["dominio"] == 8, "peso_hogar", PESO_HOGAR)
    pobreza("pobreza_lima_metropolitana_provincia", "Pobreza monetaria", "Lima Metropolitana", hogares,
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
            # Orden estable por año: dentro de cada año se conserva el orden en que se generan los indicadores,
            # el mismo que da una corrida sin indicadores.csv previo.
            consolidado = consolidado.sort_values("anio", kind="stable").reset_index(drop=True)
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
    lineas_validacion = [
        f"Metas: {INFORME_INEI}.",
        f"Tolerancia de {TOLERANCIA} puntos: réplica de una cifra que el INEI publica con un decimal; no es una prueba "
        "estadística. La incertidumbre de muestreo la dan los IC al 95 % del INEI, publicados solo para 2024.",
        f"Tolerancia de {TOLERANCIA_FACPOB07} puntos en la línea facpob07 de 2020 a 2023 y de {TOLERANCIA} en {ANIO}: "
        "contraste con el factor de cada persona, que no es el ponderador del método oficial (factor07 × mieperho); "
        "con ese ponderador, 2021 difiere en 0.16 puntos de la cifra publicada.",
        "Los hogares, filas y residentes son conteos de los archivos del INEI, no cifras publicadas.",
        "",
    ]
    total_fallos = 0

    for anio in anios_a_procesar:
        base, tabla_ind, valid = procesar_un_anio(anio)
        lineas_validacion.append(f"Validación de la ENAHO {anio} (código de encuesta {CODIGOS_INEI[anio]}) "
                                 "contra las cifras publicadas por el INEI\n")
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
