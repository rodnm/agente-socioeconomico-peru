"""Servidor MCP del BCRP: series estadísticas oficiales del Banco Central de Reserva del Perú.

    uv run pytest mcp/test_server.py   # el contrato: las 8 pruebas de la sesión 04 y 2 de comparar_series
    uv run mcp/server.py               # el servidor, por stdio (así lo lanza .mcp.json)

Parte del proyecto de la sesión 04 de Data-Science-Python: completa sus TODO y agrega comparar_series y
graficar_serie. Las cuentas las hace Python, no el modelo: así cada cifra sale de una llamada que se puede repetir.
"""
import calendar
import hashlib
import json
import re
import textwrap
import time
import unicodedata
from datetime import datetime, timedelta
from functools import cache
from pathlib import Path

import httpx
import matplotlib

matplotlib.use("Agg")  # sin ventana: el servidor corre por stdio
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from fastmcp import FastMCP  # noqa: E402
from fastmcp.exceptions import ToolError  # noqa: E402

import sys
AQUI = Path(__file__).parent
RAIZ = AQUI.parent
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))
import estilo_graficos  # noqa: E402
DATOS = RAIZ / "datos" / "bcrp"
CATALOGO = DATOS / "catalogo_bcrp.csv"
CACHE = DATOS / "cache"
FIGURAS = RAIZ / "figuras"
URL_CATALOGO = "https://estadisticas.bcrp.gob.pe/estadisticas/series/metadata"
API = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"
CABECERAS = {"User-Agent": "agente-socioeconomico-peru/0.1 (+https://github.com/rodnm/agente-socioeconomico-peru)"}
SOLO_LECTURA = {"readOnlyHint": True, "openWorldHint": True}
VIGENCIA_CACHE = timedelta(hours=24)
ESPERAS = (2, 5, 10)  # segundos entre reintentos cuando el BCRP responde una página HTML en vez de datos
MESES = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6, "jul": 7, "ago": 8, "set": 9, "sep": 9,
         "oct": 10, "nov": 11, "dic": 12}

mcp = FastMCP("bcrp", instructions=(
    "Series oficiales del Banco Central de Reserva del Perú (BCRP). Primero busca el código con buscar_series; "
    "luego usa resumen para variaciones, promedios y extremos, serie para los datos, comparar_series para "
    "relacionar dos indicadores y graficar_serie para guardar un gráfico. No calcules a mano: cita siempre el "
    "código de la serie, el periodo y la URL de la fuente. Si una herramienta falla, dilo en vez de estimar."))


def _sin_tildes(s):
    return unicodedata.normalize("NFD", str(s).lower()).encode("ascii", "ignore").decode()


def _descargar(url, es_valida):
    """GET con reintentos. Devuelve (respuesta, motivo); la respuesta es None si nunca llegaron datos válidos.

    Cuando recibe muchos pedidos, o cuando su protección anti-bots se activa, el BCRP responde una página HTML con
    código 200 en lugar de datos: por eso se valida el contenido además del código HTTP.
    """
    motivo = "sin respuesta"
    for espera in (0, *ESPERAS):
        time.sleep(espera)
        try:
            r = httpx.get(url, timeout=120, headers=CABECERAS, follow_redirects=True)
            r.raise_for_status()
        except httpx.HTTPError as e:
            motivo = f"error de conexión: {type(e).__name__}"
            continue
        if es_valida(r):
            return r, None
        motivo = "respondió una página HTML en vez de datos (límite de consultas o protección anti-bots)"
    return None, motivo


def _es_json(r):
    try:
        r.json()
        return True
    except ValueError:
        return False


