<!-- progress/review_F-050.md -->
Revisión completa (pasada 1) · `dev...HEAD` = `82bf8d6..5f66b9d`

# F-050 · Review

**Veredicto: CHANGES_REQUESTED** (CAMBIOS PEDIDOS): código sin fallos
bloqueantes; dos `[ ]` de papeleo (C4 bis campaña manual; C5 T19).

**Rigor:** `critico`, declarado: RED, cobertura ≥ 80 %, mutación con cero
supervivientes sin justificación aceptada y MANUAL con comando exacto.

## Lo ejecutado por el reviewer

- Sin `.arnes_cache/suite_*.ok`, `bash harness/init.sh` tal cual: código 0,
  **ENTORNO LISTO**. Raíz **418 passed, 1 skipped** (94,9 s), api **768**
  (74,0 s), front **184** (30,0 s), transfer **750** (14,8 s).
  `PUERTA COBERTURA` **100,0 % (341/341)**. `ruff` `[AVISO]` 237: mismos
  avisos en `dev` y en HEAD por fichero modificado; los nuevos, ninguno.
- Mutación Python, recálculo puro (`harness.alcance` +
  `generar_mutantes`): **19 ficheros, 854 líneas, 158 mutantes**, igual que
  el informe. **Campaña no reejecutada: 1236,8 s según el informe** (> 60 s).
- JS manual: **J04, J47 y J56** reproducidos al pie de la letra en un
  worktree del scratchpad (retirado): fallos **6, 2 y 1**, los del informe.
- **Una lectura en Sigrid** (solo lectura, `sigrid-api` vía el cliente del
  transfer local): `con.ide = 1705036` → «GONZALEZ PANIAGUA, MARIA DE LOS
  MILAGROS», empresa 1: el recurso de M1 es el correcto.

## Lo que pediste comprobar (todo [x])

- **Límite de servicio.** Propuesta, `mayor_de` y `mayor_inicial`, en el
  transfer (puro). La api solo busca el mayor de la elegida en la lista; el
  front filtra por el `mayor` recibido y no lee `categoria`.
- **R7.** Una llamada por petición (lotes de 500), sin `try`; `_read` lanza
  con `truncated`; `ejecutar` con lectura fallida no escribe; endpoint, 502.
- **R20.** Solo la rama manual de obra normal: si no es hoja activa de
  `nodos_origen`, la línea se omite con `MOTIVO_PARTIDA_NO_HOJA`, sin aviso ni
  conflicto, en los dos modos. VAR, postventa, capacidad, cuenta y partes no
  cambian. La lectura extra del presupuesto ya la hacía el bloque F-049.
- **R9.** Preflight y `proponer` llaman a `proponer_partida` con lo mismo;
  la api manda igual obra, empresa y trabajador en los dos caminos (con test).
- **PUT `…/partida`.** 404 (periodo, trabajador, línea u otro modo), 409,
  422 (VAR, `ide` ≤ 0); en error ni `reemplazados` ni eventos; `PARTIDA`
  solo si cambia; Ctrl+Z la devuelve.
- **R14 y F7.** `_conservar_partidas` va antes de comparar snapshots.
  `LineaIn` es `extra="forbid"`: ningún guardado trae partida para una línea
  nueva. F7 (`app.js:1725`) manda obra, modo y %. Copiar el mes copia la
  partida; Completar la conserva.
- **Sin `overrides`.** `grep overrides|partidas_obra|opcionesPartida`: vacío.
- **Tests anteriores.** El diff de `*/tests/*` sin `test_f050_*` toca solo
  la lista cerrada y los dos añadidos del humano; los de T12 coinciden uno a
  uno. No hay aserciones relajadas: lo retirado es lo que R29 elimina y su
  intención pasa a `test_f050_modal_registro.py`.
- **Desviaciones 1-10.** Razonadas y dentro de la spec (la 3 y la 5,
  comprobadas en el código).
- **`azure-apps` `edaa2b7`.** Copia literal de §3, §5 y §7 de
  `INTEGRACION.md`; «sin desplegar»; árbol limpio.
- **MANUAL en `current.md`.** M1 con `cd` absoluto y `--recurso 1705036`;
  M2 con comandos y T17 (a)-(f); M3 solo con autorización. Seguible.

## Checkpoints

- **C1** [x] init.sh código 0 · [x] ficheros base.
- **C2** [x] una sola `in_progress` · [x] la rama es la de F-050 · [x]
  `current.md` refleja la sesión (dos erratas, cambio 3) · [x] `history.md`
  (F-050 aún no está en `done`).
- **C3** [x] hexagonal (el cliente Sigrid importa `LineaHistorial` de
  `application`, hacia dentro, como `cuenta_analitica`) · [x] primera línea
  con la ruta · [x] los `print` son la salida del script; sin secretos ni
  dependencias nuevas · [x] escala 0-100/0-1 intacta, postventa por su
  clave, ninguna escritura nueva en Sigrid.
- **C3 bis** N/A: el diff no toca `docs/referencia/`. **C4 ter** N/A: no
  existe `harness/rutas_sensibles.json`.
- **C4** [x] cada R con test (tabla) y en verde · [x] sin red ni BBDD · [x]
  MANUAL con comando en `current.md`.
