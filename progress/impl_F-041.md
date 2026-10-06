# F-041 · Informe del implementer — El filtro de obra casa con el texto visible

Rama `feature/F-041-filtro-obra-postventa`, en la copia
`C:\Users\pgris\PycharmProjects\porcentajes-f041`. Rigor **estándar**,
`sdd: true`, spec aprobada por el humano el 2026-10-06 (D1-D4 = A). Hechas
T1-T5 y T7; **T6 es MANUAL (humano)**, pasos al final. Servicio: **solo
`dedicacion-front`**; api y transfer intactos. Nada escrito en Sigrid ni en
ninguna base. No tocados: `progress/current.md`, `harness/features.json`,
`.env`, `azure-apps/` (F-041 no cambia lo que exponemos ni consumimos).

**Tests anteriores que cambian: NINGUNO** (lista cerrada de requirements §7).
Ninguno cayó en ningún momento: tras T3 y tras T4, los 53 del front en verde;
`services/dedicacion-transfer/tests/test_f013_sin_partida.py` (lee `app.js`),
`44 passed`.

## Qué cambió, por tarea

| Commit | Tarea |
|---|---|
| `b388a36` T1 | `services/dedicacion-front/tests/test_f041_filtro_obra.py` (nuevo, 26 tests): estáticos y de lógica en node (ayudante `_node`, `pytest.skip` con motivo si no hay `node`) |
| `9788221` T2 | `app.js`: `etiquetaObra`, `textoObra` y `lineaCasa` tras `normalizar` (design §3, literal) |
| `72e29ec` T3 | `app.js`: `construirCatalogoObras` con `etiquetaObra`/`textoObra` y sin el alias `"postv postventa postv-"` (D1); chip de `construirCelda` y de `chipEditable` con `etiquetaObra` |
| `a448ffc` T4 | `app.js`: `trabajadoresVisibles` casa la columna por línea con `lineaCasa` (D2) y el buscador global con `textoObra`; fuera la rama `asignaciones` de `textoColumna` |
| `1a0019c` | Ajuste: la edición de T2 dejó escapes `\u00xx` literales en los tres comentarios nuevos; restituidas las tildes (solo comentarios, el código no cambia) |
| `badfbc2` T5 | `progress/mutacion_manual_F-041.md`: campaña manual, 20 mutantes, 0 supervivientes |
| `93c1a0e` | Ajuste: `itertools.pairwise` en el test de R5 (el test nuevo añadía el aviso RUF007 a ruff; ahora 0 avisos en el fichero) |

Diff de producción: solo `services/dedicacion-front/static/js/app.js`
(+36/−20 frente a `e1080e7`). Sin dependencias nuevas, sin cambios en
`index.html` ni `styles.css`.

### Decisiones de diseño (dentro de la spec)

- Funciones y usos **tal cual** design §3-§4; el orden de las claves del objeto
  del catálogo se mantiene (`obra, pv, cod, clave`), que es lo que fija
  `test_f025_r22_*`.
- El chip de la tabla pasa de `"Postv-" + escapeHtml(cod)` a
  `escapeHtml(etiquetaObra(cod, pv))`: el HTML resultante es idéntico
  (`Postv-` no tiene nada que escapar).
