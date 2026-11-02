# Inflación, actividad y pobreza en el Perú: 2020-2024 y la foto territorial de 2024

## 1. Pregunta de investigación

¿Cómo evolucionaron la inflación y la actividad económica del Perú entre 2020 y 2024, y qué brechas territoriales y urbano-rurales presentaba la pobreza monetaria en 2024?

El informe cubre tres periodos distintos: las series mensuales del BCRP de enero de 2020 a diciembre de 2024, el boletín de la SBS de diciembre de 2024 y la ENAHO 2024 del INEI, una encuesta anual con alcance nacional y departamental. No se pretende demostrar ninguna relación causal entre la macroeconomía y la pobreza.

## 2. Fuentes y metodología

- **BCRP**: `PN01273PM` (IPC de Lima Metropolitana, variación porcentual a 12 meses) y `PN01728AM` (PBI, variación porcentual interanual), ambas mensuales, de 2020-01 a 2024-12, consultadas con el servidor MCP `bcrp`.
- **SBS**: boletines B-2401 (indicadores de bancos), C-1301 (indicadores de cajas municipales) y B-2332 (ranking de créditos), periodo 2024-12, consultados con el servidor MCP `sbs`.
- **ENAHO 2024 (INEI)**: módulos 34 y 02, residentes habituales, factores de expansión `factor07 × mieperho` (hogar) y `facpob07` (persona), procesados con la skill `limpiando-enaho`. La pobreza por área y por departamento se pondera por hogar, como las cifras oficiales del INEI.
- El promedio anual del PBI es el promedio de las doce variaciones interanuales mensuales del año, no el crecimiento anual oficial.

## 3. Resultados

1. **Inflación (BCRP).** Según `PN01273PM`, la inflación a 12 meses pasó de {{bcrp.resumen(codigo=PN01273PM, desde=2020-12, hasta=2020-12).ultimo.valor|1}}% en diciembre de 2020 a {{bcrp.resumen(codigo=PN01273PM, desde=2021-12, hasta=2021-12).ultimo.valor|1}}% en diciembre de 2021, tocó su máximo de {{bcrp.resumen(codigo=PN01273PM, desde=2020-01, hasta=2024-12).maximo.valor|1}}% en {{bcrp.resumen(codigo=PN01273PM, desde=2020-01, hasta=2024-12).maximo.periodo}}, y cerró en {{bcrp.resumen(codigo=PN01273PM, desde=2022-12, hasta=2022-12).ultimo.valor|1}}% (2022), {{bcrp.resumen(codigo=PN01273PM, desde=2023-12, hasta=2023-12).ultimo.valor|1}}% (2023) y {{bcrp.resumen(codigo=PN01273PM, desde=2024-12, hasta=2024-12).ultimo.valor|1}}% (2024) en cada diciembre. Su mínimo del periodo fue {{bcrp.resumen(codigo=PN01273PM, desde=2020-01, hasta=2024-12).minimo.valor|1}}% en {{bcrp.resumen(codigo=PN01273PM, desde=2020-01, hasta=2024-12).minimo.periodo}}, y el promedio de los 60 meses, {{bcrp.resumen(codigo=PN01273PM, desde=2020-01, hasta=2024-12).promedio|1}}%.
2. **Actividad (BCRP).** Según `PN01728AM`, el PBI varió {{bcrp.resumen(codigo=PN01728AM, desde=2020-01, hasta=2024-12).minimo.valor|1}}% interanual en {{bcrp.resumen(codigo=PN01728AM, desde=2020-01, hasta=2024-12).minimo.periodo}} (su mínimo) y rebotó {{bcrp.resumen(codigo=PN01728AM, desde=2020-01, hasta=2024-12).maximo.valor|1}}% en {{bcrp.resumen(codigo=PN01728AM, desde=2020-01, hasta=2024-12).maximo.periodo}}. El promedio de las variaciones mensuales fue {{bcrp.resumen(codigo=PN01728AM, desde=2020-01, hasta=2020-12).promedio|1}}% en 2020, {{bcrp.resumen(codigo=PN01728AM, desde=2021-01, hasta=2021-12).promedio|1}}% en 2021, {{bcrp.resumen(codigo=PN01728AM, desde=2022-01, hasta=2022-12).promedio|1}}% en 2022, {{bcrp.resumen(codigo=PN01728AM, desde=2023-01, hasta=2023-12).promedio|1}}% en 2023 y {{bcrp.resumen(codigo=PN01728AM, desde=2024-01, hasta=2024-12).promedio|1}}% en 2024; diciembre de 2024 cerró en {{bcrp.resumen(codigo=PN01728AM, desde=2024-12, hasta=2024-12).ultimo.valor|1}}%.
3. **Pobreza por área (ENAHO 2024).** La pobreza monetaria nacional fue {{enaho.pobreza_nacional}}% y la pobreza extrema, {{enaho.pobreza_extrema}}% (indicadores `pobreza_nacional` y `pobreza_extrema`). En el área rural fue {{enaho.pobreza_area_rural}}% y en la urbana, {{enaho.pobreza_area_urbana}}% (`pobreza_area_rural`, `pobreza_area_urbana`): la pobreza rural fue claramente mayor. Lima Metropolitana tuvo {{enaho.pobreza_lima_metropolitana}}% (`pobreza_lima_metropolitana`).
4. **Pobreza por departamento (ENAHO 2024).** Cajamarca ({{enaho.pobreza_dep_06}}%), Loreto ({{enaho.pobreza_dep_16}}%), Puno ({{enaho.pobreza_dep_21}}%), Pasco ({{enaho.pobreza_dep_19}}%) y Huánuco ({{enaho.pobreza_dep_10}}%) fueron los cinco departamentos con mayor pobreza; Ica ({{enaho.pobreza_dep_11}}%), Moquegua ({{enaho.pobreza_dep_18}}%), Madre de Dios ({{enaho.pobreza_dep_17}}%), Lambayeque ({{enaho.pobreza_dep_14}}%) y Arequipa ({{enaho.pobreza_dep_04}}%) fueron los cinco con menor pobreza (indicadores `pobreza_dep_06`, `_16`, `_21`, `_19`, `_10`, `_11`, `_18`, `_17`, `_14` y `_04`). El Callao tuvo {{enaho.pobreza_dep_07}}% y Lima, {{enaho.pobreza_dep_15}}%, por lo que ambos van separados.
5. **Contexto financiero (SBS, diciembre de 2024).** La morosidad (créditos atrasados sobre créditos directos) fue {{sbs.indicadores(tipo_entidad=bancos, indicador=morosidad, periodo=2024-12).indicadores[0].total.valor|2}}% en la banca múltiple (B-2401) y {{sbs.indicadores(tipo_entidad=cajas municipales, indicador=morosidad, periodo=2024-12).indicadores[0].total.valor|2}}% en las cajas municipales (C-1301). Los tres mayores bancos concentraron {{sbs.ranking(tipo_entidad=bancos, concepto=creditos, periodo=2024-12, limite=3).ranking[2].acumulado_pct|1}}% de los créditos directos (B-2332).
6. **Ambas fuentes lado a lado.** Al cierre de 2024, la inflación de Lima Metropolitana volvió a {{bcrp.resumen(codigo=PN01273PM, desde=2024-12, hasta=2024-12).ultimo.valor|1}}% (`PN01273PM`, 2024-12) y el PBI crecía {{bcrp.resumen(codigo=PN01728AM, desde=2024-12, hasta=2024-12).ultimo.valor|1}}% interanual (`PN01728AM`, 2024-12), mientras que la ENAHO 2024 registraba una pobreza nacional de {{enaho.pobreza_nacional}}% con la brecha rural-urbana y la dispersión departamental descritas arriba. La correlación mensual entre inflación y PBI interanual en 2020-2024 fue {{bcrp.comparar_series(codigo_a=PN01273PM, codigo_b=PN01728AM, desde=2020-01, hasta=2024-12).correlacion|2}}, prácticamente nula, en una muestra dominada por la pandemia.

