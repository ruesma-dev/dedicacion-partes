# F-042 · Mutación manual de `app.js` y `styles.css`

`python -m harness.mutacion` **solo muta Python** y la puerta de cobertura de
`init.sh` no mide JS (sale N/A con su motivo). Lo único de producción que
cambia F-042 es `services/dedicacion-front/static/js/app.js` y
`static/css/styles.css`, así que esta campaña la sustituye (mismo patrón que
`progress/mutacion_manual_F-041.md`).

- **Medida sobre** `4e502a5` (rama `feature/F-042-ultima-fila-autocompletado`,
  tras T3). Líneas de la tabla: las de ese commit.
- **Siempre sobre una copia**: el script copia `app.js`, `styles.css` y
  `tests/` del front a un directorio temporal, aplica la sustitución (el texto
  original tiene que aparecer **una sola vez**; si no, aborta), comprueba la
  sintaxis con `node --check`, pasa `tests/test_f042_sugerencias.py` **sin
  `-x`** y anota los tests que caen. `git status` limpio después (comprobado).
- **Línea base** (sin mutar, en la copia): `18 passed in 2.02s`. Una línea base
  en rojo aborta la campaña.
- **Coste**: 2 min 24 s de reloj para 38 mutantes + línea base, en serie (1
  worker): **~3,7 s por mutante**, coherente con la suite de F-042 (~2 s, que
  arranca node 14 veces).
- **Primera pasada** (sobre `5add8eb`, antes de T3, con 17 tests): 36 muertos y
  **2 supervivientes, M18 y M26**. M18 era un hueco real (ver análisis): se
  añadió `test_f042_r2_al_agrandar_la_ventana_recupera_el_alto` (`4e502a5`) y
  se repitió la campaña entera. La tabla es la de la segunda pasada.
- **Convención de las celdas**: `\|` es `|`; los espacios del texto están
  aplanados; «(nada)» es borrar el texto. El canónico es la lista `M` del
  script.

## Reproducir

Guardar el bloque del final como `mutacion_manual_f042.py` **fuera del repo**
(un `.py` fuera de `tests/`, `specs/`, `progress/` o `docs/` entraría en el
alcance de producción de `harness/alcance.py`) y, desde la raíz del repo:

```bash
PYTHONIOENCODING=utf-8 python <ruta>/mutacion_manual_f042.py
```

## Campaña (`4e502a5`): 38 mutantes, 37 muertos, 1 superviviente (equivalente)

