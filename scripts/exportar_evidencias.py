"""Convierte transcripciones de Claude Code (JSONL) y de Google Antigravity en Markdown legible y sin datos sensibles,
para evidencias_ia/.

    uv run scripts/exportar_evidencias.py ORIGEN.jsonl evidencias_ia/skills/01_encadenamiento.md [--titulo T]
        [--ocultar TEXTO ...]
    uv run scripts/exportar_evidencias.py ~/.gemini/antigravity/brain/<sesión> evidencias_ia/gemini/01_sesion.md

Acepta las sesiones que Claude Code guarda en ~/.claude/projects/<proyecto>/<sesión>.jsonl, la salida de
`claude -p --output-format stream-json --verbose` y la carpeta de una sesión de Antigravity, cuyos fragmentos une
antes de leerlos; ahí las respuestas figuran como de Gemini. Empieza con una línea de tiempo de las herramientas
usadas, con los servidores MCP y las skills que intervinieron. Conserva los pedidos, las respuestas, cada llamada a
una herramienta con sus argumentos y un extracto de cada resultado; el razonamiento interno del modelo no se exporta.
Oculta rutas personales, el nombre de usuario del sistema, correos, claves y tokens. Revisen el resultado antes de
publicarlo: la redacción automática no reemplaza una lectura humana.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

LIMITE_RESULTADO = 1200
LIMITE_ARGUMENTOS = 600
OCULTAR = [
    (re.compile(r"(sk-ant-|sk-|ghp_|gho_|github_pat_|xox[bap]-)[A-Za-z0-9_\-]{8,}"), "[CLAVE OCULTA]"),
    (re.compile(r"(?i)(bearer|token|api[_-]?key|password|contraseña)(\"?\s*[:=]\s*\"?)[^\s\"',]{6,}"), r"\1\2[OCULTO]"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[CORREO OCULTO]"),
    (re.compile(r"(?i)[A-Z]:[\\/]+Users[\\/]+[^\\/\s\"']+"), "~"),
    (re.compile(r"/(?:c/)?(?:home|Users)/[^/\s\"']+"), "~"),
]


# Mensajes que la herramienta inserta con el rol de la persona: se muestran plegados y no cuentan como pedidos.
GENERADO_POR_LA_HERRAMIENTA = {
    "Base directory for this skill": "Instrucciones de la skill que cargó Claude Code",
    "This session is being continued from a previous conversation": (
        "Resumen automático de la parte anterior de la sesión (Claude Code compactó el contexto)"),
    "# Resuming from a compaction": "Resumen automático de la parte anterior de la sesión (Antigravity compactó el contexto)",
    "The following is a <SYSTEM_MESSAGE>": "Mensaje del sistema de Antigravity",
}
AVISO_DE_LIMITE = re.compile(r"\[(Usage limit reached|Earlier usage-limit notes)")
# Claude Code envuelve lo que la persona pega; sin quitar la envoltura, el pedido parecería un aviso del sistema.
PEGADO = re.compile(r"<pasted_content[^>]*>\n?(.*?)\n?</pasted_content[^>]*>", re.DOTALL)
# Antigravity envuelve el pedido y le agrega la hora local; solo el pedido es lo que escribió la persona.
SOLICITUD = re.compile(r"<USER_REQUEST>\n?(.*?)\n?</USER_REQUEST>", re.DOTALL)
FRAGMENTOS_DE_ANTIGRAVITY = Path(".system_generated") / "logs" / "chunks" / "transcript_full"


def ocultar(texto, extra=()):
    for patron, reemplazo in OCULTAR:
        texto = patron.sub(reemplazo, texto)
    for literal in filter(None, extra):  # un texto vacío coincidiría entre cada par de caracteres
        texto = re.sub(re.escape(literal), "[OCULTO]", texto, flags=re.IGNORECASE)
    usuario = os.environ.get("USERNAME") or os.environ.get("USER")
    return re.sub(rf"\b{re.escape(usuario)}\b", "[USUARIO]", texto) if usuario else texto


def recortar(texto, limite):
    texto = str(texto)
    return texto if len(texto) <= limite else texto[:limite] + f"\n… [{len(texto) - limite} caracteres omitidos]"


def bloques(contenido):
    """Normaliza el contenido de un mensaje a una lista de bloques {type, ...}."""
    return [{"type": "text", "text": contenido}] if isinstance(contenido, str) else contenido or []


def linea_de_tiempo(eventos, extra=()):
    """Las herramientas en el orden en que se usaron, con los servidores MCP y las skills que intervinieron."""
    pasos, servidores, skills = [], [], []
    for e in eventos:
        if e.get("type") != "assistant":
            continue
        for b in bloques((e.get("message") or {}).get("content")):
            if b.get("type") != "tool_use" or b.get("name") == "StructuredOutput":
                continue
            nombre, entrada = b.get("name", ""), b.get("input") or {}
            if nombre == "Skill":
                skills.append(entrada.get("skill", "?"))
                pasos.append(f"Skill `{skills[-1]}`")
            elif nombre.startswith("mcp__") or nombre == "call_mcp_tool":  # Claude Code o Antigravity
                _, servidor, herramienta = nombre.split("__", 2) if nombre.startswith("mcp__") else (
                    None, entrada.get("ServerName", "?"), entrada.get("ToolName", "?"))
                servidores.append(servidor)
                pasos.append(f"MCP `{servidor}.{herramienta}`")
            elif nombre in ("Bash", "run_command"):
                comando = (entrada.get("command") or entrada.get("CommandLine") or "").strip().splitlines() or [""]
                pasos.append(f"{nombre} `{ocultar(comando[0], extra)[:90].replace('`', chr(39))}`")
            else:
                pasos.append(f"`{nombre}`")
    if not pasos:
        return []
    def unicos(nombres):
        return ", ".join(f"`{n}`" for n in dict.fromkeys(nombres)) or "ninguno"
    return (["## Línea de tiempo", "",
             f"Servidores MCP: {unicos(servidores)} · Skills: {unicos(skills)} · {len(pasos)} llamadas a herramientas",
             ""] + [f"{i}. {p}" for i, p in enumerate(pasos, 1)] + [""])


def desde_antigravity(sesion):
    """Lleva los pasos de una sesión de Antigravity a la forma de los eventos de Claude Code.

    Antigravity guarda la sesión en fragmentos que pueden cortar un registro a la mitad, así que se unen antes de
    leerlos. Cada resultado de herramienta (GENERIC) sigue, en orden, a la llamada que lo produjo."""
    texto = "".join(f.read_text(encoding="utf-8") for f in sorted((sesion / FRAGMENTOS_DE_ANTIGRAVITY).glob("*.jsonl")))
    registros = [json.loads(l) for l in texto.splitlines() if l.strip()]
    eventos = []
    for r in registros:
        tipo, contenido, cuando = r.get("type"), r.get("content") or "", r.get("created_at", "")
        if tipo == "USER_INPUT":
            solicitud = SOLICITUD.search(contenido)
            eventos.append({"type": "user", "timestamp": cuando,
                            "message": {"content": solicitud.group(1) if solicitud else contenido}})
        elif tipo in ("SYSTEM_MESSAGE", "CHECKPOINT"):
            eventos.append({"type": "user", "timestamp": cuando, "message": {"content": contenido}})
        elif tipo == "GENERIC":
            eventos.append({"type": "user", "message": {"content": [{"type": "tool_result", "content": contenido}]}})
        elif tipo == "PLANNER_RESPONSE":  # el campo thinking queda fuera, como el razonamiento de Claude
            contenidos = [{"type": "text", "text": contenido}] if contenido.strip() else []
            contenidos += [{"type": "tool_use", "name": c.get("name"), "input": c.get("args")}
                           for c in r.get("tool_calls") or []]
            eventos.append({"type": "assistant", "message": {"content": contenidos}})
    return registros, eventos


def a_markdown(eventos, titulo, pedido=None, extra=(), asistente="Claude"):
    lineas, turno = [f"# {titulo}", "", *linea_de_tiempo(eventos, extra)], 0
    if pedido:  # claude -p no emite el pedido inicial como evento
        turno = 1
        lineas += ["## 1. Pedido (claude -p)", "", pedido, ""]
    for e in eventos:
        tipo, mensaje = e.get("type"), e.get("message") or {}
        cuando = e.get("timestamp", "")[:19].replace("T", " ")
        if tipo == "result":
            lineas += ["---", "", f"**Resultado final** · turnos: {e.get('num_turns')} · costo USD: "
                       f"{e.get('total_cost_usd')} · duración: {round((e.get('duration_ms') or 0) / 1000, 1)} s", ""]
            continue
        if tipo not in ("user", "assistant"):
            continue
        for b in bloques(mensaje.get("content")):
            if b.get("type") == "text" and b.get("text", "").strip():
                texto = PEGADO.sub(r"*Texto pegado:*\n\n\1", b["text"]) if tipo == "user" else b["text"]
                if tipo == "user" and (texto.lstrip().startswith("<") or AVISO_DE_LIMITE.match(texto)):
                    continue  # recordatorios y avisos del sistema, no lo que escribió la persona
                generado = next((t for inicio, t in GENERADO_POR_LA_HERRAMIENTA.items()
                                 if tipo == "user" and texto.startswith(inicio)), None)
                if generado:
                    lineas += [f"<details><summary>{generado}</summary>", "", "```markdown", texto.strip(), "```",
                               "</details>", ""]
                    continue
                turno += 1 if tipo == "user" else 0
                quien = f"## {turno}. Pedido" if tipo == "user" else f"**{asistente}:**"
                lineas += [f"{quien} {('· ' + cuando + ' UTC') if cuando and tipo == 'user' else ''}".rstrip(), "",
                           texto.strip(), ""]
            elif b.get("type") == "tool_use":
                argumentos = json.dumps(b.get("input"), ensure_ascii=False, indent=1)
                # Se oculta antes de recortar: un correo cortado a la mitad ya no lo reconoce el patrón.
                lineas += [f"**Herramienta:** `{b.get('name')}`", "", "```json",
                           recortar(ocultar(argumentos, extra), LIMITE_ARGUMENTOS), "```", ""]
            elif b.get("type") == "tool_result":
                contenido = b.get("content")
                texto = "\n".join(c.get("text", "") for c in contenido if isinstance(c, dict)) if isinstance(
                    contenido, list) else str(contenido)
                lineas += ["<details><summary>Resultado de la herramienta</summary>", "", "```text",
                           recortar(ocultar(texto, extra), LIMITE_RESULTADO), "```", "</details>", ""]
    return ocultar("\n".join(lineas), extra)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("origen", type=Path, help="Un .jsonl de Claude Code o la carpeta de una sesión de Antigravity.")
    p.add_argument("destino", type=Path)
    p.add_argument("--titulo", default=None)
    p.add_argument("--pedido", default=None, help="El pedido de una corrida claude -p, que no queda en su salida.")
    p.add_argument("--ocultar", action="append", default=[], metavar="TEXTO",
                   help="Otro texto que se reemplaza por [OCULTO], sin distinguir mayúsculas; por ejemplo, el usuario "
                        "de un correo que aparece sin la @. Se puede repetir.")
    a = p.parse_args()
    if a.origen.is_dir():
        registros, eventos = desde_antigravity(a.origen)
        asistente, cuenta = "Gemini", f"{len(registros)} registros exportados"
    else:
        eventos = [json.loads(l) for l in a.origen.read_text(encoding="utf-8").splitlines() if l.startswith("{")]
        asistente, cuenta = "Claude", f"{len(eventos)} eventos exportados"
    a.destino.parent.mkdir(parents=True, exist_ok=True)
    a.destino.write_text(a_markdown(eventos, a.titulo or a.destino.stem.replace("_", " "), a.pedido, a.ocultar,
                                    asistente), encoding="utf-8")
    print(f"{a.destino.as_posix()}: {cuenta}")


if __name__ == "__main__":
    main()
