<!-- progress/mutacion_manual_F-064.md -->
# F-064 · Mutación manual de `app.js`

`python -m harness.mutacion` **solo muta Python** y la puerta de cobertura de
`init.sh` no mide JS (sale N/A con su motivo; `alcance_de_feature('F-064')`
da `{}`). Lo único de producción que cambia F-064 es
`services/dedicacion-front/static/js/app.js`, así que esta campaña sustituye a
la automática (mismo patrón que `progress/mutacion_manual_F-042.md`).

- **Medida sobre** `d54bd3f` (rama `feature/F-064-pisado-vinculados-marcado`,
  versión final de `app.js`, que no cambia desde `3afebc1`; tests ya con el
  arreglo B3 de la review 1). Las líneas de la tabla son las de ese commit.
- **Siempre sobre una copia**: el script copia a un directorio temporal, con
  la estructura del repo, `app.js` y `styles.css` del front, su `tests/`, las
  dos constantes del transfer que `test_f050_modal_registro.py` lee al
  importarse (`propuesta_partida.py`, `reglas_porcentajes.py`) y el
  requirements de F-044 (lo lee el test de la enmienda). Aplica la
  sustitución (el texto original tiene que aparecer **una sola vez**; si no,
  aborta), comprueba la sintaxis con `node --check` y pasa
  `tests/test_f064_pisado_vinculados.py` y `tests/test_f044_vinculados_front.py`
  **sin `-x`**, anotando los tests que caen. `git status` queda limpio después
  (comprobado).
- **Línea base** (sin mutar, en la copia): `38 passed in 9.09s` (11 de F-064
  y 27 de F-044). Una línea base en rojo aborta la campaña.
- **Workers y coste**: en serie (**1 worker**), **214,6 s** de reloj para
  15 mutantes más la línea base: **~13,4 s por ejecución** (cada una arranca
  node unas 40 veces).
- **Antes del arreglo B3** sobrevivía el R2 de la review
  (`c.vinculado !== undefined`, aquí M3): el doble del conflicto de un
  trabajador no llevaba la clave `vinculado`, mientras que el `asdict` real del
  transfer la manda a `null`. Ahora la lleva (`d54bd3f`) y M3 muere.
- **Convención de las celdas**: `\|` es `|`; los espacios del texto están
  aplanados; «(nada)» es borrar el texto. El canónico es la lista `M` del
  script.

## Reproducir

Guardar el bloque del final como `mutacion_manual_f064.py` **fuera del repo**
(un `.py` fuera de `tests/`, `specs/`, `progress/` o `docs/` entraría en el
alcance de producción de `harness/alcance.py`) y, desde la raíz del repo:

```bash
PYTHONIOENCODING=utf-8 services/dedicacion-front/.venv/Scripts/python.exe <ruta>/mutacion_manual_f064.py
```

## Campaña (`d54bd3f`): 15 mutantes, 15 muertos, 0 supervivientes

