---
name: verificando-consistencia
description: Contrasta los resultados de las distintas herramientas del agente (skills de la ENAHO, servidor MCP del BCRP e informe final) y detecta inconsistencias entre ellos en salidas/consistencia.md. Úsala después de procesar datos o de armar un informe, o cuando pidan verificar, auditar o comprobar que las cifras coinciden entre fuentes.
allowed-tools: Bash(uv run *), Read
---

# Verificar la consistencia entre herramientas

1. Corre exactamente: `uv run ${CLAUDE_SKILL_DIR}/scripts/verificar.py`
   Si el BCRP o la SBS no responden, el script marca esas verificaciones como «NO VERIFICABLE» y sigue. Para revisar solo la ENAHO y el informe sin consultar al BCRP, usa `--sin-bcrp`.
2. Lee `salidas/consistencia.md` y responde con el conteo de resultados y cada línea que no sea OK, con su explicación.

## Qué contrasta

| Fuente | Verificación |
|---|---|
| ENAHO | Pobreza nacional con peso de hogar frente a peso de persona; validaciones de la limpieza; la tasa nacional entre la urbana y la rural; los 25 departamentos que exige la consigna y, frente al informe técnico del INEI (Cuadro III.1, p. 220), los 24 departamentos con cifra publicada, Lima Metropolitana y Lima provincias. Lima (15) queda fuera de esa comparación porque el INEI no publica una cifra del departamento en conjunto; el mapa frente a los indicadores |
| BCRP | La inflación a 12 meses recalculada desde el índice del IPC vigente (`PN38705PM`, Dic.2021 = 100) frente a la publicada (`PN01273PM`); `resumen` frente a los datos de `serie` |
| BCRP y SBS | La morosidad bancaria de cada diciembre de 2020 a 2024: `PN07746EM` del BCRP, «Cartera atrasada neta / Colocaciones netas (%) - Empresas Bancarias», frente al B-2401 de la SBS, «Créditos Atrasados (criterio SBS) / Créditos Directos». Informa la diferencia absoluta máxima y queda en DIFERENCIA, porque las definiciones no son iguales |
| Informe | Cada cifra de `informes/informe_final.md` frente a una nueva consulta a sus herramientas |

## Cómo leer el resultado

- **OK**: coinciden dentro de la tolerancia.
- **DIFERENCIA**: no coinciden por una razón conocida, que la tabla explica (por ejemplo, dos ponderadores distintos).
- **FALLA**: no coinciden y no debería pasar. Detente y muéstrala; no corrijas cifras a mano para que coincidan.
- **NO VERIFICABLE**: la fuente no respondió, la serie no tiene datos del periodo o falta un insumo. El detalle dice cuál de los tres. Dilo como limitación; no lo reemplaces por una estimación.
