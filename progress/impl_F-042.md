# F-042 · Informe del implementer — El desplegable de obras en la última fila

Rama `feature/F-042-ultima-fila-autocompletado` (copia principal). Rigor
**estándar**, `sdd: false`: los criterios son los `acceptance` de F-042 y el
**plan A** aprobado por el humano el 2026-10-07 (`progress/current.md`, F-042).
Servicio: **solo `dedicacion-front`**; api y transfer intactos. Nada contra
Azure ni Sigrid. Sin dependencias nuevas. `azure-apps/` no se toca: F-042 no
cambia lo que exponemos ni consumimos.

**Tests anteriores que cambian: NINGUNO.** Los que leen las funciones tocadas
(`test_f025_r23_*` y `test_f029_r10_*` sobre `montarAutocompletado`,
`test_f029_r3_*` sobre `renderTabla`, y `test_f013_sin_partida.py` del transfer,
que lee `app.js`) siguen en verde sin tocarlos.

## Causa (acceptance 1: reproducida y explicada con evidencia)

Lectura del código en `2d16185` (antes de F-042):

- `app.js`, `pintarEditor`: el panel se creaba **dentro** de la fila del editor:
  `sugerencias.className = "sugerencias oculto"; anadir.appendChild(sugerencias);`
  y `montarAutocompletado` lo rellenaba y le quitaba `oculto` al escribir.
- `styles.css` línea 380: `.sugerencias { position: absolute; top: 40px; left:
  0; width: 430px; max-height: 280px; … }`, relativo a `.anadir { position:
  relative }`.
- `styles.css` líneas 229-234: la tabla vive en `.panel { … overflow: hidden; }`
  y `.panel-tabla { overflow-x: auto; }`. Un `overflow` distinto de `visible`
  recorta a sus descendientes `absolute`; y `overflow-x: auto` fuerza también
  `overflow-y` a `auto`.
- En una fila intermedia, los 280 px del panel caen sobre las filas de abajo,
  que están dentro del contenedor: se ve. En la **última**, debajo solo queda
  el borde del `.panel`: el panel queda fuera de la caja y se recorta. La
  búsqueda sí corre (el `input` dispara `refrescar` igual), pero no se ve: es
  justo lo que contó el humano («si reordeno y no está el último, funciona»).
- Comprobado además que **ningún ancestro** de la tabla tiene `transform`,
  `filter`, `contain`, `will-change` ni `perspective` (grep en `styles.css`:
  el único `backdrop-filter` es de `.topbar`, que no es ancestro), y que no hay
  ningún manejador global de «clic fuera» que cierre el editor: colgar el
  panel de `<body>` no rompe nada.

Reproducción en navegador: la hace el humano (MANUAL abajo). Aquí se fija con
los tests estáticos de R1 y, en node, con el código real en la última fila.

## Qué cambió, por tarea

| Commit | Tarea |
|---|---|
| `12272a9` T1 | `services/dedicacion-front/tests/test_f042_sugerencias.py` (nuevo, 17 tests): estáticos, lógica en node y ciclo de vida en node con un DOM mínimo de prueba. En rojo |
| `5add8eb` T2 | `app.js` y `styles.css`: el panel cuelga de `<body>`, `position: fixed`, se coloca junto al campo (`posicionSugerencias` + `colocarSugerencias`), se recoloca con scroll y resize y se retira con `retirarSugerencias` |
| `4e502a5` T3 | Test nuevo `test_f042_r2_al_agrandar_la_ventana_recupera_el_alto`: hueco que dejó vivo el mutante M18 (el DOM de prueba no modelaba el `max-height` en línea) |
| `0e2e0a9` T4 | `progress/mutacion_manual_F-042.md`: 38 mutantes, 37 muertos, 1 equivalente |

Diff de producción: `app.js` +64/−2 (funcional: +4 funciones/variable y 3
llamadas) y `styles.css` +4/−1.

### `app.js`

- `pintarEditor`: el panel se sigue creando ahí y se pasa a
  `montarAutocompletado(inputObra, sugerencias, editor)` (misma firma), pero
  **ya no** se cuelga de `.anadir`.
- `let desmontarSugerencias = null;` — un solo panel vivo a la vez; guarda cómo
  quitarlo (nodo y escuchas).
- `posicionSugerencias(campo, alto, ventana)` — **función pura** (sin DOM):
  debajo del campo con 4 px de hueco; si debajo no cabe **y encima hay más
  sitio**, encima; el alto se limita al sitio del lado elegido (nunca < 0); el
  ancho es `min(430, ventana − 16)` y `left` se acota a [8, ventana − 8 − ancho].
- `colocarSugerencias(input, panel)` — si el panel está abierto, quita su
  `max-height` en línea, mide su alto natural, llama a la función pura con el
  `getBoundingClientRect()` del campo y el tamaño de la ventana
  (`documentElement.clientHeight/clientWidth`, sin barras de scroll) y pone
  `top`, `left`, `width` y `max-height`.