| Mutante | Fichero:línea | Texto exacto original → mutado | Resultado | Fallos (sin `-x`) | Tests que lo matan |
|---|---|---|---|---|---|
| M1 sin mirar si es vinculado | `app.js:3352` | `return Boolean(c.vinculado) && (c.motivo \|\| "pisado") === "pisado";` → `return (c.motivo \|\| "pisado") === "pisado";` | MUERTO | 6 | test_f064_al_abrir_solo_el_pisado_de_vinculado_sale_marcado, test_f064_la_casilla_marcada_lleva_checked_en_el_html, test_f064_marcada_por_defecto_solo_el_pisado_de_vinculado, test_f064_registrar_por_defecto_manda_los_pisados_de_vinculado, test_f064_sin_vinculados_el_modal_de_hoy_todo_desmarcado, test_f064_un_preflight_nuevo_vuelve_al_valor_por_defecto |
| M2 sin motivo deja de ser pisado | `app.js:3352` | `return Boolean(c.vinculado) && (c.motivo \|\| "pisado") === "pisado";` → `return Boolean(c.vinculado) && c.motivo === "pisado";` | MUERTO | 5 | test_f064_al_abrir_solo_el_pisado_de_vinculado_sale_marcado, test_f064_desmarcada_sigue_desmarcada_al_repetir_el_preflight, test_f064_marcada_por_defecto_solo_el_pisado_de_vinculado, test_f064_registrar_por_defecto_manda_los_pisados_de_vinculado, test_f064_un_preflight_nuevo_vuelve_al_valor_por_defecto |
| M3 R2 de la review: null cuenta como vinculado | `app.js:3352` | `return Boolean(c.vinculado) && (c.motivo \|\| "pisado") === "pisado";` → `return c.vinculado !== undefined && (c.motivo \|\| "pisado") === "pisado";` | MUERTO | 6 | test_f064_al_abrir_solo_el_pisado_de_vinculado_sale_marcado, test_f064_la_casilla_marcada_lleva_checked_en_el_html, test_f064_marcada_por_defecto_solo_el_pisado_de_vinculado, test_f064_registrar_por_defecto_manda_los_pisados_de_vinculado, test_f064_sin_vinculados_el_modal_de_hoy_todo_desmarcado, test_f064_un_preflight_nuevo_vuelve_al_valor_por_defecto |
| M4 siempre marcada | `app.js:3352` | `return Boolean(c.vinculado) && (c.motivo \|\| "pisado") === "pisado";` → `return true;` | MUERTO | 8 | test_f064_al_abrir_solo_el_pisado_de_vinculado_sale_marcado, test_f064_desmarcada_sigue_desmarcada_al_repetir_el_preflight, test_f064_la_casilla_marcada_lleva_checked_en_el_html, test_f064_marcada_por_defecto_solo_el_pisado_de_vinculado, test_f064_registrar_manda_exactamente_las_marcadas, test_f064_registrar_por_defecto_manda_los_pisados_de_vinculado, test_f064_sin_vinculados_el_modal_de_hoy_todo_desmarcado, test_f064_un_preflight_nuevo_vuelve_al_valor_por_defecto |
| M5 nunca marcada | `app.js:3352` | `return Boolean(c.vinculado) && (c.motivo \|\| "pisado") === "pisado";` → `return false;` | MUERTO | 8 | test_f064_al_abrir_solo_el_pisado_de_vinculado_sale_marcado, test_f064_desmarcada_sigue_desmarcada_al_repetir_el_preflight, test_f064_la_casilla_marcada_lleva_checked_en_el_html, test_f064_marcada_por_defecto_solo_el_pisado_de_vinculado, test_f064_registrar_manda_exactamente_las_marcadas, test_f064_registrar_por_defecto_manda_los_pisados_de_vinculado, test_f064_repetir_una_obra_no_toca_lo_desmarcado_en_otra, test_f064_un_preflight_nuevo_vuelve_al_valor_por_defecto |
| M6 && -> || en la condición | `app.js:3352` | `return Boolean(c.vinculado) && (c.motivo \|\| "pisado") === "pisado";` → `return Boolean(c.vinculado) \|\| (c.motivo \|\| "pisado") === "pisado";` | MUERTO | 8 | test_f064_al_abrir_solo_el_pisado_de_vinculado_sale_marcado, test_f064_desmarcada_sigue_desmarcada_al_repetir_el_preflight, test_f064_la_casilla_marcada_lleva_checked_en_el_html, test_f064_marcada_por_defecto_solo_el_pisado_de_vinculado, test_f064_registrar_manda_exactamente_las_marcadas, test_f064_registrar_por_defecto_manda_los_pisados_de_vinculado, test_f064_sin_vinculados_el_modal_de_hoy_todo_desmarcado, test_f064_un_preflight_nuevo_vuelve_al_valor_por_defecto |
| M7 === -> !== en el motivo | `app.js:3352` | `return Boolean(c.vinculado) && (c.motivo \|\| "pisado") === "pisado";` → `return Boolean(c.vinculado) && (c.motivo \|\| "pisado") !== "pisado";` | MUERTO | 8 | test_f064_al_abrir_solo_el_pisado_de_vinculado_sale_marcado, test_f064_desmarcada_sigue_desmarcada_al_repetir_el_preflight, test_f064_la_casilla_marcada_lleva_checked_en_el_html, test_f064_marcada_por_defecto_solo_el_pisado_de_vinculado, test_f064_registrar_manda_exactamente_las_marcadas, test_f064_registrar_por_defecto_manda_los_pisados_de_vinculado, test_f064_repetir_una_obra_no_toca_lo_desmarcado_en_otra, test_f064_un_preflight_nuevo_vuelve_al_valor_por_defecto |
| M8 sin mirar vistas | `app.js:3308` | `if (marcadaPorDefecto(c) && !registro.vistas.has(c.clave)) {` → `if (marcadaPorDefecto(c)) {` | MUERTO | 5 | test_f064_desmarcada_sigue_desmarcada_al_repetir_el_preflight, test_f064_marcada_por_defecto_es_pura_y_la_usa_el_modal, test_f064_registrar_manda_exactamente_las_marcadas, test_f064_repetir_una_obra_no_toca_lo_desmarcado_en_otra, test_f064_un_preflight_nuevo_vuelve_al_valor_por_defecto |
| M9 R1 de la review: && -> || en el if | `app.js:3308` | `if (marcadaPorDefecto(c) && !registro.vistas.has(c.clave)) {` → `if (marcadaPorDefecto(c) \|\| !registro.vistas.has(c.clave)) {` | MUERTO | 9 | test_f064_al_abrir_solo_el_pisado_de_vinculado_sale_marcado, test_f064_desmarcada_sigue_desmarcada_al_repetir_el_preflight, test_f064_la_casilla_marcada_lleva_checked_en_el_html, test_f064_marcada_por_defecto_es_pura_y_la_usa_el_modal, test_f064_registrar_manda_exactamente_las_marcadas, test_f064_registrar_por_defecto_manda_los_pisados_de_vinculado, test_f064_repetir_una_obra_no_toca_lo_desmarcado_en_otra, test_f064_sin_vinculados_el_modal_de_hoy_todo_desmarcado, test_f064_un_preflight_nuevo_vuelve_al_valor_por_defecto |
| M10 vistas al revés (sin !) | `app.js:3308` | `if (marcadaPorDefecto(c) && !registro.vistas.has(c.clave)) {` → `if (marcadaPorDefecto(c) && registro.vistas.has(c.clave)) {` | MUERTO | 8 | test_f064_al_abrir_solo_el_pisado_de_vinculado_sale_marcado, test_f064_desmarcada_sigue_desmarcada_al_repetir_el_preflight, test_f064_la_casilla_marcada_lleva_checked_en_el_html, test_f064_marcada_por_defecto_es_pura_y_la_usa_el_modal, test_f064_registrar_manda_exactamente_las_marcadas, test_f064_registrar_por_defecto_manda_los_pisados_de_vinculado, test_f064_repetir_una_obra_no_toca_lo_desmarcado_en_otra, test_f064_un_preflight_nuevo_vuelve_al_valor_por_defecto |
| M11 no anota la clave en vistas | `app.js:3309` | `registro.vistas.add(c.clave);` → `(nada)` | MUERTO | 4 | test_f064_desmarcada_sigue_desmarcada_al_repetir_el_preflight, test_f064_registrar_manda_exactamente_las_marcadas, test_f064_repetir_una_obra_no_toca_lo_desmarcado_en_otra, test_f064_un_preflight_nuevo_vuelve_al_valor_por_defecto |
| M12 no marca la casilla | `app.js:3309` | `registro.vistas.add(c.clave); registro.pisar.add(c.clave);` → `registro.vistas.add(c.clave);` | MUERTO | 7 | test_f064_al_abrir_solo_el_pisado_de_vinculado_sale_marcado, test_f064_desmarcada_sigue_desmarcada_al_repetir_el_preflight, test_f064_la_casilla_marcada_lleva_checked_en_el_html, test_f064_registrar_manda_exactamente_las_marcadas, test_f064_registrar_por_defecto_manda_los_pisados_de_vinculado, test_f064_repetir_una_obra_no_toca_lo_desmarcado_en_otra, test_f064_un_preflight_nuevo_vuelve_al_valor_por_defecto |
| M13 el preflight nuevo no vacía vistas | `app.js:2929` | `registro.vistas = new Set(); registro.pf = pf;` → `registro.pf = pf;` | MUERTO | 1 | test_f064_un_preflight_nuevo_vuelve_al_valor_por_defecto |
| M14 el preflight nuevo no vacía pisar | `app.js:2928` | `registro.pisar = new Set(); registro.vistas = new Set();` → `registro.vistas = new Set();` | MUERTO | 1 | test_f064_un_preflight_nuevo_vuelve_al_valor_por_defecto |
| M15 registro sin vistas de partida | `app.js:2885` | `pisar: new Set(), vistas: new Set(), trabajadorIde` → `pisar: new Set(), trabajadorIde` | MUERTO | 1 | test_f044_r31_sus_avisos_en_la_lista_de_siempre_con_tipo_y_codigo |

