# Inflación, actividad, morosidad bancaria y pobreza monetaria en el Perú, 2020-2024

## 1. Pregunta de investigación

¿Cómo evolucionaron la inflación, la actividad económica, la morosidad bancaria y la pobreza monetaria del Perú entre 2020 y 2024, y qué brechas territoriales y urbano-rurales presentaba la pobreza en 2024?

El informe describe la trayectoria de cuatro dimensiones entre 2020 y 2024 con datos oficiales y caracteriza la distribución territorial y urbano-rural de la pobreza monetaria en 2024. La inflación corresponde a Lima Metropolitana; el producto bruto interno (PBI) y la morosidad, al conjunto del país; la pobreza, a la población residente de los dominios de la Encuesta Nacional de Hogares (ENAHO). El informe no pretende demostrar relaciones causales entre estas dimensiones: cuando las pone lado a lado, describe coincidencias en el tiempo.

## 2. Fuentes y metodología

- **Banco Central de Reserva del Perú (BCRP)**, consultado con el servidor MCP `bcrp`: inflación a 12 meses del IPC de Lima Metropolitana (`PN01273PM`, mensual, 2020-01 a 2024-12); variación porcentual anual del PBI (`PM04863AA`, 2020 a 2024); variación porcentual interanual mensual del PBI (`PN01728AM`, 2020-01 a 2024-12); y cartera atrasada neta sobre colocaciones netas de las empresas bancarias (`PN07746EM`, mensual, 2020-01 a 2024-12).
- **Superintendencia de Banca, Seguros y AFP (SBS)**, consultada con el servidor MCP `sbs`: créditos atrasados sobre créditos directos, rentabilidad patrimonial (ROE) y ratio de capital global del total de la banca múltiple (boletín B-2401, diciembre de cada año); concentración de los créditos directos (B-2332, diciembre de 2024); y morosidad de las cajas municipales (C-1301, diciembre de 2024).
- **ENAHO 2020-2024 (INEI)**: módulos 34 (sumaria) y 02 (miembros del hogar), residentes habituales, procesados con la skill `limpiando-enaho`. La pobreza monetaria y la pobreza extrema se ponderan por hogar con `factor07 × mieperho`, como en las cifras oficiales del INEI; como contraste se calcula la tasa nacional con el factor por persona `facpob07`. Los mapas unen los resultados con los límites oficiales del Instituto Geográfico Nacional (IGN) por código de ubigeo.
- **Indicadores construidos.** Para la inflación y la morosidad se toma el valor de diciembre de cada año, que resume la situación al cierre del periodo; para la actividad, la variación anual del PBI. La pobreza se presenta en el nivel nacional, por área de residencia, por departamento y por ámbito, con Lima Metropolitana (provincia de Lima) y Lima provincias por separado.
- **Validación.** Para cada año de 2020 a 2024, la limpieza reproduce las tasas oficiales del INEI (nacional, extrema, urbana, rural, Lima Metropolitana y Lima provincias) dentro de una tolerancia de {{lit:0.1 puntos}}, y el mapa reproduce las tasas departamentales de 2024 del informe técnico del INEI con la misma tolerancia (`salidas/validacion.txt`, `salidas/mapa_vs_referencia.csv`).

## 3. Resultados

**Cuadro 1.** Indicadores seleccionados, 2020-2024

