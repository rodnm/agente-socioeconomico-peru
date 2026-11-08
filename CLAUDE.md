# Agente de investigación socioeconómica del Perú

Este repo es un agente de investigación: responde preguntas sobre la economía y las condiciones sociales del Perú con datos oficiales, no con lo que el modelo recuerda.

## Fuentes y herramientas

- **BCRP** (series macroeconómicas): servidor MCP `bcrp` (`mcp/server.py`). Primero `buscar_series` para encontrar el código; luego `serie`, `resumen`, `comparar_series` y `graficar_serie`. El recurso `bcrp://serie/{codigo}` describe una serie.

## Reglas

1. **Ninguna cifra de memoria.** Cada número sale de una herramienta MCP o de un script de una skill, y se cita con su fuente: código de serie, periodo y URL del BCRP, o el archivo de `salidas/` que lo contiene.
2. **No hagas cuentas a mano.** Variaciones, promedios, extremos y correlaciones los calcula `resumen` o `comparar_series`.
3. **Si algo falla, dilo.** Si una herramienta da error, no encuentra datos o devuelve algo incompatible con la pregunta, infórmalo en lugar de estimar o inventar.
4. **Asociación no es causalidad.** Si relacionas indicadores, descríbelos como asociaciones y reconoce cuando provienen de distintos niveles de agregación o periodos.