| Mutante | Fichero:línea | Texto exacto original → mutado | Resultado | Fallos (sin `-x`) | Tests que lo matan |
|---|---|---|---|---|---|
| M1 HUECO 4 -> 0 | `app.js:1140` | `const HUECO = 4;` → `const HUECO = 0;` | MUERTO | 8 | test_f042_r2_acompana_al_campo_con_scroll_y_resize, test_f042_r2_al_agrandar_la_ventana_recupera_el_alto, test_f042_r2_cabe_debajo, test_f042_r2_fila_intermedia_se_ve_debajo, test_f042_r2_si_cabe_justo_sigue_debajo, test_f042_r2_si_no_cabe_en_ningun_lado_va_donde_hay_mas_sitio, test_f042_r2_ultima_fila_busca_se_ve_encima_y_se_elige_con_teclado, test_f042_r2_ultima_fila_se_abre_hacia_arriba |
| M2 MARGEN 8 -> 0 | `app.js:1141` | `const MARGEN = 8;` → `const MARGEN = 0;` | MUERTO | 3 | test_f042_r2_al_agrandar_la_ventana_recupera_el_alto, test_f042_r2_ancho_y_left_dentro_de_la_ventana, test_f042_r2_si_no_cabe_en_ningun_lado_va_donde_hay_mas_sitio |
| M3 ancho: min -> max | `app.js:1142` | `const ancho = Math.min(430,` → `const ancho = Math.max(430,` | MUERTO | 6 | test_f042_r2_acompana_al_campo_con_scroll_y_resize, test_f042_r2_ancho_y_left_dentro_de_la_ventana, test_f042_r2_cabe_debajo, test_f042_r2_si_no_cabe_en_ningun_lado_va_donde_hay_mas_sitio, test_f042_r2_ultima_fila_busca_se_ve_encima_y_se_elige_con_teclado, test_f042_r2_ultima_fila_se_abre_hacia_arriba |
| M4 ancho con un solo margen | `app.js:1142` | `ventana.ancho - 2 * MARGEN);` → `ventana.ancho - MARGEN);` | MUERTO | 1 | test_f042_r2_ancho_y_left_dentro_de_la_ventana |
| M5 left sin margen izquierdo | `app.js:1143` | `const left = Math.max(MARGEN,` → `const left = Math.max(0,` | MUERTO | 2 | test_f042_r2_ancho_y_left_dentro_de_la_ventana, test_f042_r2_si_no_cabe_en_ningun_lado_va_donde_hay_mas_sitio |
| M6 left sin tope derecho | `app.js:1143` | `Math.max(MARGEN, Math.min(campo.left, ventana.ancho - MARGEN - ancho));` → `Math.max(MARGEN, campo.left);` | MUERTO | 1 | test_f042_r2_ancho_y_left_dentro_de_la_ventana |
| M7 abajo sin hueco ni margen | `app.js:1144` | `const abajo = ventana.alto - campo.bottom - HUECO - MARGEN;` → `const abajo = ventana.alto - campo.bottom;` | MUERTO | 2 | test_f042_r2_al_agrandar_la_ventana_recupera_el_alto, test_f042_r2_si_no_cabe_en_ningun_lado_va_donde_hay_mas_sitio |
| M8 arriba sin hueco ni margen | `app.js:1145` | `const arriba = campo.top - HUECO - MARGEN;` → `const arriba = campo.top;` | MUERTO | 1 | test_f042_r2_si_no_cabe_en_ningun_lado_va_donde_hay_mas_sitio |
| M9 cabe justo: > -> >= | `app.js:1146` | `const haciaArriba = alto > abajo && arriba > abajo;` → `const haciaArriba = alto >= abajo && arriba > abajo;` | MUERTO | 1 | test_f042_r2_si_cabe_justo_sigue_debajo |
| M10 empate de sitio: > -> >= | `app.js:1146` | `const haciaArriba = alto > abajo && arriba > abajo;` → `const haciaArriba = alto > abajo && arriba >= abajo;` | MUERTO | 1 | test_f042_r2_si_no_cabe_en_ningun_lado_va_donde_hay_mas_sitio |
| M11 arriba siempre que no quepa | `app.js:1146` | `const haciaArriba = alto > abajo && arriba > abajo;` → `const haciaArriba = alto > abajo;` | MUERTO | 2 | test_f042_r2_al_agrandar_la_ventana_recupera_el_alto, test_f042_r2_si_no_cabe_en_ningun_lado_va_donde_hay_mas_sitio |
| M12 altoMax sin suelo 0 | `app.js:1147` | `const altoMax = Math.max(0, Math.min(alto, haciaArriba ? arriba : abajo));` → `const altoMax = Math.min(alto, haciaArriba ? arriba : abajo);` | MUERTO | 1 | test_f042_r2_el_alto_nunca_es_negativo |
| M13 altoMax sin limitar al sitio | `app.js:1147` | `const altoMax = Math.max(0, Math.min(alto, haciaArriba ? arriba : abajo));` → `const altoMax = Math.max(0, alto);` | MUERTO | 3 | test_f042_r2_al_agrandar_la_ventana_recupera_el_alto, test_f042_r2_el_alto_nunca_es_negativo, test_f042_r2_si_no_cabe_en_ningun_lado_va_donde_hay_mas_sitio |
| M14 altoMax siempre con el sitio de abajo | `app.js:1147` | `Math.min(alto, haciaArriba ? arriba : abajo)` → `Math.min(alto, abajo)` | MUERTO | 4 | test_f042_r2_acompana_al_campo_con_scroll_y_resize, test_f042_r2_si_no_cabe_en_ningun_lado_va_donde_hay_mas_sitio, test_f042_r2_ultima_fila_busca_se_ve_encima_y_se_elige_con_teclado, test_f042_r2_ultima_fila_se_abre_hacia_arriba |
| M15 top hacia arriba con alto sin limitar | `app.js:1148` | `campo.top - HUECO - altoMax :` → `campo.top - HUECO - alto :` | MUERTO | 1 | test_f042_r2_si_no_cabe_en_ningun_lado_va_donde_hay_mas_sitio |
| M16 top hacia abajo desde el top del campo | `app.js:1148` | `: campo.bottom + HUECO;` → `: campo.top + HUECO;` | MUERTO | 5 | test_f042_r2_acompana_al_campo_con_scroll_y_resize, test_f042_r2_cabe_debajo, test_f042_r2_fila_intermedia_se_ve_debajo, test_f042_r2_si_cabe_justo_sigue_debajo, test_f042_r2_si_no_cabe_en_ningun_lado_va_donde_hay_mas_sitio |
| M17 colocar con el panel oculto | `app.js:1154` | `if (panel.classList.contains("oculto")) return; panel.style.maxHeight = "";` → `panel.style.maxHeight = "";` | MUERTO | 1 | test_f042_r2_acompana_al_campo_con_scroll_y_resize |
| M18 sin quitar el maxHeight antes de medir | `app.js:1155` | `panel.style.maxHeight = ""; // alto natural, con el tope del CSS` → `(nada)` | MUERTO | 1 | test_f042_r2_al_agrandar_la_ventana_recupera_el_alto |
| M19 mide el panel en vez del campo | `app.js:1156` | `posicionSugerencias(input.getBoundingClientRect(),` → `posicionSugerencias(panel.getBoundingClientRect(),` | MUERTO | 4 | test_f042_r2_acompana_al_campo_con_scroll_y_resize, test_f042_r2_al_agrandar_la_ventana_recupera_el_alto, test_f042_r2_fila_intermedia_se_ve_debajo, test_f042_r2_ultima_fila_busca_se_ve_encima_y_se_elige_con_teclado |
| M20 alto de la ventana con su ancho | `app.js:1157` | `alto: document.documentElement.clientHeight,` → `alto: document.documentElement.clientWidth,` | MUERTO | 3 | test_f042_r2_acompana_al_campo_con_scroll_y_resize, test_f042_r2_al_agrandar_la_ventana_recupera_el_alto, test_f042_r2_ultima_fila_busca_se_ve_encima_y_se_elige_con_teclado |
| M21 sin poner top | `app.js:1160` | `panel.style.top = `${pos.top}px`;` → `(nada)` | MUERTO | 3 | test_f042_r2_acompana_al_campo_con_scroll_y_resize, test_f042_r2_fila_intermedia_se_ve_debajo, test_f042_r2_ultima_fila_busca_se_ve_encima_y_se_elige_con_teclado |
| M22 sin poner left | `app.js:1161` | `panel.style.left = `${pos.left}px`;` → `(nada)` | MUERTO | 2 | test_f042_r2_acompana_al_campo_con_scroll_y_resize, test_f042_r2_ultima_fila_busca_se_ve_encima_y_se_elige_con_teclado |
| M23 sin poner width | `app.js:1162` | `panel.style.width = `${pos.ancho}px`;` → `(nada)` | MUERTO | 1 | test_f042_r2_ultima_fila_busca_se_ve_encima_y_se_elige_con_teclado |
| M24 sin poner maxHeight | `app.js:1163` | `panel.style.maxHeight = `${pos.altoMax}px`;` → `(nada)` | MUERTO | 3 | test_f042_r2_al_agrandar_la_ventana_recupera_el_alto, test_f042_r2_fila_intermedia_se_ve_debajo, test_f042_r2_ultima_fila_busca_se_ve_encima_y_se_elige_con_teclado |
| M25 retirar no desmonta | `app.js:1170` | `if (desmontarSugerencias) desmontarSugerencias();` → `(nada)` | MUERTO | 1 | test_f042_r2_un_solo_panel_y_sin_huerfanos |
| M26 retirar no olvida el desmontaje | `app.js:1171` | `desmontarSugerencias = null; }` → `}` | SUPERVIVIENTE | 0 | — |
| M27 montar sin retirar el anterior | `app.js:1178` | `retirarSugerencias(); document.body.appendChild(panel);` → `document.body.appendChild(panel);` | MUERTO | 2 | test_f042_r1_el_panel_no_vive_dentro_de_la_fila, test_f042_r2_un_solo_panel_y_sin_huerfanos |
| M28 panel fuera de body (sin colgar) | `app.js:1179` | `document.body.appendChild(panel);` → `(nada)` | MUERTO | 4 | test_f042_r1_el_panel_no_vive_dentro_de_la_fila, test_f042_r2_fila_intermedia_se_ve_debajo, test_f042_r2_ultima_fila_busca_se_ve_encima_y_se_elige_con_teclado, test_f042_r2_un_solo_panel_y_sin_huerfanos |
| M29 scroll sin captura | `app.js:1182` | `window.addEventListener("scroll", recolocar, true);` → `window.addEventListener("scroll", recolocar);` | MUERTO | 2 | test_f042_r2_scroll_en_captura_para_el_de_la_tabla, test_f042_r2_un_solo_panel_y_sin_huerfanos |
| M30 quita el scroll sin captura | `app.js:1185` | `window.removeEventListener("scroll", recolocar, true);` → `window.removeEventListener("scroll", recolocar);` | MUERTO | 1 | test_f042_r2_un_solo_panel_y_sin_huerfanos |
| M31 no quita el resize | `app.js:1186` | `window.removeEventListener("resize", recolocar);` → `(nada)` | MUERTO | 1 | test_f042_r2_un_solo_panel_y_sin_huerfanos |
| M32 no quita el nodo | `app.js:1187` | `panel.remove(); };` → `};` | MUERTO | 1 | test_f042_r2_un_solo_panel_y_sin_huerfanos |
| M33 sin escucha de resize | `app.js:1183` | `window.addEventListener("resize", recolocar);` → `(nada)` | MUERTO | 4 | test_f042_r2_acompana_al_campo_con_scroll_y_resize, test_f042_r2_al_agrandar_la_ventana_recupera_el_alto, test_f042_r2_scroll_en_captura_para_el_de_la_tabla, test_f042_r2_un_solo_panel_y_sin_huerfanos |
| M34 refrescar no coloca | `app.js:1211` | `colocarSugerencias(input, panel); };` → `};` | MUERTO | 4 | test_f042_r2_al_agrandar_la_ventana_recupera_el_alto, test_f042_r2_fila_intermedia_se_ve_debajo, test_f042_r2_ultima_fila_busca_se_ve_encima_y_se_elige_con_teclado, test_f042_r3_busqueda_identica_y_luego_se_coloca |
| M35 renderTabla no retira | `app.js:551` | `retirarSugerencias(); // F-042: el campo de obra se va a rehacer` → `(nada)` | MUERTO | 1 | test_f042_r1_cada_repintado_de_la_tabla_retira_el_panel |
| M36 vuelve el panel dentro de la fila | `app.js:1001` | `sugerencias.className = "sugerencias oculto"; editor.appendChild(anadir);` → `sugerencias.className = "sugerencias oculto"; anadir.appendChild(sugerencias); editor.appendChild(anadir);` | MUERTO | 1 | test_f042_r1_el_panel_no_vive_dentro_de_la_fila |
| M37 recolocar no hace nada | `app.js:1180` | `const recolocar = () => colocarSugerencias(input, panel);` → `const recolocar = () => {};` | MUERTO | 2 | test_f042_r2_acompana_al_campo_con_scroll_y_resize, test_f042_r2_al_agrandar_la_ventana_recupera_el_alto |
| M38 CSS vuelve a absolute | `styles.css:384` | `position: fixed; left: 0; width: 430px;` → `position: absolute; left: 0; width: 430px;` | MUERTO | 1 | test_f042_r1_el_panel_es_fixed_y_no_absolute |

