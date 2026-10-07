# F-041 · Mutación manual de `app.js`

`python -m harness.mutacion` **solo muta Python**: para F-041 da «ALCANCE VACÍO
en F-041: ni una línea de producción que mutar» (salida real, 2026-10-06) y no
escribe informe, porque lo único de producción que cambia es
`services/dedicacion-front/static/js/app.js`. La puerta de cobertura de
`init.sh` tampoco mide JS (sale N/A con su motivo). Esta campaña la sustituye
(design §7, patrón de `progress/mutacion_manual_F-035.md`).

- **Medida sobre** `1a0019c` (rama `feature/F-041-filtro-obra-postventa`, tras
  T4). Las líneas de la tabla son las de ese commit. **Repetida sobre
  `93c1a0e`** (tras cambiar `zip` por `itertools.pairwise` en el test de R5,
  aviso RUF007): línea base `26 passed in 5.16s` y tabla **idéntica fila a
  fila** (comparada con `diff`).
- **Siempre sobre una copia**: el script copia `static/js/app.js` y `tests/` del
  front a un directorio temporal, aplica la sustitución (el texto original
  tiene que aparecer **una sola vez**; si no, aborta), comprueba la sintaxis con
  `node --check`, pasa `tests/test_f041_filtro_obra.py` **sin `-x`** y anota
  los tests que caen. El árbol de trabajo no se toca: `git status` limpio
  después (comprobado).
- **Línea base** (sin mutar, en la copia): `26 passed in 5.90s`. Una línea
  base en rojo aborta la campaña.
- **Coste**: 2 min 31 s de reloj para 20 mutantes + línea base, en serie
  (1 worker): **~7,2 s por mutante**, coherente con lo que tarda la suite de
  F-041 (~6 s, que arranca node 14 veces). No es una campaña sospechosa por
  rapidez.
- **Convención de las celdas**: `\|` es `|`. El texto canónico es el de la
  lista `M` del script de abajo.

## Reproducir

Guardar el bloque del final como `mutacion_manual_f041.py` **fuera del repo**
(un `.py` fuera de `tests/`, `specs/`, `progress/` o `docs/` entraría en el
alcance de producción de `harness/alcance.py`) y, desde la raíz del repo:

```bash
PYTHONIOENCODING=utf-8 python <ruta>/mutacion_manual_f041.py
```

Imprime la línea base y una fila por mutante, con el formato de la tabla.

## Campaña (`1a0019c`): 20 mutantes, 20 muertos, 0 supervivientes

Incluye los ocho mínimos de design §7 (M1, M2, M3, M4, M5, M6, M7, M8) y doce
más sobre cada línea cambiada por F-041.