- **Regex de R3 y R13 sin acento grave.** El design pide «el literal
  `"Postv-"` una sola vez». Con la primera versión, que contaba también
  `` `Postv-` ``, el test se tropezaba con los comentarios de `app.js` (que
  escriben `Postv-` entre acentos graves, como Markdown). Quedó: comillas
  dobles o simples **una** vez, y aparte se prohíbe `Postv-${` (plantilla con
  código). Para `VAR`: ni `"VAR` ni `'VAR` en todo el fichero (lo literal del
  design), y `` `VAR `` prohibido fuera de comentarios: la copia de F-039 ya
  trae un comentario «Partida VAR fija» (sin comillas) y no debe romper esto
  al mergear.
- **R11** se comprueba en las dos direcciones sobre 15 textos: línea que casa
  ⇒ su fila se ve en la columna y su entrada (obra, modo), si está en el
  catálogo, es candidata; candidata ⇒ toda línea de esa obra y modo casa. Y,
  para que no sea vacuo, `postv` → solo `1|true`, `pos` → `1|true, 2|false`.
- **R12**: la ordenación la cubre el test de node (`0656` → `0656` antes que
  `Postv-0656`); la precarga del diálogo, un estático mínimo (las aserciones
  completas siguen en `test_f029_r10_*`, no se duplican).
- La verificación de T2 en tasks.md (`-k "r1 or r2"`) también selecciona
  r10-r13, que son de T3/T4: con ella salían 4 fallos esperados. Verificado
  con la selección exacta `-k "r1_ or r2_"`: `4 passed`.

## Fase RED (trazas reales)

**T1 · antes de existir el código** (`9b5fc46` + test nuevo), desde
`services/dedicacion-front`:

```
$ .venv/Scripts/python -m pytest tests/test_f041_filtro_obra.py -q -rs --tb=line
E   AssertionError: no existe la función etiquetaObra en app.js     (×14)
E   AssertionError: no existe la función textoObra en app.js
E   AssertionError: no existe la función lineaCasa en app.js
tests\test_f041_filtro_obra.py:180: AssertionError: ['"Postv-"', '"Postv-"', '"Postv-"']
25 failed, 1 passed in 0.51s
```

Sin ningún `skipped` (node v24.14.1). El único que pasa es
`test_f041_r12_dialogo_sigue_precargado_con_filtrar_obra`, que vigila que la
precarga **no cambie** (R12): pasar antes es lo correcto.

**Tras T2 · las funciones existen, los usos aún no** (la RED de comportamiento
de los requisitos centrales, con el `app.js` de antes en los usos):

```
$ .venv/Scripts/python -m pytest tests/test_f041_filtro_obra.py -q -rs --tb=short
____________ test_f041_r4_d2_naves_postv_no_casa_a_caballo ____________
    assert _columna(["naves postv"]) == {"naves postv": []}
E   AssertionError: assert {'naves postv': ['Carla']} == {'naves postv': []}
__________ test_f041_r9_buscador_global_encuentra_postventa ___________
    assert res["postv"] == ["Ana", "Carla"]
