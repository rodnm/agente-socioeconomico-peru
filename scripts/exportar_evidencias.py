"""Convierte transcripciones de Claude Code (JSONL) en Markdown legible y sin datos sensibles, para evidencias_ia/.

    uv run scripts/exportar_evidencias.py ORIGEN.jsonl evidencias_ia/skills/01_encadenamiento.md [--titulo T]
        [--ocultar TEXTO ...]

Acepta las sesiones que Claude Code guarda en ~/.claude/projects/<proyecto>/<sesión>.jsonl y la salida de
`claude -p --output-format stream-json --verbose`. Empieza con una línea de tiempo de las herramientas usadas, con
los servidores MCP y las skills que intervinieron. Conserva los pedidos, las respuestas, cada llamada a una
herramienta con sus argumentos y un extracto de cada resultado. Oculta rutas personales, el nombre de usuario del
sistema, correos, claves y tokens. Revisen el resultado antes de publicarlo: la redacción automática no reemplaza
una lectura humana.
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


# Mensajes que Claude Code inserta con el rol de la persona: se muestran plegados y no cuentan como pedidos.
GENERADO_POR_CLAUDE_CODE = {
    "Base directory for this skill": "Instrucciones de la skill que cargó Claude Code",
    "This session is being continued from a previous conversation": (
        "Resumen automático de la parte anterior de la sesión (Claude Code compactó el contexto)"),
}
AVISO_DE_LIMITE = re.compile(r"\[(Usage limit reached|Earlier usage-limit notes)")
# Claude Code envuelve lo que la persona pega; sin quitar la envoltura, el pedido parecería un aviso del sistema.
PEGADO = re.compile(r"<pasted_content[^>]*>\n?(.*?)\n?</pasted_content[^>]*>", re.DOTALL)


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
            elif nombre.startswith("mcp__"):
                _, servidor, herramienta = nombre.split("__", 2)
                servidores.append(servidor)
                pasos.append(f"MCP `{servidor}.{herramienta}`")
            elif nombre == "Bash":
                comando = ocultar((entrada.get("command") or "").strip().splitlines()[0], extra)[:90].replace("`", "'")
                pasos.append(f"Bash `{comando}`")
            else:
                pasos.append(f"`{nombre}`")
    if not pasos:
        return []
    def unicos(nombres):
        return ", ".join(f"`{n}`" for n in dict.fromkeys(nombres)) or "ninguno"
    return (["## Línea de tiempo", "",
             f"Servidores MCP: {unicos(servidores)} · Skills: {unicos(skills)} · {len(pasos)} llamadas a herramientas",
             ""] + [f"{i}. {p}" for i, p in enumerate(pasos, 1)] + [""])


def a_markdown(eventos, titulo, pedido=None, extra=()):
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
                generado = next((t for inicio, t in GENERADO_POR_CLAUDE_CODE.items()
                                 if tipo == "user" and texto.startswith(inicio)), None)
                if generado:
                    lineas += [f"<details><summary>{generado}</summary>", "", "```markdown", texto.strip(), "```",
                               "</details>", ""]
                    continue
                turno += 1 if tipo == "user" else 0
                quien = f"## {turno}. Pedido" if tipo == "user" else "**Claude:**"
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
    p.add_argument("origen", type=Path)
    p.add_argument("destino", type=Path)
    p.add_argument("--titulo", default=None)
    p.add_argument("--pedido", default=None, help="El pedido de una corrida claude -p, que no queda en su salida.")
    p.add_argument("--ocultar", action="append", default=[], metavar="TEXTO",
                   help="Otro texto que se reemplaza por [OCULTO], sin distinguir mayúsculas; por ejemplo, el usuario "
                        "de un correo que aparece sin la @. Se puede repetir.")
    a = p.parse_args()
    eventos = [json.loads(l) for l in a.origen.read_text(encoding="utf-8").splitlines() if l.startswith("{")]
    a.destino.parent.mkdir(parents=True, exist_ok=True)
    a.destino.write_text(a_markdown(eventos, a.titulo or a.destino.stem.replace("_", " "), a.pedido, a.ocultar),
                         encoding="utf-8")
    print(f"{a.destino.as_posix()}: {len(eventos)} eventos exportados")


if __name__ == "__main__":
    main()
