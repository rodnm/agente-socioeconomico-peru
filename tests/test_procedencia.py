"""Cada cifra de referencia se rastrea hasta un cuadro y una página que existen en el informe técnico del INEI.

    uv run pytest tests/test_procedencia.py

Las ubicaciones se verificaron contra el texto del PDF (SHA-256 ed964c41…6d73; página impresa = página del visor − 2):
el Cuadro N° III.1 ocupa las pp. 219 (nacional, áreas y dominios) y 220 (departamentos, Lima Metropolitana y Lima
provincias), y el Cuadro N° III.4 la p. 223 (pobreza extrema). Ninguna prueba descarga nada.
"""
import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]
SKILLS = RAIZ / ".claude" / "skills"
REFERENCIA = RAIZ / "referencias" / "inei_pobreza_2024.csv"
VALIDACION = RAIZ / "salidas" / "validacion.txt"
LIMPIAR = SKILLS / "limpiando-enaho" / "scripts" / "limpiar.py"
ZIPS_2024 = [RAIZ / "datos" / "966-Modulo34.zip", RAIZ / "datos" / "966-Modulo02.zip"]
CODIGOS_ENAHO = ("737", "759", "784", "906", "966")

# Las únicas ubicaciones del informe que contienen las cifras usadas, comprobadas en el PDF.
UBICACIONES_VERIFICADAS = {("Cuadro III.1", 219), ("Cuadro III.1", 220), ("Cuadro III.4", 223)}


def cargar(ruta: Path, nombre: str):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def lineas_con_meta(texto: str) -> list[str]:
    return [l for l in texto.splitlines() if "meta INEI" in l]


def comprobar_validacion(texto: str) -> None:
    """Lo que debe cumplir cualquier validacion.txt: citas reales, sin «nan» y Lima 15 declarada sin cifra."""
    assert not re.search(r"\bnan\b", texto, flags=re.I), "hay un valor vacío impreso como «nan»"
    metas = lineas_con_meta(texto)
    assert metas, "no hay líneas con meta del INEI"
    for linea in metas:
        cita = re.search(r"(Cuadro [IVX]+\.\d+), p\. (\d+)", linea)
        assert cita and (cita[1], int(cita[2])) in UBICACIONES_VERIFICADAS, linea
    for falsa in ("Cuadro 3.1", "Cuadro 3.4", "Anexo Cuadro", "consigna del curso", "p. 72", "p. 64"):
        assert falsa not in texto, falsa
    assert "departamento 15" in texto and "sin cifra publicada por el INEI" in texto


# --- referencias/inei_pobreza_2024.csv ---------------------------------------------------------------------------

def test_tabla_inei_no_incluye_el_departamento_15():
    tabla = pd.read_csv(REFERENCIA, dtype={"ccdd": str})
    assert "15" not in set(tabla["ccdd"].dropna())
    assert not tabla["ambito"].str.contains("departamento completo", case=False).any()
    # 24 departamentos y el Callao, con código de dos dígitos; Lima va como 1501 y 15_resto.
    dos_digitos = tabla["ccdd"].dropna().loc[lambda c: c.str.fullmatch(r"\d{2}")]
    assert sorted(dos_digitos) == [f"{i:02d}" for i in range(1, 26) if i != 15]
    assert {"1501", "15_resto"} <= set(tabla["ccdd"].dropna())


def test_cada_fila_de_la_tabla_inei_cita_una_pagina_que_existe():
    tabla = pd.read_csv(REFERENCIA, dtype={"ccdd": str})
    assert tabla["pagina"].notna().all() and tabla["cuadro"].notna().all()
    ubicaciones = set(zip(tabla["cuadro"], tabla["pagina"].astype(int)))
    assert ubicaciones <= UBICACIONES_VERIFICADAS, ubicaciones - UBICACIONES_VERIFICADAS


def test_pobreza_extrema_con_ic_y_cv_del_cuadro_iii_4():
    fila = pd.read_csv(REFERENCIA).set_index("ambito").loc["Pobreza extrema"]
    assert (fila["cuadro"], int(fila["pagina"])) == ("Cuadro III.4", 223)
    assert (fila["valor"], fila["ic_inf"], fila["ic_sup"], fila["cv"]) == (5.5, 5.0, 6.0, 4.5)


