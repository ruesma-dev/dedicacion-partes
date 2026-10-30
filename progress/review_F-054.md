<!-- progress/review_F-054.md -->
Revisión incremental desde 167c63f (pasada 5), HEAD `dd9a471`; `current.md` releído entero (761 líneas); CHECKPOINTS entero.

# F-054 · Review 5

**Veredicto: CAMBIOS REQUERIDOS (CHANGES_REQUESTED), solo por el rastro.**
El bloqueo de la pasada 4 está corregido tal como lo pedí. Pero mi petición
estaba mal medida: «son las dos de la review 3» no miraba el resto del
fichero. Esta vez está la lista **completa** (abajo). Código aprobado en
`9334fd3`; el delta (`dd9a471`, solo `current.md`) no lo toca.

**Rigor:** `critico` (`features.json`): RED, cobertura, mutación con 0
supervivientes, RM5 y MANUAL con comando exacto.

## Delta y relectura entera de `current.md`

- [x] Bloqueo de la pasada 4: «Para retomar» y la sección de F-054 nombran las
  dos propuestas de la review 3; cabecera, «Siguiente» y «Hoy»: review 5.
- [x] Sin cambios: T1-T22 y D1-D19 con D19 = b y sus dos decisiones; MANUAL
  T10, T18-T20 con su comando; `azure-apps` pendiente (T20); límite de servicio.
- [ ] **A. «Peticiones de arnés pendientes de decisión: dos» (l. 58-62) no es
  verdad.** (1) La del operador `not` **ya es un encargo** de `arnes-base`:
  `e7a172b` «mutantes que no compilan cuentan como muertos» (origen
  datamart-seg-anual F-148). No es una decisión nueva, es un segundo origen
  del mismo encargo. (2) La del «texto exacto» cae en el tema del encargo
  `de161b4` (C4 bis, campaña manual). (3) El mismo fichero trae más
  propuestas de arnés **pendientes**: l. 248-251 (F-061, «pendiente de PARADA 1
  con el humano, no aplicada»), l. 656-677 («Trabajo del arnés tras F-055 (…
  a proponer)», con F-056, F-057 y F-062) y l. 753-756 («Dos defectos del
  arnés, anotados para `arnes-base`»). Lo de «dos» contradice las tres.
- [ ] **B. l. 14-15: «último commit `5ba183c`»**, y hoy es `dd9a471`. Si es
  historia (el último de la ronda de O1-O5), hay que decirlo. Si no, sobra.
- [ ] **C. l. 103: «después T10/T18/T19»** deja fuera T20 (despliegue,
  `azure-apps`, aviso a `partes`), que la cabecera (l. 25-28) sí lista.
- [ ] **D. l. 78-79: «Review 1 RECHAZADA solo por este fichero
  (`progress/review_F-054.md`)»**: «este fichero» es `current.md` y el
  paréntesis nombra otro. Quien lo lea entiende que la culpa fue del informe de review.
- Resto que no toca a F-054 (no bloquea esta feature; lo dejo dicho para que
  no vuelva luego como bloqueo): la sección «F-044 · spec aprobada
  (2026-10-25)» (l. 201-227) habla de «implementer lanzado», pero F-044 está
  cerrada y desplegada (l. 45-48). Se puede retitular o resumir.
  Fuera de esto, en las 761 líneas no hay otra incoherencia con el estado de F-054.

## Checkpoints

- **C1** [x] `init.sh` (`suite_*.ok` borrados) código 0, sin `[KO]`, cobertura `[OK]` 99,5 %, tamaño en tope · [x] ficheros.
- **C2** [x] una `in_progress` · [x] rama (`git -C`) · **[ ] `current.md`**:
  A-D · [x] history.
- **C3** [x] sin cambios desde la pasada 3. **C3 bis** N/A: sin `docs/referencia/`.
- **C4** [x] trazables · [x] sin red ni BBDD · [x] MANUAL con comando exacto.
- **C4 bis** [x] como en la pasada 3: `a781d25..HEAD` solo toca `progress/` y
  `tasks.md`, así que la campaña y el RM4 siguen valiendo. **C4 ter** N/A: sin
  `rutas_sensibles.json`.
- **C5** [x] tareas no MANUAL `[x]` · T10, T18-T20 `[ ]` por MANUAL · [x]
  árbol limpio · [x] `in_progress`.

## Cambios requeridos (todos en `progress/current.md`)

1. l. 58-62: quitar el «dos». Decir que la del `not` es un segundo origen del
   encargo `e7a172b` y que la del «texto exacto» se suma a `de161b4`, o que
   queda como decisión nueva. Y remitir a las demás pendientes (l. 248, 656,
   753), o retirar las que ya estén en `arnes-base`.
2. l. 14-15: quitar «último commit `5ba183c`» o fecharlo como historia.
3. l. 103: «después T10/T18/T19» → T10, T18-T20.
4. l. 78-79: «solo por este fichero (`progress/review_F-054.md`)» → por
   `current.md` (informe en `progress/review_F-054.md`).

Pasada 6: ese delta más `init.sh`. No pediré nada fuera de esta lista salvo
que el arreglo introduzca algo nuevo.

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

- **Generador de mutantes** (ya es encargo `e7a172b` de `arnes-base`): el operador `not` sobre una expresión entre
  paréntesis quita `not (` y deja el `)` (`reglas_porcentajes.py:563` →
  `if 0.0 < porcentaje <= 1.0):`; también l. 293). Un mutante que no compila
  muere siempre: es una muerte falsa. En F-054, ninguno (`ast.parse` sobre los
  266). Que `generar_mutantes` descarte lo que no parsea. Para `arnes-base`.
- **C4 bis, campaña manual**: decidir si una fila que quita un solo elemento
  nombrado (`sin **resuelta`) vale como «texto exacto». Hoy no se distingue.

## Reviews 1, 2 y 4, resumen

- **Review 4** (`167c63f`, desde `f01d4f2`): **CAMBIOS REQUERIDOS** solo por
  `current.md` («ninguna» petición de arnés y la 2.ª propuesta sin recoger).
- **Review 2** (`0ddba84`, desde `e005e34`): **APROBADA**. O1, O2, O4 y O5
  con test; O3 y O6 aceptadas; mutación 266/266 en `c70eb61`; dejó O7 → D19.
- **Review 1** (completa, `560c10a`): **RECHAZADA** solo por el rastro; parte
  B sin bloqueos (solo `UPDATE … can = 0, tot = 0`, sin `DELETE`); 262/262.
  Detalle de cada una: `git show <sha>:progress/review_F-054.md`.
