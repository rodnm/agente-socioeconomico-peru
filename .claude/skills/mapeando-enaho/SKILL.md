---
name: mapeando-enaho
description: Hace los mapas de la pobreza del Perú con la ENAHO 2024 del INEI y los límites oficiales del IGN, uniendo por código: el de 25 departamentos que exige la consigna y el de 26 ámbitos con Lima desagregada. Úsala cuando pidan un mapa de la pobreza, un mapa por departamento o por región del Perú.
allowed-tools: Bash(uv run *)
---

# Mapear la pobreza de la ENAHO

1. Si no existe `salidas/personas_2024.parquet`, usa primero la skill `limpiando-enaho`.
2. Si faltan `referencias/limites_departamentales_ign.geojson` o `referencias/limites_ambitos_ign.geojson`, ejecuta primero `uv run scripts/preparar_limites.py`. El mapa no usa otros límites: sin esas capas se detiene.
3. Corre exactamente: `uv run ${CLAUDE_SKILL_DIR}/scripts/mapear.py`
4. Si el script se detiene, muestra su mensaje y detente: la cifra, la unión o los límites están mal.
5. Responde con `mapas/pobreza_departamento.png` (25 departamentos) y `mapas/pobreza_ambitos.png` (26 ámbitos con Lima desagregada), indicando los departamentos de mayor y menor pobreza que imprime el script. La comparación con la referencia oficial del INEI queda en `salidas/mapa_vs_referencia.csv` (25 departamentos) y en `salidas/ambitos_vs_referencia.csv` (26 ámbitos, con el intervalo de confianza y el coeficiente de variación del INEI).

## Reglas que fija el script

- Une por código: `ubigeo[:2]` con `FIRST_IDDP`, como texto. Nunca por nombre: «APURIMAC» no es «Apurímac».
- Exige 25 departamentos y ninguno sin dato. Se detiene si alguno difiere más de 0.1 puntos de `referencias/inei_pobreza_2024.csv`.
- El departamento de Lima (15) no se compara: el INEI no publica una cifra para él en conjunto, y la tabla lo declara «sin cifra publicada por el INEI» en la columna `observacion`. Si falta la cifra de cualquier otro departamento, se detiene.
- Los 26 ámbitos sí se comparan todos, Lima Metropolitana (1501) y Lima provincias incluidas, con la misma tolerancia de 0.1 puntos: sin cifra del INEI, se detiene antes de escribir la tabla; fuera de la tolerancia, después de escribirla.
- `mapas/pobreza_departamento.png` es el mapa que exige la consigna, con Lima como un solo departamento; su nota aclara que esa cifra es un cálculo propio con los microdatos.
- `mapas/pobreza_ambitos.png` es el mapa del análisis: Lima Metropolitana y Lima provincias por separado. Las cifras que el INEI publica como referenciales (CV mayor que 15 %: Ica, Madre de Dios y Moquegua) llevan un asterisco explicado al pie.
- Un recuadro amplía Lima y Callao, sin rótulos de ejes; sus nombres van en tinta oscura con halo claro para leerse sobre cualquier relleno.
- Un color de claro a oscuro, desde 0; nunca arcoíris.
- Leyenda con la unidad: % de personas.
- Lima (15) y Callao (07) van separados.
- Pondera por hogar con `factor07 × mieperho`, como en las cifras oficiales del INEI.
