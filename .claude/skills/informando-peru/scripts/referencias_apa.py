"""Referencias en formato APA 7 (en español), una función por tipo de fuente.

Cada función recibe los metadatos que devolvió la fuente (nombre de la serie, título del boletín, código de encuesta)
y nunca los completa de memoria. Las únicas constantes son las de dos obras fijas, verificadas en su origen:

- El informe técnico del INEI: título, año y URL del PDF, cuyo SHA-256 consta en referencias/README.md.
- Los límites del IGN publicados en OCHA HDX, verificados con la API de solo lectura
  https://data.humdata.org/api/3/action/package_show?id=cod-ab-per: título del conjunto («Peru - Subnational
  Administrative Boundaries»), fuente («Instituto Geográfico Nacional - IGN») y organización que lo publica
  («OCHA Field Information Services Section (FISS)»). La versión (v01) y su fecha de validez (2020-07-14) son los
  campos `version` y `valid_on` de cada unidad de per_admin1.geojson.

Reglas aplicadas: autor y fecha; título en cursiva; «(s. f.)» cuando la fuente no declara fecha de publicación;
«Recuperado el …, de URL» en el contenido que cambia con el tiempo; sin lugar de edición; sin editorial cuando
coincide con el autor; orden alfabético por autor y, para un mismo autor, primero las obras sin fecha y luego por año
y título; letras (s. f.-a, 2025a) para distinguir obras del mismo autor y fecha; sin duplicados.
"""
import calendar
import unicodedata
from dataclasses import dataclass, field
from datetime import date

BCRP = "Banco Central de Reserva del Perú"
SBS = "Superintendencia de Banca, Seguros y AFP"
INEI = "Instituto Nacional de Estadística e Informática"
IGN = "Instituto Geográfico Nacional"

MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre")
# Ruta de la página HTML de una serie en BCRPData, según su frecuencia
PAGINAS_BCRP = {"diaria": "diarias", "mensual": "mensuales", "trimestral": "trimestrales", "anual": "anuales"}
URL_BCRP = "https://estadisticas.bcrp.gob.pe/estadisticas/series/{carpeta}/resultados/{codigo}/html"
# Nombres de los módulos tal como los lista el portal de microdatos del INEI para la ENAHO anual de 2020 a 2024
# (Consulta por encuestas, «Condiciones de Vida y Pobreza - ENAHO», periodo Anual - (Ene-Dic)), en minúsculas
# salvo la primera palabra. Un módulo que no está aquí se cita solo con su número.
MODULOS_ENAHO = {"02": "Características de los miembros del hogar", "34": "Sumarias (variables calculadas)"}
ENCUESTA_ENAHO = "Encuesta Nacional de Hogares sobre Condiciones de Vida y Pobreza"
URL_INFORME_POBREZA = ("https://cdn.www.gob.pe/uploads/document/file/8058556/"
                       "6763186-peru-evolucion-de-la-pobreza-monetaria-2015-2024.pdf")
URL_LIMITES_IGN = "https://data.humdata.org/dataset/cod-ab-per"


@dataclass(frozen=True)
class Referencia:
    autor: str
    anio: int | None  # None: sin fecha de publicación, «s. f.»
    titulo: str       # va en cursiva
    resto: str        # lo que sigue al título: descripción entre corchetes, editorial, recuperación y URL
    orden: tuple = field(default=(), compare=False)  # desempate dentro del mismo autor, fecha y título


def fecha_larga(dia: date) -> str:
    """date(2026, 11, 5) → «5 de noviembre de 2026»."""
    return f"{dia.day} de {MESES[dia.month - 1]} de {dia.year}"


def fin_de_mes(periodo: str) -> str:
    """«2024-12» → «31 de diciembre de 2024»: los boletines de la SBS presentan los saldos al cierre del mes."""
    anio, mes = (int(p) for p in periodo.split("-")[:2])
    return fecha_larga(date(anio, mes, calendar.monthrange(anio, mes)[1]))


def _recuperado(dia: date | None, url: str) -> str:
    return f"Recuperado el {fecha_larga(dia)}, de {url}" if dia else url


