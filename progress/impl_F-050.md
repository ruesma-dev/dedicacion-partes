<!-- progress/impl_F-050.md -->
# F-050 · Subfilas por obra con columna Partida y partida propuesta · informe del implementer

Rama `feature/F-050-subfilas-partida`, rigor **crítico**, spec aprobada el 2026-10-09 (D1-D10 = A). T1-T15 (`686d00a`..
`f4cdb11`), T15b (`6320474`), T15c (`85d263f`..`5d75623`), review 3 (`2078505`..`bfc404a`), T15d (`552fbfb`..`5bbda9e`),
T15e (`a738252`..`8788c94`), T15f (`61ede15`..). M1 hecha; T17-T18, MANUAL. Tres paradas por tests fuera de la lista
cerrada, aprobadas en requirements §6 (`test_f037_r3_…`, `test_f003_r8_…`; en T15f, `test_f042_r3_…` y `test_f050_m2_1_…`).

## Qué cambió (T1-T15b; T15c, review 3 y T15d-T15f en su sección)

**Transfer** (solo lee): `propuesta_partida.py` puro (pasos 1-3, `mayor_de` por la raíz, `ventana`);
`historial_partidas` (lotes de 500); pipeline con UNA lectura, R20 y `partida_origen`; `POST /api/partidas/propuesta`;
fase `propuesta` del script. **Api**: `partida_*` en `AsignacionORM`/`Linea`/`LineaOut` (R18); `PUT …/partida`
(evento `PARTIDA`), `GET …/partidas` (502); registro con `paride` = elegida. **Front**: columna `partida`, subfilas
(`rowSpan`), filtro; el selector (Todas · CD · CI · CP, propuesta primera, «automática», teclas, caché), también en el
modal (T15b, omitidas por R20). **Docs**: `#regla-partida`, `INTEGRACION.md`, READMEs.

## Decisiones y desviaciones (justificadas)

1. Ventana −24 meses; empate 1e-6. 2. `_a_linea_con_partida` envuelve `_a_linea`. 3. VAR sin partida guardada (`fija`
sin transfer). 4. Postventa con `casar_postventa`. 5. `ambito` null si OTRO. 6. «automática», la última; caché por clave.
7. `MOTIVO_PARTIDA_NO_HOJA` en `propuesta_partida.py`. 8. `test_f037_r3` importa `PRESUPUESTO_ORIGEN`. **Aviso
`partes`**: `partida_catalog.categoria` clasifica mal hojas bajo `CD` (design §5.1, avisado).

## Tests anteriores que cambian (todos de la lista cerrada)

Transfer: `conftest.py`, `test_pipeline_offline`, `test_f002_fuente_unica`, `test_f037_r3`. Api: `_fila` de
`test_f022`/`f024_registro`/`f026`/`f039_registro_var`; `CAMPOS_LINEA` de `test_f034_rutas`; `test_f003_r8`. Front: los
de T12 (seis `c_*` borrados). **T15c**: solo `test_f049_a_el_preflight_repetido…` (T12; gana `obra_ide: 694`).
**Review 3**, **T15d** y **T15e**: ninguno de otra feature (T15e amplía el DOM de mentira de `test_f050_t15d_selector.py`,
como pide la review 5; sus 14 tests, sin tocar). **T15f**: `test_f042_r3_busqueda_identica_y_luego_se_coloca` (solo
`BUSQUEDA_ANTES` pierde `.slice(0, 14)`) y `test_f050_m2_1_la_tabla_se_ajusta_a_su_panel` (opción A: espera
`[280, 210, 196, 169, 190]` y `1045px`), los dos aprobados por el humano el 2026-10-14.

## Fase RED (trazas reales, comando exacto)

