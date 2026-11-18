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
(RED), `fd56da6` (código), `69647cf` (4 bis), `a781d25`. T23: `828b393` (RED) … `b660091`. T24-T26 (2026-11-03): ver su sección. MANUAL: T10, T18-T20.

## Ficheros tocados

- transfer: `sigrid_write_client.py`, `registro_models.py`, `app.py`;
  nuevos `porcentajes_existentes.py`, `reglas_obra_cero.py`,
  `poner_a_cero.py`; `lecturas_lote.py` y `registro_lote.py` (ronda A,
  `preflight_completo`); `reglas_porcentajes.py`, solo `omitir`/`decidir`
  (T22, D19); `universo_var.py` (T25-T26); `registro_pipeline.py`, solo
  los tres motivos de T26.
- api: `domain/{models,errors,ports,traer_sigrid}.py`,
  `application/{traer_sigrid,registro_sigrid}.py`, `transfer_client.py`,
  `db/{repositories,orm_models}.py`, `api/{app,routes,schemas,deps}.py`.
- api, además, `domain/obras.py` (T26). Front `app.js` y `styles.css`; docs
  `ARCHITECTURE.md` (puntos 23-24, `#regla-var`) e `INTEGRACION.md`.
- tests nuevos `test_f054_*` en los tres servicios; ajenos, solo la lista
  cerrada (`ANCLAS`; dobles `preflight_lote` de F-022/F-024/F-055 con
  `completo=False`, sin cambiar aserciones).

## Decisiones de diseño y desviaciones (justificadas)

1. **Vigencia por `vigente_en`** (activo + baja), no solo `activo` (design
   §5.2); el trabajador fuera del listado se lee con `obtener` («no vigente»,
   no «fuera del maestro»). 2. `ExistentesIn.empresa` sin tipo: lo no válido
   da 422 sin leer. 3. La 0404 siempre se excluye en A (R5); `lineas_leidas`
   cuenta todas. 4. Solo salen trabajadores con alguna entrada de Sigrid.
   5. Obra en la base fuera del listado: inactiva, «no se ofrece».
6. **Relectura del periodo** con `populate_existing=True`: sin ello no se veía
   un cierre entre medias (R22, 409). 7. «Después» del evento `SIGRID`, en
   memoria (el ORM podía no refrescar tras `ON CONFLICT`). 8. Aceptadas
   repetidas, una vez. 9. Sin cuerpo = comparar; `_encolar` solo con tocados.
10. T7 con UoW en memoria propia (sin transacción ni traza, R19/R22/R23 no se
    comprobarían con la de `test_f024`). 11. `#btn-sync` con `() =>
    sincronizarYTraer()`: arneses ajenos (`test_f050_t15e`, `test_f029`,
    `test_f050_m2`) solo definen `sincronizar` (`ReferenceError`). 12. La
    ventana usa `#modal-registro`. 13. **B**: `cubierta` reconoce postventa,
    VAR y pruebas por `obra_cod`, no por `ide` (sin lectura más). 14. En
    pruebas compara también la partida 0. 15. El lote que falla no da
    sobrantes. 16. `PonerACero` importa `_fila`/`_traza`; «en la 0404» =
    `hmoide` entre sus partes; lotes de 15. 17. T14: `poner_a_cero` con la
    empresa por defecto; viajan los campos que relee la guarda; mal formado,
    422 sin escribir; si falla, nada por obra. 18. T15: «sigue en su parte, a
    0» (un test ajeno prohíbe «se borran»). 19. T16: la remisión de
    `#regla-vinculado`, párrafo tras la firma del punto 22.

## Review 1, T22 y T23 (resumen; detalle y trazas en `progress/impl_F-054_anexo.md`)

- **Review 1**: O1 `e881a17`, O4 `56dd403`, O2 `5d426b5`, O5 `97e5fed`; O3 y O6 sin cambio (RED en el anexo).
- **T22 (D19)**: `abd5514` RED (`6 failed, 8 passed`), `fd56da6` código,
  `69647cf` 4 bis, `a781d25`; consumidores lector por lector, en el anexo.
- **T23**: `828b393` RED (`36 failed, 2 passed in 2.77s`) … `b660091`; opción
  «a» del humano para `test_f050_r29_…`; campañas 5-6, 84 mutantes, 0 vivos.

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

## MANUAL pendientes (NO ejecutadas por ningún agente)

