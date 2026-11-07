# Consistencia entre herramientas

Generado por `verificando-consistencia/scripts/verificar.py`. DIFERENCIA: 1, OK: 8.

| Fuente | Verificación | Resultado | Detalle | Explicación |
|---|---|---|---|---|
| ENAHO | Pobreza nacional: peso de hogar frente a peso de persona | **OK** | 27.58 frente a 27.53 (diferencia 0.05; tolerancia 0.1) |  |
| ENAHO | Validaciones de limpiando-enaho | **OK** | 135 comprobaciones OK, 0 fallas |  |
| ENAHO | La tasa nacional queda entre la urbana y la rural | **OK** | urbana 24.81, nacional 27.58, rural 39.30 |  |
| ENAHO | Departamentos de limpiando-enaho frente al informe técnico del INEI | **OK** | 25 departamentos en indicadores.csv (consigna: 25); comparados con el INEI: 24 departamentos, Lima Metropolitana y Lima provincias; 0 fuera de ±0.1. Lima (15) sin cifra publicada por el INEI para el departamento en conjunto |  |
| ENAHO | Mapa (mapeando-enaho) frente a indicadores (limpiando-enaho) | **OK** | 25 unidades en el mapa; 0 con cifra distinta |  |
| BCRP | Inflación a 12 meses: recalculada desde PN38705PM frente a la publicada en PN01273PM | **OK** | 12 meses de 2024; diferencia máxima 0.000 puntos en 2024-03 | El índice se publica redondeado; una diferencia mayor indicaría revisión de datos o un error de alineación de periodos. |
| BCRP | resumen frente a serie (PN01273PM, 2024) | **OK** | promedio, máximo, mínimo y cambio coinciden |  |
| BCRP / SBS | Morosidad bancaria en diciembre de 2020 a 2024: BCRP (PN07746EM) frente a SBS (B-2401) | **DIFERENCIA** | 5 diciembres; diferencia absoluta máxima 0.05 puntos en 2024-12; 2020-12: BCRP 3.81 % frente a SBS 3.80 %; 2021-12: BCRP 3.79 % frente a SBS 3.77 %; 2022-12: BCRP 3.96 % frente a SBS 3.95 %; 2023-12: BCRP 4.33 % frente a SBS 4.31 %; 2024-12: BCRP 3.80 % frente a SBS 3.75 % | Miden cosas distintas, así que no se espera que coincidan: la SBS publica en el B-2401 «Créditos Atrasados (criterio SBS) / Créditos Directos», y la serie PN07746EM del BCRP es «Cartera atrasada neta / Colocaciones netas (%) - Empresas Bancarias». Antes de comparar cifras de morosidad hay que revisar esa definición, la cobertura y la fecha. |
| Informe | Cifras del informe frente a una nueva consulta a las herramientas | **OK** | 79 cifras resueltas de nuevo; 0 distintas; 0 sin dato |  |