Cada tarea de código, antes del código (desde la carpeta del servicio, `.venv/Scripts/python.exe -m pytest … -q -p no:cacheprovider`):
```
T1 $ … tests/test_f050_propuesta.py  ⇒  E   ModuleNotFoundError: No module named 'application.services.propuesta_partida'   → 1 error in 0.46s
T2 $ … tests/test_f050_propuesta.py -k historial  ⇒  E       AttributeError: 'SigridWriteClient' object has no attribute 'historial_partidas'   (×6)
E       AttributeError: 'Settings' object has no attribute 'propuesta_meses_atras'   → 7 failed, 37 deselected in 1.91s
T3 $ … tests/test_f050_pipeline.py  ⇒  E       AssertionError: assert ('escribir', ...'auto_nombre') == ('escribir', ...rte_anterior') · E       AttributeError: 'AccionLinea' object has no attribute 'partida_origen'
E       assert [] == [([200, 400], 202407, 202607)] · E       Failed: DID NOT RAISE RuntimeError
E       AssertionError: assert 'escribir' == 'omitir'      (×6, R20)   → 18 failed, 5 passed in 0.75s
T4 $ … tests/test_f050_endpoint_propuesta.py  ⇒  E       assert 404 == 422 (×4) · KeyError: 'propuestas' (×4) · assert 404 == 502 (×2) · assert 404 == 200   → 13 failed in 1.79s
T5 $ … tests/test_f050_endpoint_propuesta.py -k script  ⇒  E   argparse.ArgumentError: argument fase: invalid choice: 'propuesta' (choose from 'inspeccionar', …)   → 4 failed, 13 deselected in 2.54s
T6 $ … tests/test_f050_partida_linea.py -k "r12 or r14 or r15 or r16"   (api)  ⇒  E   ImportError: cannot import name '_conservar_partidas' from 'application.use_cases'   → 1 error in 0.36s
T7 $ … tests/test_f050_rutas_partida.py tests/test_f034_rutas.py -k "r13 or r18 or f034"  ⇒  E       assert 404 == 200 (×4) · assert 404 == 422 (×3) · assert 'error' in {'detail': 'Not Found'} (×3)
E       Extra items in the right set: 'partida_res' 'partida_ide' …   (CAMPOS_LINEA, ×3)
T8 $ … tests/test_f050_rutas_partida.py -k r17  ⇒  E       ModuleNotFoundError: No module named 'application.partidas_linea' (×6) · E       ImportError: cannot import name 'PropuestaNoDisponible' from 'domain.errors' (×5)
E       AttributeError: 'TransferClient' object has no attribute 'propuesta_partidas'   → 12 failed, 14 deselected in 3.01s
T9 $ … tests/test_f050_partida_linea.py -k r19  ⇒  E       KeyError: 'paride'  (×2)   → 2 failed, 3 passed, 17 deselected in 1.49s
T10 $ … tests/test_f050_subfilas.py   (front)  ⇒  E       AssertionError: no existe la función textoPartida en app.js · E       assert 'const frag = document.createDocumentFragment();' in 'function construirFila(t) { …
E       AssertionError: assert ['total', 'as..., 'categoria'] == ['total', 'as..., 'categoria'] · E       AssertionError: assert [] == ['Ana']        (filtro Partida)
T11 $ … tests/test_f050_selector_partida.py  ⇒  E       AssertionError: no existe la función filtrarPartidas en app.js (×10)
E       AssertionError: no existe la función montarSelectorPartida en app.js (×5)   → 19 failed in 0.32s
T12 $ … tests/test_f050_modal_registro.py  ⇒  E       AssertionError: no existe la función textoPartidaAccion en app.js (×7) · E       AssertionError: assert [['/periodos/...or_ide': 77}]] == [['/periodos/...or_ide': 77}]]
E       AssertionError: assert 'overrides' not in '// static/j…'   → 11 failed in 0.31s
T13 $ … tests/test_f002_fuente_unica.py   (transfer, solo con ANCLAS cambiada)  ⇒  FAILED …test_f002_r1_fuente_unica_tiene_ancla_por_regla[regla-partida] · FAILED …test_f002_r1_fuente_unica_el_ancla_no_esta_repetida[regla-partida]   → 2 failed, 70 passed in 0.25s
```
Los que pasaban en RED eran controles (VAR fija…); tras cada tarea, verde.

## T15b · omitida por R20 con selector (ampliación del 2026-10-10)

