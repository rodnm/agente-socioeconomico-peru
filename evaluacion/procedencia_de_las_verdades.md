# Procedencia de las verdades de la evaluación

Este documento indica de dónde sale cada respuesta de referencia (*verdad*) de `evaluacion/preguntas.csv` y cómo se verifica.

`preguntas.csv` se escribió y se commiteó antes de las corridas de evaluación, y no se modifica: es el registro previo. Por eso algunas columnas `fuente_verdad` conservan la redacción de entonces. Este documento las precisa sin cambiar ningún valor esperado.

---

## 1. Preguntas de pobreza monetaria (ENAHO, INEI)

Las verdades de la ENAHO 2024 son cifras publicadas por el Instituto Nacional de Estadística e Informática (INEI).

### Fuentes

- **Informe técnico:**
  Instituto Nacional de Estadística e Informática. (2025). *Perú: Evolución de la pobreza monetaria, 2015-2024: Informe técnico*. https://cdn.www.gob.pe/uploads/document/file/8058556/6763186-peru-evolucion-de-la-pobreza-monetaria-2015-2024.pdf
  SHA-256 del PDF: `ed964c41c963f0ac5ce11b1713680ec93519838b9db0cd8fa139e6bb922d6c73`.
- **Anexo estadístico:** https://cdn.www.gob.pe/uploads/document/file/8058555/6763186-anexo-estadistico-excel.zip. El archivo `03_FGT de Pobreza 2015-2024_informe.xlsx` repite los cuadros III.1 (hoja `3.1`) y III.4 (hoja `3.4`).

Las páginas son las impresas en el informe. En el visor del PDF, cada una corresponde al número impreso más 2. Cada cifra se comprobó contra el texto del PDF.

### Procedencia por pregunta

| Pregunta | Indicador | Valor publicado | IC al 95 % | CV | Cuadro y página | Otras menciones en el informe |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| `e1` | Pobreza monetaria nacional | **27.6 %** | [26.6, 28.6] | 1.9 % | Cuadro III.1, p. 219 | Texto de la p. 63; Gráfico 4.1, p. 64 |
| `e2` | Pobreza monetaria en el área rural | **39.3 %** | [37.6, 41.0] | 2.1 % | Cuadro III.1, p. 219 | Texto de la p. 64; Cuadro 4.1, p. 68 |
| `e3` | Pobreza monetaria en Cusco | **18.5 %** | [14.7, 22.4] | 10.5 % | Cuadro III.1, p. 220 | Gráfico 4.7, p. 72 |
| `e4` | Pobreza extrema nacional | **5.5 %** | [5.0, 6.0] | 4.5 % | Cuadro III.4, p. 223 | Texto de la p. 72; Gráfico 4.8, p. 73 |
| `m1` *(segunda cifra)* | Pobreza monetaria en el área urbana | **24.8 %** | [23.6, 26.0] | 2.5 % | Cuadro III.1, p. 219 | Texto de la p. 64; Cuadro 4.1, p. 68 |
| `m2` *(segunda cifra)* | Pobreza en Lima Metropolitana y Callao (dominio 8 de la ENAHO) | **28.2 %** | [25.9, 30.6] | 4.2 % | Cuadro III.1, p. 219, fila «Lima Metropolitana y Prov. Const. del Callao» | Texto de la p. 67; Cuadro 4.1, p. 68. Lima Metropolitana sola (provincia 1501): 27.6 % |

`limpiando-enaho` replica cada una de estas cifras con los microdatos, a 0.05 puntos o menos, en `salidas/validacion.txt`.

### Nota sobre `e3` (Cusco)

La columna `fuente_verdad` de `e3` menciona el archivo de referencia de la sesión 16 del curso, con el que se formuló la pregunta. Ese archivo se retiró del repositorio, porque el curso calculó sus cifras con los mismos microdatos: validar contra él habría sido circular. El valor esperado, 18.5 %, coincide con la cifra que el INEI publica para Cusco en el Cuadro III.1 (p. 220): 18.5 %, con un intervalo de confianza al 95 % de [14.7, 22.4] y un coeficiente de variación de 10.5 %. La verdad descansa, por tanto, en la publicación del INEI.

### Nota sobre `m2` (Lima Metropolitana)

La pregunta dice «Lima Metropolitana», y su verdad, 28.2 %, es la del dominio 8 de la ENAHO. El INEI publica esa cifra como «Lima Metropolitana y Prov. Const. del Callao», es decir, con el Callao incluido. Para Lima Metropolitana sin el Callao, que son los 43 distritos de la provincia de Lima (provincia 1501), el mismo Cuadro III.1 (p. 220) publica 27.6 %, con un IC al 95 % de [25.0, 30.1] y un CV de 4.7 %.

El registro previo fijó 28.2 con una tolerancia de 0.1. Una respuesta de 27.6 % cita una cifra oficial, pero de otro ámbito, y queda fuera de esa tolerancia. Se declara como limitación de la pregunta; no se corrige después de ver los resultados.

---

## 2. Preguntas macroeconómicas (BCRP)

Las preguntas de series temporales (`b1` a `b4`) y la primera cifra de las preguntas mixtas (`m1`, `m2`) provienen de la API pública de estadísticas del Banco Central de Reserva del Perú (BCRP).

- **Obtención:** `evaluacion/verdades.py` las descarga de `https://estadisticas.bcrp.gob.pe/estadisticas/series/api/` sin pasar por el servidor MCP del agente.
- **Respaldo:** `evaluacion/verdades_bcrp.json`, con la URL de cada consulta.

| Pregunta | Serie | Concepto | Periodo | Valor de referencia |
| :--- | :--- | :--- | :--- | :---: |
| `b1` | `PN01273PM` | IPC Lima Metropolitana (var % 12 meses) | Diciembre de 2024 | **1.9663 %** |
| `b2` | `PD04638PD` | Tipo de cambio interbancario venta (promedio anual) | Enero a diciembre de 2024 (246 observaciones) | **3.7553 S/ por US$** |
| `b3` | `PN01271PM` | IPC Lima Metropolitana (var % mensual) | Marzo de 2025 | **0.8102 %** |
| `b4` | `PN01273PM` | IPC Lima Metropolitana (var % 12 meses) | Setiembre de 2026 | **4.5487 %** |
| `m1` *(primera cifra)* | `PN01273PM` | IPC Lima Metropolitana (var % 12 meses) | Diciembre de 2024 | **1.9663 %** |
| `m2` *(primera cifra)* | `PD04638PD` | Tipo de cambio interbancario venta (promedio anual) | Enero a diciembre de 2024 | **3.7553 S/ por US$** |
