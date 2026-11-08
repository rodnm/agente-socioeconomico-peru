# Subagente: exploración de las sesiones 04 y 16 del curso (solo lectura)

## Línea de tiempo

Servidores MCP: ninguno · Skills: ninguno · 16 llamadas a herramientas

1. Bash `ls -la "~/Documents/GitHub/Data-Science-Python/sessions/04-mcp-claude-code/" "~/Documents/`
2. Bash `gh api repos/d2cml-ai/Data-Science-Python/contents/sessions/16-skills-enaho --jq '.[] | .p`
3. `Read`
4. `Read`
5. `Read`
6. `Read`
7. `Read`
8. `Read`
9. `Read`
10. `Read`
11. Bash `gh api repos/d2cml-ai/Data-Science-Python/contents/sessions/16-skills-enaho/README.md --jq`
12. Bash `gh api repos/d2cml-ai/Data-Science-Python/contents/sessions/16-skills-enaho/referencias/po`
13. `Grep`
14. Bash `cat "~/Documents/GitHub/Data-Science-Python/sessions/04-mcp-claude-code/.gitignore" "~/Doc`
15. `Glob`
16. Bash `cd "~/Documents/GitHub/enaho-skills" 2>/dev/null && { find . -path ./.venv -prune -o -path`

## 1. Pedido · 2026-11-02 07:25:05 UTC

Read-only exploration. Goal: give me a compact map (≤2k tokens, with path:line evidence) of two course reference sessions that a homework project must build on. Search breadth: medium.

1. Local clone: ~\Documents\GitHub\Data-Science-Python\sessions\04-mcp-claude-code\ (README.md, mcps_mas_usados.md, proyecto/server.py, proyecto/test_server.py, proyecto/evaluar.py, proyecto/preguntas.csv, proyecto/pyproject.toml, proyecto/README.md). Report:
   - Every MCP tool/resource/prompt defined in server.py: name, signature, what it does, which BCRP API endpoint/URL it calls, how it parses responses, error handling. Note which functions are stubs/TODO that the student must "complete".
   - The 8 tests in test_server.py: name, what each asserts, how they import from server (module path), whether they hit the network or mock. This matters because the homework says the 8 original tests must pass unmodified except for import paths when files move to `mcp/server.py` + `mcp/test_server.py`.
   - evaluar.py + preguntas.csv: how the evaluation harness works (columns, how it runs Claude Code with/without MCP, timing, scoring). This will be reused for a "Mode A vs Mode B" experiment.
   - pyproject.toml deps and python version; FastMCP version.
