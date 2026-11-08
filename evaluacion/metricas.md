# Métricas de la evaluación

Generado por `evaluacion/analizar.py` a partir de `resultados.csv`. Cada fila de las corridas es una sesión nueva de `claude -p` con el mismo modelo.

## Aciertos por modo

| modo | acierta | se equivoca | no sabe | error | segundos promedio | turnos promedio | costo total USD |
|---|---|---|---|---|---|---|---|
| A | 9 | 1 | 0 | 0 | 22.9 | 4.8 | 0.52 |
| B | 10 | 0 | 0 | 0 | 18.8 | 4.5 | 0.57 |
| memoria | 2 | 1 | 7 | 0 | 8.2 | 2 | 0.16 |
| solo-mcp | 8 | 2 | 0 | 0 | 54.9 | 5.5 | 0.63 |
| solo-skills | 9 | 1 | 0 | 0 | 17.6 | 5.2 | 0.61 |
| sin-propia | 9 | 1 | 0 | 0 | 19.2 | 4.7 | 0.63 |

## Aciertos por tipo de pregunta

| tipo | A | B | memoria | solo-mcp | solo-skills | sin-propia |
|---|---|---|---|---|---|---|
| bcrp | 4 de 4 | 4 de 4 | 1 de 4 | 4 de 4 | 4 de 4 | 4 de 4 |
| enaho | 4 de 4 | 4 de 4 | 1 de 4 | 3 de 4 | 4 de 4 | 4 de 4 |
| mixta | 1 de 2 | 2 de 2 | 0 de 2 | 1 de 2 | 1 de 2 | 1 de 2 |

## Resultado de cada pregunta

Entre paréntesis, el valor que respondió el agente.

| pregunta | A | B | memoria | solo-mcp | solo-skills | sin-propia |
|---|---|---|---|---|---|---|
| b1 | acierta (1.97) | acierta (1.97) | acierta (1.97) | acierta (1.97) | acierta (1.97) | acierta (1.97) |
| b2 | acierta (3.7553) | acierta (3.7553) | no sabe | acierta (3.7553) | acierta (3.7553) | acierta (3.7553) |
| b3 | acierta (0.81) | acierta (0.81) | se equivoca (1.31) | acierta (0.81) | acierta (0.81) | acierta (0.81) |
| b4 | acierta (4.55) | acierta (4.55) | no sabe | acierta (4.55) | acierta (4.55) | acierta (4.55) |
| e1 | acierta (27.6) | acierta (27.6) | acierta (27.6) | acierta (27.6) | acierta (27.58) | acierta (27.58) |
| e2 | acierta (39.3) | acierta (39.3) | no sabe | acierta (39.3) | acierta (39.3) | acierta (39.3028) |
| e3 | acierta (18.5) | acierta (18.54) | no sabe | se equivoca (16.8) | acierta (18.54) | acierta (18.54) |
| e4 | acierta (5.5) | acierta (5.5) | no sabe | acierta (5.5) | acierta (5.5045) | acierta (5.5) |
| m1 | acierta (1.97) | acierta (1.97) | no sabe (1.97) | acierta (1.97) | acierta (1.97) | acierta (1.97) |
| m2 | se equivoca (3.7553) | acierta (3.755) | no sabe | se equivoca (3.755) | se equivoca (3.7553) | se equivoca (3.7553) |

## Cambios frente al Modo A

- **B**: mejoran m2; empeoran ninguna.
- **memoria**: mejoran ninguna; empeoran b2, b3, b4, e2, e3, e4, m1.
- **solo-mcp**: mejoran ninguna; empeoran e3.
- **solo-skills**: mejoran ninguna; empeoran ninguna.
- **sin-propia**: mejoran ninguna; empeoran ninguna.

## Uso de herramientas

Corridas de cada modo que usaron al menos una herramienta de cada familia.

| modo | MCP | Skill | Web | Bash |
|---|---|---|---|---|
| A | 0 | 0 | 8 | 3 |
| B | 6 | 0 | 0 | 5 |
| memoria | 0 | 0 | 0 | 0 |
| solo-mcp | 7 | 0 | 6 | 1 |
| solo-skills | 0 | 1 | 2 | 9 |
| sin-propia | 6 | 0 | 0 | 5 |

## Interpretación de las mixtas

`lenguaje_causal` marca palabras que afirman causas; la revisión con el criterio de preguntas.csv es manual.