# --- limpiando-enaho: metas por año y validacion.txt -------------------------------------------------------------

def test_metas_de_limpiar_citan_cuadros_y_paginas_que_existen():
    limpiar = cargar(LIMPIAR, "limpiar")
    for anio in range(2020, 2025):
        metas = limpiar.metas_del_anio(anio)
        assert {"nacional", "urbana", "rural", "extrema", "lima_metropolitana_callao", "lima_metropolitana",
                "lima_provincias"} <= set(metas), anio
        for clave, meta in metas.items():
            assert (meta.cuadro, meta.pagina) in UBICACIONES_VERIFICADAS, (anio, clave, meta)


def test_metas_2020_2023_son_las_del_informe_del_inei():
    # Transcritas del Cuadro III.1 (pp. 219 y 220) y del Cuadro III.4 (p. 223), columnas 2020 a 2023.
    publicadas = {
        2020: (30.1, 26.0, 45.7, 5.1, 27.5, 26.6, 26.5),
        2021: (25.9, 22.3, 39.7, 4.1, 24.9, 24.4, 26.4),
        2022: (27.5, 24.1, 41.1, 5.0, 27.3, 26.9, 22.9),
        2023: (29.0, 26.4, 39.8, 5.7, 28.7, 28.1, 26.1),
    }
    claves = ("nacional", "urbana", "rural", "extrema", "lima_metropolitana_callao", "lima_metropolitana",
              "lima_provincias")
    limpiar = cargar(LIMPIAR, "limpiar")
    for anio, valores in publicadas.items():
        metas = limpiar.metas_del_anio(anio)
        assert tuple(metas[c].valor for c in claves) == valores, anio


def test_metas_2024_salen_de_la_tabla_inei_con_su_intervalo():
    limpiar = cargar(LIMPIAR, "limpiar")
    metas = limpiar.metas_del_anio(2024)
    assert (metas["nacional"].valor, metas["nacional"].ic_inf, metas["nacional"].ic_sup) == (27.6, 26.6, 28.6)
    assert (metas["extrema"].valor, metas["extrema"].pagina) == (5.5, 223)
    assert (metas["lima_metropolitana_callao"].valor, metas["lima_metropolitana"].valor,
            metas["lima_provincias"].valor) == (28.2, 27.6, 21.7)


def test_validacion_versionada_cita_al_inei_sin_nan_y_declara_lima_15():
    texto = VALIDACION.read_text(encoding="utf-8")
    comprobar_validacion(texto)
    assert all(f"ENAHO {anio}" in texto for anio in range(2020, 2025))
    assert "FALLA" not in texto


def test_validacion_rotula_los_conteos_como_conteos_de_archivos():
    texto = VALIDACION.read_text(encoding="utf-8")
    conteos = [l for l in texto.splitlines() if l[6:].startswith(("Hogares en la sumaria", "Filas del módulo 02",
                                                                   "Residentes habituales"))]
    assert len(conteos) == 15
    assert all("conteo del archivo del INEI, no es una cifra publicada" in l for l in conteos)


def test_validacion_declara_la_tolerancia_del_ponderador_de_personas():
    texto = VALIDACION.read_text(encoding="utf-8")
    contraste = [l for l in texto.splitlines() if l.startswith(("OK", "FALLA")) and "facpob07" in l]
    assert len(contraste) == 5 and all("contraste" in l for l in contraste)
    # 2024 conserva la tolerancia de la consigna; 2020-2023 usan 0.2 porque 2021 difiere en 0.16 con este ponderador.
    de_2024 = [l for l in contraste if "IC 95 %" in l]
    assert len(de_2024) == 1 and "± 0.1 " in de_2024[0]
    assert all("± 0.2 " in l for l in contraste if l not in de_2024)