- **T10**: hecha el 2026-10-30 (`ccad4db`): mediana **10,34 s** (T19 ≤ 11,89 s).
- **T18** (humano, local, solo lecturas). 1) Hecho el 2026-11-02: en Git Bash
  `curl -s -X POST http://localhost:8006/api/porcentajes/existentes -H
  "Content-Type: application/json" -d '{"empresa":1,"ano":2026,"mes":9,"obras":[]}'`.
  2) **Pendiente, tras T23-T25 y T27**: la ventana de «Sincronizar Sigrid» y
  «No se traen» (cabecera estándar, filtros, «Limpiar», «×K», códigos) y, de
  R48 (rehecha), al bajar solo se mueven las filas: lo de arriba quieto y opaco,
  columnas alineadas, pie a la vista, sin hueco. 3) Preflight (T26). 4) Sincronizar ⇒ `igual`. Pasos exactos:
  `tasks.md` T18 y `progress/current.md` → `progress/manual_F-054.md`.
- **T19** (humano, `OBRA_PRUEBAS_FORZAR=true`, la única que escribe): `cd
  services/dedicacion-transfer && .venv/Scripts/python
  prueba_escritura_porcentajes.py estado --ano 2026 --mes 11`; registrar sin
  marcar y marcando; preflight ≤ 1,15 × 10,34 s.
- **T20** (líder, al desplegar **transfer → api → front**): refrescar
  `azure-apps/dedicacion.md` desde `docs/INTEGRACION.md` (`git -C
  C:/Users/pgris/PycharmProjects/azure-apps`) y avisar a `partes`. Nuevo de
  T25-T26: la api manda `partida_cod` en las líneas VAR (ya en
  `INTEGRACION.md` §5) y `no_traidas` gana `recurso_cod`/`recurso_nombre`.

## T24-T26 · 2026-11-03 (D20, D21): cabecera estándar, «No se traen», códigos

**Commits**: T24 RED `1b25a0c`, código `0fc94fb`, tests de la campaña 7
`cf28eea`/`4e5ac80`; T25 RED `de7951e`, código `9dd4465`; T26 RED `d6224b4`,
código `086983a`; cierre (tasks `[x]`, campañas, informe, anexo) el último.

- **T24** (`app.js`, `styles.css`): las dos tablas `tabla-reg filterable`
  con el marcado de `renderCabeceraTabla()` (`titulosOrdenables`,
  `celdaFiltroTraer`); el `<select` de Estado sigue en `pintarTraerSigrid`.
  `enlazarCabeceraTraer(tabla, parte, repintar)`, común: clic con
  `closest("[data-orden]")`, Escape solo en `INPUT` (sin cerrar), «Limpiar»
  vacía filtros y campos de esa fila sin tocar orden ni casillas. Puras
  `agruparNoTraidas` y `noTraidasVisibles` (Líneas numérica). Fuera
  `.tabla-traer`, `th.ordenable`, `#traer-filtros th`, `.filtro-traer`.
- **T25**: transfer `MOTIVO_PV_*` con `partida_cod or paride` y `codigo or
  ide`; `partida_var_de(…, *, partida_cod, obra_cod)`. Api
  `ObraRepository.codigos` (port y Pg; `existen` sigue, la usa
  `use_cases.py`), `_nombre_obra` VAR `<obra>-<partida>` o
  `VAR-<var_paride>`, `NoTraida`/`NoTraidaOut` con `recurso_cod`/`_nombre`.
- **T26**: `CatalogoVar.codigos` (presupuesto ya leído, `{}` por defecto) y
  `partida_var_de` con `codigos.get(var_paride) or partida_cod or
  var_paride`; `registro_pipeline.py`, solo los motivos `VAR_POSTVENTA`,
  la llamada (`obra_cod=origen.codigo`) y `PARTIDA_PV_NO_HOJA`. Api
  `partida_de_entrada` y la línea VAR con `partida_cod` solo si no es `None`
  (nadie lo usa para decidir: test `…_el_partida_cod_de_la_var_no_decide_nada`).
- **Interpretaciones (para el reviewer)**: a) «ni `ordenable` en `app.js`»
  se lee como la **clase** (`class="ordenable"`); la propiedad `ordenable` de
  `COLUMNAS` (tabla principal, tests de F-044/F-050) sigue. b) Dos obras con
  el mismo código salen «(0678, 0678)», como dice la spec. c) Un test de T26
  partía de una premisa falsa (sin `codigo` en la petición, el pipeline
  resuelve la obra en Sigrid): rehecho como
  `…_otra_obra_por_el_codigo_de_la_obra_resuelta` antes del código.
