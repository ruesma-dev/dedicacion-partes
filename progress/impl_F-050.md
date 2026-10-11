<!-- progress/impl_F-050.md -->
# F-050 · Subfilas por obra con columna Partida y partida propuesta · informe del implementer

Rama `feature/F-050-subfilas-partida`, rigor **crítico**, spec aprobada el
2026-10-09 (D1-D10 = A). T1-T15 (`686d00a`..`f4cdb11`), T15b (`6320474`), T15c
(`85d263f`..`5d75623`, M2 del 2026-10-11) y la review 3 (`2078505`..`bfc404a`).
T16 (M1) hecha por el humano; T17-T18, MANUAL. Dos paradas por tests fuera de
la lista cerrada, aprobadas en requirements §6 (`test_f037_r3_…`, `test_f003_r8_…`).

## Qué cambió (T1-T15b; T15c en su sección)

**Transfer** (solo lee): `propuesta_partida.py` puro (pasos 1-3, `mayor_de`
por la raíz, orden natural, `mayor_inicial`, `ventana`); `historial_partidas`
(lotes de 500, `truncated` = error); pipeline con UNA lectura, R20 y
`partida_origen`; `POST /api/partidas/propuesta`; fase `propuesta` del script.
**Api**: `AsignacionORM.partida_*` (DDL derivado); `Linea.partida_*`,
`partida_fija`; `_conservar_partidas`; `PUT …/partida` (evento `PARTIDA`) y
`GET …/partidas` (502); `LineaOut` con R18; registro con `paride` = elegida.
**Front**: columna `partida`, subfilas (`rowSpan`), filtro y buscador; el
selector (Todas · CD · CI · CP, propuesta primera, «automática», teclas,
caché, PUT), también en el modal (y en las omitidas por R20, T15b).
**Docs**: `#regla-partida`, `INTEGRACION.md`, READMEs.

## Decisiones y desviaciones (justificadas)

1. Ventana: periodo − 24 meses .. periodo; empate con tolerancia 1e-6. 2.
`_a_linea_con_partida` envuelve `_a_linea` (`test_f024_r11`, `test_f025_r18`).
3. VAR sin partida guardada; `GET …/partidas` da `fija` sin transfer. 4.
`proponer` casa la postventa con `casar_postventa`. 5. `ambito` null si el mayor
es OTRO. 6. «automática», la última; caché vaciada al cargar y su clave tras
cada PUT. 7. `MOTIVO_PARTIDA_NO_HOJA` en `propuesta_partida.py`. 8.
`test_f037_r3` importa `PRESUPUESTO_ORIGEN` y `_fila`. **Aviso `partes`**:
`partida_catalog.categoria` clasifica mal hojas bajo `CD` (design §5.1, avisado).

## Tests anteriores que cambian (todos de la lista cerrada)

Transfer: `conftest.py`, `test_pipeline_offline`, `test_f002_fuente_unica`,
`test_f037_r3`. Api: `_fila` de `test_f022`/`f024_registro`/`f026`/`f039_registro_var`;
`CAMPOS_LINEA` de `test_f034_rutas`; `test_f003_r8`. Front: los de T12 (seis `c_*`
borrados). **T15c**: solo `test_f049_a_el_preflight_repetido…` (T12; gana
`obra_ide: 694`). **Review 3**: ninguno de otra feature.

## Fase RED (trazas reales, comando exacto)

Cada tarea de código, antes de escribir el código (desde la carpeta del
servicio, `.venv/Scripts/python.exe -m pytest … -q -p no:cacheprovider`):

