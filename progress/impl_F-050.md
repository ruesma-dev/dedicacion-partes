<!-- progress/impl_F-050.md -->
# F-050 · Subfilas por obra con columna Partida y partida propuesta · informe del implementer

Rama `feature/F-050-subfilas-partida`, rigor **crítico**, spec aprobada el
2026-10-09 (D1-D10 = A). T1-T15 (`686d00a`..`f4cdb11`), T15b (`6320474`) y
T15c (`85d263f`..`5d75623`, arreglos de la M2 del 2026-10-11). T16 (M1) hecha
por el humano; T17-T18, MANUAL. Dos paradas por tests fuera de la lista
cerrada, aprobadas y recogidas en requirements §6 (`test_f037_r3_…`, T3;
`test_f003_r8_…`, T6).

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

1. Ventana: periodo − 24 meses .. periodo; empate con tolerancia 1e-6.
2. `_a_linea_con_partida` envuelve `_a_linea` (`test_f024_r11` y
   `test_f025_r18`, fuera de la lista). 3. VAR sin partida guardada; `GET
   …/partidas` da `fija` sin llamar al transfer. 4. `proponer` casa la
   postventa con `cargar_catalogo_postventa` + `casar_postventa`. 5. `ambito`
   null si el mayor de la elegida es OTRO. 6. «automática», la última; caché
   vaciada al cargar el cuadrante y su clave tras cada PUT. 7.
   `MOTIVO_PARTIDA_NO_HOJA` en `propuesta_partida.py`. 8. `test_f037_r3`
   importa `PRESUPUESTO_ORIGEN` y `_fila`. **Aviso para `partes`**: su
   `partida_catalog.categoria` clasifica mal hojas bajo `CD` (design §5.1;
   avisado al humano el 2026-10-09).

## Tests anteriores que cambian (todos de la lista cerrada)

Transfer: `conftest.py`, `test_pipeline_offline.py`, `test_f002_fuente_unica`,
`test_f037_r3`. Api: `_fila` de `test_f022`, `test_f024_registro`, `test_f026`,
`test_f039_registro_var`; `CAMPOS_LINEA` de `test_f034_rutas`; `test_f003_r8`.
Front: los de T12 (`test_f039_r22_el_resto…`, `test_f049_avisos`, los
nombrados de `test_f049_ampliacion`, seis `c_*` borrados). **T15c**: solo
`test_f049_a_el_preflight_repetido_lleva_la_partida_recien_elegida` (nombrado
en T12; el cuerpo esperado gana `obra_ide: 694`).

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

Los que pasaban en RED eran controles de lo que no cambia (sin automáticas
no se lee historial, VAR fija…). Tras cada tarea, verde la suite del servicio.

## T15b · omitida por R20 con selector (ampliación del 2026-10-10)

`pintarModalPreflight`: `botonPartida(texto)` y, si el `motivo` empieza como
`MOTIVO_PARTIDA_NO_HOJA` (leído del transfer con `ast` en los tests), el botón
con la partida que nombra. Tres tests nuevos; ninguno anterior cambia. RED
(`.venv/Scripts/python.exe -m pytest tests/test_f050_modal_registro.py -q -k "r20 or demas_omitidas" --tb=line`):
```
subprocess.CalledProcessError: Command '['C:\\Program Files\\nodejs\\node.EXE', '-']' returned non-zero exit status 1.   [node: TypeError: Cannot read properties of undefined (reading 'trabajador')]
E   AssertionError: <h2>Registrar en Sigrid · sep 2026</h2>…<td><span class="motivo">la partida 80002 elegida no es una partida hoja activa del presupuesto de la obra 0694: no se escribe; elige otra partida</span></td>…
2 failed, 1 passed, 14 deselected in 0.41s
```
Verde: front 187 passed. Mutación JS K01-K11: 11/11 muertos.

## Mutación (T15; repetida en T15c)

Python (`--workers 1`, en un `git worktree add --detach` con uniones a los
`.venv`, retirado después): T15 160/16 → 13 huecos con test y 3 equivalentes
quitados, final 158/158; **T15c: 160/160 muertos** (`progress/mutacion_F-050.md`).
JS manual (`mutacion_manual_F-050.md`, copia aislada): 56/56, 11/11, 46/46.

## T15c · arreglos de la M2 del humano (2026-10-11)

