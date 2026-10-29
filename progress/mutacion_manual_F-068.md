<!-- progress/mutacion_manual_F-068.md -->
# F-068 · Mutación manual de `app.js`

`python -m harness.mutacion` **solo muta Python** y la puerta de cobertura de
`init.sh` no mide JS. Lo único del front que cambia F-068 es una entrada del
mapa de rótulos de `rotuloOrigen` en
`services/dedicacion-front/static/js/app.js` (T11, R20): `capitulo_ci4:
"capítulo CI.4 en empate"`, más su comentario. Esta campaña sustituye a la
automática para esa línea (mismo patrón que `progress/mutacion_manual_F-067.md`).

- **Medida sobre** `e28dbd2ac4f827fdc870285ae39c5f2bd037bb4b` (rama
  `feature/F-068-propuesta-vinculado-como-titular`). `app.js` y `tests/` del
  front son los de `c3a91c84267a2e7667dd36c84b1ede9fc003708b` (T11): ningún
  commit posterior los toca. Las líneas de la tabla son las de ese `app.js`.
- **Siempre sobre una copia**: el script copia a un directorio temporal, con
  la estructura del repo, `app.js` y `styles.css` del front, su `tests/` y
  los tres ficheros ajenos que esos tests leen (dos módulos del transfer de
  los que el arnés de F-050 saca constantes y el `requirements.md` de F-044
  que mira F-064). Aplica la sustitución (el original tiene que aparecer
  **una sola vez**; si no, aborta), comprueba la sintaxis con
  `node --check` y pasa los cuatro ficheros de test que cargan
  `rotuloOrigen` en la subfila y en el modal (F-068, F-044, F-055 y F-064)
  **sin `-x`**, anotando los que caen. `git status` sin cambios después
  (comprobado).
- **Línea base** (sin mutar, en la copia): `67 passed in 25.94s`. Una línea
  base en rojo aborta la campaña.
- **Workers y coste**: en serie (**1 worker**), **233,4 s** de reloj para 5
  mutantes más la línea base.
- **Qué se muta**: la única línea con lógica que añade F-068: quitar la
  entrada (N1), dejar el rótulo vacío (N2, cae al método crudo por el `||`),
  recortarlo (N3), cambiar la clave (N4) y darle el rótulo de otro método
  (N5). El comentario no se muta.
- **Convención de las celdas**: `\|` es `|`; los espacios del texto están
  aplanados; «(nada)» es borrar el texto. El canónico es la lista `M` del
  script. «Fallos» cuenta funciones de test (un parametrizado cuenta una).

## Reproducir

Guardar el bloque del final como `mutacion_manual_f068.py` **fuera del repo**
(un `.py` fuera de `tests/`, `specs/`, `progress/` o `docs/` entraría en el
alcance de producción de `harness/alcance.py`) y, desde la raíz del repo, con
`e28dbd2ac4f827fdc870285ae39c5f2bd037bb4b` (o un descendiente que no toque
`app.js` ni los tests del front) en el árbol:

```bash
PYTHONIOENCODING=utf-8 services/dedicacion-front/.venv/Scripts/python.exe <ruta>/mutacion_manual_f068.py
```

## Campaña 1 (`e28dbd2`): 5 mutantes, 5 muertos, 0 supervivientes

| Mutante | Fichero:línea | Texto exacto original → mutado | Resultado | Fallos (sin `-x`) | Tests que lo matan |
|---|---|---|---|---|---|
| N1 sin la entrada `capitulo_ci4` (sale el método crudo) | `app.js:229` | `capitulo_ci4: "capítulo CI.4 en empate",` → `(nada)` | MUERTO | 3 | test_f068_r20_el_modal_rotula_la_partida_del_vinculado, test_f068_r20_la_subfila_rotula_su_propuesta, test_f068_r20_rotulo_del_capitulo_ci4 |
| N2 rótulo vacío (cae al método crudo por el `||`) | `app.js:229` | `capitulo_ci4: "capítulo CI.4 en empate",` → `capitulo_ci4: "",` | MUERTO | 3 | test_f068_r20_el_modal_rotula_la_partida_del_vinculado, test_f068_r20_la_subfila_rotula_su_propuesta, test_f068_r20_rotulo_del_capitulo_ci4 |
| N3 rótulo recortado | `app.js:229` | `capitulo_ci4: "capítulo CI.4 en empate",` → `capitulo_ci4: "capítulo CI.4",` | MUERTO | 3 | test_f068_r20_el_modal_rotula_la_partida_del_vinculado, test_f068_r20_la_subfila_rotula_su_propuesta, test_f068_r20_rotulo_del_capitulo_ci4 |
| N4 la clave con otro nombre | `app.js:229` | `capitulo_ci4: "capítulo CI.4 en empate",` → `capitulo_ci_4: "capítulo CI.4 en empate",` | MUERTO | 3 | test_f068_r20_el_modal_rotula_la_partida_del_vinculado, test_f068_r20_la_subfila_rotula_su_propuesta, test_f068_r20_rotulo_del_capitulo_ci4 |
| N5 el rótulo de otro método (el de su cuenta) | `app.js:229` | `capitulo_ci4: "capítulo CI.4 en empate",` → `capitulo_ci4: "CI del tipo",` | MUERTO | 3 | test_f068_r20_el_modal_rotula_la_partida_del_vinculado, test_f068_r20_la_subfila_rotula_su_propuesta, test_f068_r20_rotulo_del_capitulo_ci4 |

