# Evidencias del uso de IA

Todo el proyecto se desarrolló con Claude Code en una sola sesión, con subagentes para tareas acotadas, y con corridas automáticas de `claude -p` para demostrar y evaluar el agente. Las transcripciones se exportaron con [`scripts/exportar_evidencias.py`](../scripts/exportar_evidencias.py) (opción B del enunciado):
- Cada archivo empieza con una línea de tiempo de las herramientas usadas.
- Conserva los pedidos, las respuestas, cada llamada a una herramienta con sus argumentos y un extracto de cada resultado.
- Oculta rutas personales, nombres de usuario, correos, claves y tokens, antes de recortar cada resultado. Con `--ocultar` se agregan otros textos, como el usuario de un correo que aparece sin la @.
- Las horas de la sesión están en UTC.

## Sesión de desarrollo

[`00_sesion_de_desarrollo.md`](00_sesion_de_desarrollo.md) es la conversación completa, en orden cronológico. Abarca:
- El plan y la estructura del repositorio.
- El servidor MCP del BCRP y sus pruebas.
- Las skills de la ENAHO, el informe y la verificación de consistencia.
- El segundo MCP (SBS), el arnés de evaluación y el dashboard.
- Las corridas integradas, la evaluación y las correcciones que surgieron de ellas.
- La propuesta de preguntas pegada el 5 de noviembre, de la que salieron cuatro pedidos de robustez nuevos y la sección de trabajo futuro.

A mitad de la sesión, Claude Code compactó el contexto. El resumen que generó aparece plegado y no cuenta como pedido de la persona.

Algunos hitos para buscar en el archivo:

| Etapa | Qué buscar |
|---|---|
| Plan aprobado y estructura | `ExitPlanMode` |
| Servidor MCP y 10 pruebas | `mcp/server.py`, `10 passed` |
| Bloqueo anti-bots del BCRP | `Pardon Our Interruption` |
| Skills de la ENAHO y validación | `limpiar.py`, `validacion.txt` |
| Índice del IPC descontinuado | `PN38705PM` |
| Revisión de código aprobada | `acknowledge-approved` |
| Ablación con fugas y su corrección | `crudos-con-mcp` |
| Propuesta pegada y robustez ampliada | `Texto pegado`, `r12` |

## Subagentes

| Archivo | Tarea |
|---|---|
| [`subagentes/01_exploracion_sesiones_del_curso.md`](subagentes/01_exploracion_sesiones_del_curso.md) | Mapa de las sesiones 04 (MCP) y 16 (Skills) del curso, solo lectura |
| [`subagentes/02_exploracion_proyectos_previos.md`](subagentes/02_exploracion_proyectos_previos.md) | Mapa de proyectos propios reutilizables (skills de la ENAHO, MCP de la SBS, dashboard), solo lectura |
| [`subagentes/03_dashboard.md`](subagentes/03_dashboard.md) | Construcción del dashboard en Streamlit, con pruebas primero |

## Corridas del agente

| Archivo | Qué demuestra |
|---|---|
| [`skills/01_encadenamiento_mapa_sin_base.md`](skills/01_encadenamiento_mapa_sin_base.md) | «Haz un mapa de la pobreza monetaria por departamento con ENAHO 2024.» sin la base procesada: `mapeando-enaho` invoca primero `limpiando-enaho` |
| [`integracion/01_corrida_1_encuentra_indice_descontinuado.md`](integracion/01_corrida_1_encuentra_indice_descontinuado.md) | Primera corrida integrada: el agente detecta que `verificar.py` usaba un índice del IPC descontinuado |
| [`integracion/02_corrida_2_scripts_sin_skills.md`](integracion/02_corrida_2_scripts_sin_skills.md) | Segunda corrida: regenera todo, pero corre los scripts de las skills sin invocarlas |
| [`integracion/03_corrida_final_mcp_y_skills.md`](integracion/03_corrida_final_mcp_y_skills.md) | Tercera corrida: 2 servidores MCP (`bcrp`, `sbs`) y 5 skills en una sola ejecución; 41 cifras trazadas |
| [`integracion/04_corrida_final_series_2020_2024.md`](integracion/04_corrida_final_series_2020_2024.md) | Cuarta corrida (series 2020-2024), sin aislamiento: heredó la configuración global del usuario y su servidor MCP de Engram, y no invocó las skills de limpieza ni de gráficos. Se conserva como registro; su informe fue reemplazado |
| [`integracion/05_corrida_aislada_intento_1_reutiliza_borrador.md`](integracion/05_corrida_aislada_intento_1_reutiliza_borrador.md) | Primer intento aislado: regenera las salidas de la ENAHO, pero reutiliza el borrador de la cuarta corrida en lugar de escribir el suyo |
| [`integracion/06_corrida_aislada_intento_2_recupera_borrador_de_git.md`](integracion/06_corrida_aislada_intento_2_recupera_borrador_de_git.md) | Segundo intento aislado: invoca las cinco skills, pero recupera el borrador anterior con `git show`. Por eso se retiraron del commit el plan y el borrador antes de la corrida final |
| [`integracion/07_corrida_final_aislada.md`](integracion/07_corrida_final_aislada.md) | **Corrida final, aislada:** redacta su propio plan y borrador, invoca las 5 skills, consulta 6 herramientas MCP distintas de `bcrp` y `sbs` y produce [`informes/informe_final.md`](../informes/informe_final.md), con 50 cifras trazadas |

Las corridas de la evaluación (`claude -p` con `--no-session-persistence`) no guardan transcripción. Su registro es [`evaluacion/resultados.csv`](../evaluacion/resultados.csv) y [`evaluacion/robustez_resultados.csv`](../evaluacion/robustez_resultados.csv), con la respuesta, la fuente, las herramientas usadas, el tiempo, los turnos y el costo de cada una.

Las skills de la ENAHO y el MCP de la SBS se adaptaron de proyectos propios anteriores ([enaho-skills](https://github.com/rodnm/enaho-skills) y [mcp-sbs-peru](https://github.com/rodnm/mcp-sbs-peru)), que tienen sus propios repositorios.