@cache
def catalogo():
    """El catálogo oficial: 17 mil series en unos 7 MB. Se baja una vez y queda en datos/bcrp/."""
    if not CATALOGO.exists():
        r, motivo = _descargar(URL_CATALOGO, lambda r: not r.text.lstrip().startswith("<"))
        if r is None:
            raise ToolError(f"No se pudo descargar el catálogo del BCRP: {motivo}. Intenten de nuevo en unos minutos.")
        CATALOGO.parent.mkdir(parents=True, exist_ok=True)
        CATALOGO.write_text(r.content.decode("latin-1"), encoding="utf-8")
    df = pd.read_csv(CATALOGO, sep=";", dtype=str).fillna("")
    df = df.rename(columns={"Código de serie": "codigo", "Categoría de serie": "categoria", "Grupo de serie": "grupo",
                            "Nombre de serie": "nombre", "Frecuencia": "frecuencia",
                            "Fecha de actualización": "actualizada", "Fecha de inicio": "inicio"})
    df["texto"] = (df.categoria + " " + df.grupo + " " + df.nombre).map(_sin_tildes)
    return df


def _ficha(codigo):
    fila = catalogo().query("codigo == @codigo")
    if fila.empty:
        raise ToolError(f"No existe el código de serie {codigo!r}. Búsquenlo con buscar_series.")
    f = fila.iloc[0]
    return {"codigo": f.codigo, "nombre": f"{f.grupo} - {f.nombre}", "categoria": f.categoria,
            "frecuencia": f.frecuencia, "inicio": f.inicio, "actualizada": f.actualizada}


def _pedir(url):
    """El JSON de la API, con caché en disco de 24 horas. Devuelve (json, aviso).

    Si el BCRP no responde pero hay una copia guardada, aunque esté vencida, la usa y lo avisa: es mejor un dato
    con fecha conocida que ningún dato. Sin copia, el error dice por qué falló.
    """
    archivo = CACHE / f"{hashlib.sha1(url.encode()).hexdigest()[:16]}.json"
    guardado = datetime.fromtimestamp(archivo.stat().st_mtime) if archivo.exists() else None
    if guardado and datetime.now() - guardado < VIGENCIA_CACHE:
        return json.loads(archivo.read_text(encoding="utf-8")), None
    r, motivo = _descargar(url, _es_json)
    if r is not None:
        CACHE.mkdir(parents=True, exist_ok=True)
        archivo.write_text(r.text, encoding="utf-8")
        return r.json(), None
    if guardado:
        return (json.loads(archivo.read_text(encoding="utf-8")),
                f"El BCRP no respondió ({motivo}); se usó la copia guardada el {guardado:%Y-%m-%d %H:%M}.")
    raise ToolError(f"El BCRP no respondió con datos: {motivo}. Intenten de nuevo en unos minutos.")


def _fecha_api(fecha, frecuencia, fin=False):
    """Lleva una fecha AAAA, AAAA-MM, AAAA-Tn o AAAA-MM-DD al formato que pide la API según la frecuencia.

    La API pide 2025-1 en series mensuales y trimestrales, 2025-01-15 en diarias y 2025 en anuales. Con fin=True,
    un mes sin día en una serie diaria se lee como su último día.
    """
    m = re.fullmatch(r"(\d{4})(?:-(T?)(\d{1,2}))?(?:-(\d{1,2}))?", str(fecha).strip(), flags=re.IGNORECASE)
    if not m:
        raise ToolError(f"Fecha {fecha!r} no válida: usen AAAA, AAAA-MM, AAAA-Tn o AAAA-MM-DD, por ejemplo 2025-01.")
    anio, trimestral, num, dia = m.groups()
    f = frecuencia.lower()
    if f == "anual":
        return anio
    if num is None:
        raise ToolError(f"La serie es {f}: indiquen también el mes o el trimestre, por ejemplo {anio}-01.")
    n = int(num)
    if f == "trimestral":
        return f"{anio}-{n if trimestral else (n - 1) // 3 + 1}"
    if trimestral or not 1 <= n <= 12:
        raise ToolError(f"Fecha {fecha!r} no válida para una serie {f}: el mes va de 01 a 12.")
    if f == "mensual":
        return f"{anio}-{n}"
    if f == "diaria":
        ultimo = calendar.monthrange(int(anio), n)[1]
        return f"{anio}-{n:02d}-{int(dia) if dia else (ultimo if fin else 1):02d}"
    raise ToolError(f"Frecuencia {frecuencia!r} no soportada.")


