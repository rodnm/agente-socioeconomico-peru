# Verificación manual de cifras del informe

Cuatro afirmaciones numéricas de [`informe_final.md`](informe_final.md) comprobadas a mano en la fuente oficial, sin usar el agente, el servidor MCP ni los scripts del repositorio.

| # | Afirmación del informe                                                | Valor en el informe | Fuente para comprobarla                                                                                                                                                                                                  | Valor observado | ¿Coincide? | Diferencia |
| - | ---------------------------------------------------------------------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------- | ----------- | ---------- |
| 1 | Inflación a 12 meses del IPC de Lima Metropolitana, diciembre de 2024 | 2.0 %               | [BCRP, serie PN01273PM, dic. 2024](https://estadisticas.bcrp.gob.pe/estadisticas/series/mensuales/resultados/PN01273PM/html/2024-12/2024-12/)                                                                             | 1.97 %          | Sí, al redondear a un decimal | −0.03 pp (redondeo) |
| 2 | Variación interanual del PBI en abril de 2020, el mínimo del periodo | −39.3 %            | [BCRP, serie PN01728AM, abr. 2020](https://estadisticas.bcrp.gob.pe/estadisticas/series/mensuales/resultados/PN01728AM/html/2020-4/2020-4/)                                                                               | −39.3 %         | Sí          | 0          |
| 3 | Pobreza monetaria nacional, 2024                                       | 27.6 %              | [INEI (2025), *Perú: Evolución de la pobreza monetaria, 2015-2024*, Cuadro III.1, pág. 219 (PDF)](https://cdn.www.gob.pe/uploads/document/file/8058556/6763186-peru-evolucion-de-la-pobreza-monetaria-2015-2024.pdf) | 27.6 %          | Sí          | 0          |
| 4 | Morosidad de la banca múltiple, diciembre de 2024                     | 3.75 %              | [SBS, boletín B-2401, dic. 2024 (XLS)](https://intranet2.sbs.gob.pe/estadistica/financiera/2024/Diciembre/B-2401-di2024.XLS)                                                                                             | 3.75 %          | Sí          | 0          |

La diferencia de la fila 1 se debe al redondeo, no a un error. La API del BCRP entrega 1.9663 para diciembre de 2024 (la serie declara dos decimales), la página muestra 1.97 y el informe presenta la cifra con un decimal, porque el borrador del agente la pidió así (`ultimo.valor|1`). Las tres lecturas coinciden al redondear a un decimal. La tabla de trazabilidad del informe (cifra 7) registra la consulta y su URL.

## Procedimiento

1. **Inflación.** Abrir el enlace en el navegador y leer el valor de «Dic24». La página muestra dos decimales y el informe redondea a uno.
2. **PBI.** Abrir el enlace y leer el valor de «Abr20» en la columna «PBI» del grupo «Producto bruto interno y demanda interna (variación porcentual interanual)».
3. **Pobreza.** Abrir el PDF del INEI en la página impresa 219 (221 del visor), Cuadro III.1, y leer la columna 2024 de la fila «Nacional».
4. **Morosidad.** Descargar el XLS, buscar la fila «Créditos Atrasados (criterio SBS)\* / Créditos Directos», la primera de las filas de créditos atrasados, y leer la columna del total de la banca múltiple.

Comprobado por: Rodrigo Norabuena, 8 de noviembre de 2026.
