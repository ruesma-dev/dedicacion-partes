<!-- progress/impl_F-030.md -->
# F-030 · Informe del implementer (incidencias en el cuadrante)

Rama `feature/F-030-dias-bajas-incidencias` (copia `porcentajes-f030`),
rigor **crítico**. Tres entregas, commits `F-030 Tn`:

- **T1-T19 y T21** (`8b17e85`): catálogo `CI*`, tabla `incidencia`, celda,
  chips, modal y el par `CI*`/`CIZ`; el detalle (D-a…D-g, lista cerrada de
  T4-T16, RED de T2-T19, mutación de T21) en **`progress/impl_F-030_anexo.md`**.
- **Anexo R30, T22-T37** (`b614b91`): cambiar los días de una registrada
  **edita la `fec`** de su par, nunca escribe otro (D11-D15). §2-§5.
- **T38** (`7a96edc`): la review 2 (R48 con test, obs. 3, 4 y 6) y **D16**
  (la guarda exige la `fec` leída). §6; **hay un punto para el líder**.

**T20 (MANUAL) la hizo el líder** (§8). El implementer no escribió ni leyó en
Sigrid, ni hizo `push`, ni tocó ningún `.env`.

## 2-3. Qué cambió en el anexo R30 (T22-T37) y decisiones

Detalle completo (por servicio, y las desviaciones justificadas) en
`progress/impl_F-030_anexo.md` § «Anexo R30». En corto: contrato
`tests/contratos/f030_r30.json` en dos mitades (T22); api con `quitada`,
PUT por `id` (R36, R38), evento con `id` (R47) y traza por rol (R39);
transfer con la lectura también por `ide`, `reconciliar` (R40-R44), el
`UPDATE` de solo la `fec` con guarda y `ejecutar` con relectura del par
(R45, R46); front con `id` e `idsDeLaRespuesta` (R37); docs (T35); ruff
(T36). Desviaciones: nombres `hmores_ide_*`/`dia_*`, `xfail` quitados en
T26/T31, R42 sin día mira el mes, `deduplicar` → `reconciliar` con
adaptador en sus tests. **T38, D16**: la `fec` va al final del `UPDATE`,
fuera de `_guarda` (§6).

## 4. Tests que cambiaron (lista cerrada de design §13.7)

Ajenos, solo dobles: `services/dedicacion-transfer/tests/conftest.py`
(`stmt_editar_fecha_incidencia` y su guarda en `EdicionesFalsas`; en T38,
también la `fec` leída). `test_f051_sql_cero.py` intacto. Propios:

| Fichero | Cambio |
|---|---|
| api `test_f030_incidencias.py` | esquema; `r17_guardar_*` y `repo_reemplazar_*` por `id`; snapshot con `id`/`quitada`; T36; citas (T38) |
| api `test_f030_registro.py` | doble `_inc` con la traza; `r31_traza_*` reescritos |
| transfer `test_f030_pipeline_incidencias.py` | `ClienteInc` con `ides`; `r33_cliente_*`; `r30_ejecutar_no_reescribe_*` → `editar` |
| transfer `test_f030_reglas_incidencias.py` | adaptador `deduplicar`; `r30_deduplicar_la_nuestra_*` (R40, R41) |
| transfer `test_f030_r30_editar.py`, `…_punta_a_punta.py` | T38: `fec_leida` en `r41_sql_*`/`r41_ejecutar_*`, doble del punta a punta, `r34_*` |
| front `test_f030_tabla_incidencias.py` | `r15_cargar_edicion_*` con `id` (design §13.3) |

## 5. Fase RED del anexo (trazas reales)

Desde cada servicio, `.venv/Scripts/python -m pytest <fichero> [-k …] -q
-p no:cacheprovider`, con el test escrito y sin el código; líneas `E` y
resumen (completas en `red/T2*.txt`/`red/T3*.txt` del scratchpad).