| pregunta y modo | resultado | lenguaje_causal | interpretacion |
|---|---|---|---|
| m1 · A | acierta | False | En 2024 la inflación bajó a 1,97 %, dentro del rango meta del BCRP (1–3 %) y por debajo del 3,24 % de 2023. Esto probablemente ayudó a que la pobreza urbana bajara de 26,4 % a 24,8 %, porque los precios de los alimentos subieron menos y el  |
| m1 · B | acierta | True | La inflación cerró 2024 baja (≈2%, dentro del rango meta del BCRP), mientras que cerca de una cuarta parte de la población urbana seguía en pobreza monetaria: precios estables no implican por sí solos menor pobreza. Es solo una asociación d |
| m1 · memoria | no sabe | True | La inflación de 1,97 % quedó dentro del rango meta del BCRP (1 % a 3 %), un entorno de precios estables que favorece la reducción de la pobreza monetaria urbana. Sin la cifra de pobreza urbana verificada no puedo cuantificar esa relación, q |
| m1 · solo-skills | acierta | True | La inflación de Lima Metropolitana cerró 2024 baja (≈2%, dentro del rango meta del BCRP), mientras que cerca de una cuarta parte de la población urbana seguía en pobreza monetaria: precios estables no implican baja pobreza. Son indicadores  |
| m1 · sin-propia | acierta | True | La inflación estuvo baja y dentro del rango meta (1.97%), mientras que cerca de una de cada cuatro personas urbanas (24.8%) seguía en pobreza monetaria; es decir, una inflación baja no implica baja pobreza. Son indicadores de distinto nivel |
| m2 · A | se equivoca | True | Las dos cifras no tienen una relación causal directa que se pueda medir con estos datos. Un tipo de cambio estable, cerca de S/ 3,76 por dólar, coincide con una pobreza en Lima Metropolitana estancada en torno a 27,6 %, es decir, sin alivio |
| m2 · B | acierta | True | En 2024 el tipo de cambio fue estable (promedio ≈ S/ 3.755 por US$, rango 3.667–3.884) mientras ≈ 28 % de la población de Lima Metropolitana estaba en pobreza monetaria; son indicadores de distinto nivel (macro diario vs. microdatos anuales |
| m2 · memoria | no sabe | False | No puedo interpretar la relación sin las cifras. En general, un tipo de cambio más alto encarece los bienes importados y puede presionar la pobreza urbana, pero eso requiere los datos reales para sostenerse. |
| m2 · solo-skills | se equivoca | True | Un tipo de cambio promedio cercano a S/ 3,76 por US$ en 2024 y una pobreza del 27,6 % en Lima Metropolitana describen dimensiones distintas: una es un precio financiero diario y la otra una condición de los hogares medida en una encuesta an |
| m2 · sin-propia | se equivoca | True | En 2024 el tipo de cambio fue estable (promedio ≈ S/ 3.76 por dólar, rango 3.667–3.884) y aun así más de una cuarta parte de la población de Lima Metropolitana (≈ 27.6 %) estaba en pobreza monetaria; son series de distinto nivel (macro naci |
| m1 · solo-mcp | acierta | False | La inflación de 2024 cerró baja (≈2%, dentro del rango meta del BCRP de 1%–3%), lo que ayudó a que el poder adquisitivo de los hogares no se erosionara y es coherente con la caída de la pobreza urbana de 26,4% a 24,8%. Aun así, una cuarta p |
| m2 · solo-mcp | se equivoca | True | El tipo de cambio fue estable en 2024 (entre 3,67 y 3,88 soles por dólar, con un promedio de 3,755), así que no hubo un choque cambiario fuerte. La pobreza de Lima Metropolitana (27,6%) coincidió con la nacional y no refleja ese tipo de cam |

## Robustez

| modo | cumple | no cumple |
|---|---|---|
| A | 11 | 1 |
| B | 10 | 2 |

| pedido | A | B |
|---|---|---|
| r1 | pide_aclaracion | pide_aclaracion |
| r2 | declara_sin_datos | declara_sin_datos |
| r3 | declara_sin_datos | declara_sin_datos |
| r4 | responde | pide_aclaracion |
| r5 | declara_sin_datos | declara_sin_datos |
| r6 | pide_aclaracion | pide_aclaracion |
| r7 | pide_aclaracion | responde |
| r8 | responde | responde |
| r9 | responde | responde |
| r10 | declara_sin_datos | responde |
| r11 | responde | responde |
| r12 | responde | responde |
