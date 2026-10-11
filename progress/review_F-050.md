<!-- progress/review_F-050.md -->
Revisión incremental desde c5d07c9 (pasada 4) · `c5d07c9..49a9003`

# F-050 · Review

**Veredicto (pasada 4): APPROVED** (APROBADO). El cambio 1 de la pasada 3
está arreglado y probado con el orden exacto que lo rompía (y el contrario);
las observaciones 2 y 3, recogidas; T17 dice «(a)-(h)». Quedan pendientes
T17-T18, que son MANUAL (el humano), como en las pasadas anteriores.

**Rigor:** `critico`, declarado: RED, cobertura ≥ 80 %, mutación con cero
supervivientes sin justificación aceptada y MANUAL con comando exacto.

## Pasadas anteriores (resumen)

- **Pasada 1** (`82bf8d6..5f66b9d`, completa): CAMBIOS PEDIDOS, papeleo.
  Íntegra: `git show 493bf35:progress/review_F-050.md`.
- **Pasada 2** (`5f66b9d..d53a162`): APROBADA (T15b, RED reproducidos).
  Íntegra: `git show 8e9e8de:progress/review_F-050.md`.
- **Pasada 3** (`d53a162..8e9e8de`, T15c): CAMBIOS PEDIDOS: 1) «Registrar» se
  quedaba en «Analizando…» si, con dos repreflights en vuelo, volvía bien la
  700 y después fallaba la 694 (el `catch` reactivaba el botón viejo, ya fuera
  del DOM); 2) T17 decía «(a)-(g)». Observaciones 1-3 (manija, `obra_ide`
  crudo, `ok` de `unirPreflight`). Íntegra: `git show 49a9003:progress/review_F-050.md`.

## Pasada 4 · lo ejecutado por el reviewer

- Sin `.arnes_cache/suite_*.ok`, `bash harness/init.sh` tal cual y solo:
  **ENTORNO LISTO**, ningún `[KO]` (`ruff` 237, el aviso de siempre). Raíz
  **418 passed, 1 skipped** (42,9 s), api **780** (42,9 s), front **221**
  (22,5 s), transfer **750** (7,7 s). `PUERTA COBERTURA` **100,0 %
  (353/353)**; `PUERTA TAMAÑO` en verde.
- **Python, recálculo puro en HEAD** (`alcance_de_feature` +
  `generar_mutantes`): **19 ficheros, 882 líneas, 164 mutantes**, idéntico al
  informe; los 4 nuevos son de `_obra_ide` (`routes.py:79, 82, 83, 83`).
  Campaña no reejecutada: 1796,6 s según el informe.
- **Copia aislada** (`git worktree add --detach` de HEAD en el scratchpad,
  suites con los `.venv` del repo; front 221 y `test_f050_preflight_obra` 12
  en verde sin mutar). Reproducidas al pie de la letra **T47 → 2 fallos, T50
  → 2, T51 → 1**, los del informe manual; y dos de Python: `routes.py:83`
  `and not`→`or not` **3 fallos**, `:82` `or`→`and` **3 fallos**. Copia
  retirada; `git status` del repo limpio. Nada contra Azure ni Sigrid.

## Lo pedido en la pasada 3

1. **Cambio 1, resuelto.** El `catch` de `repreflightPartida` busca el botón
   de ahora (`$("#btn-ejecutar-registro")`, `app.js:2103`) en vez del `btn`
   del principio, y solo lo reactiva sin obras en vuelo. El test nuevo
   `…_error_despues_de_que_la_otra_vuelva_bien` lleva el **orden exacto** de la
   pasada 3 (`repreflightPartida(694); repreflightPartida(700)` → resuelve la
   700 → rechaza la 694) y además el contrario; comprueba el botón bloqueado
   entre medias, el toast, «Registrar» activo al final y el pintado. RED real
   en el informe (`{'disabled': True, 'textContent': 'Analizando…'} != …`, ×2).
2. **T17 «(a)-(h)»**: hecho (`c5d07c9`); comprobado en `tasks.md`.

## Observaciones de la pasada 3

- **Obs. 2, recogida.** `_obra_ide` (`routes.py:75`): `None` pasa; `"694"` y
  `694.0` → `694`; texto, decimal, booleano, lista, `Infinity` → `ObraNoValida`
  (422, ya mapeada en `app.py:40`) **sin analizar** (test: `llamadas == []`).
  `0` sigue filtrando (`is not None` en `registro_sigrid.py:139`). Documentado
  en `docs/INTEGRACION.md` y en `azure-apps/dedicacion.md` (`36c894a`).
- **Obs. 3, recogida.** `unirPreflight` recalcula `ok` con `every` sobre todas
  las obras; coincide con la api (`all(...) if resultados else True`,
  `registro_sigrid.py:145`). Test con los cuatro casos (incluido sin obras).
- **Obs. 1** (manija con la tabla encogida): sigue para la M2 (h) 1.

## Test propio cambiado