## Análisis

- **No sobrevive ninguno.** M3 (el R2 de la review) era el único superviviente
  de la review 1, y lo mata ahora la forma real del conflicto de un trabajador
  (`"vinculado": null`) en cinco tests de comportamiento y en el unitario de
  `marcadaPorDefecto`.
- **M13 y M14** (el preflight nuevo no vacía `vistas` o `pisar`) los mata un
  solo test, `test_f064_un_preflight_nuevo_vuelve_al_valor_por_defecto`. Es el
  único escenario que abre el modal dos veces, y es lo que fija el criterio 2.
- **M15** (`registro` sin `vistas` de partida) es equivalente dentro del flujo
  de F-064, porque toda apertura pasa por `registroPreflight`, que crea
  `vistas` antes de pintar. Lo mata
  `test_f044_r31_sus_avisos_en_la_lista_de_siempre_con_tipo_y_codigo`, que
  pinta directamente un pisado de vinculado con el `registro` de partida: sin
  `vistas`, `pintarModalPreflight` daría `TypeError`. Por eso la campaña pasa
  también ese fichero.
- **M8** también lo mata el estático
  `test_f064_marcada_por_defecto_es_pura_y_la_usa_el_modal`, pero no solo él:
  caen además cuatro tests de comportamiento.

## Script