```
T22 tests/test_f030_r30_punta_a_punta.py en api y en transfer (antes de la marca xfail)
E   At index 0 diff: {'obra': …, 'incidencias': [{'id': 8, 'recurso_ide': 200, …   2 failed in 1.21s
E   At index 0 diff: ['ini', 'ya_registrado', 20260706, None] != ['ini', 'editar', 20260706, 20260705]   2 failed in 0.80s
T23 api test_f030_r30_identidad.py -k esquema
E   Right contains 3 more items, first extra item: 'ALTER TABLE incidencia ADD COLUMN IF NOT EXISTS quitada …'
E   TypeError: 'quitada' is an invalid keyword argument for IncidenciaORM   5 failed in 3.30s
T24 api -k "r36 or r38"
E   assert (2, 6, 9, False) == (7, 6, 9, False)
E   Failed: DID NOT RAISE IncidenciaInvalida   (x7)
16 failed, 1 passed, 5 deselected in 3.06s
T25 api -k r47
E   At index 0 diff: (7, 5, 9, False, 9001, 9002) != (7, 5, 9, True, 9001, 9002)   1 failed, 4 passed, 22 deselected
T26 api -k "r39 or r38_registro"
E   Right contains 4 more items: {'dia_fin': 9, 'dia_ini': 5, 'hmores_ide_fin': 9002, 'hmores_ide_ini': 9001}
E   KeyError: 'incidencias_quitadas'   E   KeyError: 'sigrid_dia_ini'   10 failed, 27 deselected
T27 transfer test_f030_r30_editar.py -k contrato
E   AttributeError: 'IncidenciaEntrada' object has no attribute 'hmores_ide_ini'
E   TypeError: AccionIncidencia.__init__() got an unexpected keyword argument 'fec_antes'   3 failed, 1 passed
T28 transfer -k sql
E   TypeError: SigridWriteClient.incidencias_del_mes() got an unexpected keyword argument 'ides'
E   AttributeError: 'SigridWriteClient' object has no attribute 'stmt_editar_fecha_incidencia'   6 failed, 4 deselected
T29 transfer -k "r40 or r41 or r42 or r43 or r44 or r27"
E   ImportError: cannot import name 'reconciliar' from 'application.services.reglas_incidencias'
E   ImportError: cannot import name 'MOTIVO_INC_CERRADO' from …   15 failed, 6 passed, 4 deselected
T30 transfer -k "preflight or lote or r33"
E   At index 0 diff: ('ini', 'ya_registrado', 20260706, None, 9001, …) != ('ini', 'editar', 20260706, 20260705, 9001, …)
E   assert [[]] == [[9001, 9002]]              (la lectura no pedía los `ide`)
E   assert not [351]                           (obs. 3)
8 failed, 26 deselected in 1.44s
T31 transfer -k "ejecutar or r45 or r46"
E   AssertionError: assert [] == ['editar_fec', 'editar_fec']
E   AssertionError: assert ['insert'] == ['insert', 'editar_fec']   14 failed, 2 passed, 33 deselected
T32 front test_f030_r30_front.py
E   assert [[None, 5], [...], [None, 25]] == [[7, 5], [9, 25]]
E   AssertionError: no existe la función idsDeLaRespuesta en app.js   9 failed in 0.79s
T34 transfer test_f030_pipeline_incidencias.py -k script
E   assert 'fec_antes=20260705 hmores.ide=70001' in '… [editar       ] inc=990101 ini CIV …'   1 failed, 10 passed
T35 transfer test_f030_r30_editar.py -k r34
E   'no se\n      reescribe aunque cambien sus días' is contained here
E   assert 'hmores_ide_ini' in '<!-- docs/INTEGRACION.md --> …'   2 failed, 49 deselected
```

T33 y T36 no tienen RED (quitan marcas y avisos de ruff). Los 7
supervivientes de la 4.ª campaña se probaron con cada mutante aplicado a
mano tras su test: «1 failed» los siete.

## 6. T38: review 2 y D16 (2026-10-22, código en `7a96edc`)