def serie_bcrp(codigo: str, nombre: str, frecuencia: str, recuperado: date) -> Referencia:
    """Una serie de BCRPData: contenido que se actualiza, por eso sin fecha y con fecha de recuperación."""
    carpeta = PAGINAS_BCRP.get(frecuencia.strip().lower())
    if carpeta is None:
        raise ValueError(f"frecuencia {frecuencia!r} sin página HTML conocida en BCRPData para la serie {codigo}")
    url = URL_BCRP.format(carpeta=carpeta, codigo=codigo)
    return Referencia(BCRP, None, nombre, f" (Serie {codigo}) [Conjunto de datos]. BCRPData. "
                                         f"{_recuperado(recuperado, url)}")


def boletin_sbs(codigo: str, titulo: str, periodo: str, url: str, recuperado: date,
                publicado: int | None = None) -> Referencia:
    """Un boletín estadístico de la SBS en un periodo. `publicado` solo si la fuente declara el año de publicación:
    la fecha de modificación del archivo (encabezado HTTP) no lo es."""
    return Referencia(SBS, publicado, f"{titulo} al {fin_de_mes(periodo)}",
                      f" (Boletín {codigo}) [Conjunto de datos]. {_recuperado(recuperado, url)}", orden=(periodo,))


def microdatos_enaho(anio: int, codigo: int, modulo: str, url: str, recuperado: date | None = None) -> Referencia:
    """Un módulo de los microdatos anuales de la ENAHO, con la URL de su zip. `recuperado` es la fecha de descarga
    del zip, si se conoce; si no, la referencia queda solo con la URL."""
    modulo = f"{int(modulo):02d}"
    nombre = f"Módulo {modulo}" + (f", {MODULOS_ENAHO[modulo]}" if modulo in MODULOS_ENAHO else "")
    return Referencia(INEI, None, f"{ENCUESTA_ENAHO} {anio}: {nombre}",
                      f" (Código {codigo}) [Conjunto de datos]. {_recuperado(recuperado, url)}", orden=(anio, modulo))


def informe_pobreza_inei() -> Referencia:
    """El informe técnico del INEI del que salen las metas de validación de la ENAHO."""
    return Referencia(INEI, 2025, "Perú: Evolución de la pobreza monetaria, 2015-2024: Informe técnico",
                      f". {URL_INFORME_POBREZA}")


def limites_ign(recuperado: date | None = None) -> Referencia:
    """Los límites departamentales del IGN publicados por OCHA en HDX (versión v01, válida desde 2020-07-14)."""
    return Referencia(IGN, 2020, "Peru - Subnational administrative boundaries",
                      " (Versión v01) [Conjunto de datos]. OCHA Field Information Services Section; Humanitarian "
                      f"Data Exchange. {_recuperado(recuperado, URL_LIMITES_IGN)}")


def _clave(texto: str) -> str:
    """Clave de orden alfabético: sin tildes ni mayúsculas, para que «Índice» quede entre «Indicadores» e «Inflación»."""
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)).casefold()


def _orden(ref: Referencia):
    return _clave(ref.autor), ref.anio is not None, ref.anio or 0, _clave(ref.titulo), ref.orden, ref.resto


def _letra(i: int) -> str:
    """0 → a, 25 → z, 26 → aa."""
    return _letra(i // 26 - 1) + "abcdefghijklmnopqrstuvwxyz"[i % 26] if i >= 26 else "abcdefghijklmnopqrstuvwxyz"[i]


def lista_apa(referencias) -> list[str]:
    """Las referencias formateadas, ordenadas y sin duplicados, con letras para el mismo autor y fecha."""
    unicas = sorted(set(referencias), key=_orden)
    grupos = {}
    for ref in unicas:
        grupos.setdefault((ref.autor, ref.anio), []).append(ref)
    lineas = []
    for ref in unicas:
        grupo = grupos[(ref.autor, ref.anio)]
        letra = _letra(grupo.index(ref)) if len(grupo) > 1 else ""
        fecha = f"s. f.-{letra}" if ref.anio is None and letra else ("s. f." if ref.anio is None else f"{ref.anio}{letra}")
        lineas.append(f"{ref.autor}. ({fecha}). *{ref.titulo}*{ref.resto}")
    return lineas
