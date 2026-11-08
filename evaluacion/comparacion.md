# Comparación: Claude Code con y sin MCP y Skills (evaluación v2)

Las mismas 10 preguntas de [`preguntas.csv`](preguntas.csv) (4 del BCRP, 4 de la ENAHO y 2 mixtas) se hicieron a Claude Code en dos configuraciones. Las preguntas y sus respuestas esperadas se fijaron en el commit `c2f7053`, antes de la primera corrida, y no cambiaron desde entonces. La procedencia de cada respuesta esperada está en [`procedencia_de_las_verdades.md`](procedencia_de_las_verdades.md).

La v2 se corrió el 7 de noviembre de 2026 sobre el proyecto final, después de registrar el aislamiento en el commit `3c08124`. Cada pregunta corrió en una sesión nueva de `claude -p`, con el mismo modelo, dentro de una copia temporal del proyecto que no incluye `evaluacion/`.

**Aislamiento.** Las 60 filas de [`resultados.csv`](resultados.csv) registran `aislamiento = claude_md_desactivado+setting_sources_project_local`:
- `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1` apaga todo `CLAUDE.md`;
- `--setting-sources project,local` deja fuera la configuración del usuario, y `--strict-mcp-config`, sus servidores MCP;
- los modos cuya copia incluye el `CLAUDE.md` del proyecto lo reciben con `--append-system-prompt` (docstring de [`evaluar.py`](evaluar.py)).

La v1 corrió sin este aislamiento: el `CLAUDE.md` global, las reglas y el estilo de salida del usuario se aplicaron en todos los modos ([`v1/README.md`](v1/README.md)).

Los dos modos:
- **Modo A, sin MCP ni Skills.** Herramientas estándar (Bash, Read, Glob, Grep, WebSearch y WebFetch) en una carpeta con los zip de los módulos 34 y 02 de la ENAHO 2024 y un GeoJSON departamental. No ve servidores MCP, skills, ningún `CLAUDE.md` ni salidas procesadas.
- **Modo B, con MCP y Skills.** La copia del proyecto con los servidores `bcrp` y `sbs`, las skills, sus salidas y el `CLAUDE.md` del proyecto.

Las cifras salen de [`metricas.md`](metricas.md), que genera `uv run evaluacion/analizar.py`, y se comprobaron contra `resultados.csv`.

## Resultados

| | Modo A | Modo B |
|---|---|---|
| Respuestas correctas | 9 de 10 | 10 de 10 |
| Incorrectas | 1 (m2) | 0 |
| No contestadas o con error | 0 | 0 |
| Tiempo promedio por pregunta | 22.9 s | 18.8 s |
| Turnos promedio | 4.8 | 4.5 |
| Costo total | USD 0.52 | USD 0.57 |

Por tipo de pregunta, los dos modos acertaron las 4 del BCRP y las 4 de la ENAHO. En las mixtas, A acertó 1 de 2 y B, 2 de 2.

**Mejoró con MCP y Skills:** m2. **Empeoró:** ninguna.

## Errores principales

1. **m2, pobreza de Lima Metropolitana.** Es el único error del Modo A y depende de cómo se defina el ámbito. Se explica en la sección «m2 y la definición de Lima Metropolitana».
2. **Aciertos sin fuente primaria.** La calificación mide la cifra, no su procedencia.
   - En b1, el Modo A no usó ninguna herramienta y declaró que la cifra era «de memoria, no verificada en la serie del BCRP».
   - Sus cuatro respuestas de la ENAHO salen de notas de prensa o de fuentes secundarias. En las cuatro dice que no abrió o no consultó el informe del INEI.
   - El Modo B citó en las 10 el código de serie y la URL de la API del BCRP, o el `id` del indicador en `salidas/indicadores.csv`.
3. **e3, Cusco, ya no falla en el Modo A.** En la v1 respondió 16.8 % con un documento parlamentario. En la v2 encontró 18.5 % en Infobae y el IPE, fuentes secundarias que coinciden con el Cuadro III.1 del INEI (p. 220). Su carpeta es la misma en las dos versiones, así que el cambio refleja otra búsqueda web, no el proyecto.