| Indicador | Fuente | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| Inflación a 12 meses, diciembre (%) | BCRP, `PN01273PM` | {{bcrp.resumen(codigo=PN01273PM, desde=2020-12, hasta=2020-12).ultimo.valor|1}} | {{bcrp.resumen(codigo=PN01273PM, desde=2021-12, hasta=2021-12).ultimo.valor|1}} | {{bcrp.resumen(codigo=PN01273PM, desde=2022-12, hasta=2022-12).ultimo.valor|1}} | {{bcrp.resumen(codigo=PN01273PM, desde=2023-12, hasta=2023-12).ultimo.valor|1}} | {{bcrp.resumen(codigo=PN01273PM, desde=2024-12, hasta=2024-12).ultimo.valor|1}} |
| PBI, variación anual (%) | BCRP, `PM04863AA` | {{bcrp.resumen(codigo=PM04863AA, desde=2020, hasta=2020).ultimo.valor|1}} | {{bcrp.resumen(codigo=PM04863AA, desde=2021, hasta=2021).ultimo.valor|1}} | {{bcrp.resumen(codigo=PM04863AA, desde=2022, hasta=2022).ultimo.valor|1}} | {{bcrp.resumen(codigo=PM04863AA, desde=2023, hasta=2023).ultimo.valor|1}} | {{bcrp.resumen(codigo=PM04863AA, desde=2024, hasta=2024).ultimo.valor|1}} |
| Créditos atrasados / créditos directos, banca múltiple, diciembre (%) | SBS, B-2401 | {{sbs.indicadores(tipo_entidad=bancos, indicador=morosidad, periodo=2020-12).indicadores[0].total.valor|2}} | {{sbs.indicadores(tipo_entidad=bancos, indicador=morosidad, periodo=2021-12).indicadores[0].total.valor|2}} | {{sbs.indicadores(tipo_entidad=bancos, indicador=morosidad, periodo=2022-12).indicadores[0].total.valor|2}} | {{sbs.indicadores(tipo_entidad=bancos, indicador=morosidad, periodo=2023-12).indicadores[0].total.valor|2}} | {{sbs.indicadores(tipo_entidad=bancos, indicador=morosidad, periodo=2024-12).indicadores[0].total.valor|2}} |
| Cartera atrasada neta / colocaciones netas, diciembre (%) | BCRP, `PN07746EM` | {{bcrp.resumen(codigo=PN07746EM, desde=2020-12, hasta=2020-12).ultimo.valor|2}} | {{bcrp.resumen(codigo=PN07746EM, desde=2021-12, hasta=2021-12).ultimo.valor|2}} | {{bcrp.resumen(codigo=PN07746EM, desde=2022-12, hasta=2022-12).ultimo.valor|2}} | {{bcrp.resumen(codigo=PN07746EM, desde=2023-12, hasta=2023-12).ultimo.valor|2}} | {{bcrp.resumen(codigo=PN07746EM, desde=2024-12, hasta=2024-12).ultimo.valor|2}} |
| Pobreza monetaria (% de personas) | ENAHO | {{enaho.pobreza_nacional:2020}} | {{enaho.pobreza_nacional:2021}} | {{enaho.pobreza_nacional:2022}} | {{enaho.pobreza_nacional:2023}} | {{enaho.pobreza_nacional}} |
| Pobreza extrema (% de personas) | ENAHO | {{enaho.pobreza_extrema:2020}} | {{enaho.pobreza_extrema:2021}} | {{enaho.pobreza_extrema:2022}} | {{enaho.pobreza_extrema:2023}} | {{enaho.pobreza_extrema}} |
| Pobreza urbana (% de personas) | ENAHO | {{enaho.pobreza_area_urbana:2020}} | {{enaho.pobreza_area_urbana:2021}} | {{enaho.pobreza_area_urbana:2022}} | {{enaho.pobreza_area_urbana:2023}} | {{enaho.pobreza_area_urbana}} |
| Pobreza rural (% de personas) | ENAHO | {{enaho.pobreza_area_rural:2020}} | {{enaho.pobreza_area_rural:2021}} | {{enaho.pobreza_area_rural:2022}} | {{enaho.pobreza_area_rural:2023}} | {{enaho.pobreza_area_rural}} |

1. **La inflación subió hasta mediados de 2022 y volvió en 2024 a un nivel cercano al de 2020.** La inflación a 12 meses de Lima Metropolitana pasó de {{bcrp.resumen(codigo=PN01273PM, desde=2020-12, hasta=2020-12).ultimo.valor|1}} % en diciembre de 2020 a un máximo de {{bcrp.resumen(codigo=PN01273PM, desde=2020-01, hasta=2024-12).maximo.valor|1}} % en {{bcrp.resumen(codigo=PN01273PM, desde=2020-01, hasta=2024-12).maximo.periodo}}, y cerró diciembre de 2024 en {{bcrp.resumen(codigo=PN01273PM, desde=2024-12, hasta=2024-12).ultimo.valor|1}} % (BCRP, `PN01273PM`, 2020-01 a 2024-12); su promedio en los cinco años fue {{bcrp.resumen(codigo=PN01273PM, desde=2020-01, hasta=2024-12).promedio|1}} %.