| Mutante | Fichero:línea | Texto exacto original → mutado | Resultado | Fallos (sin `-x`) | Tests que lo matan |
|---|---|---|---|---|---|
| M1 etiquetaObra sin Postv- | `app.js:88` | `return (esPostventa ? "Postv-" : "") + cod;` → `return (esPostventa ? "" : "") + cod;` | MUERTO | 10 | test_f041_r10_catalogo_en_node, test_f041_r11_columna_y_completar_parten_del_mismo_texto, test_f041_r12_etiqueta_exacta_primero, test_f041_r1_etiqueta_en_una_sola_funcion, test_f041_r1_r2_etiqueta_y_texto_en_node, test_f041_r3_postv_literal_solo_en_etiqueta_obra, test_f041_r5_pos_y_completando_acota_letra_a_letra, test_f041_r6_ignora_mayusculas_y_tildes, test_f041_r7_casa_con_cualquier_parte_del_texto_visible, test_f041_r9_buscador_global_encuentra_postventa |
| M2 textoObra sin el espacio | `app.js:94` | `etiquetaObra(cod, esPostventa) + " " + (descripcion \|\| "")` → `etiquetaObra(cod, esPostventa) + "" + (descripcion \|\| "")` | MUERTO | 5 | test_f041_r10_catalogo_en_node, test_f041_r1_r2_etiqueta_y_texto_en_node, test_f041_r2_texto_visible_usa_la_etiqueta, test_f041_r6_ignora_mayusculas_y_tildes, test_f041_r7_casa_con_cualquier_parte_del_texto_visible |
| M3 lineaCasa: includes -> startsWith | `app.js:100` | `l.es_postventa)).includes(q);` → `l.es_postventa)).startsWith(q);` | MUERTO | 6 | test_f041_r11_columna_y_completar_parten_del_mismo_texto, test_f041_r13_var_29_casa_como_cualquier_obra, test_f041_r2_linea_casa_con_su_texto_visible, test_f041_r5_pos_y_completando_acota_letra_a_letra, test_f041_r6_ignora_mayusculas_y_tildes, test_f041_r7_casa_con_cualquier_parte_del_texto_visible |
| M4 columna: some -> every | `app.js:517` | `t.lineas.some((l) => lineaCasa(l, filtro))` → `t.lineas.every((l) => lineaCasa(l, filtro))` | MUERTO | 8 | test_f041_r10_d1_postventa_no_casa, test_f041_r11_columna_y_completar_parten_del_mismo_texto, test_f041_r13_var_29_casa_como_cualquier_obra, test_f041_r4_d2_naves_postv_no_casa_a_caballo, test_f041_r4_la_columna_casa_por_linea, test_f041_r5_pos_y_completando_acota_letra_a_letra, test_f041_r6_ignora_mayusculas_y_tildes, test_f041_r7_casa_con_cualquier_parte_del_texto_visible |
| M5 filtro vacío: continue -> return false | `app.js:514` | `if (!filtro) continue;` → `if (!filtro) return false;` | MUERTO | 7 | test_f041_r11_columna_y_completar_parten_del_mismo_texto, test_f041_r13_var_29_casa_como_cualquier_obra, test_f041_r5_pos_y_completando_acota_letra_a_letra, test_f041_r6_ignora_mayusculas_y_tildes, test_f041_r7_casa_con_cualquier_parte_del_texto_visible, test_f041_r8_sin_filtro_las_mismas_filas_y_orden, test_f041_r9_buscador_global_encuentra_postventa |
| M6 pajar sin textoObra | `app.js:526` | `t.lineas.map((l) => textoObra(l.cod, l.descripcion, l.es_postventa)).join(" ")` → `t.lineas.map((l) => l.cod + " " + l.descripcion).join(" ")` | MUERTO | 2 | test_f041_r9_buscador_global_encuentra_postventa, test_f041_r9_buscador_global_usa_el_texto_visible |
| M7 clave de la entrada Postv- con false | `app.js:266` | `clave: normalizar(textoObra(o.cod, o.descripcion, true)),` → `clave: normalizar(textoObra(o.cod, o.descripcion, false)),` | MUERTO | 4 | test_f041_r10_catalogo_en_node, test_f041_r10_la_clave_del_catalogo_es_el_texto_visible, test_f041_r11_columna_y_completar_parten_del_mismo_texto, test_f041_r12_etiqueta_exacta_primero |
| M8 clave normal sin normalizar | `app.js:260` | `clave: normalizar(textoObra(o.cod, o.descripcion, false)),` → `clave: textoObra(o.cod, o.descripcion, false),` | MUERTO | 4 | test_f041_r10_catalogo_en_node, test_f041_r10_la_clave_del_catalogo_es_el_texto_visible, test_f041_r11_columna_y_completar_parten_del_mismo_texto, test_f041_r13_var_29_casa_como_cualquier_obra |
| M9 clave Postv- sin normalizar | `app.js:266` | `clave: normalizar(textoObra(o.cod, o.descripcion, true)),` → `clave: textoObra(o.cod, o.descripcion, true),` | MUERTO | 4 | test_f041_r10_catalogo_en_node, test_f041_r10_la_clave_del_catalogo_es_el_texto_visible, test_f041_r11_columna_y_completar_parten_del_mismo_texto, test_f041_r12_etiqueta_exacta_primero |
| M10 lineaCasa sin normalizar | `app.js:100` | `return normalizar(textoObra(l.cod, l.descripcion, l.es_postventa)).includes(q);` → `return textoObra(l.cod, l.descripcion, l.es_postventa).includes(q);` | MUERTO | 6 | test_f041_r11_columna_y_completar_parten_del_mismo_texto, test_f041_r13_var_29_casa_como_cualquier_obra, test_f041_r2_linea_casa_con_su_texto_visible, test_f041_r5_pos_y_completando_acota_letra_a_letra, test_f041_r6_ignora_mayusculas_y_tildes, test_f041_r7_casa_con_cualquier_parte_del_texto_visible |
| M11 lineaCasa ignora es_postventa | `app.js:100` | `return normalizar(textoObra(l.cod, l.descripcion, l.es_postventa)).includes(q);` → `return normalizar(textoObra(l.cod, l.descripcion, false)).includes(q);` | MUERTO | 5 | test_f041_r11_columna_y_completar_parten_del_mismo_texto, test_f041_r2_linea_casa_con_su_texto_visible, test_f041_r5_pos_y_completando_acota_letra_a_letra, test_f041_r6_ignora_mayusculas_y_tildes, test_f041_r7_casa_con_cualquier_parte_del_texto_visible |
| M12 lineaCasa sin descripción | `app.js:100` | `return normalizar(textoObra(l.cod, l.descripcion, l.es_postventa)).includes(q);` → `return normalizar(textoObra(l.cod, "", l.es_postventa)).includes(q);` | MUERTO | 6 | test_f041_r11_columna_y_completar_parten_del_mismo_texto, test_f041_r13_var_29_casa_como_cualquier_obra, test_f041_r2_linea_casa_con_su_texto_visible, test_f041_r5_pos_y_completando_acota_letra_a_letra, test_f041_r6_ignora_mayusculas_y_tildes, test_f041_r7_casa_con_cualquier_parte_del_texto_visible |
| M13 vuelve el alias postventa (D1) | `app.js:266` | `clave: normalizar(textoObra(o.cod, o.descripcion, true)),` → `clave: normalizar("postventa " + textoObra(o.cod, o.descripcion, true)),` | MUERTO | 4 | test_f041_r10_catalogo_en_node, test_f041_r10_d1_postventa_no_casa, test_f041_r10_la_clave_del_catalogo_es_el_texto_visible, test_f041_r11_columna_y_completar_parten_del_mismo_texto |
| M14 chip de la tabla con su propio Postv- | `app.js:879` | `${escapeHtml(etiquetaObra(l.cod, l.es_postventa))}` → `${l.es_postventa ? "Postv-" : ""}${escapeHtml(l.cod)}` | MUERTO | 2 | test_f041_r3_los_chips_y_el_catalogo_usan_etiqueta_obra, test_f041_r3_postv_literal_solo_en_etiqueta_obra |
| M15 chip del editor con su propio Postv- | `app.js:1050` | `cod.textContent = etiquetaObra(linea.cod, linea.es_postventa);` → `cod.textContent = (linea.es_postventa ? "Postv-" : "") + linea.cod;` | MUERTO | 2 | test_f041_r3_los_chips_y_el_catalogo_usan_etiqueta_obra, test_f041_r3_postv_literal_solo_en_etiqueta_obra |
| M16 la columna de obras cae a textoColumna | `app.js:516` | `const casa = clave === "asignaciones"` → `const casa = clave === "asignacionesX"` | MUERTO | 6 | test_f041_r11_columna_y_completar_parten_del_mismo_texto, test_f041_r13_var_29_casa_como_cualquier_obra, test_f041_r4_la_columna_casa_por_linea, test_f041_r5_pos_y_completando_acota_letra_a_letra, test_f041_r6_ignora_mayusculas_y_tildes, test_f041_r7_casa_con_cualquier_parte_del_texto_visible |
| M17 entrada normal con etiqueta Postv- | `app.js:259` | `cod: etiquetaObra(o.cod, false),` → `cod: etiquetaObra(o.cod, true),` | MUERTO | 4 | test_f041_r10_catalogo_en_node, test_f041_r12_etiqueta_exacta_primero, test_f041_r13_var_29_casa_como_cualquier_obra, test_f041_r3_los_chips_y_el_catalogo_usan_etiqueta_obra |
| M18 entrada Postv- con etiqueta normal | `app.js:265` | `cod: etiquetaObra(o.cod, true),` → `cod: etiquetaObra(o.cod, false),` | MUERTO | 3 | test_f041_r10_catalogo_en_node, test_f041_r12_etiqueta_exacta_primero, test_f041_r3_los_chips_y_el_catalogo_usan_etiqueta_obra |
| M19 textoObra sin `\|\| ""` | `app.js:94` | `+ " " + (descripcion \|\| "");` → `+ " " + descripcion;` | MUERTO | 2 | test_f041_r1_r2_etiqueta_y_texto_en_node, test_f041_r2_texto_visible_usa_la_etiqueta |
| M20 pajar ignora es_postventa | `app.js:526` | `textoObra(l.cod, l.descripcion, l.es_postventa)).join` → `textoObra(l.cod, l.descripcion, false)).join` | MUERTO | 2 | test_f041_r9_buscador_global_encuentra_postventa, test_f041_r9_buscador_global_usa_el_texto_visible |

