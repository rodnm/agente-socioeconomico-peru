# Corrida final aislada: 2 servidores MCP y 5 skills (2026-11-07)

## Línea de tiempo

Servidores MCP: `bcrp`, `sbs` · Skills: `informando-peru`, `limpiando-enaho`, `graficando-enaho`, `mapeando-enaho`, `verificando-consistencia` · 57 llamadas a herramientas

1. Skill `informando-peru`
2. Bash `ls; ls datos salidas figuras mapas informes 2>&1 | head -50`
3. Skill `limpiando-enaho`
4. `ToolSearch`
5. `Read`
6. Bash `uv run ~/Documents/GitHub/agente-socioeconomico-peru/.claude/skills/limpiando-enaho/script`
7. Skill `graficando-enaho`
8. Skill `mapeando-enaho`
9. Bash `ls referencias; uv run ~/Documents/GitHub/agente-socioeconomico-peru/.claude/skills/grafic`
10. MCP `bcrp.buscar_series`
11. MCP `bcrp.buscar_series`
12. MCP `bcrp.buscar_series`
13. MCP `sbs.indicadores`
14. MCP `bcrp.buscar_series`
15. MCP `bcrp.buscar_series`
16. MCP `bcrp.buscar_series`
17. MCP `sbs.indicadores`
18. MCP `sbs.indicadores`
19. MCP `sbs.indicadores`
20. MCP `sbs.indicadores`
21. MCP `bcrp.buscar_series`
22. MCP `bcrp.buscar_series`
23. MCP `bcrp.buscar_series`
24. MCP `bcrp.buscar_series`
25. MCP `bcrp.buscar_series`
26. MCP `bcrp.buscar_series`
27. MCP `bcrp.buscar_series`
28. MCP `bcrp.resumen`
29. MCP `bcrp.resumen`
30. MCP `bcrp.resumen`
31. MCP `bcrp.buscar_series`
32. MCP `bcrp.graficar_serie`
33. MCP `bcrp.graficar_serie`
34. MCP `bcrp.comparar_series`
35. MCP `sbs.indicadores`
36. Bash `cd ~/Documents/GitHub/agente-socioeconomico-peru/.claude/skills/informando-peru && ls -R .`
37. `Read`
38. `Read`
39. Bash `cd ~/Documents/GitHub/agente-socioeconomico-peru && head -3 salidas/indicadores.csv; cut -`
40. Bash `awk -F, '$1==2024{print $2}' salidas/indicadores.csv | tr '\n' ' '`
41. `Grep`
42. `Grep`
43. `Write`
44. MCP `bcrp.graficar_serie`
45. MCP `bcrp.serie`
46. `Write`
47. `Edit`
48. `Edit`
49. `Edit`
50. Bash `uv run ~/Documents/GitHub/agente-socioeconomico-peru/.claude/skills/informando-peru/script`
51. `Edit`
52. Bash `uv run ~/Documents/GitHub/agente-socioeconomico-peru/.claude/skills/informando-peru/script`
53. Skill `verificando-consistencia`
54. `Read`
55. Bash `uv run ~/Documents/GitHub/agente-socioeconomico-peru/.claude/skills/verificando-consistenc`
56. `Edit`
57. Bash `uv run ~/Documents/GitHub/agente-socioeconomico-peru/.claude/skills/informando-peru/script`

## 1. Pedido (claude -p)

Investiga esta pregunta y entrégame el informe: ¿Cómo evolucionaron la inflación, la actividad económica, la morosidad bancaria y la pobreza monetaria del Perú entre 2020 y 2024, y qué brechas territoriales y urbano-rurales presentaba la pobreza en 2024? Usa el BCRP para la inflación, la actividad y la morosidad neta, la SBS para la morosidad bancaria 2020-2024 y el contexto financiero, y la ENAHO para la serie de pobreza 2020-2024 y la foto territorial de 2024 con sus mapas. Al final verifica la consistencia de las cifras.

**Claude:**

Empiezo leyendo la skill que orquesta el informe y el estado del repo.

**Herramienta:** `Skill`

```json
{
 "skill": "informando-peru"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
Launching skill: informando-peru
```
</details>

<details><summary>Instrucciones de la skill que cargó Claude Code</summary>

```markdown
Base directory for this skill: ~\Documents\GitHub\agente-socioeconomico-peru\.claude\skills\informando-peru

# Informar con cifras trazables

El informe se escribe en dos pasos: Claude redacta un borrador con **marcadores** en lugar de números y un script los resuelve llamando de nuevo a las herramientas. Así cada cifra se puede rastrear y repetir.

1. **Plan.** Escribe `informes/plan_analisis.md`: la pregunta (), qué series del BCRP y qué indicadores de la ENAHO la responden, y qué gráficos hacen falta.
2. **Insumos.** Comprueba que existan. Si falta alguno, invoca la skill indicada con la herramienta Skill, no corras su script por tu cuenta: la skill trae sus propias reglas, como detenerse si una validación falla.
   - `salidas/indicadores.csv` → `limpiando-enaho`.
   - `figuras/pobreza_por_<corte>.png` y `figuras/pobreza_serie_2020_2024.png` → `graficando-enaho`.
   - `mapas/pobreza_departamento.png` y `mapas/pobreza_ambitos.png` → `mapeando-enaho`.
   - El gráfico del BCRP → herramienta MCP `graficar_serie`.
   Consulta las series con las herramientas MCP (`buscar_series`, `resumen`, `comparar_series`) para decidir qué decir; anota los argumentos exactos que usaste.
3. **Borrador.** Copia [plantilla.md](plantilla.md) a `informes/borrador.md` y redáctalo con las 7 secciones. **Cada cifra va como marcador**:
   - `{{enaho.pobreza_nacional}}`: el `id` de `salidas/indicadores.csv` (año 2024 por defecto; admite selector como `{{enaho.pobreza_nacional:2020}}`).
   - `{{bcrp.resumen(codigo=PN01273PM, desde=2024-01, hasta=2024-12).ultimo.valor|2}}`: la herramienta, sus argumentos y el campo de la respuesta; `|2` son los decimales.
   - `{{bcrp.comparar_series(codigo_a=..., codigo_b=..., desde=..., hasta=...).correlacion|2}}`, `{{sbs.<herramienta>(...).<campo>}}`: igual con cualquier servidor de `.mcp.json`.
   - `{{lit:0.1 puntos}}`: solo para constantes metodológicas (tolerancias, umbrales), que quedan declaradas como escritas a mano.
   Los años y los códigos de serie pueden ir como texto.
4. **Armar.** Corre exactamente: `uv run ~/Documents/GitHub/agente-socioeconomico-peru/.claude/skills/informando-peru/scripts/armar_informe.py`
   - Si dice «cifra escrita a mano», reemplaza esa cifra por un marcador. Nunca la disfraces ni la saques del texto para pasar la revisión.
   - Si un marcador no se resuelve porque la herramienta falló o no hay datos, **no estimes**: explícalo en Limitaciones y vuelve a correr con `--permitir-faltantes`, que lo marca como «sin dato» y lo lista.
5. **Verificar.** Invoca la skill `verificando-consistencia` con la herramienta Skill y menciona su resultado en el informe.
6. Responde con la ruta de `informes/informe_final.md`, los tres hallazgos y cualquier dato no disponible.

## Reglas

- Asociación no es causalidad: una serie nacional mensual y una encuesta anual por departamento no prueban relaciones entre sí.
- Cada hallazgo cita su fuente en la misma oración: código de serie y periodo, boletín de la SBS y periodo, o indicador y año de la ENAHO.
- El script agrega la tabla de trazabilidad y las referencias; no las escribas a mano. Las referencias siguen la norma APA 7 y salen de los metadatos de cada respuesta: una por serie del BCRP, por boletín y periodo de la SBS y por año y módulo de la ENAHO, más el informe técnico del INEI cuando se usa la ENAHO y los límites del IGN cuando el informe incluye un mapa de `mapas/`. Si una fuente no trae metadatos suficientes, el informe lo advierte en lugar de completarla.
- El sello de la trazabilidad nombra el commit y advierte si hay cambios sin commitear en los insumos. Un informe para entregar se arma sobre un árbol commiteado.
```
</details>

**Herramienta:** `Bash`

```json
{
 "command": "ls; ls datos salidas figuras mapas informes 2>&1 | head -50",
 "description": "Listar estado del repo"
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
verificacion.md

mapas:

salidas:
consistencia.csv
consistencia.md
```
</details>

**Claude:**