2. **La actividad económica atravesó una caída, un rebote, una desaceleración, una contracción leve y una recuperación.** El PBI registró una variación anual de {{bcrp.resumen(codigo=PM04863AA, desde=2020, hasta=2020).ultimo.valor|1}} % en 2020, de {{bcrp.resumen(codigo=PM04863AA, desde=2021, hasta=2021).ultimo.valor|1}} % en 2021, de {{bcrp.resumen(codigo=PM04863AA, desde=2022, hasta=2022).ultimo.valor|1}} % en 2022, de {{bcrp.resumen(codigo=PM04863AA, desde=2023, hasta=2023).ultimo.valor|1}} % en 2023 y de {{bcrp.resumen(codigo=PM04863AA, desde=2024, hasta=2024).ultimo.valor|1}} % en 2024 (BCRP, `PM04863AA`). En la serie mensual, la variación interanual tocó su mínimo de {{bcrp.resumen(codigo=PN01728AM, desde=2020-01, hasta=2024-12).minimo.valor|1}} % en {{bcrp.resumen(codigo=PN01728AM, desde=2020-01, hasta=2024-12).minimo.periodo}} y su máximo de {{bcrp.resumen(codigo=PN01728AM, desde=2020-01, hasta=2024-12).maximo.valor|1}} % en {{bcrp.resumen(codigo=PN01728AM, desde=2020-01, hasta=2024-12).maximo.periodo}}, un rebote que refleja la comparación con el mínimo del año anterior (BCRP, `PN01728AM`, 2020-01 a 2024-12).

3. **La morosidad bancaria aumentó entre 2021 y 2023 y retrocedió en 2024.** Los créditos atrasados de la banca múltiple representaron {{sbs.indicadores(tipo_entidad=bancos, indicador=morosidad, periodo=2020-12).indicadores[0].total.valor|2}} % de los créditos directos en diciembre de 2020, {{sbs.indicadores(tipo_entidad=bancos, indicador=morosidad, periodo=2023-12).indicadores[0].total.valor|2}} % en diciembre de 2023 y {{sbs.indicadores(tipo_entidad=bancos, indicador=morosidad, periodo=2024-12).indicadores[0].total.valor|2}} % en diciembre de 2024 (SBS, boletín B-2401). La serie neta del BCRP muestra el mismo perfil: alcanzó su máximo de {{bcrp.resumen(codigo=PN07746EM, desde=2020-01, hasta=2024-12).maximo.valor|2}} % en {{bcrp.resumen(codigo=PN07746EM, desde=2020-01, hasta=2024-12).maximo.periodo}} y cerró 2024 en {{bcrp.resumen(codigo=PN07746EM, desde=2024-12, hasta=2024-12).ultimo.valor|2}} % (BCRP, `PN07746EM`). En diciembre de 2024, las entidades bancarias con mayor morosidad fueron {{sbs.indicadores(tipo_entidad=bancos, indicador=morosidad, periodo=2024-12).indicadores[0].valores[0].entidad}}, con {{sbs.indicadores(tipo_entidad=bancos, indicador=morosidad, periodo=2024-12).indicadores[0].valores[0].valor|2}} %, y {{sbs.indicadores(tipo_entidad=bancos, indicador=morosidad, periodo=2024-12).indicadores[0].valores[1].entidad}}, con {{sbs.indicadores(tipo_entidad=bancos, indicador=morosidad, periodo=2024-12).indicadores[0].valores[1].valor|2}} % (SBS, B-2401, 2024-12).

4. **El contexto financiero de 2024 combinó mayor rentabilidad que en 2020 y alta concentración del crédito.** La rentabilidad patrimonial (ROE) de la banca múltiple pasó de {{sbs.indicadores(tipo_entidad=bancos, indicador=roe, periodo=2020-12).indicadores[0].total.valor|1}} % en diciembre de 2020 a {{sbs.indicadores(tipo_entidad=bancos, indicador=roe, periodo=2024-12).indicadores[0].total.valor|1}} % en diciembre de 2024 (SBS, B-2401), y su ratio de capital global fue {{sbs.indicadores(tipo_entidad=bancos, indicador=solvencia, periodo=2024-12).indicadores[0].total.valor|1}} % al 30 de noviembre de 2024 (SBS, B-2401, edición de 2024-12). Los cuatro bancos más grandes concentraron {{sbs.ranking(tipo_entidad=bancos, concepto=creditos, periodo=2024-12).ranking[3].acumulado_pct|1}} % de los créditos directos, y el primero, {{sbs.ranking(tipo_entidad=bancos, concepto=creditos, periodo=2024-12).ranking[0].entidad}}, {{sbs.ranking(tipo_entidad=bancos, concepto=creditos, periodo=2024-12).ranking[0].participacion_pct|1}} % (SBS, B-2332, 2024-12). Las cajas municipales registraron una morosidad de {{sbs.indicadores(tipo_entidad=cajas municipales, indicador=morosidad, periodo=2024-12).indicadores[0].total.valor|2}} % en diciembre de 2024 (SBS, C-1301), superior a la de la banca múltiple.

