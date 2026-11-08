---
name: graficando-enaho
description: Grafica la pobreza monetaria de la ENAHO del INEI con ponderación y formato fijos, en barras para 2024 por área urbana y rural, sexo, edad o ámbito territorial (departamentos con Lima desagregada) y en líneas para la serie 2020-2024. Úsala cuando pidan un gráfico o una figura de la pobreza en Perú, por ejemplo graficar la pobreza urbana y rural, comparar la pobreza entre departamentos o regiones, o mostrar su evolución entre 2020 y 2024.
argument-hint: [area|sexo|edad|departamento|serie]
allowed-tools: Bash(uv run *)
---

# Graficar la pobreza de la ENAHO

1. Si no existe `salidas/personas_2024.parquet` (cortes de 2024) o `salidas/indicadores.csv` con la columna `anio` (serie), usa primero la skill `limpiando-enaho`. El script también se detiene con ese aviso si falta.
2. Elige el corte según el pedido y corre exactamente: `uv run ${CLAUDE_SKILL_DIR}/scripts/graficar.py --por <corte>`. Sin `--por` hace los cinco.

   | Si el pedido habla de… | Corte |
   |---|---|
   | urbano, rural, área, ciudad o campo | `area` |
   | hombres, mujeres, sexo o género | `sexo` |
   | edad, niños, jóvenes, adultos mayores | `edad` |
   | departamentos, regiones, territorio, comparar entre lugares | `departamento` |
   | evolución, tendencia, 2020 a 2024, cambio en el tiempo | `serie` |

3. Responde con la ruta de `figuras/pobreza_por_<corte>.png` (o `figuras/pobreza_serie_2020_2024.png`) y las cifras que imprime el script. No las recalcules.

## Reglas que fija el script

- Barras que empiezan en cero. Área y sexo de mayor a menor; las edades en su orden natural.
- El corte `departamento` muestra los 26 ámbitos del INEI: 24 departamentos, Callao, Lima Metropolitana (provincia 1501) y Lima provincias, en barras horizontales ordenadas, con una línea en el promedio nacional. La cifra va en la punta de cada barra; si ahí cruzaría la línea nacional, va en blanco dentro del extremo de la barra.
- Las cifras que el INEI publica como referenciales (coeficiente de variación mayor que 15 %, columnas `cv` y `nota` de `referencias/inei_pobreza_2024.csv`: Ica, Madre de Dios y Moquegua) llevan un asterisco y una nota al pie.
- Lima se rotula siempre «Lima Metropolitana» y «Lima provincias», igual que en los mapas.
- La serie 2020-2024 muestra la pobreza nacional, rural, urbana, de Lima Metropolitana y de Lima provincias: colores de la paleta categórica validada en orden fijo, marcador y trazo distintos por serie, leyenda arriba y la cifra del primer y del último año unida a su punto por una guía, sin superponerse.
- Un solo color en las barras y el valor escrito en cada una.
- Título analítico calculado con los datos (qué grupo está más arriba y por cuánto), subtítulo con el periodo y la unidad (% de personas). Ninguna cifra queda separada de su unidad al cambiar de línea.
- Nota al pie: «Fuente: INEI, ENAHO 2024 (módulos 34 y 02)», más el peso usado.
- PNG a 200 dpi en `figuras/`.

## Pesos

- **Área y ámbitos territoriales:** por hogar con `factor07 × mieperho`, porque así salen las cifras oficiales (24.8 % urbana, 39.3 % rural y la tabla territorial del INEI). Con `facpob07` darían 24.7 % y 39.4 %.
- **Sexo y edad:** por persona con `facpob07`, porque son atributos de cada persona.

Si piden un corte que no está en el script, dilo antes de improvisar otro gráfico. Las diferencias entre grupos son descriptivas: no las presentes como causas.