Faltan los insumos de la ENAHO (indicadores, figuras y mapas). Los regenero con sus skills, y cargo las herramientas MCP en paralelo.

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

**Herramienta:** `ToolSearch`

```json
{
 "query": "select:mcp__bcrp__buscar_series,mcp__bcrp__resumen,mcp__bcrp__comparar_series,mcp__bcrp__graficar_serie,mcp__bcrp__serie,mcp__sbs__indicadores,mcp__sbs__ultimo_periodo,mcp__sbs__listar_reportes,mcp__sbs__reporte",
 "max_results": 10
}
```

<details><summary>Resultado de la herramienta</summary>

```text









```
</details>

**Herramienta:** `Read`

```json
{
 "file_path": "~\\Documents\\GitHub\\agente-socioeconomico-peru\\.claude\\skills\\informando-peru\\plantilla.md"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
1	# Título: la pregunta en pocas palabras
2	
3	<!-- Copia esta plantilla a informes/borrador.md. Cada cifra va como marcador; armar_informe.py las resuelve.
4	     Marcadores: {{enaho.<id>}}, {{bcrp.<herramienta>(arg=valor, ...).<campo>|decimales}},
5	     {{sbs.<herramienta>(...).<campo>}} y {{lit:texto}} para constantes metodológicas. -->
6	
7	## 1. Pregunta de investigación
8	
9	Tema, objetivo y delimitación: qué periodo cubre cada fuente, qué territorio y qué no se pretende demostrar (ninguna relación causal).
10	
11	## 2. Fuentes y metodología
12	
13	- **BCRP**: series consultadas por el servidor MCP `bcrp`, con su código y periodo.
14	- **ENAHO 2024 (INEI)**: módulos 34 y 02, residentes habituales, factores de expansión `factor07 × mieperho` (hogar) y `facpob07` (persona), procesados con la skill `limpiando-enaho`.
15	- Otras fuentes oficiales, si se usaron (por ejemplo, la SBS por su servidor MCP).
16	- Indicadores construidos y por qué.
17	
18	## 3. Resultados
19	
20	Al menos tres hallazgos, cada uno con sus cifras como marcadores y la fuente en la misma oración.
21	
22	1. Hallazgo macroeconómico (BCRP).
23	2. Hallazgo territorial o urbano-rural (ENAHO).
24	3. Hallazgo que 
… [888 caracteres omitidos]
```
</details>

**Herramienta:** `Bash`

```json
{
 "command": "uv run ~/Documents/GitHub/agente-socioeconomico-peru/.claude/skills/limpiando-enaho/scripts/limpiar.py --todos 2>&1 | tail -40; echo ----; cat salidas/validacion.txt",
 "description": "Limpiar ENAHO 2020-2024 y validar",
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
----
Metas: INEI (2025), Perú: Evolución de la pobreza monetaria, 2015-2024. Informe técnico; páginas impresas del PDF con SHA-256 ed964c41c963f0ac5ce11b1713680ec93519838b9db0cd8fa139e6bb922d6c73.
Tolerancia de 0.1 puntos: réplica de una cifra que el INEI publica con un decimal; no es una prueba estadística. La incertidumbre de muestreo la dan los IC al 95 % del INEI, publicados solo para 2024.
Tolerancia de 0.2 puntos en la línea facpob07 de 2020 a 2023 y de 0.1 en 2024: contraste con el factor de cada persona, que no es el ponderador del método oficial (factor07 × mieperho); con ese ponderador, 2021 difiere en 0.16 puntos de la 
… [13331 caracteres omitidos]
```
</details>

**Claude:**