2. Session 16 is NOT in the local clone; read it remotely with `gh api repos/d2cml-ai/Data-Science-Python/contents/sessions/16-skills-enaho/README.md --jq .content | base64 -d` and `gh api repos/d2cml-ai/Data-Science-Python/contents/sessions/16-skills-enaho/referencias/pobreza_departamento_2024.csv --jq .content | base64 -d`. Report: the three skills it describes (limpiando-enaho, graficando-enaho, mapeando-enaho), the exact ENAHO processing rules (dtype handling for keys, residente habitual filter, merge validate, weights: factor07 vs facpob07 etc., poverty variable and how it's coded), expected validation numbers, SKILL.md structure/frontmatter conventions it teaches, how skills chain (graph/map skill calling cleaning skill), the reference CSV columns and the GeoJSON source/key fields (FIRST_IDDP).

Return concise bullets. Do not dump whole files. Do not modify anything.

Close your final response with a `## Key Learnings` block of 1–5 numbered items, each a standalone factual sentence of at least 20 characters and at least 4 words (omit if none).

**Claude:**

I'll start by listing the local session directory and fetching the remote session 16 files in parallel.

**Herramienta:** `Bash`

```json
{
 "command": "ls -la \"~/Documents/GitHub/Data-Science-Python/sessions/04-mcp-claude-code/\" \"~/Documents/GitHub/Data-Science-Python/sessions/04-mcp-claude-code/proyecto/\"; wc -l \"~/Documents/GitHub/Data-Science-Python/sessions/04-mcp-claude-code/\"*.md \"~/Documents/GitHub/Data-Science-Python/sessions/04-mcp-claude-code/proyecto/\"*",
 "description": "List session 04 files and line counts"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
~/Documents/GitHub/Data-Science-Python/sessions/04-mcp-claude-code/:
total 25
drwxr-xr-x 1 [USUARIO] 197121    0 Oct 28 20:53 .
drwxr-xr-x 1 [USUARIO] 197121    0 Oct 28 20:53 ..
-rw-r--r-- 1 [USUARIO] 197121   11 Oct 28 20:53 .gitignore
-rw-r--r-- 1 [USUARIO] 197121 1783 Oct 28 20:53 README.md
-rw-r--r-- 1 [USUARIO] 197121 4680 Oct 28 20:53 mcps_mas_usados.md
drwxr-xr-x 1 [USUARIO] 197121    0 Oct 28 20:53 proyecto

~/Documents/GitHub/Data-Science-Python/sessions/04-mcp-claude-code/proyecto/:
total 374
drwxr-xr-x 1 [USUARIO] 197121      0 Oct 28 20:53 .
drwxr-xr-x 1 [USUARIO] 197121      0 Oct 28 20:53 ..
-rw-r--r-- 1 [USUARIO] 197121     56 Oct 28 20:53 .gitignore
-rw-r--r-- 1 [USUARIO] 197121   7759 Oct 28 20:53 README.md
-rw-r--r-- 1 [USUARIO] 197121   3793 Oct 28 20:53 evaluar.py
-rw-r--r-- 1 [USUARIO] 197121   1223 Oct 28 20:53 preguntas.csv
-rw-r--r-- 1 [USUARIO] 197121    235 Oct 28 20:53 pyproject.toml
-rw-r--r-- 1 [USUARIO] 197121   5612 Oct 28 20:53 server.py
-rw-r--r-- 1 [USUARIO] 197121   2526 Oct 28 20:53 test_server.py
-rw-r--r-- 1 [USUARIO] 197121 340825 Oct 28 20:53 uv.lock
    37 ~/Documents/GitHub/Data-Science-Python/sessions/04-mcp-claude-code/README.md
    76 ~/Documents/GitHub/Data-Science-P
… [813 caracteres omitidos]
```
</details>

**Herramienta:** `Bash`

```json
{
 "command": "gh api repos/d2cml-ai/Data-Science-Python/contents/sessions/16-skills-enaho --jq '.[] | .path + \" \" + .type'; gh api repos/d2cml-ai/Data-Science-Python/contents/sessions/16-skills-enaho/referencias --jq '.[] | .path + \" \" + .type'",
 "description": "List remote session 16 directory contents"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
sessions/16-skills-enaho/README.md file
sessions/16-skills-enaho/referencias dir
sessions/16-skills-enaho/referencias/mapa_pobreza_2024.png file
sessions/16-skills-enaho/referencias/pobreza_departamento_2024.csv file
```
</details>

**Claude:**

Now reading the local files in parallel.

**Herramienta:** `Read`

```json
{
 "file_path": "~\\Documents\\GitHub\\Data-Science-Python\\sessions\\04-mcp-claude-code\\proyecto\\server.py"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
1	"""Servidor MCP del BCRP. Empiecen aquí: buscar_series ya funciona; completen los TODO hasta que pasen las pruebas.
2	
3	    uv run pytest                                           # el contrato: las 8 pruebas deben pasar
4	    uv run server.py                                        # el servidor, por stdio
5	    claude mcp add --scope project bcrp -- uv run server.py # conectarlo a Claude Code
6	
7	Las cuentas las hace Python, no el modelo: así cada cifra sale de una llamada que se puede repetir.
8	"""
9	import re
10	import unicodedata
11	from functools import cache
12	from pathlib import Path
13	
14	import httpx
15	import pandas as pd
16	from fastmcp import FastMCP
17	from fastmcp.exceptions import ToolError
18	
19	AQUI = Path(__file__).parent
20	CATALOGO = AQUI / "datos" / "catalogo_bcrp.csv"
21	URL_CATALOGO = "https://estadisticas.bcrp.gob.pe/estadisticas/series/metadata"
22	API = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"
23	SOLO_LECTURA = {"readOnlyHint": True, "openWorldHint": True}
24	
25	mcp = FastMCP("bcrp", instructions=(
26	    "Series oficiales del Banco Central de Reserva del Perú (BCRP). Primero busca el código con buscar_series; "
27	    "luego usa
… [4599 caracteres omitidos]
```
</details>

**Herramienta:** `Read`

```json
{
 "file_path": "~\\Documents\\GitHub\\Data-Science-Python\\sessions\\04-mcp-claude-code\\proyecto\\test_server.py"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
1	"""El contrato del servidor: si estas pruebas pasan, Claude Code y evaluar.py pueden usarlo.
2	
3	    uv run pytest -q
4	
5	Llaman al servidor en memoria, igual que lo haría Claude Code, y piden datos reales al BCRP.
6	"""
7	import asyncio
8	
9	import pytest
10	from fastmcp import Client
11	from fastmcp.exceptions import ToolError
12	
13	from server import mcp
14	
15	
16	async def _con_cliente(f):
17	    async with Client(mcp) as c:
18	        return await f(c)
19	
20	
21	def llamar(herramienta, **args):
22	    return asyncio.run(_con_cliente(lambda c: c.call_tool(herramienta, args))).data
23	
24	
25	def test_buscar_encuentra_el_ipc():
26	    r = llamar("buscar_series", texto="ipc 12 meses", limite=5)
27	    assert "PN01273PM" in [x["codigo"] for x in r]
28	    assert {"codigo", "nombre", "frecuencia"} <= r[0].keys()
29	
30	
31	def test_cuatro_herramientas_como_minimo():
32	    nombres = {t.name for t in asyncio.run(_con_cliente(lambda c: c.list_tools()))}
33	    assert {"buscar_series", "serie", "resumen"} <= nombres
34	    assert len(nombres) >= 4, "falta su herramienta propia"
35	
36	
37	def test_serie_mensual():
38	    r = llamar("serie", codigo="PN01271PM", desde="2025-01", 
… [1461 caracteres omitidos]
```
</details>

**Herramienta:** `Read`

```json
{
 "file_path": "~\\Documents\\GitHub\\Data-Science-Python\\sessions\\04-mcp-claude-code\\proyecto\\evaluar.py"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
1	"""¿Inventa cifras Claude? Las mismas preguntas sin herramientas y con su MCP, contra la cifra oficial.
2	
3	    uv run evaluar.py                                   # memoria y mcp, con Haiku
4	    uv run evaluar.py --modos memoria mcp web --modelo sonnet
5	
6	Cada pregunta se le hace a Claude Code en modo no interactivo (claude -p) y debe responder un JSON con el valor.
7	Escribe resultados.csv y cuenta cuántas acierta, cuántas se equivoca y en cuántas reconoce que no sabe.
8	"""
9	import argparse
10	import json
11	import subprocess
12	import time
13	from concurrent.futures import ThreadPoolExecutor
14	from pathlib import Path
15	
16	import pandas as pd
17	
18	AQUI = Path(__file__).parent
19	ESQUEMA = {"type": "object", "required": ["valor", "fuente"],
20	           "properties": {"valor": {"type": ["number", "null"]}, "unidad": {"type": "string"},
21	                          "fuente": {"type": "string"}}}
22	INSTRUCCION = ("Responde con un solo número en «valor», en la unidad que pide la pregunta. Si no puedes saberlo "
23	               "con certeza, pon valor null: no estimes. En «fuente» di de dónde sale la cifra.\n\n")
24	MODOS = {   # todas sin las herramientas de archivo
… [2727 caracteres omitidos]
```
</details>

**Herramienta:** `Read`

```json
{
 "file_path": "~\\Documents\\GitHub\\Data-Science-Python\\sessions\\04-mcp-claude-code\\proyecto\\preguntas.csv"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
1	id,pregunta,verdad,tolerancia,serie,periodo
2	ipc_set26,"¿Cuál fue la inflación interanual (variación del IPC en 12 meses) de Lima Metropolitana en setiembre de 2026, en %?",4.5487,0.05,PN01273PM,2026-09
3	ipc_dic25,"¿Cuál fue la inflación interanual (variación del IPC en 12 meses) de Lima Metropolitana en diciembre de 2025, en %?",1.5088,0.05,PN01273PM,2025-12
4	ipc_mar25,"¿Cuál fue la variación mensual del IPC de Lima Metropolitana en marzo de 2025, en %?",0.8102,0.02,PN01271PM,2025-03
5	referencia_set26,"¿Cuál era la tasa de referencia de la política monetaria del BCRP en setiembre de 2026, en %?",4.25,0.01,PD04722MM,2026-09
6	tc_15oct26,"¿Cuál fue el tipo de cambio interbancario venta del 15 de octubre de 2026 según el BCRP, en soles por dólar?",3.4282,0.002,PD04638PD,2026-10-15
7	rin_ago26,"¿A cuánto ascendían las reservas internacionales netas del BCRP a fines de agosto de 2026, en millones de US$?",96517.9,100,PN00027MM,2026-08
8	cobre_ago26,"¿Cuál fue el precio promedio del cobre en agosto de 2026 según el BCRP, en centavos de US$ por libra?",689.70,3.5,PN38784BM,2026-08
9	pbi_2025,"¿Cuánto creció el PBI real del Perú en 2025 según el BCRP, en %?",3.4306,0.05,PM04923AA,20
… [6 caracteres omitidos]
```
</details>

**Herramienta:** `Read`

```json
{
 "file_path": "~\\Documents\\GitHub\\Data-Science-Python\\sessions\\04-mcp-claude-code\\proyecto\\pyproject.toml"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
1	[project]
2	name = "mcp-bcrp"
3	version = "0.1.0"
4	description = "Servidor MCP con las series oficiales del BCRP"
5	requires-python = ">=3.11"
6	dependencies = ["fastmcp>=4,<5", "httpx", "pandas"]
7	
8	[dependency-groups]
9	dev = ["pytest"]
10	
```
</details>

**Herramienta:** `Read`

```json
{
 "file_path": "~\\Documents\\GitHub\\Data-Science-Python\\sessions\\04-mcp-claude-code\\proyecto\\README.md"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
1	# Proyecto · Un MCP con las series oficiales del BCRP
2	
3	En 1 h 40 min construyen un servidor MCP con FastMCP que busca entre las 17,167 series del Banco Central de Reserva
4	del Perú, las descarga y calcula variaciones. Después lo conectan a Claude Code y miden, con `claude -p`, cuántas cifras
5	acierta Claude sin su servidor y cuántas con él.
6	
7	| Archivo | Qué es |
8	|---|---|
9	| `server.py` | El servidor. `buscar_series` ya funciona; faltan los TODO 1 a 5 |
10	| `test_server.py` | El contrato: 8 pruebas con datos reales del BCRP. No lo cambien |
11	| `preguntas.csv` | 8 preguntas con la cifra oficial y la tolerancia; ustedes agregan 2 |
12	| `evaluar.py` | Le hace cada pregunta a Claude sin herramientas y con su MCP, y califica |
13	
14	Necesitan `uv`, Claude Code con su sesión iniciada e internet. Node solo hace falta para MCP Inspector, que es opcional.
15	
16	## Parte 0 · Preparar (10 min)
17	
18	```bash
19	git clone https://github.com/d2cml-ai/Data-Science-Python      # o git pull si ya lo tienen
20	cp -r Data-Science-Python/sessions/04-mcp-claude-code/proyecto mcp-bcrp
21	cd mcp-bcrp && git init
22	
23	uv run pytest -q                                               #
… [6796 caracteres omitidos]
```
</details>

**Herramienta:** `Read`

```json
{
 "file_path": "~\\Documents\\GitHub\\Data-Science-Python\\sessions\\04-mcp-claude-code\\README.md"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
1	# Sesión 04 · MCP: Claude conectado a sus datos
2	
3	Qué es el Model Context Protocol, qué servidores existen y en cuáles confiar, cómo se usan en Claude Code y cómo se
4	construye uno propio con FastMCP. Basada en el curso corto «MCP: Build Rich-Context AI Apps with Anthropic» de
5	DeepLearning.AI, llevado a Claude Code.
6	
7	**Slides de la clase:** https://claude.ai/artifact/B9W8izJCRr6qsTLwbMXqcT
8	
9	| Bloque | Duración | Qué se hace |
10	|---|---|---|
11	| Explicación y demo | 60 min | Arquitectura, primitivas y transportes; el catálogo de servidores; `claude mcp add` y sus alcances; seguridad; FastMCP |
12	| Proyecto | 1 h 40 min | Un MCP con las 17,167 series del BCRP, probado, conectado a Claude Code y evaluado con `claude -p` |
13	| Resultados | 20 min | Tres repositorios al azar: ¿cuántas cifras acertó Claude sin su MCP y cuántas con él? |
14	
15	## Contenido
16	
17	| Carpeta | Qué hay |
18	|---|---|
19	| [`proyecto/`](proyecto/) | El enunciado, el servidor inicial, las 8 pruebas, las preguntas y el script de evaluación |
20	| [`mcps_mas_usados.md`](mcps_mas_usados.md) | Los MCP con más estrellas y descargas, los que sirven para datos y cómo repetir la medición |
21	
22
… [626 caracteres omitidos]
```
</details>

**Herramienta:** `Read`

```json
{
 "file_path": "~\\Documents\\GitHub\\Data-Science-Python\\sessions\\04-mcp-claude-code\\mcps_mas_usados.md"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
1	# Los MCP más usados
2	
3	Medido el 28 de octubre de 2026. No hay un ranking oficial de uso, así que se miran dos cosas:
4	
5	- **Estrellas en GitHub**: miden interés, no uso.
6	- **Descargas de la última semana** en npm o PyPI: se acercan más al uso real, aunque están algo infladas porque
7	  `npx …@latest` vuelve a bajar el paquete en cada arranque y porque cuentan las corridas de CI.
8	
9	Quedan fuera las listas (`punkpeye/awesome-mcp-servers` tiene 97 mil estrellas) y las aplicaciones que solo traen un MCP
10	como extra. «—» quiere decir que no hay dato de npm ni de PyPI.
11	
12	## En general
13	
14	| Repositorio | Qué hace | ★ GitHub | Descargas/semana |
15	|---|---|---|---|
16	| `modelcontextprotocol/servers` | Los de referencia: Fetch, Filesystem, Git, Memory, Time | 91.6k | Filesystem 911k, Fetch 247k |
17	| `upstash/context7` | Documentación al día de librerías | 63.9k | 478k |
18	| `ChromeDevTools/chrome-devtools-mcp` | Depurar páginas en Chrome | 54.4k | 2.95 M |
19	| `DeusData/codebase-memory-mcp` | Índice local del código para agentes | 47.7k | — |
20	| `microsoft/playwright-mcp` | Un navegador que Claude maneja | 38.8k | **6.9 M** |
21	| `github/github-mcp-server` |
… [3567 caracteres omitidos]
```
</details>

**Claude:**

Now fetching the session 16 README and reference CSV, plus checking the locked FastMCP version.

**Herramienta:** `Bash`

```json
{
 "command": "gh api repos/d2cml-ai/Data-Science-Python/contents/sessions/16-skills-enaho/README.md --jq .content | base64 -d | cat -n",
 "description": "Fetch remote session 16 README with line numbers"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
     1	# Sesión 16 · Skills de Claude Code: limpiar, graficar y mapear la ENAHO
     2	
     3	Qué es una skill de Claude Code, por qué conviene crearla dentro del repositorio y cómo se arma una que limpie la ENAHO
     4	siempre de la misma forma. El proyecto son tres skills que trabajan juntas: una limpia los módulos del INEI, otra
     5	hace gráficos y otra hace un mapa por departamento.
     6	
     7	**Slides de la clase:** https://claude.ai/artifact/X7H6PUvaWKde1epsYCJNze
     8	
     9	| Bloque | Duración | Qué se hace |
    10	|---|---|---|
    11	| Clase | 30 min | Qué es una skill, cómo se carga y se activa, por qué en Claude Code, el pipeline de la ENAHO y sus trampas |
    12	| Proyecto | 45 min | Tres skills: `limpiando-enaho`, `graficando-enaho` y `mapeando-enaho`, validadas y probadas con y sin ellas |
    13	| Presentaciones | 15 min | Cuatro repositorios al azar, tres minutos cada uno |
    14	
    15	## Contenido
    16	
    17	| Archivo | Qué hay |
    18	|---|---|
    19	| [`referencias/pobreza_departamento_2024.csv`](referencias/pobreza_departamento_2024.csv) | La pobreza 2024 de los 25 departamentos, para validar el mapa |
    20	| [`referencias/mapa_pobreza_
… [11808 caracteres omitidos]
```
</details>

**Herramienta:** `Bash`

```json
{
 "command": "gh api repos/d2cml-ai/Data-Science-Python/contents/sessions/16-skills-enaho/referencias/pobreza_departamento_2024.csv --jq .content | base64 -d | cat -n",
 "description": "Fetch remote poverty reference CSV"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
     1	ccdd,departamento,pobreza_pct
     2	01,AMAZONAS,25.7
     3	02,ANCASH,22.8
     4	03,APURIMAC,24.0
     5	04,AREQUIPA,15.8
     6	05,AYACUCHO,32.8
     7	06,CAJAMARCA,45.0
     8	07,CALLAO,33.9
     9	08,CUSCO,18.5
    10	09,HUANCAVELICA,33.4
    11	10,HUANUCO,39.0
    12	11,ICA,6.0
    13	12,JUNIN,18.5
    14	13,LA LIBERTAD,30.2
    15	14,LAMBAYEQUE,14.0
    16	15,LIMA,27.1
    17	16,LORETO,43.0
    18	17,MADRE DE DIOS,11.1
    19	18,MOQUEGUA,11.0
    20	19,PASCO,39.0
    21	20,PIURA,31.9
    22	21,PUNO,39.9
    23	22,SAN MARTIN,22.0
    24	23,TACNA,24.0
    25	24,TUMBES,26.9
    26	25,UCAYALI,27.1
```
</details>

**Herramienta:** `Grep`

```json
{
 "pattern": "^name = \"(fastmcp|mcp|httpx|pandas|pytest)\"",
 "path": "~\\Documents\\GitHub\\Data-Science-Python\\sessions\\04-mcp-claude-code\\proyecto\\uv.lock",
 "output_mode": "content",
 "-A": 1
}
```

<details><summary>Resultado de la herramienta</summary>

```text
391:name = "fastmcp"
392-version = "4.1.4"
--
502:name = "httpx"
503-version = "0.28.1"
--
636:name = "mcp"
637-version = "2.3.0"
--
909:name = "pandas"
910-version = "3.1.0"
--
1238:name = "pytest"
1239-version = "9.2.0"
```
</details>

**Herramienta:** `Bash`

```json
{
 "command": "cat \"~/Documents/GitHub/Data-Science-Python/sessions/04-mcp-claude-code/.gitignore\" \"~/Documents/GitHub/Data-Science-Python/sessions/04-mcp-claude-code/proyecto/.gitignore\"; head -3 \"~/Documents/GitHub/Data-Science-Python/sessions/04-mcp-claude-code/proyecto/uv.lock\"",
 "description": "Show gitignore files and uv.lock header"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
solucion/
.venv/
datos/
__pycache__/
.pytest_cache/
salidas/
version = 1
revision = 3
requires-python = ">=3.11"
```
</details>

**Claude:**

Quick check on the related session 11 lab mentioned in the README, which pairs a BCRP MCP with a skill.

**Herramienta:** `Glob`

```json
{
 "pattern": "sessions/11-agentes/lab/Skills_Claude/**/*.{md,py,json,toml}",
 "path": "~\\Documents\\GitHub\\Data-Science-Python"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
No files found
```
</details>

**Claude:**

The environment lists an existing local `enaho-skills/` project with these skills. I'll do a quick check since it's directly relevant.

**Herramienta:** `Bash`

```json
{
 "command": "cd \"~/Documents/GitHub/enaho-skills\" 2>/dev/null && { find . -path ./.venv -prune -o -path ./.git -prune -o -path ./datos -prune -o -type f -print | head -50; git log --oneline -5 2>/dev/null; cat salidas/validacion.txt 2>/dev/null; }",
 "description": "List local enaho-skills project files and validation output"
}
```

<details><summary>Resultado de la herramienta</summary>

```text
./.claude/skills/descargando-enaho/scripts/descargar.py
./.claude/skills/descargando-enaho/SKILL.md
./.claude/skills/graficando-enaho/scripts/graficar.py
./.claude/skills/graficando-enaho/SKILL.md
./.claude/skills/limpiando-enaho/reference.md
./.claude/skills/limpiando-enaho/scripts/limpiar.py
./.claude/skills/limpiando-enaho/SKILL.md
./.claude/skills/mapeando-enaho/scripts/mapear.py
./.claude/skills/mapeando-enaho/SKILL.md
./.gitignore
./evaluacion.md
./figuras/pobreza_por_area.png
./figuras/pobreza_por_edad.png
./figuras/pobreza_por_sexo.png
./LICENSE
./mapas/pobreza_departamento.png
./pyproject.toml
./README.md
./referencias/mapa_pobreza_2024.png
./referencias/pobreza_departamento_2024.csv
./salidas/personas_2024.parquet
./salidas/validacion.txt
./uv.lock
c60027b Merge pull request #3 from rodnm/docs/evaluacion-y-readme
ac410b0 Merge pull request #2 from rodnm/feat/graficos-y-mapa
c48ab0c Merge pull request #1 from rodnm/feat/descarga-y-limpieza
2f4254d docs(enaho): record the evaluation and how to run the project
30819a8 feat(enaho): chart and map poverty with fixed rules
Validación de la ENAHO 2024 contra las cifras de la sesión y del INEI

OK    Hogares en la sumaria: 33,69
… [2499 caracteres omitidos]
```
</details>

**Claude:**

# Map of the two reference sessions (04 MCP-BCRP and 16 ENAHO skills)

Session 04 has only one working tool, `buscar_series`. The other four pieces are TODOs for the student. All 8 tests call the live BCRP API with no mocks, so they need internet. Session 16's numbers are already reproduced in your local `enaho-skills` repo. Before you move the files, read "Moving to `mcp/`" below: the obvious import fix clashes with the MCP library.

`P` = `~\Documents\GitHub\Data-Science-Python\sessions\04-mcp-claude-code\proyecto`

## 1. Session 04: the BCRP MCP server

**What `server.py` defines**
- Constants (`P\server.py:19-23`):
  - `CATALOGO = datos/catalogo_bcrp.csv`
  - `URL_CATALOGO = https://estadisticas.bcrp.gob.pe/estadisticas/series/metadata`
  - `API = https://estadisticas.bcrp.gob.pe/estadisticas/series/api`
  - `SOLO_LECTURA = {"readOnlyHint": True, "openWorldHint": True}`
- `mcp = FastMCP("bcrp", instructions=...)` (`:25-28`). The instructions tell the model to search first, use `resumen`/`serie`, never calculate by hand, and cite the code and period.
- `catalogo()`, cached (`:35-48`):
  - Downloads the catalogue once with a 120 s timeout and `raise_for_status`, decodes it as latin-1 and saves it as UTF-8.
  - Reads it with `read_csv(sep=";", dtype=str)` and renames the Spanish headers to `codigo, categoria, grupo, nombre, frecuencia, actualizada, inicio`.
  - Adds a `texto` column without accents for searching.
- `_ficha(codigo)` (`:51-57`) raises `ToolError(f"No existe el código de serie {codigo!r}...")`. It returns `codigo`, `nombre` (= grupo - nombre), `categoria`, `frecuencia`, `inicio`, `actualizada`.
- Tool `buscar_series(texto: str, frecuencia: str|None=None, limite: int=10) -> list[dict]` is complete (`:60-78`):
  - Every word must appear in `texto`; the frequency filter is optional.
  - Sorts current series first (updated ≥ 2025), then shorter names.
  - Calls no endpoint itself; it only reads the catalogue.

**The TODOs the student must complete** (the stubs are comments only)
- TODO 1, `serie(codigo, desde, hasta)` (`:81-90`):
  - Returns `{"codigo","nombre","frecuencia","datos":[{"periodo","valor"}],"fuente"}`.
  - Calls `f"{API}/{codigo}/json/{desde}/{hasta}"`, which answers `{"config":…, "periods":[{"name":"Ene.2025","values":["0.81"]}]}`.
  - Dates sent to the API: `2025-1` (monthly and quarterly), `2025-01-15` (daily), `2025` (annual).
  - Periods it returns are `Ene.2025`, `01.Oct.26`, `T1.25` and `2025`; September comes as `Set`. Output them as `2025-01`, `2026-10-01`, `2025-T1`, `2025`.
  - Skip `n.d.` values and use the frequency from `_ficha` to pick the date format.
  - When rate-limited, the API returns an HTML page instead of JSON: retry and cache.
  - An unknown code must raise a `ToolError` that names the code.
- TODO 2, `resumen(...)` (`:92-93`): returns `primero, ultimo, cambio, variacion_pct, promedio, maximo, minimo`. The last three include their period.
- TODO 3 (`:95-99`): one tool of your own. Suggestions are World Bank `comparar_paises`, `correlacion` or `grafico`.
- TODO 4 (`:101`): a resource, e.g. `bcrp://serie/{codigo}`.
- TODO 5 (`:103`): a prompt, e.g. `informe(tema)`.
- The `.gitignore` excludes `solucion/`, so no reference solution is published.

**The 8 tests in `P\test_server.py`**
- How they run:
  - Imports `from server import mcp` (`:13`).
  - Uses an in-memory `fastmcp.Client(mcp)` through `asyncio.run` (`:16-22`).
  - `.data` unwraps the result.
  - No mocks: real BCRP network calls (`:5`).

| # | Test | What it asserts |
|---|---|---|
| 1 | `test_buscar_encuentra_el_ipc` `:25` | `PN01273PM` is in the top 5 for "ipc 12 meses"; keys ⊇ {codigo, nombre, frecuencia} |
| 2 | `test_cuatro_herramientas_como_minimo` `:31` | {buscar_series, serie, resumen} exist and there are ≥ 4 tools |
| 3 | `test_serie_mensual` `:37` | `PN01271PM` 2025-01..2025-12 gives 12 rows; `[0].periodo=="2025-01"`; `[2].valor≈0.81±0.01`; `fuente` starts with `https://estadisticas.bcrp.gob.pe` |
| 4 | `test_serie_diaria` `:45` | `PD04638PD` 2026-10-01..15: first is `2026-10-01`; last `== {"periodo":"2026-10-15","valor":≈3.428±0.001}` (only those 2 keys) |
| 5 | `test_resumen_sin_cuentas_a_mano` `:51` | `PN01273PM` 2025-12..2026-09: `primero.valor≈1.51`, `ultimo.valor≈4.55`, `maximo.periodo=="2026-09"`; keys cambio, variacion_pct, promedio, minimo exist |
| 6 | `test_codigo_inexistente_da_un_error_claro` `:59` | `ToolError` whose message matches "XX999" |
| 7 | `test_un_recurso` `:64` | resources + resource templates ≥ 1 |
| 8 | `test_un_prompt` `:70` | prompts ≥ 1 |

- The tests pass dates as `2025-01` (zero-padded), so `serie` must turn them into `2025-1` for the API.

**Moving to `mcp/`: the import trap**
- FastMCP depends on the `mcp` SDK, version 2.3.0 (`P\uv.lock:636`), which has its own `mcp.server` subpackage.
- Do not change the import to `from mcp.server import mcp`, and do not add `mcp/__init__.py`. Either one makes your folder and the SDK collide.
- Keep `from server import mcp` and let pytest find it. Its default import mode adds the test file's folder to the path, or you can set `pythonpath=["mcp"]` in the pytest config.
- `server.py` writes `datos/` next to itself (`AQUI`), so after the move it lands in `mcp/datos/`.

**How `evaluar.py` and `preguntas.csv` work**
- `preguntas.csv` columns: `id,pregunta,verdad,tolerancia,serie,periodo`. There are 8 rows (`P\preguntas.csv:1-9`); `serie` and `periodo` are never read by `evaluar.py`.
- Each question runs as `claude -p INSTRUCCION+pregunta --output-format json --json-schema ESQUEMA --no-session-persistence --model <m>` plus the mode's flags (`P\evaluar.py:31-35`).
  - Each call times out at 600 s and runs with `cwd=AQUI`.
  - `ESQUEMA` requires `valor` (number or null) and `fuente`; `unidad` is optional (`:19-21`).
  - `INSTRUCCION` says to answer `null` instead of guessing (`:22-23`).
- Modes (`:24-28`):
  - `memoria`: `--tools "" --strict-mcp-config`
  - `web`: `--tools WebSearch,WebFetch` plus the same `--allowedTools`
  - `mcp`: `--tools "" --strict-mcp-config --mcp-config AQUI/.mcp.json --allowedTools mcp__bcrp`
  - A Mode A vs Mode B experiment means adding a new entry to the `MODOS` dict and adding it to the `--modos` choices.
- Each call records `valor`, `fuente` (from `structured_output`), `segundos` (wall clock) and `turnos` (`num_turns`) (`:36-42`).
- Scoring `calificar` (`:45-48`): `None` → "no sabe"; `|valor-verdad|<=tolerancia` → "acierta"; otherwise "se equivoca".
- Command line (`:52-59`):
  - Options: `--modos` (default `memoria mcp`), `--modelo haiku`, `--preguntas`, `--paralelo 4` (a `ThreadPoolExecutor`).
  - It exits if `.mcp.json` is missing from the script's folder.
- Output (`:67-75`):
  - Writes `resultados.csv` with `id,modo,verdad,valor,fuente,segundos,turnos,resultado`.
  - Prints a pivot table of values and the counts per mode with mean seconds.
- Reference result with Haiku: memoria 0/8, web 7/8, MCP 8/8 (`P\README.md:108`).

**Dependencies** (`P\pyproject.toml`)
- `requires-python>=3.11`; `fastmcp>=4,<5`, `httpx`, `pandas`; dev group `pytest`.
- Locked versions: fastmcp 4.1.4, mcp 2.3.0, httpx 0.28.1, pandas 3.1.0, pytest 9.2.0 (`P\uv.lock:391-392,502,636,909,1238`).

**Other session 04 rules**
- `test_server.py` must not be changed (`P\README.md:10,125`).
- `.mcp.json` must include `bcrp` and `fetch` and no keys (`:76-77,135`).
- Expected error message when the API fails: «El BCRP no respondió con datos» (`:143`).

## 2. Session 16: ENAHO skills (remote README, line numbers from `cat -n`)

**Skill conventions**
- Each skill is a folder `.claude/skills/<name>/` with a `SKILL.md` and optional `reference.md` and `scripts/` (`:24-25,163-166`).
- The YAML frontmatter must start on line 1 with `---` (`:211`):
  - `name`: lowercase, digits and hyphens, at most 64 characters.
  - `description`: third person, says what the skill does and when to use it, with trigger words like ENAHO, INEI, pobreza, mapa.
  - Body under 500 lines (`:26-34`).
  - Optional `argument-hint`.
- Variables available inside a skill: `$ARGUMENTS`/`$0` and `${CLAUDE_SKILL_DIR}` (`:31-32`).
- Fixed steps (keys, filters, merges, validation) go in a script; judgment calls go in the text (`:35-36`).

**The three skills**
- `limpiando-enaho`:
  - Takes the module 34 and 02 zips; produces `salidas/personas_2024.parquet` and `salidas/validacion.txt` (`:65`).
  - Reference `SKILL.md` (`:101-113`):
    1. Ask the user for the zips if they are missing.
    2. Run `uv run ${CLAUDE_SKILL_DIR}/scripts/limpiar.py --anio $0`.
    3. Stop if poverty differs from INEI by more than 0.1 points.
    4. Weight every figure with `facpob07`.
    5. Read `reference.md` before using a variable not in the base.
- `graficando-enaho` (`:117-124`):
  - Poverty by area, sex or age; weight with `facpob07`.
  - Sorted bars starting at 0, one colour, value written on each bar.
  - Title says what and when; footnote «Fuente: INEI, ENAHO 2024».
  - PNG at 200 dpi in `figuras/`.
- `mapeando-enaho` (`:117-124`):
  - Join `ubigeo[:2]` to `FIRST_IDDP` as text, never by name.
  - Require 25 departments, none missing.
  - Sequential colour scale from 0, no rainbow; legend says "% de personas".
  - Lima (15) and Callao (07) stay separate.
  - Output `mapas/pobreza_departamento.png`.
- Chaining: the graph and map skills say «Si no existe `salidas/personas_2024.parquet`, usa primero la skill `limpiando-enaho`» (`:69-70`).

**Cleaning rules, in order** (`:84-92`)
1. Read with `pd.read_stata(..., convert_categoricals=False)` and the keys as text.
2. Lowercase the column names (the year column arrives as `aÑo`).
3. Keep habitual residents: `(p204==1 & p205==2) | (p204==2 & p206==1)`.
4. Merge people to households with `merge(..., validate="m:1")`.
5. Build `departamento=ubigeo[:2]`, `urbano=estrato<=5`, `pobre=pobreza<=2`.
6. Validate that keys are unique and the merge loses or duplicates no rows.
7. Save the parquet and `validacion.txt`.

**Data sources** (`:52-54`)
- Module 34 (sumaria): one row per household, 33,691 rows, keys `conglome, vivienda, hogar`, weight `factor07`.
- Module 02 (miembros): one row per person, 117,721 rows, the same keys plus `codperso`, weight `facpob07`.
- GeoJSON from `.../sessions/06-geoespacial/lab/Data/peru_departamental_simple.geojson`: 25 features, key `FIRST_IDDP`.
- `966` is the INEI code for ENAHO 2024.
- The README does not spell out the codes of `pobreza`. The usual ENAHO coding is 1 = extreme poor, 2 = non-extreme poor, 3 = not poor, which matches extreme poverty at 5.5 %.

**Expected validation numbers** (`:149-156`)

| Figure | Value |
|---|---|
| National poverty | 27.6 % (27.58 % with household `factor07×mieperho`; 27.53 % with people `facpob07`) |
| Extreme poverty | 5.5 % |
| Households | 33,691 |
| Habitual residents | 108,664 of 117,721 rows |
| Urban / rural | 24.8 / 39.3 % |
| Lima Metropolitana (`dominio==8`) | 28.2 % |

- Evaluation prompts (`:138-140`): Cusco 18.5 %; urban/rural 24.8 % and 39.3 %; map with Cajamarca 45.0 % and Ica 6.0 %.
- The without-skills run uses `claude -p --disallowedTools Skill "..."` (`:133`).

**Reference CSV** (`referencias/pobreza_departamento_2024.csv`)
- Columns `ccdd,departamento,pobreza_pct`; 25 rows; `ccdd` is zero-padded ("01"–"25"); names are uppercase without accents.
- Examples: 06 CAJAMARCA 45.0, 11 ICA 6.0, 15 LIMA 27.1, 07 CALLAO 33.9.

**Your local copy is already done:** `~\Documents\GitHub\enaho-skills\`
- It has the three skills plus a fourth, `descargando-enaho`, with their scripts, and `evaluacion.md`.
- `salidas\validacion.txt` passes every check: 108,664 residents, 27.53/27.58 %, and all 25 departments within ±0.1.

## Key Learnings
1. Only `buscar_series` works in session 04's `server.py`; `serie`, `resumen`, a tool of your own, a resource and a prompt are TODO comments.
2. All 8 tests in `test_server.py` import `from server import mcp` and call the live BCRP API through an in-memory FastMCP Client, with no mocking.
3. Changing the test import to `mcp.server` or adding `mcp/__init__.py` would collide with the `mcp` SDK, version 2.3.0, that FastMCP 4.1.4 depends on.
4. `evaluar.py` runs `claude -p` with a `--json-schema` per mode from the `MODOS` dict, and scores a null `valor` as "no sabe" and a value within tolerance as "acierta".
5. ENAHO 2024 validation targets are 27.6 % poverty, 108,664 habitual residents, and a department join from `ubigeo[:2]` to `FIRST_IDDP` as text.