- **Tests anteriores cambiados**: lista cerrada (T26) `test_f039_preflight_var.py`,
  `test_f002_postventa.py` (`"11"`), `test_f025_universo_postventa.py`
  (`"0713"`), api `test_f039_registro_var.py` y `test_f050_partida_linea.py`
  (`"29"`). De F-054: `test_f054_traer_front.py` (escuchas, r39-r41, dobles),
  `test_f054_traduccion.py` (`"0678, 0678"`; r10 `"28"`), `test_f054_mutacion.py`
  (×2), `test_f054_aceptar.py`, `test_f054_comparar.py`, `test_f054_rutas.py`.
  Ninguno más; `test_f050_modal_registro.py` sin tocar (`17 passed`).
- **Consumidores** (grep, tres servicios): `MOTIVO_PV_*`, solo
  `porcentajes_existentes.py`; `partida_var_de`, ella y `registro_pipeline.py`;
  `no_traidas`/`NoTraida`, `traer_sigrid.py`, `schemas.py` y `app.js`. Ningún
  motivo entra en `clave_conflicto`; `pintarModalPreflight` solo lo pinta.
- **Docs**: `ARCHITECTURE.md` punto 23 y `#regla-var`; `INTEGRACION.md` §5.

**RED** (desde cada servicio, `.venv/Scripts/python -m pytest <ficheros> -q
-p no:cacheprovider`, antes del código):

- T24 front `tests/test_f054_traer_front.py`: `E AssertionError: no existe la
  función titulosOrdenables en app.js` (49), `… agruparNoTraidas …`, `…
  enlazarCabeceraTraer …`, `filtro-traer` presente → `52 failed, 4 passed in
  4.80s`. Tras `0fc94fb`: `56 passed`; con la campaña 7, `60 passed`.
- T25 transfer `tests/test_f054_traduccion.py tests/test_f054_mutacion.py`:
  `- (0678, 0678) + (555001, 555999)`, `- la partida 11 … + la partida 70002
  …`, `- partida VAR 28 … + partida VAR 417002 …`, `TypeError:
  partida_var_de() got an unexpected keyword argument 'partida_cod'` → `6
  failed, 43 passed in 3.03s`. Api `test_f054_{comparar,aceptar,mutacion,rutas}.py`:
  `'la obra VAR-1234 …' != 'la obra VAR-29 …'`, `AttributeError: 'NoTraida'
  object has no attribute 'recurso_cod'`, `'SimpleNamespace' object has no
  attribute 'existen'`, `'PgObraRepository' object has no attribute
  'codigos'` → `31 failed, 97 passed in 15.97s`.
- T26 transfer `test_f054_motivos_preflight.py test_f039_preflight_var.py
  test_f002_postventa.py test_f025_universo_postventa.py`: `AttributeError:
  'CatalogoVar' object has no attribute 'codigos'`, `- partida VAR 28 … +
  partida VAR 417002 …` → `19 failed, 104 passed in 3.36s`. Api: `ImportError:
  cannot import name 'partida_de_entrada' from 'domain.obras'` (`1 error`) y
  `test_f039_r20_…`/`test_f050_r19_…` → `2 failed, 31 passed`.
- **O11** (review 8, «ok» del humano; `353d290`): `OTRA_OBRA` nombra «VAR (ide N)» si el código es
  el de la VAR (`_nombre_otra_obra`, `universo_var.py`). RED `pytest tests/test_f054_traduccion.py -k "otra_obra or o11"`:
  `'…la obra VAR no es la obra VAR VAR' != '…la obra VAR (ide 12345) no es…'` → `2 failed`. Grep: nadie decide
  por el texto (`app.js` solo hace `exec` de `MOTIVO_PARTIDA_NO_HOJA`; `.motivo ==` solo con `pisado`/`sobrecarga`/`sin_partida`).

**Mutación.** Python (`python -m harness.mutacion --feature F-054`, SHA
`086983a`, 4 workers): **287 generados, 287 muertos, 0 supervivientes**, 0
timeouts, 2676 s (`progress/mutacion_F-054.md`). `app.js`
(`progress/mutacion_manual_F-054.md`): campaña 7 (`0fc94fb`) 90 mutantes, 85
muertos, 5 vivos, todos huecos de test (E4 filtro `recurso` inicial, E6 clave
sin obra, E28 orden sin minúsculas, E46/E49 Parte y Obra sin escapar), tests
nuevos sin tocar producción; campaña 8 (`4e5ac80`): 5/5 muertos. Total T24:
95, **0 supervivientes**.