Sin fallas. Ahora gráficos y mapas.

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
 "command": "ls referencias; uv run ~/Documents/GitHub/agente-socioeconomico-peru/.claude/skills/graficando-enaho/scripts/graficar.py 2>&1 | tail -30; echo ---MAPA; uv run ~/Documents/GitHub/agente-socioeconomico-peru/.claude/skills/mapeando-enaho/scripts/mapear.py 2>&1 | tail -30",
 "description": "Generar gráficos y mapas ENAHO",
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
---MAPA
mapas/pobreza_departamento.png (25 departamentos con dato; CAJAMARCA: 45.0 %, LORETO: 43.0 %, PUNO: 39.9 %, MADRE DE DIOS: 11.1 %, MOQUEGUA: 11.0 %, ICA: 6.0 %)
mapas/pobreza_ambitos.png (26 á
… [30 caracteres omitidos]
```
</details>

**Claude:**

Ahora las series del BCRP y la SBS.

**Herramienta:** `mcp__bcrp__buscar_series`

```json
{
 "texto": "ipc lima metropolitana variación porcentual 12 meses",
 "frecuencia": "Mensual"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
{"result":[]}
```
</details>

**Herramienta:** `mcp__bcrp__buscar_series`

```json
{
 "texto": "producto bruto interno variaciones porcentuales 12 meses",
 "frecuencia": "Mensual"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
{"result":[]}
```
</details>

**Herramienta:** `mcp__bcrp__buscar_series`

```json
{
 "texto": "morosidad neta"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
{"result":[]}
```
</details>

**Herramienta:** `mcp__sbs__indicadores`

```json
{
 "tipo_entidad": "bancos",
 "indicador": "morosidad",
 "periodo": "2024-12"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
{"tipo_entidad":"bancos","codigo":"B-2401","titulo":"Indicadores Financieros por Empresa Bancaria","periodo":"2024-12","fuente":"https://intranet2.sbs.gob.pe/estadistica/financiera/2024/Diciembre/B-2401-di2024.XLS","actualizado":"Thu, 30 Jan 2025 23:45:56 GMT","cita":"Fuente: SBS, Indicadores Financieros por Empresa Bancaria (B-2401), 2024-12. https://intranet2.sbs.gob.pe/estadistica/financiera/2024/Diciembre/B-2401-di2024.XLS","orden":"de mayor a menor valor","indicadores":[{"seccion":"CALIDAD DE ACTIVOS","indicador":"Créditos Atrasados (criterio SBS) / Créditos Directos","valores":[{"entidad":"B. Pichincha","valor":6.75},{"entidad":"Mibanco","valor":6.63},{"entidad":"B. Santander Perú","valor":4.89},{"entidad":"Alfin Banco","valor":4.37},{"entidad":"Scotiabank Perú","valor":4.26},{"entidad":"BANCOM","valor":3.93},{"entidad":"B. Interamericano de Finanzas","valor":3.84},{"entidad":"B. BBVA Perú","valor":3.72},{"entidad":"B. Ripley","valor":3.67},{"entidad":"B. De Crédito del Perú (con sucursales en el exterior)","valor":3.56},{"entidad":"B. Falabella Perú","valor":3.2600000000000002},{"entidad":"Interbank","valor":2.71},{"entidad":"B. GNB","valor":2.69},{"entidad":"B. BCI Perú","v
… [225 caracteres omitidos]
```
</details>

**Herramienta:** `mcp__bcrp__buscar_series`

```json
{
 "texto": "ipc",
 "frecuencia": "Mensual",
 "limite": 25
}
```

<details><summary>Resultado de la herramienta</summary>

```text
{"result":[{"codigo":"PN01271PM","nombre":"Índice de precios Lima Metropolitana (var% mensual) - IPC","categoria":"Inflación","frecuencia":"Mensual","inicio":"Ene-1950","actualizada":"2026-10-08"},{"codigo":"PN01273PM","nombre":"Índice de precios Lima Metropolitana (var% 12 meses) - IPC","categoria":"Inflación","frecuencia":"Mensual","inicio":"Ene-1950","actualizada":"2026-10-08"},{"codigo":"PN01272PM","nombre":"Índice de precios Lima Metropolitana (var% acumulada) - IPC","categoria":"Inflación","frecuencia":"Mensual","inicio":"Ene-1950","actualizada":"2026-10-08"},{"codigo":"PN09818PM","nombre":"Índice de precios Lima Metropolitana (var% mensual) - IPC Importado","categoria":"Inflación","frecuencia":"Mensual","inicio":"Ene-1991","actualizada":"2026-10-08"},{"codigo":"PN01278PM","nombre":"Índice de precios Lima Metropolitana (var% mensual) - IPC Subyacente","categoria":"Inflación","frecuencia":"Mensual","inicio":"Ene-1993","actualizada":"2026-10-08"},{"codigo":"PN01280PM","nombre":"Índice de precios Lima Metropolitana (var% mensual) - IPC Transables","categoria":"Inflación","frecuencia":"Mensual","inicio":"Ene-1993","actualizada":"2026-10-08"},{"codigo":"PN09821PM","nombre":"Índice
… [3855 caracteres omitidos]
```
</details>

**Herramienta:** `mcp__bcrp__buscar_series`

```json
{
 "texto": "pbi",
 "frecuencia": "Mensual",
 "limite": 25
}
```

<details><summary>Resultado de la herramienta</summary>

```text
{"result":[{"codigo":"PN02079AM","nombre":"Producción manufacturera (índice 2007 = 100) - Total","categoria":"PBI por sectores","frecuencia":"Mensual","inicio":"Ene-1994","actualizada":"2026-10-23"},{"codigo":"PD38048AM","nombre":"Expectativas macroeconómicas - Expectativa de PBI a 12 meses","categoria":"Expectativas Macroeconómicas","frecuencia":"Mensual","inicio":"Ene-2007","actualizada":"2026-10-02"},{"codigo":"PN01787AM","nombre":"Producción agropecuaria (miles de toneladas) - Agrícola - Ajo","categoria":"PBI por sectores","frecuencia":"Mensual","inicio":"Ene-2007","actualizada":"2026-10-23"},{"codigo":"PN01793AM","nombre":"Producción agropecuaria (miles de toneladas) - Agrícola - Uva","categoria":"PBI por sectores","frecuencia":"Mensual","inicio":"Ene-2007","actualizada":"2026-10-23"},{"codigo":"PN01800AM","nombre":"Producción agropecuaria (miles de toneladas) - Pecuario - Ave","categoria":"PBI por sectores","frecuencia":"Mensual","inicio":"Ene-2003","actualizada":"2026-10-23"},{"codigo":"PN01777AM","nombre":"Producción agropecuaria (miles de toneladas) - Agrícola - Papa","categoria":"PBI por sectores","frecuencia":"Mensual","inicio":"Ene-2007","actualizada":"2026-10-23"},{"co
… [3802 caracteres omitidos]
```
</details>

**Herramienta:** `mcp__bcrp__buscar_series`

```json
{
 "texto": "morosidad",
 "limite": 25
}
```

<details><summary>Resultado de la herramienta</summary>

```text
{"result":[]}
```
</details>

**Herramienta:** `mcp__sbs__indicadores`

```json
{
 "tipo_entidad": "bancos",
 "indicador": "morosidad",
 "periodo": "2020-12"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
{"tipo_entidad":"bancos","codigo":"B-2401","titulo":"Indicadores Financieros por Empresa Bancaria","periodo":"2020-12","fuente":"https://intranet2.sbs.gob.pe/estadistica/financiera/2020/Diciembre/B-2401-di2020.XLS","actualizado":"Fri, 03 Jun 2022 18:14:02 GMT","cita":"Fuente: SBS, Indicadores Financieros por Empresa Bancaria (B-2401), 2020-12. https://intranet2.sbs.gob.pe/estadistica/financiera/2020/Diciembre/B-2401-di2020.XLS","orden":"de mayor a menor valor","indicadores":[{"seccion":"CALIDAD DE ACTIVOS","indicador":"Créditos Atrasados (criterio SBS) / Créditos Directos","valores":[{"entidad":"B. Azteca Perú","valor":15.46},{"entidad":"B. Ripley","valor":11.65},{"entidad":"Mibanco","valor":7.08},{"entidad":"B. Pichincha","valor":5.55},{"entidad":"Scotiabank Perú","valor":5.37},{"entidad":"B. Falabella Perú","valor":4.69},{"entidad":"B. GNB","valor":3.89},{"entidad":"Interbank (con sucursales en el exterior)","valor":3.4},{"entidad":"B. BBVA Perú","valor":3.22},{"entidad":"B. De Crédito del Perú (con sucursales en el exterior)","valor":3.2},{"entidad":"B. Interamericano de Finanzas","valor":3.18},{"entidad":"B. De Comercio","valor":2.56},{"entidad":"B. Santander Perú","valor":0.89
… [211 caracteres omitidos]
```
</details>

**Herramienta:** `mcp__sbs__indicadores`

```json
{
 "tipo_entidad": "bancos",
 "indicador": "morosidad",
 "periodo": "2021-12"
}
```

**Herramienta:** `mcp__sbs__indicadores`

```json
{
 "tipo_entidad": "bancos",
 "indicador": "morosidad",
 "periodo": "2022-12"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
{"tipo_entidad":"bancos","codigo":"B-2401","titulo":"Indicadores Financieros por Empresa Bancaria","periodo":"2021-12","fuente":"https://intranet2.sbs.gob.pe/estadistica/financiera/2021/Diciembre/B-2401-di2021.XLS","actualizado":"Wed, 02 Feb 2022 21:53:57 GMT","cita":"Fuente: SBS, Indicadores Financieros por Empresa Bancaria (B-2401), 2021-12. https://intranet2.sbs.gob.pe/estadistica/financiera/2021/Diciembre/B-2401-di2021.XLS","orden":"de mayor a menor valor","indicadores":[{"seccion":"CALIDAD DE ACTIVOS","indicador":"Créditos Atrasados (criterio SBS) / Créditos Directos","valores":[{"entidad":"Mibanco","valor":6.79},{"entidad":"B. Pichincha","valor":5.4},{"entidad":"Alfin Banco","valor":5.02},{"entidad":"B. GNB","valor":4.21},{"entidad":"Scotiabank Perú","valor":3.85},{"entidad":"B. De Comercio","valor":3.75},{"entidad":"B. De Crédito del Perú (con sucursales en el exterior)","valor":3.73},{"entidad":"B. BBVA Perú","valor":3.7},{"entidad":"Interbank","valor":3.62},{"entidad":"B. Interamericano de Finanzas","valor":2.94},{"entidad":"B. Ripley","valor":1.88},{"entidad":"B. Falabella Perú","valor":1.74},{"entidad":"B. Santander Perú","valor":1.05},{"entidad":"Citibank","valor":0},{"
… [175 caracteres omitidos]
```
</details>

**Herramienta:** `mcp__sbs__indicadores`

```json
{
 "tipo_entidad": "bancos",
 "indicador": "morosidad",
 "periodo": "2023-12"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
{"tipo_entidad":"bancos","codigo":"B-2401","titulo":"Indicadores Financieros por Empresa Bancaria","periodo":"2022-12","fuente":"https://intranet2.sbs.gob.pe/estadistica/financiera/2022/Diciembre/B-2401-di2022.XLS","actualizado":"Tue, 31 Jan 2023 15:07:55 GMT","cita":"Fuente: SBS, Indicadores Financieros por Empresa Bancaria (B-2401), 2022-12. https://intranet2.sbs.gob.pe/estadistica/financiera/2022/Diciembre/B-2401-di2022.XLS","orden":"de mayor a menor valor","indicadores":[{"seccion":"CALIDAD DE ACTIVOS","indicador":"Créditos Atrasados (criterio SBS) / Créditos Directos","valores":[{"entidad":"Mibanco","valor":5.57},{"entidad":"B. Pichincha","valor":5.51},{"entidad":"B. BBVA Perú","valor":4.37},{"entidad":"B. Falabella Perú","valor":4.13},{"entidad":"Scotiabank Perú","valor":4.08},{"entidad":"B. De Crédito del Perú (con sucursales en el exterior)","valor":3.96},{"entidad":"Alfin Banco","valor":3.75},{"entidad":"B. De Comercio","valor":3.73},{"entidad":"B. GNB","valor":3.73},{"entidad":"B. Interamericano de Finanzas","valor":3.44},{"entidad":"Interbank","valor":3.03},{"entidad":"B. Ripley","valor":2.92},{"entidad":"B. Santander Perú","valor":1.53},{"entidad":"Citibank","valor":0},
… [213 caracteres omitidos]
```
</details>

<details><summary>Resultado de la herramienta</summary>

```text
{"tipo_entidad":"bancos","codigo":"B-2401","titulo":"Indicadores Financieros por Empresa Bancaria","periodo":"2023-12","fuente":"https://intranet2.sbs.gob.pe/estadistica/financiera/2023/Diciembre/B-2401-di2023.XLS","actualizado":"Thu, 25 Jan 2024 14:05:49 GMT","cita":"Fuente: SBS, Indicadores Financieros por Empresa Bancaria (B-2401), 2023-12. https://intranet2.sbs.gob.pe/estadistica/financiera/2023/Diciembre/B-2401-di2023.XLS","orden":"de mayor a menor valor","indicadores":[{"seccion":"CALIDAD DE ACTIVOS","indicador":"Créditos Atrasados (criterio SBS) / Créditos Directos","valores":[{"entidad":"B. Falabella Perú","valor":7.03},{"entidad":"B. Pichincha","valor":6.55},{"entidad":"Mibanco","valor":6.3500000000000005},{"entidad":"B. Ripley","valor":5.76},{"entidad":"B. BBVA Perú","valor":4.71},{"entidad":"Scotiabank Perú","valor":4.5200000000000005},{"entidad":"B. De Crédito del Perú (con sucursales en el exterior)","valor":4.21},{"entidad":"BANCOM","valor":4.08},{"entidad":"Interbank","valor":3.54},{"entidad":"B. Interamericano de Finanzas","valor":3.5100000000000002},{"entidad":"B. GNB","valor":3.42},{"entidad":"Alfin Banco","valor":3.14},{"entidad":"B. BCI Perú","valor":1.84},{"ent
… [264 caracteres omitidos]
```
</details>

**Herramienta:** `mcp__bcrp__buscar_series`

```json
{
 "texto": "producto bruto interno demanda interna var",
 "limite": 25
}
```

<details><summary>Resultado de la herramienta</summary>

```text
{"result":[{"codigo":"PN01728AM","nombre":"Producto bruto interno y demanda interna (variación porcentual interanual) - PBI","categoria":"PBI por sectores","frecuencia":"Mensual","inicio":"Ene-1995","actualizada":"2026-10-23"},{"codigo":"PN01716AM","nombre":"Producto bruto interno y demanda interna (variación porcentual interanual) - Pesca","categoria":"PBI por sectores","frecuencia":"Mensual","inicio":"Ene-1995","actualizada":"2026-10-23"},{"codigo":"PN01725AM","nombre":"Producto bruto interno y demanda interna (variación porcentual interanual) - Comercio","categoria":"PBI por sectores","frecuencia":"Mensual","inicio":"Ene-1995","actualizada":"2026-10-23"},{"codigo":"PN01720AM","nombre":"Producto bruto interno y demanda interna (variación porcentual interanual) - Manufactura","categoria":"PBI por sectores","frecuencia":"Mensual","inicio":"Ene-1995","actualizada":"2026-10-23"},{"codigo":"PN01713AM","nombre":"Producto bruto interno y demanda interna (variación porcentual interanual) - Agropecuario","categoria":"PBI por sectores","frecuencia":"Mensual","inicio":"Ene-1995","actualizada":"2026-10-23"},{"codigo":"PN01724AM","nombre":"Producto bruto interno y demanda interna (variación p
… [4604 caracteres omitidos]
```
</details>

**Herramienta:** `mcp__bcrp__buscar_series`

```json
{
 "texto": "morosidad",
 "frecuencia": "Mensual"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
{"result":[]}
```
</details>

**Herramienta:** `mcp__bcrp__buscar_series`

```json
{
 "texto": "mora"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
{"result":[{"codigo":"RD12939DM","nombre":"Desembarque de anchoveta para harina y aceite por departamento y puerto (toneladas) - Ica - Puerto de Tambo de Mora","categoria":"Producción","frecuencia":"Mensual","inicio":"Ene-2004","actualizada":"2026-09-16"},{"codigo":"RD14250DQ","nombre":"Desembarque de anchoveta para harina y aceite por departamento y puerto (toneladas) - Ica - Puerto de Tambo de Mora","categoria":"Producción","frecuencia":"Trimestral","inicio":"T1-2016","actualizada":"2026-04-30"},{"codigo":"RD15504DA","nombre":"Desembarque de anchoveta para harina y aceite por departamento y puerto (toneladas) - Ica - Puerto de Tambo de Mora","categoria":"Producción","frecuencia":"Anual","inicio":"2003","actualizada":"2026-04-30"}]}
```
</details>

**Herramienta:** `mcp__bcrp__buscar_series`

```json
{
 "texto": "cartera",
 "limite": 25
}
```

<details><summary>Resultado de la herramienta</summary>

```text
{"result":[{"codigo":"PN01183MM","nombre":"Sistema privado de pensiones - Cartera de Inversiones (millones S/)","categoria":"Mercado de capitales","frecuencia":"Mensual","inicio":"Ene-2002","actualizada":"2026-10-23"},{"codigo":"PM10177FA","nombre":"Saldo deuda pública (millones S/) - Canje Temporal de Cartera (mill. S/)","categoria":"Deuda pública","frecuencia":"Anual","inicio":"1999","actualizada":"2026-08-20"},{"codigo":"PM10209FA","nombre":"Saldo deuda pública (porcentaje del PBI) - Canje Temporal de Cartera (% PBI)","categoria":"Deuda pública","frecuencia":"Anual","inicio":"1999","actualizada":"2026-08-20"},{"codigo":"PN01184MM","nombre":"Sistema privado de pensiones - Cartera de Inversiones (composición porcentual)","categoria":"Mercado de capitales","frecuencia":"Mensual","inicio":"Ene-2002","actualizada":"2026-10-23"},{"codigo":"PN39278BQ","nombre":"Cuenta financiera del sector privado (millones US$) - Activos - Inversión de Cartera","categoria":"Cuenta financiera","frecuencia":"Trimestral","inicio":"T1-2012","actualizada":"2026-08-20"},{"codigo":"PN39285BQ","nombre":"Cuenta financiera del sector privado (millones US$) - Pasivos - Inversión de Cartera","categoria":"Cuenta f
… [4461 caracteres omitidos]
```
</details>

**Claude:**

Hay series por banco; busco la del total del sistema.

**Herramienta:** `mcp__bcrp__buscar_series`

```json
{
 "texto": "cartera atrasada neta colocaciones netas total",
 "frecuencia": "Mensual"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
{"result":[]}
```
</details>

**Herramienta:** `mcp__bcrp__buscar_series`

```json
{
 "texto": "cartera atrasada neta colocaciones netas sistema"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
{"result":[]}
```
</details>

**Herramienta:** `mcp__bcrp__buscar_series`

```json
{
 "texto": "cartera atrasada neta colocaciones netas",
 "frecuencia": "Mensual",
 "limite": 60
}
```

<details><summary>Resultado de la herramienta</summary>

```text
{"result":[{"codigo":"PN07738EM","nombre":"Indicadores de las empresas bancarias - Cartera atrasada neta / Colocaciones netas (%) - GNB","categoria":"Empresas bancarias","frecuencia":"Mensual","inicio":"Ene-2010","actualizada":"2026-10-08"},{"codigo":"PN43422EM","nombre":"Indicadores de las empresas bancarias - Cartera atrasada neta / Colocaciones netas (%) - BCI","categoria":"Empresas bancarias","frecuencia":"Mensual","inicio":"Ene-2025","actualizada":"2026-10-08"},{"codigo":"PN07745EM","nombre":"Indicadores de las empresas bancarias - Cartera atrasada neta / Colocaciones netas (%) - ICBC","categoria":"Empresas bancarias","frecuencia":"Mensual","inicio":"Ene-2015","actualizada":"2026-10-08"},{"codigo":"PN07736EM","nombre":"Indicadores de las empresas bancarias - Cartera atrasada neta / Colocaciones netas (%) - BanBif","categoria":"Empresas bancarias","frecuencia":"Mensual","inicio":"Ene-2010","actualizada":"2026-10-08"},{"codigo":"PN07741EM","nombre":"Indicadores de las empresas bancarias - Cartera atrasada neta / Colocaciones netas (%) - Ripley","categoria":"Empresas bancarias","frecuencia":"Mensual","inicio":"Ene-2010","actualizada":"2026-10-08"},{"codigo":"PN07742EM","nombre":"
… [3763 caracteres omitidos]
```
</details>

**Claude:**

Tengo los códigos: inflación `PN01273PM`, PBI `PN01728AM`, morosidad neta de la banca `PN07746EM`. Pruebo la forma de la respuesta de `resumen`.

**Herramienta:** `mcp__bcrp__resumen`

```json
{
 "codigo": "PN01273PM",
 "desde": "2020-01",
 "hasta": "2024-12"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
{"codigo":"PN01273PM","nombre":"Índice de precios Lima Metropolitana (var% 12 meses) - IPC","frecuencia":"Mensual","periodo":"2020-01 a 2024-12","n":60,"primero":{"periodo":"2020-01","valor":1.88835605229068},"ultimo":{"periodo":"2024-12","valor":1.96630270142824},"cambio":0.077947,"variacion_pct":4.127752,"promedio":4.466356,"maximo":{"periodo":"2022-06","valor":8.81263294388897},"minimo":{"periodo":"2020-06","valor":1.59873239164688},"fuente":"https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01273PM/json/2020-1/2024-12"}
```
</details>

**Herramienta:** `mcp__bcrp__resumen`

```json
{
 "codigo": "PN01728AM",
 "desde": "2020-01",
 "hasta": "2024-12"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
{"codigo":"PN01728AM","nombre":"Producto bruto interno y demanda interna (variación porcentual interanual) - PBI","frecuencia":"Mensual","periodo":"2020-01 a 2024-12","n":60,"primero":{"periodo":"2020-01","valor":3.30328579210706},"ultimo":{"periodo":"2024-12","valor":5.06622215564914},"cambio":1.762936,"variacion_pct":53.369175,"promedio":2.247028,"maximo":{"periodo":"2021-04","valor":59.8947623291564},"minimo":{"periodo":"2020-04","valor":-39.276985716532},"fuente":"https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01728AM/json/2020-1/2024-12"}
```
</details>

**Herramienta:** `mcp__bcrp__resumen`

```json
{
 "codigo": "PN07746EM",
 "desde": "2020-01",
 "hasta": "2024-12"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
{"codigo":"PN07746EM","nombre":"Indicadores de las empresas bancarias - Cartera atrasada neta / Colocaciones netas (%) - Empresas Bancarias","frecuencia":"Mensual","periodo":"2020-01 a 2024-12","n":60,"primero":{"periodo":"2020-01","valor":3.1038717695207},"ultimo":{"periodo":"2024-12","valor":3.8},"cambio":0.696128,"variacion_pct":22.427738,"promedio":3.882788,"maximo":{"periodo":"2024-05","valor":4.57},"minimo":{"periodo":"2020-07","valor":3.03434570860496},"fuente":"https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN07746EM/json/2020-1/2024-12"}
```
</details>

**Herramienta:** `mcp__bcrp__buscar_series`

```json
{
 "texto": "producto bruto interno tipo de gasto variaciones porcentuales reales PBI",
 "frecuencia": "Anual"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
{"result":[{"codigo":"PM04923AA","nombre":"Producto bruto interno por tipo de gasto (variaciones porcentuales reales) - PBI","categoria":"PBI gasto","frecuencia":"Anual","inicio":"1922","actualizada":"2026-08-20"},{"codigo":"PM04921AA","nombre":"Producto bruto interno por tipo de gasto (variaciones porcentuales reales) - Exportaciones","categoria":"PBI gasto","frecuencia":"Anual","inicio":"1922","actualizada":"2026-08-20"},{"codigo":"PM04922AA","nombre":"Producto bruto interno por tipo de gasto (variaciones porcentuales reales) - Importaciones","categoria":"PBI gasto","frecuencia":"Anual","inicio":"1922","actualizada":"2026-08-20"},{"codigo":"PM04914AA","nombre":"Producto bruto interno por tipo de gasto (variaciones porcentuales reales) - Demanda Interna","categoria":"PBI gasto","frecuencia":"Anual","inicio":"1922","actualizada":"2026-08-20"},{"codigo":"PM04924AA","nombre":"Producto bruto interno por tipo de gasto (variaciones porcentuales reales) - Demanda Interna sin Inventarios","categoria":"PBI gasto","frecuencia":"Anual","inicio":"1951","actualizada":"2026-08-20"},{"codigo":"PM04915AA","nombre":"Producto bruto interno por tipo de gasto (variaciones porcentuales reales) - Deman
… [1132 caracteres omitidos]
```
</details>

**Herramienta:** `mcp__bcrp__graficar_serie`

```json
{
 "codigo": "PN01273PM",
 "desde": "2020-01",
 "hasta": "2024-12",
 "titulo": "La inflación llegó a su máximo en mediados de 2022 y volvió cerca del 2 % en 2024"
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
 "codigo": "PN07746EM",
 "desde": "2020-01",
 "hasta": "2024-12",
 "titulo": "La morosidad neta de la banca se mantuvo entre 3 % y 4,6 % durante 2020-2024"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
{"archivo":"figuras/bcrp_PN07746EM_2020-01_2024-12.png","codigo":"PN07746EM","nombre":"Indicadores de las empresas bancarias - Cartera atrasada neta / Colocaciones netas (%) - Empresas Bancarias","periodo":"2020-01 a 2024-12","n":60,"primero":{"periodo":"2020-01","valor":3.1038717695207},"ultimo":{"periodo":"2024-12","valor":3.8},"fuente":"https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN07746EM/json/2020-1/2024-12"}
```
</details>

**Herramienta:** `mcp__bcrp__comparar_series`

```json
{
 "codigo_a": "PN01273PM",
 "codigo_b": "PN07746EM",
 "desde": "2020-01",
 "hasta": "2024-12"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
{"frecuencia":"Mensual","periodo":"2020-01 a 2024-12","n":60,"excluidos":0,"correlacion":0.2371,"series":[{"codigo":"PN01273PM","nombre":"Índice de precios Lima Metropolitana (var% 12 meses) - IPC","primero":{"periodo":"2020-01","valor":1.88835605229068},"ultimo":{"periodo":"2024-12","valor":1.96630270142824},"cambio":0.077947,"promedio":4.466356},{"codigo":"PN07746EM","nombre":"Indicadores de las empresas bancarias - Cartera atrasada neta / Colocaciones netas (%) - Empresas Bancarias","primero":{"periodo":"2020-01","valor":3.1038717695207},"ultimo":{"periodo":"2024-12","valor":3.8},"cambio":0.696128,"promedio":3.882788}],"diferencia_a_menos_b":{"promedio":0.583568,"brecha_maxima":{"periodo":"2022-06","valor":4.96451500502738}},"fuentes":["https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01273PM/json/2020-1/2024-12","https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN07746EM/json/2020-1/2024-12"],"nota":"La correlación describe una asociación entre las dos series, no una relación causal."}
```
</details>

**Herramienta:** `mcp__sbs__indicadores`

```json
{
 "tipo_entidad": "cajas municipales",
 "indicador": "morosidad",
 "periodo": "2024-12"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
{"tipo_entidad":"cajas municipales","codigo":"C-1301","titulo":"Indicadores Financieros por Caja Municipal","periodo":"2024-12","fuente":"https://intranet2.sbs.gob.pe/estadistica/financiera/2024/Diciembre/C-1301-di2024.XLS","actualizado":"Thu, 20 Feb 2025 18:59:59 GMT","cita":"Fuente: SBS, Indicadores Financieros por Caja Municipal (C-1301), 2024-12. https://intranet2.sbs.gob.pe/estadistica/financiera/2024/Diciembre/C-1301-di2024.XLS","orden":"de mayor a menor valor","indicadores":[{"seccion":"CALIDAD DE ACTIVOS","indicador":"Créditos Atrasados (criterio SBS) / Créditos Directos","valores":[{"entidad":"CMAC Paita","valor":9.83},{"entidad":"CMAC Maynas","valor":9.39},{"entidad":"CMAC Tacna","valor":8.82},{"entidad":"CMAC Trujillo","valor":8.82},{"entidad":"CMAC Del Santa","valor":8.33},{"entidad":"CMAC Piura","valor":8.18},{"entidad":"CMAC Arequipa","valor":5.47},{"entidad":"CMAC Ica","valor":4.98},{"entidad":"CMAC Cusco","valor":4.76},{"entidad":"CMAC Huancayo","valor":4.63},{"entidad":"CMCP Lima","valor":4.51}],"total":{"entidad":"TOTAL CM","valor":5.98},"subtotales":[{"entidad":"TOTAL CMAC","valor":6}]}]}
```
</details>

**Claude:**

Revisé las series. Antes de redactar los marcadores, miro cómo el script resuelve campos anidados (SBS) y qué hace con el texto escrito.

**Herramienta:** `Bash`

```json
{
 "command": "cd ~/Documents/GitHub/agente-socioeconomico-peru/.claude/skills/informando-peru && ls -R . | head; wc -l scripts/armar_informe.py; grep -n \"def \\|regex\\|re.compile\\|escrita a mano\\|\\[\\]\" scripts/armar_informe.py | head -80",
 "description": "Inspeccionar el script de armado"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
.:
SKILL.md
plantilla.md
scripts

./scripts:
__pycache__
armar_informe.py
referencias_apa.py

415 scripts/armar_informe.py
11:    {{lit:0.1 puntos}}                    una constante metodológica escrita a mano, declarada como tal
42:MARCADOR = re.compile(r"\{\{\s*(.+?)\s*\}\}")
43:LLAMADA = re.compile(r"^(\w+)\.(\w+)\((.*)\)((?:\.\w+|\[-?\d+\])*)$")
44:CIFRA_SUELTA = re.compile(
51:def formatear(valor, decimales):
59:def separar_decimales(texto):
65:def campo(dato, ruta):
71:def argumentos(texto):
73:    pares = [p for p in re.split(r",(?![^\[]*\])", texto) if p.strip()]
77:def tipar(args, esquema):
83:def cliente(servidor):
95:async def llamar_todo(llamadas):
114:def fuente_de(resultado, servidor):
123:COPIA_GUARDADA = re.compile(r"copia guardada el (\d{4}-\d{2}-\d{2})")
124:MODULOS = re.compile(r"m[oó]dulos?\s+(\d+(?:\s*(?:,|y)\s*\d+)*)", re.I)
127:def registrar_fuentes(fuentes, servidor, herramienta, resultado, hoy):
150:def registrar_enaho(fuentes, fila, expr):
154:    modulos = re.findall(r"\d+", m.group(1)) if (m := MODULOS.search(texto)) else []
161:def resolver(borrador, permitir_faltantes):
166:def resolver_con_fuentes(borrador, permitir_faltantes, hoy=None):
179:    reemp
… [745 caracteres omitidos]
```
</details>

**Herramienta:** `Read`

```json
{
 "file_path": "~\\Documents\\GitHub\\agente-socioeconomico-peru\\.claude\\skills\\informando-peru\\scripts\\armar_informe.py",
 "offset": 1,
 "limit": 120
}
```

<details><summary>Resultado de la herramienta</summary>

```text
1	"""Arma el informe final desde un borrador con marcadores: ninguna cifra se escribe a mano.
2	
3	    uv run .claude/skills/informando-peru/scripts/armar_informe.py [--borrador B] [--salida S] [--permitir-faltantes]
4	
5	Marcadores que reemplaza:
6	    {{enaho.pobreza_nacional}}            el valor de salidas/indicadores.csv (año 2024 por defecto)
7	    {{enaho.pobreza_nacional:2020}}       el valor de salidas/indicadores.csv para el año especificado
8	    {{enaho.residentes_habituales|0}}     con 0 decimales (los enteros llevan separador de miles)
9	    {{bcrp.resumen(codigo=PN01273PM, desde=2024-01, hasta=2024-12).ultimo.valor|2}}
10	    {{sbs.indicadores(...).campo[0].otro}} cualquier herramienta de un servidor de .mcp.json, y un campo de su respuesta
11	    {{lit:0.1 puntos}}                    una constante metodológica escrita a mano, declarada como tal
12	
13	Cada valor sale de llamar de nuevo a la herramienta (el servidor del BCRP corre en proceso, el resto como los lanza
14	Claude Code desde .mcp.json). El script falla si queda un marcador sin resolver, si una figura citada no existe o si
15	la narrativa trae una cifra suelta: porcentajes, decimales o números de 3 o más d
… [5075 caracteres omitidos]
```
</details>

**Herramienta:** `Read`

```json
{
 "file_path": "~\\Documents\\GitHub\\agente-socioeconomico-peru\\.claude\\skills\\informando-peru\\scripts\\armar_informe.py",
 "offset": 160,
 "limit": 90
}
```

<details><summary>Resultado de la herramienta</summary>

```text
160	
161	def resolver(borrador, permitir_faltantes):
162	    """(reemplazos, traza, faltantes, constantes): traza son tuplas (cifra, origen, fuente)."""
163	    return resolver_con_fuentes(borrador, permitir_faltantes)[:4]
164	
165	
166	def resolver_con_fuentes(borrador, permitir_faltantes, hoy=None):
167	    """Como resolver, más los metadatos de cada fuente consultada para armar las referencias. `hoy` es la fecha de
168	    recuperación de lo que se consulta en esta corrida."""
169	    hoy = hoy or date.today()
170	    fuentes = {}
171	    indicadores = pd.read_csv(INDICADORES) if INDICADORES.is_file() else None
172	    marcadores = [(m.group(0), *separar_decimales(m.group(1))) for m in MARCADOR.finditer(borrador)]
173	    llamadas = {}
174	    for _, expr, _ in marcadores:
175	        if (m := LLAMADA.match(expr)) and m.group(1) != "enaho":
176	            llamadas[(m.group(1), m.group(2), json.dumps(argumentos(m.group(3)), sort_keys=True))] = None
177	    resultados = asyncio.run(llamar_todo(llamadas)) if llamadas else {}
178	
179	    reemplazos, traza, faltantes, constantes = {}, [], [], []
180	    for texto, expr, decimales in marcadores:
181	        if texto in reemplazos:
1
… [3581 caracteres omitidos]
```
</details>

**Herramienta:** `Bash`

```json
{
 "command": "cd ~/Documents/GitHub/agente-socioeconomico-peru && head -3 salidas/indicadores.csv; cut -d, -f1 salidas/indicadores.csv | sort -u | tr '\\n' ' '; echo; grep -c sbs .mcp.json; cat informes/verificacion.md | head -20; ls evaluacion | head",
 "description": "Ver ids de indicadores ENAHO"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
anio,id,indicador,grupo,valor,unidad,ponderador,n_muestral,fuente
2020,pobreza_nacional,Pobreza monetaria,Nacional,30.1332,% de personas,factor07 × mieperho (por hogar),34490,"INEI, ENAHO 2020, módulos 34 y 02; limpiando-enaho/limpiar.py"
2020,pobreza_nacional_personas,Pobreza monetaria,Nacional,30.01,% de personas,facpob07 (por persona),118810,"INEI, ENAHO 2020, módulos 34 y 02; limpiando-enaho/limpiar.py"
2020 2021 2022 2023 2024 anio 
2
# Verificación manual de cifras del informe

Cuatro afirmaciones numéricas de [`informe_final.md`](informe_final.md) comprobadas a mano en la fuente oficial, sin usar el agente, el servidor MCP ni los scripts del repositorio.

| # | Afirmación del informe | Valor en el informe | Fuente para comprobarla | Valor observado | ¿Coincide? | Diferencia |
|---|---|---|---|---|---|---|
| 1 | Inflación a 12 meses del IPC de Lima Metropolitana, diciembre de 2024 | 2.0 % | [BCRP, serie PN01273PM, dic. 2024](https://estadisticas.bcrp.gob.pe/estadisticas/series/mensuales/resultados/PN01273PM/html/2024-12/2024-12/) | _completar_ | _completar_ | _completar_ |
| 2 | Variación interanual del PBI en abril de 2020, el mínimo del periodo | −39.3 % | [BCRP, serie P
… [1503 caracteres omitidos]
```
</details>

**Herramienta:** `Bash`

```json
{
 "command": "awk -F, '$1==2024{print $2}' salidas/indicadores.csv | tr '\\n' ' '",
 "description": "Listar ids de indicadores 2024"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
This Bash command contains multiple operations. The following part requires approval: awk -F, '$1==2024{print $2}' salidas/indicadores.csv
```
</details>

**Herramienta:** `Grep`

```json
{
 "pattern": "^2024,",
 "path": "~\\Documents\\GitHub\\agente-socioeconomico-peru\\salidas\\indicadores.csv",
 "output_mode": "content",
 "-o": true,
 "head_limit": 0
}
```

<details><summary>Resultado de la herramienta</summary>

```text
178:2024,
179:2024,
180:2024,
181:2024,
182:2024,
183:2024,
184:2024,
185:2024,
186:2024,
187:2024,
188:2024,
189:2024,
190:2024,
191:2024,
192:2024,
193:2024,
194:2024,
195:2024,
196:2024,
197:2024,
198:2024,
199:2024,
200:2024,
201:2024,
202:2024,
203:2024,
204:2024,
205:2024,
206:2024,
207:2024,
208:2024,
209:2024,
210:2024,
211:2024,
212:2024,
213:2024,
214:2024,
215:2024,
216:2024,
217:2024,
218:2024,
219:2024,
220:2024,
221:2024,
```
</details>

**Herramienta:** `Grep`

```json
{
 "pattern": "^2024,[^,]+",
 "path": "~\\Documents\\GitHub\\agente-socioeconomico-peru\\salidas\\indicadores.csv",
 "output_mode": "content",
 "-o": true,
 "head_limit": 0,
 "-n": false
}
```

<details><summary>Resultado de la herramienta</summary>

```text
2024,pobreza_nacional
2024,pobreza_nacional_personas
2024,pobreza_extrema
2024,pobreza_area_urbana
2024,pobreza_area_rural
2024,pobreza_lima_metropolitana
2024,pobreza_lima_metropolitana_provincia
2024,pobreza_lima_provincias
2024,pobreza_dep_01
2024,pobreza_dep_02
2024,pobreza_dep_03
2024,pobreza_dep_04
2024,pobreza_dep_05
2024,pobreza_dep_06
2024,pobreza_dep_07
2024,pobreza_dep_08
2024,pobreza_dep_09
2024,pobreza_dep_10
2024,pobreza_dep_11
2024,pobreza_dep_12
2024,pobreza_dep_13
2024,pobreza_dep_14
2024,pobreza_dep_15
2024,pobreza_dep_16
2024,pobreza_dep_17
2024,pobreza_dep_18
2024,pobreza_dep_19
2024,pobreza_dep_20
2024,pobreza_dep_21
2024,pobreza_dep_22
2024,pobreza_dep_23
2024,pobreza_dep_24
2024,pobreza_dep_25
2024,pobreza_sexo_hombres
2024,pobreza_sexo_mujeres
2024,pobreza_edad_0_14
2024,pobreza_edad_15_29
2024,pobreza_edad_30_44
2024,pobreza_edad_45_59
2024,pobreza_edad_60_mas
2024,residentes_habituales
2024,hogares
2024,poblacion_expandida
2024,departamentos
```
</details>

**Herramienta:** `Write`

```json
{
 "file_path": "~\\Documents\\GitHub\\agente-socioeconomico-peru\\informes\\plan_analisis.md",
 "content": "# Plan de análisis\n\n**Pregunta.** ¿Cómo evolucionaron la inflación, la actividad económica, la morosidad bancaria y la pobreza monetaria del Perú entre 2020 y 2024, y qué brechas territoriales y urbano-rurales presentaba la pobreza en 2024?\n\n## Fuentes e indicadores\n\n| Dimensión | Fuente | Serie o indicador | Argumentos |\n|---|---|---|---|\n| Inflación | BCRP | `PN01273PM` (IPC Lima Metropolitana, var. % 12 meses) | 2020-01 a 2024-12 |\n| Actividad | BCRP | `PN01728AM` (PBI, var.
… [1226 caracteres omitidos]
```

<details><summary>Resultado de la herramienta</summary>

```text
File created successfully at: ~\Documents\GitHub\agente-socioeconomico-peru\informes\plan_analisis.md (file state is current in your context — no need to Read it back)
```
</details>

**Herramienta:** `mcp__bcrp__graficar_serie`

```json
{
 "codigo": "PM04923AA",
 "desde": "2020",
 "hasta": "2024",
 "titulo": "El PBI cayó en 2020, rebotó en 2021 y se desaceleró hasta 2023 antes de recuperarse en 2024"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
{"archivo":"figuras/bcrp_PM04923AA_2020_2024.png","codigo":"PM04923AA","nombre":"Producto bruto interno por tipo de gasto (variaciones porcentuales reales) - PBI","periodo":"2020 a 2024","n":5,"primero":{"periodo":"2020","valor":-10.9333064926168},"ultimo":{"periodo":"2024","valor":3.5152749172251},"fuente":"https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PM04923AA/json/2020/2024"}
```
</details>

**Claude:**

Escribí un título de gráfico sobre 2022-2023 sin haber visto esos años. Lo compruebo con los datos.

**Herramienta:** `mcp__bcrp__serie`

```json
{
 "codigo": "PM04923AA",
 "desde": "2020",
 "hasta": "2024"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
{"codigo":"PM04923AA","nombre":"Producto bruto interno por tipo de gasto (variaciones porcentuales reales) - PBI","frecuencia":"Anual","datos":[{"periodo":"2020","valor":-10.9333064926168},{"periodo":"2021","valor":13.4166455992199},{"periodo":"2022","valor":2.81819976987154},{"periodo":"2023","valor":-0.350699813229653},{"periodo":"2024","valor":3.5152749172251}],"fuente":"https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PM04923AA/json/2020/2024"}
```
</details>

**Claude:**

El título se sostiene: 2023 fue levemente negativo. Redacto el borrador, con cada cifra como marcador.

**Herramienta:** `Write`

```json
{
 "file_path": "~\\Documents\\GitHub\\agente-socioeconomico-peru\\informes\\borrador.md",
 "content": "# Inflación, actividad, morosidad y pobreza en el Perú, 2020-2024\n\n## 1. Pregunta de investigación\n\n¿Cómo evolucionaron la inflación, la actividad económica, la morosidad bancaria y la pobreza monetaria del Perú entre 2020 y 2024, y qué brechas territoriales y urbano-rurales presentaba la pobreza en 2024?\n\nEl informe cubre enero de 2020 a diciembre de 2024 en las series mensuales (BCRP) y los cierres de diciembre de cada año (SBS); la pobreza proviene de la ENAHO anual de 2020 a 2024 y
… [8824 caracteres omitidos]
```

<details><summary>Resultado de la herramienta</summary>

```text
File created successfully at: ~\Documents\GitHub\agente-socioeconomico-peru\informes\borrador.md (file state is current in your context — no need to Read it back)
```
</details>

**Claude:**

Dejé dos marcadores provisionales y una frase sobre 2022 que no encaja con los datos (la pobreza subió en 2022). Corrijo las tres.

**Herramienta:** `Edit`

```json
{
 "replace_all": false,
 "file_path": "~\\Documents\\GitHub\\agente-socioeconomico-peru\\informes\\borrador.md",
 "old_string": "la rural, {{enaho.pobreza_rural_placeholder}}.",
 "new_string": "la rural, {{enaho.pobreza_area_rural:2020}} % en 2020 y {{enaho.pobreza_area_rural:2024}} % en 2024 (`pobreza_area_urbana`, `pobreza_area_rural`). Lima Metropolitana pasó de {{enaho.pobreza_lima_metropolitana_provincia:2020}} % en 2020 a {{enaho.pobreza_lima_metropolitana_provincia:2024}} % en 2024."
}
```

<details><summary>Resultado de la herramienta</summary>

```text
The file ~\Documents\GitHub\agente-socioeconomico-peru\informes\borrador.md has been updated successfully. (file state is current in your context — no need to Read it back)
```
</details>

**Herramienta:** `Edit`

```json
{
 "replace_all": false,
 "file_path": "~\\Documents\\GitHub\\agente-socioeconomico-peru\\informes\\borrador.md",
 "old_string": "`pobreza_area_urbana`), una brecha de {{enaho.brecha_placeholder}}. Entre",
 "new_string": "`pobreza_area_urbana`), es decir, el campo supera a la ciudad. Entre"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
The file ~\Documents\GitHub\agente-socioeconomico-peru\informes\borrador.md has been updated successfully. (file state is current in your context — no need to Read it back)
```
</details>

**Herramienta:** `Edit`

```json
{
 "replace_all": false,
 "file_path": "~\\Documents\\GitHub\\agente-socioeconomico-peru\\informes\\borrador.md",
 "old_string": "La inflación subió en 2022 y volvió cerca de la meta en 2024, mientras la pobreza cayó en 2021, se mantuvo alta en 2022 y volvió a subir en 2023; la morosidad bancaria se movió en un rango estrecho.",
 "new_string": "La inflación subió hasta mediados de 2022 y bajó después, mientras la pobreza cayó en 2021, subió en 2022 y 2023 y bajó en 2024; la morosidad bancaria se movió en un rango estrecho."
}
```

<details><summary>Resultado de la herramienta</summary>

```text
The file ~\Documents\GitHub\agente-socioeconomico-peru\informes\borrador.md has been updated successfully. (file state is current in your context — no need to Read it back)
```
</details>

**Herramienta:** `Bash`

```json
{
 "command": "uv run ~/Documents/GitHub/agente-socioeconomico-peru/.claude/skills/informando-peru/scripts/armar_informe.py 2>&1 | tail -30",
 "description": "Armar el informe final",
 "timeout": 300000
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
… [499 caracteres omitidos]
```
</details>

**Claude:**

Es el umbral del INEI (CV mayor que 15 %), una constante metodológica: va como `lit`.

**Herramienta:** `Edit`

```json
{
 "replace_all": false,
 "file_path": "~\\Documents\\GitHub\\agente-socioeconomico-peru\\informes\\borrador.md",
 "old_string": "mayor que 15 %)",
 "new_string": "mayor que {{lit:15 %}})"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
The file ~\Documents\GitHub\agente-socioeconomico-peru\informes\borrador.md has been updated successfully. (file state is current in your context — no need to Read it back)
```
</details>

**Herramienta:** `Bash`

```json
{
 "command": "uv run ~/Documents/GitHub/agente-socioeconomico-peru/.claude/skills/informando-peru/scripts/armar_informe.py 2>&1 | tail -8",
 "description": "Rearmar el informe final",
 "timeout": 300000
}
```

<details><summary>Resultado de la herramienta</summary>

```text
|                 \U0001f680 Deploy free: https://horizon.prefect.io                  |
|                                                                             |
+-----------------------------------------------------------------------------+


[11/07/26 09:58:00] INFO     Starting MCP server 'sbs' with    transport.py:241
                             transport 'stdio'                                 
informe_final.md: 50 cifras resueltas y trazadas.
```
</details>

**Claude:**

Informe armado con 50 cifras trazadas. Ahora la verificación de consistencia.

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

**Herramienta:** `Read`

```json
{
 "file_path": "~\\Documents\\GitHub\\agente-socioeconomico-peru\\informes\\informe_final.md",
 "limit": 40
}
```

<details><summary>Resultado de la herramienta</summary>

```text
1	# Inflación, actividad, morosidad y pobreza en el Perú, 2020-2024
2	
3	## 1. Pregunta de investigación
4	
5	¿Cómo evolucionaron la inflación, la actividad económica, la morosidad bancaria y la pobreza monetaria del Perú entre 2020 y 2024, y qué brechas territoriales y urbano-rurales presentaba la pobreza en 2024?
6	
7	El informe cubre enero de 2020 a diciembre de 2024 en las series mensuales (BCRP) y los cierres de diciembre de cada año (SBS); la pobreza proviene de la ENAHO anual de 2020 a 2024 y su foto territorial es la de 2024. La inflación es la de Lima Metropolitana, no nacional. No se pretende demostrar relaciones causales entre indicadores: se comparan series de distinto nivel de agregación y frecuencia.
8	
9	## 2. Fuentes y metodología
10	
11	- **BCRP** (servidor MCP `bcrp`): inflación `PN01273PM` (IPC de Lima Metropolitana, variación porcentual en 12 meses), actividad `PN01728AM` (PBI, variación porcentual interanual mensual) y `PM04923AA` (PBI real, variación porcentual anual), y morosidad neta `PN07746EM` (cartera atrasada neta sobre colocaciones netas de las empresas bancarias), todas de 2020 a 2024.
12	- **SBS** (servidor MCP `sbs`): boletín `B-2401`, indicador «Cré
… [3437 caracteres omitidos]
```
</details>

**Herramienta:** `Bash`

```json
{
 "command": "uv run ~/Documents/GitHub/agente-socioeconomico-peru/.claude/skills/verificando-consistencia/scripts/verificar.py 2>&1 | tail -15; echo ----; cat salidas/consistencia.md",
 "description": "Verificar consistencia entre herramientas",
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


[11/07/26 09:58:34] INFO     Starting MCP server 'sbs' with    transport.py:241
                             transport 'stdio'                                 
salidas/consistencia.md: DIFERENCIA 1, OK 8
----
# Consistencia entre herramientas

Generado por `verificando-consistencia/scripts/verificar.py`. DIFERENCIA: 1, OK: 8.

| Fuente | Verificación | Resulta
… [2145 caracteres omitidos]
```
</details>

**Claude:**

La verificación pasó sin fallas. La skill pide mencionar su resultado en el informe, así que lo agrego, rearmo y reverifico.

**Herramienta:** `Edit`

```json
{
 "replace_all": false,
 "file_path": "~\\Documents\\GitHub\\agente-socioeconomico-peru\\informes\\borrador.md",
 "old_string": "- No se estima ninguna relación causal.",
 "new_string": "- No se estima ninguna relación causal.\n- **Verificación de consistencia** (`salidas/consistencia.md`): no hubo fallas. Todas las comprobaciones de la ENAHO, del IPC y de las cifras de este informe resultaron OK. La única DIFERENCIA esperada es la morosidad de diciembre de cada año: el BCRP (`PN07746EM`, neta) y la SBS (`B-2401`, bruta) difieren en como máximo {{lit:0.05 puntos}} porque miden cosas distintas
… [4 caracteres omitidos]
```

<details><summary>Resultado de la herramienta</summary>

```text
The file ~\Documents\GitHub\agente-socioeconomico-peru\informes\borrador.md has been updated successfully. (file state is current in your context — no need to Read it back)
```
</details>

**Herramienta:** `Bash`

```json
{
 "command": "uv run ~/Documents/GitHub/agente-socioeconomico-peru/.claude/skills/informando-peru/scripts/armar_informe.py 2>&1 | tail -2; uv run ~/Documents/GitHub/agente-socioeconomico-peru/.claude/skills/verificando-consistencia/scripts/verificar.py 2>&1 | tail -1",
 "description": "Rearmar informe y reverificar",
 "timeout": 600000
}
```

<details><summary>Resultado de la herramienta</summary>

```text
                             transport 'stdio'                                 
informe_final.md: 50 cifras resueltas y trazadas.
salidas/consistencia.md: DIFERENCIA 1, OK 8
```
</details>

**Claude:**

El informe está en `informes/informe_final.md`. Tiene 50 cifras, todas resueltas desde las herramientas, y cada una con su fuente en la tabla de trazabilidad.

## Hallazgos

1. **Inflación y actividad (BCRP).** La inflación a 12 meses (`PN01273PM`, IPC de Lima Metropolitana) fue 1.9 % en enero de 2020 y llegó a su máximo de 8.8 % en junio de 2022. Cerró 2024 en 2.0 %.
   - El PBI real (`PM04923AA`) creció −10.9 % en 2020, 13.4 % en 2021, 2.8 % en 2022, −0.4 % en 2023 y 3.5 % en 2024.
   - En la serie mensual (`PN01728AM`) el mínimo fue −39.3 % en abril de 2020. El máximo fue 59.9 % en abril de 2021, un rebote sobre una base muy baja.
2. **Morosidad bancaria.** La morosidad neta del BCRP (`PN07746EM`) fue 3.1 % en enero de 2020. Tocó su máximo de 4.6 % en mayo de 2024 y cerró 2024 en 3.8 %.
   - La SBS (`B-2401`, créditos atrasados sobre créditos directos) da, al cierre de cada diciembre de 2020 a 2024: 3.80 %, 3.77 %, 3.95 %, 4.31 % y 3.75 %.
   - Para dar contexto, las cajas municipales (`C-1301`) cerraron 2024 con 5.98 %.
3. **Pobreza monetaria (ENAHO).** La pobreza nacional fue 30.1 % en 2020, 25.9 % en 2021, 27.5 % en 2022, 29.0 % en 2023 y 27.6 % en 2024.
   - En 2024 la pobreza rural fue 39.3 % y la urbana 24.8 %.
   - Cajamarca (45.0 %) y Loreto (43.0 %) tuvieron las cifras más altas, y Ica (6.0 %) la más baja. Ica es una cifra referencial del INEI.
   - Lima Metropolitana tuvo 27.6 % y Lima provincias 21.7 %.

## Verificación

La verificación no encontró fallas. El resultado es 8 comprobaciones OK y 1 DIFERENCIA, que era esperable. Esa diferencia es la morosidad de los diciembres: la serie del BCRP es neta y la de la SBS es bruta, y difieren en 0.05 puntos como máximo. La limpieza de la ENAHO pasó sus 135 validaciones contra el INEI sin fallas.

## Limitaciones

- La inflación es solo la de Lima Metropolitana.
- Las cifras departamentales de la ENAHO tienen intervalos de confianza amplios.
- El INEI no publica una cifra para el departamento de Lima en conjunto. El mapa departamental muestra un cálculo propio con los microdatos, y el análisis usa Lima desagregada.
- Las relaciones entre indicadores se describen como asociaciones, no como causas. Por ejemplo, la correlación mensual entre inflación y morosidad neta es débil (0.24).

## Archivos y estado del repo

Las figuras están en `figuras/`, incluidos los gráficos del BCRP, y los dos mapas en `mapas/`. El plan y el borrador con los marcadores están en `informes/`, y la verificación en `salidas/consistencia.md`.

Regeneré `salidas/indicadores.csv`, las figuras y los mapas porque estaban borrados en tu árbol de trabajo. Nada de esto está commiteado. El script de armado advierte que un informe para entregar debe armarse sobre un árbol commiteado, así que conviene hacer commit y volver a armarlo. No toqué `informes/verificacion.md`, que ya existía y sigue con sus campos `_completar_`.

---

**Resultado final** · turnos: 63 · costo USD: 0.6997938 · duración: 296.8 s
