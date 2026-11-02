<!-- progress/impl_F-054.md -->
# F-054 · Informe del implementer

Rama `feature/F-054-sync-trae-porcentajes`, copia `porcentajes-f054`. Rigor
**crítico**. Spec (T1-T22) escrita a medida (cortes del entorno tras T3 y
T7). Sin escrituras en Sigrid ni llamadas a Azure: todo con dobles.

## Estado por tarea

Commit por tarea: T1 `d12ec81`, T2 `bf2361a`, T3 `f99e0cd`, T4
`3ba3f37`, T5 `50f5d2e`, T6 `69583c9`, T7 `ef06704`, T8 `1c8d4a5`, T9
`ccad4db`, T11 `892d93f`, T12 `eaaca4b`, T13 `60a7dab`, T14 `d382ae7`, T15
`f5a9bb8`, T16 `95cc089`, T17 `e72d22c`/`c614be3`/`1c16454`, T21. Review 1:
O1 `e881a17`, O4 `56dd403`, O2 `5d426b5`, O5 `97e5fed`. T22 (D19): `abd5514`
(RED), `fd56da6` (código), `69647cf` (4 bis), `a781d25`. MANUAL: T10, T18-T20.

## Ficheros tocados

- transfer: `sigrid_write_client.py`, `registro_models.py`, `app.py`;
  nuevos `porcentajes_existentes.py`, `reglas_obra_cero.py`,
  `poner_a_cero.py`; `lecturas_lote.py` y `registro_lote.py` (ronda A,
  `preflight_completo`); `reglas_porcentajes.py`, solo `omitir`/`decidir`
  (T22, D19). `registro_pipeline.py` NO se toca.
- api: `domain/{models,errors,ports,traer_sigrid}.py`,
  `application/{traer_sigrid,registro_sigrid}.py`, `transfer_client.py`,
  `db/{repositories,orm_models}.py`, `api/{app,routes,schemas,deps}.py`.
- front `app.js`; docs `ARCHITECTURE.md` (puntos 23-24) e `INTEGRACION.md`.
- tests nuevos `test_f054_*` en los tres servicios; ajenos, solo la lista
  cerrada (`ANCLAS`; dobles `preflight_lote` de F-022/F-024/F-055 con
  `completo=False`, sin cambiar aserciones).

## Decisiones de diseño y desviaciones (justificadas)

1. **Vigencia por `vigente_en`** (activo + fecha de baja), la regla única del
   dominio, no solo `activo` (design §5.2): `listar_para_periodo` ya da
   `activo` = vigente en el mes; el trabajador que no sale en el listado (no
   vigente sin líneas) se lee con `obtener` para que su motivo sea «no
   vigente» y no «fuera del maestro».
2. `ExistentesIn.empresa` sin tipo: lo no válido da 422 sin leer. 3. La 0404
   siempre se excluye en A (R5); `lineas_leidas` cuenta todas. 4. La
   comparación solo saca a trabajadores con alguna entrada de Sigrid.
5. Obra en la base y no en el listado (inactiva): inactiva, «no se ofrece».
6. **Relectura del periodo**: `PgPeriodoRepository.obtener` con
   `populate_existing=True`; sin ello el mapa de identidad no veía un cierre
   entre medias (R22, 409). A los demás llamantes solo les da el dato de la base.
7. «Después» del evento `SIGRID`, en memoria (fila de antes + aceptadas y
   subfilas): tras el `INSERT … ON CONFLICT` el ORM podía no refrescar.
8. Aceptadas repetidas cuentan una vez. 9. Sin cuerpo = comparar; `_encolar` solo con tocados.
10. T7 con UoW en memoria **propia**, no la de `test_f024_cuadrante_empresa.py`
    (design §9): sin transacción ni traza, R19/R22/R23 no se comprobarían.
11. Front: `#btn-sync` con `() => sincronizarYTraer()`: los arneses ajenos de
    `test_f050_t15e_sombreado.py`, `test_f029_seleccion.py` y
    `test_f050_m2_arreglos.py` solo definen `sincronizar`; con la referencia
    directa fallaba `ReferenceError: sincronizarYTraer is not defined`.
12. La ventana usa `#modal-registro`, sin casillas.
13. **B, la obra especial por código**: `cubierta` reconoce postventa, VAR y
    pruebas por `obra_cod` (la lectura va por empresa), no por `ide` (design
    §6.1): el preflight no siempre las resuelve y así no hay lectura más.
14. En pruebas, «alguna acción tiene su partida» compara también la partida 0:
    una omitida sin partida cubre las sin partida de la 0404 (menos sobrantes).
    15. El lote que falla no da sobrantes.
16. `PonerACero` importa `_fila` y `_traza` de `registro_pipeline.py`; «en la
    0404» = `hmoide` entre sus partes del periodo; lotes de 15 (`SIGRID_MAX_STATEMENTS`).
