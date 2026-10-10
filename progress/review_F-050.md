<!-- progress/review_F-050.md -->
Revisión incremental desde 5f66b9d (pasada 2) · `5f66b9d..d53a162`

# F-050 · Review

**Veredicto (pasada 2): APPROVED** (APROBADO): lo pedido en la pasada 1,
resuelto; T15b cumple R29 sin que el front decida qué partida vale.

**Rigor:** `critico`, declarado: RED, cobertura ≥ 80 %, mutación con cero
supervivientes sin justificación aceptada y MANUAL con comando exacto.

## Pasada 1 (resumen; revisión completa `82bf8d6..5f66b9d`)

CAMBIOS PEDIDOS, solo papeleo; código sin fallos bloqueantes. init.sh en
verde (raíz 418+1 skip, api 768, front 184, transfer 750; cobertura 341/341);
Python recalculado 19 ficheros / 854 líneas / 158 mutantes (campaña no
reejecutada: 1236,8 s); J04, J47 y J56 reproducidos; `con.ide = 1705036`
leído en Sigrid (solo lectura). Revisado a fondo y dado por bueno: límite de
servicio, R7, R20, R9, PUT `…/partida`, R14/F7, sin `overrides`, tests
anteriores solo de la lista cerrada, desviaciones 1-10, `azure-apps`
`edaa2b7`, MANUAL. Pedido: (1) texto exacto de J08, J28, J34, J37, J41, J43
y J51; (2) T19 `[x]`; (3) `current.md`: F-050 duplicada en «Lo siguiente» y
rango de commits. Observaciones: (g) en T17; omitida por R20 sin botón;
postventa en R9; `<res.ide …>` en T16. Texto íntegro:
`git show 493bf35:progress/review_F-050.md`.

## Pasada 2 · lo ejecutado por el reviewer

- Sin `.arnes_cache/suite_*.ok`, `bash harness/init.sh` tal cual y solo:
  código 0, **ENTORNO LISTO**, ningún `[KO]`. Raíz **418 passed, 1 skipped**
  (40,4 s), api **768** (43,5 s), front **187** (16,5 s), transfer **750**
  (7,3 s). `PUERTA COBERTURA` **100,0 % (341/341)**. `ruff` 237, igual.
- Python, recálculo puro en HEAD: **19 ficheros, 854 líneas, 158 mutantes**,
  idéntico; desde `f4cdb11` ningún `.py` de producción cambia.
- **RED de T15b reproducida**: los tests de HEAD contra el `app.js` de
  `1c78608`, en una copia del scratchpad: **2 failed, 1 passed** (el que pasa
  es el control «las demás omitidas siguen sin selector»), como el informe.
- **Mutantes JS reproducidos al pie de la letra** (copia aislada del front +
  las dos constantes del transfer; suite entera, 187 en verde sin mutar;
  `app.js` restaurado y comprobado): **K01 1, K04 2, K05 3, K09 5** fallos,
  los del informe. De las filas corregidas: **J08 1** (igual) y **J51 4** en
  `f4cdb11`, igual; en HEAD da 5, por el test nuevo de T15b que también abre
  el selector con el callback: coherente.
- `git status` limpio al acabar. Nada contra Azure ni Sigrid.

## Lo pedido en la pasada 1

1. [x] **Textos exactos**: J08, J37, J41, J51 enteros en la celda; J26, J28,
   J34, J43 con enlace al texto literal de varias líneas. J51 dice ya qué
   cambia (`repreflightPartida` → `null`). 2. [x] **T19** `[x]`.
3. [x] **`current.md`**: F-050 una sola vez en «Lo siguiente»; rango bien.
- Observaciones: (g) en la M2 de `current.md` (abajo, 1); postventa en R9 en
  «Hechos…»; T16 con `--recurso 1705036`.

## T15b (ampliación del 2026-10-10, R29 última frase)

- **Solo front** (`pintarModalPreflight`): `botonPartida(texto)` comparte
  botón, alta en `registro.lineas` (`a.registro_id`, `o.obra.ide`) y callback
  de re-preflight entre la acción a escribir y la omitida. La api reenvía el
  `motivo` del preflight sin tocarlo.
- **El front no decide qué vale.** Solo pinta el botón si el `motivo` que
  manda el transfer empieza por el texto de `MOTIVO_PARTIDA_NO_HOJA`
  (anclado con `^`), y la partida que enseña es la que nombra ese motivo
  (`linea.partida_cod or paride`, `registro_pipeline.py:401`). La validez la
  sigue decidiendo R20 en el transfer al repetir el preflight.
- **Contrato.** Los tests leen `MOTIVO_PARTIDA_NO_HOJA` y
  `MOTIVO_PARTIDA_PV_NO_HOJA` del propio transfer con `ast`: si el texto
  cambia allí, fallan aquí. Cubren: botón con la rechazada, su línea y la
  apertura del selector con callback; `paride` sin código y escapado HTML;
  postventa (otro motivo), sin motivo y motivo no inicial, sin botón.
