<!-- progress/mutacion_manual_F-063.md -->
# F-063 · Mutación manual de `app.js`

`python -m harness.mutacion` **solo muta Python** y la puerta de cobertura de
`init.sh` no mide JS. Lo único de producción que cambia F-063 es
`services/dedicacion-front/static/js/app.js` (más una frase del README), así
que esta campaña sustituye a la automática (mismo patrón que
`progress/mutacion_manual_F-064.md`).

- **Medida sobre** `b982703` (rama `feature/F-063-filtro-por-incidencia`,
  versión final de `app.js`, que no cambia desde `05254ca`; tests con el de
  T3). Las líneas de la tabla son las de ese commit.
- **Siempre sobre una copia**: el script copia a un directorio temporal, con
  la estructura del repo, `app.js` del front y su `tests/` (el test de F-063
  no lee ningún otro fichero). Aplica la sustitución (el texto original tiene
  que aparecer **una sola vez**; si no, aborta), comprueba la sintaxis con
  `node --check` y pasa `tests/test_f063_filtro_incidencia.py` **sin `-x`**,
  anotando los tests que caen. `git status` sin cambios en lo versionado
  después (comprobado: solo los `progress/` que se estaban escribiendo).
- **Línea base** (sin mutar, en la copia): `16 passed in 15.83s`. Una línea
  base en rojo aborta la campaña.
- **Workers y coste**: en serie (**1 worker**), **811,1 s** de reloj para 25
  mutantes más la línea base: **~31 s por ejecución** (la máquina iba
  cargada; la misma campaña con 15 tests tardó 430,1 s).
- **Primera pasada** (sobre `05254ca`, sin el test de T3): **M14** (sin
  desempate por nombre) sobrevivía: ningún dato tenía dos tipos con la misma
  letra. Se añadió `test_f063_r1_misma_letra_dos_tipos_por_codigo_y_por_nombre`
  (`b982703`) y ahora muere. M25 sobrevivía igual que ahora.
- **Convención de las celdas**: `\|` es `|`; los espacios del texto están
  aplanados; «(nada)» es borrar el texto. El canónico es la lista `M` del
  script.

## Reproducir

Guardar el bloque del final como `mutacion_manual_f063.py` **fuera del repo**
(un `.py` fuera de `tests/`, `specs/`, `progress/` o `docs/` entraría en el
alcance de producción de `harness/alcance.py`) y, desde la raíz del repo:

```bash
PYTHONIOENCODING=utf-8 services/dedicacion-front/.venv/Scripts/python.exe <ruta>/mutacion_manual_f063.py
```

## Campaña (`b982703`): 25 mutantes, 24 muertos, 1 superviviente (equivalente)

