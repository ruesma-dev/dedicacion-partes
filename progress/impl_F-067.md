<!-- progress/impl_F-067.md -->
# F-067 · informe del implementer

Casilla «Recursos vinculados» junto a las fichas del resumen para ver u
ocultar en el CUADRANTE las subfilas de vinculado de F-044. `sdd: false`,
rigor estándar, solo front. Rama `feature/F-067-ver-vinculados` (alta en
`117686d`), worktree `porcentajes-f067` (los `.venv` enlazados a la copia
principal, sin versionar; ningún `.env` leído ni copiado).

## Qué cambió

| Commit | Tarea | Ficheros |
|---|---|---|
| `74808f3` | T1 · tests (fase RED: 12 en rojo) | `services/dedicacion-front/tests/test_f067_ver_vinculados.py` (nuevo) |
| `d5117a8` | T2 · casilla, preferencia, filtrado y filas | `services/dedicacion-front/static/js/app.js`, `services/dedicacion-front/static/css/styles.css`, el test (quitada la referencia a una función auxiliar, ver «Decisiones») |
| `7016870` | T3 · test por el superviviente N9 de la campaña 1 | el test |
| (este) | campaña, informe y rastro; `check=False` en el test (ruff) | `progress/mutacion_manual_F-067.md` (nuevo), `progress/current.md` (MANUAL), el test, este informe |

En `app.js` (+61 / −10; `styles.css` +3):

- `state.verVinculados: true` (defecto marcada).
- `cargarPrefsTabla`: `state.verVinculados = datos.verVinculados !== false;`
  dentro del `try` existente: solo un `false` guardado la desmarca; unas
  preferencias antiguas sin la clave, nada guardado o un `localStorage` que
  lanza la dejan marcada. `guardarPrefsTabla` la escribe junto a `orden` y
  `anchos` en la misma clave `dedicacion:tabla:v1`.
- `renderCabecera`: detrás de las fichas de estado e incidencia, si alguna
  línea del mes trae `vinculados` no vacío, un `<label class="check
  chk-vinculados">` con su `<input type="checkbox">` (marcado según el
  estado) y el rótulo «Recursos vinculados». Al cambiar: guarda el estado,
  `guardarPrefsTabla()` y `renderTabla()`.
- `construirFila`: con la casilla desmarcada no se construye ninguna subfila
  de vinculado. El `rowSpan` ya se calculaba con las filas pintadas
  (`trs.length`), así que cuadra solo con líneas e incidencias.
- `textoColumna(t, clave, conVinculados = true)`: con `false`, «Tipo
  recurso» es solo «Persona». `trabajadoresVisibles`: con la casilla
  desmarcada, la rama de «Partida» no mira las elegidas de las subfilas y
  «Tipo recurso» tiene su propia rama, que llama a `textoColumna(t, clave,
  false)`. Marcada, todo como hoy.
- `styles.css`: la casilla algo más pequeña que «Solo pendientes» (rótulo
  0,8rem, casilla 13 px).

No cambian el modal de registro (`pintarModalPreflight`, `fila-vinculado-reg`,
`marcadaPorDefecto`), el buscador libre (no miraba vinculados), el editor,
la api ni el transfer. Ningún texto nuevo nombra motivos de conflicto (test
de F-013 R4 del transfer en verde, `42 passed`). `azure-apps/` no cambia
(no cambia lo que se expone ni se consume). Ningún test existente cambia.

## Decisiones

- **Casilla dentro de `#resumen`, como último hijo**: es «junto a las
  fichas» y se repinta con ellas; con la clase `check` de «Solo pendientes»
  (mismo aspecto, ya pequeño) y un rótulo en un `<span>` (un `textContent`
  en el `<label>` borraría el `<input>`).
- **«El mes tiene algún vinculado» va en línea en `renderCabecera`**, no en
  una función aparte: el arnés node de F-063 (y F-065) carga
  `renderCabecera` con una lista cerrada de funciones y una nueva lo ponía en
  rojo (16 fallos con `ReferenceError`). Cambiar esa lista era tocar tests
  ajenos; se dejó como estaba. El test de F-067 escrito en RED la cargaba
  si existía; en T2 se quitó esa referencia (nada de sus aserciones).
- **Rama propia para «Tipo recurso» desmarcado**: el estático de F-041 R4
  (`test_f041_r4_la_columna_casa_por_linea`) fija el texto exacto de la línea
  genérica `normalizar(textoColumna(t, clave)).includes(filtro)`; pasarle el
  tercer argumento lo ponía en rojo. La línea queda intacta.
- **`state.verVinculados !== false` en `construirFila` y en el filtrado**
  (en la casilla y en las preferencias se usa el booleano tal cual): los
  arneses node de F-044 montan un `state` sin la clave y esperan las subfilas
  (el defecto es marcada). En la aplicación el valor es siempre booleano,
  así que en el filtrado el cambio a `=== true` es equivalente (N18, abajo).