Un commit por punto (`85d263f`, `35078fa`, `1560620`+`d46b012`, `708d53c`,
`948ed7d`) y el test de un mutante (`5d75623`). Tests nuevos: front
`test_f050_m2_arreglos.py` (31), api `test_f050_preflight_obra.py` (6).

1. **Tabla que cabe**: `anchosAjustados` (pura): si no caben, cada columna
   cede en proporción lo que tiene sobre su `MINIMO_COLUMNA` (Total no
   encoge); por debajo, el scroll horizontal de `.panel-tabla`. Se pinta
   **sin tocar `state.anchos`**; un `ResizeObserver` del panel reajusta. El
   panel de F-042 cuelga de `<body>`: no le afecta.
2. **Cursor**: `construirFila` marca `col-primera`/`col-ultima` en las celdas
   de los bordes; fondo en todas las subfilas y barra solo ahí (antes, una
   barra por celda pintaba rayas por dentro). La de F-029, igual.
3. **Selector**: `montarSelectorPartida(ctx)` monta el panel con «Cargando
   partidas…» y devuelve `llenar(resp)`, que llena ESE panel;
   `selector.abierto` evita otro panel en la misma línea (el clic en su ancla
   no lo cierra); la respuesta (y su error) solo cuenta si su panel sigue vivo.
4. **Modal**: el panel ya iba a `<body>` con `z-index` 70 (> 60); lo que
   salía «en el cuadrante» era una respuesta tardía de la columna, imposible
   tras el punto 3. Además `abrirModal` cierra cualquier selector.
5. **Repreflight de una obra**: la api admite `obra_ide` en `POST
   …/registro/preflight` (la obra del grupo; en VAR, la de registro);
   `ejecutar` no se acota; **el transfer no se toca**. El front manda la obra
   de la línea, `unirPreflight` la sustituye en su sitio y
   `registro.analizando` guarda por obra el último pedido (dos obras a la vez
   cuentan; «Registrar» bloqueado mientras quede alguna). `INTEGRACION.md` §5
   al día; **para el líder**: `azure-apps/dedicacion.md` gana el `obra_ide`.

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
**Mutación JS manual T15c**: 46; primera pasada 1 vivo (T20: la respuesta
tardía se pintaba en el panel ya quitado), hueco real cerrado (`5d75623`);
**final 46/46 muertos**, 1185,4 s + 48,5 s. Textos enteros en el informe.

## Fuera del alcance y MANUAL pendiente

Fuera: F-051, F-044, F-054, F-021, el Excel (D8) y la lentitud de fondo del
preflight (F-055). Nada contra Sigrid ni Azure en esta implementación.
**T16 · M1**: hecha por el humano el 2026-10-11, OK. **T17 · M2** (navegador,
modo pruebas): `tasks.md` T17, puntos (a)-(g) y **(h)** con cómo comprobar
los cinco arreglos; **Cancelar, sin Registrar**. **T18 · M3**: solo con
autorización del humano en ese momento (`tasks.md` T18).

## Evidencias

| Evidencia | Valor real |
|---|---|
| `bash harness/init.sh` (tal cual, sin `.arnes_cache/suite_*.ok`, T15c) | código 0, **ENTORNO LISTO**; todo `[OK]` salvo el `[AVISO]` de `ruff` (237, la deuda de antes); `PUERTA TAMAÑO` impl ≤ 220 |
| Tests por servicio (ejecutados, no caché) | raíz **418 passed, 1 skipped** (45,78 s); api **774 passed** (45,11 s); front **218 passed** (22,27 s; node v24.14.1); transfer **750 passed** (8,51 s) |
| Tests nuevos de F-050 | transfer 47 + 24 + 19; api 23 + 30 + **6** (T15c); front 16 + 19 + 17 + **31** (T15c) |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: 100.0% de 343 líneas cambiadas cubiertas (343/343, umbral 80%, nivel critico)` (Python; el JS lo cubre la campaña manual) |
| Mutantes Python | **160 generados, 0 supervivientes** (T15c, `948ed7d`), 1807,9 s, 1 worker, sin muestreo; después solo cambia una anotación de tipo (`obra_ide: int \| None`, ruff UP045) |
| Mutantes JS (manual) | T15 **56/0**, T15b **11/0**, T15c **46 generados, 0 supervivientes** (1 vivo en la primera pasada, con test) |