- **C4 bis**
  - [x] `rigor` declarado · [x] RED con trazas reales de T1-T13 · [x]
    cobertura `[OK]` 100 % · [x] informe de la herramienta, recalculado.
  - [x] Muertos: > 60 s, vale el recálculo puro · [x] coste 7,8 s/mutante.
  - [x] Sin «⚠ CAMPAÑA NO VÁLIDA»; «Sin veredicto (base rota)» = 0.
  - [x] RM1: medido en `f4cdb11`; después solo cambian `progress/`,
    `tasks.md` y un test, así que el alcance es el mismo.
  - [x] RM2: media 7,8 s × 1 frente a bases de 19,5 y 5,1 s;
    158 × 7,8 ≈ 1232 s.
  - [x] RM5: N/A justificado, no queda ningún equivalente; los 3 de la
    primera pasada se quitaron sin cambiar la conducta (`7f5f115..f4cdb11`).
  - [x] RM6: no se quitó ninguna guarda.
  - **[ ] Campaña MANUAL (JS): 7 de 56 filas sin texto exacto** (cambio 1).
  - [x] Cero supervivientes, sin `PENDIENTE` · [x] Evidencias completas
    (workers 1) · [x] ningún N/A sin motivo.
- **C5** **[ ] T19 («`bash harness/init.sh` en verde») sigue `[ ]`**
  (cambio 2). T1-T13 y T15 llevan su commit `F-050 Tn:`; T14 la hizo el
  líder (`5f66b9d`); T16-T18 son MANUAL, que en `critico` puede quedar
  pendiente, como en F-039 · [x] sin artefactos · [x] `features.json` en
  `in_progress`.

## Cobertura requisito → test (`test_f050_*`)

| R | Test |
|---|---|
| R1-R5, R10 | `propuesta`: `r1_paso1_*`, `r1_paso2_*`, `r2_*empate*`, `r3_paso1_hoja_de_baja…`, `r4_historial_sql…`, `r5_filas_barajadas…`, `r10_orden_natural…` |
| R6-R9, R11, R21 | `pipeline`: `r7_*`, `r9_*`, `r21_*`; `endpoint`: `r8_*`, `r9_misma_propuesta…`, `r11_*`; `propuesta`: `r7_historial_truncado…` |
| R12-R19 | `partida_linea`: `r12_*`, `r14_*`, `r15_*`, `r16_*`, `r19_*`; `rutas_partida`: `r13_*`, `r17_*`, `r18_*` |
| R20 | `pipeline`: `r20_manual_que_no_es_hoja_activa_se_omite` (×6), `r20_ejecutar_no_escribe…` |
| R22-R29 | `subfilas`: `r22_*`-`r25_*`, `r28_*`; `selector`: `r26_*`, `r27_*`; `modal_registro`: `r29_*` |
| R30 | `test_f002_fuente_unica` (`regla-partida`), `test_f004_readme` |

## Cambios requeridos

1. **`progress/mutacion_manual_F-050.md`**: en **J08, J28, J34, J37, J41,
   J43 y J51** el texto original o el mutado está cortado con «…», así que
   la fila no se puede reproducir y C4 bis no se marca. En **J51** lo
   visible del original y del mutado es idéntico: no se sabe qué cambió.
   Hay que poner el texto entero, en la celda o en una lista de mutantes
   versionada en `progress/` y enlazada. Si `js_mut.py` ya no existe, se
   rehacen esos 7 en una copia aislada (unos 15 s cada uno), con sus fallos.
2. **`specs/F-050-subfilas-partida/tasks.md` T19**: marcarla `[x]`. El
   init.sh en verde ya consta en las Evidencias y yo lo he repetido arriba.
3. **`progress/current.md`**: en «Lo siguiente», la lista de orden nombra
   **F-050 dos veces** (quitar la segunda, tras F-054). Y «T1-T15
   (`1f0a425`..`e182915`)» arranca en el commit de T6: el rango real es
   `686d00a`..`e182915`.

## Observaciones (no bloquean; que el líder las lleve al humano)

- **Tiempo del preflight de todo el periodo.** Cada petición al transfer
  (una por obra) añade una lectura del historial. M1 mide una sola lectura,
  y el registro general hace una por obra en la misma petición del front.
  Propongo añadir a T17 un punto (g) que cronometre «Registrar en Sigrid» de
  todo el mes, o que el humano decida por escrito dejarlo para F-055.
- Una omitida por R20 no tiene botón en el modal (R29 solo lo pide en las
  que se escriben) aunque su motivo dice «elige otra»: verlo en M2 (e).
- Postventa en R9: `proponer` casa con `origen.codigo` (Sigrid) y el
  preflight con `obra.codigo` (api). Hoy coinciden; si divergen, difieren.
- `impl_F-050.md`/`tasks.md` T16 aún dicen `<res.ide de GONZALEZ PANIAGUA>`.

## Automejora (propuesta, no aplicada)

En la casilla de campaña MANUAL (`CHECKPOINTS.md`, `reviewer.md`): «el texto
exacto no se trunca con “…”; si no cabe, los pares original → mutado se
versionan en `progress/` y la tabla los enlaza».