## Uso de herramientas

| | Modo A | Modo B |
|---|---|---|
| Corridas con WebSearch o WebFetch | 8 de 10 | 0 de 10 |
| Corridas con un servidor MCP | — | 6 de 10 |
| Corridas con Bash | 3 de 10 | 5 de 10 |
| Corridas sin ninguna herramienta | 1 de 10 (b1) | 0 de 10 |
| Corridas con la herramienta Skill | 0 de 10 | 0 de 10 |

Como en la v1, el Modo B no invocó las skills en las preguntas: leyó `salidas/indicadores.csv`, que las skills ya habían generado. Tampoco usó `comparar_series` en ninguna de las 10.

**Sobre `referencias/`.** La copia del Modo B incluye `referencias/inei_pobreza_2024.csv`, la tabla publicada del INEI, y `salidas/validacion.txt`, con las metas del INEI. Leerlas es citar la fuente oficial, no una fuga: las respuestas esperadas de la ENAHO son cifras publicadas por el INEI. Ninguna respuesta de la v2 cita `referencias/`. La de e2 cita `validacion.txt`, y las demás cifras de la ENAHO del Modo B salen de `salidas/indicadores.csv`, la réplica con microdatos.

## m2 y la definición de «Lima Metropolitana»

La respuesta esperada, 28.2 % con una tolerancia de 0.1, es la cifra del INEI para «Lima Metropolitana y Prov. Const. del Callao», el dominio 8 de la ENAHO (Cuadro III.1, p. 219). El mismo cuadro publica 27.6 % para Lima Metropolitana sin el Callao, es decir, la provincia de Lima (p. 220). La primera cifra de m2, el tipo de cambio, fue correcta en todos los modos que respondieron.

| Modo | Segunda cifra | De dónde salió |
|---|---|---|
| B | 28.21 | `indicadores.csv`, `pobreza_lima_metropolitana` (dominio 8, con el Callao); menciona además 27.58 sin el Callao |
| A | 27.60 | Notas de prensa (Bloomberg Línea, Canal N); no pudo abrir la nota del INEI |
| solo-mcp | 27.60 | Notas de prensa (Canal N, América TV); no pudo abrir la nota del INEI y la presenta como «igual al promedio nacional» |
| solo-skills | 27.58 | `indicadores.csv`, `pobreza_lima_metropolitana_provincia` (provincia de Lima, sin el Callao); menciona 28.21 con el Callao |
| sin-propia | 27.58 | El mismo `id`; menciona 28.21 con el Callao |

- **solo-skills y sin-propia** eligieron de forma explícita Lima Metropolitana sin el Callao, que también es una cifra oficial del INEI: su réplica, 27.58, coincide con el 27.6 publicado.
- **A y solo-mcp** dieron 27.6, que coincide con esa cifra y también con la tasa nacional. La tomaron de la prensa, así que sus respuestas no permiten saber a qué ámbito corresponde.
- **La calificación se mantiene.** El registro previo fijó 28.2 ± 0.1, y no se recalifica después de ver los resultados.
- **Limitación declarada.** La pregunta no definió «Lima Metropolitana», y las dos lecturas tienen una cifra oficial. Desde que el proyecto analiza Lima desagregada (Fase 1), `indicadores.csv` ofrece los dos ámbitos, así que el acierto en m2 depende de qué lectura elija el agente.

## Interpretación de las preguntas mixtas

Se revisó a mano con el `criterio_interpretacion` de `preguntas.csv`, escrito antes de las corridas.

| Pregunta | Modo A | Modo B |
|---|---|---|
| m1 | **No cumple.** Dice que la inflación baja «probablemente ayudó a que la pobreza urbana bajara», una afirmación causal, y no distingue el IPC de Lima de la tasa urbana nacional. | **Cumple en parte.** La presenta como «una asociación descriptiva» y no causal, y distingue Lima del ámbito urbano nacional, pero no dice que una cifra es de un mes y la otra una tasa anual de una encuesta. |
| m2 | **Cumple en parte.** Niega una relación causal medible, pero no explica la diferencia de naturaleza entre las cifras y afirma sin datos que la pobreza «depende más del empleo, los ingresos y los precios de los alimentos». | **Cumple.** Distingue un dato «macro diario» de «microdatos anuales de hogares» y los lee como contexto simultáneo, «sin inferir causalidad». |