```python
# mutacion_manual_f064.py (fuera del repo, a propósito)
"""Campaña de mutación manual de F-064 sobre `app.js`.

Se ejecuta desde la raíz del repositorio. Por cada mutante: copia a un
directorio temporal, con la MISMA estructura del repo, `app.js` y
`styles.css` del front, su `tests/`, las dos constantes del transfer que
`test_f050_modal_registro.py` lee al importarse y el requirements de F-044
(lo lee el test de la enmienda); aplica la sustitución en `app.js` (el texto
original tiene que aparecer UNA sola vez; si no, aborta), comprueba la
sintaxis con `node --check`, pasa los dos ficheros de test sin `-x` y anota
los tests que caen. El árbol de trabajo no se toca. En serie (1 worker).
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
TESTS = ["tests/test_f064_pisado_vinculados.py",
         "tests/test_f044_vinculados_front.py"]
JS = "static/js/app.js"
COPIAS = [
    "services/dedicacion-front/static/css/styles.css",
    "services/dedicacion-transfer/application/services/propuesta_partida.py",
    "services/dedicacion-transfer/application/services/reglas_porcentajes.py",
    "specs/F-044-recursos-vinculados/requirements.md",
]

RET = 'return Boolean(c.vinculado) && (c.motivo || "pisado") === "pisado";'
IF = "if (marcadaPorDefecto(c) && !registro.vistas.has(c.clave)) {"
M = [
    ("M1", "sin mirar si es vinculado", RET,
     'return (c.motivo || "pisado") === "pisado";'),
    ("M2", "sin motivo deja de ser pisado", RET,
     'return Boolean(c.vinculado) && c.motivo === "pisado";'),
    ("M3", "R2 de la review: null cuenta como vinculado", RET,
     'return c.vinculado !== undefined && (c.motivo || "pisado") === "pisado";'),
    ("M4", "siempre marcada", RET, "return true;"),
    ("M5", "nunca marcada", RET, "return false;"),
    ("M6", "&& -> || en la condición", RET,
     'return Boolean(c.vinculado) || (c.motivo || "pisado") === "pisado";'),
    ("M7", "=== -> !== en el motivo", RET,
     'return Boolean(c.vinculado) && (c.motivo || "pisado") !== "pisado";'),
    ("M8", "sin mirar vistas", IF, "if (marcadaPorDefecto(c)) {"),
    ("M9", "R1 de la review: && -> || en el if", IF,
     "if (marcadaPorDefecto(c) || !registro.vistas.has(c.clave)) {"),
    ("M10", "vistas al revés (sin !)", IF,
     "if (marcadaPorDefecto(c) && registro.vistas.has(c.clave)) {"),
    ("M11", "no anota la clave en vistas",
     "        registro.vistas.add(c.clave);\n", ""),
    ("M12", "no marca la casilla",
     "        registro.vistas.add(c.clave);\n        registro.pisar.add(c.clave);\n",
     "        registro.vistas.add(c.clave);\n"),
    ("M13", "el preflight nuevo no vacía vistas",
     "    registro.vistas = new Set();\n    registro.pf = pf;",
     "    registro.pf = pf;"),
    ("M14", "el preflight nuevo no vacía pisar",
     "    registro.pisar = new Set();\n    registro.vistas = new Set();",
     "    registro.vistas = new Set();"),
    ("M15", "registro sin vistas de partida",
     "pisar: new Set(), vistas: new Set(), trabajadorIde",
     "pisar: new Set(), trabajadorIde"),
]


def correr(js: str) -> tuple[str, list[str], str]:
    with tempfile.TemporaryDirectory(prefix="mm_f064_") as tmp:
        raiz = Path(tmp)
        front = raiz / FRONT
        (front / JS).parent.mkdir(parents=True, exist_ok=True)
        (front / JS).write_bytes(js.encode("utf-8"))
        for rel in COPIAS:
            (raiz / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(rel, raiz / rel)
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