## Análisis

- **Supervivientes: ninguno.** No hay análisis de equivalencia que hacer.
- **M14 y M15 (chips) mueren solo por los tests estáticos de R3.** Es lo
  esperado: `construirCelda` y `chipEditable` tocan el DOM y no se ejecutan en
  node (design §6 solo lleva a node funciones sin DOM). Además ambos mutantes
  son *equivalentes en comportamiento* (devuelven el código anterior a F-041,
  que pinta el mismo texto): lo que R3 exige y lo que los mata es que no haya
  una segunda concatenación de `Postv-`, no un cambio visible. Que el chip
  pinte bien lo comprueba el humano en T6.
- **M6 y M20 (buscador global)** los mata, además del estático, el test de
  lógica `test_f041_r9_buscador_global_encuentra_postventa`: es exactamente el
  fallo que dio origen a la feature (requirements §0.1).
- **M4 (`some` → `every`)** lo matan 8 tests, entre ellos el de D2
  (`naves postv`) y el de D1 (con `every`, Fede, sin líneas, casaría con
  cualquier filtro): casar por línea está fijado por comportamiento,
  no solo por texto.
- **M13 (vuelve el alias `postventa`)** lo mata
  `test_f041_r10_d1_postventa_no_casa`, la decisión D1 = A del humano.