17. T14: `poner_a_cero` con la empresa por defecto de la api
    (`self._por_defecto`), la del preflight; viajan los campos que relee la
    guarda (`hmores_ide, recurso_ide, hora, vinculado, can, synckey`). Un
    `sobrantes_a_cero` mal formado es 422 sin escribir; si poner a 0 falla,
    no se escribe nada por obra.
18. T15: «la línea sigue en su parte, a 0», no «no se borran» (un test ajeno
    prohíbe «se borran» en `app.js`). 19. T16: la remisión de
    `#regla-vinculado` es un párrafo tras la firma del punto 22.

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

## Fase RED de T1-T15 (trazas reales; comando y salida)

Desde la carpeta del servicio: `.venv/Scripts/python -m pytest tests/<fichero>
-q -p no:cacheprovider` (módulo ya escrito: apartado para la RED).

- T1 `test_f054_lectura_mensuales.py`: `E AttributeError: 'SigridWriteClient'
  object has no attribute 'lineas_mensuales_del_periodo'` → `16 failed in 4.11s`.
- `1 error`, `E ModuleNotFoundError: No module named …`: T2 `test_f054_traduccion.py` (`'application.services.porcentajes_existentes'`, `1.14s`), T4 `test_f054_comparar.py` (`'domain.traer_sigrid'`, `1.82s`), T7 `test_f054_aceptar.py` (`'application.traer_sigrid'`, `5.39s`), T11 `test_f054_obra_cero.py` (`'application.services.reglas_obra_cero'`, `0.49s`), T13 `test_f054_poner_a_cero.py` (`'application.pipelines.poner_a_cero'`, `0.37s`).
- `E ImportError: cannot import name …`: T5 `test_f054_rutas.py` (`'PorcentajesSigridNoDisponible' from 'domain.errors'`, `1 error in 1.26s`), T6 `test_f054_aceptar.py` (`'MOTIVO_TRAIDA_DE_SIGRID' from 'infrastructure.db.repositories'`, `6.03s`).
- T3 `test_f054_endpoint.py`: `FAILED …test_f054_contrato_de_la_respuesta`,
  `…empresa_no_valida_422_sin_leer[None|0|-1|True|x]`,
  `…test_f054_r3_lectura_que_falla_502` → `11 failed, 1 warning in 12.56s`.
- T8 `test_f054_rutas.py`: `E AssertionError: {"detail":"Not Found"}` / `E
  assert 404 == 200` / `E AttributeError: 'Contenedor' object has no attribute
  'traer_sigrid'` → `14 failed, 8 passed, 1 warning in 29.07s` (8 de T5).
- T9 front `test_f054_traer_front.py`: `E AssertionError: no existe la función
  sincronizarYTraer en app.js` (10), `… pintarTraerSigrid …` (1) y el enlace
  de `#btn-sync` → `12 failed in 0.84s`. T15 front `test_f054_modal_cero.py`:
  `… pintarSobrantes en app.js` → `5 failed in 0.33s`.
- T12 `-k lote`: `E AttributeError: 'RegistroLote' object has no attribute
  'preflight_completo'` (7) y `E KeyError: 'sobrantes'` → `8 failed, 1 passed, 11 deselected`.
- T14 api `test_f054_registro_cero.py`: `E AssertionError: assert [('preflight_lote', False)] == [('preflight_lote', True)]` (4), `E TypeError: RegistroSigrid.ejecutar() got an unexpected keyword argument 'sobrantes_a_cero'` (4), `E AttributeError: 'TransferClient' object has no attribute 'poner_a_cero'` (2), `E TypeError: TransferClient.preflight_lote() got an unexpected keyword argument 'completo'` → `11 failed, 1 passed in 3.05s`.

## MANUAL pendientes (NO ejecutadas; comando exacto en `tasks.md`)

- **T10** (líder, solo lecturas): preflight de 2026-09 desde el front, tres
  pasadas (F-055 T18), en `ccad4db` (**antes de B**). **Hecha el 2026-10-30**:
  12,25 / 9,20 / 10,34 s, **mediana 10,34 s** (umbral de T19: ≤ 11,89 s); el
  log del transfer, solo `preflight-lote` y `propuesta-lote`.
- **T18** (humano, local, solo lecturas; **tras cerrar T23**): 1) Git Bash: `curl -s -X POST http://localhost:8006/api/porcentajes/existentes -H "Content-Type: application/json" -d '{"empresa":1,"ano":2026,"mes":9,"obras":[]}'`. 2) **Nuevo**: front, 2026-09, «Sincronizar Sigrid» → una sola tabla, **ninguna** casilla marcada; `0694` en Obra → solo sus filas y «Aceptar 0 marcadas»; «Marcar las visibles» → «Aceptar N marcadas»; otra obra en el filtro → «(N ocultas por el filtro)»; «Desmarcar todas» y vaciar el filtro → «Aceptar 0 marcadas»; dos clics en Obra → orden invertido; con `0694`, marcar solo la `MADM`, aceptar y «Deshacer» (si sale `igual`, otra `distinta`/`solo_sigrid`, y anotarlo). 3) y 4) como en `tasks.md` → `progress/manual_F-054.md`.
- **T19** (humano, `OBRA_PRUEBAS_FORZAR=true`): líneas a mano en la 0404;
  `cd services/dedicacion-transfer && .venv/Scripts/python
  prueba_escritura_porcentajes.py estado --ano 2026 --mes 11`; registrar sin
  marcar y marcando; preflight ≤ 1,15 × mediana de T10. **Es la única prueba
  que escribe y no la ha lanzado ningún agente.**