- **La casilla solo sale si alguna línea trae `vinculados` no vacío**: la api
  solo manda la clave si hay alguno (`LineaOut.vinculados`, `exclude_if`).
  Una preferencia desmarcada en un mes sin vinculados no se ve ni se pierde.
- **Solo pantalla**: la preferencia solo la leen o escriben `renderCabecera`,
  `cargarPrefsTabla`, `guardarPrefsTabla`, `trabajadoresVisibles` y
  `construirFila` (lo fija un estático); ninguna función del modal ni del
  registro.
- **Fuera**: ocultar por tipo de vinculado (lo dice la feature). Tras pulsar
  la casilla el foco queda en ella y ↑↓/Enter no mueven el cursor hasta salir
  de ella, igual que con «Solo pendientes» (comportamiento existente del
  manejador de teclas, no se toca).

## Fase RED (T1, antes de tocar `app.js`)

Tests escritos sobre `117686d` (sin código de F-067). Comando, desde
`services/dedicacion-front`:

```
.venv/Scripts/python.exe -m pytest tests/test_f067_ver_vinculados.py -q -p no:cacheprovider --tb=line
```

Salida real (resumida a las líneas `E` y el resumen; trazas de node
recortadas):

```
FF.F.FFFFFFFF..F                                                         [100%]
E   AssertionError: assert [('fila selec...la', 2, None)] == [('fila selec...la', 2, None)]
      At index 1 diff: ('fila fila-vin seleccionada subfila', 0, 10) != ('fila seleccionada subfila', 1, None)
E   assert [None, 10, 11, None] == [None, None]
E   assert (<re.Match object; span=(2216, 4158), match='const state = {\n  anio: 0,\n ...> and None)
E   assert True is False
E   AssertionError: assert {'orden': ['t...'total': 200}} == {'orden': ['t...lados': False}
      Right contains 1 more item:
      {'verVinculados': False}
E   AssertionError: [stdin]:372
        c.input.checked = valor;
      TypeError: Cannot read properties of null (reading 'input')
E   AssertionError: assert ['Ana'] == []
E   AssertionError: assert ['Benito', 'Carla'] == ['Benito']
E   AssertionError: assert 6 == (6 + 1)
     +  where 6 = len(['3 trabajadores', '2 OK', '0 sin carga', '1 falta', '0 exceso', 'V Vacaciones 1'])
E   AssertionError: [stdin]:372
        c.input.checked = valor;
      TypeError: Cannot read properties of null (reading 'input')
E   TypeError: 'NoneType' object is not subscriptable
E   AssertionError: assert set() == {'cargarPrefs...oresVisibles'}
FAILED tests/test_f067_ver_vinculados.py::test_f067_r1_desmarcada_ninguna_subfila_de_vinculado_y_rowspan_cuadra
FAILED tests/test_f067_ver_vinculados.py::test_f067_r1_desmarcada_sin_incidencias_rowspan_de_las_lineas
FAILED tests/test_f067_ver_vinculados.py::test_f067_r1_el_estado_arranca_marcado
FAILED tests/test_f067_ver_vinculados.py::test_f067_r2_se_recupera_lo_guardado
FAILED tests/test_f067_ver_vinculados.py::test_f067_r2_se_guarda_con_las_de_la_tabla_y_vuelve
FAILED tests/test_f067_ver_vinculados.py::test_f067_r2_sin_localstorage_la_pagina_funciona_marcada
FAILED tests/test_f067_ver_vinculados.py::test_f067_r3_tipo_recurso_desmarcada_solo_persona
FAILED tests/test_f067_ver_vinculados.py::test_f067_r3_partida_desmarcada_solo_las_lineas
FAILED tests/test_f067_ver_vinculados.py::test_f067_r1_la_casilla_sale_marcada_junto_a_las_fichas
FAILED tests/test_f067_ver_vinculados.py::test_f067_r2_desmarcar_guarda_y_repinta_la_tabla
FAILED tests/test_f067_ver_vinculados.py::test_f067_r2_con_la_preferencia_desmarcada_la_casilla_sale_desmarcada
FAILED tests/test_f067_ver_vinculados.py::test_f067_r4_solo_pantalla_la_preferencia_no_llega_al_registro
12 failed, 4 passed in 9.83s
```

Todos caen por lo que hace la pantalla (subfilas pintadas, filtros que ven
el teléfono, preferencia no guardada, casilla inexistente), no por un nombre
que falta. Pasan en RED las cuatro guardas de «como hoy»: marcada = el
cuadrante de hoy, prefs antiguas sin la clave = marcada, el modal igual en
los dos estados y sin vinculados no hay casilla (tienen que estar en verde
antes y después; la campaña demuestra que muerden: N1, N3, N6, N8, N15,
N16, N24). Tras T2: `100 passed in 26.34s` en F-067 + F-041 + F-044 + F-063
+ F-064 + F-065.

## Tests (`test_f067_ver_vinculados.py`, 17; sin red ni BBDD)