5. **La pobreza monetaria bajó en 2021, volvió a subir en 2022 y 2023 y retrocedió en 2024 sin regresar al nivel de 2021.** La pobreza monetaria nacional fue {{enaho.pobreza_nacional:2020}} % en 2020, {{enaho.pobreza_nacional:2021}} % en 2021, {{enaho.pobreza_nacional:2022}} % en 2022, {{enaho.pobreza_nacional:2023}} % en 2023 y {{enaho.pobreza_nacional}} % en 2024 (ENAHO 2020-2024, `pobreza_nacional`). La pobreza extrema siguió un perfil distinto: tras bajar de {{enaho.pobreza_extrema:2020}} % en 2020 a {{enaho.pobreza_extrema:2021}} % en 2021, subió hasta {{enaho.pobreza_extrema:2023}} % en 2023 y fue {{enaho.pobreza_extrema}} % en 2024, por encima de su nivel de 2020 (ENAHO 2020-2024, `pobreza_extrema`).

6. **En 2024 la pobreza rural siguió muy por encima de la urbana, aunque la brecha se redujo desde 2020.** La pobreza rural fue {{enaho.pobreza_area_rural}} % y la urbana {{enaho.pobreza_area_urbana}} % en 2024, frente a {{enaho.pobreza_area_rural:2020}} % y {{enaho.pobreza_area_urbana:2020}} % en 2020 (ENAHO 2020 y 2024, `pobreza_area_rural` y `pobreza_area_urbana`). La reducción se concentró en el área rural; la urbana llegó a {{enaho.pobreza_area_urbana:2023}} % en 2023, por encima de su nivel de 2020, antes de bajar en 2024 (ENAHO 2023 y 2024, `pobreza_area_urbana`).

7. **En 2024 la pobreza fue más alta en Cajamarca, Loreto y Puno, y más baja en Ica, Moquegua y Madre de Dios.** Las tasas más altas correspondieron a Cajamarca ({{enaho.pobreza_dep_06}} %), Loreto ({{enaho.pobreza_dep_16}} %) y Puno ({{enaho.pobreza_dep_21}} %), seguidos de Pasco ({{enaho.pobreza_dep_19}} %) y Huánuco ({{enaho.pobreza_dep_10}} %); las más bajas, a Ica ({{enaho.pobreza_dep_11}} %), Moquegua ({{enaho.pobreza_dep_18}} %), Madre de Dios ({{enaho.pobreza_dep_17}} %), Lambayeque ({{enaho.pobreza_dep_14}} %) y Arequipa ({{enaho.pobreza_dep_04}} %) (ENAHO 2024, `pobreza_dep_*`). Con Lima desagregada, la pobreza fue {{enaho.pobreza_lima_metropolitana_provincia}} % en Lima Metropolitana (provincia de Lima) y {{enaho.pobreza_lima_provincias}} % en Lima provincias, mientras que en la Provincia Constitucional del Callao alcanzó {{enaho.pobreza_dep_07}} % (ENAHO 2024, `pobreza_lima_metropolitana_provincia`, `pobreza_lima_provincias` y `pobreza_dep_07`).

8. **La pobreza de 2024 afectó más a la niñez y casi por igual a hombres y mujeres.** La tasa fue {{enaho.pobreza_edad_0_14}} % entre las personas de 0 a 14 años, frente a {{enaho.pobreza_edad_45_59}} % entre las de 45 a 59 años y {{enaho.pobreza_edad_60_mas}} % entre las de 60 años y más (ENAHO 2024, `pobreza_edad_*`); entre hombres fue {{enaho.pobreza_sexo_hombres}} % y entre mujeres {{enaho.pobreza_sexo_mujeres}} % (ENAHO 2024, `pobreza_sexo_*`), una diferencia que no puede distinguirse del error muestral sin un intervalo de confianza.