E   AssertionError: assert [] == ['Ana', 'Carla']
__________________ test_f041_r10_catalogo_en_node _____________________
E     At index 1 diff: [1, True, 'Postv-0656', 'postv postventa postv-0656 0656 edificio arroyo'] != [1, True, 'Postv-0656', 'postv-0656 edificio arroyo']
_________________ test_f041_r10_d1_postventa_no_casa __________________
E   AssertionError: assert {'postventa': ['Postv-0656']} == {'postventa': []}
______ test_f041_r11_columna_y_completar_parten_del_mismo_texto _______
E   Failed: 'postventa': candidata 1|true sin casar {'clave': '1|true', 'nombre': 'Ana', 'casa': False}
14 failed, 12 passed in 7.73s
```

Es justo el fallo del humano: el buscador global no encuentra ninguna `Postv-`
(R9), la columna casa «a caballo» entre dos chips (D2) y el catálogo casa con
un alias que no se ve (D1, R10, R11). Los otros 9 fallos eran estáticos de R3,
R4, R9 y R10 (usos sin cambiar). Tras T3: `13 passed` en
`-k "r3 or r10 or r11 or r12 or r13"`; quedaban en rojo solo R4 y R9 (5
tests), que pasaron en T4.

**Lo que ya pasaba con el `app.js` de antes** (honestidad sobre el alcance de
la RED): R5-R8 y R13 en la **columna** dan lo mismo antes y después con estos
datos (requirements §0: la columna ya casaba `pos`/`postv`). Su RED es la de
T1 (las funciones no existían); lo que les cambia F-041 es la fuente del
texto, y lo vigilan los mutantes M3, M4, M10-M12 y M16, todos muertos.

## Mutación

`python -m harness.mutacion --feature F-041` (salida real): «ALCANCE VACÍO en
F-041: ni una línea de producción que mutar … No se escribe informe». Solo
muta Python; lo de producción de F-041 es JavaScript. Por eso **no existe
`progress/mutacion_F-041.md`** y lo sustituye la campaña manual (design §7):
`progress/mutacion_manual_F-041.md`, con la tabla reproducible (texto exacto
original → mutado, test que lo mata, nº de fallos), el análisis y el script.

**Resultado: 20 mutantes, 20 muertos, 0 supervivientes.** Incluye los ocho
mínimos de design §7. M14/M15 (los chips, que tocan el DOM) solo los matan los
estáticos de R3; el resto, también tests de lógica en node.
Medida sobre `1a0019c` y **repetida sobre `93c1a0e`** (tras el ajuste
`pairwise` del test): tabla idéntica fila a fila. `git status` limpio tras
las dos (el script trabaja en un directorio temporal).

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests de F-041 | `26 passed in 4.10s` (`tests/test_f041_filtro_obra.py`, 0 `skipped`, node v24.14.1) |
| Suite del front | `79 passed` (53 anteriores + 26 nuevos), `11.70s` dentro de `init.sh` |
| Transfer `test_f013_sin_partida.py` | `44 passed in 2.25s` |
| Suite global de `init.sh` | `418 passed, 1 skipped in 107.99s` (el `skipped` es previo, ajeno a F-041) |
| Cobertura de líneas cambiadas | **N/A** con motivo impreso por `init.sh`: «F-041 no cambia líneas Python de producción frente a dev». `coverage` no mide JS |
| Mutantes generados / supervivientes | herramienta: alcance vacío (solo Python). Manual: **20 / 0** (`progress/mutacion_manual_F-041.md`) |
| Workers de la campaña manual | 1 (en serie); ~7 s por mutante, línea base `26 passed` |
| `node --check static/js/app.js` | OK tras T2, T3, T4 y el ajuste de tildes |

### `bash harness/init.sh` (desde `porcentajes-f041`)

```
INIT_FINAL
```

## Fuera del alcance

- Ocultar los chips que no casan con el filtro: **F-021** (D3 = A). Con
  «Filtrar obra…» activo la fila sigue pintando todos sus chips; `lineaCasa`
  queda lista para que F-021 decida cuál se ve.
- El alias `postventa` desaparece también del autocompletado (D1 = A, riesgo
  aceptado por el humano): quien escribía `postventa` ahora tiene que escribir
  `postv`.
- `pintarModalPreflight` (lo toca F-039) no se ha tocado. Riesgo de merge con
  F-039: ninguna función en común; quien entre segundo pasa la suite del front.

## Qué falta para cerrar

1. Review contra `CHECKPOINTS.md`.
2. **T6, MANUAL (humano)**, en local, antes de desplegar (abajo). Su resultado
   va a `progress/current.md` (lo escribe el líder, no el implementer).
3. Marcar `[x]` T6 y T7 en `tasks.md` tras la review (T7 hecha: init en verde).

## MANUAL (humano) · T6, prueba en local

F-041 no cambia la api: se usa la de siempre. Todo en local, nada contra Azure.

1. Arrancar la api local como siempre:
   `cd C:\Users\pgris\PycharmProjects\porcentajes\services\dedicacion-api` y
   `.venv\Scripts\python main.py` (puerto 8090).
2. Parar cualquier otro front que esté en el 8080 y arrancar el de la rama:
   `cd C:\Users\pgris\PycharmProjects\porcentajes-f041\services\dedicacion-front`
   y `.venv\Scripts\python main.py`.
3. Abrir `http://127.0.0.1:8080`, **Ctrl+F5** (para no usar un `app.js` en
   caché) y elegir un periodo con líneas `Postv-`.
4. En «Filtrar obra…» escribir, letra a letra, `p`, `po`, `pos`, `post`,
   `postv`, `postv-` y el código de una `Postv-` (`postv-0656`, por ejemplo).
   Esperado: con `pos` salen todos los que tienen alguna `Postv-` (y quien
   tenga una obra con «pos» en el nombre, p. ej. «Depósito»); desde `post`,
   solo los de postventa; con cada letra, la lista igual o más corta.
5. Esc, y lo mismo en el buscador global (tecla `/`). Esperado: el mismo
   comportamiento (antes no encontraba ninguna `Postv-`).
6. Escribir `postventa` en «Filtrar obra…». Esperado: **nadie** (D1 = A).
7. Escribir un trozo del nombre de una obra con tilde, sin ella y en
   mayúsculas (`DEPOSITO`). Esperado: casa igual que con la tilde.
8. Si hay alguien con una obra normal y una `Postv-` de otra obra: escribir
   «nombre de la normal» + ` postv` (p. ej. `naves postv`). Esperado: esa fila
   ya **no** sale en la columna (D2), pero sí en el buscador global.
9. Con `postv` en «Filtrar obra…», seleccionar dos filas (Ctrl+clic) y pulsar
   **C**. Esperado: el diálogo sale precargado con `postv` y solo ofrece
   entradas `Postv-`. **Cerrar con Esc, sin completar** (no escribe nada).
10. «Limpiar»: la tabla queda como antes de filtrar (mismas filas, mismo orden).

Resultado de cada paso a `progress/current.md`.
