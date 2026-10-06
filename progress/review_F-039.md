<!-- progress/review_F-039.md -->
Revisión completa (pasada 1), diff de F-039 `f7cc4e9..3b531ac` (= `8a012d7..HEAD` sin los merges de dev)

# F-039 · Review (reviewer, 2026-10-06)

**Veredicto: CHANGES_REQUESTED**, solo por el rastro de `progress/current.md`.
El código, los tests, la mutación y los docs quedan dados por buenos hasta
`3b531ac`: la pasada 2 puede ser incremental y mirar solo `current.md`.

**Nivel de rigor:** `critico`, declarado en `features.json`. Exige RED,
cobertura ≥ 80 %, cero supervivientes y las MANUAL con su comando exacto.

## Lo verificado

- **`bash harness/init.sh`**: `ENTORNO LISTO`, exit 0. Raíz 418/1 skipped; api,
  front y transfer en verde; `PUERTA COBERTURA` 100 % (181/181); `PUERTA
  TAMAÑO` dentro.
- **Límite de servicio (1).** El universo VAR solo lo calcula el transfer
  (`universo_var.py`). El endpoint y el preflight comparten
  `cargar_catalogo_var` y `partida_var_de`. La api lo pide una vez en
  `preparar_obras`, la misma función para el step y el preview, y no conoce ni
  «VAR» ni «29». El front solo pinta `partida_metodo === "var"`, sin
  literales (hay test).
- **Registro VAR (2).** La rama VAR va antes del override. Se omiten con motivo
  y sin aviso de «sin partida»: la postventa (sin leer la VAR), la línea sin
  universo, la de otra obra y la partida fuera del universo. Si vale, `paride`
  queda fijo con `metodo var`, sin cascada P5. La cuenta sale del paso 4 bis en
  el centro de destino (test de ejecutar: `caaide` 91001; en pruebas, `0404`).
  En la api, `_payloads` agrupa por `registro_obra_ide`, manda `var_paride` y
  nunca el override.
- **6+ dígitos (3).** El filtro `[0-9]{n}` (sin filtro con `n<=0`) actúa antes
  de pedir ningún universo. Si la obra ya estaba guardada, `sincronizar` la deja
  sin `activa` ni `admite_postventa`, y sus líneas quedan no ofrecibles y se
  registran como hoy (D5).
- **Columnas e `ide` negativo (4).** Son nulables y sin default, solo en el ORM,
  y el ALTER lo deriva `esquema` (r18). Busqué `gt=0`, `PositiveInt` y `> 0`
  sobre el `ide` de obra en schemas, rutas, casos de uso y `app.js`: no hay
  ninguno. Las claves del front son `${obra_ide}|${pv}`. El FK no impone signo.
- **Tests anteriores (5).** `git diff f7cc4e9..HEAD -- '*tests*'` toca solo
  `conftest.UniversoFalso`, las `_fila` de f022, f024 y f026 (3 atributos a
  `None`) y `ANCLAS` de f002 (+2). Coincide con design §7.1 y con el informe §3,
  y ningún assert pierde exigencia. `test_f037_copias_partes.py` viene de dev.
- **Docs (7).** `ARCHITECTURE` tiene las reglas 17 y 18, la lista de anclas y la
  tabla `obra`. `INTEGRACION` tiene la cabecera, §3, §5 y §7, con el orden
  transfer → api → front. `azure-apps` `f01156f` es copia literal y su árbol
  está limpio. El README del transfer remite a la ancla.
- **Script.** `verif_f039_var.ps1` no menciona `ejecutar` y solo llama a
  `127.0.0.1`.

## Mutación (C4 bis, RM1-RM6)

- **Recálculo puro** (`harness.alcance` + `generar_mutantes`): 18 ficheros, 495
  líneas y **60 mutantes**, lo mismo que el informe. **No reejecuté la
  campaña**: según el informe tardó 1274,4 s, más de 60.
- **RM1.** Midió `6ab6588`. Después no cambió ningún fichero del alcance:
  `e69ff2a` solo retoca la forma de dos tests (`Decimal(30)` y unos
  paréntesis), y `sigrid_write_client.py` viene de dev y queda fuera del
  alcance (merge-base `f7cc4e9`).
- **RM2.** 1 worker con media de 21,2 s: 60 × 21,2 = 1272 s, que cuadra. Las
  líneas base (api 37,8 s, transfer 14,0 s) no dan ningún salto.
- **RM3.** Repasé los 60: ningún muerto es equivalente. Cada `or→and`, `frozen`
  y default cambia algo observable y tiene un test que lo ve.
- **RM4.** Sobre una copia (`git archive`) en el scratchpad murieron todos:
  #47 `>=`→`>` (25 fallos), #52 `!=`→`==` (30), #2 `normal and not`→`or not`
  (13) y #17 default `0`→`1` (6). #2 y #17 eran supervivientes de la 1.ª.
- **`registro_sigrid.py`**: el generador no le saca mutantes, así que probé dos
  a mano y murieron los dos: `elif overrides`→`if` (1 fallo) y agrupar siempre
  por la obra propia (3).