| Mutante | Fichero:línea | Texto exacto original → mutado | Resultado | Fallos (sin `-x`) | Tests que lo matan |
|---|---|---|---|---|---|
| M1 sin filtro de incidencia en el filtrado | `app.js:876` | `if (state.filtroIncidencia && !tieneIncidencia(t, state.filtroIncidencia.codigo)) return false;` → `(nada)` | MUERTO | 9 | test_f063_el_filtro_solo_vive_en_la_cabecera_y_el_filtrado, test_f063_r1_misma_letra_dos_tipos_por_codigo_y_por_nombre, test_f063_r2_activo_y_sin_trabajadores_la_ficha_sigue_para_quitarlo, test_f063_r2_elegir_otra_sustituye_a_la_anterior, test_f063_r2_un_clic_filtra_y_marca_la_ficha, test_f063_r2_una_quitada_no_filtra, test_f063_r3_se_combina_con_el_buscador, test_f063_r3_se_combina_con_la_ficha_de_estado, test_f063_r3_se_combina_con_los_filtros_de_columna |
| M2 filtro al revés (sin !) | `app.js:877` | `!tieneIncidencia(t, state.filtroIncidencia.codigo)) return false;` → `tieneIncidencia(t, state.filtroIncidencia.codigo)) return false;` | MUERTO | 8 | test_f063_r1_misma_letra_dos_tipos_por_codigo_y_por_nombre, test_f063_r2_activo_y_sin_trabajadores_la_ficha_sigue_para_quitarlo, test_f063_r2_elegir_otra_sustituye_a_la_anterior, test_f063_r2_un_clic_filtra_y_marca_la_ficha, test_f063_r2_una_quitada_no_filtra, test_f063_r3_se_combina_con_el_buscador, test_f063_r3_se_combina_con_la_ficha_de_estado, test_f063_r3_se_combina_con_los_filtros_de_columna |
| M3 la quitada cuenta | `app.js:618` | `(i) => !i.quitada && i.codigo === codigo` → `(i) => i.codigo === codigo` | MUERTO | 11 | test_f063_r1_las_quitadas_solas_no_sacan_ficha, test_f063_r1_tipos_del_mes_cuenta_trabajadores_por_codigo, test_f063_r1_una_ficha_por_tipo_presente_con_letra_nombre_y_trabajadores, test_f063_r2_elegir_otra_sustituye_a_la_anterior, test_f063_r2_n_trabajadores_quita_el_filtro_de_incidencia_y_el_de_estado, test_f063_r2_otro_clic_quita_el_filtro, test_f063_r2_un_clic_filtra_y_marca_la_ficha, test_f063_r2_una_quitada_no_filtra, test_f063_r3_se_combina_con_el_buscador, test_f063_r3_se_combina_con_la_ficha_de_estado, test_f063_r3_se_combina_con_los_filtros_de_columna |
| M4 && -> || en tieneIncidencia | `app.js:618` | `(i) => !i.quitada && i.codigo === codigo` → `(i) => !i.quitada \|\| i.codigo === codigo` | MUERTO | 12 | test_f063_r1_las_quitadas_solas_no_sacan_ficha, test_f063_r1_misma_letra_dos_tipos_por_codigo_y_por_nombre, test_f063_r1_tipos_del_mes_cuenta_trabajadores_por_codigo, test_f063_r1_una_ficha_por_tipo_presente_con_letra_nombre_y_trabajadores, test_f063_r2_elegir_otra_sustituye_a_la_anterior, test_f063_r2_n_trabajadores_quita_el_filtro_de_incidencia_y_el_de_estado, test_f063_r2_otro_clic_quita_el_filtro, test_f063_r2_un_clic_filtra_y_marca_la_ficha, test_f063_r2_una_quitada_no_filtra, test_f063_r3_se_combina_con_el_buscador, test_f063_r3_se_combina_con_la_ficha_de_estado, test_f063_r3_se_combina_con_los_filtros_de_columna |
| M5 === -> !== en tieneIncidencia | `app.js:618` | `(i) => !i.quitada && i.codigo === codigo` → `(i) => !i.quitada && i.codigo !== codigo` | MUERTO | 11 | test_f063_r1_misma_letra_dos_tipos_por_codigo_y_por_nombre, test_f063_r1_tipos_del_mes_cuenta_trabajadores_por_codigo, test_f063_r1_una_ficha_por_tipo_presente_con_letra_nombre_y_trabajadores, test_f063_r2_elegir_otra_sustituye_a_la_anterior, test_f063_r2_n_trabajadores_quita_el_filtro_de_incidencia_y_el_de_estado, test_f063_r2_otro_clic_quita_el_filtro, test_f063_r2_un_clic_filtra_y_marca_la_ficha, test_f063_r2_una_quitada_no_filtra, test_f063_r3_se_combina_con_el_buscador, test_f063_r3_se_combina_con_la_ficha_de_estado, test_f063_r3_se_combina_con_los_filtros_de_columna |
| M6 la baja sin carga cuenta | `app.js:600` | `if (!t.activo && !t.lineas.length) return; const contados` → `const contados` | MUERTO | 9 | test_f063_r1_tipos_del_mes_cuenta_trabajadores_por_codigo, test_f063_r1_una_ficha_por_tipo_presente_con_letra_nombre_y_trabajadores, test_f063_r2_elegir_otra_sustituye_a_la_anterior, test_f063_r2_n_trabajadores_quita_el_filtro_de_incidencia_y_el_de_estado, test_f063_r2_otro_clic_quita_el_filtro, test_f063_r2_un_clic_filtra_y_marca_la_ficha, test_f063_r3_se_combina_con_el_buscador, test_f063_r3_se_combina_con_la_ficha_de_estado, test_f063_r3_se_combina_con_los_filtros_de_columna |
| M7 cuenta incidencias, no trabajadores | `app.js:603` | `if (contados.has(i.codigo) \|\| !tieneIncidencia(t, i.codigo)) return;` → `if (!tieneIncidencia(t, i.codigo)) return;` | MUERTO | 9 | test_f063_r1_tipos_del_mes_cuenta_trabajadores_por_codigo, test_f063_r1_una_ficha_por_tipo_presente_con_letra_nombre_y_trabajadores, test_f063_r2_elegir_otra_sustituye_a_la_anterior, test_f063_r2_n_trabajadores_quita_el_filtro_de_incidencia_y_el_de_estado, test_f063_r2_otro_clic_quita_el_filtro, test_f063_r2_un_clic_filtra_y_marca_la_ficha, test_f063_r3_se_combina_con_el_buscador, test_f063_r3_se_combina_con_la_ficha_de_estado, test_f063_r3_se_combina_con_los_filtros_de_columna |
| M8 el conteo no mira quitadas | `app.js:603` | `if (contados.has(i.codigo) \|\| !tieneIncidencia(t, i.codigo)) return;` → `if (contados.has(i.codigo)) return;` | MUERTO | 11 | test_f063_r1_las_quitadas_solas_no_sacan_ficha, test_f063_r1_tipos_del_mes_cuenta_trabajadores_por_codigo, test_f063_r1_una_ficha_por_tipo_presente_con_letra_nombre_y_trabajadores, test_f063_r2_elegir_otra_sustituye_a_la_anterior, test_f063_r2_n_trabajadores_quita_el_filtro_de_incidencia_y_el_de_estado, test_f063_r2_otro_clic_quita_el_filtro, test_f063_r2_un_clic_filtra_y_marca_la_ficha, test_f063_r2_una_quitada_no_filtra, test_f063_r3_se_combina_con_el_buscador, test_f063_r3_se_combina_con_la_ficha_de_estado, test_f063_r3_se_combina_con_los_filtros_de_columna |
| M9 no anota el tipo contado | `app.js:604` | `contados.add(i.codigo);` → `(nada)` | MUERTO | 9 | test_f063_r1_tipos_del_mes_cuenta_trabajadores_por_codigo, test_f063_r1_una_ficha_por_tipo_presente_con_letra_nombre_y_trabajadores, test_f063_r2_elegir_otra_sustituye_a_la_anterior, test_f063_r2_n_trabajadores_quita_el_filtro_de_incidencia_y_el_de_estado, test_f063_r2_otro_clic_quita_el_filtro, test_f063_r2_un_clic_filtra_y_marca_la_ficha, test_f063_r3_se_combina_con_el_buscador, test_f063_r3_se_combina_con_la_ficha_de_estado, test_f063_r3_se_combina_con_los_filtros_de_columna |
| M10 el conteo empieza en 1 | `app.js:606` | `nombre: i.nombre, n: 0 };` → `nombre: i.nombre, n: 1 };` | MUERTO | 11 | test_f063_r1_misma_letra_dos_tipos_por_codigo_y_por_nombre, test_f063_r1_tipos_del_mes_cuenta_trabajadores_por_codigo, test_f063_r1_una_ficha_por_tipo_presente_con_letra_nombre_y_trabajadores, test_f063_r2_elegir_otra_sustituye_a_la_anterior, test_f063_r2_n_trabajadores_quita_el_filtro_de_incidencia_y_el_de_estado, test_f063_r2_otro_clic_quita_el_filtro, test_f063_r2_un_clic_filtra_y_marca_la_ficha, test_f063_r2_una_quitada_no_filtra, test_f063_r3_se_combina_con_el_buscador, test_f063_r3_se_combina_con_la_ficha_de_estado, test_f063_r3_se_combina_con_los_filtros_de_columna |
| M11 no guarda el tipo | `app.js:608` | `tipos.set(i.codigo, tipo);` → `(nada)` | MUERTO | 11 | test_f063_r1_misma_letra_dos_tipos_por_codigo_y_por_nombre, test_f063_r1_tipos_del_mes_cuenta_trabajadores_por_codigo, test_f063_r1_una_ficha_por_tipo_presente_con_letra_nombre_y_trabajadores, test_f063_r2_elegir_otra_sustituye_a_la_anterior, test_f063_r2_n_trabajadores_quita_el_filtro_de_incidencia_y_el_de_estado, test_f063_r2_otro_clic_quita_el_filtro, test_f063_r2_un_clic_filtra_y_marca_la_ficha, test_f063_r2_una_quitada_no_filtra, test_f063_r3_se_combina_con_el_buscador, test_f063_r3_se_combina_con_la_ficha_de_estado, test_f063_r3_se_combina_con_los_filtros_de_columna |
| M12 sin ordenar | `app.js:611` | `return [...tipos.values()].sort((a, b) => a.letra.localeCompare(b.letra, "es") \|\| a.nombre.localeCompare(b.nombre, "es"));` → `return [...tipos.values()];` | MUERTO | 3 | test_f063_r1_misma_letra_dos_tipos_por_codigo_y_por_nombre, test_f063_r1_tipos_del_mes_cuenta_trabajadores_por_codigo, test_f063_r1_una_ficha_por_tipo_presente_con_letra_nombre_y_trabajadores |
| M13 letra al revés | `app.js:612` | `a.letra.localeCompare(b.letra, "es")` → `b.letra.localeCompare(a.letra, "es")` | MUERTO | 2 | test_f063_r1_tipos_del_mes_cuenta_trabajadores_por_codigo, test_f063_r1_una_ficha_por_tipo_presente_con_letra_nombre_y_trabajadores |
| M14 sin desempate por nombre | `app.js:612` | `\|\| a.nombre.localeCompare(b.nombre, "es"));` → `);` | MUERTO | 1 | test_f063_r1_misma_letra_dos_tipos_por_codigo_y_por_nombre |
| M15 «N trabajadores» no quita la de incidencia | `app.js:562` | `if (!c.clave) state.filtroIncidencia = null;` → `(nada)` | MUERTO | 1 | test_f063_r2_n_trabajadores_quita_el_filtro_de_incidencia_y_el_de_estado |
| M16 la de estado quita la de incidencia | `app.js:562` | `if (!c.clave) state.filtroIncidencia = null;` → `if (c.clave) state.filtroIncidencia = null;` | MUERTO | 1 | test_f063_r3_se_combina_con_la_ficha_de_estado |
| M17 la activa sin trabajadores desaparece | `app.js:575` | `tipos.push({ ...activa, n: 0 });` → `(nada)` | MUERTO | 1 | test_f063_r2_activo_y_sin_trabajadores_la_ficha_sigue_para_quitarlo |
| M18 condición de la activa al revés | `app.js:574` | `if (activa && !tipos.some((x) => x.codigo === activa.codigo)) {` → `if (activa && tipos.some((x) => x.codigo === activa.codigo)) {` | MUERTO | 5 | test_f063_r1_misma_letra_dos_tipos_por_codigo_y_por_nombre, test_f063_r2_activo_y_sin_trabajadores_la_ficha_sigue_para_quitarlo, test_f063_r2_elegir_otra_sustituye_a_la_anterior, test_f063_r2_un_clic_filtra_y_marca_la_ficha, test_f063_r3_se_combina_con_la_ficha_de_estado |
| M19 no marca la activa | `app.js:580` | `(activa && activa.codigo === x.codigo ? " filtro-activo" : "");` → `"";` | MUERTO | 5 | test_f063_r1_misma_letra_dos_tipos_por_codigo_y_por_nombre, test_f063_r2_activo_y_sin_trabajadores_la_ficha_sigue_para_quitarlo, test_f063_r2_elegir_otra_sustituye_a_la_anterior, test_f063_r2_un_clic_filtra_y_marca_la_ficha, test_f063_r3_se_combina_con_la_ficha_de_estado |
| M20 otro clic no la quita | `app.js:584` | `state.filtroIncidencia = activa && activa.codigo === x.codigo ? null` → `state.filtroIncidencia = false ? null` | MUERTO | 2 | test_f063_r2_activo_y_sin_trabajadores_la_ficha_sigue_para_quitarlo, test_f063_r2_otro_clic_quita_el_filtro |
| M21 el clic no repinta la tabla | `app.js:587` | `renderTabla(); }); cont.appendChild(el); }); } // F-063: los tipos` → `}); cont.appendChild(el); }); } // F-063: los tipos` | MUERTO | 1 | test_f063_r2_un_clic_filtra_y_marca_la_ficha |
| M22 cambiar de mes no la quita | `app.js:2857` | `state.filtroIncidencia = null; // F-063: otro mes, otros tipos` → `(nada)` | MUERTO | 2 | test_f063_el_filtro_solo_vive_en_la_cabecera_y_el_filtrado, test_f063_r2_cambiar_de_mes_quita_el_filtro_de_incidencia |
| M23 texto en otro orden | `app.js:581` | ``${x.letra} ${x.nombre} ${x.n}`` → ``${x.n} ${x.letra} ${x.nombre}`` | MUERTO | 11 | test_f063_r1_misma_letra_dos_tipos_por_codigo_y_por_nombre, test_f063_r1_una_ficha_por_tipo_presente_con_letra_nombre_y_trabajadores, test_f063_r2_activo_y_sin_trabajadores_la_ficha_sigue_para_quitarlo, test_f063_r2_elegir_otra_sustituye_a_la_anterior, test_f063_r2_n_trabajadores_quita_el_filtro_de_incidencia_y_el_de_estado, test_f063_r2_otro_clic_quita_el_filtro, test_f063_r2_un_clic_filtra_y_marca_la_ficha, test_f063_r2_una_quitada_no_filtra, test_f063_r3_se_combina_con_el_buscador, test_f063_r3_se_combina_con_la_ficha_de_estado, test_f063_r3_se_combina_con_los_filtros_de_columna |
| M24 el filtro guarda la letra como código | `app.js:585` | `{ codigo: x.codigo, letra: x.letra, nombre: x.nombre }` → `{ codigo: x.letra, letra: x.letra, nombre: x.nombre }` | MUERTO | 8 | test_f063_r1_misma_letra_dos_tipos_por_codigo_y_por_nombre, test_f063_r2_elegir_otra_sustituye_a_la_anterior, test_f063_r2_otro_clic_quita_el_filtro, test_f063_r2_un_clic_filtra_y_marca_la_ficha, test_f063_r2_una_quitada_no_filtra, test_f063_r3_se_combina_con_el_buscador, test_f063_r3_se_combina_con_la_ficha_de_estado, test_f063_r3_se_combina_con_los_filtros_de_columna |
| M25 sin respaldo de incidencias ausentes | `app.js:618` | `return (t.incidencias \|\| []).some((i) => !i.quitada` → `return t.incidencias.some((i) => !i.quitada` | SUPERVIVIENTE | 0 | — |