`pintarModalPreflight`: `botonPartida(texto)` y, si el `motivo` empieza como `MOTIVO_PARTIDA_NO_HOJA`, el botón con la
partida que nombra. RED (`.venv/Scripts/python.exe -m pytest tests/test_f050_modal_registro.py -q -k "r20 or demas_omitidas" --tb=line`):
```
subprocess.CalledProcessError: Command '['C:\\Program Files\\nodejs\\node.EXE', '-']' returned non-zero exit status 1.   [node: TypeError: Cannot read properties of undefined (reading 'trabajador')]
E   AssertionError: <h2>Registrar en Sigrid · sep 2026</h2>…<td><span class="motivo">la partida 80002 elegida no es una partida hoja activa del presupuesto de la obra 0694: no se escribe; elige otra partida</span></td>…   → 2 failed, 1 passed, 14 deselected in 0.41s
```
Verde: front 187 passed. Mutación JS K01-K11: 11/11 muertos.

## T15c · arreglos de la M2 del humano (2026-10-11)

Commits `85d263f`..`5d75623`; tests `test_f050_m2_arreglos.py` (front), `test_f050_preflight_obra.py` (api). 1)
`anchosAjustados`. 2) `col-primera`/`col-ultima`. 3) «Cargando partidas…», un panel por línea. 4) `z-index` 70;
`abrirModal` cierra el selector. 5) `obra_ide` en el preflight, `unirPreflight`, `registro.analizando` por obra. Tests
propios que cambian: `…_r22_una_subfila…`, `…_r27_elegir…`, `…_r29_pedir_y_ejecutar…`, `…_r27_r29_elegir_en_el_modal…`.

**RED** (front `.venv/Scripts/python.exe -m pytest tests/test_f050_m2_arreglos.py -q -p no:cacheprovider --tb=line -k m2_N`, api `… tests/test_f050_preflight_obra.py …`):
```
1 E   AssertionError: no existe la función anchosAjustados en app.js   (×4) · E   AssertionError: no existe `const MINIMO_COLUMNA` en app.js   (×3)
  E   assert 'new ResizeObserver(() => sincronizarAnchoTabla()).observe($("#tabla").parentElement);' in 'function enlazarEventos() { $("#btn-mes-prev").addEventListener("click", () => moverMes(-1)); $("#btn-mes-next").addE..."keydown", teclas); window.addEventListener("beforeunload", () => { if (state.guardadoPendiente) guardarAhora(); }); }'   → 8 failed in 0.09s
2 E   AssertionError: assert [[True, [['no...da', 1, '']]]] == [[True, [['no...da', 1, '']]]] · E   AssertionError: assert [[], []] == [[['asignacio...col-ultima']]]
  E   AssertionError: assert [[True, [['no...al', 1, '']]]] == [[True, [['no...ol-ultima']]]] · E   AssertionError: assert 'background: ...var(--brand);' == 'background: ...-brand-soft);'   → 4 failed, 8 deselected in 0.49s
3 E   assert 0 == 1 · E   assert [0, 2] == [1, 1] · E   assert 1 == 0 · E   assert (0 == 1)
  E   assert ('NUEVA' in '<input class="buscar-partida" autocomplete="off" placeholder="Buscar partida (código o descripción)…"><div class="may...<span class="cod">VIEJA</span><span class="desc">R</span><span class="desc">automática (la propone el registro)</span>')
  E   assert (1 == 1 and 'Cargando partidas…' in '<input class="buscar-partida" autocomplete="off" placeholder="Buscar partida (código o descripción)…"><div class="may...<span class="cod">VIEJA</span><span class="desc">R</span><span class="desc">automática (la propone el registro)</span>')   → 6 failed, 12 deselected in 1.43s
4 E   assert [1, 1, True] == [0, 0, True]   → 1 failed, 2 passed, 18 deselected in 0.44s        (los 2 que pasan: z-index y ancla, guardas)
5 api E   TypeError: RegistroSigrid.preflight() got an unexpected keyword argument 'obra_ide'   (×4) · E   KeyError: 'obra_ide'   → 5 failed, 1 passed, 1 warning in 3.72s
5 front (con `unirPreflight` ya escrita y sus 3 tests en verde; antes, 10 × «no existe la función unirPreflight»)  ⇒  E   AssertionError: assert {'trabajador_ide': 77} == {'trabajador_...bra_ide': 694} · E   AssertionError: assert [{'trabajador...r_ide': None}] == [{'trabajador...ra_ide': 694}]
  E   AssertionError: assert [[[700, 'v2']... 'Registrar'}] == [[[694, 'v1']...Analizando…'}] · E   AssertionError: assert [[[694, 'v3']]] == [[[694, 'v3'], [700, 'v1']]]
  E   AssertionError: assert [[], {'disabl...lizando…'}, 1] == [['transfer c...lizando…'}, 1] · E   AssertionError: assert [['/periodos/...or_ide': 77}]] == [['/periodos/...a_ide': 694}]]   → 6 failed, 4 passed, 21 deselected in 1.92s
```
**Mutación JS manual T15c**: 46; 1 vivo en la primera pasada (T20), hueco real cerrado (`5d75623`); **final 46/46**.