9. **Puestas lado a lado, las fuentes muestran coincidencias en el tiempo, no relaciones causales.** El año de mayor pobreza del periodo, 2020, coincidió con la mayor contracción del PBI ({{bcrp.resumen(codigo=PM04863AA, desde=2020, hasta=2020).ultimo.valor|1}} %, BCRP `PM04863AA`; pobreza {{enaho.pobreza_nacional:2020}} %, ENAHO 2020), y la menor pobreza, 2021, con el rebote ({{bcrp.resumen(codigo=PM04863AA, desde=2021, hasta=2021).ultimo.valor|1}} %, BCRP `PM04863AA`; pobreza {{enaho.pobreza_nacional:2021}} %, ENAHO 2021). El aumento de la pobreza en 2022 y 2023 coincidió con la inflación más alta del periodo y con la contracción del PBI de 2023 ({{bcrp.resumen(codigo=PM04863AA, desde=2023, hasta=2023).ultimo.valor|1}} %, BCRP `PM04863AA`), mientras que la morosidad bancaria alcanzó sus valores más altos entre fines de 2023 y mediados de 2024 (SBS B-2401; BCRP `PN07746EM`).

## 4. Visualizaciones

**Figura 1.** Inflación a 12 meses del IPC de Lima Metropolitana, 2020-01 a 2024-12 (BCRP, `PN01273PM`).

![Inflación a 12 meses, PN01273PM](../figuras/bcrp_PN01273PM_2020-01_2024-12.png)

**Figura 2.** Variación porcentual interanual del PBI, 2020-01 a 2024-12 (BCRP, `PN01728AM`).

![PBI interanual, PN01728AM](../figuras/bcrp_PN01728AM_2020-01_2024-12.png)

**Figura 3.** Cartera atrasada neta sobre colocaciones netas de las empresas bancarias, 2020-01 a 2024-12 (BCRP, `PN07746EM`).

![Morosidad neta bancaria, PN07746EM](../figuras/bcrp_PN07746EM_2020-01_2024-12.png)

**Figura 4.** Evolución de la pobreza monetaria, 2020-2024 (ENAHO).

![Pobreza monetaria 2020-2024](../figuras/pobreza_serie_2020_2024.png)

**Figura 5.** Pobreza monetaria por área de residencia, 2024 (ENAHO 2024).

![Pobreza por área](../figuras/pobreza_por_area.png)

**Figura 6.** Pobreza monetaria por departamento, 2024 (ENAHO 2024).

![Pobreza por departamento](../figuras/pobreza_por_departamento.png)

**Figura 7.** Mapa de la pobreza monetaria por departamento, 2024 (ENAHO 2024; límites del IGN).

![Mapa departamental](../mapas/pobreza_departamento.png)

**Figura 8.** Mapa de la pobreza monetaria por ámbito, con Lima Metropolitana y Lima provincias por separado, 2024 (ENAHO 2024; límites del IGN).

![Mapa por ámbitos](../mapas/pobreza_ambitos.png)

## 5. Interpretación

Entre 2020 y 2024 la economía peruana pasó por un choque, un rebote, un episodio inflacionario y una contracción leve en 2023 antes de recuperarse. La pobreza monetaria acompañó ese recorrido: descendió con el rebote de 2021, aumentó en 2022 y 2023, años de inflación elevada (2022) y de contracción del PBI (2023), y retrocedió en 2024, cuando la inflación ya había bajado y el PBI volvió a crecer. Estas coincidencias son asociaciones temporales: con solo cinco observaciones anuales no es posible separar el efecto de los precios, del empleo o de las transferencias públicas.

Las series no tienen el mismo nivel de agregación. La inflación del BCRP mide los precios de Lima Metropolitana y no los de las zonas rurales o de otros departamentos; el PBI y la morosidad son agregados nacionales mensuales o anuales; la pobreza proviene de una encuesta anual representativa por dominio. Por eso el informe no relaciona la morosidad o la inflación con la pobreza de un departamento concreto.

La morosidad bancaria tuvo un perfil propio: subió en la segunda mitad de 2020, tuvo un valor de diciembre similar en 2020 y 2021, volvió a subir durante 2022 y 2023 y bajó desde mediados de 2024. Las dos fuentes, con definiciones distintas (créditos atrasados sobre créditos directos en la SBS; cartera atrasada neta sobre colocaciones netas en el BCRP), muestran la misma dirección. El aumento de la rentabilidad entre 2020 y 2024 indica que el deterioro de la cartera no impidió la recuperación de las utilidades del sistema, aunque la morosidad fue mayor en algunas entidades bancarias y en las cajas municipales.

