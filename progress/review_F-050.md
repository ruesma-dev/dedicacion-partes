<!-- progress/review_F-050.md -->
Revisión incremental desde d53a162 (pasada 3) · `d53a162..8e9e8de`

# F-050 · Review

**Veredicto (pasada 3): CHANGES_REQUESTED** (CAMBIOS PEDIDOS): un fallo real
en el repreflight por obra (punto 5), reproducido en node, y la verificación
de T17 sin el punto (h). El resto de T15c, bien.

**Rigor:** `critico`, declarado: RED, cobertura ≥ 80 %, mutación con cero
supervivientes sin justificación aceptada y MANUAL con comando exacto.

## Pasadas anteriores (resumen)

- **Pasada 1** (`82bf8d6..5f66b9d`, completa): CAMBIOS PEDIDOS, papeleo.
  Íntegra: `git show 493bf35:progress/review_F-050.md`.
- **Pasada 2** (`5f66b9d..d53a162`): APROBADA. Lo pedido, resuelto; T15b
  (selector en la omitida por R20) sin que el front decida qué partida vale;
  RED de T15b y K01/K04/K05/K09/J08/J51 reproducidos. Observaciones (g) en
  T17 y `motivo_codigo` → F-048: ambas recogidas (`6782567`, `features.json`).
  Texto íntegro: `git show 8e9e8de:progress/review_F-050.md`.

## Pasada 3 · lo ejecutado por el reviewer

- Sin `.arnes_cache/suite_*.ok`, `bash harness/init.sh` tal cual y solo:
  código 0, **ENTORNO LISTO**, ningún `[KO]` (`ruff` 237, el aviso de
  siempre). Raíz **418 passed, 1 skipped** (38,0 s), api **774** (30,4 s),
  front **218** (15,6 s), transfer **750** (5,0 s). `PUERTA COBERTURA`
  **100,0 % (343/343)**; `PUERTA TAMAÑO` en verde.
- **Python, recálculo puro en HEAD** (`harness.alcance` + `generar_mutantes`):
  **19 ficheros, 866 líneas, 160 mutantes**, idéntico al informe. Campaña no
  reejecutada: 1807,9 s según el informe. Los 2 mutantes nuevos
  (`registro_sigrid.py:139` `is not None`→`is None`, `:140` `==`→`!=`)
  ejecutados en copia aislada contra `test_f050_preflight_obra.py`: **4 y 3
  fallos**, muertos.
- **JS T15c, tres filas reproducidas al pie de la letra** (worktree aislado
  en el scratchpad, suite entera del front, 218 en verde sin mutar): **T44 1,
  T24 1, T31 4** fallos, los del informe. Worktree retirado; `git status`
  limpio. Nada contra Azure ni Sigrid.
- Escenario propio en node (harness `_flujo`, en el scratchpad): cambio 1.

## Lo que pedía el líder

- **`obra_ide` acota sin cambiar qué se escribe ni la forma.** Filtra los
  payloads ya construidos por `p["obra"]["ide"]` (la obra del grupo, la misma
  que el front guarda en `registro.lineas` desde `o.obra.ide`); la respuesta
  sigue siendo `{ok, obras, no_vigentes}`. `ejecutar` no recibe `obra_ide`
  (test de la ruta). El transfer no cambia. Una obra que no está:
  `{"ok": true, "obras": [], "no_vigentes": []}`, sin llamadas (test `999`).
- **Selector.** `selector.abierto` evita el segundo panel en la misma línea;
  `vivo` descarta la respuesta y el error de un panel cerrado o sustituido;
  el clic en su ancla no lo cierra. Correcto.
- **Modal.** Panel en `<body>` con `z-index` 70 > 60 (desde T11); `abrirModal`
  cierra cualquier selector, también uno cargando (test y T28).
- **CSS.** `.panel-tabla` ya tenía `overflow-x: auto`; los anchos ajustados
  no tocan `state.anchos` (test); F-042 cuelga de `<body>` y sigue en verde.
- **Tests anteriores que cambian:** solo
  `test_f049_a_el_preflight_repetido…` (lista cerrada, T12) y los cuatro de
  F-050 citados. Ninguno se relaja: los cinco **endurecen** lo esperado
  (cuerpo con `obra_ide: 694`, `despues(ctx.obraIde)`, `td` en la celda).
- **MANUAL M2 (h)** se puede seguir: cinco pasos con qué mirar en cada uno
  y «Cancelar, sin Registrar».

## Checkpoints (lo que toca el delta)

- **C1** [x] init.sh código 0, sin caché · [x] ficheros base.
- **C2** [x] una `in_progress` · [x] rama · [x] `current.md` al día (T15c,
  `azure-apps` `1037904`) · `history.md` N/A: F-050 aún no está `done`.
- **C3** [x] límite de servicio: api y front; transfer intacto · [x] el front
  no decide qué se escribe (`unirPreflight` solo compone lo que devuelve la
  api) · [x] primera línea con ruta · [x] sin `console.log` ni secretos.