## Review 3 · cambio 1 y observaciones 2 y 3 (2026-10-11)

Commits `2078505` (1), `6ef5c64` (2), `ee4c70d` (3), `bfc404a` (mutación JS). 1) el `catch` de `repreflightPartida`
reactiva el botón de AHORA; 2) `_obra_ide`: `"694"`/`694.0` → `694`, lo demás 422; 3) `unirPreflight`: `ok` = todas
las obras `ok` (`…_unir_quita_la_obra…`, test propio, gana `"ok": True`: se endurece). **RED** (mismos comandos que T15c):
```
1 $ (front) … tests/test_f050_m2_arreglos.py -q -p no:cacheprovider -k "error_despues_de_que_la_otra_vuelva_bien"  ⇒  E         At index 1 diff: {'disabled': True, 'textContent': 'Analizando…'} != {'disabled': False, 'textContent': 'Registrar'}   (×2)   → 2 failed, 31 deselected in 0.60s
2 $ (api) … tests/test_f050_preflight_obra.py -q -p no:cacheprovider  ⇒  E       AssertionError: {"ok":true,"obras":[]} · E       assert 200 == 422      (×5, uno por caso)   → 6 failed, 6 passed, 1 warning in 5.86s
  $ (api) … tests/test_f050_preflight_obra.py -q -p no:cacheprovider -k convierte  ⇒  E           AssertionError: assert ('694' == 694)   → 1 failed, 11 deselected, 1 warning in 4.76s
3 $ (front) … tests/test_f050_m2_arreglos.py -q -p no:cacheprovider -k "unir_recalcula"  ⇒  E       assert True is False   → 1 failed, 33 deselected in 0.36s
```
Verde tras cada uno (front 221, api 780). **Mutación**: JS manual T47-T53 **7/7** (T47 = el fallo de la review); Python
**164/164** (4 nuevos de `_obra_ide`).

## T15d · dos fallos de la M2 repetida (2026-10-12)

Commits `552fbfb` (1), `a6d7cf3` (2), `5bbda9e` (S02/S04); tests (front) `test_f050_t15d_sombreado.py` (6) y
`test_f050_t15d_selector.py` (14). 1) La captura es el *hover* (píxel `#f8f4f5`; el cursor, `#f7eaee`, ya cubría el
bloque): cada subfila pone/quita `resaltada` en TODAS las del bloque (`mouseenter`/`mouseleave`), y cursor, editor y
`multi` siguen mandando. 2) `recolocar` medía con el `max-height` de «Cargando…» (34 px) puesto; ahora mide el alto
natural y `posicionSugerencias` gana `minimo` (`ALTO_UTIL = 240`; 0 en F-042, intacto): arriba si no cabe debajo, o
dentro de la ventana. Mismo código en cuadrante y modal. **RED** (front, `.venv/Scripts/python.exe -m pytest tests/<fichero> -q -p no:cacheprovider --tb=line`):
```
1 $ … test_f050_t15d_sombreado.py  ⇒  E   AssertionError: assert {'dentro': [F...False, False]} == {'dentro': [T...False, False]}   (×2: bloque y sin carga)
  E   AssertionError: assert {'segunda': [...False, False]} == {'segunda': [..., True, True]} · E   AssertionError: assert {'a': [False,...False, False]} == {'a': [False,...False, False]}
  E   AssertionError: no está la regla `tr.fila.resaltada td` en styles.css · E   ValueError: substring not found   → 6 failed in 0.57s
2 $ … test_f050_t15d_selector.py  ⇒  E   AssertionError: assert {'top': 702, ...Max': 34, ...} == {'top': 702, ...ax': 240, ...} · E   AssertionError: assert {'top': 552, ...Max': 34, ...} == {'top': 552, ...ax': 240, ...}
  E   assert (140, 152, False) == (52, 240, False) · assert (8, 188, True) == (8, 240, True) · assert (120, 72) == (8, 184)
  E   AssertionError: assert ['134px', '34px', 34] == ['134px', '240px', 34] · E   AssertionError: assert ['702px', '34px', 34] == ['702px', '240px', 34]   (cada uno ×2: cuadrante y modal)
  E   AssertionError: assert ['471px', '34px', 34] == ['8px', '409px', 409]   (la captura: 34 px junto al borde)
  E   assert 'const ALTO_UTIL = 240;' in 'function montarSelectorPartida(ctx) { cerrarSelectorPartida(); …'   → 11 failed, 2 passed in 3.16s        (los 2 que pasan: controles, F-042 sin mínimo y lista que ya llena el sitio)
```
Verde: front 227 tras 1 y 240 tras 2 (241 con `5bbda9e`). **Mutación JS/CSS manual** (copia aislada): 1.ª pasada 23/25 (S02, S04 vivos: huecos reales, cerrados en `5bbda9e`); **final 26/26 muertos**.

