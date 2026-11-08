# Título: la pregunta en pocas palabras

<!-- Copia esta plantilla a informes/borrador.md. Cada cifra va como marcador; armar_informe.py las resuelve.
     Marcadores: {{enaho.<id>}}, {{bcrp.<herramienta>(arg=valor, ...).<campo>|decimales}},
     {{sbs.<herramienta>(...).<campo>}} y {{lit:texto}} para constantes metodológicas. -->

## 1. Pregunta de investigación

Tema, objetivo y delimitación: qué periodo cubre cada fuente, qué territorio y qué no se pretende demostrar (ninguna relación causal).

## 2. Fuentes y metodología

- **BCRP**: series consultadas por el servidor MCP `bcrp`, con su código y periodo.
- **ENAHO 2024 (INEI)**: módulos 34 y 02, residentes habituales, factores de expansión `factor07 × mieperho` (hogar) y `facpob07` (persona), procesados con la skill `limpiando-enaho`.
- Otras fuentes oficiales, si se usaron (por ejemplo, la SBS por su servidor MCP).
- Indicadores construidos y por qué.

## 3. Resultados

Al menos tres hallazgos, cada uno con sus cifras como marcadores y la fuente en la misma oración.

1. Hallazgo macroeconómico (BCRP).
2. Hallazgo territorial o urbano-rural (ENAHO).
3. Hallazgo que pone ambas fuentes lado a lado.

## 4. Visualizaciones

![Serie del BCRP](../figuras/bcrp_<codigo>_<desde>_<hasta>.png)

![Pobreza por área o grupo](../figuras/pobreza_por_area.png)

![Mapa departamental](../mapas/pobreza_departamento.png)

## 5. Interpretación

Patrones principales, descritos como asociaciones. Reconocer cuando se comparan datos de distinto nivel de agregación (series nacionales mensuales frente a una encuesta anual por departamento).

## 6. Limitaciones

Cobertura temporal, calidad de los datos, márgenes de error de la encuesta, fallas de las herramientas durante la ejecución y alcance de las conclusiones.

## 7. Reproducibilidad

Scripts, archivos de `salidas/`, códigos de serie y comandos para regenerar el informe. `armar_informe.py` agrega al final la tabla de trazabilidad y las referencias.
