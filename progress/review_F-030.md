Revisión incremental desde 8d9eca8 (pasada 2) · `git diff 8d9eca8..HEAD`, HEAD `0e80f92`
<!-- progress/review_F-030.md -->
# F-030 · Review (pasada 2)

**Veredicto: RECHAZADO (CHANGES_REQUESTED), solo por papeleo.** La obs. 1
queda resuelta de punta a punta y el código del anexo está bien. Fallan dos
casillas: C2 (`current.md` da por no probado lo que T20 ya probó y calla
lo que deja sin probar la segunda mitad) y C4 (R48, sin test con su nombre).
Ningún arreglo toca producción: la 5.ª campaña sigue valiendo (RM1).

**Rigor:** `critico`, declarado. Exige RED, cobertura, mutación con 0
supervivientes y MANUAL con su comando exacto y su resultado real.

## Lo que se ha ejecutado

- **`bash harness/init.sh`** tal cual, con las cachés `suite_*.ok`
  borradas: **ENTORNO LISTO**, 0 `[KO]`.
  - Suites: raíz 418 (+1 skipped), api 1125, front 359, transfer 1224.
  - COBERTURA 99,9 % (831/832) y TAMAÑO, los dos `[OK]`.
  - Ruff, 277 como `dev`: en los 6 ficheros de producción que más toca el
    anexo, ningún aviso nuevo.
- **Mutación, recálculo puro** (`alcance_de_feature` + `generar_mutantes`
  sobre HEAD): 23 ficheros, 1997 líneas y **405 mutantes**, como el informe.
  El timeout (`reglas_incidencias.py:247`) y los de la 4.ª campaña (`:149`,
  `:171`, `:274`) existen tal cual.
  - No reejecutada: 1626,6 s según el informe (> 60 s).
  - RM1: se midió en `b614b91`; lo posterior solo toca `progress/` y
    `tasks.md`.
  - RM2: media de 4,0 s con bases de 13,8 y 9,2 s, y 405 × 4,0 ≈ 1620 s:
    coherente.
  - Sin «CAMPAÑA NO VÁLIDA» ni base rota. RM3: en mi muestra (cliente,
    lote, traza, dominio), ningún equivalente.
  - RM5: N/A. RM6: `b614b91` solo añade tests.
- **RM4**, en una copia del scratchpad, cuatro mutantes aplicados y
  revertidos, todos muertos: `sigrid_write_client.py:910` (1 failed),
  `reglas_incidencias.py:171` (1), `lecturas_lote.py:524` (6) y api
  `incidencias.py:106` (7). El árbol de trabajo sigue limpio.

## Obs. 1 de punta a punta: RESUELTA

- **Contrato** `tests/contratos/f030_r30.json`: sin cambios desde T22.
  `4e24df6` y `423a203` solo quitan los `xfail`.
- **Mitad api**, con el código real: la 7 conserva su `id`, 9001/9002 y los
  días 5/9, y `_payloads` arma exactamente la `peticion` de los casos 6-9 y
  12-14.
- **Mitad transfer**, por HTTP y con el pipeline real: solo `editar_fec`,
  con los mismos `ide`; ni `INSERT` ni `DELETE`.
- **La cadena entera** está cubierta: front (`r37_*`) → caso de uso
  (`r36_*`) → payload → transfer.

## Lo que pidió el líder

- **Guarda del `UPDATE`.** Es la de F-051 (`ide`, recurso, `can` ≈ 0,
  `synckey`, sin enlaces, `con.est`) más `a.cod = ?`: igual de estricta.
  Sin `hora`, el texto de F-051 queda idéntico (test
  `r41_sql_la_guarda_sin_codigo_…`).
- **R45, el par.** Al releer se editan las dos líneas o ninguna; la que la
  guarda no cambia pasa a `omitir` y nunca se inserta. La ventana que queda
  está aceptada en design §12.
- **Ni `DELETE` ni `INSERT` nuevos** por las líneas que se editan.
- **Front sin lógica.** `idsDeLaRespuesta` solo copia identidad (§13.3).
- **`test_f051_sql_cero.py` intacto** (`dev...HEAD` vacío).
- **Obs. 3-7, recogidas**: 3 (con test), 4 (T36), 5 (docstring con test),
  6 (`reconciliar`) y 7 (el parte, solo por las `escribir`).
- **Desviaciones del §3, aceptadas**: los nombres (§6 no los fijaba), los
  `xfail` quitados en T26/T31 (con `strict`, el XPASS pone la suite en
  rojo), `reconciliar` con su adaptador, R42 sin día (solo la de T20, ya
  limpia) y R43.
