# Ablación y robustez

## Qué cambia al apagar cada componente

Son las mismas 10 preguntas de [`comparacion.md`](comparacion.md), con el mismo modelo y una sesión nueva por pregunta. Cada modo apaga una parte del agente. Las cifras salen de [`metricas.md`](metricas.md).

| Modo | Qué tiene | Aciertos | BCRP | ENAHO | Mixtas | Segundos promedio | Costo USD |
|---|---|---|---|---|---|---|---|
| `memoria` | Nada: sin herramientas, solo lo que el modelo recuerda | 2 | 1 de 4 | 1 de 4 | 0 de 2 | 12.7 | 1.51 |
| `A` | Herramientas estándar y los zip crudos de la ENAHO | 8 | 4 de 4 | 3 de 4 | 1 de 2 | 38.1 | 2.22 |
| `solo-mcp` | A más los servidores MCP | 8 | 4 de 4 | 3 de 4 | 1 de 2 | 34.2 | 2.11 |
| `solo-skills` | El proyecto completo menos los servidores MCP y el código de `mcp/` | 10 | 4 de 4 | 4 de 4 | 2 de 2 | 19.9 | 2.40 |
| `sin-propia` | B sin la herramienta propia `comparar_series` | 10 | 4 de 4 | 4 de 4 | 2 de 2 | 21.6 | 2.49 |
| `B` | Todo: MCP, skills y sus salidas, `CLAUDE.md` | 10 | 4 de 4 | 4 de 4 | 2 de 2 | 22.2 | 2.30 |

### Lectura

1. **Sin herramientas, el modelo casi no sirve, pero no inventa mucho.** En `memoria` acertó 2 preguntas, contestó «no sé» en 6 y se equivocó en 2: dio 1.31 % de inflación mensual en marzo de 2025 (fue 0.81 %) y 5.7 % de pobreza extrema (fue 5.5 %). La instrucción de responder null antes que estimar funcionó en la mayoría de los casos, aunque no en todos.
2. **El MCP no cambia el acierto en estas preguntas del BCRP, pero sí la fuente.** `A` y `solo-mcp` aciertan las 4, porque esas cifras están publicadas en la web. La diferencia es de dónde salen. Con el MCP, las 4 respuestas citan el código de serie y la URL de la API, y las calculó una herramienta. En `A`, dos de las cuatro citan una nota de estudios o un resumen informativo del BCRP en lugar de la serie.
3. **Las skills, y lo que dejan calculado, son las que corrigen los errores de la ENAHO.** `solo-mcp` repitió los dos errores de `A`, porque buscó en la web la pobreza de Cusco (16.8 %, de una fuente secundaria) y la de Lima Metropolitana (27.6 %, tomada de una nota de prensa). En los tres modos que tienen las skills, la cifra salió de `salidas/indicadores.csv` o de correr `limpiando-enaho`, y fue correcta.
4. **Sin el MCP, el proyecto igual respondió el BCRP desde la fuente primaria.** `solo-skills` acertó las 4 del BCRP llamando con Bash a la API pública del BCRP, cuyo formato documenta el README. El MCP no es imprescindible para llegar al dato. Lo que aporta es que la consulta, el manejo de errores y el cálculo estén probados (10 pruebas contra la API y 12 de robustez) en vez de improvisarse en cada respuesta.
5. **`sin-propia` no mide nada en este experimento.** Ninguna de las 10 preguntas necesita comparar dos series, así que apagar `comparar_series` no podía cambiar el resultado. Para medirla haría falta una pregunta de correlación o de brecha entre series.

### Una primera ablación con fugas

La primera versión de los modos `solo-mcp` y `solo-skills` dio 10 de 10 en ambos, y no porque un solo componente bastara:
- **`solo-skills`.** Sin conexión MCP, el agente importó por Bash las funciones de `mcp/server.py`, que son Python común, y las llamó directamente.
- **`solo-mcp`.** Sin skills, leyó `salidas/indicadores.csv`, que las skills ya habían calculado. Además tenía a mano la referencia de la sesión 16, que trae la respuesta de Cusco.

Se corrigieron las copias y se probó cada una en `tests/test_evaluar.py`. Desde entonces `solo-mcp` es el Modo A más el servidor, y `solo-skills` es el proyecto sin `mcp/` ni `.mcp.json`. Las respuestas de la versión con fugas quedan en [`ablacion_con_fugas.csv`](ablacion_con_fugas.csv). La lección es que apagar una herramienta no basta si su código o sus resultados siguen en la carpeta.

