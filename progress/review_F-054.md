<!-- progress/review_F-054.md -->
Revisión incremental desde f01d4f2 (pasada 4), HEAD `56c0078`; CHECKPOINTS entero sobre el estado actual.

# F-054 · Review 4

**Veredicto: CAMBIOS REQUERIDOS (CHANGES_REQUESTED), solo por el rastro.**
El bloqueo de la review 3 está corregido, pero el arreglo deja otra
contradicción dentro de `current.md` (C2). El código sigue aprobado en `9334fd3`
y el delta no lo toca.

**Rigor:** `critico`, declarado en `features.json`. Exige RED, cobertura,
mutación completa con 0 supervivientes, RM5 y MANUAL con comando exacto.

## Delta revisado (`git diff f01d4f2..HEAD`: `976eb29`, `56c0078`)

Solo `progress/current.md` (+18/−9); no toca código, spec, tests ni el
alcance de la campaña, así que no invalida nada de lo aprobado.

- [x] **Bloqueo de la review 3 resuelto**: la línea «Spec» dice (T1-T22) y
  D1-D19, con D19 = b del 2026-10-30, el efecto en el modal aceptado y el
  vinculado omitido «Dejarlo así». `grep "T1-T21\|D1-D18"`: nada.
- [x] Cabecera: implementación con T22, review 3 con su motivo, «en review 4».
  «Siguiente» y «Hoy (2026-10-30)»: review 4. Sección F-054: review 3
  resumida y review 4 lanzada; MANUAL T10, T18-T20 con su comando, intactas.
- [ ] **Nueva contradicción** (l. 56-57, «Para retomar»): «Peticiones de arnés
  pendientes de decisión: **ninguna** (la de C4 bis, al encargo `de161b4`)».
  En el mismo fichero, l. 96-101, se anota como «a decidir por el humano» la
  propuesta del operador `not`. Quien retome una sesión nueva lee «ninguna».
- [ ] **Una propuesta de la review 3 no está recogida**: de las dos de
  «Automejora» (abajo), `current.md` lleva la del operador `not` y no la de
  C4 bis (si una fila de campaña manual que quita un solo elemento nombrado
  vale como «texto exacto»). Hay que anotarla como pendiente o decir que se descarta.

## Checkpoints

- **C1** [x] `init.sh` (`suite_*.ok` borrados) código 0, sin `[KO]`, cobertura `[OK]` 99,5 %, tamaño 127/140 · [x] ficheros.
- **C2** [x] una `in_progress` · [x] rama `feature/F-054-sync-trae-porcentajes`
  (con `git -C`) · **[ ] `current.md`**: ver las dos casillas de arriba · [x] history.
- **C3** [x] sin cambios desde la pasada 3 (el delta no toca código).
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] trazables · [x] sin red ni BBDD · [x] MANUAL con comando exacto
  en `current.md` (T10 `worktree add … ccad4db`; T18 el `curl` de
  `existentes`; T19 `prueba_escritura_porcentajes.py estado --ano 2026 --mes
  11`; T20 `git -C … log -1 -- dedicacion.md`), sin cambios.
- **C4 bis** [x] todo como en la pasada 3 (abajo): el delta no toca ningún
  fichero del alcance, así que la campaña de `a781d25` y el RM4 siguen valiendo
  (RM1: `a781d25..HEAD` solo toca `progress/` y `tasks.md`).
- **C4 ter** N/A: sin `harness/rutas_sensibles.json`.
- **C5** [x] tareas no MANUAL `[x]` · T10, T18-T20 `[ ]` por MANUAL, legítimo ·
  [x] árbol limpio · [x] `in_progress`.

## Cambios requeridos

1. `progress/current.md` l. 56-57: cambiar «Peticiones de arnés pendientes de
   decisión: ninguna (…)» para que diga las que hay. Hoy son las dos de la
   review 3: el operador `not` de `harness/mutacion` y la del «texto exacto»
   de la campaña manual en C4 bis. Mantener la nota de C4 bis de `de161b4`
   si sigue siendo cierta. O, si el líder descarta la segunda, decirlo ahí
   mismo. Antes, `grep -n "arnés\|ninguna"` en `current.md`: que no quede
   ninguna otra línea que diga lo contrario.

