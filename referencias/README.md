# Referencias oficiales

Este directorio contiene las cifras de pobreza monetaria que publica el Instituto Nacional de Estadística e Informática (INEI), contra las que se validan los resultados del proyecto, y los límites territoriales oficiales del Instituto Geográfico Nacional (IGN) que usan los mapas.

## Cifras de pobreza monetaria del INEI

### Fuente

**Cita en formato APA 7:**
> Instituto Nacional de Estadística e Informática. (2025). *Perú: Evolución de la pobreza monetaria, 2015-2024: Informe técnico*. https://cdn.www.gob.pe/uploads/document/file/8058556/6763186-peru-evolucion-de-la-pobreza-monetaria-2015-2024.pdf

- **Publicación:** Lima, mayo de 2025, según la presentación del informe.
- **SHA-256 del PDF:** `ed964c41c963f0ac5ce11b1713680ec93519838b9db0cd8fa139e6bb922d6c73`.
- **Anexo estadístico (Excel):** `https://cdn.www.gob.pe/uploads/document/file/8058555/6763186-anexo-estadistico-excel.zip`. Su archivo `03_FGT de Pobreza 2015-2024_informe.xlsx` repite el Cuadro III.1 (hoja `3.1`) y el Cuadro III.4 (hoja `3.4`).
- **Fecha de consulta y verificación:** 5 de noviembre de 2026.

Las páginas citadas son las impresas en el informe. En el visor del PDF, cada una corresponde al número impreso más 2.

### `inei_pobreza_2024.csv`

Columnas: `ambito, ccdd, valor, ic_inf, ic_sup, cv, cuadro, pagina, nota`. Cada fila es la columna 2024 de un cuadro del informe, con su intervalo de confianza al 95 % y su coeficiente de variación:

| Filas | Cuadro y página |
|---|---|
| Nacional, urbana, rural y Lima Metropolitana con Callao (dominio 8) | Cuadro III.1, p. 219 |
| Los 24 departamentos con cifra publicada, el Callao, Lima Metropolitana (provincia 1501) y Lima provincias | Cuadro III.1, p. 220 |
| Pobreza extrema nacional | Cuadro III.4, p. 223 |

- **Transcripción:** cada valor se transcribió del informe y se cotejó de nuevo, fila por fila, con el texto del PDF: valor, límites del intervalo y CV.
- **Cifras referenciales:** el INEI considera referenciales las cifras con un CV mayor a 15 % (nota del Cuadro III.1 y p. 71). Son Ica (15.6 %), Moquegua (16.3 %) y Madre de Dios (19.5 %), marcadas en la columna `nota`.
- **Años 2020 a 2023:** los mismos cuadros traen la serie 2015-2024, pero sin intervalos ni CV para esos años. Sus metas están en `METAS_INEI` de `.claude/skills/limpiando-enaho/scripts/limpiar.py`, con el mismo cuadro y la misma página.

### Lima, departamento 15: sin cifra publicada por el INEI

El INEI publica en el Cuadro III.1 dos ámbitos para el departamento de Lima, pero no una cifra del departamento en conjunto:

- **Lima Metropolitana**, los 43 distritos de la provincia de Lima (provincia 1501): **27.6 %** (IC 95 %: [25.0, 30.1], CV 4.7 %).
- **Lima provincias**, las provincias de Barranca, Cajatambo, Canta, Cañete, Huaral, Huarochirí, Huaura, Oyón y Yauyos: **21.7 %** (IC 95 %: [18.3, 25.1], CV 8.0 %).

Por eso la tabla no tiene una fila para el departamento 15, y ninguna comprobación del proyecto lo valida contra el INEI. Se validan los dos ámbitos. Una versión anterior incluía 27.1 % para el departamento completo: era un cálculo del curso con los mismos microdatos, no una cifra del INEI, y se retiró.

La cifra de 28.2 % (dominio 8 de la ENAHO) corresponde a Lima Metropolitana **con** el Callao, que el INEI rotula «Lima Metropolitana y Prov. Const. del Callao».

### Validación sin circularidad

Se retiraron los archivos del curso (`pobreza_departamento_2024.csv` y `mapa_pobreza_2024.png`), cuyas cifras se calcularon con los mismos microdatos que replica el proyecto. Todas las metas de validación son cifras publicadas por el INEI, con su cuadro y su página.

## Límites cartográficos oficiales (IGN / OCHA HDX COD-AB)

Para la representación espacial de la pobreza departamental y por ámbitos territoriales, el proyecto utiliza las delimitaciones cartográficas oficiales del Instituto Geográfico Nacional (IGN), publicadas bajo los estándares de Common Operational Datasets (COD-AB) por la Oficina de las Naciones Unidas para la Coordinación de Asuntos Humanitarios (UN OCHA).

### Fuente primaria y licencia

**Cita en formato APA 7:**
> Instituto Geográfico Nacional & Oficina de las Naciones Unidas para la Coordinación de Asuntos Humanitarios. (2020). *Peru: Subnational Administrative Boundaries (COD-AB)* [Conjunto de datos]. Humanitarian Data Exchange. Licencia CC BY-IGO. https://data.humdata.org/dataset/cod-ab-per

- **Publicación:** 14 de julio de 2020 (versión validada COD-AB).
- **URL del conjunto de datos:** `https://data.humdata.org/dataset/cod-ab-per`
- **Archivo fuente:** `per_admin_boundaries.geojson.zip` (45.1 MB)
- **SHA-256 del archivo zip:** `2f0ec51b7a0899b407546aa644621e1c3255cba59fdda76fcde6975ca6baafb3`
- **Licencia:** Creative Commons Attribution for Intergovernmental Organizations (CC BY-IGO), que autoriza expresamente la redistribución y adaptación manteniendo la atribución.

### Capas procesadas en `referencias/`

El script `scripts/preparar_limites.py` procesa los límites oficiales en proyección EPSG:4326 y simplifica la topología conservando la integridad de fronteras e islas:

1. **`referencias/limites_departamentales_ign.geojson` (25 unidades):**
   - Corresponde a los 24 departamentos y la Provincia Constitucional del Callao.
   - Propiedades: `ccdd` (código oficial de 2 dígitos "01" a "25"), `FIRST_IDDP` (alias idéntico a `ccdd` para mantener compatibilidad con las consignas del curso), `NOMBDEP` (nombre en mayúsculas) y `nombre`.
   - Utilizado en `mapas/pobreza_departamento.png` y en el tablero interactivo.

2. **`referencias/limites_ambitos_ign.geojson` (26 ámbitos territoriales):**
   - Desagrega el departamento 15 en **Lima Metropolitana (provincia 1501)** y **Lima provincias** (unión de las 9 provincias restantes de Lima: Barranca, Cajatambo, Canta, Cañete, Huaral, Huarochirí, Huaura, Oyón y Yauyos).
   - Reconstruye de forma geométrica exacta el contorno del departamento de Lima (diferencia de área de 0.0 %).
   - Utilizado en `mapas/pobreza_ambitos.png` para reflejar las brechas socioeconómicas identificadas por el INEI.
