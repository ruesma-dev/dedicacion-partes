<!-- progress/mutacion_manual_F-065.md -->
# F-065 · Mutación manual de `app.js`

`python -m harness.mutacion` **solo muta Python** y la puerta de cobertura de
`init.sh` no mide JS. Lo único de producción que cambia F-065 es
`services/dedicacion-front/static/js/app.js`, así que esta campaña sustituye
a la automática (mismo patrón que `progress/mutacion_manual_F-063.md`).

- **Medida sobre** `6abe00dc656c81da38a8ea9479e9e8dcaa9fcf13` (rama
  `feature/F-065-ficha-activa-en-su-sitio`, T2: versión final de `app.js` y
  de los tests). Las líneas de la tabla son las de ese commit.
- **Siempre sobre una copia**: el script copia a un directorio temporal, con
  la estructura del repo, `app.js` del front y su `tests/` (los dos ficheros
  de test no leen nada más; el de F-065 importa el arnés del de F-063).
  Aplica la sustitución (el original tiene que aparecer **una sola vez**; si
  no, aborta), comprueba la sintaxis con `node --check` y pasa
  `test_f063_filtro_incidencia.py` y `test_f065_ficha_activa_en_su_sitio.py`
  **sin `-x`**, anotando los tests que caen. `git status` sin cambios
  después (comprobado: árbol limpio).
- **Línea base** (sin mutar, en la copia): `20 passed in 4.19s` (16 de F-063
  y 4 de F-065). Una línea base en rojo aborta la campaña.
- **Workers y coste**: en serie (**1 worker**), **76,9 s** de reloj para 12
  mutantes más la línea base (~6 s por ejecución).
- **Qué se muta**: las líneas que cambia F-065 (N1-N10: la siembra de la
  activa en `tiposIncidenciaDelMes` y la llamada de `renderCabecera`) y el
  orden del que depende (N11 y N12, los mismos cambios que M12 y M14 de
  F-063, repetidos para ver que los tests nuevos también los cazan). N2
  reintroduce el fallo de antes (añadir la activa después de ordenar) dentro
  de la función.
- **Convención de las celdas**: `\|` es `|`; los espacios del texto están
  aplanados; «(nada)» es borrar el texto. El canónico es la lista `M` del
  script.

## Reproducir

Guardar el bloque del final como `mutacion_manual_f065.py` **fuera del repo**
(un `.py` fuera de `tests/`, `specs/`, `progress/` o `docs/` entraría en el
alcance de producción de `harness/alcance.py`) y, desde la raíz del repo, con
`6abe00dc656c81da38a8ea9479e9e8dcaa9fcf13` (o un descendiente que no toque
`app.js` ni esos dos tests) en el árbol:

```bash
PYTHONIOENCODING=utf-8 services/dedicacion-front/.venv/Scripts/python.exe <ruta>/mutacion_manual_f065.py
```

## Campaña (`6abe00d`): 12 mutantes, 11 muertos, 1 superviviente (equivalente)

