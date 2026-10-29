<!-- progress/mutacion_manual_F-067.md -->
# F-067 · Mutación manual de `app.js`

`python -m harness.mutacion` **solo muta Python** y la puerta de cobertura de
`init.sh` no mide JS. Lo único de producción que cambia F-067 es
`services/dedicacion-front/static/js/app.js` (más tres líneas de
`styles.css`, sin lógica), así que esta campaña sustituye a la automática
(mismo patrón que `progress/mutacion_manual_F-065.md`).

- **Medida sobre** `7016870ad9b64deab5ae72ef55ef07511e39f8db` (rama
  `feature/F-067-ver-vinculados`, T3: versión final de `app.js` y de los
  tests; `app.js` es el mismo que en T2, `d5117a8`). Las líneas de la tabla
  son las de ese commit.
- **Campaña 1** (sobre `d5117a8`, 984,6 s, mismos 27 mutantes): 26 muertos y
  el mismo superviviente N18; N9 solo moría de rebote (un trabajador sin
  líneas de F-063 hace `every([])` verdadero). Se añadió en T3
  `test_f067_r5_basta_un_vinculado_bajo_cualquier_linea_del_mes`, que lo
  mata por sí mismo, y se repitió la campaña entera: es la de abajo.
- **Después** de la campaña 2, el único cambio en los tests es `check=False`
  explícito en el `subprocess.run` del arnés de F-067 (aviso `PLW1510` de
  ruff): mismo comportamiento, la campaña sigue valiendo.
- **Siempre sobre una copia**: el script copia a un directorio temporal, con
  la estructura del repo, `app.js` y `styles.css` del front, su `tests/` y
  los tres ficheros ajenos que esos tests leen (dos módulos del transfer de
  los que el arnés de F-050 saca constantes y el `requirements.md` de F-044
  que mira F-064). Aplica la sustitución (el original tiene que aparecer
  **una sola vez**; si no, aborta), comprueba la sintaxis con
  `node --check` y pasa los seis ficheros de test que cargan el código
  tocado (F-067, F-044, F-041, F-063, F-064 y F-065) **sin `-x`**, anotando
  los que caen. `git status` sin cambios en código después (comprobado).
- **Línea base** (sin mutar, en la copia): `101 passed in 26.39s`. Una línea
  base en rojo aborta la campaña.
- **Workers y coste**: en serie (**1 worker**), **917,7 s** de reloj para 27
  mutantes más la línea base (~33 s por ejecución).
- **Qué se muta**: todas las líneas que cambia F-067: la preferencia
  (cargar y guardar, N1-N5), la casilla (si sale, cómo y qué hace al
  cambiar, N6-N14, N26, N27), el filtrado (N15-N22), el pintado de filas
  (N23, N24) y el estado inicial (N25).
- **Convención de las celdas**: `\|` es `|`; los espacios del texto están
  aplanados; «(nada)» es borrar el texto. El canónico es la lista `M` del
  script.

## Reproducir

Guardar el bloque del final como `mutacion_manual_f067.py` **fuera del repo**
(un `.py` fuera de `tests/`, `specs/`, `progress/` o `docs/` entraría en el
alcance de producción de `harness/alcance.py`) y, desde la raíz del repo, con
`7016870ad9b64deab5ae72ef55ef07511e39f8db` (o un descendiente que no toque
`app.js` ni esos tests) en el árbol:

```bash
PYTHONIOENCODING=utf-8 services/dedicacion-front/.venv/Scripts/python.exe <ruta>/mutacion_manual_f067.py
```

## Campaña 2 (`7016870`): 27 mutantes, 26 muertos, 1 superviviente (equivalente)