@pytest.mark.skipif(not all(z.is_file() for z in ZIPS_2024), reason="faltan los zip de la ENAHO 2024 en datos/")
def test_limpiar_2024_escribe_una_validacion_trazable(tmp_path):
    shutil.copytree(SKILLS / "limpiando-enaho", tmp_path / ".claude" / "skills" / "limpiando-enaho")
    shutil.copytree(RAIZ / "referencias", tmp_path / "referencias")
    (tmp_path / "datos").mkdir()
    for archivo in ZIPS_2024:
        shutil.copy(archivo, tmp_path / "datos")
    script = tmp_path / ".claude" / "skills" / "limpiando-enaho" / "scripts" / "limpiar.py"
    r = subprocess.run([sys.executable, str(script), "--anio", "2024"], capture_output=True, text=True,
                       encoding="utf-8", cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    texto = (tmp_path / "salidas" / "validacion.txt").read_text(encoding="utf-8")
    comprobar_validacion(texto)
    assert "OK    Pobreza en Lima Metropolitana (provincia 1501)" in texto
    assert "OK    Pobreza en Lima provincias" in texto
    assert "OK    Departamentos con cifra publicada por el INEI en la referencia: 24" in texto
    grupos = pd.read_csv(tmp_path / "salidas" / "indicadores.csv").set_index("id")["grupo"]
    assert grupos["pobreza_lima_metropolitana"] == "Lima Metropolitana y Callao"
    assert grupos["pobreza_lima_metropolitana_provincia"] == "Lima Metropolitana"
    assert grupos["pobreza_lima_provincias"] == "Lima provincias"


def test_indicadores_versionados_rotulan_los_tres_ambitos_de_lima():
    tabla = pd.read_csv(RAIZ / "salidas" / "indicadores.csv")
    for anio, grupos in tabla.groupby("anio"):
        g = grupos.set_index("id")["grupo"]
        assert g["pobreza_lima_metropolitana"] == "Lima Metropolitana y Callao", anio
        assert g["pobreza_lima_metropolitana_provincia"] == "Lima Metropolitana", anio
        assert g["pobreza_lima_provincias"] == "Lima provincias", anio


# --- Documentación de las skills y de la evaluación --------------------------------------------------------------

def test_skills_de_la_enaho_describen_el_modo_multianual():
    limpiando = (SKILLS / "limpiando-enaho" / "SKILL.md").read_text(encoding="utf-8")
    descargando = (SKILLS / "descargando-enaho" / "SKILL.md").read_text(encoding="utf-8")
    referencia = (SKILLS / "limpiando-enaho" / "reference.md").read_text(encoding="utf-8")
    assert "Solo valida 2024" not in limpiando and "Solo trabaja con 2024" not in descargando
    for texto in (limpiando, descargando, referencia):
        assert "2020" in texto and "2024" in texto
        assert all(codigo in texto for codigo in CODIGOS_ENAHO)
    assert "Cuadro III.1" in referencia and "Cuadro III.4" in referencia and "p. 223" in referencia
    assert "factor_p" in referencia and "0.2" in referencia


def test_verdades_py_no_atribuye_cifras_al_curso():
    docstring = (RAIZ / "evaluacion" / "verdades.py").read_text(encoding="utf-8").split('"""')[1]
    assert "sesión 16" not in docstring
    assert "procedencia_de_las_verdades.md" in docstring


def test_procedencia_de_las_verdades_cita_lo_que_dice_el_informe():
    texto = (RAIZ / "evaluacion" / "procedencia_de_las_verdades.md").read_text(encoding="utf-8")
    filas = {}  # la primera fila de cada pregunta es la de la tabla de la ENAHO
    for m in re.finditer(r"^\| `(\w+)`.*$", texto, flags=re.M):
        filas.setdefault(m[1], m[0])
    assert "[14.7, 22.4]" in filas["e3"] and "10.5" in filas["e3"] and "220" in filas["e3"]
    assert "Cuadro III.4" in filas["e4"] and "223" in filas["e4"]
    assert "Callao" in filas["m2"] and "27.6" in filas["m2"]
    for inventada in ("[15.2, 21.8]", "9.1 %", "Cuadro 1.1", "Cuadro 1.2", "(y 27)", "(y 28)"):
        assert inventada not in texto, inventada


def test_readme_de_referencias_cita_paginas_reales():
    texto = (RAIZ / "referencias" / "README.md").read_text(encoding="utf-8")
    assert "p. 72" not in texto and "p. 223" in texto
    assert "requisito de consigna" not in texto.lower()
    assert "sin cifra publicada por el INEI" in texto
