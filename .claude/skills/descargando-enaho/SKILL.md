---
name: descargando-enaho
description: Descarga del INEI los módulos 34 (sumaria) y 02 (miembros) de la ENAHO de 2020 a 2024 a datos/. Úsala cuando pidan bajar o descargar la ENAHO o los microdatos del INEI, o cuando falten los zip en datos/.
argument-hint: [año]
allowed-tools: Bash(uv run *)
---

# Descargar la ENAHO

1. Corre exactamente: `uv run ${CLAUDE_SKILL_DIR}/scripts/descargar.py --anio $0`. Sin año baja 2024. Para los cinco años: `uv run ${CLAUDE_SKILL_DIR}/scripts/descargar.py --todos`.
2. Si termina con error, muéstralo tal cual y detente. No busques los datos en otra fuente.
3. Responde con lo que quedó en `datos/`: `{código}-Modulo34.zip` y `{código}-Modulo02.zip` por cada año.

| Año | Código de encuesta del INEI |
|---|---|
| 2020 | `737` |
| 2021 | `759` |
| 2022 | `784` |
| 2023 | `906` |
| 2024 | `966` |

Los zip se bajan de `https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/{código}-Modulo{34|02}.zip`, el portal de microdatos del INEI. Si piden otro año, el script lo rechaza: dilo y no inventes otra URL. Un zip ya válido no se vuelve a bajar. La carpeta `datos/` no se sube a git.