`test_f050_m2_5_unir_quita_la_obra_que_ya_no_viene_y_anade_la_nueva` (T15c)
compara el dict entero; sus dos esperados ganan `"ok": True`. **Se endurece**:
antes no miraba `ok`; ahora exige el valor recalculado. No relaja nada. Es de
F-050; ningún test de otra feature cambia en el delta.

## Checkpoints (lo que toca el delta)

- **C1** [x] init.sh sin caché, ENTORNO LISTO · [x] ficheros base.
- **C2** [x] una `in_progress` · [x] rama · [x] `current.md` al día («Review 4
  lanzada», `azure-apps` `36c894a`) · `history.md` N/A: F-050 no está `done`.
- **C3** [x] límite de servicio: api y front; transfer intacto · [x] el front
  no decide qué se escribe (`ok` solo agrega lo que devuelve la api; nadie lo
  lee) · [x] la validación de entrada vive en la ruta (capa de interfaz) ·
  [x] primera línea con ruta · [x] sin `console.log`/`print` ni secretos.
- **C3 bis** N/A: el delta no toca `docs/referencia/`. **C4 ter** N/A: no
  existe `harness/rutas_sensibles.json`.
- **C4** [x] tests sin red ni BBDD (node local y dobles) · [x] el camino de
  error del punto 5, en los dos órdenes · [x] MANUAL T17 con (a)-(h).
- **C4 bis**
  - [x] `rigor` · [x] RED real de los tres arreglos (impl 184-199).
  - [x] cobertura 100 % · [x] Python recalculado (164 = 164).
  - [x] RM1: medido en `ee4c70d`; después solo cambian `progress/` y
    `docs/INTEGRACION.md` (sin código del alcance).
  - [x] RM2: 164 × 11,0 s ≈ 1804 s frente a 1796,6 s; media < base (38,9 s
    api) con 164/164 muertos y `-x`: coherente.
  - [x] Sin «⚠ CAMPAÑA NO VÁLIDA»; «Sin veredicto (base rota)» = 0.
  - [x] RM3: ningún equivalente muerto (los 4 de `_obra_ide` cambian el
    resultado observable) · [x] RM5 N/A: ningún equivalente declarado ·
    [x] RM6: no se quita ninguna guarda; se añade una.
  - [x] MANUAL JS T47-T53: 7 filas con texto exacto, SHA `ee4c70d` y fallos;
    tres reproducidas · [x] cero supervivientes · [x] Evidencias, 4 números.
- **C5** [x] commits `F-050 T15c: review 3 …` · [x] T16 hecha; T17-T18
  MANUAL pendientes (humano) · [x] sin artefactos (copia retirada).

## Cobertura requisito → test (`test_f050_*`)

| R | Test |
|---|---|
| R1-R21 | sin cambios desde la pasada 2 (`propuesta`, `pipeline`, `partida_linea`, `rutas_partida`, `endpoint_propuesta`) |
| R22-R28 | `subfilas` `r22_*`-`r25_*`, `r28_*`; `selector` `r26_*`, `r27_*` |
| R29 (+ amp.) | `modal_registro` `r29_*` |
| T15c 1-5 | `m2_arreglos` `m2_1_*`…`m2_5_*`; api `preflight_obra` `m2_5_*` |
| Rev. 3 | `m2_5_error_despues_de_que_la_otra_vuelva_bien` (×2), `m2_5_unir_recalcula_el_ok_*`; api `m2_5_la_ruta_convierte_*`, `m2_5_obra_que_no_es_entero_422_*` (×5) |
| R30 | `test_f002_fuente_unica`, `test_f004_readme` |

## Cambios requeridos

Ninguno.

## Observaciones (no bloquean; que el líder las recoja, no «anotado»)

1. **`trabajador_ide` crudo** (`routes.py:393` preflight y `:409` ejecutar).
   No es inyección (va como parámetro ligado) y el front manda un número o
   `null`. Dos riesgos, ninguno de F-050 (la ruta de `ejecutar` no se tocó):
   a) `registro_sigrid.py:81` filtra con `if trabajador_ide`, así que un
   valor falso (`0`, `""`, `false`) **quita el filtro** y `ejecutar` registra
   el mes entero en vez de una línea; b) un `"abc"` llega a PostgreSQL y
   sale 500, no 422. Propuesta: una feature pequeña (rigor `critico`, toca la
   escritura) que lo valide como `_obra_ide` en las dos rutas y cambie el
   filtro a `is not None`.
2. **Tras un error, el bloque de esa obra enseña el análisis anterior** y
   «Registrar» vuelve activo; `ejecutar` recalcula desde la base, con la
   partida nueva. Viene de F-049 (el `catch` ya reactivaba el botón) y el
   toast lo avisa. Si molesta, marcar el bloque «sin analizar» o mantener
   «Registrar» bloqueado hasta un análisis bueno. Mirarlo en la M2 (h) 5.
3. La manija de ancho (obs. 1 de la pasada 3): en la M2 (h) 1.

## Automejora (propuesta, no aplicada; sigue en pie)

Casilla MANUAL con texto exacto y SHA (pasada 2); test por **orden de
llegada** en peticiones concurrentes del front (pasada 3), a `CHECKPOINTS.md`.