## T15e · review 5: la lista del selector se desplaza (2026-10-12)

Commits `a738252` (1-2), `030c0da` (obs. 1), `15f8f61` (3, `tasks.md`), `7ecc6e3` (DOM), `8788c94` (ruff). 1)
`recolocar(ev)` guarda el `scrollTop` de `.lista-partidas` antes de quitar el `max-height` y lo repone tras fijar el
nuevo; un `scroll` con `ev.target` dentro del panel (la rueda) no recoloca; el `resize` no llega a `contains` (con
`window` lanza `TypeError`). `pintar` sin cambios (`scrollIntoView` y `recolocar`): con la reposición la activa sigue
visible (test ↓ ×25 y Chrome). 2) El DOM de mentira de `t15d_selector` modela vista, filas, `scrollIntoView`
«nearest» y el recorte a 0 sin `max-height` (al leer `offsetHeight` o `scrollTop`); 6 tests nuevos, los 14 de T15d
intactos. 3) M2 (h) 3 (y (h) 2, por la obs. 1) en T17. Obs. 1) `state.ratonIde`/`resaltadas`: el bloque repintado
bajo el ratón quieto sale sombreado; al entrar en otro se apaga el que hubiera; al salir de la fila o de `#cuerpo`, el
que haya (`test_f050_t15e_sombreado.py`, 6). Límite (sencillo, no se arregla): si la tabla se reordena o se desplaza
bajo el ratón quieto, el sombreado sigue al trabajador hasta mover el ratón (como ya pasaba con el scroll en T15d).
**RED** (copia aislada con el `app.js` de `a663a0a`, desde el front: `….venv/Scripts/python.exe -m pytest tests/test_f050_t15d_selector.py tests/test_f050_t15e_sombreado.py -q -p no:cacheprovider --tb=line`):
```
E   AssertionError: assert [25, 0, False, '658px'] == [25, 200, True, '658px']   (×2: cuadrante y modal)
E   AssertionError: assert [0, '334px', '458px'] == [650, '134px', '658px']   (×2: cuadrante y modal)
E   AssertionError: assert [0, '234px', '558px'] == [400, '234px', '558px']   (×2: cuadrante y modal)
E   AssertionError: assert {'r': [None, None]} == {'r': [None, []]} · E   AssertionError: assert {'nuevo': [Fa...False, False]} == {'nuevo': [Tr...False, False]}
E   AssertionError: assert {'b': [False,... [True, True]} == {'b': [False,...ue], 'ide': 8}
E   AssertionError: TypeError: Cannot read properties of undefined (reading 'length')   (×2: fila vieja y sin repintar)
E   AssertionError: TypeError: escuchas.#cuerpo mouseleave is not a function   → 12 failed, 14 passed in 3.10s        (los 14: los de T15d, sin cambios)
```
**Chrome headless** (scratchpad `t15e/chrome_gen.py`: el selector REAL con `styles.css` y 95 partidas; ↓ ×40, rueda =
`scrollTop = 1500` + `scroll` de la lista, página = `scrollBy(0, 50)` + `scroll` de `document`; extracto de
`t15e/chrome_t15e_1.txt`, dos ejecuciones iguales, sin los campos de alto ni el registro de eventos):
```
head {"flechas":[0,false],"rueda":[1500,0,"157px"],"pagina":[0,"107px"]}       ([scrollTop, activa visible], [puesto, queda, top])
fix  {"flechas":[813,true],"rueda":[1500,1500,"157px"],"pagina":[1500,"107px"]}
```
Verde: front 253. **Mutación JS manual** (copia aislada, `7ecc6e3`): **23/23 muertos**, una pasada (V01 = sin reposición, 4 fallos).

