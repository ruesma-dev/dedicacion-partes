<!-- progress/review_F-054.md -->
Revisión incremental desde 10bcf85 (pasada 6), HEAD `90c3e4f`; CHECKPOINTS entero sobre el estado actual.

# F-054 · Review 6

**Veredicto: APROBADO (APPROVED).** Los cuatro cambios de la pasada 5 están
hechos y el arreglo no mete nada nuevo. El código sigue aprobado en `9334fd3`;
el delta (`90c3e4f`, solo `progress/current.md`, +27/−28) no lo toca.

**Rigor:** `critico` (`features.json`): RED, cobertura, mutación con 0
supervivientes, RM5 y MANUAL con comando exacto.

## Delta revisado (`git diff 10bcf85..HEAD`)

- [x] **A** «Para retomar»: ya no dice «dos» pendientes. Las dos automejoras de
  la review 3 constan en encargos de `arnes-base`, sin decisión nueva. Lo
  comprobé contra `arnes-base`: `e7a172b` trae «P-1 · El operador `not` genera
  código inválido» y la solución (compilar y apartar). `de161b4` exige en la
  campaña manual «una fila por mutante (texto original y mutado…)». Remite a
  las demás pendientes y están donde dice: F-061 (l. 247), «⚠ Lo que espera
  al humano» (l. 547; «Trabajo del arnés tras F-055», l. 655) y «Hechos que no
  conviene volver a descubrir» (l. 742; «Dos defectos del arnés», l. 752).
- [x] **B** Fuera «último commit `5ba183c`».
- [x] **C** Sección de F-054: «después T10, T18 y T19, y T20 al desplegar».
- [x] **D** Review 1 «solo por `progress/current.md` (veredicto en
  `progress/review_F-054.md`)».
- [x] F-044: el título dice «cerrada y desplegada el 2026-10-27» y el
  implementer, «ya terminado». La remisión de l. 55 («F-044 · spec aprobada»,
  más abajo) sigue encontrando la sección.
- [x] **Nada nuevo.** Cabecera: «Reviews 3, 4 y 5 … solo por este fichero»
  (aquí «este fichero» sí es `current.md`), «en review 6». «Siguiente» y
  «Hoy»: review 6. Intactos: T1-T22, D1-D19 con D19 = b y sus dos decisiones,
  MANUAL T10, T18-T20 con su comando y `azure-apps` pendiente (T20).

## Checkpoints

- **C1** [x] `init.sh` (`suite_*.ok` borrados) código 0, sin `[KO]`, cobertura `[OK]` 99,5 % (755/759), tamaño dentro · [x] ficheros.
- **C2** [x] una `in_progress` · [x] rama `feature/F-054-sync-trae-porcentajes`
  (con `git -C`) · [x] `current.md` coherente con F-054 (relectura entera de la
  pasada 5 más este delta) · [x] history.
- **C3** [x] hexagonal, primera línea, sin `print`/secretos, escala,
  postventa, solo escribe el transfer: sin cambios desde la pasada 3.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] trazables (D19 → `test_f054_d19_*`) · [x] sin red ni BBDD ·
  [x] MANUAL con comando exacto en `current.md` (T10, T18, T19, T20).
- **C4 bis** [x] como en la pasada 3 (abajo). RM1: `a781d25..HEAD` solo toca
  `progress/` y `tasks.md`, así que la campaña 266/266 y el RM4 8/8 siguen valiendo.
- **C4 ter** N/A: sin `harness/rutas_sensibles.json`.
- **C5** [x] tareas no MANUAL `[x]` y commits `F-054 Tn:` · T10, T18-T20 `[ ]`
  por MANUAL, legítimo (rigor `critico`) · [x] árbol limpio · [x] `in_progress`.

## Cambios requeridos

Ninguno. Para cerrar faltan las MANUAL T10, T18 y T19 (resultado en
`progress/manual_F-054.md`) y T20 al desplegar (`azure-apps/dedicacion.md` y
aviso a `partes`). **R37 sin cifra** hasta T10 y T19: si pasa del 15 %, PARA.

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

Suites: api 1469, transfer 1865, front 489, raíz 418 (1 skipped).

## Automejora (review 3; ya en los encargos `e7a172b` y `de161b4` de `arnes-base`)

- **Generador de mutantes** (ya es encargo `e7a172b` de `arnes-base`): el operador `not` sobre una expresión entre
  paréntesis quita `not (` y deja el `)` (`reglas_porcentajes.py:563` →
  `if 0.0 < porcentaje <= 1.0):`; también l. 293). Un mutante que no compila
  muere siempre: es una muerte falsa. En F-054, ninguno (`ast.parse` sobre los
  266). Que `generar_mutantes` descarte lo que no parsea. Para `arnes-base`.
- **C4 bis, campaña manual**: decidir si una fila que quita un solo elemento
  nombrado (`sin **resuelta`) vale como «texto exacto». Hoy no se distingue.

## Reviews 1, 2, 4 y 5, resumen

- **Review 5** (`10bcf85`, desde `167c63f`): **CAMBIOS REQUERIDOS** solo por
  `current.md` (A-D: peticiones de arnés, commit obsoleto, T20, referencia).
- **Review 4** (`167c63f`, desde `f01d4f2`): **CAMBIOS REQUERIDOS** solo por
  `current.md` («ninguna» petición de arnés y la 2.ª propuesta sin recoger).
- **Review 2** (`0ddba84`, desde `e005e34`): **APROBADA**. O1, O2, O4 y O5
  con test; O3 y O6 aceptadas; mutación 266/266 en `c70eb61`; dejó O7 → D19.
- **Review 1** (completa, `560c10a`): **RECHAZADA** solo por el rastro; parte
  B sin bloqueos (solo `UPDATE … can = 0, tot = 0`, sin `DELETE`); 262/262.
  Detalle de cada una: `git show <sha>:progress/review_F-054.md`.