| Mutante | Fichero:línea | Texto exacto original → mutado | Resultado | Fallos (sin `-x`) | Tests que lo matan |
|---|---|---|---|---|---|
| N1 cargar: solo `true` la marca (prefs antiguas, desmarcada) | `app.js:302` | `datos.verVinculados !== false;` → `datos.verVinculados === true;` | MUERTO | 1 | test_f067_r2_sin_nada_guardado_o_con_prefs_antiguas_marcada |
| N2 cargar no lee la preferencia | `app.js:302` | `state.verVinculados = datos.verVinculados !== false;` → `(nada)` | MUERTO | 3 | test_f067_r2_se_guarda_con_las_de_la_tabla_y_vuelve, test_f067_r2_se_recupera_lo_guardado, test_f067_r4_solo_pantalla_la_preferencia_no_llega_al_registro |
| N3 cargar: cualquier valor no verdadero la desmarca | `app.js:302` | `state.verVinculados = datos.verVinculados !== false;` → `state.verVinculados = !!datos.verVinculados;` | MUERTO | 1 | test_f067_r2_sin_nada_guardado_o_con_prefs_antiguas_marcada |
| N4 guardar no escribe la preferencia | `app.js:310` | `anchos: state.anchos, verVinculados: state.verVinculados })` → `anchos: state.anchos })` | MUERTO | 3 | test_f067_r2_desmarcar_guarda_y_repinta_la_tabla, test_f067_r2_se_guarda_con_las_de_la_tabla_y_vuelve, test_f067_r4_solo_pantalla_la_preferencia_no_llega_al_registro |
| N5 guardar escribe siempre marcada | `app.js:311` | `verVinculados: state.verVinculados })` → `verVinculados: true })` | MUERTO | 2 | test_f067_r2_desmarcar_guarda_y_repinta_la_tabla, test_f067_r2_se_guarda_con_las_de_la_tabla_y_vuelve |
| N6 la casilla sale siempre | `app.js:604` | `if (hayVinculados) {` → `if (true) {` | MUERTO | 9 | test_f063_r1_las_quitadas_solas_no_sacan_ficha, test_f063_r1_misma_letra_dos_tipos_por_codigo_y_por_nombre, test_f063_r1_sin_incidencias_en_el_mes_ninguna_ficha_nueva, test_f063_r1_una_ficha_por_tipo_presente_con_letra_nombre_y_trabajadores, test_f063_r2_activo_y_sin_trabajadores_la_ficha_sigue_para_quitarlo, test_f065_r1_la_activa_a_0_desempata_por_nombre_con_la_misma_letra, test_f065_r1_la_activa_a_0_sale_por_letra_y_no_al_final, test_f065_r1_sin_filtro_activo_la_fila_no_cambia, test_f067_r5_sin_vinculados_en_el_mes_no_sale_la_casilla |
| N7 la casilla no sale nunca | `app.js:604` | `if (hayVinculados) {` → `if (false) {` | MUERTO | 5 | test_f067_r1_la_casilla_sale_marcada_junto_a_las_fichas, test_f067_r2_con_la_preferencia_desmarcada_la_casilla_sale_desmarcada, test_f067_r2_desmarcar_guarda_y_repinta_la_tabla, test_f067_r2_sin_localstorage_la_pagina_funciona_marcada, test_f067_r5_basta_un_vinculado_bajo_cualquier_linea_del_mes |
| N8 hay vinculados con una lista vacía | `app.js:603` | `(l.vinculados \|\| []).length > 0));` → `(l.vinculados \|\| []).length >= 0));` | MUERTO | 9 | test_f063_r1_las_quitadas_solas_no_sacan_ficha, test_f063_r1_misma_letra_dos_tipos_por_codigo_y_por_nombre, test_f063_r1_sin_incidencias_en_el_mes_ninguna_ficha_nueva, test_f063_r1_una_ficha_por_tipo_presente_con_letra_nombre_y_trabajadores, test_f063_r2_activo_y_sin_trabajadores_la_ficha_sigue_para_quitarlo, test_f065_r1_la_activa_a_0_desempata_por_nombre_con_la_misma_letra, test_f065_r1_la_activa_a_0_sale_por_letra_y_no_al_final, test_f065_r1_sin_filtro_activo_la_fila_no_cambia, test_f067_r5_sin_vinculados_en_el_mes_no_sale_la_casilla |
| N9 hay vinculados solo si TODAS las líneas del trabajador tienen | `app.js:603` | `t.lineas.some((l) => (l.vinculados \|\| []).length > 0));` → `t.lineas.every((l) => (l.vinculados \|\| []).length > 0));` | MUERTO | 7 | test_f063_r1_las_quitadas_solas_no_sacan_ficha, test_f063_r1_sin_incidencias_en_el_mes_ninguna_ficha_nueva, test_f063_r1_una_ficha_por_tipo_presente_con_letra_nombre_y_trabajadores, test_f063_r2_activo_y_sin_trabajadores_la_ficha_sigue_para_quitarlo, test_f065_r1_la_activa_a_0_sale_por_letra_y_no_al_final, test_f065_r1_sin_filtro_activo_la_fila_no_cambia, test_f067_r5_basta_un_vinculado_bajo_cualquier_linea_del_mes |
| N10 hay vinculados solo si TODOS los trabajadores tienen | `app.js:602` | `const hayVinculados = state.trabajadores.some(` → `const hayVinculados = state.trabajadores.every(` | MUERTO | 5 | test_f067_r1_la_casilla_sale_marcada_junto_a_las_fichas, test_f067_r2_con_la_preferencia_desmarcada_la_casilla_sale_desmarcada, test_f067_r2_desmarcar_guarda_y_repinta_la_tabla, test_f067_r2_sin_localstorage_la_pagina_funciona_marcada, test_f067_r5_basta_un_vinculado_bajo_cualquier_linea_del_mes |
| N11 la casilla sale siempre marcada | `app.js:612` | `input.checked = state.verVinculados;` → `input.checked = true;` | MUERTO | 1 | test_f067_r2_con_la_preferencia_desmarcada_la_casilla_sale_desmarcada |
| N12 el cambio guarda lo contrario | `app.js:614` | `state.verVinculados = input.checked;` → `state.verVinculados = !input.checked;` | MUERTO | 2 | test_f067_r2_desmarcar_guarda_y_repinta_la_tabla, test_f067_r2_sin_localstorage_la_pagina_funciona_marcada |
| N13 el cambio no guarda la preferencia | `app.js:615` | `guardarPrefsTabla(); renderTabla(); });` → `renderTabla(); });` | MUERTO | 1 | test_f067_r2_desmarcar_guarda_y_repinta_la_tabla |
| N14 el cambio no repinta la tabla | `app.js:615` | `guardarPrefsTabla(); renderTabla(); });` → `guardarPrefsTabla(); });` | MUERTO | 2 | test_f067_r2_desmarcar_guarda_y_repinta_la_tabla, test_f067_r2_sin_localstorage_la_pagina_funciona_marcada |
| N15 textoColumna: el modo al revés | `app.js:894` | `conVinculados ? t.lineas.flatMap((l) =>` → `!conVinculados ? t.lineas.flatMap((l) =>` | MUERTO | 2 | test_f044_r6_el_filtro_de_la_columna_ve_persona_y_cada_vinculado, test_f067_r3_tipo_recurso_desmarcada_solo_persona |
| N16 textoColumna: por defecto sin vinculados | `app.js:887` | `function textoColumna(t, clave, conVinculados = true) {` → `function textoColumna(t, clave, conVinculados = false) {` | MUERTO | 2 | test_f044_r6_el_filtro_de_la_columna_ve_persona_y_cada_vinculado, test_f067_r3_tipo_recurso_desmarcada_solo_persona |
| N17 filtrado: siempre con vinculados | `app.js:913` | `const conVinculados = state.verVinculados !== false;` → `const conVinculados = true;` | MUERTO | 3 | test_f067_r3_partida_desmarcada_solo_las_lineas, test_f067_r3_tipo_recurso_desmarcada_solo_persona, test_f067_r4_solo_pantalla_la_preferencia_no_llega_al_registro |
| N18 filtrado: sin la clave, desmarcada | `app.js:913` | `const conVinculados = state.verVinculados !== false;` → `const conVinculados = state.verVinculados === true;` | SUPERVIVIENTE | 0 | — |
| N19 Partida mira los vinculados aunque no se vean | `app.js:935` | `(conVinculados && (l.vinculados \|\| []).some((v) =>` → `(true && (l.vinculados \|\| []).some((v) =>` | MUERTO | 1 | test_f067_r3_partida_desmarcada_solo_las_lineas |
| N20 Tipo recurso: rama al revés | `app.js:942` | `if (clave === "tipo" && !conVinculados) {` → `if (clave === "tipo" && conVinculados) {` | MUERTO | 1 | test_f067_r3_tipo_recurso_desmarcada_solo_persona |
| N21 Tipo recurso: sin su rama | `app.js:942` | `if (clave === "tipo" && !conVinculados) { if (!normalizar(textoColumna(t, clave, false)).includes(filtro)) return false; continue; }` → `(nada)` | MUERTO | 1 | test_f067_r3_tipo_recurso_desmarcada_solo_persona |
| N22 Tipo recurso: la rama mira los vinculados | `app.js:943` | `textoColumna(t, clave, false)).includes(filtro)) return false;` → `textoColumna(t, clave)).includes(filtro)) return false;` | MUERTO | 1 | test_f067_r3_tipo_recurso_desmarcada_solo_persona |
| N23 construirFila: pinta siempre los vinculados | `app.js:1092` | `const vinculados = (state.verVinculados !== false && idx < n &&` → `const vinculados = (idx < n &&` | MUERTO | 3 | test_f067_r1_desmarcada_ninguna_subfila_de_vinculado_y_rowspan_cuadra, test_f067_r1_desmarcada_sin_incidencias_rowspan_de_las_lineas, test_f067_r4_solo_pantalla_la_preferencia_no_llega_al_registro |
| N24 construirFila: sin la clave, desmarcada | `app.js:1092` | `const vinculados = (state.verVinculados !== false && idx < n &&` → `const vinculados = (state.verVinculados === true && idx < n &&` | MUERTO | 2 | test_f044_r6_la_subfila_marca_los_bordes_y_el_cursor_como_las_demas, test_f044_r6_una_subfila_por_vinculado_bajo_su_linea |
| N25 el estado arranca desmarcado | `app.js:91` | `verVinculados: true,` → `verVinculados: false,` | MUERTO | 1 | test_f067_r1_el_estado_arranca_marcado |
| N26 la casilla sin la clase `check` | `app.js:606` | `casilla.className = "check chk-vinculados";` → `casilla.className = "chk-vinculados";` | MUERTO | 1 | test_f067_r1_la_casilla_sale_marcada_junto_a_las_fichas |
| N27 la casilla sin su rótulo | `app.js:619` | `texto.textContent = "Recursos vinculados";` → `texto.textContent = "";` | MUERTO | 1 | test_f067_r1_la_casilla_sale_marcada_junto_a_las_fichas |