## T15f · M2 del 2026-10-14: obras sin tope y Total sin cortar

Commits `61ede15` (1, editor), `a81c41c` (1, «Completar»), `a23a373` (2); tests (front) `test_f050_t15f_obras.py` (8) y
`test_f050_t15f_total.py` (8). 1) Sin `.slice(0, 14)` en los dos desplegables. **Editor**: `marcarActiva` lleva la
activa a la vista con `offsetTop`/`clientHeight` (lo que hace `scrollIntoView` «nearest»; el DOM de mentira de F-042,
de la lista cerrada, no tiene `scrollIntoView`); `colocarSugerencias` guarda y repone el `scrollTop` (medir sin
`max-height` lo recorta, lección de T15e) y un `scroll` de la propia lista no recoloca. Arriba si no cabe debajo: lo de
F-042 (`posicionSugerencias` sin mínimo; con la lista larga el panel ya mide sus 280 px). **«Completar»**: su lista va
dentro del modal (sin «arriba», aprobado); `pintar` conserva el `scrollTop` al vaciarla y hace `scrollIntoView`
«nearest» de la activa. 2) `sincronizarAnchoTabla`: Total, preferido y mínimo, nunca bajo su contenido (un `Range` sobre
cada `td.celda-total`, el mayor, + relleno + 2 px de bordes y redondeo); al estrechar, una pasada de `anchosAjustados`
solo con Asignaciones y Partida y otra con todas (Trabajador y Categoría solo ceden con ellas en su mínimo); si no cabe,
scroll. `renderTabla` y `refrescarCeldasFila` (guardar en el editor: sale «↩», cambia «falta») vuelven a medir.
`state.anchos`, manija y mover columnas, sin tocar. Todo dentro de `sincronizarAnchoTabla` para no tocar el arnés
`_sincronizar` de `test_f050_m2_arreglos.py`.

