<!-- progress/impl_F-054_anexo.md -->
# F-054 · Anexo del informe del implementer

Detalle trasladado tal cual desde `progress/impl_F-054.md` el 2026-11-03
(tope de 220 líneas del informe). Sin cambios de contenido.

## Review 1: observaciones recogidas (O3 y O6, aceptadas sin cambio)

- **O1** (`e881a17`): 54 avisos de `ruff` corregidos (contra `1ed18be`: 309 →
  308); la fixture `api` de F-055 se reexporta con nombre.
- **O4** (`56dd403`): `cubierta` sin `cod_pruebas`. **O5** (`97e5fed`): `api()`
  deja `status` en el error; comparar con 404/409 no avisa (aceptar sí); el
  aviso de registrar da el motivo de cada sobrante omitida, en rojo si hay.
- **O2** (`5d426b5`): `coberturas_de` marca de postventa la acción (y sus
  vinculados) de una `Postv-` aunque llegue con `destino="obra"`; en la obra
  de postventa cubre si su partida es la de la línea **o 0** (cubre todas).
  Corrección (review 2, O7): hasta D19 **toda** `Postv-` omitida llevaba
  `paride` 0, también la omitida **tras** resolver su partida (sin recurso,
  %, sin `M*`), y cubría todas; desde T22 solo la omitida antes de resolverla.
- RED: O4 `TypeError: cubierta() missing 1 required keyword-only argument:
  'cod_pruebas'` → `4 failed, 16 passed`. O2 `-k o2`: `AssertionError`
  (`obra` ≠ `postventa`), `assert False`, `assert [7001] == [7002]` → `3
  failed, 1 passed`. O5: `assert [['No se pudo...riodo', True]] == []` (×2),
  `['cerrado', None] == ['cerrado', 409]`, `'1 sin poner a 0: x' in '… · 1
  sin poner a 0'`, `assert False is True` → `5 failed, 24 passed`.
- Mutación tras la review: `6d23067` (267, 2 vivos, 4541 s), dos mutantes
  de O1 (`Decimal("0")` → `Decimal(0)`) reproducidos en serie: `Decimal(1) <
  pct` (hueco real: test `0.50`/`1.00` en R16, RED `2 failed`) y el % de la
  `Linea` de sondeo de `_motivo_obra` (equivalente; ahora `Decimal()`).
  `c70eb61`: 0 vivos. `app.js`: C7 vivo en O5, test nuevo (`870e585`).

## T22 · D19 (review 2, O7; el humano, 2026-10-30)

`omitir(motivo, **resuelta)`; tras P5, `resuelta = {destino, paride,
partida_cod}` va en los cuatro `omitir` posteriores (sin recurso, % no
numérico, fuera de rango, sin `M*`). Los anteriores (sin empresa, motivo de
empresa, P5 off, partida sin resolver) y toda no `Postv-`: `obra`/0/`None`.
`cubierta`, `_destino`, `registro_pipeline.py` y `reglas_vinculados.py`, intactos.

- RED (`tests/test_f054_obra_cero.py -k d19`, transfer, antes de `fd56da6`):
  `E AssertionError: assert ('omitir', 'obra', 0, None) == ('omitir',
  'p...a', 33, 'P33')` ×5 (`[kw0]`-`[kw4]`) y `E assert [] == [2]` (sobrantes)
  → `6 failed, 8 passed`. Verde: `14 passed`.
- 4 bis, respuesta (`-k d19_respuesta`, con `reglas_porcentajes.py` de
  `abd5514` restaurado a mano y devuelto después): `At index 0 diff:
  ('omitir', 'obra', 0, None, '200|202607|0|0') != ('omitir', 'postventa',
  70001, '0678', '200|202607|0|70001')` → `1 failed, 1 passed`; verde `2
  passed`. Front (`test_f054_modal_cero.py`): el modal pinta el
  `destino` publicado, **sin cambio de `app.js`**, así que no tiene RED
  propio (lo fija la de la respuesta): `Postventa`×2 / `Obra`×2; el fichero, `9 passed`.
