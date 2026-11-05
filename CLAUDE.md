# Agente de investigación socioeconómica del Perú

Este repo es un agente de investigación: responde preguntas sobre la economía y las condiciones sociales del Perú con datos oficiales, no con lo que el modelo recuerda.

## Fuentes y herramientas

- **BCRP** (series macroeconómicas): servidor MCP `bcrp` (`mcp/server.py`). Primero `buscar_series` para encontrar el código; luego `serie`, `resumen`, `comparar_series` y `graficar_serie`. El recurso `bcrp://serie/{codigo}` describe una serie y el prompt `interpretar_indicador` guía su lectura.
- **SBS** (sistema financiero): servidor MCP `sbs` ([mcp-sbs-peru](https://github.com/rodnm/mcp-sbs-peru)), con boletines oficiales de bancos, cajas, AFP y seguros: `indicadores` (morosidad, ROE, liquidez), `ranking`, `reporte`.
- **ENAHO 2020-2024** (INEI, microdatos de hogares): skills en `.claude/skills/`.
  - `descargando-enaho` baja los módulos 34 y 02 (2020 a 2024).
  - `limpiando-enaho` une, filtra residentes, pondera, valida contra metas oficiales del INEI y escribe `salidas/indicadores.csv`.
  - `graficando-enaho` grafica la pobreza por área, sexo, edad, departamento y la serie temporal 2020-2024.
  - `mapeando-enaho` elabora mapas con límites oficiales del IGN para 25 departamentos y 26 ámbitos (Lima desagregada).
- **Informe y control**: `informando-peru` arma `informes/informe_final.md` con cifras trazables; `verificando-consistencia` contrasta las herramientas entre sí.

## Reglas

1. **Ninguna cifra de memoria.** Cada número sale de una herramienta MCP o de un script de una skill, y se cita con su fuente: código de serie, periodo y URL del BCRP, boletín de la SBS, o el `id` de `salidas/indicadores.csv`.
2. **No hagas cuentas a mano.** Variaciones, promedios, extremos y correlaciones los calcula `resumen` o `comparar_series`; las tasas de pobreza, las skills de la ENAHO, siempre ponderadas.
3. **Si algo falla, dilo.** Si una herramienta da error, no encuentra datos o devuelve algo incompatible con la pregunta, infórmalo en lugar de estimar o inventar. El BCRP a veces responde una página anti-bots: reintenta una vez y, si persiste, decláralo como limitación.
4. **Si la pregunta es ambigua** (sin periodo, sin indicador claro o con un lugar que no existe), pide la aclaración o explicita el supuesto que tomas antes de responder.
5. **Asociación no es causalidad.** Si relacionas indicadores, descríbelos como asociaciones y reconoce cuando provienen de distintos niveles de agregación o periodos.