- **D16 = A (R41):** `stmt_editar_fecha_incidencia(…, fec_leida)` (sin
  defecto: sin ella no hay `UPDATE`) añade `AND fec = ?` **al final**,
  fuera de `_guarda`: el texto de F-051 no cambia (`test_f051_sql_cero.py`
  intacto, `git diff --quiet dev`). El pipeline pasa la `fec` de la
  relectura de R45 (= `fec_antes`, que `sigue_editable` ya exige). Si
  alguien la mueve entre esa relectura y el `UPDATE`, la línea no se toca y
  `_comprobar_escrito` la saca a `omitir` «cambiada en Sigrid»; nunca se
  inserta otra. Dobles con la misma guarda: `conftest.py` (lista cerrada)
  y el del punta a punta (propio). Docs: `#regla-incidencia` (y D16 en su
  pie) e `INTEGRACION.md` §5, con test (`r34_*`).
- **Para el líder: el par en esa ventana.** La otra línea del par ya pasó
  la relectura y su `UPDATE` sí entra (sigrid-api confirma el lote entero,
  no por filas): queda un par a medias, que la respuesta y el log dicen
  (una `editar`, otra `omitir`). Es el riesgo que design §12 acepta y R41
  pide («cada línea, sola»); D16 garantiza que **no se pisa** la `fec`
  cambiada a mano, no la atomicidad del par. Cerrarla del todo exigiría
  acoplar las dos guardas en SQL (cada `UPDATE` comprobando la otra línea):
  cambio de spec, no de T38; no se ha hecho. Lo fija
  `test_f030_r41_d16_la_fec_cambiada_tras_releer_no_se_pisa` (`ini`/`fin`).
- **Cambio 2 (R48):** `test_f030_r48_la_nuestra_en_otro_mes_no_se_edita`
  (transfer, con día, sin día y solo por `synckey`: las dos `omitir`) y
  `test_f030_r48_guardar_id_de_otro_periodo_422` (api). **Verdes de
  entrada, como T1**: R48 ya lo cumplían `_cambiada` (T29) e `identificar`
  (T24); fijan lo que hay, sin código nuevo.
- **Obs. 3:** `_TRAZA_ROL` debajo de los `import`, con su comentario.
  **Obs. 4:** el log de R46 usa `_fila_incidencia` = `_fila` + `reside`,
  `hmoide`, `est` y `enlazada`; `_fila` y el log de F-051, sin tocar.
  **Obs. 6:** citan su motivo real los propios que §13.7 no lista
  (api `test_f030_incidencias.py`: `r17_esquema` y `r21_cuadrante_repo` →
  T23; los `r17_guardar_*` del snapshot → R47/T24; `_IncidenciasMem` →
  R36/R38/T24; `test_f030_registro.py::_inc` → T26; transfer `ClienteInc`
  → R40/T28). Los que §13.7 sí lista siguen citándolo.
- Tests propios que cambian por D16: `r41_sql_editar_la_fec_*` y
  `r41_ejecutar_edita_el_par_*` (el parámetro `fec_leida`) y los dos `r34_*`.

**RED de T38**, desde `services/dedicacion-transfer`, con los tests
escritos y sin el código (completa en `red_T38_a.txt`/`red_T38_b.txt` del
scratchpad):

```
.venv/Scripts/python -m pytest tests/test_f030_r30_editar.py -k "r41 or r46 or r48" -q -p no:cacheprovider
E   TypeError: SigridWriteClient.stmt_editar_fecha_incidencia() got an unexpected keyword argument 'fec_leida'
E   Failed: DID NOT RAISE TypeError
E   At index 0 diff: {…, 'fecha_int': 20260706} != {…, 'fecha_int': 20260706, 'fec_leida': 20260705}
E   {9002: 20260709} != {9002: 20260712}        (d16[ini]: la guarda del doble pide la fec)
E   {9001: 20260705} != {9001: 20260706}        (d16[fin])
E   assert "'reside': 200" in "[registro] edita fec incidencia ide=9001 … antes={'can': 0.0, …, 'tex': None} fec=20260706"
8 failed, 8 passed, 43 deselected in 1.64s      (passed: los 3 r48, 4 r41 de reglas/SQL y el r46 de contrato)
# y la ventana en sí, con el doble de HEAD (guarda sin fec, como el UPDATE de antes):
.venv/Scripts/python -m pytest tests/test_f030_r30_editar.py -k "d16_la_fec" -q -p no:cacheprovider
E   {9001: 20260706} != {9001: 20260707}        (la fec puesta a mano el 7 se pisaba con el 6)
E   {9002: 20260712} != {9002: 20260710}
2 failed, 57 deselected in 1.00s
```