**`bash harness/init.sh`** (cachés borradas, sin pipes): código 0, **sin `[KO]`**;
cobertura 99.5 % (786/790), impl 212/220. Suites abajo.

## T27 (R48): la ventana de «Sincronizar Sigrid» en tres zonas (rehecha el 2026-11-06)

**Primera versión (historia; detalle en `git show`)**: `5442c4b`/`ff3d1ac` (`thead:has(> #…)` sticky en `.modal`, campaña 9 15/15) y `645ccdb`/`c9611c3` (`--modal-pad-top` y `top` negativo, campaña 10 13/13). La MANUAL de T18 paso 2 la rechazó dos veces; el humano aprobó tres zonas («si hazlo asi», spec `1a2ca2c`). **Rehecha, `f82fd6b`** (RED y código en el mismo commit: la RED se lanzó con los tests nuevos sobre el código de `c9611c3`, abajo). `app.js`, solo `pintarTraerSigrid`: `.acciones-traer` sale del `if (modelo.filas.length)` (con casillas siempre hay filas: mismo HTML) y las dos tablas y el `<h3>` «No se traen» van en `<div class="zona-traer" id="traer-zona">`, pintado siempre, hijo directo de `.modal`, justo antes de `.pie-modal`; `id`, escuchas y `abrirTraerSigrid`, iguales. `styles.css`: `.modal` vuelve a `padding: 22px 26px` (fuera `--modal-pad-top` y su comentario); en lugar de `thead:has(> #…)`, las reglas (a)-(d) de la spec, literales.
**Tests** (lista cerrada, solo `test_f054_r48_*` de `test_f054_traer_front.py`): fuera `…_el_top_compensa_el_padding_superior_del_modal` y `…_la_regla_fija_las_dos_cabeceras…`; `SELECTORES_R48` y `DECLARACIONES_R48` (sustituye a `TOP_R48`) a lo nuevo; nuevos: las cuatro reglas exactas (parametrizado; el retoque `083076c`, abajo, suma la quinta), ninguna otra nombra `.zona-traer`, `.modal` con `22px 26px` y ni `--modal-pad-top` ni `thead:has(` en CSS ni `app.js`, solo dos `sticky`, zona una vez con dentro las tablas y «No se traen» y fuera (antes) `<h2>`, avisos y `.acciones-traer` y (después) el pie, sin «No se traen», sin entradas, sin nada (zona vacía), zona hija directa (divs equilibrados antes), registro sin `zona-traer`; siguen `…_cada_th…_fondo_opaco` y `…_los_id_van_en_la_primera_fila…`. Ningún test de T9/T23-T24 tocado.
RED: `cd services/dedicacion-front && python -m pytest tests/test_f054_traer_front.py -k r48 -q --tb=line -p no:cacheprovider` (sobre `c9611c3`) → `E AssertionError: falta (o sobra) la regla «columna» de T27` (y «hijos», «zona», «cabecera»); `E AssertionError: assert 'var(--modal-pad-top) 26px' == '22px 26px'`; `E AssertionError: assert [['.topbar'],...as-titulos)']] == [['.topbar'],...traer thead']]`; `E AssertionError: assert [] == [('.modal:has...raer thead',)]`; `E AssertionError: la zona, una vez` / `assert 0 == 1` (×5) → `12 failed, 3 passed, 60 deselected in 1.88s`.
Verde: `-k r48` `15 passed, 60 deselected in 1.80s`; el fichero `75 passed`; front entero (`.venv`) `542 passed, 19 warnings in 125.48s`. **Campaña 11** (`progress/mutacion_manual_F-054.md`): **38/38 muertos**, 0 vivos (28 de CSS: cada declaración, valores vecinos, cada selector, la regla y la variable de `c9611c3`; 10 de `app.js`: pie, acciones, título o «Ningún trabajador» dentro, «No se traen» fuera, sin cerrar, sin `id`, otra clase, condicional, anidada). **Riesgos que solo ve la MANUAL** (no los ve un test sin navegador): `:has` (Edge/Chrome ≥ 105), márgenes de `h2`/`p` que en flex no colapsan, hueco, transparencia o columnas desalineadas ⇒ PARA (T27). Pendiente: review y T18 paso 2 con R48.
**`bash harness/init.sh`** (`d510084`, `.arnes_cache/suite_*.ok` borrados, sin pipes): código 0, **sin `[KO]`**, «ENTORNO LISTO»; raíz `418 passed, 1 skipped` (46,47 s), api `1504 passed` (61,63 s), front `542 passed` (59,28 s), transfer `1887 passed` (19,16 s); cobertura 99.5 % (793/797); tamaño requirements 150/150, design 250/250, impl 219/220.
**Retoque (2026-11-06, MANUAL T18 paso 2 sobre `f82fd6b`: «casi perfecto», franja de ~1 px entre títulos y filtros por la que pasaban las filas), `083076c`**: `border-collapse: collapse` deja los bordes en la rejilla, que no viaja con el `thead` fijo; se elige `.zona-traer .tabla-reg { border-collapse: separate; border-spacing: 0; }` (no `box-shadow` inset: habría que rehacer el borde de cada `th`/`td` y su color; con `separate` cada celda lleva el suyo y viaja con ella; sin dobles porque ninguna celda de esas tablas lleva borde arriba ni a la izquierda, mismo aspecto; va tras `.modal .tabla-reg`, igual especificidad; registro y cuadrante, intactos). Tests: `bordes` en `SELECTORES_R48`/`DECLARACIONES_R48` y nuevo `…_los_bordes_viajan_con_la_cabecera_sin_dobles`. RED (`cd services/dedicacion-front && .venv/Scripts/python.exe -m pytest tests/test_f054_traer_front.py -k r48 -q --tb=line -p no:cacheprovider`) → `AssertionError: falta (o sobra) la regla «bordes» de T27`, `assert [('.modal:has...raer thead',)] == [...]`, `ValueError: ['.zona-traer .tabla-reg'] is not in list` → `3 failed, 14 passed, 60 deselected in 4.55s`; verde `17 passed`, fichero `77 passed`, front `544 passed, 19 warnings in 224.91s`; **campaña 12: 12/12 muertos**; MANUAL de T18 paso 2 con «sin franja entre títulos y filtros». `init.sh` (`4ae866a`, cachés borradas, sin pipes): código 0, **sin `[KO]`**, «ENTORNO LISTO»; raíz `418 passed, 1 skipped` (175,59 s), api `1504 passed` (275,12 s), front `544 passed` (348,36 s), transfer `1887 passed` (58,02 s); cobertura 99.5 % (793/797); impl 220/220.

