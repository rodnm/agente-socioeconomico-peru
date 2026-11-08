# Corrida aislada, intento 1: reutiliza el borrador existente (2026-11-07)

## Línea de tiempo

Servidores MCP: `bcrp` · Skills: `limpiando-enaho`, `graficando-enaho`, `mapeando-enaho`, `verificando-consistencia` · 16 llamadas a herramientas

1. `ToolSearch`
2. Bash `ls; ls datos salidas informes figuras mapas 2>&1 | head -60; cat informes/verificacion.md `
3. Bash `ls scripts .claude/skills/*; cat .claude/skills/informando-peru/SKILL.md; head -60 informe`
4. Skill `limpiando-enaho`
5. Bash `uv run ~/Documents/GitHub/agente-socioeconomico-peru/.claude/skills/limpiando-enaho/script`
6. Skill `graficando-enaho`
7. Skill `mapeando-enaho`
8. Bash `ls referencias; uv run .claude/skills/graficando-enaho/scripts/graficar.py 2>&1 | tail -25`
9. MCP `bcrp.graficar_serie`
10. MCP `bcrp.graficar_serie`
11. MCP `bcrp.graficar_serie`
12. Bash `grep -n "figuras/\|mapas/" informes/borrador.md; grep -c "{{" informes/borrador.md; git st`
13. Bash `uv run .claude/skills/informando-peru/scripts/armar_informe.py 2>&1 | tail -30`
14. Skill `verificando-consistencia`
15. Bash `uv run .claude/skills/verificando-consistencia/scripts/verificar.py 2>&1 | tail -15; echo `
16. Bash `sed -n 1,12p informes/informe_final.md >/dev/null; grep -n "^## " informes/informe_final.m`

## 1. Pedido (claude -p)

Investiga esta pregunta y entrégame el informe: ¿Cómo evolucionaron la inflación, la actividad económica, la morosidad bancaria y la pobreza monetaria del Perú entre 2020 y 2024, y qué brechas territoriales y urbano-rurales presentaba la pobreza en 2024? Usa el BCRP para la inflación, la actividad y la morosidad neta, la SBS para la morosidad bancaria 2020-2024 y el contexto financiero, y la ENAHO para la serie de pobreza 2020-2024 y la foto territorial de 2024 con sus mapas. Al final verifica la consistencia de las cifras.

**Claude:**

Empiezo revisando el estado del repo y cargando las herramientas.

**Herramienta:** `ToolSearch`

```json
{
 "query": "select:mcp__bcrp__buscar_series,mcp__bcrp__resumen,mcp__bcrp__serie,mcp__bcrp__comparar_series,mcp__bcrp__graficar_serie,mcp__sbs__indicadores,mcp__sbs__ultimo_periodo,mcp__sbs__listar_reportes,mcp__sbs__reporte,mcp__sbs__ranking",
 "max_results": 12
}
```

<details><summary>Resultado de la herramienta</summary>

```text










```
</details>

**Herramienta:** `Bash`

```json
{
 "command": "ls; ls datos salidas informes figuras mapas 2>&1 | head -60; cat informes/verificacion.md | head -40"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
CLAUDE.md
LICENSE
README.md
dashboard
datos
evaluacion
evidencias_ia
figuras
informes
mapas
mcp
odd
pyproject.toml
referencias
salidas
scripts
tests
uv.lock
datos:
737-Modulo02.zip
737-Modulo34.zip
759-Modulo02.zip
759-Modulo34.zip
784-Modulo02.zip
784-Modulo34.zip
906-Modulo02.zip
906-Modulo34.zip
966-Modulo02.zip
966-Modulo34.zip
anexo_estadistico.zip
bcrp
per_admin_boundaries.geojson.zip
peru_departamental_simple.geojson

figuras:

informes:
borrador.md
informe_final.md
plan_analisis.md
verificacion.md

mapas:

salidas:
# Verificación manual de cifras del informe

Cuatro afirmaciones numéricas de [`informe_final.md`](informe_final.md) comprobadas a mano en la fuente oficial, sin usar el agente, el servidor MCP ni los scripts del repositorio.

| # | Afirmación del informe | Valor en el informe | Fuente para comprobarla | Valor observado | ¿Coincide? | Diferencia |
|---|---|---|---|---|---|---|
| 1 | Inflación a 12 meses del IPC de Lima Metropolitana, diciembre de 2024 | 2.0 % | [BCRP, serie PN01273PM, dic. 2024](https://estadisticas.bcrp.gob.pe/estadisticas/series/mensuales/resultados/PN01273PM/html/2024-12/2024-12/) | _completar_ | _completar_ | _completar_ |
| 2 | Variación int
… [1428 caracteres omitidos]
```
</details>