- `retirarSugerencias()` — ejecuta el desmontaje vivo (si lo hay) y lo olvida.
- `montarAutocompletado`: al empezar, `retirarSugerencias()` y
  `document.body.appendChild(panel)`; escucha `scroll` **en captura** (el
  scroll horizontal de `.panel-tabla` no burbujea) y `resize`; el desmontaje
  quita ambas (con la misma fase) y el nodo. `refrescar` llama a
  `colocarSugerencias` justo después de mostrar u ocultar el panel.
- `renderTabla`: empieza con `retirarSugerencias()`. Es el punto por el que
  pasan cerrar el editor (`cerrarEditor`), cambiar de fila (`abrirEditor`),
  cambiar de periodo (`aplicarCuadrante`) y cualquier repintado: todos
  destruyen el campo de obra, y su panel se va con él. Los repintados del
  propio editor (`pintarEditor` al elegir, PV o ✕) pasan por
  `montarAutocompletado`, que retira el anterior.

### `styles.css`

`.sugerencias`: `position: fixed`, fuera `top: 40px` (lo pone el JS). Se
mantienen `width: 430px` y `max-height: 280px` como tamaño natural (el JS mide
con ellos); el resto de estilos del panel y de `.sugerencia`, sin cambios (no
dependían de estar dentro de `.editor`).

### Decisiones de diseño (dentro del plan A)

- **Colgado de `<body>`** (el plan lo dejaba «si hace falta»): con `fixed`
  dentro de la fila ya bastaría hoy, porque ningún ancestro crea bloque
  contenedor, pero un `transform` futuro en `.panel` volvería a recortarlo.
  En `<body>` no depende de eso; el riesgo de paneles huérfanos lo cubren
  `retirarSugerencias` en `renderTabla`/`montarAutocompletado` y su test.
- **Abrir hacia arriba solo si encima hay más sitio** que debajo: matiz sobre
  «si no cabe debajo, se abre hacia arriba». Si no cabe en ningún lado (ventana
  muy baja), va donde más sitio hay y recorta su alto (se desplaza por dentro,
  como ya hacía con 14 sugerencias). Sin el matiz, una ventana baja con el
  campo arriba lo abriría hacia arriba en 20 px. En el caso del fallo (última
  fila, ventana normal) se abre hacia arriba siempre.
- **Con scroll, acompaña al campo** (el MANUAL admitía «acompaña o se cierra»).
- **`asset_version` no se toca**: ya es `str(int(time.time()))` en
  `interface_adapters/web/app.py` y cambia en cada arranque, así que el
  `?v=` de `app.js` y `styles.css` rompe la caché al desplegar.
- Sin cambios en el teclado, la búsqueda, `elegir`, el `blur` (150 ms) ni la
  API. El front no decide nada de negocio: solo dónde se pinta un panel.

## Fase RED (trazas reales)

**T1, antes de existir el código** (`2d16185` + test nuevo), desde
`services/dedicacion-front`:

```
$ .venv/Scripts/python -m pytest tests/test_f042_sugerencias.py -q --tb=line -p no:cacheprovider
FFFFFFFFFFFFFF.F.                                                        [100%]
E   AssertionError: no existe la función posicionSugerencias en app.js        (x11)
E   AssertionError: position: absolute; top: 40px; left: 0; width: 430px; max-height: 280px; overflow-y: auto; ...
E   assert 'anadir.appe...sugerencias)' not in 'function pi...acciones); }'
E   AssertionError: function renderTabla() { const cuerpo = $("#cuerpo"); cuerpo.innerHTML = ""; con
E   assert ('const refrescar = () => { ... panel.classList.toggle("oculto", !q || candidatas.length === 0); ' + 'colocarSugerencias(input, panel); };') in 'function montarAutocompletado(...'
FAILED tests/test_f042_sugerencias.py::test_f042_r1_el_panel_es_fixed_y_no_absolute
FAILED tests/test_f042_sugerencias.py::test_f042_r1_el_panel_no_vive_dentro_de_la_fila
FAILED tests/test_f042_sugerencias.py::test_f042_r1_cada_repintado_de_la_tabla_retira_el_panel
FAILED tests/test_f042_sugerencias.py::test_f042_r2_ultima_fila_busca_se_ve_encima_y_se_elige_con_teclado
FAILED tests/test_f042_sugerencias.py::test_f042_r2_ultima_fila_se_abre_hacia_arriba
FAILED tests/test_f042_sugerencias.py::test_f042_r2_un_solo_panel_y_sin_huerfanos
  (… y 9 más de R2/R3: cabe_debajo, si_cabe_justo, si_no_cabe_en_ningun_lado,
   el_alto_nunca_es_negativo, ancho_y_left, fila_intermedia, acompana_al_campo,
   scroll_en_captura, busqueda_identica_y_luego_se_coloca)
15 failed, 2 passed in 0.05s
```