def _anio(aa):
    """Año de dos dígitos a cuatro: 26 → 2026 y 98 → 1998."""
    return int(aa) + (2000 if int(aa) <= datetime.now().year % 100 + 1 else 1900)


def _periodo(nombre):
    """Nombre de periodo de la API en formato ISO: Ene.2025 → 2025-01, 01.Oct.26 → 2026-10-01, T1.25 → 2025-T1."""
    partes = nombre.split(".")
    try:
        if len(partes) == 1:
            return nombre
        if len(partes) == 2 and partes[0][:1].upper() == "T":
            return f"{_anio(partes[1][-2:])}-T{int(partes[0][1:])}"
        if len(partes) == 2:
            return f"{partes[1]}-{MESES[partes[0][:3].lower()]:02d}"
        dia, mes, aa = partes
        return f"{_anio(aa[-2:])}-{MESES[mes[:3].lower()]:02d}-{int(dia):02d}"
    except (KeyError, ValueError):
        return nombre  # un formato desconocido se devuelve tal cual antes que inventar una fecha


def _consultar(codigo, desde, hasta):
    """Ficha, datos [{periodo, valor}] sin los "n.d.", URL de la fuente y aviso de caché de una serie."""
    ficha = _ficha(codigo)
    url = f"{API}/{codigo}/json/{_fecha_api(desde, ficha['frecuencia'])}/{_fecha_api(hasta, ficha['frecuencia'], True)}"
    respuesta, aviso = _pedir(url)
    datos = []
    for p in respuesta.get("periods", []):
        try:
            datos.append({"periodo": _periodo(p["name"]), "valor": float(p["values"][0])})
        except (ValueError, IndexError, KeyError):
            continue  # "n.d." o celda vacía
    if not datos:
        raise ToolError(f"La serie {codigo} no tiene datos entre {desde} y {hasta}. Empieza en {ficha['inicio']} y "
                        f"se actualizó el {ficha['actualizada']}.")
    return ficha, datos, url, aviso


def _como_serie(datos):
    return pd.Series({d["periodo"]: d["valor"] for d in datos}).sort_index()


def _punto(s, periodo):
    return {"periodo": periodo, "valor": float(s[periodo])}


@mcp.tool(annotations=SOLO_LECTURA)
def buscar_series(texto: str, frecuencia: str | None = None, limite: int = 10) -> list[dict]:
    """Busca series del BCRP por palabras: todas deben aparecer en la categoría, el grupo o el nombre.

    Ejemplos: "ipc 12 meses", "tipo de cambio interbancario venta", "reservas internacionales netas",
    "tasa de referencia", "cobre precio". frecuencia: "Diaria", "Mensual", "Trimestral" o "Anual".
    Devuelve el código, el nombre completo, la frecuencia y desde cuándo hay datos. Si no hay resultados,
    prueben con menos palabras.
    """
    df = catalogo()
    m = pd.Series(True, index=df.index)
    for palabra in _sin_tildes(texto).split():
        m &= df.texto.str.contains(re.escape(palabra))
    if frecuencia:
        m &= df.frecuencia.str.lower() == frecuencia.lower()
    # primero las series vigentes y, entre ellas, las de nombre más corto (las más generales)
    sel = df[m]
    orden = sel.assign(vieja=sel.actualizada < "2025", largo=(sel.grupo + sel.nombre).str.len())
    return [_ficha(c) for c in orden.sort_values(["vieja", "largo"]).head(limite).codigo]


