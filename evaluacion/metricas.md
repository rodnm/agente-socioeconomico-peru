# Métricas de la evaluación

Generado por `evaluacion/analizar.py` a partir de `resultados.csv`. Cada fila de las corridas es una sesión nueva de `claude -p` con el mismo modelo.

## Aciertos por modo

| modo | acierta | se equivoca | no sabe | error | segundos promedio | turnos promedio | costo total USD |
|---|---|---|---|---|---|---|---|
| A | 8 | 2 | 0 | 0 | 38.1 | 6.3 | 2.22 |
| B | 10 | 0 | 0 | 0 | 22.2 | 4.9 | 2.3 |
| memoria | 2 | 2 | 6 | 0 | 12.7 | 2 | 1.51 |
| solo-mcp | 8 | 2 | 0 | 0 | 34.2 | 6.4 | 2.11 |
| solo-skills | 10 | 0 | 0 | 0 | 19.9 | 6.3 | 2.4 |
| sin-propia | 10 | 0 | 0 | 0 | 21.6 | 5.2 | 2.49 |

## Aciertos por tipo de pregunta

| tipo | A | B | memoria | solo-mcp | solo-skills | sin-propia |
|---|---|---|---|---|---|---|
| bcrp | 4 de 4 | 4 de 4 | 1 de 4 | 4 de 4 | 4 de 4 | 4 de 4 |
| enaho | 3 de 4 | 4 de 4 | 1 de 4 | 3 de 4 | 4 de 4 | 4 de 4 |
| mixta | 1 de 2 | 2 de 2 | 0 de 2 | 1 de 2 | 2 de 2 | 2 de 2 |

## Resultado de cada pregunta

Entre paréntesis, el valor que respondió el agente.

| pregunta | A | B | memoria | solo-mcp | solo-skills | sin-propia |
|---|---|---|---|---|---|---|
| b1 | acierta (1.97) | acierta (1.97) | acierta (1.97) | acierta (1.97) | acierta (1.97) | acierta (1.97) |
| b2 | acierta (3.7553) | acierta (3.7553) | no sabe | acierta (3.7553) | acierta (3.7553) | acierta (3.7553) |
| b3 | acierta (0.81) | acierta (0.81) | se equivoca (1.31) | acierta (0.81) | acierta (0.81) | acierta (0.81) |
| b4 | acierta (4.55) | acierta (4.55) | no sabe | acierta (4.55) | acierta (4.55) | acierta (4.55) |
| e1 | acierta (27.6) | acierta (27.58) | acierta (27.6) | acierta (27.6) | acierta (27.58) | acierta (27.58) |
| e2 | acierta (39.3) | acierta (39.3) | no sabe | acierta (39.3) | acierta (39.3028) | acierta (39.3) |
| e3 | se equivoca (16.8) | acierta (18.54) | no sabe | se equivoca (16.8) | acierta (18.54) | acierta (18.54) |
| e4 | acierta (5.5) | acierta (5.5) | se equivoca (5.7) | acierta (5.5) | acierta (5.5) | acierta (5.5) |
| m1 | acierta (1.97) | acierta (1.97) | no sabe (1.97) | acierta (1.97) | acierta (1.97) | acierta (1.97) |
| m2 | se equivoca (3.755) | acierta (3.7553) | no sabe | se equivoca (3.7553) | acierta (3.7553) | acierta (3.7553) |

## Cambios frente al Modo A

- **B**: mejoran e3, m2; empeoran ninguna.
- **memoria**: mejoran ninguna; empeoran b2, b3, b4, e2, e4, m1.
- **solo-mcp**: mejoran ninguna; empeoran ninguna.
- **solo-skills**: mejoran e3, m2; empeoran ninguna.
- **sin-propia**: mejoran e3, m2; empeoran ninguna.

## Uso de herramientas

Corridas de cada modo que usaron al menos una herramienta de cada familia.

| modo | MCP | Skill | Web | Bash |
|---|---|---|---|---|
| A | 0 | 0 | 9 | 3 |
| B | 6 | 0 | 0 | 6 |
| memoria | 0 | 0 | 0 | 0 |
| solo-mcp | 6 | 0 | 6 | 1 |
| solo-skills | 0 | 2 | 1 | 10 |
| sin-propia | 6 | 0 | 0 | 3 |

## Interpretación de las mixtas

`lenguaje_causal` marca palabras que afirman causas; la revisión con el criterio de preguntas.csv es manual.