## Evidencias

| Evidencia | Resultado real |
|---|---|
| Tests | 2026-11-06, tras T27 rehecha (`init.sh`): api `1504 passed` (61,63 s), front `542 passed` (59,28 s), transfer `1887 passed` (19,16 s), raíz `418 passed, 1 skipped` (46,47 s). 2026-11-05, tras T27: api `1504 passed` (223,45 s), front `531 passed` (251,20 s), transfer `1887 passed` (79,66 s), raíz `418 passed, 1 skipped` (103,22 s). 2026-11-03, tras T24-T26: api `1502 passed` (81,77 s), front `527 passed` (82,13 s), transfer `1886 passed` (34,62 s), raíz `418 passed, 1 skipped` (43,01 s). Tras T23: api 1469, transfer 1865, front 507, raíz 418+1 |
| Cobertura de líneas cambiadas | **99,5 %** (793/797, tras T27) (umbral 80 %). No mide JS ni CSS |
| Mutación Python | O11: **289/289 muertos**, 0 vivos, 0 timeouts, 2936 s, SHA `353d290`. T24-T26: 287/287, `086983a`. Antes: T22 266/266 (+ RM4 8/8 a mano), `c70eb61` 266/266, `c614be3` 262/262 |
| Mutación `app.js`/CSS | manual: T9/T15 69 + O5 14; T23 81 + 3; T24 90 + 5; T27 15 + 13, rehecha 38 (campaña 11) y retoque 12 (campaña 12); **0 supervivientes** |
| Tiempo de la suite | el de cada suite en la fila Tests |

**Análisis de supervivientes.** Ningún equivalente pendiente del humano. La
campaña 1 (`95cc089`, 207/262, `progress/mutacion_F-054_campana1.md`) dejó 55
vivos Python y 9 de `app.js`: huecos reales, cerrados con tests sin cambiar
producción (detalle en el anexo). Campaña 2, T22 y T24-T26: sin vivos Python.
Los vivos de `app.js` de cada campaña manual (9, C7, D11, D51, E4, E6, E28,
E46, E49) se mataron con tests; D10, equivalente, se quitó del código.