- **RM5** N/A: no hay equivalentes declarados (0 supervivientes). **RM6** N/A:
  T11 solo añade tests. No sale «⚠ CAMPAÑA NO VÁLIDA» y «Sin veredicto» está a
  0. `git status` limpio.

## Checkpoints

- **C1** [x] init.sh con exit 0 · [x] ficheros base.
- **C2** [x] una sola `in_progress` · [x] la rama de F-039 · **[ ] `current.md`
  solo con la sesión activa**: tiene restos que se contradicen (cambio 1) ·
  [x] las `done` están en `history.md`.
- **C3** [x] hexagonal (`domain/obras.py`, `models` y `ports` puros; el cliente
  en infrastructure) · [x] primera línea con la ruta · [x] sin prints, TODOs,
  secretos ni dependencias nuevas · [x] las tres trampas: la escala va sobre 1
  (r20, 0,4); la postventa con `var_paride` se omite; solo escribe el
  transfer, con `synckey` y en modo pruebas (R8).
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] todo requisito con test (tabla) · [x] sin red ni BBDD · **[ ] las
  MANUAL con su comando exacto en `current.md`**: falta el arranque de los
  servicios (cambio 2).
- **C4 bis** [x] rigor declarado · [x] RED pegada (T1-T8, T11) · [x] cobertura
  100 % · [x] totales recalculados · [x] regla de los 60 s (no se reejecuta) ·
  [x] coste por mutante 21,2 s, mayor de 1 s · [x] sin cabecera de campaña no
  válida · [x] RM1 · [x] RM2 · N/A RM5 y RM6 (ver arriba) · N/A la campaña
  manual (la automática dio 60) · [x] 0 supervivientes · [x] «Evidencias» con
  los workers.
- **C4 ter** N/A: no hay `harness/rutas_sensibles.json`.
- **C5** [x] T1-T11 y T15 `[x]`, cada una con su commit `F-039 Tn:`; T9 es del
  líder (`f01156f`); T12-T14 son MANUAL pendientes del humano, legítimo en
  `critico` · [x] sin artefactos · [x] `features.json` en `in_progress`.

## Cobertura requisito → test (`test_f039_…`)

| R | Test | R | Test |
|---|---|---|---|
| R1 | `r1_*` (7, contrato de la ruta) | R13 | `r13_*` (8, repo incluido) |
| R2 | `r2_*` (29, 30, 100, 029, 29.1, 29A / 28, 05, CI) | R14 | `r14_*` (2) |
| R3 | `r3_*` (6) | R15 | `r15_la_entrada_que_sale_…_inactiva` |
| R4 | `r4_*` (422 sin leer, 502) | R16 | `r16_*` (8, sync sin commit, 502) |
| R5 | `r5_*`, `cruce_universo_y_preflight` | R17 | `r17_*` (4) |
| R6 | `r6_*` (4 casos) | R18 | `r18_*` (3) |
| R7 | `r7_el_paride_manual_no_cambia…` | R19 | `r19_*` (2) |
| R8 | `r8_*` (5) | R20 | `r20_*` (4) |
| R9 | `r9_*` (2) | R21 | `r21_*` (3) |
| R10 | `r10_*` (7) | R22 | front `r22_*` (3) |
| R11 | `r10_r11_…`, `r11_…_sin_marcas` | R23 | `test_f002_fuente_unica` (`ANCLAS`) |
| R12 | `r12_…_una_vez…` | R24 | documental, verificado leyendo `INTEGRACION` y `f01156f` |

## Cambios requeridos

1. **`progress/current.md`: podar lo que contradice el estado real**, en el
   orden de `BACKLOG.md`. l. 12 «Primera del backlog» (es la 4.ª); l. 42-43
   «F-040 … espera al humano con D1-D6» (l. 38-41: aprobada); l. 49-51
   «F-039 tercera. No hay F-041.» (F-041 existe, prioridad 3); l. 112-117
   «F-029 espera a desplegar» (desplegada el 2026-10-06), «Ahora **F-037**»
   (cerrada) y «**F-039** (spec lista)» (implementada, en review).
2. **`progress/current.md`, MANUAL T12-T14 (l. 22-35).** Añadir el arranque, que
   hoy falta: «`python main.py` con la `.venv` de cada servicio en
   `services/dedicacion-transfer` y `services/dedicacion-api` (la api con
   `PG_HOST=localhost`)». Para T14, además, «`python main.py` en
   `services/dedicacion-front` y abrir `http://127.0.0.1:8080`». Así lo tienen
   `tasks.md` y el informe §5.

## Observaciones (no bloquean; que el líder las recoja)

- `registro_sigrid.py` da 0 mutantes automáticos. Lo cubren los dos mutantes a
  mano de arriba. Es un posible hueco del generador para `arnes-base`, si el
  humano lo quiere.
- La 1.ª campaña dio por supervivientes a #2 y #17, que estaban muertos. Ya
  consta en el informe del implementer, para quien mantenga
  `harness/mutacion.py`.
