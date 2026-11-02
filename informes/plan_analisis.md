# Plan de análisis

## Pregunta

¿Cómo evolucionaron la inflación y la actividad económica del Perú entre 2020 y 2024, y qué brechas territoriales y urbano-rurales presentaba la pobreza monetaria en 2024?

## Fuentes e indicadores

| Parte de la pregunta | Fuente | Indicador | Argumentos |
|---|---|---|---|
| Inflación 2020-2024 | BCRP, servidor MCP `bcrp` | `PN01273PM`, IPC Lima Metropolitana, variación porcentual a 12 meses | `resumen(desde=2020-01, hasta=2024-12)` y cada diciembre de 2020 a 2024 |
| Actividad 2020-2024 | BCRP | `PN01728AM`, PBI, variación porcentual interanual mensual | `resumen(desde=2020-01, hasta=2024-12)` y cada año calendario |
| Relación inflación-actividad | BCRP | `comparar_series(PN01273PM, PN01728AM, 2020-01, 2024-12)` | Solo como asociación |
| Contexto financiero 2024 | SBS, servidor MCP `sbs` | Morosidad de bancos (B-2401) y de cajas municipales (C-1301); créditos por banco (B-2332) | `periodo=2024-12` |
| Pobreza por área | ENAHO 2024 | `pobreza_nacional`, `pobreza_area_urbana`, `pobreza_area_rural`, `pobreza_extrema` | `salidas/indicadores.csv` |
| Pobreza por departamento | ENAHO 2024 | `pobreza_dep_01` a `pobreza_dep_25` | `salidas/indicadores.csv` |

## Gráficos

1. Inflación a 12 meses, `PN01273PM` 2020-01 a 2024-12 (`graficar_serie`).
2. PBI interanual, `PN01728AM` 2020-01 a 2024-12 (`graficar_serie`).
3. Pobreza por área (`graficando-enaho --por area`).
4. Pobreza por departamento (`graficando-enaho --por departamento`).
5. Mapa departamental (`mapeando-enaho`).

## Cuidados

- La inflación es de Lima Metropolitana y la pobreza es nacional por departamento: distinto alcance geográfico.
- La ENAHO es de un solo año (2024): no se describe la evolución de la pobreza.
- Ninguna relación entre series macro y pobreza se presenta como causal.