- **C3 bis** N/A: el delta no toca `docs/referencia/`. **C4 ter** N/A: no
  existe `harness/rutas_sensibles.json`.
- **C4** [x] tests sin red ni BBDD (node local, dobles) · [ ] **un camino de
  error del punto 5 sin cubrir y roto** (cambio 1) · [ ] MANUAL: T17 dice
  «(a)-(g)» en su verificación (cambio 2).
- **C4 bis**
  - [x] `rigor` · [x] RED real por punto (impl 164-197) · [x] cobertura 100 %.
  - [x] Python recalculado (160) · [x] RM1: medido en `948ed7d`; después solo
    cambia una anotación de tipo en `registro_sigrid.py` (sin mutantes).
  - [x] RM2: 160 × 11,3 s ≈ 1808 s; media < base (26,2 s api) con 160/160
    muertos y `-x`: coherente.
  - [x] Sin «⚠ CAMPAÑA NO VÁLIDA»; «Sin veredicto (base rota)» = 0.
  - [x] RM5 N/A: ningún equivalente · [x] RM6: no quita guardas.
  - [x] Campaña MANUAL T15c: 46 filas con texto exacto, SHA (`d46b012`/
    `5d75623`) y fallos; T20 vivo → test → muerto; tres filas reproducidas.
  - [x] Cero supervivientes · [x] Evidencias con los cuatro números.
- **C5** [x] T15c `[x]` con ocho commits `F-050 T15c:` · [x] T16 hecha;
  T17-T18 MANUAL pendientes (como en F-039) · [x] sin artefactos.

## Cobertura requisito → test (`test_f050_*`)

| R | Test |
|---|---|
| R1-R21 | sin cambios desde la pasada 2 (`propuesta`, `pipeline`, `partida_linea`, `rutas_partida`, `endpoint_propuesta`) |
| R22-R28 | `subfilas` `r22_*`-`r25_*`, `r28_*`; `selector` `r26_*`, `r27_*` |
| R29 (+ amp.) | `modal_registro` `r29_*` |
| T15c 1-5 | `m2_arreglos` `m2_1_*`…`m2_5_*`; api `preflight_obra` `m2_5_*` (6) |
| R30 | `test_f002_fuente_unica`, `test_f004_readme` |

## Cambios requeridos

1. **«Registrar» se queda en «Analizando…» para siempre** si, con dos obras
   en vuelo, la segunda vuelve bien y la primera falla.
   `services/dedicacion-front/static/js/app.js:2081` guarda `btn` al empezar;
   la respuesta buena de la otra obra repinta el modal (botón nuevo, que se
   deja bloqueado porque queda una en vuelo) y el `catch` (`app.js:2101`)
   reactiva el botón **viejo**, ya fuera del DOM. Reproducido con el propio
   harness: `repreflightPartida(694); repreflightPartida(700);` → resolver la
   700 → rechazar la 694 → `{disabled: true, textContent: "Analizando…"}`
   (se esperaba «Registrar» activo). Es el caso de los 502 del punto 5; la
   única salida es Cancelar y reabrir (el mes entero). Arreglo: en el `catch`, buscar el botón de nuevo
   (`$("#btn-ejecutar-registro")`), como ya hace la rama buena. Test nuevo en
   `test_f050_m2_arreglos.py` con ese orden (RED con la salida real) y su
   mutante en `mutacion_manual_F-050.md`.
2. **`tasks.md` T17, verificación:** dice «(a)-(g) en
   `progress/impl_F-050.md`»; el texto ya tiene (h). Poner «(a)-(h)» (es la
   misma observación de la pasada 2 con (g); que no se repita al añadir
   puntos).

## Observaciones (no bloquean; que el líder las recoja, no «anotado»)

1. **La manija de ancho con la tabla encogida** guarda como preferencia el
   ancho AJUSTADO más el arrastre (`montarManijaAncho`: `inicioW =
   th.offsetWidth`), y durante el arrastre la columna crece menos que el
   ratón porque se reparte. Funciona; si molesta, partir de
   `state.anchos[clave]` en vez de `offsetWidth`. Comprobarlo en la M2 (h) 1.
2. **`obra_ide` no se valida en la ruta** (`routes.py:378`, viene crudo del
   cuerpo): un `"694"` de texto no casa con el `int` y devuelve `obras: []`,
   y el front quitaría esa obra del modal. Hoy el front manda un número;
   `int(...)` como con `overrides` lo blindaría.
3. `unirPreflight` deja el `ok` de arriba del primer análisis; hoy nadie lo
   lee. Si se llega a leer, recalcularlo.

## Automejora (propuesta, no aplicada; sigue en pie)

Casilla MANUAL: texto exacto sin truncar y SHA de la tabla (pasada 2, en
pie). Nueva: con peticiones concurrentes en el front, un test por **orden de
llegada** (A antes que B y al revés, con éxito y con error); el cambio 1 se
escapó por probar solo un orden del error.
