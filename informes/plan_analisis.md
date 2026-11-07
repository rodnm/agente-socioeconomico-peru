# Plan de análisis

**Pregunta.** ¿Cómo evolucionaron la inflación, la actividad económica, la morosidad bancaria y la pobreza monetaria del Perú entre 2020 y 2024, y qué brechas territoriales y urbano-rurales presentaba la pobreza en 2024?

## Fuentes e indicadores

| Dimensión | Fuente | Serie o indicador | Argumentos |
|---|---|---|---|
| Inflación | BCRP | `PN01273PM` (IPC Lima Metropolitana, var. % 12 meses) | 2020-01 a 2024-12 |
| Actividad | BCRP | `PN01728AM` (PBI, var. % interanual, mensual) y `PM04923AA` (PBI real, var. % anual) | 2020-01 a 2024-12; 2020 a 2024 |
| Morosidad neta | BCRP | `PN07746EM` (cartera atrasada neta / colocaciones netas, empresas bancarias) | 2020-01 a 2024-12 |
| Morosidad bancaria | SBS | `B-2401` vía `indicadores` (bancos, morosidad, cierre de diciembre 2020 a 2024) | periodo `AAAA-12` |
| Contexto financiero | SBS | `C-1301` vía `indicadores` (cajas municipales, 2024-12) | `2024-12` |
| Pobreza 2020-2024 | ENAHO (INEI) | `pobreza_nacional`, `pobreza_area_urbana`, `pobreza_area_rural`, Lima | selector de año |
| Foto 2024 | ENAHO (INEI) | `pobreza_dep_XX`, `pobreza_lima_metropolitana_provincia`, `pobreza_lima_provincias` | 2024 |

## Gráficos

- BCRP: `PN01273PM` y `PN07746EM` (`graficar_serie`), `PM04923AA` anual.
- ENAHO: `pobreza_serie_2020_2024`, `pobreza_por_area`, `pobreza_por_departamento`.
- Mapas: `pobreza_departamento` (25 departamentos) y `pobreza_ambitos` (26 ámbitos).

## Cautelas

- La morosidad del BCRP es neta (cartera atrasada neta de provisiones) y la de la SBS es bruta (créditos atrasados / directos): se presentan por separado.
- Series nacionales mensuales frente a una encuesta anual: solo asociaciones.
