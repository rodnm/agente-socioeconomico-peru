"""¿Mejoran el MCP y las Skills las respuestas de Claude Code? Las mismas preguntas en varias configuraciones.

    uv run evaluacion/evaluar.py                               # Modo A y Modo B, con Sonnet
    uv run evaluacion/evaluar.py --modos A B memoria solo-mcp solo-skills sin-propia   # con la ablación
    uv run evaluacion/evaluar.py --robustez --modos A B        # pedidos ambiguos o imposibles

Adaptado del evaluar.py de la sesión 04. Cada pregunta corre en una sesión nueva de `claude -p` y en una copia nueva
del proyecto en una carpeta temporal, para que ninguna respuesta contamine a otra y para que ningún modo lea
evaluacion/ (donde están las respuestas esperadas). Las configuraciones:

    A            herramientas estándar de Claude Code; sin MCP, sin skills, sin CLAUDE.md ni salidas: solo los zip
    B            lo mismo que A más los servidores MCP (bcrp, sbs) y las skills del proyecto
    memoria      sin ninguna herramienta
    solo-mcp     A más los servidores MCP: sin skills, sin sus salidas y sin CLAUDE.md
    solo-skills  B sin los servidores MCP ni el código de mcp/ (Bash podría llamar sus funciones directamente)
    sin-propia   B sin la herramienta propia comparar_series

Todos los modos corren aislados de la configuración global del usuario (evaluación v2, hipótesis H7): la variable
CLAUDE_CODE_DISABLE_CLAUDE_MDS=1 apaga todo CLAUDE.md, --setting-sources project,local deja fuera los settings.json del
usuario y --strict-mcp-config sus servidores MCP. Como la variable apaga también el CLAUDE.md del proyecto, los modos
cuya copia lo incluye (B, solo-skills, sin-propia) lo reciben con --append-system-prompt.

Escribe evaluacion/resultados.csv (o robustez_resultados.csv) y un resumen por modo en la consola. Cada fila registra en
«aislamiento» la configuración usada, para distinguirla de las filas de la v1, que corrieron sin aislamiento.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
AQUI = RAIZ / "evaluacion"
BASICAS = "Bash,Read,Glob,Grep,WebSearch,WebFetch"
ESQUEMA = {"type": "object", "required": ["valor", "fuente"],
           "properties": {"valor": {"type": ["number", "null"]}, "valor_2": {"type": ["number", "null"]},
                          "unidad": {"type": "string"}, "fuente": {"type": "string"},
                          "interpretacion": {"type": "string"}}}
INSTRUCCION = ("Responde en «valor» con un solo número, en la unidad que pide la pregunta. Si la pregunta pide dos "
               "cifras, pon la segunda en «valor_2», en el orden en que se piden. Si no puedes obtener una cifra de una "
               "fuente verificable, pon null: no estimes. En «fuente» di de dónde sale cada cifra (código de serie, "
               "periodo, encuesta o archivo). Si la pregunta pide una interpretación, escríbela en «interpretacion» en "
               "una o dos oraciones.\n\n")
ESQUEMA_ROBUSTEZ = {"type": "object", "required": ["conducta", "respuesta"],
                    "properties": {"conducta": {"enum": ["responde", "pide_aclaracion", "declara_sin_datos"]},
                                   "valor": {"type": ["number", "null"]}, "supuesto": {"type": "string"},
                                   "respuesta": {"type": "string"}}}
INSTRUCCION_ROBUSTEZ = ("Atiende el pedido. En «conducta» indica si lo respondiste, si necesitas una aclaración o si "
                        "no hay datos para responderlo. Si respondes tomando un supuesto, escríbelo en «supuesto».\n\n")
MCP_PROYECTO = ["--mcp-config", ".mcp.json"]
MODOS = {  # (qué se copia, argumentos de claude -p)
    "A": ("crudos", ["--tools", BASICAS, "--allowedTools", BASICAS, "--disallowedTools", "Skill"]),
    "B": ("proyecto", ["--tools", f"{BASICAS},Skill", *MCP_PROYECTO,
                       "--allowedTools", f"{BASICAS},Skill,mcp__bcrp,mcp__sbs"]),
    "memoria": ("vacio", ["--tools", ""]),
    "solo-mcp": ("crudos-con-mcp", ["--tools", BASICAS, *MCP_PROYECTO, "--allowedTools",
                                    f"{BASICAS},mcp__bcrp,mcp__sbs", "--disallowedTools", "Skill"]),
    "solo-skills": ("proyecto-sin-mcp", ["--tools", f"{BASICAS},Skill", "--allowedTools", f"{BASICAS},Skill"]),
    "sin-propia": ("proyecto", ["--tools", f"{BASICAS},Skill", *MCP_PROYECTO,
                                "--allowedTools", f"{BASICAS},Skill,mcp__bcrp,mcp__sbs",
                                "--disallowedTools", "mcp__bcrp__comparar_series"]),
}
# Lo que nunca se copia: las respuestas esperadas, la historia y el entorno (se reutiliza por UV_PROJECT_ENVIRONMENT)
EXCLUIDOS = {".git", ".venv", "evaluacion", "evidencias_ia", "odd", ".pytest_cache", "__pycache__", "informes"}
# Aislamiento de la configuración del usuario (H7): --setting-sources no excluye el CLAUDE.md global; la variable sí.
SIN_CLAUDE_MD = {"CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1"}
SOLO_CONFIGURACION_DEL_PROYECTO = ["--setting-sources", "project,local"]
AISLAMIENTO = "claude_md_desactivado+setting_sources_project_local"


def preparar(copia, destino):
    """Arma la carpeta de trabajo de un modo. Ningún modo ve evaluacion/."""
    if copia == "vacio":
        return
    if copia.startswith("crudos"):  # solo los microdatos y límites originales, como los bajaría cualquiera
        (destino / "datos").mkdir()
        for archivo in ("966-Modulo34.zip", "966-Modulo02.zip", "peru_departamental_simple.geojson"):
            if (RAIZ / "datos" / archivo).is_file():
                shutil.copy(RAIZ / "datos" / archivo, destino / "datos")
        if copia == "crudos-con-mcp":  # el Modo A más el servidor del BCRP y su entorno: nada de lo que hicieron las skills
            shutil.copytree(RAIZ / "mcp", destino / "mcp", ignore=shutil.ignore_patterns("__pycache__"))
            for archivo in (".mcp.json", "pyproject.toml", "uv.lock"):
                shutil.copy(RAIZ / archivo, destino)
            # El servidor importa el estilo de los gráficos al arrancar; sin él, el modo se queda sin BCRP.
            (destino / "scripts").mkdir()
            shutil.copy(RAIZ / "scripts" / "estilo_graficos.py", destino / "scripts")
        return
    shutil.copytree(RAIZ, destino, dirs_exist_ok=True, ignore=lambda d, nombres: [n for n in nombres if n in EXCLUIDOS])
    if copia == "proyecto-sin-mcp":  # las herramientas son funciones de Python: con el código, Bash las llamaría igual
        shutil.rmtree(destino / "mcp")
        (destino / ".mcp.json").unlink()


def reglas_del_proyecto(carpeta):
    """El CLAUDE.md de la copia como prompt de sistema adicional, porque SIN_CLAUDE_MD apaga también el del proyecto."""
    archivo = carpeta / "CLAUDE.md"
    return ["--append-system-prompt", archivo.read_text(encoding="utf-8")] if archivo.is_file() else []


def herramientas_usadas(eventos):
    usadas = []
    for e in eventos:
        for c in e.get("message", {}).get("content", []) if e.get("type") == "assistant" else []:
            if c.get("type") == "tool_use" and c["name"] != "StructuredOutput":
                nombre = f"Skill:{c['input'].get('skill', '?')}" if c["name"] == "Skill" else c["name"]
                if nombre not in usadas:
                    usadas.append(nombre)
    return usadas


def motivo_de_error(codigo, stderr):
    """La causa de una corrida fallida, sin el aviso de workspace no confiable que sale en toda copia temporal."""
    if codigo == 0:
        return ""
    lineas = [l for l in stderr.splitlines() if l.strip() and "has not been trusted" not in l]
    return "\n".join(lineas)[-300:] or f"claude -p salió con código {codigo}"


def preguntar(texto, modo, modelo, robustez=False):
    copia, argumentos = MODOS[modo]
    with tempfile.TemporaryDirectory(prefix=f"eval_{modo}_") as tmp:
        preparar(copia, Path(tmp))
        esquema, instruccion = (ESQUEMA_ROBUSTEZ, INSTRUCCION_ROBUSTEZ) if robustez else (ESQUEMA, INSTRUCCION)
        cmd = ["claude", "-p", instruccion + texto, "--output-format", "stream-json", "--verbose",
               "--json-schema", json.dumps(esquema), "--no-session-persistence", "--model", modelo,
               "--strict-mcp-config", *argumentos, *SOLO_CONFIGURACION_DEL_PROYECTO, *reglas_del_proyecto(Path(tmp))]
        entorno = os.environ | {"UV_PROJECT_ENVIRONMENT": str(RAIZ / ".venv")} | SIN_CLAUDE_MD
        t = time.time()
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=900, cwd=tmp,
                                  env=entorno)
            salida, error = proc.stdout, motivo_de_error(proc.returncode, proc.stderr)
        except subprocess.TimeoutExpired:
            salida, error = "", "tiempo agotado (900 s)"
    eventos = [json.loads(l) for l in salida.splitlines() if l.startswith("{")]
    final = next((e for e in reversed(eventos) if e.get("type") == "result"), {})
    r = final.get("structured_output") or {}
    return {**r, "segundos": round(time.time() - t, 1), "turnos": final.get("num_turns"),
            "costo_usd": final.get("total_cost_usd"), "herramientas": ";".join(herramientas_usadas(eventos)),
            "error": error or ("sin respuesta estructurada" if not r else "")}


def calificar(fila):
    """acierta si cada cifra pedida cae dentro de su tolerancia; no sabe si alguna es null."""
    pares = [(fila.get("valor"), fila["verdad"], fila["tolerancia"])]
    if pd.notna(fila.get("verdad_2")):
        pares.append((fila.get("valor_2"), fila["verdad_2"], fila["tolerancia_2"]))
    if fila.get("error") and all(v is None for v, _, _ in pares):
        return "error"
    if any(v is None or pd.isna(v) for v, _, _ in pares):
        return "no sabe"
    return "acierta" if all(abs(v - verdad) <= tol for v, verdad, tol in pares) else "se equivoca"


def lenguaje_causal(texto):
    """Ayuda para la revisión manual de las preguntas mixtas: marca palabras que afirman causas."""
    return bool(re.search(r"\b(caus\w*|provoc\w*|debido a|gener[óo]|explica[n]? (que|la)|por culpa)\b", str(texto),
                          re.IGNORECASE))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--modos", nargs="+", default=["A", "B"], choices=list(MODOS))
    p.add_argument("--modelo", default="sonnet")
    p.add_argument("--paralelo", type=int, default=4)
    p.add_argument("--robustez", action="store_true", help="Usa evaluacion/robustez.csv en lugar de preguntas.csv.")
    p.add_argument("--solo", nargs="+", help="Ids de preguntas a correr, para repetir una sola.")
    a = p.parse_args()

    archivo = AQUI / ("robustez.csv" if a.robustez else "preguntas.csv")
    preguntas = pd.read_csv(archivo)
    if a.solo:
        preguntas = preguntas[preguntas["id"].astype(str).isin(a.solo)]
    casos = [(q, m) for q in preguntas.to_dict("records") for m in a.modos]
    print(f"{len(casos)} llamadas a claude -p con {a.modelo} ({', '.join(a.modos)})...")
    texto = "pedido" if a.robustez else "pregunta"
    with ThreadPoolExecutor(a.paralelo) as ex:
        respuestas = list(ex.map(lambda c: preguntar(c[0][texto], c[1], a.modelo, a.robustez), casos))

    if a.robustez:
        filas = [{"id": q["id"], "modo": m, "pedido": q["pedido"], "conducta_esperada": q["conducta_esperada"],
                  "conducta_observada": r.get("conducta"), "supuesto": r.get("supuesto", ""),
                  "respuesta": r.get("respuesta", ""), "herramientas": r["herramientas"], "segundos": r["segundos"],
                  "resultado": "cumple" if r.get("conducta") in q["conducta_esperada"].split("|") else "no cumple",
                  "error": r["error"], "aislamiento": AISLAMIENTO} for (q, m), r in zip(casos, respuestas)]
        destino = AQUI / "robustez_resultados.csv"
    else:
        filas = []
        for (q, m), r in zip(casos, respuestas):
            fila = {**{k: q.get(k) for k in ("id", "tipo", "pregunta", "verdad", "verdad_2", "unidad", "tolerancia",
                                             "tolerancia_2")}, "modo": m, **r}
            fila["resultado"] = calificar(fila)
            fila["lenguaje_causal"] = lenguaje_causal(r.get("interpretacion", ""))
            fila["aislamiento"] = AISLAMIENTO
            filas.append(fila)
        destino = AQUI / "resultados.csv"
    res = pd.DataFrame(filas)
    previos = pd.read_csv(destino) if destino.is_file() else pd.DataFrame()
    if not previos.empty:  # conserva las corridas de otros modos o preguntas
        clave = res[["id", "modo"]].astype(str).agg("|".join, axis=1)
        previos = previos[~previos[["id", "modo"]].astype(str).agg("|".join, axis=1).isin(clave)]
    pd.concat([previos, res], ignore_index=True).to_csv(destino, index=False, encoding="utf-8")

    tabla = res.groupby("modo")["resultado"].value_counts().unstack(fill_value=0)
    tabla["segundos"] = res.groupby("modo")["segundos"].mean().round(1)
    print(f"\n{destino.relative_to(RAIZ).as_posix()}\n" + tabla.to_string())


if __name__ == "__main__":
    main()