- **Consumidores**, lector por lector (sin cambio salvo lo aceptado):
  - `registro_pipeline.py`: `obra_de` (l. 764, 1136, 1413) solo sobre
    `escribir`, `vin_escribir`, `a_escribir`, `a_insertar`, `pendientes`;
    `normales`/`validas` (l. 647, 651) filtran `escribir`; el bucle de
    partida salta lo demás (l. 666); `sin_partida`, `_cuentas`, idempotencia,
    `_emparejar_ceros`/`pisables_al_cero`, `_nueva`, `_escrita`, sobre
    `escribir`; `omitidas` publica solo `registro_id` y `motivo`.
  - `registro_lote.py`: no los lee. `registro_vinculados.py`: `PartidaTitular` y `_partida` solo con
    `escribir`. `decidir_vinculados` copia `destino` y **no** `paride`: el
    vinculado omitido sale `postventa`/0 y cubre todas (asimetría aceptada).
  - `app.py`: el preflight publica `asdict(a)` y `clave_conflicto(a)`; la
    omitida tras resolver lleva `postventa`, su `paride`/`partida_cod` y
    clave `|<paride>` (**aceptado**); `ejecutar` publica las omitidas solo
    con `registro_id` y `motivo`.
  - api `registro_sigrid.py`, `_guardar_propuestas`: exige `paride` y un
    `partida_metodo` de propuesta; la omitida lleva `None` y no guarda nada.
  - `app.js`, `pintarModalPreflight` l. 3510 y 3549: «Postventa» en
    Destino para ella y sus vinculados omitidos (**aceptado**). El `print`
    de `prueba_escritura_porcentajes.py` l. 311 también (**aceptado**).
- Transfer entero tras `fd56da6`: `1863 passed`, nada fuera de la lista cerrada.


## T23 · 2026-11-02 (enmienda tras T18): ventana de una tabla, D12 desmarcada

- **Commits**: RED `828b393`; código `8c83473`; parada e informe `d883019`/`68fa411`; opción «a» `8d997dd`; `ARCHITECTURE.md` punto 23 `488d423`; mutación y tests nuevos `2af8177`; campañas y T23 `[x]` `b660091`.
- **Código** (`app.js`): las puras `filasTraerVisibles` (filtros «contiene» sin mayúsculas sobre lo pintado y estado exacto; `sort` estable, raya al final en los dos sentidos) y `textoAceptarTraer`; `modeloTraerSigrid` (filas en el orden de la respuesta, `marcada = false`, D12), `textoBotonTraer`, `cuerpoTraerSigrid`, `titulosTraerSigrid` (▲/▼); `filaEntradaSigrid(f)`, `pintarTraerSigrid(datos, modelo)`, `aceptadasMarcadas(modelo)` (lee el modelo, ocultas incluidas; cuerpo de hoy) y `abrirTraerSigrid` (modelo en su cierre; escuchas en `#traer-titulos`, `#traer-filtros` y `#traer-cuerpo`; repinta títulos, `<tbody>` y botón, nunca los filtros). CSS `.acciones-traer` y `.tabla-traer`. Api, transfer y contrato, intactos. El botón dice «Aceptar N marcadas», como la spec (el singular no está decidido).
- **Tests** (`test_f054_traer_front.py`): 20 nuevos (R39-R42 y los dos de la campaña 5); de T9 cambian sin borrarse el de la casilla (ahora **ninguna** `checked`), escuchas, sin casillas, sin pulsar y aceptar (desde el modelo). Fichero: `40 passed`.
- **RED** (desde el front, `.venv/Scripts/python -m pytest tests/test_f054_traer_front.py -q -p no:cacheprovider`, antes del código): `E AssertionError: no existe la función modeloTraerSigrid en app.js` (35) y `… textoAceptarTraer …` (1) → `36 failed, 2 passed in 2.77s`. Tras `8c83473`: `38 passed in 9.62s`.
- **Parada y decisión**: el `<select>` de Estado (R41) tumbaba `test_f050_r29_el_front_ya_no_manda_overrides_ni_lee_catalogos` (`"<select" not in JS`, fuera de la lista cerrada). El humano eligió **«a»** (2026-11-02): la aserción se acota a la elección de partida (ningún `<select` en `pintarModalPreflight`, `montarSelectorPartida`, `listaSelector` ni `htmlPartida`, y en todo `app.js` solo los de `pintarTraerSigrid`); el resto del test, igual. `test_f050_modal_registro.py` entra en la lista cerrada (tasks, design §3 y T23). Comprobado con 5 mutantes a mano (un `<select>` al principio de cada una de esas cuatro funciones y de `textoPartidaAccion`): **5/5 muertos**, base `1 passed`.
- **Mutación manual de `app.js`** (`progress/mutacion_manual_F-054.md`, campañas 5 y 6): 81 mutantes sobre las funciones nuevas, 78 muertos y 3 vivos. D10, equivalente (`asc` inicial sin leer), se quita del código; D11 (filtro inicial) y D51 (tabla sin filas), huecos reales con test nuevo; la campaña 6 los mata (3/3, más D10b). **Total: 84 mutantes, 0 supervivientes.**
- **Docs**: `ARCHITECTURE.md` punto 23 (`#regla-traer-sigrid`): tabla única, las dos desmarcadas, orden, filtros, botones y la D12 revisada con su cita. `INTEGRACION.md` no la describía: sin cambio.
- **`bash harness/init.sh`** tras `b660091` (caché `suite_*.ok` borrada, sin pipes): código 0, **sin `[KO]`**: api `1469 passed` (110,67 s), front `507 passed` (97,94 s), transfer `1865 passed` (42,41 s), raíz `418 passed, 1 skipped` (74,03 s); cobertura 99,5 % (755/759; no mide JS) y tamaño (impl 210/220) en `[OK]`.
- **Pendiente** (humano): MANUAL T18 paso 2 (comando y pasos abajo), T19; T20 al desplegar (líder).