| pregunta y modo | resultado | lenguaje_causal | interpretacion |
|---|---|---|---|
| m1 · A | acierta | True | Una inflación de 1,97 %, en el centro del rango meta de 1–3 %, protegió el poder de compra urbano y es coherente con la baja de la pobreza urbana de 26,4 % a 24,8 %. Aun así, uno de cada cuatro habitantes urbanos seguía en pobreza, y la rel |
| m1 · B | acierta | True | La inflación de Lima fue baja (1.97%, dentro del rango meta del BCRP), por lo que en 2024 los precios no erosionaron de forma notable el poder de compra de los hogares; aun así, una de cada cuatro personas urbanas (24.8%) seguía bajo la lín |
| m2 · A | se equivoca | False | Las dos cifras casi no se relacionan de forma directa. El tipo de cambio de 2024 fue estable (~S/ 3,76 por dólar) y la pobreza monetaria se mide en soles constantes con el gasto per cápita, así que el dólar no la explica. Ambos datos descri |
| m2 · B | acierta | False | Los dos datos son de 2024 pero de naturaleza distinta (un promedio de 246 cotizaciones diarias del mercado cambiario frente a una tasa anual de hogares de una encuesta), así que solo se pueden leer como contexto conjunto: un dólar relativam |
| m1 · memoria | no sabe | False | Las dos cifras miden fenómenos distintos y no se derivan una de la otra. Una inflación de 1,97 %, dentro del rango meta del BCRP (1 % a 3 %), ayuda a no erosionar el poder adquisitivo, pero la pobreza monetaria depende además del empleo y d |
| m2 · memoria | no sabe | False | Sin las dos cifras verificadas no puedo relacionarlas con rigor. En general, un tipo de cambio más estable o apreciado suele aliviar los precios de bienes importados y alimentos, pero la pobreza monetaria depende sobre todo del empleo, los  |
| m1 · sin-propia | acierta | True | En diciembre de 2024 la inflación fue de 1.97 %, dentro del rango meta del BCRP (1 %–3 %), mientras que alrededor de uno de cada cuatro peruanos urbanos (24.8 %) seguía en pobreza monetaria. Son indicadores de distinto nivel de agregación ( |
| m2 · sin-propia | acierta | True | El dólar interbancario se mantuvo estable en 2024 (promedio ≈ S/ 3.76, entre 3.67 y 3.88), así que no hubo un shock cambiario que explique la pobreza en Lima Metropolitana, donde alrededor de 28 de cada 100 personas son pobres monetarios. S |
| m1 · solo-mcp | acierta | True | Con inflación de apenas ~2% en diciembre de 2024 (dentro del rango meta del BCRP), los precios, y en particular los de los alimentos, dejaron de erosionar el poder adquisitivo de los hogares urbanos. Eso es coherente con la baja de la pobre |
| m1 · solo-skills | acierta | False | La inflación de cierre de 2024 (1.97%) quedó dentro del rango meta del BCRP (1%–3%), con precios estables, y aun así casi una de cada cuatro personas urbanas (24.8%) seguía en pobreza monetaria. Son indicadores de distinto nivel y periodo ( |
| m2 · solo-mcp | se equivoca | True | En 2024 el dólar interbancario se mantuvo estable (promedio de S/ 3,755, con un rango de 3,667 a 3,884), mientras que cerca de 28 de cada 100 limeños seguían en pobreza monetaria. Esto indica que un tipo de cambio calmado no garantiza reduc |
| m2 · solo-skills | acierta | False | En 2024 el dólar interbancario promedió unos S/ 3.76 con poca variación (3.67–3.88), un entorno cambiario estable, mientras que cerca de 28 de cada 100 personas en Lima Metropolitana vivían en pobreza monetaria. Son indicadores de distinto  |

## Robustez

| modo | cumple | no cumple |
|---|---|---|
| A | 7 | 1 |
| B | 6 | 2 |

| pedido | A | B |
|---|---|---|
| r1 | pide_aclaracion | pide_aclaracion |
| r2 | declara_sin_datos | declara_sin_datos |
| r3 | declara_sin_datos | declara_sin_datos |
| r4 | pide_aclaracion | pide_aclaracion |
| r5 | declara_sin_datos | pide_aclaracion |
| r6 | pide_aclaracion | pide_aclaracion |
| r7 | responde | responde |
| r8 | responde | responde |