Los 2 que pasan son `test_f042_r3_teclado_identico` y
`test_f042_r3_la_secuencia_pct_enter_obra_no_cambia`: vigilan que el teclado
**no cambie** (acceptance 3); pasar antes es lo correcto. La causa sale literal
en la RED: `position: absolute; top: 40px` y `anadir.appendChild(sugerencias)`.

**Tras T2:** `node --check static/js/app.js` OK; `17 passed in 1.32s`.
**Tras T3:** `18 passed in 1.83s` (el test nuevo pasa con el código de T2; su
RED es el mutante M18, que sobrevivía con 17 tests y muere con 18).

## Mutación

`python -m harness.mutacion --feature F-042` (salida real): «ALCANCE VACÍO en
F-042: ni una línea de producción que mutar … No se escribe informe». Solo muta
Python. La sustituye la campaña manual `progress/mutacion_manual_F-042.md`
(tabla reproducible, análisis y script, patrón de F-041).

**Resultado: 38 mutantes (37 de `app.js`, 1 de `styles.css`), 37 muertos, 1
superviviente EQUIVALENTE (M26).** Primera pasada (17 tests): 2 supervivientes,
M18 (hueco real, cerrado con el test de T3) y M26. M26 quita
`desmontarSugerencias = null;`: el desmontaje es idempotente, así que repetirlo
no cambia nada observable; la línea solo suelta memoria. M35 (`renderTabla`) y
M36 (panel dentro de la fila) solo los matan estáticos: el primero toca el DOM
real de la tabla, y el segundo es equivalente en comportamiento
(`appendChild` lo traslada a `<body>` igual). Detalle, en el informe.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests de F-042 | `18 passed in 2.12s` (`tests/test_f042_sugerencias.py`, 0 `skipped`, node v24.14.1) |
| Suite del front | `100 passed` (82 anteriores + 18 nuevos), `8.57s` dentro de `init.sh` |
| Transfer `test_f013_sin_partida.py` (lee `app.js`) | `44 passed in 0.61s` (relanzado a mano: `init.sh` lo da por caché) |
| Suite global de `init.sh` | `418 passed, 1 skipped in 53.32s` (el `skipped` es previo y ajeno) |
| Cobertura de líneas cambiadas | **N/A**, motivo impreso por `init.sh`: «F-042 no cambia líneas Python de producción frente a dev». `coverage` no mide JS ni CSS |
| Mutantes generados / supervivientes | herramienta: alcance vacío (solo Python). Manual: **38 / 1 equivalente** |
| Campaña manual | 2 min 24 s, 1 worker, ~3,7 s por mutante; línea base `18 passed` |
| `node --check static/js/app.js` | OK tras T2 y al final |
| ruff del test nuevo | `All checks passed!`; el total del repo sigue en 237 avisos (deuda previa) |

### `bash harness/init.sh` (sobre `0e2e0a9`), extracto

```
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 237 avisos (deuda previa, no bloquea)      <- los mismos 237 que antes de F-042
418 passed, 1 skipped in 53.32s
[OK] pytest en verde (con medición de cobertura)
[OK] servicio api (services/dedicacion-api): pytest en verde (caché: árbol sin cambios desde el último verde)
100 passed, 19 warnings in 8.57s
[OK] servicio front (services/dedicacion-front): pytest en verde
[OK] servicio transfer (services/dedicacion-transfer): pytest en verde (caché: árbol sin cambios desde el último verde)
[OK] PUERTA COBERTURA: N/A (F-042 no cambia líneas Python de producción frente a dev)
[OK] Rama actual: feature/F-042-ultima-fila-autocompletado
ENTORNO LISTO. Puedes trabajar.
```

(Tras añadir este informe se vuelve a pasar; el resultado final, al pie.)

## Fuera del alcance

- El diálogo «Completar al 100 %» (F-029) tiene su propia lista de candidatas
  dentro del `.modal` (`overflow: auto`): no es el panel `.sugerencias` y no
  tiene el fallo; no se ha tocado.
- Que el panel siga a la fila activa con las flechas (scroll interno hasta la
  sugerencia marcada) no existía antes y no se añade (teclado sin cambios).
- Plan B (dejar hueco bajo la tabla): descartado por el humano.

## Qué falta para cerrar

1. Review contra `CHECKPOINTS.md`.
2. **MANUAL (humano)**, en local, nada contra Azure: los 7 pasos de
   `progress/current.md` (sección F-042), con Ctrl+F5. Su resultado lo apunta
   el líder en `current.md`.
3. Despliegue (lo lanza el humano, desde `dev`): solo el front.

## Resultado final de `bash harness/init.sh` (sobre `cca97a5`)

Código de salida 0, ningún `[KO]`: `418 passed, 1 skipped in 49.57s`; front,
api y transfer en verde (caché, árbol sin cambios desde el verde anterior);
`PUERTA COBERTURA: N/A` (sin Python de producción); `PUERTA TAMAÑO: impl
208/220`; «ENTORNO LISTO».