```
T1 $ … tests/test_f050_propuesta.py
E   ModuleNotFoundError: No module named 'application.services.propuesta_partida'
1 error in 0.46s
T2 $ … tests/test_f050_propuesta.py -k historial
E       AttributeError: 'SigridWriteClient' object has no attribute 'historial_partidas'   (×6)
E       AttributeError: 'Settings' object has no attribute 'propuesta_meses_atras'
7 failed, 37 deselected in 1.91s
T3 $ … tests/test_f050_pipeline.py
E       AssertionError: assert ('escribir', ...'auto_nombre') == ('escribir', ...rte_anterior')
E       AttributeError: 'AccionLinea' object has no attribute 'partida_origen'
E       assert [] == [([200, 400], 202407, 202607)]
E       Failed: DID NOT RAISE RuntimeError
E       AssertionError: assert 'escribir' == 'omitir'      (×6, R20)
18 failed, 5 passed in 0.75s
T4 $ … tests/test_f050_endpoint_propuesta.py
E       assert 404 == 422 (×4) · KeyError: 'propuestas' (×4) · assert 404 == 502 (×2) · assert 404 == 200
13 failed in 1.79s
T5 $ … tests/test_f050_endpoint_propuesta.py -k script
E   argparse.ArgumentError: argument fase: invalid choice: 'propuesta' (choose from 'inspeccionar', …)
4 failed, 13 deselected in 2.54s
T6 $ … tests/test_f050_partida_linea.py -k "r12 or r14 or r15 or r16"   (api)
E   ImportError: cannot import name '_conservar_partidas' from 'application.use_cases'
1 error in 0.36s
T7 $ … tests/test_f050_rutas_partida.py tests/test_f034_rutas.py -k "r13 or r18 or f034"
E       assert 404 == 200 (×4) · assert 404 == 422 (×3) · assert 'error' in {'detail': 'Not Found'} (×3)
E       Extra items in the right set: 'partida_res' 'partida_ide' …   (CAMPOS_LINEA, ×3)
T8 $ … tests/test_f050_rutas_partida.py -k r17
E       ModuleNotFoundError: No module named 'application.partidas_linea' (×6)
E       ImportError: cannot import name 'PropuestaNoDisponible' from 'domain.errors' (×5)
E       AttributeError: 'TransferClient' object has no attribute 'propuesta_partidas'
12 failed, 14 deselected in 3.01s
T9 $ … tests/test_f050_partida_linea.py -k r19
E       KeyError: 'paride'  (×2)
2 failed, 3 passed, 17 deselected in 1.49s
T10 $ … tests/test_f050_subfilas.py   (front)
E       AssertionError: no existe la función textoPartida en app.js
E       assert 'const frag = document.createDocumentFragment();' in 'function construirFila(t) { …
E       AssertionError: assert ['total', 'as..., 'categoria'] == ['total', 'as..., 'categoria']
E       AssertionError: assert [] == ['Ana']        (filtro Partida)
T11 $ … tests/test_f050_selector_partida.py
E       AssertionError: no existe la función filtrarPartidas en app.js (×10)
E       AssertionError: no existe la función montarSelectorPartida en app.js (×5)
19 failed in 0.32s
T12 $ … tests/test_f050_modal_registro.py
E       AssertionError: no existe la función textoPartidaAccion en app.js (×7)
E       AssertionError: assert [['/periodos/...or_ide': 77}]] == [['/periodos/...or_ide': 77}]]
E       AssertionError: assert 'overrides' not in '// static/j…'
11 failed in 0.31s
T13 $ … tests/test_f002_fuente_unica.py   (transfer, solo con ANCLAS cambiada)
FAILED …test_f002_r1_fuente_unica_tiene_ancla_por_regla[regla-partida]
FAILED …test_f002_r1_fuente_unica_el_ancla_no_esta_repetida[regla-partida]
2 failed, 70 passed in 0.25s
```

Los que pasaban en RED eran controles (VAR fija…); tras cada tarea, verde.

## T15b · omitida por R20 con selector (ampliación del 2026-10-10)

`pintarModalPreflight`: `botonPartida(texto)` y, si el `motivo` empieza como
`MOTIVO_PARTIDA_NO_HOJA`, el botón con la partida que nombra. RED
(`.venv/Scripts/python.exe -m pytest tests/test_f050_modal_registro.py -q -k "r20 or demas_omitidas" --tb=line`):
```
subprocess.CalledProcessError: Command '['C:\\Program Files\\nodejs\\node.EXE', '-']' returned non-zero exit status 1.   [node: TypeError: Cannot read properties of undefined (reading 'trabajador')]
E   AssertionError: <h2>Registrar en Sigrid · sep 2026</h2>…<td><span class="motivo">la partida 80002 elegida no es una partida hoja activa del presupuesto de la obra 0694: no se escribe; elige otra partida</span></td>…
2 failed, 1 passed, 14 deselected in 0.41s
```
Verde: front 187 passed. Mutación JS K01-K11: 11/11 muertos.

## T15c · arreglos de la M2 del humano (2026-10-11)

