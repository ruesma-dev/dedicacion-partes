Revisión incremental desde 22c8999 (pasada 3) · `git diff 22c8999..HEAD`, HEAD `8c5a01b`
<!-- progress/review_F-030.md -->
# F-030 · Review (pasada 3)

**Veredicto: APROBADO (APPROVED).** Los dos cambios de la pasada 2 están
hechos. D16 trae su RED, y la guarda de F-051 no cambia ni un carácter.
Las obs. 3, 4 y 6 están recogidas y la 5 la cierra D16. La 6.ª campaña
cuadra con el recálculo y con RM4. El cierre (`done`) sigue pendiente de la
segunda mitad de T20 (del líder, con autorización del humano). Eso no es
motivo de rechazo.

**Rigor:** `critico`, declarado. Exige RED, cobertura, mutación con 0
supervivientes y MANUAL con su comando exacto.

## Lo que se ha ejecutado

- **`bash harness/init.sh`**, tal cual y con las cachés `suite_*.ok`
  borradas: **ENTORNO LISTO**, 0 `[KO]`. Suites: raíz 418 (+1 skipped),
  api 1126, front 359 y transfer 1230. COBERTURA 99,9 % (833/834) y
  TAMAÑO, los dos `[OK]`; ruff, 277 como `dev`. El árbol queda limpio.
- **Mutación, recálculo puro** (`alcance_de_feature` + `generar_mutantes`
  sobre HEAD): 23 ficheros, 2014 líneas y **406 mutantes**, igual que el
  informe. El mutante nuevo (`sigrid_write_client.py:938`, `+
  [int(fec_leida)]` → `-`) y el timeout (`reglas_incidencias.py:249`,
  `not`) existen tal cual.
  - **Campaña no reejecutada:** 3240,5 s según el informe (más de 60 s).
  - **RM1:** medida en `7a96edc`; lo posterior solo toca `progress/` y
    `tasks.md`.
  - **RM2:** 1 worker, media 8,0 s, bases de 33,9 y 19,2 s, y
    406 × 8,0 ≈ 3248 s: coherente. Sin «CAMPAÑA NO VÁLIDA» y sin base rota.
  - **RM3:** el mutante nuevo no es equivalente (`list - list` lanza
    `TypeError`). **RM5:** N/A, no hay equivalentes declarados. **RM6:**
    el delta no quita ninguna guarda; solo añade la de la `fec`.
- **RM4**, sobre una copia en el scratchpad (`git archive HEAD`), con `-B`
  y `__pycache__` borrado entre mutantes. Base: 171 passed (los f030 del
  transfer y `test_f051_sql_cero.py`). Cada mutante se aplicó y se
  revirtió, y **todos salen muertos**: el de la herramienta (`:938`), la
  SQL sin `AND fec = ?` y `+ [int(fecha_int)]` en vez de `fec_leida`, 1
  failed cada uno (`r41_sql_editar_la_fec_*`); el pipeline con
  `fec_leida=a.fecha_int`, 11 failed (los dos `d16_*` y el punta a punta);
  el log con `_fila`, 1 failed (`r46_*`).

## Lo que pidió el líder

- **Cambio 2 (R48).** `test_f030_r48_la_nuestra_en_otro_mes_no_se_edita`
  (transfer: con día, sin día y solo por `synckey`; las dos `omitir`) y
  `test_f030_r48_guardar_id_de_otro_periodo_422` (api: 422, nada escrito,
  la del otro mes intacta). Verdes de entrada, como T1, y lo dicen.
- **D16.** `stmt_editar_fecha_incidencia(…, fec_leida)` no tiene valor por
  defecto y añade `AND fec = ?` después de `_guarda`. El pipeline le pasa
  la `fec` releída en R45, que `sigue_editable` ya comparó con
  `fec_antes`. **La RED es real** (impl §6): 8 failed, más 2 de la ventana
  con el doble antiguo (la `fec` puesta a mano el 7 se pisaba con el 6).
  **F-051 queda byte a byte igual:** `_guarda` no cambia en el delta, y
  `test_f051_sql_cero.py` es idéntico a `dev`, compara el texto exacto y
  pasa. Constan R41, design §11, `#regla-incidencia` e `INTEGRACION.md`
  §5 (con su test `r34_*`).
- **Obs. 3:** `_TRAZA_ROL` va después del último `import`, comentado.
  **Obs. 4:** `_fila_incidencia` = `_fila` + `reside`, `hmoide`, `est` y
  `enlazada`; el log de F-051 no se toca y el test exige los cuatro.
  **Obs. 6:** las citas de «design §13.7» que quedan están en tests que
  §13.7 lista; las demás citan su R/T. **Obs. 5:** cerrada por D16.
- **`current.md` y `tasks.md`.** Los dos tienen el comando exacto de la
  segunda mitad de T20. `current.md` dice qué prueba (el `UPDATE` con
  `AND fec = ?`, `lineas_para_editar` sobre `CI*`, la relectura por `ide`
  y las columnas nuevas) y qué no (la rama `OR h.ide IN`, R42 con día y la
  ventana de D16: solo tests).