@mcp.tool(annotations=SOLO_LECTURA)
def serie(codigo: str, desde: str, hasta: str) -> dict:
    """Descarga los datos de una serie del BCRP entre dos fechas, incluidas ambas.

    codigo: el de buscar_series, por ejemplo "PN01273PM". desde y hasta: "2025-01" en series mensuales,
    "2026-10-01" en diarias, "2025-T1" en trimestrales y "2025" en anuales. Omite los periodos sin dato ("n.d.").
    Devuelve el nombre, la frecuencia, los datos [{periodo, valor}] y la URL de la fuente para citarla.
    """
    ficha, datos, url, aviso = _consultar(codigo, desde, hasta)
    r = {"codigo": codigo, "nombre": ficha["nombre"], "frecuencia": ficha["frecuencia"], "datos": datos, "fuente": url}
    return r | ({"aviso": aviso} if aviso else {})


@mcp.tool(annotations=SOLO_LECTURA)
def resumen(codigo: str, desde: str, hasta: str) -> dict:
    """Resume una serie del BCRP sin cuentas a mano: primer y último valor, cambio, variación porcentual,
    promedio, máximo y mínimo, estos dos con su periodo.

    cambio es la diferencia en las unidades de la serie. Si la serie ya es una tasa (inflación, tasa de interés),
    el cambio está en puntos porcentuales y variacion_pct suele no tener sentido: usen cambio. Mismas fechas que serie.
    """
    ficha, datos, url, aviso = _consultar(codigo, desde, hasta)
    s = _como_serie(datos)
    primero, ultimo = float(s.iloc[0]), float(s.iloc[-1])
    r = {"codigo": codigo, "nombre": ficha["nombre"], "frecuencia": ficha["frecuencia"],
         "periodo": f"{s.index[0]} a {s.index[-1]}", "n": len(s),
         "primero": _punto(s, s.index[0]), "ultimo": _punto(s, s.index[-1]),
         "cambio": round(ultimo - primero, 6),
         "variacion_pct": round((ultimo / primero - 1) * 100, 6) if primero else None,
         "promedio": round(float(s.mean()), 6),
         "maximo": _punto(s, s.idxmax()), "minimo": _punto(s, s.idxmin()), "fuente": url}
    return r | ({"aviso": aviso} if aviso else {})


@mcp.tool(annotations=SOLO_LECTURA)
def comparar_series(codigo_a: str, codigo_b: str, desde: str, hasta: str) -> dict:
    """Compara dos series del BCRP de la misma frecuencia en los periodos en que ambas tienen dato.

    Alinea los periodos, descarta los que faltan en alguna de las dos y calcula la correlación de Pearson, el
    cambio de cada serie y la diferencia a - b: su promedio y la brecha máxima con su periodo. Sirve, por ejemplo,
    para contrastar la inflación total con la inflación sin alimentos y energía, o el tipo de cambio con otra serie
    diaria. La correlación describe una asociación entre las series, no una relación causal.
    """
    fichas = {codigo_a: _ficha(codigo_a), codigo_b: _ficha(codigo_b)}
    frecuencias = {c: f["frecuencia"] for c, f in fichas.items()}
    if len(set(frecuencias.values())) > 1:
        raise ToolError(f"Las series tienen frecuencias distintas: {codigo_a} es {frecuencias[codigo_a].lower()} y "
                        f"{codigo_b} es {frecuencias[codigo_b].lower()}. Elijan series con la misma frecuencia o "
                        "comparen sus promedios con resumen.")
    consultas = {c: _consultar(c, desde, hasta) for c in (codigo_a, codigo_b)}
    juntas = pd.concat({"a": _como_serie(consultas[codigo_a][1]), "b": _como_serie(consultas[codigo_b][1])},
                       axis=1).sort_index()
    comunes = juntas.dropna()
    if len(comunes) < 3:
        raise ToolError(f"Solo hay {len(comunes)} periodos con dato en ambas series entre {desde} y {hasta}: "
                        "hacen falta al menos 3 para compararlas.")
    correlacion = comunes.a.corr(comunes.b)
    diferencia = comunes.a - comunes.b
    brecha = diferencia.abs().idxmax()
    series = [{"codigo": c, "nombre": consultas[c][0]["nombre"], "primero": _punto(comunes[k], comunes.index[0]),
               "ultimo": _punto(comunes[k], comunes.index[-1]),
               "cambio": round(float(comunes[k].iloc[-1] - comunes[k].iloc[0]), 6),
               "promedio": round(float(comunes[k].mean()), 6)}
              for k, c in (("a", codigo_a), ("b", codigo_b))]
    nota = "La correlación describe una asociación entre las dos series, no una relación causal."
    if pd.isna(correlacion):
        nota += " No se pudo calcular porque una de las series no varía en el periodo."
    avisos = [consultas[c][3] for c in consultas if consultas[c][3]]
    return {"frecuencia": frecuencias[codigo_a], "periodo": f"{comunes.index[0]} a {comunes.index[-1]}",
            "n": len(comunes), "excluidos": len(juntas) - len(comunes),
            "correlacion": None if pd.isna(correlacion) else round(float(correlacion), 4), "series": series,
            "diferencia_a_menos_b": {"promedio": round(float(diferencia.mean()), 6),
                                     "brecha_maxima": _punto(diferencia, brecha)},
            "fuentes": [consultas[c][2] for c in (codigo_a, codigo_b)], "nota": nota} | (
        {"avisos": avisos} if avisos else {})


