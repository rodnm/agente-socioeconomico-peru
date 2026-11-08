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

Son 8 pedidos de [`robustez.csv`](robustez.csv), cada uno con la conducta esperada fijada antes de correr. Los resultados están en [`robustez_resultados.csv`](robustez_resultados.csv).

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
| **Total** | | **7 de 8** | **6 de 8** |

Ningún modo inventó una cifra para un dato que no existe. Los tres incumplimientos son de clasificación, no de contenido. En r4 y r5 la respuesta dice explícitamente que el departamento 26 o Narnia no existen y que no hay cifra. Después ofrece consultar otro lugar, y por eso eligió «pide aclaración» en lugar de «declara sin datos». El esquema obligaba a elegir una sola conducta, y la expectativa no admitía las dos. En esta prueba, las herramientas no cambiaron la prudencia del modelo: la mostró con y sin ellas.