| Mutante | Fichero:línea | Texto exacto original → mutado | Resultado | Fallos (sin `-x`) | Tests que lo matan |
|---|---|---|---|---|---|
| N1 la activa a 0 no entra | `app.js:609` | `if (activo && !tipos.has(activo.codigo)) { tipos.set(activo.codigo, { ...activo, n: 0 }); }` → `(nada)` | MUERTO | 3 | test_f063_r2_activo_y_sin_trabajadores_la_ficha_sigue_para_quitarlo, test_f065_r1_la_activa_a_0_desempata_por_nombre_con_la_misma_letra, test_f065_r1_la_activa_a_0_sale_por_letra_y_no_al_final |
| N2 la activa entra después de ordenar (el fallo de antes) | `app.js:609` | `if (activo && !tipos.has(activo.codigo)) { tipos.set(activo.codigo, { ...activo, n: 0 }); } return [...tipos.values()].sort((a, b) => a.letra.localeCompare(b.letra, "es") \|\| a.nombre.localeCompare(b.nombre, "es"));` → `const lista = [...tipos.values()].sort((a, b) => a.letra.localeCompare(b.letra, "es") \|\| a.nombre.localeCompare(b.nombre, "es")); if (activo && !tipos.has(activo.codigo)) lista.push({ ...activo, n: 0 }); return lista;` | MUERTO | 2 | test_f065_r1_la_activa_a_0_desempata_por_nombre_con_la_misma_letra, test_f065_r1_la_activa_a_0_sale_por_letra_y_no_al_final |
| N3 renderCabecera no pasa la activa | `app.js:573` | `tiposIncidenciaDelMes(state.trabajadores, activa).forEach` → `tiposIncidenciaDelMes(state.trabajadores).forEach` | MUERTO | 3 | test_f063_r2_activo_y_sin_trabajadores_la_ficha_sigue_para_quitarlo, test_f065_r1_la_activa_a_0_desempata_por_nombre_con_la_misma_letra, test_f065_r1_la_activa_a_0_sale_por_letra_y_no_al_final |
| N4 condición de la siembra al revés | `app.js:609` | `if (activo && !tipos.has(activo.codigo)) {` → `if (activo && tipos.has(activo.codigo)) {` | MUERTO | 8 | test_f063_r1_misma_letra_dos_tipos_por_codigo_y_por_nombre, test_f063_r2_activo_y_sin_trabajadores_la_ficha_sigue_para_quitarlo, test_f063_r2_elegir_otra_sustituye_a_la_anterior, test_f063_r2_otro_clic_quita_el_filtro, test_f063_r2_un_clic_filtra_y_marca_la_ficha, test_f063_r3_se_combina_con_la_ficha_de_estado, test_f065_r1_la_activa_a_0_desempata_por_nombre_con_la_misma_letra, test_f065_r1_la_activa_a_0_sale_por_letra_y_no_al_final |
| N5 siembra sin mirar si ya está (pisa la presente con 0) | `app.js:609` | `if (activo && !tipos.has(activo.codigo)) {` → `if (activo) {` | MUERTO | 6 | test_f063_r1_misma_letra_dos_tipos_por_codigo_y_por_nombre, test_f063_r2_elegir_otra_sustituye_a_la_anterior, test_f063_r2_otro_clic_quita_el_filtro, test_f063_r2_un_clic_filtra_y_marca_la_ficha, test_f063_r3_se_combina_con_la_ficha_de_estado, test_f065_r1_la_activa_a_0_sale_por_letra_y_no_al_final |
| N6 siembra sin guarda de activo (null) | `app.js:609` | `if (activo && !tipos.has(activo.codigo)) {` → `if (!tipos.has(activo.codigo)) {` | MUERTO | 16 | test_f063_r1_las_quitadas_solas_no_sacan_ficha, test_f063_r1_misma_letra_dos_tipos_por_codigo_y_por_nombre, test_f063_r1_sin_incidencias_en_el_mes_ninguna_ficha_nueva, test_f063_r1_tipos_del_mes_cuenta_trabajadores_por_codigo, test_f063_r1_una_ficha_por_tipo_presente_con_letra_nombre_y_trabajadores, test_f063_r2_activo_y_sin_trabajadores_la_ficha_sigue_para_quitarlo, test_f063_r2_elegir_otra_sustituye_a_la_anterior, test_f063_r2_n_trabajadores_quita_el_filtro_de_incidencia_y_el_de_estado, test_f063_r2_otro_clic_quita_el_filtro, test_f063_r2_un_clic_filtra_y_marca_la_ficha, test_f063_r2_una_quitada_no_filtra, test_f063_r3_se_combina_con_el_buscador, test_f063_r3_se_combina_con_la_ficha_de_estado, test_f063_r3_se_combina_con_los_filtros_de_columna, test_f065_r1_la_activa_a_0_sale_por_letra_y_no_al_final, test_f065_r1_sin_filtro_activo_la_fila_no_cambia |
| N7 busca la activa por letra, no por código | `app.js:609` | `if (activo && !tipos.has(activo.codigo)) {` → `if (activo && !tipos.has(activo.letra)) {` | MUERTO | 6 | test_f063_r1_misma_letra_dos_tipos_por_codigo_y_por_nombre, test_f063_r2_elegir_otra_sustituye_a_la_anterior, test_f063_r2_otro_clic_quita_el_filtro, test_f063_r2_un_clic_filtra_y_marca_la_ficha, test_f063_r3_se_combina_con_la_ficha_de_estado, test_f065_r1_la_activa_a_0_sale_por_letra_y_no_al_final |
| N8 la activa entra con 1 | `app.js:610` | `{ ...activo, n: 0 }` → `{ ...activo, n: 1 }` | MUERTO | 3 | test_f063_r2_activo_y_sin_trabajadores_la_ficha_sigue_para_quitarlo, test_f065_r1_la_activa_a_0_desempata_por_nombre_con_la_misma_letra, test_f065_r1_la_activa_a_0_sale_por_letra_y_no_al_final |
| N9 la activa entra sin letra ni nombre | `app.js:610` | `{ ...activo, n: 0 }` → `{ codigo: activo.codigo, n: 0 }` | MUERTO | 3 | test_f063_r2_activo_y_sin_trabajadores_la_ficha_sigue_para_quitarlo, test_f065_r1_la_activa_a_0_desempata_por_nombre_con_la_misma_letra, test_f065_r1_la_activa_a_0_sale_por_letra_y_no_al_final |
| N10 la activa se guarda con la letra como clave | `app.js:610` | `tipos.set(activo.codigo, { ...activo, n: 0 });` → `tipos.set(activo.letra, { ...activo, n: 0 });` | SUPERVIVIENTE | 0 | — |
| N11 sin ordenar | `app.js:612` | `return [...tipos.values()].sort((a, b) => a.letra.localeCompare(b.letra, "es") \|\| a.nombre.localeCompare(b.nombre, "es"));` → `return [...tipos.values()];` | MUERTO | 7 | test_f063_r1_misma_letra_dos_tipos_por_codigo_y_por_nombre, test_f063_r1_tipos_del_mes_cuenta_trabajadores_por_codigo, test_f063_r1_una_ficha_por_tipo_presente_con_letra_nombre_y_trabajadores, test_f065_r1_el_orden_de_las_fichas_vive_en_un_solo_sitio, test_f065_r1_la_activa_a_0_desempata_por_nombre_con_la_misma_letra, test_f065_r1_la_activa_a_0_sale_por_letra_y_no_al_final, test_f065_r1_sin_filtro_activo_la_fila_no_cambia |
| N12 sin desempate por nombre | `app.js:613` | `\|\| a.nombre.localeCompare(b.nombre, "es"));` → `);` | MUERTO | 2 | test_f063_r1_misma_letra_dos_tipos_por_codigo_y_por_nombre, test_f065_r1_la_activa_a_0_desempata_por_nombre_con_la_misma_letra |

