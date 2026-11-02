"""Convierte transcripciones de Claude Code (JSONL) en Markdown legible y sin datos sensibles, para evidencias_ia/.

    uv run scripts/exportar_evidencias.py ORIGEN.jsonl evidencias_ia/skills/01_encadenamiento.md [--titulo T]

Acepta las sesiones que Claude Code guarda en ~/.claude/projects/<proyecto>/<sesión>.jsonl y la salida de
`claude -p --output-format stream-json --verbose`. Conserva los pedidos, las respuestas, cada llamada a una
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


def ocultar(texto):
    for patron, reemplazo in OCULTAR:
        texto = patron.sub(reemplazo, texto)
    usuario = os.environ.get("USERNAME") or os.environ.get("USER")
    return re.sub(rf"\b{re.escape(usuario)}\b", "[USUARIO]", texto) if usuario else texto


def recortar(texto, limite):
    texto = str(texto)
    return texto if len(texto) <= limite else texto[:limite] + f"\n… [{len(texto) - limite} caracteres omitidos]"


def bloques(contenido):
    """Normaliza el contenido de un mensaje a una lista de bloques {type, ...}."""
    return [{"type": "text", "text": contenido}] if isinstance(contenido, str) else contenido or []


def a_markdown(eventos, titulo, pedido=None):
    lineas, turno = [f"# {titulo}", ""], 0
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
                if tipo == "user" and b["text"].lstrip().startswith("<"):
                    continue  # recordatorios y avisos del sistema, no lo que escribió la persona
                if tipo == "user" and b["text"].startswith("Base directory for this skill"):
                    lineas += ["<details><summary>Instrucciones de la skill que cargó Claude Code</summary>", "",
                               "```markdown", b["text"].strip(), "```", "</details>", ""]
                    continue
                turno += 1 if tipo == "user" else 0
                quien = f"## {turno}. Pedido" if tipo == "user" else "**Claude:**"
                lineas += [f"{quien} {('· ' + cuando) if cuando and tipo == 'user' else ''}".rstrip(), "",
                           b["text"].strip(), ""]
            elif b.get("type") == "tool_use":
                argumentos = json.dumps(b.get("input"), ensure_ascii=False, indent=1)
                lineas += [f"**Herramienta:** `{b.get('name')}`", "", "```json", recortar(argumentos, LIMITE_ARGUMENTOS),
                           "```", ""]
            elif b.get("type") == "tool_result":
                contenido = b.get("content")
                texto = "\n".join(c.get("text", "") for c in contenido if isinstance(c, dict)) if isinstance(
                    contenido, list) else str(contenido)
                lineas += ["<details><summary>Resultado de la herramienta</summary>", "", "```text",
                           recortar(texto, LIMITE_RESULTADO), "```", "</details>", ""]
    return ocultar("\n".join(lineas))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("origen", type=Path)
    p.add_argument("destino", type=Path)
    p.add_argument("--titulo", default=None)
    p.add_argument("--pedido", default=None, help="El pedido de una corrida claude -p, que no queda en su salida.")
    a = p.parse_args()
    eventos = [json.loads(l) for l in a.origen.read_text(encoding="utf-8").splitlines() if l.startswith("{")]
    a.destino.parent.mkdir(parents=True, exist_ok=True)
    a.destino.write_text(a_markdown(eventos, a.titulo or a.destino.stem.replace("_", " "), a.pedido),
                         encoding="utf-8")
    print(f"{a.destino.as_posix()}: {len(eventos)} eventos exportados")


if __name__ == "__main__":
    main()