## Análisis

- **N18 (superviviente): equivalente.** Cambia, en `trabajadoresVisibles`,
  `state.verVinculados !== false` por `state.verVinculados === true`. Las dos
  solo difieren si el valor no es booleano, y en la aplicación lo es
  siempre: arranca `true` (`const state`), `cargarPrefsTabla` escribe el
  booleano `datos.verVinculados !== false` y la casilla escribe
  `input.checked`; no hay más escrituras (lo fija
  `test_f067_r4_solo_pantalla_la_preferencia_no_llega_al_registro`). El
  `!== false` está por los arneses node de otras features cuyo `state` no
  trae la clave: en `construirFila` el mismo cambio (N24) sí muere, por los
  tests de F-044 (su `state` no la lleva y espera las subfilas). En el
  filtrado, ningún test existente combina un `state` sin la clave con
  vinculados y un filtro de Tipo recurso o Partida; matarlo exigiría un
  `state` sin la clave, que la aplicación no produce.
- **N6 y N8** (la casilla sale en un mes sin vinculados) los cazan, además
  del test de R5, nueve tests de F-063 y F-065: la casilla sería un hijo más
  de la fila de fichas. **N9** (`every` en las líneas) lo mata el test de T3
  (único vinculado bajo la segunda línea), además de los de F-063/F-065 de
  rebote; **N10** (`every` en los trabajadores), los de la casilla de F-067
  (Benito no tiene vinculados).