## Análisis

- **N10 (superviviente): equivalente.** Guarda la activa a 0 en el mapa con
  la letra como clave en vez del código. La clave es interna: sirve para
  deduplicar mientras se cuenta, y la siembra va DESPUÉS del conteo y solo
  cuando el código no está. Lo que sale son los valores
  (`[...tipos.values()]`), el mismo objeto `{ ...activo, n: 0 }` y en el
  mismo orden. Solo cambiaría si un tipo presente tuviera como `codigo` la
  letra de la activa (un código de una sola letra igual a la letra de otro
  tipo): la activa pisaría a ese tipo. Los códigos de la api son los del
  catálogo (`IncidenciaOut.codigo`, p. ej. `CIV`, `CIE`), no letras: el sync
  solo trae códigos `CI%` distintos de `CIZ` (`services/dedicacion-api/config/config.yaml`,
  `sync.incidencias`, `WHERE aux.cod LIKE 'CI%' AND aux.cod <> 'CIZ'`) y la
  letra sale aparte (`domain/incidencias.py::letra_y_nombre`), así que ningún
  código mide una letra (O2 de la review 1, añadido por el líder); matarlo
  exigiría un doble con un código de una letra inventado, fuera de la forma
  real.
- **N2** (el fallo de antes, dentro de la función) lo matan solo los dos
  tests nuevos de posición: ningún test de F-063 lo veía, que es la O1 de su
  review. **N1** y **N3** (no pasar la activa) los caza además el test de
  F-063 de la activa a 0.