Pasada 5: ese delta más `init.sh`.

## Review 3 (`f01d4f2`, incremental desde `0ddba84`): CAMBIOS REQUERIDOS, resumen

Solo por `current.md` (línea «Spec» con T1-T21 y D1-D18; corregido en `976eb29`).
**Código de T22 (D19) aprobado** en `9334fd3`:

- `reglas_porcentajes.py:528-573`: `omitir(motivo, **resuelta)`. Los cuatro
  `omitir` de después de P5 llevan `destino`/`paride`/`partida_cod`; los de
  antes y las no `Postv-`, `obra`/0/`None`. Sin choque de claves con `base`.
- Tests `test_f054_*d19*` (transfer 14, respuesta HTTP 2, front 1) y RED real
  (`6 failed, 8 passed`; respuesta `1 failed`). D19 coherente en requirements,
  design §3/§6.1/§10/§12, tasks, `ARCHITECTURE.md#regla-obra-cero`,
  `spec_F-054.md` e `impl_F-054.md`.
- **Consumidores**, contra el código: `registro_pipeline.py` (647, 651, 666,
  764, 910, 1136, 1142, 1413) solo sobre `escribir`; `PartidaTitular`
  (`registro_vinculados.py:245`) solo lo usa `_partida` con `escribir`;
  `registro_lote.py` no los lee; api `_guardar_propuestas` exige método de
  propuesta; `app.js` solo cambia Destino (aceptado). Nada fuera de lo aceptado.
- **Mutación**: recálculo de 22 ficheros, 1651 líneas y **266 mutantes**,
  coincide. Campaña no reejecutada: 3696 s según el informe. RM2 66-105 s de
  base contra 13,9 × 4 = 55,6 s, coherente con `-x`. 0 supervivientes. RM3, RM6
  [x], RM5 N/A (sin equivalentes). Cobertura `[OK]` 99,5 % (755/759).
- **Cero mutantes en `reglas_porcentajes.py`, legítimo**: sus 12 líneas en
  alcance no tienen ningún objetivo de operador. Control sin exclusión de
  alcance: 70 mutantes en el fichero.
- **RM4 manual reproducido 8/8** (copia `git archive` en el scratchpad, base 40
  passed): sin `**resuelta` en `omitir` 7 fallos; sin recurso 1; % no numérico 1;
  fuera de rango 4; sin `M*` 2; `destino="obra"` 6; `paride=0` 7;
  `partida_cod=None` 6. Coinciden con la tabla.

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

## Automejora (review 3; propuesta, no aplicada)

- **Generador de mutantes**: el operador `not` sobre una expresión entre
  paréntesis quita `not (` y deja el `)` (`reglas_porcentajes.py:563` →
  `if 0.0 < porcentaje <= 1.0):`; también l. 293). Un mutante que no compila
  muere siempre: es una muerte falsa. En F-054, ninguno (`ast.parse` sobre los
  266). Que `generar_mutantes` descarte lo que no parsea. Para `arnes-base`.
- **C4 bis, campaña manual**: decidir si una fila que quita un solo elemento
  nombrado (`sin **resuelta`) vale como «texto exacto». Hoy no se distingue.

## Reviews 1 y 2, resumen

- **Review 2** (`0ddba84`, incremental desde `e005e34`): **APROBADA**.
  Bloqueos de la 1 corregidos. O1, O2, O4 y O5 recogidas con test; O3 y O6
  aceptadas. Mutación 266/266 en `c70eb61`; `app.js` 69 + 14. Dejó O7 →
  D19/T22. Detalle: `git show 0ddba84:progress/review_F-054.md`.
- **Review 1** (completa, `560c10a`): **RECHAZADA** solo por el rastro (C4
  MANUAL sin comando; C2 sección obsoleta). Sin bloqueos en la parte B (guarda
  doble, solo `UPDATE … can = 0, tot = 0`, sin `DELETE`). Campaña 1 262/262 en
  `c614be3`. Detalle: `git show e005e34:progress/review_F-054.md`.