Commits `85d263f`, `35078fa`, `1560620`+`d46b012`, `708d53c`, `948ed7d`,
`5d75623`. Tests nuevos: front `test_f050_m2_arreglos.py`, api
`test_f050_preflight_obra.py`. 1) `anchosAjustados` encoge hasta
`MINIMO_COLUMNA` (luego scroll), sin tocar `state.anchos`. 2) `col-primera`/
`col-ultima`: barra solo en los bordes. 3) Selector con «Cargando partidas…»,
uno por línea, solo cuenta su panel vivo. 4) `z-index` 70 y `abrirModal` cierra
el selector. 5) `obra_ide` en el preflight (transfer intacto), `unirPreflight`
y `registro.analizando` por obra. `INTEGRACION.md` §5.

Tests propios de F-050 que cambian: `test_f050_r22_una_subfila…`,
`test_f050_r27_elegir…`, `test_f050_r29_pedir_y_ejecutar…`, `…_r27_r29_elegir_en_el_modal…`.

**RED** (antes del código; front `.venv/Scripts/python.exe -m pytest
tests/test_f050_m2_arreglos.py -q -p no:cacheprovider --tb=line -k m2_N`,
api `… tests/test_f050_preflight_obra.py …`):
```
1 E   AssertionError: no existe la función anchosAjustados en app.js   (×4)
  E   AssertionError: no existe `const MINIMO_COLUMNA` en app.js   (×3)
  E   assert 'new ResizeObserver(() => sincronizarAnchoTabla()).observe($("#tabla").parentElement);' in 'function enlazarEventos() { $("#btn-mes-prev").addEventListener("click", () => moverMes(-1)); $("#btn-mes-next").addE..."keydown", teclas); window.addEventListener("beforeunload", () => { if (state.guardadoPendiente) guardarAhora(); }); }'
  8 failed in 0.09s
2 E   AssertionError: assert [[True, [['no...da', 1, '']]]] == [[True, [['no...da', 1, '']]]]
  E   AssertionError: assert [[], []] == [[['asignacio...col-ultima']]]
  E   AssertionError: assert [[True, [['no...al', 1, '']]]] == [[True, [['no...ol-ultima']]]]
  E   AssertionError: assert 'background: ...var(--brand);' == 'background: ...-brand-soft);'
  4 failed, 8 deselected in 0.49s
3 E   assert 0 == 1
  E   assert [0, 2] == [1, 1]
  E   assert ('NUEVA' in '<input class="buscar-partida" autocomplete="off" placeholder="Buscar partida (código o descripción)…"><div class="may...<span class="cod">VIEJA</span><span class="desc">R</span><span class="desc">automática (la propone el registro)</span>')
  E   assert (1 == 1 and 'Cargando partidas…' in '<input class="buscar-partida" autocomplete="off" placeholder="Buscar partida (código o descripción)…"><div class="may...<span class="cod">VIEJA</span><span class="desc">R</span><span class="desc">automática (la propone el registro)</span>')
  E   assert 1 == 0
  E   assert (0 == 1)
  6 failed, 12 deselected in 1.43s
4 E   assert [1, 1, True] == [0, 0, True]
  1 failed, 2 passed, 18 deselected in 0.44s        (los 2 que pasan: z-index y ancla, guardas)
5 api E   TypeError: RegistroSigrid.preflight() got an unexpected keyword argument 'obra_ide'   (×4)
  E   KeyError: 'obra_ide'
  5 failed, 1 passed, 1 warning in 3.72s
5 front (con `unirPreflight` ya escrita y sus 3 tests en verde; antes, 10 × «no existe la función unirPreflight»)
  E   AssertionError: assert {'trabajador_ide': 77} == {'trabajador_...bra_ide': 694}
  E   AssertionError: assert [{'trabajador...r_ide': None}] == [{'trabajador...ra_ide': 694}]
  E   AssertionError: assert [[[700, 'v2']... 'Registrar'}] == [[[694, 'v1']...Analizando…'}]
  E   AssertionError: assert [[[694, 'v3']]] == [[[694, 'v3'], [700, 'v1']]]
  E   AssertionError: assert [[], {'disabl...lizando…'}, 1] == [['transfer c...lizando…'}, 1]
  E   AssertionError: assert [['/periodos/...or_ide': 77}]] == [['/periodos/...a_ide': 694}]]
  6 failed, 4 passed, 21 deselected in 1.92s
```
**Mutación JS manual T15c**: 46; 1 vivo en la primera pasada (T20), hueco
real cerrado (`5d75623`); **final 46/46**. Textos en `mutacion_manual_F-050.md`.

## Review 3 · cambio 1 y observaciones 2 y 3 (2026-10-11)