## Análisis

- **M26 (superviviente, EQUIVALENTE).** Quitar `desmontarSugerencias = null;`
  de `retirarSugerencias` deja guardada la función de desmontaje ya usada. La
  siguiente llamada la ejecuta otra vez, y es idempotente: `removeEventListener`
  de una escucha ya quitada no hace nada y `panel.remove()` de un nodo sin padre
  tampoco. Ningún comportamiento observable cambia (lo comprueba la llamada
  doble de `test_f042_r2_un_solo_panel_y_sin_huerfanos`, que da `[0, 0]` con y
  sin la línea). Se mantiene porque suelta el cierre (campo y panel viejos) para
  el recolector de basura, no por comportamiento.
- **M18 (muerto en la segunda pasada; era un hueco real).** Sin
  `panel.style.maxHeight = ""` antes de medir, `offsetHeight` sale limitado por
  el `max-height` de la colocación anterior: con la ventana baja el panel se
  recorta y al agrandarla ya no recupera su alto. El DOM de prueba de la
  primera pasada no modelaba el `max-height` en línea, y por eso sobrevivía.
  Ahora lo modela (como el navegador) y lo mata
  `test_f042_r2_al_agrandar_la_ventana_recupera_el_alto`.
- **M36 (vuelve el panel dentro de la fila)** solo lo mata el estático de R1:
  en comportamiento es equivalente, porque `montarAutocompletado` lo mueve
  igualmente a `<body>` (`appendChild` de un nodo ya colgado lo traslada). Lo
  que R1 exige es que el editor no lo cuelgue de la fila.
