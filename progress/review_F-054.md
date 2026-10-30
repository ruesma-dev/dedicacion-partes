<!-- progress/review_F-054.md -->
Revisión incremental desde 0ddba84 (pasada 3), HEAD `9334fd3`; CHECKPOINTS entero sobre el estado actual.

# F-054 · Review 3

**Veredicto: CAMBIOS REQUERIDOS (CHANGES_REQUESTED), solo por el rastro.**
El código de T22 (D19) es correcto, con tests, RED, consumidores verificados
uno a uno y RM4 reproducido 8/8. Bloquea una línea obsoleta de `current.md` (C2).

**Rigor:** `critico`, declarado en `features.json`. Exige RED, cobertura,
mutación completa con 0 supervivientes, RM5 y MANUAL con comando exacto.

## Delta revisado (`git diff 0ddba84..HEAD`, 12 ficheros)

- **Código** (`reglas_porcentajes.py:528-573`): `omitir(motivo, **resuelta)`;
  `resuelta = {destino, paride, partida_cod}` se fija tras P5 y va solo en los
  cuatro `omitir` posteriores (sin recurso, % no numérico, fuera de rango, sin
  `M*`). Los anteriores (empresa, motivo de empresa, P5 off, partida sin
  resolver) siguen con los valores por defecto. `base` no lleva esas claves:
  no hay `TypeError` por clave duplicada. `escribir` sin cambios. Coincide con
  T22 y design §6.1.
- **Tests** `test_f054_obra_cero.py -k d19` (14) y
  `test_f054_d19_modal_destino_*` (front): cada motivo posterior → `postventa`/33/`P33`;
  cada anterior y la no `Postv-` → `obra`/0/`None`; `sobrantes` (la otra
  partida sí, la suya no; la omitida antes, ninguna); la respuesta HTTP con
  clave `|70001` y el vinculado `postventa`/0; el modal `Postventa`×2/`Obra`×2.
  RED real en `impl_F-054.md` (`6 failed, 8 passed`; respuesta `1 failed`).
- **D19 coherente** en requirements (cabecera, §5 R31, §6), design (§3, §6.1,
  §10, §12), tasks (cabecera, T22), `ARCHITECTURE.md#regla-obra-cero` (texto y
  firma), `spec_F-054.md` e `impl_F-054.md` (frase de T22 (5) corregida, l. 83).
  **Salvo `current.md`** (cambio requerido 1).
- **Consumidores, lector por lector contra el código** (grep de `.destino`,
  `.paride`, `.partida_cod` en los tres servicios):
  `registro_pipeline.py` `normales`/`validas` (647, 651) y el bucle de partida
  (666) filtran `escribir`; `obra_de` (764, 1136, 1413) solo sobre `escribir`,
  `vin_escribir`, `pendientes`; `clave_conflicto` (910) sobre `grupo` ⊂
  `pendientes`; `omitidas` (1142) solo `registro_id` y `motivo`.
  `registro_vinculados.py:245` construye `PartidaTitular` también con la
  omitida, pero solo la usa `_partida` tras `av.accion == "escribir"` (252).
  `reglas_vinculados.py:368` copia `destino` y no `paride` (asimetría aceptada).
  `registro_lote.py`: no los lee. `app.py:365` publica `asdict(a)` y la clave
  (aceptado). api `_guardar_propuestas` (`registro_sigrid.py:447`) exige
  `paride` y método de propuesta: la omitida lleva `partida_metodo=None`.
  `app.js` 3510/3549 pintan Destino (aceptado); la celda Partida de una
  omitida solo pinta el motivo (3537-3544, 3493), y `.clave` de acción no la
  lee el front (solo la de conflicto). `prueba_escritura_porcentajes.py:312`
  (aceptado). **Ningún lector fuera de lo aceptado cambia.**

## Checkpoints

- **C1** [x] `init.sh` (`suite_*.ok` borrados) código 0, sin `[KO]`; antes, dos
  `[KO]` por el borrador de ESTE informe (145 líneas, y un falso positivo
  de credencial de `test_f008_r21` por una palabra), corregidos · [x] ficheros.
- **C2** [x] una `in_progress` · [x] rama (comprobada con `git -C`) ·
  **[ ] `current.md`**: l. 61-62 dice «(T1-T21), todas las decisiones cerradas
  (D1-D18; las últimas, D16 = C, D17 = A y D18 = A …)»; hoy son T1-T22 y
  D1-D19 (D19 = b, 2026-10-30). El resto de la sección y la cabecera sí lo
  recogen: queda una contradicción dentro del propio fichero · [x] history.
- **C3** [x] hexagonal · [x] primera línea · [x] sin `print`/TODO/secretos ·
  [x] escala intacta · [x] postventa: la omitida no se escribe, solo cambia su
  cobertura · [x] solo escribe el transfer; nada cambia en lo que se escribe.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] trazables (D19 → `test_f054_d19_*`) · [x] sin red ni BBDD
  (`ClienteFalso`, node con dobles) · [x] MANUAL con comando exacto (T10, T18-T20).
- **C4 bis** [x] rigor declarado · [x] RED de T22 pegado · [x] cobertura
  `[OK]` 99,5 % (755/759) · [x] **totales recalculados** con `alcance_de_feature` y
  `generar_mutantes`: 22 ficheros, 1651 líneas, **266 mutantes**, coinciden ·
  [x] sin «CAMPAÑA NO VÁLIDA», sin veredicto 0 · [x] **campaña no
  reejecutada: 3696 s según el informe** · [x] coste por mutante 3696 × 4 /
  266 = 55,6 s · [x] 0 supervivientes · [x] Evidencias con los cuatro números y workers.
