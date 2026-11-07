# Referencia de la ENAHO 2020–2024

Nombres, etiquetas y códigos leídos de los `.dta` del INEI. Cada zip trae además el diccionario y la ficha técnica del año, con todas las variables.

## Años y códigos de encuesta

| Año | Código del INEI | Módulo 34 | Módulo 02 |
|---|---|---|---|
| 2020 | `737` | `737-Modulo34.zip` → `sumaria-2020.dta` | `737-Modulo02.zip` → `enaho01-2020-200.dta` |
| 2021 | `759` | `759-Modulo34.zip` → `sumaria-2021.dta` | `759-Modulo02.zip` → `enaho01-2021-200.dta` |
| 2022 | `784` | `784-Modulo34.zip` → `sumaria-2022.dta` | `784-Modulo02.zip` → `enaho01-2022-200.dta` |
| 2023 | `906` | `906-Modulo34.zip` → `sumaria-2023.dta` | `906-Modulo02.zip` → `enaho01-2023-200.dta` |
| 2024 | `966` | `966-Modulo34.zip` → `sumaria-2024.dta` | `966-Modulo02.zip` → `enaho01-2024-200.dta` |

Fuente de los zip: `https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/{código}-Modulo{34|02}.zip`.

## Módulo 34, `sumaria-AAAA.dta`: una fila por hogar

Los códigos de `dominio`, `estrato` y `pobreza` significan lo mismo en los cinco años; desde 2023 solo cambia la escritura de las etiquetas de `estrato`.

| Variable | Etiqueta | Códigos o uso |
|---|---|---|
| `conglome`, `vivienda`, `hogar` | Llaves del hogar | Texto de 6, 3 y 2 caracteres |
| `ubigeo` | Ubicación geográfica | Texto de 6 caracteres; `ubigeo[:2]` es el departamento y `ubigeo[:4] == "1501"` la provincia de Lima |
| `dominio` | Dominio geográfico | 1 costa norte, 2 costa centro, 3 costa sur, 4 sierra norte, 5 sierra centro, 6 sierra sur, 7 selva, 8 Lima Metropolitana. El dominio 8 incluye el Callao: su tasa replica la fila «Lima Metropolitana y Prov. Const. del Callao» del Cuadro III.1 (p. 219), no la de «Lima Metropolitana» (p. 220) |
| `estrato` | Estrato geográfico | 1 a 5: 2 000 habitantes o más (urbano). 6: 500 a 1 999 habitantes. 7 y 8: áreas de empadronamiento rural (rural) |
| `pobreza` | Pobreza | 1 pobre extremo, 2 pobre no extremo, 3 no pobre |
| `mieperho` | Total de miembros del hogar | Conteo de `p204 == 1`, incluye a los miembros ausentes |
| `factor07` | Factor de expansión anual | Por hogar; `factor07 × mieperho` expande a personas |

## Módulo 02, `enaho01-AAAA-200.dta`: una fila por persona

| Variable | Etiqueta | Códigos o uso |
|---|---|---|
| `codperso` | Número de orden de la persona | Texto de 2 caracteres; completa la llave de persona |
| `p203` | Parentesco con el jefe(a) del hogar | 0 panel, 1 jefe(a), 2 esposo(a), 3 hijo(a), 4 yerno/nuera, 5 nieto(a), 6 padres/suegros, 7 otros parientes, 8 trabajador del hogar, 9 pensionista, 10 otros no parientes, 11 hermano(a) |
| `p204` | ¿Es miembro del hogar? | 1 sí, 2 no |
| `p205` | ¿Ausente del hogar 30 días o más? | 1 sí, 2 no. Solo si `p204 == 1` |
| `p206` | ¿Presente en el hogar 30 días o más? | 1 sí, 2 no. Solo si `p204 == 2` |
| `p207` | Sexo | 1 hombre, 2 mujer |
| `p208a` | Edad en años cumplidos | 0 a 98 |
| `facpob07` | Factor de expansión anual de población | Por persona |

## Variables que construye `limpiar.py`

| Variable | Definición |
|---|---|
| `anio` | La columna del año, renombrada |
| `departamento` | `ubigeo[:2]` |
| `departamento_nombre` | Nombre con tildes, solo para mostrar; las uniones usan `departamento` |
| `urbano` | `estrato <= 5` |
| `pobre` | `pobreza <= 2` |
| `peso_hogar` | `factor07 × mieperho` |

## Qué peso usar

| Cifra | Peso | Filas |
|---|---|---|
| Pobreza nacional, por área, dominio o departamento | `peso_hogar` | Una por hogar |
| Pobreza por sexo o edad | `facpob07` | Todas |

