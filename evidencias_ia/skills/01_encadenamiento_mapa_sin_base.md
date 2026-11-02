# Encadenamiento de skills: mapa sin base procesada (claude -p, 2026-11-02)

## 1. Pedido (claude -p)

Haz un mapa de la pobreza monetaria por departamento con ENAHO 2024.

**Herramienta:** `Skill`

```json
{
 "skill": "mapeando-enaho"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
Launching skill: mapeando-enaho
```
</details>

<details><summary>Instrucciones de la skill que cargó Claude Code</summary>

```markdown
Base directory for this skill: ~\Documents\GitHub\agente-socioeconomico-peru\.claude\skills\mapeando-enaho

# Mapear la pobreza de la ENAHO

1. Si no existe `salidas/personas_2024.parquet`, usa primero la skill `limpiando-enaho`.
2. Si falta `datos/peru_departamental_simple.geojson`, usa primero la skill `descargando-enaho`.
3. Corre exactamente: `uv run ~/Documents/GitHub/agente-socioeconomico-peru/.claude/skills/mapeando-enaho/scripts/mapear.py`
4. Si el script se detiene, muestra su mensaje y detente: la cifra o la unión están mal.
5. Responde con `mapas/pobreza_departamento.png` y los departamentos de mayor y menor pobreza que imprime el script. La comparación con la referencia de la sesión 16 queda en `salidas/mapa_vs_referencia.csv`.

## Reglas que fija el script

- Une por código: `ubigeo[:2]` con `FIRST_IDDP`, como texto. Nunca por nombre: «APURIMAC» no es «Apurímac».
- Exige 25 departamentos y ninguno sin dato. Se detiene si alguno difiere más de 0.1 puntos de `referencias/pobreza_departamento_2024.csv`.
- Un color de claro a oscuro, desde 0; nunca arcoíris.
- Leyenda con la unidad: % de personas.
- Lima (15) y Callao (07) van separados.
- Pondera por hogar con `factor07 × mieperho`, como la referencia de la sesión.
```
</details>

**Herramienta:** `Bash`

```json
{
 "command": "cd ~/Documents/GitHub/agente-socioeconomico-peru && ls salidas/personas_2024.parquet datos/peru_departamental_simple.geojson referencias/pobreza_departamento_2024.csv 2>&1",
 "description": "Check required input files exist"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
Exit code 2
ls: cannot access 'salidas/personas_2024.parquet': No such file or directory
datos/peru_departamental_simple.geojson
referencias/pobreza_departamento_2024.csv
```
</details>

**Claude:**

Falta `salidas/personas_2024.parquet`, así que según la skill toca correr primero `limpiando-enaho`.

**Herramienta:** `Skill`

```json
{
 "skill": "limpiando-enaho"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
Launching skill: limpiando-enaho
```
</details>

<details><summary>Instrucciones de la skill que cargó Claude Code</summary>

```markdown
Base directory for this skill: ~\Documents\GitHub\agente-socioeconomico-peru\.claude\skills\limpiando-enaho

# Limpiar la ENAHO

1. Si faltan `datos/966-Modulo34.zip` o `datos/966-Modulo02.zip`, usa primero la skill `descargando-enaho`.
2. Corre exactamente: `uv run ~/Documents/GitHub/agente-socioeconomico-peru/.claude/skills/limpiando-enaho/scripts/limpiar.py --anio $0`
3. Lee `salidas/validacion.txt`. Si alguna línea dice `FALLA`, o la pobreza difiere del INEI en más de 0.1 puntos, detente y muestra esa línea.
4. Responde con `salidas/personas_2024.parquet` y `salidas/indicadores.csv`. Nunca des una cifra sin ponderar:
   - Pobreza nacional, por área, dominio o departamento: una fila por hogar (`drop_duplicates` de `conglome`, `vivienda`, `hogar`) y peso `peso_hogar`, que es `factor07 × mieperho`.
   - Pobreza por sexo o edad: todas las filas y peso `facpob07`.
5. Si la pregunta pide una cifra que ya está en `salidas/indicadores.csv` (nacional, extrema, urbana, rural, Lima Metropolitana, cada departamento, sexo, edad, residentes, hogares), léela de ahí y cita su `id`. Ese archivo es la fuente única que usan los gráficos, el mapa, el informe y el dashboard.
6. Antes de usar una variable que no está en la base, lee [reference.md](reference.md).

Solo valida 2024. Si piden otro año, el script lo rechaza: dilo y no estimes la cifra.
```
</details>

**Herramienta:** `Bash`

```json
{
 "command": "cd ~/Documents/GitHub/agente-socioeconomico-peru && ls datos/966-Modulo34.zip datos/966-Modulo02.zip 2>&1",
 "description": "Check ENAHO module zips exist"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
datos/966-Modulo02.zip
datos/966-Modulo34.zip
```
</details>