## Evidencias tras T22-T23 (histórico)

`bash harness/init.sh` tras T22 (`.arnes_cache/suite_*.ok` borrados antes): código 0, sin `[KO]`.

| Evidencia | Resultado real |
|---|---|
| Tests | api `1469 passed` (152,47 s); transfer `1865 passed` (69,40 s); front `489 passed` (241,96 s); tras T23 (`b660091`), front `507 passed` (97,94 s) y el resto igual; raíz `418 passed, 1 skipped` (72,71 s). Antes de T22 (`36a7d4b`): 1469 / 1849 / 488 / 418+1 |
| Cobertura de líneas cambiadas | **99,5 %** (755/759, umbral 80 %; antes 748/752). No mide JS |
| Mutación Python | T22: 266 generados, **266 muertos, 0 supervivientes**, 0 timeouts, 4 workers, 3696 s, SHA `a781d25`; `reglas_porcentajes.py` no genera ninguno: RM4 a mano, **8/8 muertos** (`progress/mutacion_F-054.md`). Antes: `c70eb61` 266/266 (4837 s), `c614be3` 262/262 |
| Mutación `app.js` | manual, **69 + 14 (O5) mutantes, 0 supervivientes**: `progress/mutacion_manual_F-054.md`; T22 no toca `app.js`; T23: **81 + 3, 0 supervivientes** (campañas 5 y 6; D10 equivalente, quitado del código) |

**Análisis de supervivientes.** Ningún equivalente: nada queda para que lo
acepte el humano. La campaña 1 (`95cc089`, 207/262,
`progress/mutacion_F-054_campana1.md`) dejó 55 vivos y la de `app.js`, 9;
todos se matan con tests, **sin cambiar código de producción**:
`test_f054_mutacion.py` (api 35, transfer 20) y 4 en el front. Huecos reales:
validación de `sobrantes_a_cero` en `routes.py` (6, sin ningún test); guarda
de `can` y `_EPS` exacto; `ok: true` con todo omitido (la api lo tomaría por
fallo); 502 de la ruta; pruebas sin 0404; partida 0 frente a 1 (6); `cod_var`
y `desde`; textos de la sobrante (el test miraba todo el modal y el pisado de
F-064 los repetía). De poco riesgo: `frozen` (11) y defectos (10). La campaña
2 (`c70eb61`, 266/266, `progress/mutacion_F-054_campana2.md`) y la de T22
no dejan vivos: no hubo nada que reproducir en serie.
