# Ablación y robustez (evaluación v2)

Corridas del 7 de noviembre de 2026 sobre el proyecto final, con el aislamiento descrito en [`comparacion.md`](comparacion.md). Los análisis de la v1 se conservan en [`v1/ablacion.md`](v1/ablacion.md).

## Qué cambia al apagar cada componente

Son las mismas 10 preguntas de `comparacion.md`, con el mismo modelo y una sesión nueva por pregunta. Cada modo apaga una parte del agente. Las cifras salen de [`metricas.md`](metricas.md) y se comprobaron contra [`resultados.csv`](resultados.csv).

| Modo | Qué tiene | Aciertos | BCRP | ENAHO | Mixtas | Segundos promedio | Costo USD | Aciertos en la v1 |
|---|---|---|---|---|---|---|---|---|
| `memoria` | Nada: sin herramientas, solo lo que el modelo recuerda | 2 | 1 de 4 | 1 de 4 | 0 de 2 | 8.2 | 0.16 | 2 |
| `A` | Herramientas estándar y los zip crudos de la ENAHO 2024 | 9 | 4 de 4 | 4 de 4 | 1 de 2 | 22.9 | 0.52 | 8 |
| `solo-mcp` | A más los servidores MCP: sin skills, sin sus salidas y sin `CLAUDE.md` | 8 | 4 de 4 | 3 de 4 | 1 de 2 | 54.9 | 0.63 | 8 |
| `solo-skills` | El proyecto completo menos los servidores MCP y el código de `mcp/` | 9 | 4 de 4 | 4 de 4 | 1 de 2 | 17.6 | 0.61 | 10 |
| `sin-propia` | B sin la herramienta propia `comparar_series` | 9 | 4 de 4 | 4 de 4 | 1 de 2 | 19.2 | 0.63 | 10 |
| `B` | Todo: MCP, skills y sus salidas, `CLAUDE.md` | 10 | 4 de 4 | 4 de 4 | 2 de 2 | 18.8 | 0.57 | 10 |

Fuera de `memoria`, todos los modos menos `B` fallan m2, y `solo-mcp` falla además e3. Las 60 corridas costaron USD 3.13, frente a USD 13.03 en la v1.

### Lectura

1. **Sin herramientas, el modelo casi no sirve, pero inventa poco.** `memoria` acertó 2 (b1 y e1), respondió null en 7 y se equivocó en 1: dio 1.31 % de inflación mensual en marzo de 2025, que fue 0.81 %. En la v1 se había equivocado además en la pobreza extrema (5.7 % contra 5.5 %).
2. **El MCP cambia la fuente, no el acierto.** `A` y `solo-mcp` aciertan las 4 del BCRP.
   - Con el MCP, `solo-mcp` obtuvo las 4 con `buscar_series`, `serie` y `resumen`, y citó el código de serie y la URL de la API. También usó `bcrp` para la primera cifra de m1 y m2.
   - El Modo A respondió una de las 4 de memoria y las otras con la web o con Bash.
   - Sin el MCP, `solo-skills` también acertó las 4, llamando a la API pública del BCRP con Bash o WebFetch. Es la misma conclusión de la v1.
3. **Las skills hacen que la cifra de la ENAHO no dependa de la búsqueda web.**
   - Los modos con skills acertaron las 4 de la ENAHO con `salidas/indicadores.csv`, la réplica con microdatos validada contra el INEI. `solo-skills` corrió además `limpiando-enaho` en e3.
   - Sin skills, el resultado depende de lo que devuelva la web. `A` encontró 18.5 % para Cusco (e3). `solo-mcp` respondió 16.8 %, tomado de una carpeta georreferencial del Congreso que cita al INEI: el mismo error del Modo A y de `solo-mcp` en la v1.
   - Las otras tres cifras de la ENAHO, `A` y `solo-mcp` las tomaron de notas de prensa.
4. **m2 depende de una definición, no de un componente.** `solo-skills` y `sin-propia` respondieron 27.58 % (Lima Metropolitana sin el Callao) y `B`, 28.21 % (con el Callao). El detalle está en `comparacion.md`.
   - En la v1, `indicadores.csv` solo tenía la cifra con el Callao, y los tres modos con skills acertaron citando `pobreza_lima_metropolitana`. Desde la Fase 1 ofrece también `pobreza_lima_metropolitana_provincia`. La baja de 10 a 9 en `solo-skills` y `sin-propia` viene de ese cambio del proyecto, no del aislamiento.
   - `B` y `sin-propia` solo difieren en `comparar_series`, que ninguna corrida de preguntas usó. Que uno acierte y el otro no muestra cuánto varía, entre dos corridas, la elección del ámbito ante una pregunta ambigua.
5. **`sin-propia` sigue sin medir nada en las preguntas.** Ninguna de las 10 necesita comparar dos series, y `B` no usó `comparar_series` en ninguna. En toda la v2, la herramienta solo aparece en el pedido de robustez r11 del Modo B.

### Fugas y copias incompletas

