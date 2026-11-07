# Comparación: Claude Code con y sin MCP y Skills

Las mismas 10 preguntas ([`preguntas.csv`](preguntas.csv): 4 del BCRP, 4 de la ENAHO y 2 mixtas) se hicieron a Claude Code (Sonnet) en dos configuraciones. Cada pregunta corrió en una sesión nueva de `claude -p`, dentro de una copia temporal del proyecto que no incluye `evaluacion/`. Las preguntas y sus respuestas esperadas se fijaron en un commit (`c2f7053`) antes de la primera corrida. Las respuestas esperadas del BCRP salen de la API pública, sin pasar por el servidor MCP ([`verdades.py`](verdades.py)); las de la ENAHO son cifras publicadas por el INEI y la referencia de la sesión 16.

- **Modo A, sin MCP ni Skills.** Herramientas estándar (Bash, Read, Glob, Grep, WebSearch y WebFetch) en una carpeta con solo los zip crudos de la ENAHO. No ve los servidores MCP, las skills, el `CLAUDE.md` del proyecto ni las salidas procesadas.
- **Modo B, con MCP y Skills.** Lo mismo más los servidores `bcrp` y `sbs` y las skills del proyecto.

Las cifras salen de [`metricas.md`](metricas.md), que genera `uv run evaluacion/analizar.py` a partir de [`resultados.csv`](resultados.csv).

## Resultados

| | Modo A | Modo B |
|---|---|---|
| Respuestas correctas | 8 de 10 | 10 de 10 |
| Incorrectas | 2 (e3, m2) | 0 |
| No contestadas o con error | 0 | 0 |
| Tiempo promedio por pregunta | 38.1 s | 22.2 s |
| Turnos promedio | 6.3 | 4.9 |
| Costo total | USD 2.22 | USD 2.30 |

Por tipo de pregunta, los dos modos acertaron las 4 del BCRP. En la ENAHO, A acertó 3 de 4 y B 4 de 4; en las mixtas, A acertó 1 de 2 y B 2 de 2.

**Mejoraron con MCP y Skills:** e3 y m2. **Empeoraron:** ninguna.

## Errores principales

1. **e3, pobreza de Cusco.** El Modo A respondió 16.8 % tomando la cifra de un documento parlamentario que cita al INEI. Es una fuente secundaria: el propio agente dijo que no pudo abrir el informe técnico del INEI. La referencia de la sesión 16 da 18.5 %, y el Modo B obtuvo 18.54 % de los microdatos con `limpiando-enaho`.
2. **m2, pobreza de Lima Metropolitana.** El Modo A respondió 25.7 %, la cifra que el INEI publica para «Lima Metropolitana» entendida como los 43 distritos de la provincia de Lima. La respuesta esperada, 28.2 %, corresponde al dominio 8 de la ENAHO, que incluye al Callao. El propio Modo A mencionó las dos cifras en su interpretación. Este error se debe en parte a la pregunta, que no definió el ámbito.
3. **En el BCRP no hubo diferencia de aciertos.** Las cuatro cifras pedidas están publicadas en notas del BCRP y en la prensa, y el Modo A las encontró con WebSearch, o bajó los datos de la API para calcular el promedio del tipo de cambio. La diferencia está en la fuente: B citó el código de serie, el periodo y la URL de la API en todas sus respuestas, mientras que A respondió dos de las cuatro con una nota de estudios o un resumen informativo del BCRP en lugar de la serie.

## Uso de herramientas

| | Modo A | Modo B |
|---|---|---|
| Corridas con WebSearch o WebFetch | 9 de 10 | 0 de 10 |
| Corridas con un servidor MCP | — | 6 de 10 |
| Corridas con Bash | 3 de 10 | 6 de 10 |

En las preguntas de la ENAHO, el Modo B no invocó las skills: leyó `salidas/indicadores.csv`, que las skills ya habían generado y que su `CLAUDE.md` señala como fuente única. El Modo A, en cambio, respondió las cuatro con cifras publicadas que encontró en la web, aunque tenía los zip de la ENAHO en su carpeta. En e3 la única cifra que encontró venía de una fuente secundaria.

## Interpretación de las preguntas mixtas

Se revisó a mano con el criterio escrito en `preguntas.csv` antes de las corridas: no afirmar causalidad y reconocer que las cifras vienen de niveles de agregación distintos.

| Pregunta | Modo A | Modo B |
|---|---|---|
| m1 | **No cumple.** Dice que la inflación baja «protegió el poder de compra urbano» y la vincula con la baja de la pobreza, y agrega una cifra de 2023 que no se pidió. No distingue el IPC de Lima de la tasa urbana nacional. | **No cumple.** Distingue los niveles de agregación, pero concluye que la pobreza urbana «responde más a ingresos y empleo que a la inflación», una afirmación causal sin datos que la respalden. |
| m2 | **Cumple en parte.** No afirma causalidad, pero no explica la diferencia de naturaleza entre las dos cifras. | **Cumple.** Explica que una es un promedio de cotizaciones diarias y la otra una tasa anual de una encuesta, y presenta cualquier vínculo como una hipótesis no contrastada. |

Las herramientas mejoran las cifras, pero no garantizan una interpretación prudente. La regla 5 del `CLAUDE.md` (asociación no es causalidad) no impidió la conclusión causal de m1 en el Modo B.

## Conclusión

Con MCP y Skills, Claude Code acertó las 10 preguntas, tardó 42 % menos en promedio y citó en todas una fuente primaria y reproducible: el código de serie y la URL del BCRP, o el `id` del indicador de la ENAHO. Sin ellas acertó 8. Los dos errores aparecen justo donde la web no alcanza: una cifra departamental que no figura en fuentes de fácil acceso, y una definición territorial que la búsqueda resolvió de otra manera. En las preguntas del BCRP, con cifras muy difundidas, la mejora no está en el acierto sino en la trazabilidad. El costo fue casi el mismo (USD 2.30 contra 2.22), porque las búsquedas web del Modo A cuestan tanto como las herramientas del Modo B.

Limitaciones del experimento:
- Es una sola corrida por pregunta y modo, así que una diferencia de 2 preguntas no permite afirmar que la mejora sea estadísticamente significativa.
- Las cifras del BCRP son fáciles de encontrar en la web.
- La pregunta m2 debió definir «Lima Metropolitana».

La ablación, que apaga cada herramienta por separado, está en [`ablacion.md`](ablacion.md).