**Herramienta:** `Bash`

```json
{
 "command": "ls scripts .claude/skills/*; cat .claude/skills/informando-peru/SKILL.md; head -60 informes/informe_final.md; git log --oneline | head -5"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
.claude/skills/descargando-enaho:
SKILL.md
scripts

.claude/skills/graficando-enaho:
SKILL.md
scripts

.claude/skills/informando-peru:
SKILL.md
plantilla.md
scripts

.claude/skills/limpiando-enaho:
SKILL.md
reference.md
scripts

.claude/skills/mapeando-enaho:
SKILL.md
scripts

.claude/skills/verificando-consistencia:
SKILL.md
scripts

scripts:
__pycache__
estilo_graficos.py
exportar_evidencias.py
preparar_limites.py
---
name: informando-peru
description: Arma un informe socioeconómico del Perú en informes/informe_final.md con tablas, gráficos y referencias, donde cada cifra sale de una herramienta (MCP del BCRP o de la SBS, o indicadores de la ENAHO) y nunca se escribe a mano. Úsala cuando pidan un informe, un reporte o una investigación sobre la economía o la pobreza del Perú, o redactar los resultados de un análisis con datos oficiales.
argument-hint: [pregunta de investigación]
allowed-tools: Bash(uv run *), Read, Write, Edit
---

# Informar con cifras trazables

El informe se escribe en dos pasos: Claude redacta un borrador con **marcadores** en lugar de números y un script los resuelve llamando de nuevo a las herramientas. Así cada cifra se puede rastrear y repetir.

1. **Plan
… [12737 caracteres omitidos]
```
</details>

**Claude:**

Los insumos (`salidas/`, `figuras/`, `mapas/`) están borrados, así que los regenero con las skills. Empiezo por la limpieza de la ENAHO.

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

1. Si faltan los zip del año en `datos/` (`{código}-Modulo34.zip` y `{código}-Modulo02.zip`), usa primero la skill `descargando-enaho`. Códigos de encuesta del INEI: 2020 = `737`, 2021 = `759`, 2022 = `784`, 2023 = `906`, 2024 = `966`.
2. Corre exactamente: `uv run ~/Documents/GitHub/agente-socioeconomico-peru/.claude/skills/limpiando-enaho/scripts/limpiar.py --anio $0`. Sin año procesa 2024. Para los cinco años: `uv run ~/Documents/GitHub/agente-socioeconomico-peru/.claude/skills/limpiando-enaho/scripts/limpiar.py --todos`.
3. Lee `salidas/validacion.txt`. Si alguna línea dice `FALLA`, detente y muestra esa línea: el script ya se detuvo sin escribir la base de ese año. Las líneas `NOTA` aclaran, no son fallas.
4. Responde con `salidas/personas_{año}.parquet` y `salidas/indicadores.csv` (columna `anio`). Nunca des una cifra sin ponderar:
   - Pobreza nacional, por área, dominio o departamento: una fila por hogar (`drop_duplicates` de `conglome`, `vivienda`, `hogar`) y peso `peso_hogar`, que es `factor07 × mieperho`.
   - Pobreza por sexo o edad: todas las filas y peso `facpob07`.
5. Si la pregunta pide una cifra que ya está en `salidas/indicadores.csv` (nacional, extrema, urbana, rural, Lima Metropolitana y Callao, Lima Metropolitana, Lima provincias, cada departamento, sexo, edad, residentes, hogares), léela de ahí con su año y cita su `id`. Ese archivo es la fuente única que usan los gráficos, el mapa, el informe y el dashboard.
6. Antes de usar una variable que no está en la base, o para saber contra qué cuadro del INEI se valida cada cifra, lee [reference.md](reference.md).