En el territorio, la pobreza de 2024 dibuja un patrón definido: tasas altas en la sierra norte (Cajamarca), la Amazonía (Loreto) y el altiplano (Puno), y tasas bajas en la costa sur (Ica, Moquegua, Arequipa). La brecha urbano-rural se redujo porque la pobreza rural bajó más que la urbana, no porque la urbana mejorara: la pobreza urbana de 2023 superó la de 2020. Lima Metropolitana tuvo una tasa cercana a la nacional, y el Callao presentó una tasa superior a la de la provincia de Lima.

## 6. Limitaciones

- **Cobertura geográfica de la inflación.** `PN01273PM` mide los precios de Lima Metropolitana; no representa la inflación que enfrentan los hogares rurales o de otros departamentos.
- **Definiciones de morosidad.** La SBS (créditos atrasados / créditos directos) y el BCRP (cartera atrasada neta / colocaciones netas) usan definiciones distintas; sus valores se presentan por separado y no deben sumarse ni promediarse.
- **Fecha del ratio de capital global.** El boletín B-2401 de diciembre de 2024 publica el ratio de capital global al 30 de noviembre de 2024.
- **Error muestral de la ENAHO.** Las tasas son estimaciones de una encuesta por muestreo; el informe no calcula intervalos de confianza. Diferencias pequeñas, como la de hombres y mujeres o la de departamentos con tasas cercanas (Pasco y Huánuco), pueden no ser estadísticamente significativas, y las estimaciones departamentales tienen mayor error que las nacionales.
- **Ponderador.** Las tasas oficiales se ponderan por hogar (`factor07 × mieperho`); con el factor por persona (`facpob07`), la pobreza nacional de 2024 es {{enaho.pobreza_nacional_personas}} %, frente a {{enaho.pobreza_nacional}} % con el ponderador oficial (ENAHO 2024).
- **Pocas observaciones anuales.** Cinco años no permiten estimar relaciones entre las series; las coincidencias descritas en la sección 5 son descriptivas.
- **Gráficos.** En la figura 4 las etiquetas de 2020 de la pobreza urbana y de Lima se superponen, y en el recuadro de Lima y Callao de la figura 8 los rótulos de ambos ámbitos se superponen; en la figura 3 el subtítulo con el nombre oficial de la serie aparece cortado. Las cifras correctas están en el cuadro 1 y en la sección 3.

## 7. Reproducibilidad

- **ENAHO:** `uv run .claude/skills/descargando-enaho/scripts/descargar.py` (descarga), `uv run .claude/skills/limpiando-enaho/scripts/limpiar.py` (limpieza y validación; escribe `salidas/indicadores.csv` y `salidas/validacion.txt`), `uv run .claude/skills/graficando-enaho/scripts/graficar.py` (figuras 4 a 6) y `uv run .claude/skills/mapeando-enaho/scripts/mapear.py` (figuras 7 y 8; escribe `salidas/mapa_vs_referencia.csv`).
- **BCRP:** servidor `mcp/server.py`, herramientas `resumen` y `graficar_serie` con los códigos `PN01273PM`, `PM04863AA`, `PN01728AM` y `PN07746EM` y los periodos del cuadro 1.
- **SBS:** servidor `mcp-sbs-peru`, herramientas `indicadores` (bancos: morosidad, ROE y solvencia; cajas municipales: morosidad) y `ranking` (bancos, créditos), con los periodos indicados en cada hallazgo.
- **Verificación de consistencia:** `salidas/consistencia.md` no registra fallas. Las cifras de este informe coinciden con una nueva consulta a sus herramientas; las tasas departamentales coinciden con el informe técnico del INEI y con el mapa; la tasa nacional queda entre la urbana y la rural; y la inflación publicada coincide con la recalculada desde el índice del IPC. La única diferencia registrada es la esperada entre la morosidad de la SBS y la del BCRP de diciembre de 2024, que responden a definiciones distintas.
- **Informe:** `uv run .claude/skills/informando-peru/scripts/armar_informe.py` resuelve los marcadores de `informes/borrador.md` y escribe este informe; `uv run .claude/skills/verificando-consistencia/scripts/verificar.py` contrasta las cifras y escribe `salidas/consistencia.md`.
