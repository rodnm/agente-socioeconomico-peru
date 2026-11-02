---
name: verificando-consistencia
description: Contrasta los resultados de las distintas herramientas del agente (skills de la ENAHO, servidor MCP del BCRP e informe final) y detecta inconsistencias entre ellos en salidas/consistencia.md. Úsala después de procesar datos o de armar un informe, o cuando pidan verificar, auditar o comprobar que las cifras coinciden entre fuentes.
allowed-tools: Bash(uv run *), Read
---

# Verificar la consistencia entre herramientas

1. Corre exactamente: `uv run ${CLAUDE_SKILL_DIR}/scripts/verificar.py`
   Si el BCRP no responde, el script marca esas verificaciones como «NO VERIFICABLE» y sigue. Para revisar solo la ENAHO y el informe sin consultar al BCRP, usa `--sin-bcrp`.
2. Lee `salidas/consistencia.md` y responde con el conteo de resultados y cada línea que no sea OK, con su explicación.

## Qué contrasta

| Fuente | Verificación |
|---|---|
| ENAHO | Pobreza nacional con peso de hogar frente a peso de persona; validaciones de la limpieza; la tasa nacional entre la urbana y la rural; los 25 departamentos frente a la referencia de la sesión 16; el mapa frente a los indicadores |
| BCRP | La inflación a 12 meses recalculada desde el índice del IPC vigente (`PN38705PM`, Dic.2021 = 100) frente a la publicada (`PN01273PM`); `resumen` frente a los datos de `serie` |
| Informe | Cada cifra de `informes/informe_final.md` frente a una nueva consulta a sus herramientas |

## Cómo leer el resultado

- **OK**: coinciden dentro de la tolerancia.
- **DIFERENCIA**: no coinciden por una razón conocida, que la tabla explica (por ejemplo, dos ponderadores distintos).
- **FALLA**: no coinciden y no debería pasar. Detente y muéstrala; no corrijas cifras a mano para que coincidan.
- **NO VERIFICABLE**: la fuente no respondió, la serie no tiene datos del periodo o falta un insumo. El detalle dice cuál de los tres. Dilo como limitación; no lo reemplaces por una estimación.