Solo hay datos de 2020 a 2024. Si piden otro año, el script lo rechaza: dilo y no estimes la cifra. Lima se analiza desagregada: el INEI no publica una cifra del departamento 15 en conjunto, sino Lima Metropolitana (provincia 1501) y Lima provincias.
```
</details>

**Herramienta:** `Bash`

```json
{
 "command": "uv run ~/Documents/GitHub/agente-socioeconomico-peru/.claude/skills/limpiando-enaho/scripts/limpiar.py --todos 2>&1 | tail -40; echo ---; cat salidas/validacion.txt | grep -c FALLA; grep FALLA salidas/validacion.txt",
 "timeout": 600000
}
```

<details><summary>Resultado de la herramienta</summary>

```text
Año 2020 listo: 118,810 personas en salidas/personas_2020.parquet; pobreza nacional 30.13 %.
Año 2021 listo: 113,057 personas en salidas/personas_2021.parquet; pobreza nacional 25.87 %.
Año 2022 listo: 113,142 personas en salidas/personas_2022.parquet; pobreza nacional 27.52 %.
Año 2023 listo: 110,792 personas en salidas/personas_2023.parquet; pobreza nacional 29.05 %.
Año 2024 listo: 108,664 personas en salidas/personas_2024.parquet; pobreza nacional 27.58 %.
salidas/indicadores.csv actualizado con éxito para años: [2020, 2021, 2022, 2023, 2024].
---
0
```
</details>

**Claude:**

Sin fallas de validación. Sigo con los gráficos y mapas de la ENAHO.

**Herramienta:** `Skill`

```json
{
 "skill": "graficando-enaho"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
Launching skill: graficando-enaho
```
</details>

<details><summary>Instrucciones de la skill que cargó Claude Code</summary>

```markdown
Base directory for this skill: ~\Documents\GitHub\agente-socioeconomico-peru\.claude\skills\graficando-enaho

# Graficar la pobreza de la ENAHO

1. Si no existe `salidas/personas_2024.parquet` (cortes de 2024) o `salidas/indicadores.csv` con la columna `anio` (serie), usa primero la skill `limpiando-enaho`. El script también se detiene con ese aviso si falta.
2. Elige el corte según el pedido y corre exactamente: `uv run ~/Documents/GitHub/agente-socioeconomico-peru/.claude/skills/graficando-enaho/scripts/graficar.py --por <corte>`. Sin `--por` hace los cinco.

   | Si el pedido habla de… | Corte |
   |---|---|
   | urbano, rural, área, ciudad o campo | `area` |
   | hombres, mujeres, sexo o género | `sexo` |
   | edad, niños, jóvenes, adultos mayores | `edad` |
   | departamentos, regiones, territorio, comparar entre lugares | `departamento` |
   | evolución, tendencia, 2020 a 2024, cambio en el tiempo | `serie` |

3. Responde con la ruta de `figuras/pobreza_por_<corte>.png` (o `figuras/pobreza_serie_2020_2024.png`) y las cifras que imprime el script. No las recalcules.

## Reglas que fija el script

- Barras que empiezan en cero. Área y sexo de mayor a menor; las edades en su orden natural.
- El corte `departamento` muestra los 26 ámbitos del INEI: 24 departamentos, Callao, Lima Metropolitana (provincia 1501) y Lima provincias, en barras horizontales ordenadas, con una línea en el promedio nacional. La cifra va en la punta de cada barra; si ahí cruzaría la línea nacional, va en blanco dentro del extremo de la barra.
- Las cifras que el INEI publica como referenciales (coeficiente de variación mayor que 15 %, columnas `cv` y `nota` de `referencias/inei_pobreza_2024.csv`: Ica, Madre de Dios y Moquegua) llevan un asterisco y una nota al pie.
- Lima se rotula siempre «Lima Metropolitana» y «Lima provincias», igual que en los mapas.
- La serie 2020-2024 muestra la pobreza nacional, rural, urbana, de Lima Metropolitana y de Lima provincias: colores de la paleta categórica validada en orden fijo, marcador y trazo distintos por serie, leyenda arriba y la cifra del primer y del último año unida a su punto por una guía, sin superponerse.
- Un solo color en las barras y el valor escrito en cada una.
- Título analítico calculado con los datos (qué grupo está más arriba y por cuánto), subtítulo con el periodo y la unidad (% de personas). Ninguna cifra queda separada de su unidad al cambiar de línea.
- Nota al pie: «Fuente: INEI, ENAHO 2024 (módulos 34 y 02)», más el peso usado.
- PNG a 200 dpi en `figuras/`.

## Pesos

- **Área y ámbitos territoriales:** por hogar con `factor07 × mieperho`, porque así salen las cifras oficiales (24.8 % urbana, 39.3 % rural y la tabla territorial del INEI). Con `facpob07` darían 24.7 % y 39.4 %.
- **Sexo y edad:** por persona con `facpob07`, porque son atributos de cada persona.

Si piden un corte que no está en el script, dilo antes de improvisar otro gráfico. Las diferencias entre grupos son descriptivas: no las presentes como causas.
```
</details>

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
2. Si faltan `referencias/limites_departamentales_ign.geojson` o `referencias/limites_ambitos_ign.geojson`, ejecuta primero `uv run scripts/preparar_limites.py`. El mapa no usa otros límites: sin esas capas se detiene.
3. Corre exactamente: `uv run ~/Documents/GitHub/agente-socioeconomico-peru/.claude/skills/mapeando-enaho/scripts/mapear.py`
4. Si el script se detiene, muestra su mensaje y detente: la cifra, la unión o los límites están mal.
5. Responde con `mapas/pobreza_departamento.png` (25 departamentos) y `mapas/pobreza_ambitos.png` (26 ámbitos con Lima desagregada), indicando los departamentos de mayor y menor pobreza que imprime el script. La comparación con la referencia oficial del INEI queda en `salidas/mapa_vs_referencia.csv`.

## Reglas que fija el script

- Une por código: `ubigeo[:2]` con `FIRST_IDDP`, como texto. Nunca por nombre: «APURIMAC» no es «Apurímac».
- Exige 25 departamentos y ninguno sin dato. Se detiene si alguno difiere más de 0.1 puntos de `referencias/inei_pobreza_2024.csv`.
- El departamento de Lima (15) no se compara: el INEI no publica una cifra para él en conjunto, y la tabla lo declara «sin cifra publicada por el INEI» en la columna `observacion`. Si falta la cifra de cualquier otro departamento, se detiene.
- `mapas/pobreza_departamento.png` es el mapa que exige la consigna, con Lima como un solo departamento; su nota aclara que esa cifra es un cálculo propio con los microdatos.
- `mapas/pobreza_ambitos.png` es el mapa del análisis: Lima Metropolitana y Lima provincias por separado. Las cifras que el INEI publica como referenciales (CV mayor que 15 %: Ica, Madre de Dios y Moquegua) llevan un asterisco explicado al pie.
- Un recuadro amplía Lima y Callao, sin rótulos de ejes; sus nombres van en tinta oscura con halo claro para leerse sobre cualquier relleno.
- Un color de claro a oscuro, desde 0; nunca arcoíris.
- Leyenda con la unidad: % de personas.
- Lima (15) y Callao (07) van separados.
- Pondera por hogar con `factor07 × mieperho`, como en las cifras oficiales del INEI.
```
</details>

**Herramienta:** `Bash`

```json
{
 "command": "ls referencias; uv run .claude/skills/graficando-enaho/scripts/graficar.py 2>&1 | tail -25; echo ======; uv run .claude/skills/mapeando-enaho/scripts/mapear.py 2>&1 | tail -25; ls figuras mapas",
 "timeout": 600000
}
```

<details><summary>Resultado de la herramienta</summary>

```text
README.md
inei_pobreza_2024.csv
limites_ambitos_ign.geojson
limites_departamentales_ign.geojson
figuras/pobreza_por_area.png (Rural: 39.3 %, Urbana: 24.8 %)
figuras/pobreza_por_departamento.png (Cajamarca: 45.0 %, Loreto: 43.0 %, Puno: 39.9 %, Pasco: 39.0 %, Huánuco: 39.0 %, Callao: 33.9 %, Huancavelica: 33.4 %, Ayacucho: 32.8 %, Piura: 31.9 %, La Libertad: 30.2 %, Lima Metropolitana: 27.6 %, Ucayali: 27.1 %, Tumbes: 26.9 %, Amazonas: 25.7 %, Tacna: 24.0 %, Apurímac: 24.0 %, Áncash: 22.8 %, San Martín: 22.0 %, Lima provincias: 21.7 %, Cusco: 18.5 %, Junín: 18.5 %, Arequipa: 15.8 %, Lambayeque: 14.0 %, Madre de Dios: 11.1 %, Moquegua: 11.0 %, Ica: 6.0 %; cifras referenciales del INEI (CV > 15 %): Ica, Madre de Dios y Moquegua)
figuras/pobreza_por_edad.png (0 a 14 años: 37.5 %, 15 a 29 años: 26.0 %, 30 a 44 años: 27.9 %, 45 a 59 años: 21.4 %, 60 años y más: 22.0 %)
figuras/pobreza_por_sexo.png (Mujeres: 27.7 %, Hombres: 27.4 %)
figuras/pobreza_serie_2020_2024.png (serie 2020-2024)
======
mapas/pobreza_departamento.png (25 departamentos con dato; CAJAMARCA: 45.0 %, LORETO: 43.0 %, PUNO: 39.9 %, MADRE DE DIOS: 11.1 %, MOQUEGUA: 11.0 %, ICA: 6.0 %)
mapas/pobreza_ambitos.png (26 ám
… [212 caracteres omitidos]
```
</details>

**Claude:**

Ahora los gráficos del BCRP y la revisión del borrador existente.

**Herramienta:** `mcp__bcrp__graficar_serie`

```json
{
 "codigo": "PN01273PM",
 "desde": "2020-01",
 "hasta": "2024-12"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
{"archivo":"figuras/bcrp_PN01273PM_2020-01_2024-12.png","codigo":"PN01273PM","nombre":"Índice de precios Lima Metropolitana (var% 12 meses) - IPC","periodo":"2020-01 a 2024-12","n":60,"primero":{"periodo":"2020-01","valor":1.88835605229068},"ultimo":{"periodo":"2024-12","valor":1.96630270142824},"fuente":"https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01273PM/json/2020-1/2024-12"}
```
</details>

**Herramienta:** `mcp__bcrp__graficar_serie`

```json
{
 "codigo": "PN01728AM",
 "desde": "2020-01",
 "hasta": "2024-12"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
{"archivo":"figuras/bcrp_PN01728AM_2020-01_2024-12.png","codigo":"PN01728AM","nombre":"Producto bruto interno y demanda interna (variación porcentual interanual) - PBI","periodo":"2020-01 a 2024-12","n":60,"primero":{"periodo":"2020-01","valor":3.30328579210706},"ultimo":{"periodo":"2024-12","valor":5.06622215564914},"fuente":"https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01728AM/json/2020-1/2024-12"}
```
</details>

**Herramienta:** `mcp__bcrp__graficar_serie`

```json
{
 "codigo": "PN07746EM",
 "desde": "2020-01",
 "hasta": "2024-12"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
{"archivo":"figuras/bcrp_PN07746EM_2020-01_2024-12.png","codigo":"PN07746EM","nombre":"Indicadores de las empresas bancarias - Cartera atrasada neta / Colocaciones netas (%) - Empresas Bancarias","periodo":"2020-01 a 2024-12","n":60,"primero":{"periodo":"2020-01","valor":3.1038717695207},"ultimo":{"periodo":"2024-12","valor":3.8},"fuente":"https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN07746EM/json/2020-1/2024-12"}
```
</details>

**Herramienta:** `Bash`

```json
{
 "command": "grep -n \"figuras/\\|mapas/\" informes/borrador.md; grep -c \"{{\" informes/borrador.md; git status --short informes"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
54:![Inflación a 12 meses, PN01273PM](../figuras/bcrp_PN01273PM_2020-01_2024-12.png)
58:![PBI interanual, PN01728AM](../figuras/bcrp_PN01728AM_2020-01_2024-12.png)
62:![Morosidad neta bancaria, PN07746EM](../figuras/bcrp_PN07746EM_2020-01_2024-12.png)
66:![Pobreza monetaria 2020-2024](../figuras/pobreza_serie_2020_2024.png)
70:![Pobreza por área](../figuras/pobreza_por_area.png)
74:![Pobreza por departamento](../figuras/pobreza_por_departamento.png)
78:![Mapa departamental](../mapas/pobreza_departamento.png)
82:![Mapa por ámbitos](../mapas/pobreza_ambitos.png)
19
?? informes/verificacion.md
```
</details>

**Claude:**

El borrador con marcadores ya existe y los insumos están regenerados. Armo el informe.

**Herramienta:** `Bash`

```json
{
 "command": "uv run .claude/skills/informando-peru/scripts/armar_informe.py 2>&1 | tail -30",
 "timeout": 600000
}
```

<details><summary>Resultado de la herramienta</summary>

```text
+-----------------------------------------------------------------------------+
|                                                                             |
|                                                                             |
|                        \u2584\u2580\u2580 \u2584\u2580\u2588 \u2588\u2580\u2580 \u2580\u2588\u2580 \u2588\u2580\u2584\u2580\u2588 \u2588\u2580\u2580 \u2588\u2580\u2588                        |
|                        \u2588\u2580  \u2588\u2580\u2588 \u2584\u2584\u2588  \u2588  \u2588 \u2580 \u2588 \u2588\u2584\u2584 \u2588\u2580\u2580                        |
|                                                                             |
|                                                                             |
|                                                                             |
|                                FastMCP 4.1.6                                |
|                            https://gofastmcp.com                            |
|                                                                             |
|                 \U0001f5a5  Server:      sbs, 4.1.6                                  |
|             
… [452 caracteres omitidos]
```
</details>

**Claude:**

Informe armado: 79 cifras resueltas. Ahora la verificación de consistencia.

**Herramienta:** `Skill`

```json
{
 "skill": "verificando-consistencia"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
Launching skill: verificando-consistencia
```
</details>

<details><summary>Instrucciones de la skill que cargó Claude Code</summary>

```markdown
Base directory for this skill: ~\Documents\GitHub\agente-socioeconomico-peru\.claude\skills\verificando-consistencia

# Verificar la consistencia entre herramientas

1. Corre exactamente: `uv run ~/Documents/GitHub/agente-socioeconomico-peru/.claude/skills/verificando-consistencia/scripts/verificar.py`
   Si el BCRP o la SBS no responden, el script marca esas verificaciones como «NO VERIFICABLE» y sigue. Para revisar solo la ENAHO y el informe sin consultar al BCRP, usa `--sin-bcrp`.
2. Lee `salidas/consistencia.md` y responde con el conteo de resultados y cada línea que no sea OK, con su explicación.

## Qué contrasta

| Fuente | Verificación |
|---|---|
| ENAHO | Pobreza nacional con peso de hogar frente a peso de persona; validaciones de la limpieza; la tasa nacional entre la urbana y la rural; los 25 departamentos que exige la consigna y, frente al informe técnico del INEI (Cuadro III.1, p. 220), los 24 departamentos con cifra publicada, Lima Metropolitana y Lima provincias. Lima (15) queda fuera de esa comparación porque el INEI no publica una cifra del departamento en conjunto; el mapa frente a los indicadores |
| BCRP | La inflación a 12 meses recalculada desde el índice del IPC vigente (`PN38705PM`, Dic.2021 = 100) frente a la publicada (`PN01273PM`); `resumen` frente a los datos de `serie` |
| BCRP y SBS | La morosidad bancaria de cada diciembre de 2020 a 2024: `PN07746EM` del BCRP, «Cartera atrasada neta / Colocaciones netas (%) - Empresas Bancarias», frente al B-2401 de la SBS, «Créditos Atrasados (criterio SBS) / Créditos Directos». Informa la diferencia absoluta máxima y queda en DIFERENCIA, porque las definiciones no son iguales |
| Informe | Cada cifra de `informes/informe_final.md` frente a una nueva consulta a sus herramientas |

## Cómo leer el resultado

- **OK**: coinciden dentro de la tolerancia.
- **DIFERENCIA**: no coinciden por una razón conocida, que la tabla explica (por ejemplo, dos ponderadores distintos).
- **FALLA**: no coinciden y no debería pasar. Detente y muéstrala; no corrijas cifras a mano para que coincidan.
- **NO VERIFICABLE**: la fuente no respondió, la serie no tiene datos del periodo o falta un insumo. El detalle dice cuál de los tres. Dilo como limitación; no lo reemplaces por una estimación.
```
</details>

**Herramienta:** `Bash`

```json
{
 "command": "uv run .claude/skills/verificando-consistencia/scripts/verificar.py 2>&1 | tail -15; echo ====; grep -v \"| OK |\" salidas/consistencia.md | head -60; grep -c \"| OK |\" salidas/consistencia.md",
 "timeout": 600000
}
```

<details><summary>Resultado de la herramienta</summary>

```text
|                                                                             |
|                                                                             |
|                                                                             |
|                                FastMCP 4.1.6                                |
|                            https://gofastmcp.com                            |
|                                                                             |
|                 \U0001f5a5  Server:      sbs, 4.1.6                                  |
|                 \U0001f680 Deploy free: https://horizon.prefect.io                  |
|                                                                             |
+-----------------------------------------------------------------------------+


[11/07/26 09:48:00] INFO     Starting MCP server 'sbs' with    transport.py:241
                             transport 'stdio'                                 
salidas/consistencia.md: DIFERENCIA 1, OK 8
====
# Consistencia entre herramientas

Generado por `verificando-consistencia/scripts/verificar.py`. DIFERENCIA: 1, OK: 8.

| Fuente | Verificación | Resultado |
… [2133 caracteres omitidos]
```
</details>

**Herramienta:** `Bash`

```json
{
 "command": "sed -n 1,12p informes/informe_final.md >/dev/null; grep -n \"^## \" informes/informe_final.md; grep -n -i \"limitaci\" -A8 informes/informe_final.md | head -30; git status --short | head"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
3:## 1. Pregunta de investigación
9:## 2. Fuentes y metodología
17:## 3. Resultados
50:## 4. Visualizaciones
84:## 5. Interpretación
94:## 6. Limitaciones
104:## 7. Reproducibilidad
112:## Trazabilidad de las cifras
200:## Referencias
94:## 6. Limitaciones
95-
96-- **Cobertura geográfica de la inflación.** `PN01273PM` mide los precios de Lima Metropolitana; no representa la inflación que enfrentan los hogares rurales o de otros departamentos.
97-- **Definiciones de morosidad.** La SBS (créditos atrasados / créditos directos) y el BCRP (cartera atrasada neta / colocaciones netas) usan definiciones distintas; sus valores se presentan por separado y no deben sumarse ni promediarse.
98-- **Fecha del ratio de capital global.** El boletín B-2401 de diciembre de 2024 publica el ratio de capital global al 30 de noviembre de 2024.
99-- **Error muestral de la ENAHO.** Las tasas son estimaciones de una encuesta por muestreo; el informe no calcula intervalos de confianza. Diferencias pequeñas, como la de hombres y mujeres o la de departamentos con tasas cercanas (Pasco y Huánuco), pueden no ser estadísticamente significativas, y las estimaciones departamentales tienen mayor error que las nacio
… [939 caracteres omitidos]
```
</details>

**Claude:**

El informe está listo en `informes/informe_final.md`. Las 79 cifras se resolvieron de nuevo con sus herramientas y ninguna difiere ni quedó sin dato.

## Hallazgos principales
1. **Inflación y actividad:** la inflación a 12 meses de Lima Metropolitana (BCRP, `PN01273PM`) pasó de 2.0 % en diciembre de 2020 a un máximo de 8.8 % en junio de 2022 y cerró 2024 en 2.0 %. El PBI (BCRP, `PM04863AA`) varió −10.9 % en 2020, 13.4 % en 2021, 2.8 % en 2022, −0.4 % en 2023 y 3.5 % en 2024.
2. **Morosidad:** subió de 2021 a 2023 y bajó en 2024.
   - Créditos atrasados sobre créditos directos de la banca múltiple (SBS, B-2401, diciembre): 3.80 % en 2020, 4.31 % en 2023 y 3.75 % en 2024.
   - La serie neta del BCRP (`PN07746EM`) tiene el mismo perfil y cerró 2024 en 3.80 %.
   - Contexto financiero de la SBS: el ROE de la banca pasó de 4.0 % a 15.3 % entre diciembre de 2020 y diciembre de 2024. Los cuatro mayores bancos concentraban 84.0 % de los créditos directos.
3. **Pobreza monetaria (ENAHO):** fue 30.1 % en 2020, 25.9 % en 2021, 27.5 % en 2022, 29.0 % en 2023 y 27.6 % en 2024.
   - **Urbano-rural en 2024:** 39.3 % en el área rural y 24.8 % en la urbana. La brecha es menor que en 2020 (45.7 % frente a 26.0 %).
   - **Territorio en 2024:** las tasas más altas fueron Cajamarca (45.0 %), Loreto (43.0 %) y Puno (39.9 %). Las más bajas fueron Ica (6.0 %), Moquegua (11.0 %) y Madre de Dios (11.1 %). Lima Metropolitana tuvo 27.6 %.
   - Ica, Moquegua y Madre de Dios son cifras referenciales del INEI (coeficiente de variación mayor que 15 %).

Las series se describen lado a lado como coincidencias en el tiempo, no como causas.

## Verificación de consistencia (`salidas/consistencia.md`)
- **Resultado:** 8 OK, 1 DIFERENCIA y 0 fallas.
- **ENAHO:** las 135 comprobaciones de la limpieza pasan. Los departamentos y el mapa coinciden con el INEI dentro de ±0.1 puntos.
- **BCRP:** la inflación recalculada desde el índice del IPC coincide con la publicada.
- **Diferencia esperada:** la morosidad del BCRP y la de la SBS no coinciden porque miden cosas distintas. La brecha máxima es 0.05 puntos, en diciembre de 2024 (3.80 % del BCRP frente a 3.75 % de la SBS). Por eso el informe las presenta por separado.

## Limitaciones
- Las tasas de la ENAHO no llevan intervalos de confianza, así que diferencias pequeñas pueden no ser significativas. Por ejemplo, la tasa de hombres (27.4 %) y la de mujeres (27.7 %), o la de Pasco y Huánuco (ambas 39.0 %).
- Hay defectos de rotulado en tres figuras:
  - Figura 3: el subtítulo aparece cortado.
  - Figura 4: se superponen las etiquetas de 2020 de la pobreza urbana y de Lima.
  - Figura 8: se superponen los rótulos de Lima y Callao.
  - Las cifras correctas están en el cuadro 1 y en la sección 3.

## Para dejar al día en git
- `salidas/`, `figuras/` y `mapas/` estaban borrados en el árbol de trabajo y los regeneré. El informe también cambió respecto al último commit.
- Los gráficos del BCRP nuevos no están en el repo, y tampoco `salidas/bcrp/`. El último commit había retirado los gráficos del BCRP con el estilo anterior.
- El sello de trazabilidad advierte de cambios sin commitear. Un informe para entregar debería armarse sobre un árbol commiteado, así que conviene commitear y volver a correr `armar_informe.py`.
- No he hecho commit.
- `informes/verificacion.md` sigue con la plantilla sin completar (`_completar_`), porque es la comprobación manual que debe hacer una persona.

---

**Resultado final** · turnos: 21 · costo USD: 0.2744205 · duración: 111.0 s
