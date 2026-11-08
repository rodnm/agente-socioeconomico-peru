# Plan de análisis

## Pregunta

¿Cómo evolucionaron la inflación, la actividad económica, la morosidad bancaria y la pobreza monetaria del Perú entre 2020 y 2024, y qué brechas territoriales y urbano-rurales presentaba la pobreza en 2024?

## Fuentes e indicadores

| Parte de la pregunta | Fuente | Indicador | Argumentos exactos |
|---|---|---|---|
| Inflación 2020-2024 | BCRP, servidor MCP `bcrp` | `PN01273PM`, IPC Lima Metropolitana, variación porcentual a 12 meses | `resumen(codigo=PN01273PM, desde=2020-01, hasta=2024-12)` y `resumen` de cada diciembre (`desde=hasta=AAAA-12`) |
| Actividad 2020-2024 | BCRP | `PM04863AA`, PBI, variación porcentual anual | `resumen(codigo=PM04863AA, desde=AAAA, hasta=AAAA)` para cada año de 2020 a 2024 |
| Actividad mensual | BCRP | `PN01728AM`, PBI, variación porcentual interanual mensual | `resumen(codigo=PN01728AM, desde=2020-01, hasta=2024-12)`: mínimo, máximo y último mes |
| Morosidad neta 2020-2024 | BCRP | `PN07746EM`, cartera atrasada neta / colocaciones netas, empresas bancarias | `resumen` de cada diciembre y `resumen(desde=2020-01, hasta=2024-12)` para el máximo |
| Morosidad bancaria 2020-2024 | SBS, servidor MCP `sbs` | Boletín B-2401, créditos atrasados / créditos directos, total banca múltiple | `indicadores(tipo_entidad=bancos, indicador=morosidad, periodo=AAAA-12)` de 2020 a 2024 |
| Contexto financiero 2024 | SBS | ROE (B-2401), ratio de capital global (B-2401), concentración de créditos (B-2332), morosidad de cajas municipales (C-1301) | `indicadores(... indicador=roe, periodo=2020-12 y 2024-12)`, `indicadores(... indicador=solvencia, periodo=2024-12)`, `ranking(tipo_entidad=bancos, concepto=creditos, periodo=2024-12)`, `indicadores(tipo_entidad=cajas municipales, indicador=morosidad, periodo=2024-12)` |
| Pobreza 2020-2024 | ENAHO 2020-2024 (INEI) | `pobreza_nacional`, `pobreza_extrema`, `pobreza_area_urbana`, `pobreza_area_rural`, `pobreza_lima_metropolitana_provincia`, `pobreza_lima_provincias` | `salidas/indicadores.csv`, años 2020 a 2024 |
| Pobreza territorial 2024 | ENAHO 2024 | `pobreza_dep_01` a `pobreza_dep_25`, ámbitos con Lima desagregada, grupos de edad y sexo | `salidas/indicadores.csv`, año 2024 |

## Gráficos

1. Inflación a 12 meses, `PN01273PM`, 2020-01 a 2024-12 (`graficar_serie`).
2. PBI interanual, `PN01728AM`, 2020-01 a 2024-12 (`graficar_serie`).
3. Morosidad neta bancaria, `PN07746EM`, 2020-01 a 2024-12 (`graficar_serie`).
4. Serie de pobreza 2020-2024 (`graficando-enaho`).
5. Pobreza por área y por departamento en 2024 (`graficando-enaho`).
6. Mapa departamental y mapa de ámbitos con Lima desagregada (`mapeando-enaho`).

## Cuidados

- La inflación corresponde a Lima Metropolitana; el PBI y la morosidad son nacionales; la pobreza es anual y por dominio de la encuesta: distinto alcance y frecuencia.
- La morosidad tiene dos definiciones: la de la SBS (créditos atrasados / créditos directos) y la del BCRP (cartera atrasada neta / colocaciones netas). Se presentan por separado.
- Ninguna relación entre series macroeconómicas, financieras y de pobreza se presenta como causal.
- Las diferencias entre grupos de la ENAHO son estimaciones muestrales: diferencias pequeñas pueden no ser significativas.