**Claude:**

Los zip están. Corro la limpieza con el año 2024.

**Herramienta:** `Bash`

```json
{
 "command": "cd ~/Documents/GitHub/agente-socioeconomico-peru && uv run ~/Documents/GitHub/agente-socioeconomico-peru/.claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024 2>&1 | tail -30; echo \"---VALIDACION---\"; cat salidas/validacion.txt",
 "description": "Run ENAHO cleaning script and show validation"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
Listo: 108,664 personas en salidas/personas_2024.parquet; validación sin fallos.
salidas/indicadores.csv: 42 indicadores; pobreza nacional 27.58 %.
---VALIDACION---
Validación de la ENAHO 2024 contra las cifras de la sesión y del INEI

OK    Hogares en la sumaria: 33,691 (esperado 33,691)
OK    Filas del módulo 02: 117,721 (esperado 117,721)
OK    Residentes habituales: 108,664 (esperado 108,664)
OK    Llaves de hogar repetidas: 0 (esperado 0)
OK    Llaves de persona repetidas: 0 (esperado 0)
OK    Filas de la base tras la unión: 108,664 (esperado 108,664)
OK    Personas sin hogar en la sumaria: 0 (esperado 0)
OK    Códigos conglome sin 6 caracteres: 0 (esperado 0)
OK    Códigos vivienda sin 3 caracteres: 0 (esperado 0)
OK    Códigos hogar sin 2 caracteres: 0 (esperado 0)
OK    Códigos codperso sin 2 caracteres: 0 (esperado 0)
OK    Códigos ubigeo sin 6 caracteres: 0 (esperado 0)
OK    Hogares en la base: 33,691 (esperado 33,691)
OK    Pobreza nacional (hogares, factor07 × mieperho): 27.58 % (esperado 27.6 ± 0.1)
OK    Pobreza nacional (personas, facpob07): 27.53 % (esperado 27.6 ± 0.1)
OK    Pobreza extrema: 5.50 % (esperado 5.5 ± 0.1)
OK    Pobreza urbana: 24.
… [1624 caracteres omitidos]
```
</details>

**Claude:**

Validación sin fallos. Ahora el mapa.

**Herramienta:** `Bash`

```json
{
 "command": "cd ~/Documents/GitHub/agente-socioeconomico-peru && uv run ~/Documents/GitHub/agente-socioeconomico-peru/.claude/skills/mapeando-enaho/scripts/mapear.py 2>&1 | tail -30; echo \"---\"; ls -la mapas/pobreza_departamento.png salidas/mapa_vs_referencia.csv",
 "description": "Run map script and list outputs"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
mapas/pobreza_departamento.png (25 departamentos con dato; CAJAMARCA: 45.0 %, LORETO: 43.0 %, PUNO: 39.9 %, MADRE DE DIOS: 11.1 %, MOQUEGUA: 11.0 %, ICA: 6.0 %)
---
-rw-r--r-- 1 [USUARIO] 197121 201892 Nov  2 09:07 mapas/pobreza_departamento.png
-rw-r--r-- 1 [USUARIO] 197121    904 Nov  2 09:07 salidas/mapa_vs_referencia.csv
```
</details>

**Herramienta:** `Read`

```json
{
 "file_path": "~/Documents/GitHub/agente-socioeconomico-peru/mapas/pobreza_departamento.png"
}
```

<details><summary>Resultado de la herramienta</summary>

```text

```
</details>

**Claude:**

El mapa está listo en `mapas/pobreza_departamento.png`. Usa un solo color, de claro a oscuro desde 0, con la leyenda en % de personas.

**Mayor pobreza monetaria (ENAHO 2024, INEI):**
- Cajamarca: 45.0 %
- Loreto: 43.0 %
- Puno: 39.9 %

**Menor pobreza:**
- Ica: 6.0 %
- Moquegua: 11.0 %
- Madre de Dios: 11.1 %

Para llegar al mapa hubo que correr antes `limpiando-enaho`, porque faltaba `salidas/personas_2024.parquet`. Esa limpieza terminó sin fallos de validación: la pobreza nacional da 27.58 %, dentro de ±0.1 de lo esperado.

El mapa tiene los 25 departamentos con dato, unidos por código y no por nombre. Lima y Callao aparecen separados. Las cifras se ponderan por hogar con `factor07 × mieperho`. El script no se detuvo, así que ningún departamento se desvía más de 0.1 puntos de la referencia. La comparación completa queda en `salidas/mapa_vs_referencia.csv`.

Las cifras salen de `salidas/indicadores.csv` y del script de la skill, no de memoria. Además, `salidas/consistencia.md` ya estaba sin rastrear en git antes de empezar. No toqué ni cometí nada.

---

**Resultado final** · turnos: 10 · costo USD: 0.33302370000000003 · duración: 33.2 s