La marca automática `lenguaje_causal` de `metricas.md` no sirve para calificar. Marca m1 B, que escribe «no una relación causal», y no marca m1 A, que sí atribuye una causa.

## De la v1 a la v2

| | A v1 | A v2 | B v1 | B v2 |
|---|---|---|---|---|
| Respuestas correctas | 8 de 10 | 9 de 10 | 10 de 10 | 10 de 10 |
| Errores | e3 (16.8), m2 (25.7) | m2 (27.6) | ninguno | ninguno |
| Tiempo promedio | 38.1 s | 22.9 s | 22.2 s | 18.8 s |
| Turnos promedio | 6.3 | 4.8 | 4.9 | 4.5 |
| Costo total | USD 2.22 | USD 0.52 | USD 2.30 | USD 0.57 |
| Corridas con web | 9 | 8 | 0 | 0 |
| Corridas con MCP | — | — | 6 | 6 |
| Interpretación de m1 | no cumple | no cumple | no cumple | cumple en parte |
| Interpretación de m2 | cumple en parte | cumple en parte | cumple | cumple |

- **La diferencia mezcla dos cambios.** Entre las dos versiones cambió el proyecto, con las fases 1 a 5 (tabla del INEI, Lima desagregada, límites del IGN, referencias APA y ENAHO 2020–2024), y se agregó el aislamiento. Con una sola corrida por versión no se pueden separar.
- **El Modo A refleja, sobre todo, el aislamiento.** Recibió en las dos versiones la misma carpeta y las mismas herramientas (función `preparar` de `evaluar.py`). Lo que cambió para él es que ya no carga la configuración global del usuario.
- **El costo bajó en los dos modos.** En el Modo A, el costo bajó 77 % y el tiempo, 40 %; en el Modo B, 75 % y 15 %. La caída es coherente con menos contexto en cada sesión, pero los CSV no registran tokens, así que no está medida.
- **Lo que cambió en las respuestas** fue e3 en A, por la búsqueda web, y la interpretación de m1 en B, que dejó de afirmar una causa. Con una corrida no se puede saber si esto último se debe al aislamiento o a la variación entre corridas.
- **El 25.7 % de la v1 en m2.** El Modo A de la v1 lo atribuyó al Gráfico 4.7 del informe del INEI, y [`v1/comparacion.md`](v1/comparacion.md) lo presentó como la cifra de los 43 distritos de Lima. No coincide con el 27.6 % que el Cuadro III.1 (p. 220) publica para ese ámbito. En el Gráfico 4.7 (p. 72), el 25.7 % corresponde a Amazonas; Lima Metropolitana figura con 27.6 %.

## Conclusión

Con MCP y Skills, Claude Code acertó las 10 preguntas; sin ellos, 9. La única diferencia es m2, que depende de cómo se defina Lima Metropolitana. Las cifras del BCRP y de la ENAHO están publicadas, y el Modo A las encontró, pero en la prensa o en fuentes secundarias, y una la dio de memoria. El Modo B citó en todas una fuente primaria y reproducible: el código de serie y la URL del BCRP, o el `id` del indicador de la ENAHO. Tardó 18 % menos en promedio y costó 10 % más (USD 0.57 contra 0.52). En las mixtas interpretó con más prudencia que A: a diferencia de la v1, ninguna de sus respuestas afirmó una causa.

Limitaciones del experimento:
- Es una sola corrida por pregunta y modo, así que una diferencia de una pregunta no es estadísticamente significativa.
- Las cifras del BCRP y las nacionales de la ENAHO son fáciles de encontrar en la web.
- La pregunta m2 debió definir «Lima Metropolitana».
- La columna `herramientas` registra qué herramientas se usaron, no qué archivos se leyeron.

La ablación y la robustez están en [`ablacion.md`](ablacion.md). Los análisis de la v1 se conservan sin cambios en [`v1/`](v1/).