## Script

```python
# mutacion_manual_f041.py (fuera del repo, a propósito)
"""Campaña de mutación manual de F-041 sobre `app.js`.

Se ejecuta desde la raíz del repositorio. Por cada mutante: copia
`static/js/app.js` y `tests/` del front a un directorio temporal, aplica la
sustitución (el texto original tiene que aparecer UNA sola vez), comprueba la
sintaxis con `node --check`, pasa `tests/test_f041_filtro_obra.py` sin `-x` y
anota los tests que caen. El árbol de trabajo no se toca.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

FRONT = Path("services/dedicacion-front")
PYTHON = str((FRONT / ".venv" / "Scripts" / "python.exe").resolve())
TEST = "tests/test_f041_filtro_obra.py"

M = [
    ("M1", "etiquetaObra sin Postv-",
     'return (esPostventa ? "Postv-" : "") + cod;',
     'return (esPostventa ? "" : "") + cod;'),
    ("M2", "textoObra sin el espacio",
     'etiquetaObra(cod, esPostventa) + " " + (descripcion || "")',
     'etiquetaObra(cod, esPostventa) + "" + (descripcion || "")'),
    ("M3", "lineaCasa: includes -> startsWith",
     "l.es_postventa)).includes(q);",
     "l.es_postventa)).startsWith(q);"),
    ("M4", "columna: some -> every",
     "t.lineas.some((l) => lineaCasa(l, filtro))",
     "t.lineas.every((l) => lineaCasa(l, filtro))"),
    ("M5", "filtro vacío: continue -> return false",
     "if (!filtro) continue;",
     "if (!filtro) return false;"),
    ("M6", "pajar sin textoObra",
     't.lineas.map((l) => textoObra(l.cod, l.descripcion, l.es_postventa)).join(" ")',
     't.lineas.map((l) => l.cod + " " + l.descripcion).join(" ")'),
    ("M7", "clave de la entrada Postv- con false",
     "clave: normalizar(textoObra(o.cod, o.descripcion, true)),",
     "clave: normalizar(textoObra(o.cod, o.descripcion, false)),"),
    ("M8", "clave normal sin normalizar",
     "clave: normalizar(textoObra(o.cod, o.descripcion, false)),",
     "clave: textoObra(o.cod, o.descripcion, false),"),
    ("M9", "clave Postv- sin normalizar",
     "clave: normalizar(textoObra(o.cod, o.descripcion, true)),",
     "clave: textoObra(o.cod, o.descripcion, true),"),
    ("M10", "lineaCasa sin normalizar",
     "return normalizar(textoObra(l.cod, l.descripcion, l.es_postventa)).includes(q);",
     "return textoObra(l.cod, l.descripcion, l.es_postventa).includes(q);"),
    ("M11", "lineaCasa ignora es_postventa",
     "return normalizar(textoObra(l.cod, l.descripcion, l.es_postventa)).includes(q);",
     "return normalizar(textoObra(l.cod, l.descripcion, false)).includes(q);"),
    ("M12", "lineaCasa sin descripción",
     "return normalizar(textoObra(l.cod, l.descripcion, l.es_postventa)).includes(q);",
     'return normalizar(textoObra(l.cod, "", l.es_postventa)).includes(q);'),
    ("M13", "vuelve el alias postventa (D1)",
     "clave: normalizar(textoObra(o.cod, o.descripcion, true)),",
     'clave: normalizar("postventa " + textoObra(o.cod, o.descripcion, true)),'),
    ("M14", "chip de la tabla con su propio Postv-",
     "${escapeHtml(etiquetaObra(l.cod, l.es_postventa))}",
     '${l.es_postventa ? "Postv-" : ""}${escapeHtml(l.cod)}'),
    ("M15", "chip del editor con su propio Postv-",
     "cod.textContent = etiquetaObra(linea.cod, linea.es_postventa);",
     'cod.textContent = (linea.es_postventa ? "Postv-" : "") + linea.cod;'),
    ("M16", "la columna de obras cae a textoColumna",
     'const casa = clave === "asignaciones"',
     'const casa = clave === "asignacionesX"'),
    ("M17", "entrada normal con etiqueta Postv-",
     "cod: etiquetaObra(o.cod, false),",
     "cod: etiquetaObra(o.cod, true),"),
    ("M18", "entrada Postv- con etiqueta normal",
     "cod: etiquetaObra(o.cod, true),",
     "cod: etiquetaObra(o.cod, false),"),
    ("M19", "textoObra sin || \"\"",
     '+ " " + (descripcion || "");',
     '+ " " + descripcion;'),
    ("M20", "pajar ignora es_postventa",
     "textoObra(l.cod, l.descripcion, l.es_postventa)).join",
     "textoObra(l.cod, l.descripcion, false)).join"),
]


def correr(app_js: str) -> tuple[str, list[str], str]:
    with tempfile.TemporaryDirectory(prefix="mm_f041_") as tmp:
        raiz = Path(tmp)
        (raiz / "static" / "js").mkdir(parents=True)
        (raiz / "static" / "js" / "app.js").write_bytes(app_js.encode("utf-8"))
        shutil.copytree(FRONT / "tests", raiz / "tests",
                        ignore=shutil.ignore_patterns("__pycache__"))
        chk = subprocess.run(["node", "--check", "static/js/app.js"], cwd=raiz,
                             capture_output=True, text=True)
        if chk.returncode != 0:
            return "SINTAXIS", [], ""
        r = subprocess.run([PYTHON, "-m", "pytest", TEST, "-q", "-rA",
                            "--tb=no", "-p", "no:cacheprovider"], cwd=raiz,
                           capture_output=True, text=True, encoding="utf-8")
        caidos = sorted(set(re.findall(
            r"^(?:FAILED|ERROR) tests/test_f041_filtro_obra\.py::(\w+)",
            r.stdout, re.MULTILINE)))
        resumen = r.stdout.strip().splitlines()[-1]
        return ("MUERTO" if r.returncode else "SUPERVIVIENTE"), caidos, resumen


def main() -> None:
    original = (FRONT / "static" / "js" / "app.js").read_bytes().decode("utf-8")
    estado, caidos, resumen = correr(original)
    print(f"Línea base: {estado} · {resumen}")
    if estado != "SUPERVIVIENTE":
        sys.exit("la línea base no está en verde: la campaña no vale")
    for ide, desc, antes, despues in M:
        n = original.count(antes)
        if n != 1:
            sys.exit(f"{ide}: el original aparece {n} veces, tiene que ser 1")
        linea = original[:original.index(antes)].count("\n") + 1
        estado, caidos, resumen = correr(original.replace(antes, despues))
        esc = lambda s: s.replace("|", "\\|")
        print(f"| {ide} {desc} | `app.js:{linea}` | `{esc(antes)}` → "
              f"`{esc(despues)}` | {estado} | {len(caidos)} | "
              f"{', '.join(caidos) or '—'} |")


if __name__ == "__main__":
    main()
```
