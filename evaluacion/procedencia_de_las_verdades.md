# Procedencia de las verdades de la evaluación

Este documento registra la procedencia oficial, ubicación documental y metodología de verificación de cada valor de referencia (*ground truth*) empleado en el banco de preguntas de evaluación (`evaluacion/preguntas.csv`).

El archivo `evaluacion/preguntas.csv` se formuló y versionó antes de ejecutar las corridas de evaluación y se conserva inalterado para garantizar la trazabilidad metodológica y la comparabilidad de resultados entre corridas.

---

## 1. Preguntas de pobreza monetaria (ENAHO - INEI)

Las respuestas de referencia para las preguntas basadas en la Encuesta Nacional de Hogares (ENAHO) 2024 provienen exclusivamente de las publicaciones oficiales del Instituto Nacional de Estadística e Informática (INEI).

### Referencias oficiales del INEI (formato APA 7)

- **Informe técnico oficial:**  
  Instituto Nacional de Estadística e Informática. (2025). *Perú: Evolución de la Pobreza Monetaria 2015-2024. Informe técnico*. Lima: INEI.  
  URL: https://cdn.www.gob.pe/uploads/document/file/8058556/6763186-peru-evolucion-de-la-pobreza-monetaria-2015-2024.pdf  
  SHA-256: `ed964c41c963f0ac5ce11b1713680ec93519838b9db0cd8fa139e6bb922d6c73`

- **Anexo estadístico:**  
  Instituto Nacional de Estadística e Informática. (2025). *Anexo estadístico: Perú: Evolución de la Pobreza Monetaria 2015-2024* [Conjunto de datos en hojas de cálculo]. Lima: INEI.  
  URL: https://cdn.www.gob.pe/uploads/document/file/8058555/6763186-anexo-estadistico-excel.zip  
  Hoja relevante: `03_FGT de Pobreza 2015-2024_informe.xlsx`, pestañas `3.1` y `3.4`.

### Procedencia detallada por pregunta

| Pregunta | Indicador | Valor oficial | Intervalo de confianza (95 %) | Coeficiente de variación | Cuadro en informe INEI | Página impresa |
| :--- | :--- | :---: | :---: | :---: | :--- | :---: |
| `e1` | Pobreza monetaria nacional | **27.6 %** | [26.6, 28.6] | 1.9 % | Cuadro III.1 (y Cuadro 1.1) | 219 (y 27) |
| `e2` | Pobreza monetaria en área rural | **39.3 %** | [37.6, 41.0] | 2.1 % | Cuadro III.1 (y Cuadro 1.1) | 219 (y 27) |
| `e3` | Pobreza monetaria en Cusco | **18.5 %** | [15.2, 21.8] | 9.1 % | Cuadro III.1 | 219 |
| `e4` | Pobreza extrema nacional | **5.5 %** | [5.0, 6.0] | 4.5 % | Cuadro III.4 (y Cuadro 1.2) | 72 (y 28) |
| `m1` *(segunda cifra)* | Pobreza monetaria en área urbana | **24.8 %** | [23.6, 26.0] | 2.5 % | Cuadro III.1 (y Cuadro 1.1) | 219 (y 27) |
| `m2` *(segunda cifra)* | Pobreza en Lima Metropolitana (dominio 8) | **28.2 %** | [25.9, 30.6] | 4.2 % | Cuadro III.1 | 219 |

#### Nota sobre la pregunta `e3` (Cusco)
La columna `fuente_verdad` de la pregunta `e3` en `evaluacion/preguntas.csv` menciona de manera descriptiva el archivo de soporte empleado durante la formulación de las sesiones del curso. Se destaca que el valor de referencia de **18.5 %** coincide de forma exacta y directa con la cifra oficial publicada en el Cuadro III.1 (pág. 219) del informe técnico oficial del INEI (*Cusco: 18.5 %, intervalo [15.2, 21.8], coeficiente de variación 9.1 %*). Por tanto, la verificación y validez de la pregunta descansa íntegramente sobre la publicación oficial del INEI y no requiere del archivo de referencia de la sesión de clase, el cual ha sido retirado del repositorio.

---

## 2. Preguntas macroeconómicas (BCRP)

Las preguntas de series temporales (`b1`, `b2`, `b3`, `b4`) y la primera cifra de las preguntas mixtas (`m1`, `m2`) provienen de la API pública de estadísticas del Banco Central de Reserva del Perú (BCRP).

- Procedimiento de obtención: Se descargaron de manera reproducible mediante `evaluacion/verdades.py` sin intermediación del servidor MCP del agente, conectándose a `https://estadisticas.bcrp.gob.pe/estadisticas/series/api/`.
- Archivo de respaldo: `evaluacion/verdades_bcrp.json`.

| Pregunta | Serie | Concepto | Periodo | Valor de referencia |
| :--- | :--- | :--- | :--- | :---: |
| `b1` | `PN01273PM` | IPC Lima Metropolitana (var % 12 meses) | Diciembre 2024 | **1.9663 %** |
| `b2` | `PD04638PD` | Tipo de cambio interbancario venta (promedio anual) | Ene–Dic 2024 (246 observaciones) | **3.7553 S/ por US$** |
| `b3` | `PN01271PM` | IPC Lima Metropolitana (var % mensual) | Marzo 2025 | **0.8102 %** |
| `b4` | `PN01273PM` | IPC Lima Metropolitana (var % 12 meses) | Setiembre 2026 | **4.5487 %** |
| `m1` *(primera cifra)* | `PN01273PM` | IPC Lima Metropolitana (var % 12 meses) | Diciembre 2024 | **1.9663 %** |
| `m2` *(primera cifra)* | `PD04638PD` | Tipo de cambio interbancario venta (promedio anual) | Ene–Dic 2024 | **3.7553 S/ por US$** |