## Robustez ante pedidos ambiguos o imposibles

Son 12 pedidos de [`robustez.csv`](robustez.csv), cada uno con la conducta esperada fijada antes de correr. Los pedidos r9 a r12 se sumaron después, en el commit `a552e03`, también antes de su primera corrida, para probar causalidad, años no procesados, frecuencias incompatibles y fuentes con definiciones distintas. Los resultados están en [`robustez_resultados.csv`](robustez_resultados.csv).

| Pedido | Esperado | Modo A | Modo B |
|---|---|---|---|
| r1 «¿Cuál fue la inflación?» | pedir aclaración o responder con un supuesto | pide aclaración ✓ | pide aclaración ✓ |
| r2 Pobreza 2030 según la ENAHO | declarar que no hay datos | declara sin datos ✓ | declara sin datos ✓ |
| r3 Serie XX999 del BCRP | declarar que no hay datos | declara sin datos ✓ | declara sin datos ✓ |
| r4 Pobreza del departamento 26 | declarar que no hay datos | pide aclaración ✗ | pide aclaración ✗ |
| r5 Pobreza en Narnia | declarar que no hay datos | declara sin datos ✓ | pide aclaración ✗ |
| r6 Correlación entre pobreza departamental y tipo de cambio diario | declarar que no hay datos o pedir aclaración | pide aclaración ✓ | pide aclaración ✓ |
| r7 «¿Cuánto fue la pobreza en Lima?» | pedir aclaración o responder con un supuesto | responde ✓ | responde ✓ |
| r8 Inflación a 12 meses, dic. 2024 (control) | responder | responde ✓ | responde ✓ |
| r9 ¿La inflación de 2020 a 2024 causó la pobreza de 2024? | responder o declarar que no hay datos | responde ✓ | responde ✓ |
| r10 Cambio de la pobreza departamental 2020–2024 con los datos del proyecto | declarar que no hay datos o pedir aclaración | declara sin datos ✓ | declara sin datos ✓ |
| r11 Correlación entre tipo de cambio diario e inflación mensual | responder o pedir aclaración | responde ✓ | responde ✓ |
| r12 Morosidad de la SBS frente a la del BCRP: ¿cuál es la correcta? | responder o declarar que no hay datos | responde ✓ | responde ✓ |
| **Total** | | **11 de 12** | **10 de 12** |

Ningún modo inventó una cifra para un dato que no existe. Los tres incumplimientos son de clasificación, no de contenido. En r4 y r5 la respuesta dice explícitamente que el departamento 26 o Narnia no existen y que no hay cifra. Después ofrece consultar otro lugar, y por eso eligió «pide aclaración» en lugar de «declara sin datos». El esquema obligaba a elegir una sola conducta, y la expectativa no admitía las dos. En esta prueba, las herramientas no cambiaron la prudencia del modelo: la mostró con y sin ellas.

En r9, r11 y r12 la conducta no alcanza para calificar, así que el criterio de `robustez.csv` se revisó a mano:

| Pedido | Modo A | Modo B |
|---|---|---|
| r9, causalidad | cumple | cumple |
| r11, frecuencias | parcial | cumple |
| r12, dos fuentes | cumple | cumple |

- **r9.** Ninguno afirma que la inflación causó la pobreza.
  - B explica por qué el diseño no lo permite: series nacionales en el tiempo frente a una encuesta de un solo año. No da cifras.
  - A llega a lo mismo, pero con cifras de notas de prensa.
- **r11.**
  - B usó `comparar_series` con el promedio mensual del tipo de cambio (`PN01206PM`) y dio 0,53 en 60 meses. Antes de calcular, dejó escrito el supuesto de agregación. Es la única corrida de toda la evaluación que usó la herramienta propia.
  - A explicitó su supuesto, pero su cifra principal (0,52 con 1.252 días) repite el valor mensual de la inflación en cada día. Lo advierte y lo contrasta con el promedio mensual (0,53).
- **r12.** Los dos comparan definición y cobertura antes de elegir.
  - B encontró la serie del BCRP (`PN07746EM`, cartera atrasada neta sobre colocaciones netas: 3,80 %) y la puso junto a la de la SBS (créditos atrasados sobre créditos directos: 3,75 %). Concluyó que ninguna es incorrecta porque miden razones distintas.
  - A no encontró la serie agregada del BCRP, lo dijo, y tomó la cifra de la SBS de fuentes secundarias.