- **Tests ajenos:** solo el doble `EdicionesFalsas` de `conftest.py` (§13.7).

### El par a medias (el punto que el implementer deja al líder)

**Cumple la spec tal como está escrita. No es un defecto.**

- **R41** pide «cada línea, sola»: cada `UPDATE` lleva su propia guarda.
- **R45** pide «el par o ninguna» en la **relectura** (`no_editar_el_par`),
  y se cumple. Para lo de después pide «sin su `fec` va a `omitir`, nunca
  se inserta», y también se cumple.
- **design §12 («Par a medias»)** acepta este caso tal cual: si la guarda
  de una falla entre la relectura y el `UPDATE`, sale a `omitir` y el log
  lo dice.

D16 solo añade una causa más a esa ventana. A cambio, ya no se pisa el
cambio a mano, que es lo que pide D14. El estado que queda es estable y se
ve: en el registro siguiente, la línea movida sale otra vez `omitir`
«cambiada en Sigrid» (R42) y la otra, `ya_registrado`.

## Checkpoints

| | Estado |
|---|---|
| C1 init.sh exit 0 · ficheros base | [x] · [x] |
| C2 una `in_progress` · rama · `history.md` · `current.md` | [x] · [x] · [x] (no está `done`) · [x] cambio 1 hecho (`7946363`) y al día con T38 |
| C3 hexagonal · ruta · sin `print` · sin secretos · sin dependencias | [x] el delta: transfer (infra, aplicación) y tests |
| C3 reglas del dominio | [x] `#regla-incidencia` con D16, y `INTEGRACION.md` |
| C3 bis · C4 ter | N/A: sin `docs/referencia/` en el delta · sin `rutas_sensibles.json` |
| C4 cada R con su test · sin red ni BBDD | [x] R48 ya tiene el suyo (api y transfer) · [x] |
| C4 MANUAL en `current.md` con su comando exacto | [x] la segunda mitad, con `--ano`/`--mes` |
| C4 bis nivel · RED · cobertura · mutación | [x] · [x] T38 con su traza real · [x] 99,9 % · [x] recálculo + RM4 |
| C4 bis muertos · coste · cabecera · RM1 · RM2 · RM5 · RM6 · manual · supervivientes | [x] (sin reejecutar, > 60 s) · [x] 8,0 s · [x] · [x] · [x] · N/A · [x] · N/A (automática) · [x] 0 |
| C4 bis «Evidencias» con workers · C5 `tasks.md` · árbol · `features.json` | [x] · [x] T38 `[x]`; T20 MANUAL pendiente · [x] · [x] |

## Cobertura (R1-R35 en la pasada 1; R36-R47 y R49 en la pasada 2)

| R | Test(s) |
|---|---|
| R41 (D16), R46, R34 | transfer `test_f030_r30_editar.py`: `r41_sql_editar_la_fec_*`, `r41_d16_*` (SQL y la ventana, ini/fin), `r41_ejecutar_*`, `r46_el_log_*`, los dos `r34_*` |
| **R48** | api `test_f030_r48_guardar_id_de_otro_periodo_422` · transfer `test_f030_r48_la_nuestra_en_otro_mes_no_se_edita` (3 casos) |

## Cambios requeridos

Ninguno.

## Observaciones no bloqueantes (para el líder y el humano)

1. **Para el humano, el par a medias.** Cerrarlo costaría una D17 con
   guarda cruzada (cada `UPDATE` exige también la `fec` de la otra línea,
   la leída o la nueva; toca R41, R45 y §13.5), una tarea, una 7.ª campaña
   (unos 55 min en serie) y otra review. Hace falta que alguien edite esa
   línea en Sigrid entre la relectura y el lote de la misma petición, y el
   efecto se ve y no destruye nada. **Recomiendo aceptarlo como está en
   §12.**
2. **design §13.2 y §13.5 siguen sin D16** (la firma sin `fec_leida`, la
   SQL sin `AND fec = ?`). Lo arregla §11, pero quien lea solo §13.5 ve la
   guarda antigua. Son dos retoques del spec-author o del líder, sin
   líneas nuevas (246/250); lo dice también impl §9.
3. T20: `tasks.md` anota en `impl_F-030.md`, `current.md` en `manual_F-030.md`.

**Automejora (propuesta, sin aplicar):** que RM4 en
`.claude/agents/reviewer.md` pida `python -B`, o borrar `__pycache__`
entre mutantes. Un mutante del mismo tamaño revertido en el mismo segundo
deja un `.pyc` válido que contamina la prueba siguiente. Me pasó en la
primera tanda y la repetí.

## Pasadas anteriores, resumidas

- **Pasada 2** (`git show 22c8999:progress/review_F-030.md`): RECHAZADO
  por papeleo; todo resuelto arriba. Su automejora sigue propuesta.
- **Pasada 1** (`git show 774b5cd:progress/review_F-030.md`): RECHAZADO
  por R30, resuelto por el anexo (D11-D15).