def _eje_x(periodos, frecuencia):
    f = frecuencia.lower()
    if f == "mensual":
        return pd.to_datetime([p + "-01" for p in periodos])
    if f == "trimestral":
        return pd.PeriodIndex([p.replace("-T", "Q") for p in periodos], freq="Q").to_timestamp()
    if f == "anual":
        return pd.to_datetime([p + "-01-01" for p in periodos])
    return pd.to_datetime(list(periodos))


@mcp.tool(annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True,
                       "openWorldHint": True})
def graficar_serie(codigo: str, desde: str, hasta: str, titulo: str | None = None) -> dict:
    """Grafica una serie del BCRP y guarda el PNG en figuras/, con título, periodo, frecuencia y fuente.

    titulo: opcional, una frase analítica sobre lo que muestra el gráfico; por defecto, el nombre oficial de la
    serie. Mismas fechas que serie. Devuelve la ruta del archivo para citarlo en el informe, el primer y el último
    valor graficados y la URL de la fuente.
    """
    ficha, datos, url, aviso = _consultar(codigo, desde, hasta)
    s = _como_serie(datos)
    fig, ax = plt.subplots(figsize=(9, 4.8), facecolor=estilo_graficos.COLOR_FONDO)
    ax.set_facecolor(estilo_graficos.COLOR_FONDO)
    ax.plot(_eje_x(s.index, ficha["frecuencia"]), s.to_numpy(), color=estilo_graficos.COLOR_PRINCIPAL, linewidth=1.8)

    nombre_l = ficha["nombre"].lower()
    if "%" in nombre_l or "var%" in nombre_l:
        ax.set_ylabel("%", color=estilo_graficos.COLOR_SECUNDARIO, fontsize=9)
    elif "soles" in nombre_l or "s/" in nombre_l or "tipo de cambio" in nombre_l:
        ax.set_ylabel("S/ por US$", color=estilo_graficos.COLOR_SECUNDARIO, fontsize=9)
    elif "índice" in nombre_l or "indice" in nombre_l:
        ax.set_ylabel("Índice", color=estilo_graficos.COLOR_SECUNDARIO, fontsize=9)

    if s.min() < 0 < s.max():
        ax.axhline(0, color=estilo_graficos.COLOR_LINEA_GUIA, linewidth=0.8, linestyle="--")
    estilo_graficos.estilizar_ejes(ax)

    titulo_texto = titulo or ficha["nombre"]
    subtitulo_texto = f"{ficha['nombre'][:100]} · {s.index[0]} a {s.index[-1]}"
    fuente_texto = f"Fuente: BCRP, serie {codigo} ({ficha['frecuencia'].lower()})."
    estilo_graficos.encabezado(fig, ax, titulo=titulo_texto, subtitulo=subtitulo_texto, fuente=fuente_texto)

    FIGURAS.mkdir(exist_ok=True)
    archivo = FIGURAS / f"bcrp_{codigo}_{desde}_{hasta}.png"
    fig.savefig(archivo, dpi=200, facecolor=estilo_graficos.COLOR_FONDO)
    plt.close(fig)
    # Los datos graficados quedan junto a las salidas: el dashboard los lee sin volver a consultar al BCRP
    (RAIZ / "salidas" / "bcrp").mkdir(parents=True, exist_ok=True)
    s.rename_axis("periodo").rename("valor").to_frame().assign(codigo=codigo, nombre=ficha["nombre"], fuente=url).to_csv(
        RAIZ / "salidas" / "bcrp" / f"{codigo}_{desde}_{hasta}.csv", encoding="utf-8")
    r = {"archivo": archivo.relative_to(RAIZ).as_posix(), "codigo": codigo, "nombre": ficha["nombre"],
         "periodo": f"{s.index[0]} a {s.index[-1]}", "n": len(s), "primero": _punto(s, s.index[0]),
         "ultimo": _punto(s, s.index[-1]), "fuente": url}
    return r | ({"aviso": aviso} if aviso else {})