- **T20** (líder, al desplegar): **transfer → api → front**; refrescar
  `azure-apps/dedicacion.md` desde `docs/INTEGRACION.md` (`git -C`) y avisar
  a `partes`: el transfer pone a 0 (sin borrar) `M*` y de vinculados en
  partes compartidos. **Fuera**: `features.json` y el cierre (líder).

## T23 · 2026-11-02 (enmienda tras T18): PARADA, falta una decisión

- **Hecho**: RED `828b393` (`test_f054_traer_front.py`: 18 tests nuevos de R39-R42; de T9 cambian, sin borrarse, el de la casilla, que ahora fija **ninguna** `checked` (D12), el de las escuchas, sin casillas, sin pulsar y aceptar, que lee el modelo). Código `8c83473`, **sin cerrar T23**: en `app.js` las puras `filasTraerVisibles` y `textoAceptarTraer` y `modeloTraerSigrid`, `textoBotonTraer`, `cuerpoTraerSigrid`, `titulosTraerSigrid` (▲/▼); `filaEntradaSigrid(f)`, `pintarTraerSigrid(datos, modelo)`, `aceptadasMarcadas(modelo)` y `abrirTraerSigrid` (modelo en su cierre; escuchas en `#traer-titulos`, `#traer-filtros` y `#traer-cuerpo`; repinta títulos, `<tbody>` y botón, nunca los filtros). CSS `.acciones-traer`, `.tabla-traer`. Api, transfer y contrato, intactos.
- **RED** (desde el front, `.venv/Scripts/python -m pytest tests/test_f054_traer_front.py -q -p no:cacheprovider`, antes del código): `E AssertionError: no existe la función modeloTraerSigrid en app.js` (35) y `… textoAceptarTraer …` (1) → `36 failed, 2 passed in 2.77s`. Tras `8c83473`: `38 passed in 9.62s`.
- **Motivo de la parada**: front entero `1 failed, 504 passed in 74.79s`. Cae `test_f050_modal_registro.py::test_f050_r29_el_front_ya_no_manda_overrides_ni_lee_catalogos`, que exige `"<select" not in JS` en **todo** `app.js` (F-050 T12, `46b393a`: el modal de registro elige la partida sin `<select>`). El desplegable de Estado de R41 es un `<select>`. El test **no** está en la lista cerrada de `tasks.md` ⇒ no se toca; tampoco se esquiva (un `createElement("select")` cumpliría la letra y no la intención).
- **Opciones para el humano**: (a) **recomendada**: acotar esa aserción a lo que protege F-050 (`"<select" not in _funcion("pintarModalPreflight")`, o ningún `select` de partida) y sumar el fichero a la lista cerrada; el `<select>` de T23 filtra estados, no elige partida. (b) Estado como filtro de texto, como los otros (cambia R41). (c) Desplegable sin `<select>` (botón y panel, como el selector de partida): más código y más mutantes.
- **Pendiente tras decidir**: `ARCHITECTURE.md` punto 23, mutación manual de `app.js` (mecanismo de `progress/mutacion_manual_F-054.md`), `bash harness/init.sh` sin `[KO]`, T23 `[x]` y la MANUAL T18 paso 2. Sin tocar: `current.md`, `features.json`, los `.env`.
- Detalle a confirmar: el rótulo sigue la spec al pie de la letra, «Aceptar 1 marcadas» incluido; se puede poner en singular si se quiere.

## Evidencias

`bash harness/init.sh` tras T22 (`.arnes_cache/suite_*.ok` borrados antes): código 0, sin `[KO]`.

| Evidencia | Resultado real |
|---|---|
| Tests | api `1469 passed` (152,47 s); transfer `1865 passed` (69,40 s); front `489 passed` (241,96 s); raíz `418 passed, 1 skipped` (72,71 s). Antes de T22 (`36a7d4b`): 1469 / 1849 / 488 / 418+1 |
| Cobertura de líneas cambiadas | **99,5 %** (755/759, umbral 80 %; antes 748/752). No mide JS |
| Mutación Python | T22: 266 generados, **266 muertos, 0 supervivientes**, 0 timeouts, 4 workers, 3696 s, SHA `a781d25`; `reglas_porcentajes.py` no genera ninguno: RM4 a mano, **8/8 muertos** (`progress/mutacion_F-054.md`). Antes: `c70eb61` 266/266 (4837 s), `c614be3` 262/262 |
| Mutación `app.js` | manual, **69 + 14 (O5) mutantes, 0 supervivientes**: `progress/mutacion_manual_F-054.md`; T22 no toca `app.js` |

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