- **RM1** [x] SHA `a781d25…`; `a781d25..HEAD` solo toca `progress/` y `tasks.md`.
  **RM2** [x] 266 × 13,9 = 3697 ≈ 3696 s; 13,9 × 4 = 55,6 s frente a bases de
  66-105 s, coherente con `-x`. **RM3** [x] ningún equivalente. **RM5** N/A:
  ningún equivalente declarado. **RM6** [x] no se quitó ninguna guarda.
- **Cero mutantes en `reglas_porcentajes.py`** [x] legítimo. Sus 12 líneas en
  alcance (528-532, 552-553, 556, 562, 564-565, 573) son `def omitir`, el
  `dict` y los `**resuelta`: ningún operador del generador (comparación,
  entero, booleano, lógico, `not`, aritmético) tiene objetivo ahí. Prueba de
  control: el mismo fichero sin exclusión de alcance da **70** mutantes; el
  generador funciona y el cero es por diseño.
- **RM4 manual** [x] la tabla trae una fila por mutante con su número de
  fallos; reproducidas **las 8**, copia `git archive HEAD` en el scratchpad,
  base `40 passed`: `omitir` sin `**resuelta` 7; sin recurso 1; % no numérico
  1; fuera de rango 4; sin `M*` 2; `destino="obra"` 6; `paride=0` 7;
  `partida_cod=None` 6. Coinciden fila por fila. La tabla describe el cambio
  con palabras, pero cada fila quita o fija un único elemento; reproducible sin
  ambigüedad, se acepta (ver automejora).
- **C4 ter** N/A: sin `harness/rutas_sensibles.json`.
- **C5** [x] T22 `[x]`, commits `F-054 T22:` · T10, T18-T20 `[ ]` por MANUAL,
  legítimo · [x] árbol limpio · [x] `in_progress`.

## Cobertura

| Requisito | Test o verificación |
|---|---|
| R1-R3 | `test_f054_r1_*` (front), `r2`, `r3`; O5: `test_f054_o5_*` |
| R4-R12 | `test_f054_lectura_mensuales`, `endpoint`, `traduccion` |
| R13-R18 | `test_f054_comparar` (R16 con `0.50` y `1.00`) |
| R19-R28 | `test_f054_aceptar`, `rutas`, `traer_front` |
| R29 | `test_f002_fuente_unica` y grep; `azure-apps`, T20 |
| R30, R37 | MANUAL T10, T18, T19 |
| R31 (D19), R32-R34, R38 | `test_f054_obra_cero` (`r31_o2_*`, `d19_*`), `modal_cero` (`d19_*`) |
| R35-R36 | `test_f054_poner_a_cero`, `registro_cero`, `modal_cero` (`r35_o5_*`) |

Suites: api 1469, transfer 1865, front 489, raíz 418 (1 skipped). **R37 sin cifra** hasta T10/T19.

## Cambios requeridos

1. `progress/current.md` l. 61-62 (sección «F-054 · en review»): «(T1-T21)»
   → «(T1-T22)» y «D1-D18; las últimas, D16 = C, D17 = A y D18 = A, el
   2026-10-29» → D1-D19 con D19 = b del 2026-10-30. Antes, `grep -n "D1-D18\|T1-T21\|D16-D18"`
   en `current.md`: es el cuarto sitio de una decisión que se cierra.

Pasada 4: ese delta más `init.sh`; el código de T22 queda aprobado en `9334fd3`.

## Automejora (propuesta, no aplicada)

- **Generador de mutantes**: el operador `not` sobre una expresión entre
  paréntesis quita `not (` y deja el `)` (p. ej. `reglas_porcentajes.py:563`
  → `if 0.0 < porcentaje <= 1.0):`; también l. 293). Un mutante que no
  compila muere siempre: es una muerte falsa. En el alcance de F-054 no hay
  ninguno (comprobado con `ast.parse` sobre los 266), pero conviene que
  `generar_mutantes` descarte lo que no parsea. Para `arnes-base`.
- **C4 bis, campaña manual**: decidir si una fila que quita un solo elemento
  nombrado (`sin **resuelta`) vale como «texto exacto». Hoy no se distingue.

## Review 2 (`0ddba84`, incremental desde `e005e34`): APROBADA, resumen

Bloqueos de la review 1 corregidos; O1, O2, O4 y O5 con test, O3 y O6
aceptadas. Mutación 266/266 en `c70eb61` (4837 s), `app.js` 69 + 14. Dejó
**O7** (toda `Postv-` omitida cubría todas): el humano eligió (b) → D19 y
T22, revisadas aquí. Detalle: `git show 0ddba84:progress/review_F-054.md`.

## Review 1 (pasada completa, `560c10a`): RECHAZADA, resumen

Solo por el rastro (C4 MANUAL sin comando; C2 sección obsoleta). Sin bloqueos
en la parte B (guarda doble, solo `UPDATE … can = 0, tot = 0`, sin `DELETE`)
ni en las desviaciones 1, 6, 13, 14 y 16. Campaña 1 262/262 en `c614be3`.
Detalle: `git show e005e34:progress/review_F-054.md`.