- **El mismo peso en los cinco años.** `factor07 × mieperho` reproduce todas las cifras publicadas que se validan, a 0.05 puntos o menos en cada año. La sumaria de 2020 y de 2021 solo trae `factor07`. El módulo 02 de 2020 trae además `factor_p` («factor de expansión anual - tipo presencial - proyecciones cpv-2007»), con valor solo en 63,866 de sus 126,831 filas; no se usa. El módulo 02 de 2021 no trae `factor_p`.
- **Por qué no `facpob07` para la pobreza oficial.** Usar `peso_hogar` sin quitar duplicados cuenta cada hogar tantas veces como residentes tenga. Con `facpob07` la cifra nacional se aleja de la publicada: 0.09 puntos en 2020, 0.16 en 2021, 0.02 en 2022, 0.02 en 2023 y 0.07 en 2024. En 2024, además, 13 de los 24 departamentos con cifra publicada se alejan más de 0.1 puntos de la cifra del INEI (Puno 40.42 % frente a 39.9 %). Por eso `validacion.txt` muestra la línea de `facpob07` solo como contraste, con una tolerancia de 0.2 puntos de 2020 a 2023 (en 2021 difiere en 0.16 puntos) y de 0.1 en 2024, la misma de la consigna.

## Contra qué se valida cada año

Las metas vienen del informe técnico del INEI (2025), *Perú: Evolución de la pobreza monetaria, 2015-2024*. Las páginas son las impresas; en el visor del PDF, cada una corresponde al número impreso más 2. Los dos cuadros traen la serie 2015-2024; el intervalo de confianza al 95 % y el coeficiente de variación solo se publican para 2024.

| Meta | Cuadro y página | Años |
|---|---|---|
| Pobreza nacional, urbana y rural | Cuadro III.1, p. 219 | 2020 a 2024 |
| Lima Metropolitana y Callao (dominio 8) | Cuadro III.1, p. 219 | 2020 a 2024 |
| Lima Metropolitana (provincia 1501) y Lima provincias | Cuadro III.1, p. 220 | 2020 a 2024 |
| Pobreza extrema | Cuadro III.4, p. 223 | 2020 a 2024 |
| Cada departamento y el Callao, con IC y CV | Cuadro III.1, p. 220 | 2024 |

- **Valores de 2020 a 2023:** `METAS_INEI` en `limpiar.py`. **Valores de 2024:** `referencias/inei_pobreza_2024.csv`, con su IC y su CV.
- **Lima, departamento 15:** el INEI no publica una cifra del departamento en conjunto, así que no se valida. Se validan Lima Metropolitana y Lima provincias. El departamento 15 se conserva en `indicadores.csv` porque la consigna pide 25 códigos territoriales.
- **Tolerancia de 0.1 puntos:** es una réplica de una cifra que el INEI publica con un decimal, no una prueba estadística. La incertidumbre de muestreo la dan los IC del INEI.
- **Conteos de hogares, filas y residentes:** se leen de los `.dta` del INEI y detectan un archivo distinto o incompleto. No son cifras publicadas. Los 108,664 residentes de 2024 son la cifra que pide la consigna.

## `salidas/indicadores.csv`

Una fila por año e indicador, con `anio`, `id`, `indicador`, `grupo`, `valor`, `unidad`, `ponderador`, `n_muestral` y `fuente`. Los `id` son estables y los cita el informe: `pobreza_nacional`, `pobreza_nacional_personas`, `pobreza_extrema`, `pobreza_area_urbana`, `pobreza_area_rural`, `pobreza_lima_metropolitana` (dominio 8, grupo «Lima Metropolitana y Callao»), `pobreza_lima_metropolitana_provincia` (provincia 1501, grupo «Lima Metropolitana»), `pobreza_lima_provincias` (grupo «Lima provincias»), `pobreza_dep_01` a `pobreza_dep_25` (código `ubigeo[:2]`), `pobreza_sexo_hombres`, `pobreza_sexo_mujeres`, `pobreza_edad_0_14` a `pobreza_edad_60_mas`, `residentes_habituales`, `hogares`, `poblacion_expandida` y `departamentos`.

## Siete trampas

1. **Ceros a la izquierda.** `conglome` «015009» y `ubigeo` «010101» son texto. Como número pierden el cero y la unión falla.
2. **Nombres rotos.** La columna del año llega como `aÑo` con el byte dañado. Hay que normalizar antes de usarla.
3. **No todos son residentes.** En 2024, el módulo 02 tiene 117,721 filas y 108,664 residentes habituales: `(p204 == 1 & p205 == 2) | (p204 == 2 & p206 == 1)`.
4. **Uniones que duplican.** Sin `validate="m:1"`, un hogar repetido multiplica personas sin avisar.
5. **Encuestas no son personas.** Los 33,691 hogares de 2024 representan 34.5 millones de personas con `factor07 × mieperho`; con `facpob07` sobre los residentes habituales son 34.1 millones (`poblacion_expandida`).
6. **Códigos, no números.** `pobreza` 1, 2 y 3 son categorías: pobre es `pobreza <= 2`, nunca un promedio.
7. **Dos sumarias por zip.** Cada zip del módulo 34 trae `sumaria-AAAA.dta` y `sumaria-AAAA-12g.dta`, esta última con el gasto en 12 grupos. El script lee solo la primera, con un patrón exacto.