## Análisis

- **M25 (superviviente): equivalente con la forma real de la api.** Quita el
  respaldo `|| []` de `tieneIncidencia`. Solo cambia algo si un trabajador
  llega **sin** la clave `incidencias`, y eso no ocurre: `TrabajadorOut`
  declara `incidencias: list[IncidenciaOut] = []` sin `exclude_if`, así que la
  api la serializa siempre (vacía o no), y `state.trabajadores` solo se
  rellena con esa respuesta (`aplicarCuadrante`, `aplicarFila`). Matarlo
  exigiría un doble sin `incidencias`, contrario a la forma real que piden
  los dobles. Se deja el respaldo por coherencia con el resto de `app.js`
  (`(t.incidencias || [])` en F-030) y porque los arneses antiguos de F-041
  y F-050 sí construyen trabajadores sin la clave.
- **M14** lo mata un solo test, el de T3, escrito tras la primera pasada:
  es el único con dos tipos de la misma letra.
- **M15, M16, M17 y M21** los mata un test cada uno: «N trabajadores» quita
  la de incidencia (M15), la de estado no la quita (M16), la activa sin
  trabajadores sigue (M17) y el clic repinta la tabla (M21). Cada uno es el
  escenario que fija ese punto del criterio.
- **M22** (cambiar de mes no la quita) lo matan el estático de `moverMes` y
  el de límite; `moverMes` es asíncrono y llama a la api, así que no se
  ejecuta en node (mismo criterio que `test_f029` R6).