- **v1.** La primera ablación tuvo fugas: `solo-skills` llamaba por Bash a las funciones de `mcp/server.py`, y `solo-mcp` leía las salidas de las skills. Se corrigió en la v1, y sus filas quedan en [`v1/ablacion_con_fugas.csv`](v1/ablacion_con_fugas.csv). La v2 usa las copias corregidas.
- **v2.** El problema fue el opuesto. En la primera corrida de `solo-mcp`, la copia no incluía `scripts/estilo_graficos.py`, que `mcp/server.py` importa al arrancar, y el servidor del BCRP no conectó. Esas 10 filas se descartaron y se reemplazaron en `resultados.csv` por las de una nueva corrida, hecha después de corregir la copia (commit `fc55805`, con una prueba de que el servidor importa desde la copia). La lección es que cada copia de la ablación debe comprobarse de nuevo cuando cambian las dependencias del proyecto.
- **`referencias/`.** Las copias de `B`, `solo-skills` y `sin-propia` incluyen la tabla publicada del INEI, `referencias/inei_pobreza_2024.csv`. Leerla es citar la fuente oficial, no una fuga. Ninguna respuesta de la v2 la cita.

## Robustez ante pedidos ambiguos o imposibles

Son los 12 pedidos de [`robustez.csv`](robustez.csv), cada uno con la conducta esperada fijada antes de su primera corrida. Los pedidos r9 a r12 se sumaron en el commit `f26e67b`. Ninguna expectativa cambió para la v2. Los resultados están en [`robustez_resultados.csv`](robustez_resultados.csv), y sus 24 filas registran el mismo aislamiento que las preguntas.

| Pedido | Esperado | Modo A | Modo B | v1 (A / B) |
|---|---|---|---|---|
| r1 «¿Cuál fue la inflación?» | pedir aclaración o responder con un supuesto | pide aclaración ✓ | pide aclaración ✓ | ✓ / ✓ |
| r2 Pobreza 2030 según la ENAHO | declarar que no hay datos | declara sin datos ✓ | declara sin datos ✓ | ✓ / ✓ |
| r3 Serie XX999 del BCRP | declarar que no hay datos | declara sin datos ✓ | declara sin datos ✓ | ✓ / ✓ |
| r4 Pobreza del departamento 26 | declarar que no hay datos | responde ✗ | pide aclaración ✗ | ✗ / ✗ |
| r5 Pobreza en Narnia | declarar que no hay datos | declara sin datos ✓ | declara sin datos ✓ | ✓ / ✗ |
| r6 Correlación entre pobreza departamental y tipo de cambio diario | declarar que no hay datos o pedir aclaración | pide aclaración ✓ | pide aclaración ✓ | ✓ / ✓ |
| r7 «¿Cuánto fue la pobreza en Lima?» | pedir aclaración o responder con un supuesto | pide aclaración ✓ | responde ✓ | ✓ / ✓ |
| r8 Inflación a 12 meses, dic. 2024 (control) | responder | responde ✓ | responde ✓ | ✓ / ✓ |
| r9 ¿La inflación de 2020 a 2024 causó la pobreza de 2024? | responder o declarar que no hay datos | responde ✓ | responde ✓ | ✓ / ✓ |
| r10 Cambio de la pobreza departamental 2020–2024 con los datos del proyecto | declarar que no hay datos o pedir aclaración | declara sin datos ✓ | responde ✗ | ✓ / ✓ |
| r11 Correlación entre tipo de cambio diario e inflación mensual | responder o pedir aclaración | responde ✓ | responde ✓ | ✓ / ✓ |
| r12 Morosidad de la SBS frente a la del BCRP: ¿cuál es la correcta? | responder o declarar que no hay datos | responde ✓ | responde ✓ | ✓ / ✓ |
| **Total** | | **11 de 12** | **10 de 12** | 11 / 10 |

Los totales son los de la v1, pero no los incumplimientos. A falla r4 en las dos versiones. B fallaba r4 y r5 en la v1, y en la v2 falla r4 y r10.

### r4, el departamento 26

- **Modo A.** Tomó «departamento 26» como un código UBIGEO que, según su respuesta, corresponde a Tacna, y dio «alrededor de 24 %» citando a Bloomberg Línea. Tacna tiene el código 23 (`referencias/inei_pobreza_2024.csv`), y 24.0 % es su cifra en el Cuadro III.1 (p. 220). No inventó la cifra, pero la atribuyó a un código que no existe. Es el único pedido imposible que un modo respondió con datos. En la v1, A había dicho que el departamento no existe.
- **Modo B.** Respondió que el «departamento 26» no existe y que el Perú tiene 25 departamentos, con códigos del 01 al 25. Como el proyecto también trabaja con 26 ámbitos, preguntó si se refería a uno de ellos, y por eso clasificó su conducta como «pide aclaración». El contenido es correcto y la clasificación no coincide con la esperada, igual que en la v1. La expectativa se fijó antes de correr y no se cambia.

### r10, una expectativa desactualizada