- **N24** lo matan solo los tests de F-044 (marcada = el cuadrante de hoy,
  sin tocar sus aserciones); **N15 y N16**, el de F-044 del texto de la
  columna y el de R3 de F-067; **N1 y N3**, el de las preferencias antiguas
  sin la clave.
- **N19-N22** (el filtrado desmarcado) los matan los dos tests de R3; N17
  (siempre con vinculados), también.

## Script

```python
# mutacion_manual_f067.py (fuera del repo, a propósito)
"""Campaña de mutación manual de F-067 sobre `app.js`.

Se ejecuta desde la raíz del repositorio. Por cada mutante: copia a un
directorio temporal, con la MISMA estructura del repo, `app.js` y
`styles.css` del front, su `tests/` y los tres ficheros ajenos que esos
tests leen (`AJENOS`); aplica la sustitución en `app.js` (el
texto original tiene que aparecer UNA sola vez; si no, aborta), comprueba la
sintaxis con `node --check`, pasa los tests que cargan el código tocado sin
`-x` y anota los que caen. El árbol de trabajo no se toca. En serie
(1 worker).
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

FRONT = Path("services/dedicacion-front")
PYTHON = str((FRONT / ".venv" / "Scripts" / "python.exe").resolve())
TESTS = ["tests/test_f067_ver_vinculados.py",
         "tests/test_f044_vinculados_front.py",
         "tests/test_f041_filtro_obra.py",
         "tests/test_f063_filtro_incidencia.py",
         "tests/test_f064_pisado_vinculados.py",
         "tests/test_f065_ficha_activa_en_su_sitio.py"]
JS = "static/js/app.js"
CSS = "static/css/styles.css"
#: Lo que los tests leen fuera del front (solo lectura): las constantes del
#: transfer que importa el arnés de F-050 y la spec de F-044 (F-064).
AJENOS = ["services/dedicacion-transfer/application/services/propuesta_partida.py",
          "services/dedicacion-transfer/application/services/reglas_porcentajes.py",
          "specs/F-044-recursos-vinculados/requirements.md"]

CARGAR = "    state.verVinculados = datos.verVinculados !== false;\n"
TIPO = ('      if (clave === "tipo" && !conVinculados) {\n'
        '        if (!normalizar(textoColumna(t, clave, false))'
        '.includes(filtro)) return false;\n'
        '        continue;\n'
        '      }\n')
M = [
    ("N1", "cargar: solo `true` la marca (prefs antiguas, desmarcada)",
     "datos.verVinculados !== false;", "datos.verVinculados === true;"),
    ("N2", "cargar no lee la preferencia", CARGAR, ""),
    ("N3", "cargar: cualquier valor no verdadero la desmarca",
     "state.verVinculados = datos.verVinculados !== false;",
     "state.verVinculados = !!datos.verVinculados;"),
    ("N4", "guardar no escribe la preferencia",
     "anchos: state.anchos,\n        verVinculados: state.verVinculados })",
     "anchos: state.anchos })"),
    ("N5", "guardar escribe siempre marcada",
     "verVinculados: state.verVinculados })", "verVinculados: true })"),
    ("N6", "la casilla sale siempre", "  if (hayVinculados) {",
     "  if (true) {"),
    ("N7", "la casilla no sale nunca", "  if (hayVinculados) {",
     "  if (false) {"),
    ("N8", "hay vinculados con una lista vacía",
     "(l.vinculados || []).length > 0));",
     "(l.vinculados || []).length >= 0));"),
    ("N9", "hay vinculados solo si TODAS las líneas del trabajador tienen",
     "    t.lineas.some((l) => (l.vinculados || []).length > 0));",
     "    t.lineas.every((l) => (l.vinculados || []).length > 0));"),
    ("N10", "hay vinculados solo si TODOS los trabajadores tienen",
     "const hayVinculados = state.trabajadores.some(",
     "const hayVinculados = state.trabajadores.every("),
    ("N11", "la casilla sale siempre marcada",
     "input.checked = state.verVinculados;", "input.checked = true;"),
    ("N12", "el cambio guarda lo contrario",
     "state.verVinculados = input.checked;",
     "state.verVinculados = !input.checked;"),
    ("N13", "el cambio no guarda la preferencia",
     "      guardarPrefsTabla();\n      renderTabla();\n    });",
     "      renderTabla();\n    });"),
    ("N14", "el cambio no repinta la tabla",
     "      guardarPrefsTabla();\n      renderTabla();\n    });",
     "      guardarPrefsTabla();\n    });"),
    ("N15", "textoColumna: el modo al revés",
     "conVinculados ? t.lineas.flatMap((l) =>",
     "!conVinculados ? t.lineas.flatMap((l) =>"),
    ("N16", "textoColumna: por defecto sin vinculados",
     "function textoColumna(t, clave, conVinculados = true) {",
     "function textoColumna(t, clave, conVinculados = false) {"),
    ("N17", "filtrado: siempre con vinculados",
     "const conVinculados = state.verVinculados !== false;",
     "const conVinculados = true;"),
    ("N18", "filtrado: sin la clave, desmarcada",
     "const conVinculados = state.verVinculados !== false;",
     "const conVinculados = state.verVinculados === true;"),
    ("N19", "Partida mira los vinculados aunque no se vean",
     "(conVinculados && (l.vinculados || []).some((v) =>",
     "(true && (l.vinculados || []).some((v) =>"),
    ("N20", "Tipo recurso: rama al revés",
     'if (clave === "tipo" && !conVinculados) {',
     'if (clave === "tipo" && conVinculados) {'),
    ("N21", "Tipo recurso: sin su rama", TIPO, ""),
    ("N22", "Tipo recurso: la rama mira los vinculados",
     "textoColumna(t, clave, false)).includes(filtro)) return false;",
     "textoColumna(t, clave)).includes(filtro)) return false;"),
    ("N23", "construirFila: pinta siempre los vinculados",
     "const vinculados = (state.verVinculados !== false && idx < n &&",
     "const vinculados = (idx < n &&"),
    ("N24", "construirFila: sin la clave, desmarcada",
     "const vinculados = (state.verVinculados !== false && idx < n &&",
     "const vinculados = (state.verVinculados === true && idx < n &&"),
    ("N25", "el estado arranca desmarcado",
     "  verVinculados: true,\n", "  verVinculados: false,\n"),
    ("N26", "la casilla sin la clase `check`",
     'casilla.className = "check chk-vinculados";',
     'casilla.className = "chk-vinculados";'),
    ("N27", "la casilla sin su rótulo",
     'texto.textContent = "Recursos vinculados";', 'texto.textContent = "";'),
]


def correr(js: str) -> tuple[str, list[str], str]:
    with tempfile.TemporaryDirectory(prefix="mm_f067_") as tmp:
        raiz = Path(tmp)
        front = raiz / FRONT
        (front / JS).parent.mkdir(parents=True, exist_ok=True)
        (front / CSS).parent.mkdir(parents=True, exist_ok=True)
        (front / JS).write_bytes(js.encode("utf-8"))
        shutil.copy2(FRONT / CSS, front / CSS)
        for ajeno in AJENOS:
            (raiz / ajeno).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ajeno, raiz / ajeno)
        shutil.copytree(FRONT / "tests", front / "tests",
                        ignore=shutil.ignore_patterns("__pycache__"))
        chk = subprocess.run(["node", "--check", JS], cwd=front,
                             capture_output=True, text=True)
        if chk.returncode != 0:
            return "SINTAXIS", [], ""
        r = subprocess.run([PYTHON, "-m", "pytest", *TESTS, "-q", "-rA",
                            "--tb=no", "-p", "no:cacheprovider"], cwd=front,
                           capture_output=True, text=True, encoding="utf-8")
        caidos = sorted(set(re.findall(
            r"^(?:FAILED|ERROR) tests/(test_\w+)\.py::(\w+)",
            r.stdout, re.MULTILINE)))
        resumen = r.stdout.strip().splitlines()[-1]
        return ("MUERTO" if r.returncode else "SUPERVIVIENTE"), \
            [t for _, t in caidos], resumen


def main() -> None:
    t0 = time.monotonic()
    original = (FRONT / JS).read_bytes().decode("utf-8")
    estado, _, resumen = correr(original)
    print(f"Línea base: {estado} · {resumen}")
    if estado != "SUPERVIVIENTE":
        sys.exit("la línea base no está en verde: la campaña no vale")
    for ide, desc, antes, despues in M:
        n = original.count(antes)
        if n != 1:
            sys.exit(f"{ide}: el original aparece {n} veces, tiene que ser 1")
        linea = original[:original.index(antes)].count("\n") + 1
        estado, caidos, resumen = correr(original.replace(antes, despues))

        def esc(s: str) -> str:
            return " ".join(s.split()).replace("|", "\\|") or "(nada)"

        print(f"| {ide} {desc} | `app.js:{linea}` | `{esc(antes)}` → "
              f"`{esc(despues)}` | {estado} | {len(caidos)} | "
              f"{', '.join(caidos) or '—'} |", flush=True)
    print(f"Tiempo: {time.monotonic() - t0:.1f} s")


if __name__ == "__main__":
    main()
```