Con el código: transfer 1.230 passed, api 1.126 passed.

## 7. `bash harness/init.sh` y mutación (T37 y T38)

`init.sh` del cierre de T38 (código de `7a96edc`), cachés `suite_*.ok`
borradas: **ENTORNO LISTO**, ningún `[KO]`; ruff 277 (`[AVISO]`, los de
`dev`; los ficheros tocados, mismos avisos antes y después). PUERTA
COBERTURA 99,9 % (833/834; falta el `continue` de `lecturas_lote.py`, obra
de pruebas no encontrada en el lote, de T15). PUERTA TAMAÑO en `[OK]`.

Mutación en serie (`--workers 1`), completa, sobre todo el diff de F-030:
4.ª (`42c1cc8`) 405 mutantes y 7 supervivientes, huecos reales cerrados con
tests (`b614b91`); 5.ª (`b614b91`) 405 y 0. **6.ª, T38** (`7a96edc`, 2.014
líneas): **406 mutantes, 405 muertos, 0 supervivientes**, 1 timeout
detectado (el punto fijo de R44 no termina, `reglas_incidencias.py:249`).
El mutante nuevo, en la guarda (`+ [int(fec_leida)]` → `-`), muerto.
Ninguno equivalente; detalle en `progress/mutacion_F-030.md` § «Historial».

## 8. Verificación MANUAL (T20, del líder): hecha

Las dos mitades, en la 0404 con autorización expresa del humano (2026-10-21
y 2026-10-22); detalle en `progress/manual_F-030.md`. Segunda mitad: el par
5-9 (`ide` 411828/411829) pasó a 6-12 con **los mismos dos `ide`**, ninguna
línea nueva; el siguiente `ejecutar` dio `ya_registrado` y `limpiar` dejó
el parte como estaba. Sin probar contra Sigrid (solo tests): `OR h.ide IN`,
R42 con día y la ventana de D16.

## 9. Fuera del alcance y pendiente

- **`azure-apps/dedicacion.md`** (R34), del líder al desplegar: leemos
  `auxhor` (`CI*`); escribimos `CI*`/`CIZ` con `can = 0` y `synckey
  porcentajes:inc:` tras una lectura de las `CI*` del mes (y por `ide`);
  **editamos la `fec`** del par (`UPDATE` con guarda, también la `fec`
  leída; nunca `DELETE`); `id`, `quitada`, `incidencias_quitadas`,
  `fec_antes`. Avisar a `partes` de que su `partes.md` debería contarlo.
- Por D10 quedan fuera F-059 y F-060. Retirar una `quitada` es a mano (D11).

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados | 3.133 passed, 1 skipped, 0 failed: raíz 418 (+1 skipped), api 1.126, front 359 (los de node `passed`), transfer 1.230 (`init.sh` de T38) |
| Cobertura de líneas cambiadas | 99,9 % (833/834), PUERTA COBERTURA de `init.sh` |
| Mutación | 6.ª campaña: 406 generados, 405 muertos, **0 supervivientes**, 1 timeout (detectado); `--workers 1`; 3.240,5 s (HEAD `7a96edc`) |
| Tiempo de la suite | raíz 48,44 s, api 56,41 s, front 38,65 s, transfer 22,50 s (166,0 s; `init.sh` de T38) |