- **Tests anteriores:** ninguno cambia; el diff de `*/tests/*` es solo
  `test_f050_modal_registro.py` (+3).
- **MANUAL:** T17 (e) añade el caso R20 (PUT desde la consola, **solo base
  local**; `app.js` no es módulo) y «Cancelar, sin Registrar».

## Checkpoints (lo que toca el delta)

- **C1** [x] init.sh código 0, sin caché · [x] ficheros base.
- **C2** [x] una `in_progress` · [x] rama de F-050 · [x] `current.md` al día
  · [x] `history.md` (F-050 aún no está en `done`).
- **C3** [x] el front no lleva lógica de negocio (arriba) · [x] primera línea
  con la ruta · [x] sin `console.log` ni secretos ni dependencias.
- **C3 bis** N/A: el delta no toca `docs/referencia/`. **C4 ter** N/A: no
  existe `harness/rutas_sensibles.json`.
- **C4** [x] la ampliación de R29 tiene tres tests y están en verde · [x] sin
  red ni BBDD (node local) · [x] MANUAL con comando exacto (T17 e).
- **C4 bis**
  - [x] `rigor` declarado · [x] RED real de T15b, reproducida · [x]
    cobertura `[OK]` 100 % (341/341).
  - [x] Python: recalculado; campaña no reejecutada (1236,8 s según el
    informe) · [x] RM1: `f4cdb11`, sin `.py` de producción cambiado después.
  - [x] RM2: Python, igual que en la pasada 1. JS T15b: 11 en 122,9 s ≈
    11 s/mutante frente a ~15 s por mutante en mi reproducción: coherente.
  - [x] Sin «⚠ CAMPAÑA NO VÁLIDA»; «Sin veredicto (base rota)» = 0.
  - [x] RM5: N/A, ningún equivalente declarado · [x] RM6: no quita guardas.
  - [x] **Campaña MANUAL**: J01-J56 y K01-K11 con fichero:línea, texto
    exacto y nº de fallos; seis filas reproducidas (J08, J51, K01, K04, K05,
    K09).
  - [x] Cero supervivientes, sin `PENDIENTE` · [x] Evidencias con los cuatro
    números (T15b incluido) · [x] ningún N/A sin motivo.
- **C5** [x] T1-T15, T15b y T19 `[x]`; T15b con su commit `F-050 T15b:`
  (`6320474`); T16-T18 son MANUAL y en `critico` pueden quedar pendientes
  (como en F-039) · [x] sin artefactos · [x] `features.json` `in_progress`
  con la ampliación anotada.

## Cobertura requisito → test (`test_f050_*`)

| R | Test |
|---|---|
| R1-R5, R10 | `propuesta`: `r1_*`, `r2_*`, `r3_*`, `r4_*`, `r5_*`, `r10_*` |
| R6-R9, R11, R21 | `pipeline` `r7_*` `r9_*` `r21_*`; `endpoint_propuesta` `r8_*` `r9_*` `r11_*` |
| R12-R19 | `partida_linea`: `r12_*`-`r19_*`; `rutas_partida`: `r13_*`, `r17_*`, `r18_*` |
| R20 | `pipeline`: `r20_manual_que_no_es_hoja_activa_se_omite` (×6), `r20_ejecutar_no_escribe…` |
| R22-R28 | `subfilas`: `r22_*`-`r25_*`, `r28_*`; `selector`: `r26_*`, `r27_*` |
| R29 | `modal_registro`: `r29_*` (14) |
| R29 (amp.) | `modal_registro`: `r29_omitida_por_r20_lleva_el_selector…`, `…_sin_codigo_y_escapada`, `r29_las_demas_omitidas_siguen_sin_selector` |
| R30 | `test_f002_fuente_unica` (`regla-partida`), `test_f004_readme` |

## Cambios requeridos

Ninguno.

## Observaciones (no bloquean; que el líder las recoja, no «anotado»)

1. **(g) solo vive en `current.md`.** `tasks.md` T17 sigue diciendo
   «(a)-(f)» y su verificación «(a)-(f) en `impl_F-050.md`»: al cerrar,
   añadir (g) a T17 o el resultado de (g) se quedará sin sitio.
2. **El front reconoce la omitida por el TEXTO del motivo.** Hoy está
   blindado por el test de contrato (lee la constante del transfer), pero es
   texto para personas. Si otra omisión necesita botón, mejor un campo
   estructurado en la acción (p. ej. `motivo_codigo`) en el transfer, en una
   feature propia.
3. La tabla J se midió en `f4cdb11` (184 tests); en HEAD alguno sube
   (J51: 4 → 5) por los tests de T15b. Reproducir contra `f4cdb11`.

## Automejora (propuesta, no aplicada; sigue en pie)

En la casilla de campaña MANUAL (`CHECKPOINTS.md`, `reviewer.md`): «el texto
exacto no se trunca con “…”; si no cabe, va en una sección o fichero
enlazado; y la tabla dice contra qué SHA se contaron los fallos».
