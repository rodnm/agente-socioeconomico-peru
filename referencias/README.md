# Referencias oficiales de pobreza monetaria (INEI 2024)

Este directorio contiene las cifras oficiales de referencia sobre la incidencia de la pobreza monetaria en el Perú correspondientes al año 2024, transcritas directamente del informe técnico publicado por el Instituto Nacional de Estadística e Informática (INEI) y su anexo estadístico en Excel.

## Fuente primaria oficial

**Cita en formato APA 7:**
> Instituto Nacional de Estadística e Informática. (2025). *Perú: Evolución de la pobreza monetaria 2015-2024: Informe técnico*. Lima: INEI. https://cdn.www.gob.pe/uploads/document/file/8058556/6763186-peru-evolucion-de-la-pobreza-monetaria-2015-2024.pdf

- **Publicación:** Mayo de 2025.
- **URL del documento principal (PDF):** `https://cdn.www.gob.pe/uploads/document/file/8058556/6763186-peru-evolucion-de-la-pobreza-monetaria-2015-2024.pdf`
- **SHA-256 del archivo PDF:** `ed964c41c963f0ac5ce11b1713680ec93519838b9db0cd8fa139e6bb922d6c73`
- **URL del anexo estadístico (Excel):** `https://cdn.www.gob.pe/uploads/document/file/8058555/6763186-anexo-estadistico-excel.zip`
- **Fecha de consulta y verificación:** 5 de noviembre de 2026.

## Procedimiento de transcripción y rigor científico

1. **Tabla base (`referencias/inei_pobreza_2024.csv`):**
   - Se transcribieron las tasas de pobreza monetaria, intervalos de confianza al 95 % (límite inferior y superior) y coeficientes de variación (C.V.) reportados en el **Cuadro N° III.1** (pp. 219–220 del informe impreso) y en el **Cuadro N° III.4** (p. 72 / Anexo).
   - Las cifras departamentales y de ámbitos provienen de la hoja `3.1` del archivo `03_FGT de Pobreza 2015-2024_informe.xlsx` incluido en el anexo oficial.
   - Conforme a la metodología del INEI, los resultados con un coeficiente de variación mayor al 15 % (Ica con 15.6 %, Moquegua con 16.3 % y Madre de Dios con 19.5 %) están clasificados explícitamente como de carácter **referencial**.

2. **Desagregación territorial de Lima:**
   - El INEI publica en el Cuadro III.1 dos ámbitos diferenciados para el departamento de Lima:
     - **Lima Metropolitana** (provincia 1501, con los 43 distritos de la capital): **27.6 %** (IC 95 %: [25.0, 30.1], C.V. 4.7 %).
     - **Lima provincias** (las 9 provincias restantes: Barranca, Cajatambo, Canta, Cañete, Huaral, Huarochirí, Huaura, Oyón y Yauyos): **21.7 %** (IC 95 %: [18.3, 25.1], C.V. 8.0 %).
   - El INEI no publica una cifra oficial agregada para el departamento 15 en su conjunto; la cifra de 27.1 % correspondía a un cálculo ponderado heredado de los materiales introductorios del curso, el cual se mantiene únicamente rotulado como requisito de consigna territorial.

3. **Superación de la validación circular:**
   - Se eliminaron los artefactos anteriores del curso (`pobreza_departamento_2024.csv` y `mapa_pobreza_2024.png`) para asegurar trazabilidad verificable hasta la fuente gubernamental original sin depender de referencias intermedias.