Commits `2078505` (1), `6ef5c64` (2), `ee4c70d` (3), `bfc404a` (mutación JS).
1. **Cambio 1** (`repreflightPartida`): el `catch` reactiva el botón de AHORA
   (`$("#btn-ejecutar-registro")`, como la rama buena) si no queda obra en
   vuelo; antes, el `btn` del principio, fuera del DOM tras el repintado de la
   otra. Test `…_error_despues_de_que_la_otra_vuelva_bien`, los dos órdenes.
2. **Obs. 2** (`routes.py`, `_obra_ide`): `"694"`/`694.0` → `694`; texto,
   decimal, booleano, lista o `Infinity` → `ObraNoValida` (422) sin analizar.
   `trabajador_ide` sigue crudo. **Para el líder**: el 422 en `azure-apps`.
3. **Obs. 3** (`unirPreflight`): `ok` = todas las obras `ok` (sin obras, `true`,
   como la api). Test `…_unir_recalcula_el_ok_con_todas_las_obras`. **Cambia
   un test propio (T15c)**: `…_unir_quita_la_obra_que_ya_no_viene_y_anade_la_
   nueva` compara el dict entero y sus dos esperados ganan `"ok": True` (se
   endurece; no se relaja nada).

**RED** (antes del código, mismos comandos que T15c):
```
1 $ (front) … tests/test_f050_m2_arreglos.py -q -p no:cacheprovider -k "error_despues_de_que_la_otra_vuelva_bien"
  E         At index 1 diff: {'disabled': True, 'textContent': 'Analizando…'} != {'disabled': False, 'textContent': 'Registrar'}   (×2)
  2 failed, 31 deselected in 0.60s
2 $ (api) … tests/test_f050_preflight_obra.py -q -p no:cacheprovider
  E       AssertionError: {"ok":true,"obras":[]}
  E       assert 200 == 422      (×5, uno por caso)
  6 failed, 6 passed, 1 warning in 5.86s
  $ (api) … tests/test_f050_preflight_obra.py -q -p no:cacheprovider -k convierte
  E           AssertionError: assert ('694' == 694)
  1 failed, 11 deselected, 1 warning in 4.76s
3 $ (front) … tests/test_f050_m2_arreglos.py -q -p no:cacheprovider -k "unir_recalcula"
  E       assert True is False
  1 failed, 33 deselected in 0.36s
```
Verde tras cada uno (front 221, api 780). **Mutación**: JS manual T47-T53
**7/7** (T47 = el fallo de la review); Python **164/164** (4 nuevos de `_obra_ide`).

## Fuera del alcance y MANUAL pendiente

Fuera: F-051, F-044, F-054, F-021, el Excel (D8), la lentitud del preflight
(F-055) y la observación 1 de la review 3 (manija de ancho, se mira en la M2
(h) 1). Nada contra Sigrid ni Azure. **T16 · M1**: OK (humano, 2026-10-11).
**T17 · M2** (navegador, modo pruebas): `tasks.md` T17 (a)-(h); **Cancelar, sin
Registrar**. **T18 · M3**: solo con autorización del humano en ese momento.

## Evidencias

| Evidencia | Valor real |
|---|---|
| `bash harness/init.sh` (tal cual, sin `.arnes_cache/suite_*.ok`, review 3) | código 0, **ENTORNO LISTO**; todo `[OK]` salvo el `[AVISO]` de `ruff` (237, la deuda de antes); `PUERTA TAMAÑO` en verde |
| Tests por servicio (ejecutados, no caché) | raíz **418 passed, 1 skipped**; api **780 passed**; front **221 passed** (node); transfer **750 passed** (41,41 s · 39,67 s · 21,35 s · 7,26 s) |
| Tests nuevos de F-050 | transfer 47 + 24 + 19; api 23 + 30 + 6 + **6** (rev. 3); front 16 + 19 + 17 + 31 + **3** (rev. 3) |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: 100.0% de 353 líneas cambiadas cubiertas (353/353, umbral 80%, nivel critico)` (Python; el JS, la campaña manual) |
| Mutantes Python | **164 generados, 0 supervivientes** (`ee4c70d`, igual código que HEAD), 1796,6 s, 1 worker, sin muestreo, copia aislada; base api 38,9 s (medida con la campaña JS en paralelo) |
| Mutantes JS (manual) | T15 **56/0**, T15b **11/0**, T15c **46/0** (1 vivo en la primera pasada, con test), review 3 **7/0** |