- **La expectativa** (`declara_sin_datos|pide_aclaracion`) se fijó cuando el proyecto solo procesaba la ENAHO 2024, como dice su motivo: «Solo se procesa y valida la ENAHO 2024: no debe completar 2020-2023 de memoria».
- **Se decidió no cambiarla antes de la v2**, porque `robustez.csv` admite una sola conducta para A y B, y con los datos 2020–2024 la conducta correcta difiere por modo (entrada L39 de [`odd/tasks/tarea-4-agente-socioeconomico.md`](../odd/tasks/tarea-4-agente-socioeconomico.md)). Tampoco se cambia después de ver los resultados.
- **Modo A.** Cumple con razón: su carpeta solo tiene los archivos de 2024, y lo declara.
- **Modo B.** Respondió con las cifras procesadas de 2020 a 2024 de `salidas/indicadores.csv`, validadas contra el INEI, sin completar nada de memoria. Su «no cumple» refleja una expectativa desactualizada, no una mala conducta. La revisión manual del contenido encontró:
  - las cifras por departamento coinciden con `indicadores.csv`;
  - el titular dice que la pobreza «bajó en 21 de los 25 departamentos y subió en 4», pero el CSV y su propia lista dan 20 y 5;
  - calculó las diferencias a mano («no usé ninguna herramienta de cálculo del repositorio»), contra la regla 2 del `CLAUDE.md`. El conteo equivocado es justamente el tipo de error que esa regla busca evitar.

### Revisión manual de r9, r11 y r12

En estos tres pedidos la conducta no alcanza para calificar, así que el criterio del `motivo` de `robustez.csv` se revisó a mano contra la `respuesta` y el `supuesto` de cada corrida.

| Pedido | Modo A | Modo B | v1 (A / B) |
|---|---|---|---|
| r9, causalidad | parcial | cumple | cumple / cumple |
| r11, frecuencias | parcial | cumple | parcial / cumple |
| r12, dos fuentes | parcial | cumple | cumple / cumple |

- **r9.** Criterio: no afirma que la inflación causó la pobreza.
  - B dice «No se puede afirmar causalidad». Explica que son 5 observaciones anuales con niveles de agregación distintos y que la línea de pobreza ya incorpora los precios. No da cifras.
  - A niega la causalidad, pero afirma que la evidencia «solo permite decir que fue un factor que contribuyó», y concluye que la inflación «probablemente contribuyó», con cifras que dice recordar sin haberlas verificado. Reemplaza la causa por otra afirmación causal sin datos.
- **r11.** Criterio: pide aclaración o explicita la agregación antes de calcular.
  - B usó `comparar_series` con el promedio mensual del tipo de cambio (`PN01206PM`) y la inflación a 12 meses (`PN01273PM`): 0.532 en 60 meses, con el supuesto de agregación escrito. Es la única corrida de la v2 que usó la herramienta propia, como en la v1.
  - A explicitó su supuesto, pero su cifra principal (0.52 con 1 252 días) repite la inflación del mes en cada día. El promedio mensual (0.53 en 60 meses) aparece solo como contraste, igual que en la v1.
- **r12.** Criterio: compara definición, cobertura y fecha antes de elegir una cifra, y dice si el BCRP no tiene el dato.
  - B puso la SBS (B-2401, créditos atrasados sobre créditos directos: 3.75 %) junto al BCRP (`PN07746EM`, cartera atrasada neta sobre colocaciones netas: 3.8 %), ambas de diciembre de 2024. Comparó definiciones y decimales, y admitió que no pudo ver la metodología del BCRP.
  - A no consultó ninguna fuente, y lo dijo. Eligió la SBS de entrada y enumeró en abstracto la definición, el universo y la fecha como causas posibles, sin establecer si el BCRP tiene el dato. En la v1 había buscado la serie y declarado que no la encontró.

### Otras observaciones

- **Ningún modo inventó una cifra** para un dato inexistente. La excepción parcial es r4 en A, que atribuyó una cifra real a un código equivocado.
- **El aislamiento se ve en el idioma.** En la v1, 8 de las 24 respuestas de robustez usaban voseo (r1, r4, r5 y r6 en los dos modos), el registro de la configuración global del usuario. En la v2 no aparece en ninguna de las 84 respuestas. El detector de `tests/test_espanol_neutro.py` marca solo un verbo en pretérito de primera persona en r4 A, que es un falso positivo.
- **Sin ningún `CLAUDE.md`, el Modo A no sabe que el agente trata del Perú.** En r1 preguntó de qué país se trataba y ofreció, entre otros, Argentina, México y España.
- **El Modo A usó menos herramientas que en la v1.** Respondió sin ninguna 7 de los 12 pedidos (r1, r2, r5, r7, r8, r9 y r12), frente a 4 en la v1, y en r8 declaró que respondía de memoria. En las preguntas pasó de 0 a 1 respuesta sin herramientas (b1). Puede deberse a que ya no recibe la configuración global del usuario o a la variación entre corridas; con una corrida por pedido no se pueden separar.