## 4. Visualizaciones

![Inflación a 12 meses, BCRP PN01273PM](../figuras/bcrp_PN01273PM_2020-01_2024-12.png)

![PBI interanual, BCRP PN01728AM](../figuras/bcrp_PN01728AM_2020-01_2024-12.png)

![Pobreza por área, ENAHO 2024](../figuras/pobreza_por_area.png)

![Pobreza por departamento, ENAHO 2024](../figuras/pobreza_por_departamento.png)

![Mapa departamental de la pobreza, ENAHO 2024](../mapas/pobreza_departamento.png)

## 5. Interpretación

- La inflación tuvo un ciclo claro: subió desde 2020, alcanzó su máximo a mediados de 2022 y volvió hacia el rango habitual hacia fines de 2024, según `PN01273PM`.
- La actividad fue muy volátil en 2020 y 2021 por el efecto base de la pandemia: la caída y el rebote de `PN01728AM` son en gran parte espejos uno del otro, no dos fenómenos independientes.
- La pobreza de 2024 se asocia a un patrón territorial: mayor en departamentos andinos y amazónicos del norte, centro y sur (Cajamarca, Loreto, Puno) y menor en departamentos costeros del sur y del norte (Ica, Moquegua, Lambayeque). La rural supera a la urbana. Son asociaciones descriptivas de una encuesta de un año.
- La inflación (Lima Metropolitana, mensual, serie nacional de precios) y la pobreza (hogares, anual, por departamento) tienen distinto nivel de agregación y periodo: ponerlas juntas ilustra el contexto, no prueba relación alguna.

## 6. Limitaciones

- El IPC del BCRP es de Lima Metropolitana, no nacional; la pobreza de la ENAHO es nacional y por departamento.
- La ENAHO se procesó solo para 2024: este informe no describe cómo cambió la pobreza entre 2020 y 2024.
- La serie de PBI es la variación interanual mensual; los promedios anuales de este informe no son el crecimiento anual oficial.
- Las cifras de pobreza vienen de una muestra y tienen error de muestreo; las diferencias entre departamentos cercanos pueden no ser significativas.
- La morosidad de la SBS es una foto de un mes (2024-12) y no hay serie 2020-2024 en este informe.
- Todas las herramientas respondieron sin errores durante la ejecución.

## 7. Reproducibilidad

- Plan: `informes/plan_analisis.md`; borrador: `informes/borrador.md`.
- ENAHO: `.claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024` produce `salidas/personas_2024.parquet`, `salidas/indicadores.csv` y `salidas/validacion.txt`; `graficar.py` y `mapear.py` producen `figuras/` y `mapas/`.
- BCRP: series `PN01273PM` y `PN01728AM`, 2020-01 a 2024-12.
- SBS: B-2401, C-1301 y B-2332, 2024-12.
- Verificación de consistencia (`verificando-consistencia`, detalle en `salidas/consistencia.md`): todas las comprobaciones resultaron OK, sin diferencias, fallas ni datos no verificables; incluye el contraste de cada cifra de este informe con una nueva consulta a sus herramientas.
- Regenerar: `uv run .claude/skills/informando-peru/scripts/armar_informe.py`.