@mcp.resource("bcrp://serie/{codigo}", mime_type="application/json")
def ficha_serie(codigo: str) -> str:
    """Ficha descriptiva de una serie del BCRP: nombre, categoría, frecuencia, inicio, última actualización y
    las direcciones de la API para consultarla."""
    return json.dumps(_ficha(codigo) | {"api": f"{API}/{codigo}/json/<desde>/<hasta>",
                                        "catalogo": URL_CATALOGO}, ensure_ascii=False)


@mcp.prompt
def interpretar_indicador(codigo: str, desde: str, hasta: str) -> str:
    """Guía para interpretar un indicador del BCRP en un periodo, citando el código, el periodo y la fuente."""
    return (f"Interpreta la serie {codigo} del BCRP entre {desde} y {hasta}.\n"
            f"1. Lee su ficha en el recurso bcrp://serie/{codigo} para saber qué mide y en qué unidad.\n"
            "2. Usa resumen para el primer y último valor, el cambio, el promedio y los extremos. No hagas cuentas a "
            "mano.\n"
            "3. Si la serie es una tasa (inflación, interés), expresa los cambios en puntos porcentuales.\n"
            "4. Si ayuda, contrástala con otra serie de la misma frecuencia mediante comparar_series, y recuerda que "
            "una correlación no prueba causalidad.\n"
            "5. Escribe de 3 a 5 oraciones. Cada cifra va con el código de la serie, el periodo y la URL de la fuente.\n"
            "6. Si una herramienta falla o no hay datos, dilo en lugar de estimar.")


@mcp.prompt
def informe(tema: str, desde: str, hasta: str) -> str:
    """Plantilla de un informe breve sobre un tema macroeconómico del Perú con series oficiales del BCRP."""
    return (f"Prepara un informe breve sobre «{tema}» en el Perú entre {desde} y {hasta} con series del BCRP.\n"
            "1. Busca con buscar_series de 2 a 4 series pertinentes y explica por qué elegiste cada código.\n"
            "2. Resume cada una con resumen y, si comparten frecuencia, relaciónalas con comparar_series.\n"
            "3. Guarda con graficar_serie el gráfico de la serie principal.\n"
            "4. Estructura: pregunta, fuentes y método, 3 hallazgos con cifras, interpretación y limitaciones.\n"
            "5. Cada cifra con su código, periodo y URL. No afirmes causalidad y, si algo falla, dilo.")


if __name__ == "__main__":
    mcp.run()