**RED** (front, `.venv/Scripts/python.exe -m pytest tests/<fichero> -q -p no:cacheprovider --tb=line`):
```
1 $ … test_f050_t15f_obras.py  ⇒  E   AssertionError: assert [14, '280px', False] == [40, '280px', False] · E   AssertionError: assert {'bajando': [...da': ['0603']} == {'bajando': [...da': ['0615']}
  E   AssertionError: assert ['240px', '202px', 2] == ['240px', '202px', 1] · E   AssertionError: assert {'trasResize'...: [224, True]} == {'trasResize'...: [700, True]}
  E   AssertionError: assert ['468px', '28..., 14, 0, True] == ['468px', '28..., 40, 0, True] · E   assert [14, 0, 0] == [40, 0, 0]
  E   AssertionError: assert {'bajando': [...ng> · Obra 3'} == {'bajando': [...g> · Obra 15'} · E   AssertionError: TypeError: Cannot read properties of undefined (reading 'fire')   → 8 failed in 1.97s
2 $ … test_f050_t15f_total.py "tests/test_f050_m2_arreglos.py::test_f050_m2_1_la_tabla_se_ajusta_a_su_panel"  ⇒  E   assert [203, 140, 299, 212, 190] == [280, 210, 196, 169, 190] · E   assert [167, 106, 175, 160, 190] == [186, 123, 150, 150, 190]
  E   assert [212, 203, 140, 299, 190] == [169, 280, 210, 196, 190] · E   assert [280, 210, 560, 320, 190] == [280, 210, 536, 310, 263]
  E   assert [160, 100, 150, 150, 190] == [160, 100, 150, 150, 263] · E   AssertionError: assert (150, {'total': 150}) == (263, {'total': 150})
  E   assert False · E   AssertionError: assert ['203px', '14...2px', '190px'] == ['280px', '21...9px', '190px']   → 8 failed in 1.55s
  $ … test_f050_t15f_total.py -k refrescar        (añadido al ver que guardar en el editor solo rehace su fila)  ⇒  E   assert False   → 1 failed, 7 deselected in 0.05s
```
**Chrome headless** (scratchpad `chrome/gen.py` y `chrome/gen_obras.py`: el código REAL con `styles.css`; `antes` =
`app.js` de `a81c41c`/`68e80b4`, `despues` = `a23a373`). Total con VINDEL (50 %, falta, «⇪ Sigrid», «↩»), una OK y una
que sobra, panel de 1600/1100/900/600 px; `entero` = el contenido cabe en la celda:
```
antes   1600 ths [287,215,574,328,195] entero [false,true,false] · 1100 [211,147,326,223,190] [false,true,false] · 900 [181,120,225,181,190] [false,true,false] · 600 [160,100,150,150,190] [false,true,false]
despues 1600 ths [280,210,521,304,282] entero [true,true,true] sin scroll · 1100 [280,210,168,157,282] · 900 [189,126,150,150,282] · 600 [160,100,150,150,282] scroll
obras antes   {"filas":14,"top":"8px","alto":"188px","flechas":[13,false],"rueda":[303,211],"resize":211}   (ventana baja: se abre arriba)
obras despues {"filas":40,"top":"8px","alto":"188px","flechas":[25,true],"rueda":[1213,1213],"resize":1213}
```
Verde: front **269**. **Mutación JS manual** (copia aislada, `a23a373`): **34/34 muertos**, una pasada, 1275,5 s (X = editor, C = «Completar», T = Total).

## Fuera del alcance y MANUAL pendiente

Fuera: F-051, F-044, F-054, F-021, el Excel (D8), F-055 y la manija de ancho (obs. 1 de la review 3, M2 (h) 1). Nada
contra Sigrid ni Azure. **M1**: OK (2026-10-11). **T17 · M2**: `tasks.md` T17 (a)-(i): lo de T15d y T15e en (h) 2 y 3;
T15f en (i) (y (d), (h) 1); **Cancelar, sin Registrar**. **T18 · M3**: solo con autorización del humano.

## Evidencias

| Evidencia | Valor real |
|---|---|
| `bash harness/init.sh` (tal cual, sin `.arnes_cache/suite_*.ok`, T15f) | código 0, **ENTORNO LISTO**; todo `[OK]` salvo el `[AVISO]` de `ruff` (237, la deuda de antes; los ficheros de T15f, limpios); `PUERTA TAMAÑO` en verde (impl 218/220) |
| Tests por servicio (ejecutados, no caché) | raíz **418 passed, 1 skipped**; api **780 passed**; front **269 passed** (node); transfer **750 passed** (131,14 s · 102,57 s · 62,65 s · 16,87 s; última ejecución, tras `69f266b`) |
| Tests nuevos de F-050 | transfer 47 + 24 + 19; api 23 + 30 + 6 + 6 (rev. 3); front 16 + 19 + 17 + 31 + 3 (rev. 3) + 6 + 14 (T15d) + 6 + 6 (T15e) + **8 + 8** (T15f) |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: 100.0% de 353 líneas cambiadas cubiertas (353/353, umbral 80%, nivel critico)` (Python; T15f es JS: su cobertura, la campaña manual) |
| Mutantes Python | **164 generados, 0 supervivientes** (`ee4c70d`; T15d-T15f no tocan Python), 1796,6 s, 1 worker, sin muestreo, copia aislada; base api 38,9 s (medida con la campaña JS en paralelo) |
| Mutantes JS (manual) | T15 **56/0**, T15b **11/0**, T15c **46/0** (1 vivo en la primera pasada, con test), review 3 **7/0**, T15d **26/0** (JS y CSS; 2 vivos en la primera pasada, con test), T15e **23/0** (398,8 s), T15f **34/0** (1275,5 s) |

Textos exactos de todos los mutantes JS: `progress/mutacion_manual_F-050.md`.