- **N11** lo caza también el estático `el_orden_de_las_fichas_vive_en_un_solo_sitio`
  (exige `localeCompare` en `tiposIncidenciaDelMes`); **N12** (sin
  desempate), el test nuevo del desempate con la activa a 0, además del de
  F-063.
- **N6** (sin guarda de `activo`) revienta con `activo` `undefined`: lo
  tumban todos los escenarios sin filtro, incluidas las guardas de F-063.

## Script

```python
# mutacion_manual_f065.py (fuera del repo, a propósito)
"""Campaña de mutación manual de F-065 sobre `app.js`.

Se ejecuta desde la raíz del repositorio. Por cada mutante: copia a un
directorio temporal, con la MISMA estructura del repo, `app.js` del front y
su `tests/`; aplica la sustitución en `app.js` (el texto original tiene que
aparecer UNA sola vez; si no, aborta), comprueba la sintaxis con
`node --check`, pasa los tests de F-063 y F-065 sin `-x` y anota los que
caen. El árbol de trabajo no se toca. En serie (1 worker).
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
TESTS = ["tests/test_f063_filtro_incidencia.py",
         "tests/test_f065_ficha_activa_en_su_sitio.py"]
JS = "static/js/app.js"

SIEMBRA = ("  if (activo && !tipos.has(activo.codigo)) {\n"
           "    tipos.set(activo.codigo, { ...activo, n: 0 });\n"
           "  }\n")
ORDEN = ('  return [...tipos.values()].sort((a, b) =>\n'
         '    a.letra.localeCompare(b.letra, "es") || '
         'a.nombre.localeCompare(b.nombre, "es"));\n')
# El fallo de antes, dentro de la función: añadir la activa DESPUÉS de ordenar.
TRAS_ORDENAR = ('  const lista = [...tipos.values()].sort((a, b) =>\n'
                '    a.letra.localeCompare(b.letra, "es") || '
                'a.nombre.localeCompare(b.nombre, "es"));\n'
                '  if (activo && !tipos.has(activo.codigo)) '
                'lista.push({ ...activo, n: 0 });\n'
                '  return lista;\n')
M = [
    ("N1", "la activa a 0 no entra", SIEMBRA, ""),
    ("N2", "la activa entra después de ordenar (el fallo de antes)",
     SIEMBRA + ORDEN, TRAS_ORDENAR),
    ("N3", "renderCabecera no pasa la activa",
     "tiposIncidenciaDelMes(state.trabajadores, activa).forEach",
     "tiposIncidenciaDelMes(state.trabajadores).forEach"),
    ("N4", "condición de la siembra al revés",
     "if (activo && !tipos.has(activo.codigo)) {",
     "if (activo && tipos.has(activo.codigo)) {"),
    ("N5", "siembra sin mirar si ya está (pisa la presente con 0)",
     "if (activo && !tipos.has(activo.codigo)) {", "if (activo) {"),
    ("N6", "siembra sin guarda de activo (null)",
     "if (activo && !tipos.has(activo.codigo)) {",
     "if (!tipos.has(activo.codigo)) {"),
    ("N7", "busca la activa por letra, no por código",
     "if (activo && !tipos.has(activo.codigo)) {",
     "if (activo && !tipos.has(activo.letra)) {"),
    ("N8", "la activa entra con 1", "{ ...activo, n: 0 }",
     "{ ...activo, n: 1 }"),
    ("N9", "la activa entra sin letra ni nombre", "{ ...activo, n: 0 }",
     "{ codigo: activo.codigo, n: 0 }"),
    ("N10", "la activa se guarda con la letra como clave",
     "tipos.set(activo.codigo, { ...activo, n: 0 });",
     "tipos.set(activo.letra, { ...activo, n: 0 });"),
    ("N11", "sin ordenar", ORDEN, "  return [...tipos.values()];\n"),
    ("N12", "sin desempate por nombre",
     ' || a.nombre.localeCompare(b.nombre, "es"));', ");"),
]


def correr(js: str) -> tuple[str, list[str], str]:
    with tempfile.TemporaryDirectory(prefix="mm_f065_") as tmp:
        raiz = Path(tmp)
        front = raiz / FRONT
        (front / JS).parent.mkdir(parents=True, exist_ok=True)
        (front / JS).write_bytes(js.encode("utf-8"))
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