- **M3, M4 y M8** tumban además las dos guardas que estaban en verde en la
  fase RED (`sin_incidencias…` y `las_quitadas_solas…`): muerden.

## Script

```python
# mutacion_manual_f063.py (fuera del repo, a propósito)
"""Campaña de mutación manual de F-063 sobre `app.js`.

Se ejecuta desde la raíz del repositorio. Por cada mutante: copia a un
directorio temporal, con la MISMA estructura del repo, `app.js` del front y
su `tests/`; aplica la sustitución en `app.js` (el texto original tiene que
aparecer UNA sola vez; si no, aborta), comprueba la sintaxis con
`node --check`, pasa `tests/test_f063_filtro_incidencia.py` sin `-x` y anota
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
TESTS = ["tests/test_f063_filtro_incidencia.py"]
JS = "static/js/app.js"

FILTRO = ("    if (state.filtroIncidencia &&\n"
          "        !tieneIncidencia(t, state.filtroIncidencia.codigo)) return false;\n")
TIENE = "(i) => !i.quitada && i.codigo === codigo"
CUENTA = "if (contados.has(i.codigo) || !tieneIncidencia(t, i.codigo)) return;"
ORDEN = ('return [...tipos.values()].sort((a, b) =>\n'
         '    a.letra.localeCompare(b.letra, "es") || '
         'a.nombre.localeCompare(b.nombre, "es"));')
EMPUJA = "if (activa && !tipos.some((x) => x.codigo === activa.codigo)) {"
COLA = ("      renderTabla();\n    });\n    cont.appendChild(el);\n  });\n}\n\n"
        "// F-063: los tipos")
M = [
    ("M1", "sin filtro de incidencia en el filtrado", FILTRO, ""),
    ("M2", "filtro al revés (sin !)",
     "!tieneIncidencia(t, state.filtroIncidencia.codigo)) return false;",
     "tieneIncidencia(t, state.filtroIncidencia.codigo)) return false;"),
    ("M3", "la quitada cuenta", TIENE, "(i) => i.codigo === codigo"),
    ("M4", "&& -> || en tieneIncidencia", TIENE,
     "(i) => !i.quitada || i.codigo === codigo"),
    ("M5", "=== -> !== en tieneIncidencia", TIENE,
     "(i) => !i.quitada && i.codigo !== codigo"),
    ("M6", "la baja sin carga cuenta",
     "    if (!t.activo && !t.lineas.length) return;\n    const contados",
     "    const contados"),
    ("M7", "cuenta incidencias, no trabajadores", CUENTA,
     "if (!tieneIncidencia(t, i.codigo)) return;"),
    ("M8", "el conteo no mira quitadas", CUENTA,
     "if (contados.has(i.codigo)) return;"),
    ("M9", "no anota el tipo contado", "      contados.add(i.codigo);\n", ""),
    ("M10", "el conteo empieza en 1", "nombre: i.nombre, n: 0 };",
     "nombre: i.nombre, n: 1 };"),
    ("M11", "no guarda el tipo", "      tipos.set(i.codigo, tipo);\n", ""),
    ("M12", "sin ordenar", ORDEN, "return [...tipos.values()];"),
    ("M13", "letra al revés", 'a.letra.localeCompare(b.letra, "es")',
     'b.letra.localeCompare(a.letra, "es")'),
    ("M14", "sin desempate por nombre",
     ' || a.nombre.localeCompare(b.nombre, "es"));', ");"),
    ("M15", "«N trabajadores» no quita la de incidencia",
     "      if (!c.clave) state.filtroIncidencia = null;\n", ""),
    ("M16", "la de estado quita la de incidencia",
     "if (!c.clave) state.filtroIncidencia = null;",
     "if (c.clave) state.filtroIncidencia = null;"),
    ("M17", "la activa sin trabajadores desaparece",
     "    tipos.push({ ...activa, n: 0 });\n", ""),
    ("M18", "condición de la activa al revés", EMPUJA,
     "if (activa && tipos.some((x) => x.codigo === activa.codigo)) {"),
    ("M19", "no marca la activa",
     '(activa && activa.codigo === x.codigo ? " filtro-activo" : "");', '"";'),
    ("M20", "otro clic no la quita",
     "state.filtroIncidencia = activa && activa.codigo === x.codigo ? null",
     "state.filtroIncidencia = false ? null"),
    ("M21", "el clic no repinta la tabla", COLA,
     COLA.replace("      renderTabla();\n", "")),
    ("M22", "cambiar de mes no la quita",
     "  state.filtroIncidencia = null;   // F-063: otro mes, otros tipos\n", ""),
    ("M23", "texto en otro orden", "`${x.letra} ${x.nombre} ${x.n}`",
     "`${x.n} ${x.letra} ${x.nombre}`"),
    ("M24", "el filtro guarda la letra como código",
     "{ codigo: x.codigo, letra: x.letra, nombre: x.nombre }",
     "{ codigo: x.letra, letra: x.letra, nombre: x.nombre }"),
    ("M25", "sin respaldo de incidencias ausentes",
     "return (t.incidencias || []).some((i) => !i.quitada",
     "return t.incidencias.some((i) => !i.quitada"),
]


def correr(js: str) -> tuple[str, list[str], str]:
    with tempfile.TemporaryDirectory(prefix="mm_f063_") as tmp:
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