## Análisis

- Sin supervivientes. Los cinco los matan los tres tests de R20 de
  `test_f068_front.py`: el de `rotuloOrigen` directo, el de la subfila del
  cuadrante (`construirFila`, código real con el arnés de F-044) y el del
  modal de registro (código real con el de F-050). Ningún test de F-044,
  F-055 ni F-064 cae: los rótulos de siempre no cambian (R20, «los demás con
  sus rótulos de siempre», que fija además
  `test_f068_r20_los_demas_metodos_con_sus_rotulos_de_siempre`).

## Script

```python
# mutacion_manual_f068.py (fuera del repo, a propósito)
"""Campaña de mutación manual de F-068 sobre `app.js`.

Se ejecuta desde la raíz del repositorio. Por cada mutante: copia a un
directorio temporal, con la MISMA estructura del repo, `app.js` y
`styles.css` del front, su `tests/` y los ficheros ajenos que esos tests
leen (`AJENOS`); aplica la sustitución en `app.js` (el texto original tiene
que aparecer UNA sola vez; si no, aborta), comprueba la sintaxis con
`node --check`, pasa los tests que cargan `rotuloOrigen` sin `-x` y anota
los que caen. El árbol de trabajo no se toca. En serie (1 worker).
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
TESTS = ["tests/test_f068_front.py",
         "tests/test_f044_vinculados_front.py",
         "tests/test_f055_propuesta_celda.py",
         "tests/test_f064_pisado_vinculados.py"]
JS = "static/js/app.js"
CSS = "static/css/styles.css"
#: Lo que los tests leen fuera del front (solo lectura): las constantes del
#: transfer que importa el arnés de F-050 y la spec de F-044 (F-064).
AJENOS = ["services/dedicacion-transfer/application/services/propuesta_partida.py",
          "services/dedicacion-transfer/application/services/reglas_porcentajes.py",
          "specs/F-044-recursos-vinculados/requirements.md"]

ENTRADA = '    capitulo_ci4: "capítulo CI.4 en empate",\n'
M = [
    ("N1", "sin la entrada `capitulo_ci4` (sale el método crudo)",
     ENTRADA, ""),
    ("N2", "rótulo vacío (cae al método crudo por el `||`)",
     'capitulo_ci4: "capítulo CI.4 en empate",', 'capitulo_ci4: "",'),
    ("N3", "rótulo recortado",
     'capitulo_ci4: "capítulo CI.4 en empate",',
     'capitulo_ci4: "capítulo CI.4",'),
    ("N4", "la clave con otro nombre",
     'capitulo_ci4: "capítulo CI.4 en empate",',
     'capitulo_ci_4: "capítulo CI.4 en empate",'),
    ("N5", "el rótulo de otro método (el de su cuenta)",
     'capitulo_ci4: "capítulo CI.4 en empate",',
     'capitulo_ci4: "CI del tipo",'),
]


def correr(js: str) -> tuple[str, list[str], str]:
    with tempfile.TemporaryDirectory(prefix="mm_f068_") as tmp:
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
                             capture_output=True, text=True, check=False)
        if chk.returncode != 0:
            return "SINTAXIS", [], ""
        r = subprocess.run([PYTHON, "-m", "pytest", *TESTS, "-q", "-rA",
                            "--tb=no", "-p", "no:cacheprovider"], cwd=front,
                           capture_output=True, text=True, encoding="utf-8",
                           check=False)
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
