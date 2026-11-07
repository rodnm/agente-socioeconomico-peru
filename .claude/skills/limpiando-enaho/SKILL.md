---
name: limpiando-enaho
description: Limpia los módulos 34 (sumaria) y 02 (miembros) de la ENAHO del INEI de 2020 a 2024 y arma una base de personas con pobreza y factor de expansión, validada contra las cifras publicadas por el INEI. Úsala cuando pidan limpiar, unir o analizar la ENAHO, o calcular pobreza por región, departamento, sexo o edad de un año entre 2020 y 2024, por ejemplo la pobreza en Cusco en 2024.
argument-hint: [año]
allowed-tools: Bash(uv run *)
---

# Limpiar la ENAHO

1. Si faltan los zip del año en `datos/` (`{código}-Modulo34.zip` y `{código}-Modulo02.zip`), usa primero la skill `descargando-enaho`. Códigos de encuesta del INEI: 2020 = `737`, 2021 = `759`, 2022 = `784`, 2023 = `906`, 2024 = `966`.
2. Corre exactamente: `uv run ${CLAUDE_SKILL_DIR}/scripts/limpiar.py --anio $0`. Sin año procesa 2024. Para los cinco años: `uv run ${CLAUDE_SKILL_DIR}/scripts/limpiar.py --todos`.
3. Lee `salidas/validacion.txt`. Si alguna línea dice `FALLA`, detente y muestra esa línea: el script ya se detuvo sin escribir la base de ese año. Las líneas `NOTA` aclaran, no son fallas.
4. Responde con `salidas/personas_{año}.parquet` y `salidas/indicadores.csv` (columna `anio`). Nunca des una cifra sin ponderar:
   - Pobreza nacional, por área, dominio o departamento: una fila por hogar (`drop_duplicates` de `conglome`, `vivienda`, `hogar`) y peso `peso_hogar`, que es `factor07 × mieperho`.
   - Pobreza por sexo o edad: todas las filas y peso `facpob07`.
5. Si la pregunta pide una cifra que ya está en `salidas/indicadores.csv` (nacional, extrema, urbana, rural, Lima Metropolitana y Callao, Lima Metropolitana, Lima provincias, cada departamento, sexo, edad, residentes, hogares), léela de ahí con su año y cita su `id`. Ese archivo es la fuente única que usan los gráficos, el mapa, el informe y el dashboard.
6. Antes de usar una variable que no está en la base, o para saber contra qué cuadro del INEI se valida cada cifra, lee [reference.md](reference.md).

Solo hay datos de 2020 a 2024. Si piden otro año, el script lo rechaza: dilo y no estimes la cifra. Lima se analiza desagregada: el INEI no publica una cifra del departamento 15 en conjunto, sino Lima Metropolitana (provincia 1501) y Lima provincias.
