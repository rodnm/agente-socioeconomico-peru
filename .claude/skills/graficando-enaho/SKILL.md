---
name: graficando-enaho
description: Grafica en barras la pobreza monetaria de la ENAHO 2024 del INEI por área urbana y rural, sexo, edad o departamento, con ponderación y formato fijos. Úsala cuando pidan un gráfico o una figura de la pobreza en Perú, por ejemplo graficar la pobreza urbana y rural o comparar la pobreza entre departamentos o regiones.
argument-hint: [area|sexo|edad|departamento]
allowed-tools: Bash(uv run *)
---

# Graficar la pobreza de la ENAHO

1. Si no existe `salidas/personas_2024.parquet`, usa primero la skill `limpiando-enaho`. El script también se detiene con ese aviso si falta.
2. Elige el corte según el pedido y corre exactamente: `uv run ${CLAUDE_SKILL_DIR}/scripts/graficar.py --por <corte>`. Sin `--por` hace los cuatro.

   | Si el pedido habla de… | Corte |
   |---|---|
   | urbano, rural, área, ciudad o campo | `area` |
   | hombres, mujeres, sexo o género | `sexo` |
   | edad, niños, jóvenes, adultos mayores | `edad` |
   | departamentos, regiones, territorio, comparar entre lugares | `departamento` |

3. Responde con la ruta de `figuras/pobreza_por_<corte>.png` y las cifras que imprime el script. No las recalcules.

## Reglas que fija el script

- Barras que empiezan en cero. Área y sexo de mayor a menor; las edades en su orden natural; los departamentos en barras horizontales ordenadas, con una línea en el promedio nacional.
- Un solo color y el valor escrito en cada barra.
- Título analítico calculado con los datos (qué grupo está más arriba y por cuánto), subtítulo con el periodo y la unidad (% de personas).
- Nota al pie: «Fuente: INEI, ENAHO 2024 (módulos 34 y 02)», más el peso usado.
- PNG a 200 dpi en `figuras/`.

## Pesos

- **Área y departamento:** por hogar con `factor07 × mieperho`, porque así salen las cifras oficiales (24.8 % urbana, 39.3 % rural y la tabla departamental del INEI). Con `facpob07` darían 24.7 % y 39.4 %.
- **Sexo y edad:** por persona con `facpob07`, porque son atributos de cada persona.

Si piden un corte que no está en el script, dilo antes de improvisar otro gráfico. Las diferencias entre grupos son descriptivas: no las presentes como causas.
