# Agente de investigación socioeconómica del Perú

Tarea 4 del curso Python Intermedio ([enunciado](https://github.com/d2cml-ai/Data-Science-Python/issues/201)). Es un agente en Claude Code que responde preguntas sobre la economía y la pobreza del Perú con datos oficiales: series del BCRP por un servidor MCP propio, boletines de la SBS por un segundo MCP y microdatos de la ENAHO 2024 del INEI por Skills. Cada cifra del informe sale de una herramienta y se puede rastrear hasta su fuente.

**Pregunta de investigación:** ¿Cómo evolucionaron la inflación y la actividad económica del Perú entre 2020 y 2024, y qué brechas territoriales y urbano-rurales presentaba la pobreza monetaria en 2024?

| Entregable | Archivo |
|---|---|
| Informe final | [`informes/informe_final.md`](informes/informe_final.md) |
| Servidor MCP del BCRP y sus 10 pruebas | [`mcp/server.py`](mcp/server.py), [`mcp/test_server.py`](mcp/test_server.py) |
| Skills de la ENAHO | [`.claude/skills/`](.claude/skills/) |
| Validación de la ENAHO | [`salidas/validacion.txt`](salidas/validacion.txt) |
| Evaluación con y sin MCP y Skills | [`evaluacion/resultados.csv`](evaluacion/resultados.csv), [`evaluacion/comparacion.md`](evaluacion/comparacion.md) |
| Evidencias del uso de IA | [`evidencias_ia/`](evidencias_ia/) |

## 1. Objetivo

Construir un agente que no conteste de memoria. Ante una pregunta en lenguaje natural, el agente busca la serie o el indicador correcto, lo consulta en la fuente oficial, calcula con código y no a mano, y entrega gráficos, un mapa y un informe con la procedencia de cada número. Después, una evaluación mide si esas herramientas mejoran las respuestas frente a Claude Code sin ellas.

## 2. Arquitectura

```mermaid
flowchart LR
    U[Pregunta en lenguaje natural] --> A[Claude Code<br/>reglas en CLAUDE.md]
    A -->|MCP| B[bcrp<br/>mcp/server.py]
    A -->|MCP| S[sbs<br/>mcp-sbs-peru]
    A -->|Skills| E[limpiando · graficando · mapeando<br/>ENAHO 2024]
    B --> API[(API del BCRP)]
    S --> SBS[(Boletines de la SBS)]
    E --> INEI[(Microdatos del INEI)]
    E --> IND[salidas/indicadores.csv]
    B --> FIG[figuras/ y salidas/bcrp/]
    A -->|Skill| I[informando-peru]
    I --> R[informes/informe_final.md]
    A -->|Skill| V[verificando-consistencia]
    V --> C[salidas/consistencia.md]
    IND --> D[dashboard/]
    R --> D
```

- **`CLAUDE.md`** fija las reglas del agente: ninguna cifra de memoria, nada de cálculos a mano, informar las fallas, pedir aclaración ante preguntas ambiguas y no confundir asociación con causalidad.
- **`salidas/indicadores.csv`** es la fuente única de las cifras de la ENAHO. La escribe `limpiando-enaho` y la leen los gráficos, el mapa, el informe, el verificador y el dashboard, así que todos muestran el mismo número.
- El informe se arma en dos pasos. Claude redacta un borrador con marcadores en lugar de números (`{{enaho.pobreza_nacional|1}}`, `{{bcrp.resumen(codigo=PN01273PM, desde=2020-01, hasta=2024-12).ultimo.valor|2}}`). Después un script resuelve cada marcador llamando otra vez a las herramientas y rechaza cualquier cifra escrita a mano.

## 3. Herramientas MCP

### Servidor del BCRP (`mcp/server.py`, FastMCP)

| Componente | Qué hace |
|---|---|
| `buscar_series(texto, frecuencia, limite)` | Busca en el catálogo oficial del BCRP por palabras, sin importar tildes ni mayúsculas. |
| `serie(codigo, desde, hasta)` | Devuelve los datos de una serie entre dos fechas (`2025-01`, `2025-01-15` o `2025`, según la frecuencia), con los periodos normalizados (`Ene.2025` → `2025-01`, `T1.25` → `2025-T1`) y sin los `n.d.`. |
| `resumen(codigo, desde, hasta)` | Calcula primero, último, cambio, variación porcentual, promedio, máximo y mínimo, cada uno con su periodo. |
| **`comparar_series(codigo_a, codigo_b, desde, hasta)`** | Herramienta propia. Alinea dos series de la misma frecuencia por periodo y devuelve cuántos periodos comparten, su correlación de Pearson y la diferencia en cada periodo. Si las frecuencias no coinciden, explica el error en vez de mezclar datos mensuales con diarios. |
| `graficar_serie(codigo, desde, hasta, titulo)` | Guarda el gráfico en `figuras/` y sus datos en `salidas/bcrp/`, con unidad, periodo y fuente. |
| Recurso `bcrp://serie/{codigo}` | Ficha descriptiva de la serie: nombre, grupo, frecuencia, fechas disponibles y URL. |
| Prompts `interpretar_indicador` e `informe` | Guías reutilizables que obligan a citar código, periodo y URL en cada cifra. |

El servidor tolera las fallas de la API. Reintenta con espera creciente, valida el contenido y no solo el código HTTP, porque el BCRP responde una página HTML anti-bots con estado 200. Guarda las respuestas en caché por 24 horas y, si la API no responde, usa la copia vieja con un aviso. Cuando no hay datos, devuelve un `ToolError` con el código y el rango pedidos.

### Servidor de la SBS (segunda fuente oficial)

[`mcp-sbs-peru`](https://github.com/rodnm/mcp-sbs-peru) lee los boletines estadísticos de la Superintendencia de Banca, Seguros y AFP: morosidad, ROE y liquidez por entidad (`indicadores`), rankings (`ranking`), cualquier boletín por su código (`reporte`), AFP y seguros. En el informe aporta el contexto financiero de 2024. Se instala desde GitHub con `uvx`, sin copiar su código.

## 4. Skills

Están en `.claude/skills/`. Cada una tiene un `SKILL.md` que Claude Code carga cuando la pregunta lo amerita, y un script que hace el trabajo.

| Skill | Qué hace |
|---|---|
| **`limpiando-enaho`** | Lee los módulos 34 (sumaria) y 02 (miembros) con las llaves como texto, filtra a los residentes habituales (`((p204==1)&(p205==2))\|((p204==2)&(p206==1))`), une con `merge(..., validate="m:1")` y define `urbano = estrato <= 5` y `pobre = pobreza <= 2`. Pondera por hogar (`factor07 × mieperho`) para las cifras nacionales, por área y por departamento, y por persona (`facpob07`) para sexo y edad. Escribe `salidas/validacion.txt` y se detiene si una validación esencial falla, sin dejar la base. |
| **`graficando-enaho`** | Grafica la pobreza por área, sexo, edad o departamento con títulos que dicen el hallazgo, unidad, periodo y fuente. Si falta la base procesada, primero corre `limpiando-enaho`. |
| **`mapeando-enaho`** | Hace el mapa departamental uniendo `ubigeo[:2]` con `FIRST_IDDP`, con 25 unidades (Lima y Callao separados) y una escala que empieza en 0. Compara cada departamento con la referencia de la sesión 16 en `salidas/mapa_vs_referencia.csv`. |
| `descargando-enaho` | Baja los zip del INEI y los límites departamentales a `datos/`. |
| ★ `informando-peru` | Arma el informe con marcadores, tabla de trazabilidad y referencias (ver la sección 2). |
| ★ `verificando-consistencia` | Contrasta las herramientas entre sí y escribe `salidas/consistencia.md` con OK, DIFERENCIA, FALLA o NO VERIFICABLE. Compara la pobreza con dos ponderadores, el mapa con los indicadores, la inflación a 12 meses recalculada desde el índice del IPC con la publicada, `resumen` con `serie` y cada cifra del informe con su fuente. |

## 5. Fuentes de datos

| Fuente | Enlace | Cómo se obtiene |
|---|---|---|
| ENAHO 2024, módulo 34 (sumaria) | <https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo34.zip> | `descargando-enaho` |
| ENAHO 2024, módulo 02 (miembros del hogar) | <https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo02.zip> | `descargando-enaho` |
| Límites departamentales | [`peru_departamental_simple.geojson`](https://github.com/d2cml-ai/Data-Science-Python/tree/main/sessions/16-skills-enaho) del repo del curso | `descargando-enaho` |
| Series del BCRP | API: `https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{código}/json/{desde}/{hasta}` ([documentación](https://estadisticas.bcrp.gob.pe/estadisticas/series/documentos/bcrpdataapi.pdf)) | servidor `bcrp`, al consultar |
| Boletines de la SBS | archivos oficiales de la SBS; cada respuesta del servidor trae la URL del boletín ([detalle](https://github.com/rodnm/mcp-sbs-peru)) | servidor `sbs`, al consultar |
| Referencia departamental de la sesión 16 | [`referencias/pobreza_departamento_2024.csv`](referencias/pobreza_departamento_2024.csv) | incluida en el repo |

Los microdatos no se suben al repositorio: `datos/` está en `.gitignore`.

## 6. Instalación

Requisitos: [uv](https://docs.astral.sh/uv/), Python 3.12 o superior (uv lo instala si falta) y [Claude Code](https://docs.claude.com/claude-code).

```bash
git clone https://github.com/rodnm/agente-socioeconomico-peru
cd agente-socioeconomico-peru
uv sync
```

## 7. Conectar los MCP a Claude Code

El archivo [`.mcp.json`](.mcp.json) declara los servidores `bcrp` (`uv run mcp/server.py`), `sbs` y `fetch`, y [`.claude/settings.json`](.claude/settings.json) los habilita y permite sus herramientas. Basta con abrir Claude Code en la raíz del repo:

```bash
claude            # la primera vez pide aprobar los servidores del proyecto
/mcp              # dentro de Claude Code: los tres deben figurar como conectados
```

Para registrarlo en otro proyecto: `claude mcp add bcrp -- uv run --directory <ruta al repo> mcp/server.py`.

## 8. Reproducir el procesamiento y las pruebas

```bash
# Datos de la ENAHO y procesamiento
uv run .claude/skills/descargando-enaho/scripts/descargar.py --anio 2024
uv run .claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024        # salidas/validacion.txt
uv run .claude/skills/graficando-enaho/scripts/graficar.py --por area        # también sexo, edad, departamento
uv run .claude/skills/mapeando-enaho/scripts/mapear.py                       # mapas/pobreza_departamento.png

# Pruebas
uv run pytest mcp/test_server.py      # las 8 originales de la sesión 04 y 2 nuevas, contra la API real: 10 passed
uv run pytest tests                   # robustez, skills, informe, consistencia, evaluación y dashboard, sin internet

# Informe, verificación y dashboard
uv run .claude/skills/informando-peru/scripts/armar_informe.py              # informes/borrador.md → informe_final.md
uv run .claude/skills/verificando-consistencia/scripts/verificar.py         # salidas/consistencia.md
uv run streamlit run dashboard/app.py

# Evaluación (cada pregunta es una sesión nueva de claude -p)
uv run evaluacion/verdades.py                                               # respuestas esperadas del BCRP, sin el MCP
uv run evaluacion/evaluar.py --modos A B
uv run evaluacion/evaluar.py --modos memoria solo-mcp solo-skills sin-propia
uv run evaluacion/evaluar.py --robustez --modos A B
```

## 9. Resultados de la evaluación

Son 10 preguntas con respuesta verificable: 4 del BCRP, 4 de la ENAHO y 2 mixtas. Cada una corrió en una sesión nueva de Claude Code (Sonnet), y las respuestas esperadas se fijaron en un commit antes de la primera corrida.

| | Sin MCP ni Skills (A) | Con MCP y Skills (B) |
|---|---|---|
| Respuestas correctas | 8 de 10 | **10 de 10** |
| Incorrectas o sin respuesta | 2 (Cusco y Lima Metropolitana) | 0 |
| Tiempo promedio | 38.1 s | 22.2 s |
| Costo total | USD 2.22 | USD 2.30 |

- **Comparación** ([`evaluacion/comparacion.md`](evaluacion/comparacion.md)):
  - Los dos modos aciertan las cifras del BCRP. B las cita siempre con el código de serie y la URL de la API.
  - A falla donde la web no alcanza: tomó una cifra departamental de una fuente secundaria y resolvió de otra manera la definición de Lima Metropolitana.
  - En la revisión manual de las interpretaciones, ninguno de los dos modos fue impecable: B también hizo una afirmación causal sin respaldo en m1.
- **Ablación** ([`evaluacion/ablacion.md`](evaluacion/ablacion.md)):
  - Sin herramientas, el modelo acierta 2 de 10 y responde «no sé» en 6.
  - Con solo el MCP acierta 8, porque repite los errores de la ENAHO del Modo A.
  - Con solo las skills acierta 10, porque llamó a la API del BCRP por su cuenta.
  - La primera versión de la ablación tenía fugas entre componentes, y se documenta cómo se corrigió.
- **Robustez:** el Modo A cumplió la conducta esperada en 7 de 8 pedidos ambiguos o imposibles y el Modo B en 6. Ninguno inventó un dato inexistente.

Las tablas completas salen de `uv run evaluacion/analizar.py` → [`evaluacion/metricas.md`](evaluacion/metricas.md). Los datos están en [`resultados.csv`](evaluacion/resultados.csv) y [`robustez_resultados.csv`](evaluacion/robustez_resultados.csv).

## 10. Limitaciones y problemas encontrados

- **Bloqueo anti-bots del BCRP.** La mañana del 2 de noviembre de 2026 la API del BCRP respondió a todo programa, desde la primera consulta, una página de Imperva («Pardon Our Interruption») con estado 200, mientras el navegador sí cargaba. Por eso el servidor valida el contenido de cada respuesta, reintenta, guarda caché y responde con un error explícito. También por eso las pruebas de robustez simulan la API (`tests/test_robustez_mcp.py`). Una lección: el BCRP entrega su JSON con `Content-Type: text/html`, así que comprobar la cabecera no sirve para saber si respondió datos; hay que leer el cuerpo.
- **Ponderadores.** La pobreza nacional se reproduce con 27.58 % al ponderar por hogar (`factor07 × mieperho`) y da 27.53 % con `facpob07`. Las dos están dentro de la tolerancia de 0.1 puntos; el verificador reporta la diferencia.
- **Niveles de agregación.** El BCRP publica series nacionales o de Lima con frecuencia mensual o diaria; la ENAHO da tasas anuales por área y departamento. El informe las presenta juntas como contexto, sin afirmar relaciones causales, y la SBS no publica boletines por departamento.
- **Evaluación.** El `CLAUDE.md` global y los hooks del usuario se aplican en todos los modos por igual. El Modo A corre en una carpeta temporal con solo los zip crudos y con `--strict-mcp-config`, para que no herede los servidores MCP ni las skills del usuario.
- **Lo que encontró el propio agente.** En la primera corrida integrada, el verificador marcó la inflación como no verificable. El agente investigó y vio que `verificar.py` usaba `PN01270PM`, el índice del IPC base 2009 que el BCRP descontinuó en diciembre de 2021. Se corrigió por `PN38705PM` (Dic.2021 = 100). En la segunda corrida, el agente leyó las instrucciones de las skills de la ENAHO y corrió sus scripts directamente, sin invocarlas. Ahora `informando-peru` exige invocarlas, porque cada skill trae sus propias reglas, como detenerse si una validación falla.
- **Permisos en `claude -p`.** Mientras no se acepte el diálogo de confianza del proyecto en una sesión interactiva, Claude Code ignora los permisos de `.claude/settings.json`. Por eso las corridas automáticas pasan `--allowedTools` explícitamente.

## 11. Ejemplo de una ejecución completa

Una sola ejecución desde la raíz del repo, con las salidas de la ENAHO borradas para que el agente tuviera que generarlas:

```bash
claude -p "Investiga esta pregunta y entrégame el informe: ¿Cómo evolucionaron la inflación y la actividad económica del Perú entre 2020 y 2024, y qué brechas territoriales y urbano-rurales presentaba la pobreza monetaria en 2024? Usa el BCRP para la inflación y la actividad, la SBS para el contexto financiero de 2024 y la ENAHO 2024 para la pobreza por área y por departamento, con su mapa. Al final verifica la consistencia de las cifras." \
  --model sonnet --strict-mcp-config --mcp-config .mcp.json \
  --allowedTools "Skill,Bash(uv run *),Read,Write,Edit,Glob,Grep,mcp__bcrp,mcp__sbs" \
  --output-format stream-json --verbose > corrida.jsonl
```

Usó 2 servidores MCP y 5 skills en 41 turnos, 188 segundos y USD 0.76. La transcripción completa, con su línea de tiempo, está en [`evidencias_ia/integracion/03_corrida_final_mcp_y_skills.md`](evidencias_ia/integracion/03_corrida_final_mcp_y_skills.md). En resumen:

| Pasos | Herramienta | Resultado |
|---|---|---|
| 1 | skill `informando-peru` | carga el procedimiento del informe |
| 4–5 | MCP `bcrp.buscar_series` | elige `PN01273PM` (IPC de Lima, a 12 meses) y `PN01728AM` (PBI, interanual) |
| 7, 11 | skill `limpiando-enaho` | reconstruye la base; 45 validaciones OK |
| 8–9, 16 | MCP `bcrp.resumen`, `bcrp.comparar_series` | extremos, promedios y correlación de las dos series |
| 10, 18–19 | MCP `sbs.indicadores`, `sbs.ranking` | morosidad de bancos y cajas, y concentración del crédito |
| 12–13, 17 | skills `graficando-enaho` y `mapeando-enaho` | gráficos por área y departamento, y el mapa |
| 14–15 | MCP `bcrp.graficar_serie` | gráficos de la inflación y del PBI |
| 23–26 | `armar_informe.py` | [`informes/informe_final.md`](informes/informe_final.md), con 41 cifras trazadas |
| 27–28 | skill `verificando-consistencia` | [`salidas/consistencia.md`](salidas/consistencia.md): 8 de 8 OK |

Las salidas de la ENAHO regeneradas coinciden byte a byte con las versionadas.

## 12. Evidencias del uso de IA

Las conversaciones con Claude Code están en [`evidencias_ia/`](evidencias_ia/), ordenadas por etapa (`mcp/`, `skills/`, `integracion/`, `evaluacion/`). Se exportaron con [`scripts/exportar_evidencias.py`](scripts/exportar_evidencias.py), que convierte las transcripciones JSONL de Claude Code en Markdown y oculta rutas personales, nombres de usuario, correos, claves y tokens.

## Innovaciones

| Idea del enunciado | Dónde está |
|---|---|
| Skill para generar informes | `.claude/skills/informando-peru/` |
| Segundo MCP con otra fuente oficial | servidor `sbs` en `.mcp.json` |
| Detectar inconsistencias entre herramientas | `.claude/skills/verificando-consistencia/` → `salidas/consistencia.md` |
| Dashboard | `dashboard/app.py` (Streamlit) |
| Pruebas de robustez | `tests/test_robustez_mcp.py` y `evaluacion/robustez.csv` |
| Calidad al desactivar herramientas | modos `memoria`, `solo-mcp`, `solo-skills` y `sin-propia` de `evaluacion/evaluar.py` → `evaluacion/ablacion.md` |
| Informes con tablas, gráficos y referencias | `armar_informe.py` agrega la trazabilidad y las referencias |

## Estructura

```text
├── CLAUDE.md                 reglas del agente
├── .mcp.json                 servidores bcrp, sbs y fetch
├── .claude/skills/           descargando, limpiando, graficando, mapeando, informando-peru, verificando-consistencia
├── mcp/                      server.py y test_server.py
├── tests/                    pruebas sin internet
├── referencias/              pobreza departamental de la sesión 16
├── salidas/  figuras/  mapas/  informes/
├── evaluacion/               preguntas, verdades, arnés, resultados y análisis
├── dashboard/                app.py y logica.py
├── scripts/                  exportar_evidencias.py
└── evidencias_ia/
```

## Licencia

[MIT](LICENSE).