- **Lista cerrada (§13.7).** De los tests ajenos solo cambian dobles. Hay
  propios cambiados que la lista no nombra: los esquemas `r17`/`r2`,
  `r21_cuadrante_repo_de_periodo`, los `r17_guardar_*` del snapshot y
  `r15_cargar_edicion` en el front. Los obligan T23, R36 y §13.3, constan en
  impl §4 y ninguno debilita una aserción: aceptados (obs. 6).

## Checkpoints

| | Estado |
|---|---|
| C1 init.sh exit 0 · ficheros base | [x] · [x] |
| C2 una `in_progress` · rama · `history.md` | [x] · [x] · [x] (no está `done`) |
| C2 `current.md` sin restos | [ ] cambio 1: líneas 119-122 caducadas |
| C3 hexagonal · ruta · sin `print` · sin secretos · sin dependencias | [x] reglas puras; el ORM de `traza_incidencias.py` consta |
| C3 reglas del dominio | [x] `#regla-incidencia` («Cambiar los días», «Quitar»); `INTEGRACION.md` |
| C3 bis · C4 ter | N/A: sin `docs/referencia/` · sin `rutas_sensibles.json` |
| C4 cada R con su test · sin red ni BBDD | [ ] cambio 2: R48 · [x] |
| C4 MANUAL en `current.md` con su comando exacto | [x] las dos mitades, con `--ano`/`--mes` |
| C4 bis nivel · RED · cobertura · mutación | [x] · [x] trazas de T22-T35 · [x] · [x] recálculo + RM4 |
| C4 bis muertos · coste · cabecera · RM1 · RM2 · RM5 · RM6 · manual · supervivientes | [x] · [x] · [x] · [x] · [x] · N/A · [x] · N/A · [x] 0 |
| C4 bis «Evidencias» · C5 `tasks.md` · árbol · `features.json` | [x] · [x] (T20, MANUAL pendiente) · [x] · [x] |

## Cobertura del anexo (R1-R35, en la pasada 1)

| R | Test(s) |
|---|---|
| R36, R38, R39, R47 | api `test_f030_r30_identidad.py`: `r36_*`, `r38_*`, `r39_*`, `r47_*` |
| R37, R38, R46 | front `test_f030_r30_front.py`: `r37_*`, `r38_*`, `r46_*` |
| R40-R46 | transfer `test_f030_r30_editar.py`: de `r40_*` a `r46_*` |
| **R48** | **ninguno con su nombre** (lo cubren `r41_sin_dia_…_del_mes` y `r42_cambiada`): cambio 2 |
| R49 · R30 | `r49_script_*` y T20 · los dos `test_f030_r30_punta_a_punta.py` |

## Cambios requeridos

1. **`progress/current.md` (del líder), líneas 119-122.** Dicen que falta
   probar el `INSERT` del par y la lectura de las `CI*`, y eso ya lo probó
   la primera mitad (`manual_F-030.md`). Hay que poner en su lugar:
   - **Lo que la segunda mitad tiene que probar:** el `UPDATE … SET fec`
     con su guarda, `lineas_para_editar` sobre líneas `CI*`, la relectura
     por `ide` y las columnas nuevas (`can`, `hmoide`, `est`).
   - **Lo que no probará ni así:** el script no manda la traza y localiza
     por `synckey`, así que la rama `OR h.ide IN (…)` y R42 con día solo
     quedan probadas con tests de texto. Si esa SQL falla, el preflight
     falla sin escribir nada.
2. **R48 sin test con su nombre (C4).** Añadir un `test_f030_r48_*` (la
   nuestra en otro mes no se edita, o un `id` de otro periodo da 422).
   Saldrá verde de entrada, como T1, sin campaña nueva.

## Observaciones no bloqueantes (recógelas o di por qué no)

3. `reglas_incidencias.py:34-37`: `_TRAZA_ROL` está entre dos bloques de
   `import`. Va debajo de ellos.
4. R46 pide «todo lo leído», y el log (`_fila`, como en F-051) no lleva
   `reside`, `hmoide`, `est` ni `enlazada`.
5. Para el humano: la guarda no exige `fec = fec_antes`. R41 no lo pide,
   pero cerraría la ventana de §12.
6. Esos tests propios citan «design §13.7», y §13.7 no los lista.

**Automejora (propuesta):** que en `specs/SPECS.md` la lista cerrada separe
los tests ajenos (cerrados) de los propios que fija un R nuevo (permitidos
si se citan).

## Pasada 1, resumida (completa en `git show 0e80f92:progress/review_F-030.md`)

**RECHAZADO** sobre `32d764a`. Obs. 1, resuelta arriba; obs. 2, lo de T19
corregido y lo sin probar abierto (cambio 1); obs. 3-7, recogidas.