Código REAL de `app.js` en node: el DOM de mentira de F-063 (fichas con su
clic) más un `localStorage` de mentira (o uno que lanza), el arnés de filas
de F-044 y el del modal de F-064. Dobles con la forma de la api: `LineaOut`
con `vinculados` solo si hay alguno y las subfilas `TEL`/`GAS` de F-044
(todas las claves de `SubfilaOut`). Por criterio:

- **R1**: desmarcada, sin subfilas de vinculado y `rowSpan` 3 (2 líneas + 1
  incidencia) o 2 (sin incidencias); marcada, las 5 filas y `rowSpan` 5;
  el estado arranca `verVinculados: true`; la casilla sale marcada detrás
  de las fichas, con rótulo y clase `check`.
- **R2**: sin nada guardado o con prefs antiguas, marcada (y los anchos se
  leen igual); `false`/`true` guardados se recuperan; guardar escribe
  `orden`, `anchos` y `verVinculados` y vuelve al cargar; desmarcar guarda y
  repinta la tabla; con la preferencia desmarcada la casilla sale
  desmarcada; con `localStorage` que lanza, marcada y la casilla funciona.
- **R3**: «Tipo recurso» `telefono`/`co-11` solo encuentra con la casilla
  marcada, `persona` en los dos; «Partida» `ciga14` encuentra la línea de
  Benito en los dos y la subfila de Carla solo marcada; `automatica`, igual
  en los dos.
- **R4**: el HTML del modal y las casillas marcadas (el pisado del
  vinculado) son idénticos con la casilla marcada o no, con
  `fila-vinculado-reg`; estático: ninguna función del modal o del registro
  lee la preferencia.
- **R5**: sin vinculados en el mes, ninguna casilla (y las fichas, las de
  siempre); con un único vinculado bajo la segunda línea de un trabajador,
  sale.

## Mutación manual del JS

`harness.mutacion` solo muta Python; la campaña manual, reproducible, está en
`progress/mutacion_manual_F-067.md` (SHA completo, línea base, workers,
tiempo, una fila por mutante, análisis y el script). Campaña 2 sobre
`7016870ad9b64deab5ae72ef55ef07511e39f8db`, 1 worker, 917,7 s: **27
mutantes, 26 muertos, 1 superviviente**.

- La campaña 1 (sobre `d5117a8`) dejó N9 (`every` en vez de `some` en las
  líneas) muerto solo de rebote, por los trabajadores sin líneas de F-063;
  T3 añade un test que lo mata por sí mismo y se repitió la campaña entera.
- **N18** (en el filtrado, `!== false` → `=== true`) sobrevive y es
  **equivalente**: la preferencia es siempre booleana en la aplicación
  (arranca `true`; solo la escriben `cargarPrefsTabla`, con el booleano
  `!== false`, y la casilla, con `input.checked`). El mismo cambio en
  `construirFila` (N24) muere por los tests de F-044. Análisis en la
  campaña.

## Pendiente (MANUAL)

La comprobación en el navegador (vale en producción tras desplegar el
front: solo mirar, marcar y desmarcar; el modal, solo mirar y Cancelar):
pasos exactos en `progress/current.md`, «⚠ Lo que espera al humano»,
entrada F-067.

## Fuera del alcance

- Ocultar por tipo de vinculado (lo excluye la feature).
- Cualquier cambio del modal de registro, de la api o del transfer.
- Desplegar: lo decide el humano tras la review.

## Evidencias

`bash harness/init.sh` tal cual, solo, sobre `7016870` más este papeleo
(2026-10-28), tras `rm -f .arnes_cache/suite_*.ok` (las tres suites
corrieron de verdad): «ENTORNO LISTO. Puedes trabajar.», **sin ningún
[KO]** (el [AVISO] de ruff dio 310: el aviso nuevo era `PLW1510` del test,
corregido después con `check=False`, sin cambio de comportamiento).

| Evidencia | Valor real |
|---|---|
| Tests de la raíz | 418 passed, 1 skipped en 83,34 s |
| Tests de la api | 1308 passed en 124,63 s |
| Tests del front | 451 passed en 116,03 s (434 de antes + 17 de F-067; F-041/F-044/F-063/F-064/F-065 sin tocar) |
| Tests del transfer | 1585 passed en 55,98 s (F-013 R4 incluido) |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: N/A (F-067 no cambia líneas Python de producción frente a dev)`; el JS no tiene medidor de cobertura |
| Mutantes | `harness.mutacion` no aplica (no hay Python de producción). Campaña manual del JS (`progress/mutacion_manual_F-067.md`, `7016870ad9b64deab5ae72ef55ef07511e39f8db`, 1 worker, 917,7 s): **27 generados, 26 muertos, 1 superviviente** (N18, equivalente, analizado) |
| Pasada final | sobre `2a4fd90`, cachés borradas: sin [KO], ruff 309 (deuda previa), front 451 passed en 70,70 s, `PUERTA TAMAÑO: F-067 dentro de los topes (impl 216/220)` |