- **M35 (renderTabla no retira)** solo lo mata el estático de R1:
  `renderTabla` toca el DOM real de la tabla y no se ejecuta en node. Lo que
  hace `retirarSugerencias` sí está fijado por comportamiento (M25, M30-M32).
- **M38 (CSS a `absolute`)** es la causa original del fallo; lo mata el
  estático del CSS. Que el panel se vea en la última fila de un navegador real
  lo comprueba el humano (MANUAL en `progress/current.md`, F-042).
- **M29/M30 (captura)**: el DOM de prueba quita una escucha solo si coincide la
  fase, como el navegador; por eso quitar el `true` de un lado u otro deja una
  escucha huérfana y cae `test_f042_r2_un_solo_panel_y_sin_huerfanos`.

## Script

```python
# mutacion_manual_f042.py (fuera del repo, a propósito)
"""Campaña de mutación manual de F-042 sobre `app.js` y `styles.css`.

Se ejecuta desde la raíz del repositorio. Por cada mutante: copia
`static/js/app.js`, `static/css/styles.css` y `tests/` del front a un
directorio temporal, aplica la sustitución en su fichero (el texto original
tiene que aparecer UNA sola vez; si no, aborta), comprueba la sintaxis de
`app.js` con `node --check`, pasa `tests/test_f042_sugerencias.py` sin `-x` y
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
TEST = "tests/test_f042_sugerencias.py"
JS = "static/js/app.js"
CSS = "static/css/styles.css"

M = [
    ("M1", "HUECO 4 -> 0", JS,
     "const HUECO = 4;", "const HUECO = 0;"),
    ("M2", "MARGEN 8 -> 0", JS,
     "const MARGEN = 8;", "const MARGEN = 0;"),
    ("M3", "ancho: min -> max", JS,
     "const ancho = Math.min(430,", "const ancho = Math.max(430,"),
    ("M4", "ancho con un solo margen", JS,
     "ventana.ancho - 2 * MARGEN);", "ventana.ancho - MARGEN);"),
    ("M5", "left sin margen izquierdo", JS,
     "const left = Math.max(MARGEN,", "const left = Math.max(0,"),
    ("M6", "left sin tope derecho", JS,
     "Math.max(MARGEN, Math.min(campo.left, ventana.ancho - MARGEN - ancho));",
     "Math.max(MARGEN, campo.left);"),
    ("M7", "abajo sin hueco ni margen", JS,
     "const abajo = ventana.alto - campo.bottom - HUECO - MARGEN;",
     "const abajo = ventana.alto - campo.bottom;"),
    ("M8", "arriba sin hueco ni margen", JS,
     "const arriba = campo.top - HUECO - MARGEN;",
     "const arriba = campo.top;"),
    ("M9", "cabe justo: > -> >=", JS,
     "const haciaArriba = alto > abajo && arriba > abajo;",
     "const haciaArriba = alto >= abajo && arriba > abajo;"),
    ("M10", "empate de sitio: > -> >=", JS,
     "const haciaArriba = alto > abajo && arriba > abajo;",
     "const haciaArriba = alto > abajo && arriba >= abajo;"),
    ("M11", "arriba siempre que no quepa", JS,
     "const haciaArriba = alto > abajo && arriba > abajo;",
     "const haciaArriba = alto > abajo;"),
    ("M12", "altoMax sin suelo 0", JS,
     "const altoMax = Math.max(0, Math.min(alto, haciaArriba ? arriba : abajo));",
     "const altoMax = Math.min(alto, haciaArriba ? arriba : abajo);"),
    ("M13", "altoMax sin limitar al sitio", JS,
     "const altoMax = Math.max(0, Math.min(alto, haciaArriba ? arriba : abajo));",
     "const altoMax = Math.max(0, alto);"),
    ("M14", "altoMax siempre con el sitio de abajo", JS,
     "Math.min(alto, haciaArriba ? arriba : abajo)", "Math.min(alto, abajo)"),
    ("M15", "top hacia arriba con alto sin limitar", JS,
     "campo.top - HUECO - altoMax :", "campo.top - HUECO - alto :"),
    ("M16", "top hacia abajo desde el top del campo", JS,
     ": campo.bottom + HUECO;", ": campo.top + HUECO;"),
    ("M17", "colocar con el panel oculto", JS,
     '  if (panel.classList.contains("oculto")) return;\n  panel.style.maxHeight = "";',
     '  panel.style.maxHeight = "";'),
    ("M18", "sin quitar el maxHeight antes de medir", JS,
     '  panel.style.maxHeight = "";       // alto natural, con el tope del CSS\n',
     ""),
    ("M19", "mide el panel en vez del campo", JS,
     "posicionSugerencias(input.getBoundingClientRect(),",
     "posicionSugerencias(panel.getBoundingClientRect(),"),
    ("M20", "alto de la ventana con su ancho", JS,
     "alto: document.documentElement.clientHeight,",
     "alto: document.documentElement.clientWidth,"),
    ("M21", "sin poner top", JS,
     "  panel.style.top = `${pos.top}px`;\n", ""),
    ("M22", "sin poner left", JS,
     "  panel.style.left = `${pos.left}px`;\n", ""),
    ("M23", "sin poner width", JS,
     "  panel.style.width = `${pos.ancho}px`;\n", ""),
    ("M24", "sin poner maxHeight", JS,
     "  panel.style.maxHeight = `${pos.altoMax}px`;\n", ""),
    ("M25", "retirar no desmonta", JS,
     "  if (desmontarSugerencias) desmontarSugerencias();\n", ""),
    ("M26", "retirar no olvida el desmontaje", JS,
     "  desmontarSugerencias = null;\n}", "}"),
    ("M27", "montar sin retirar el anterior", JS,
     "  retirarSugerencias();\n  document.body.appendChild(panel);",
     "  document.body.appendChild(panel);"),
    ("M28", "panel fuera de body (sin colgar)", JS,
     "  document.body.appendChild(panel);\n", ""),
    ("M29", "scroll sin captura", JS,
     'window.addEventListener("scroll", recolocar, true);',
     'window.addEventListener("scroll", recolocar);'),
    ("M30", "quita el scroll sin captura", JS,
     'window.removeEventListener("scroll", recolocar, true);',
     'window.removeEventListener("scroll", recolocar);'),
    ("M31", "no quita el resize", JS,
     '    window.removeEventListener("resize", recolocar);\n', ""),
    ("M32", "no quita el nodo", JS,
     "    panel.remove();\n  };", "  };"),
    ("M33", "sin escucha de resize", JS,
     '  window.addEventListener("resize", recolocar);\n', ""),
    ("M34", "refrescar no coloca", JS,
     "    colocarSugerencias(input, panel);\n  };", "  };"),
    ("M35", "renderTabla no retira", JS,
     "  retirarSugerencias();             // F-042: el campo de obra se va a rehacer\n",
     ""),
    ("M36", "vuelve el panel dentro de la fila", JS,
     '  sugerencias.className = "sugerencias oculto";\n  editor.appendChild(anadir);',
     '  sugerencias.className = "sugerencias oculto";\n'
     '  anadir.appendChild(sugerencias);\n  editor.appendChild(anadir);'),
    ("M37", "recolocar no hace nada", JS,
     "const recolocar = () => colocarSugerencias(input, panel);",
     "const recolocar = () => {};"),
    ("M38", "CSS vuelve a absolute", CSS,
     "position: fixed; left: 0; width: 430px;",
     "position: absolute; left: 0; width: 430px;"),
]


def correr(textos: dict[str, str]) -> tuple[str, list[str], str]:
    with tempfile.TemporaryDirectory(prefix="mm_f042_") as tmp:
        raiz = Path(tmp)
        for rel, texto in textos.items():
            (raiz / rel).parent.mkdir(parents=True, exist_ok=True)
            (raiz / rel).write_bytes(texto.encode("utf-8"))
        shutil.copytree(FRONT / "tests", raiz / "tests",
                        ignore=shutil.ignore_patterns("__pycache__"))
        chk = subprocess.run(["node", "--check", JS], cwd=raiz,
                             capture_output=True, text=True)
        if chk.returncode != 0:
            return "SINTAXIS", [], ""
        r = subprocess.run([PYTHON, "-m", "pytest", TEST, "-q", "-rA",
                            "--tb=no", "-p", "no:cacheprovider"], cwd=raiz,
                           capture_output=True, text=True, encoding="utf-8")
        caidos = sorted(set(re.findall(
            r"^(?:FAILED|ERROR) tests/test_f042_sugerencias\.py::(\w+)",
            r.stdout, re.MULTILINE)))
        resumen = r.stdout.strip().splitlines()[-1]
        return ("MUERTO" if r.returncode else "SUPERVIVIENTE"), caidos, resumen


def main() -> None:
    originales = {rel: (FRONT / rel).read_bytes().decode("utf-8")
                  for rel in (JS, CSS)}
    estado, caidos, resumen = correr(originales)
    print(f"Línea base: {estado} · {resumen}")
    if estado != "SUPERVIVIENTE":
        sys.exit("la línea base no está en verde: la campaña no vale")
    for ide, desc, rel, antes, despues in M:
        original = originales[rel]
        n = original.count(antes)
        if n != 1:
            sys.exit(f"{ide}: el original aparece {n} veces, tiene que ser 1")
        linea = original[:original.index(antes)].count("\n") + 1
        textos = dict(originales)
        textos[rel] = original.replace(antes, despues)
        estado, caidos, resumen = correr(textos)

        def esc(s: str) -> str:
            return " ".join(s.split()).replace("|", "\\|") or "(nada)"

        print(f"| {ide} {desc} | `{Path(rel).name}:{linea}` | `{esc(antes)}` → "
              f"`{esc(despues)}` | {estado} | {len(caidos)} | "
              f"{', '.join(caidos) or '—'} |", flush=True)


if __name__ == "__main__":
    main()
```
