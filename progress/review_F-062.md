<!-- progress/review_F-062.md -->
Revisión incremental desde `fb351e0` (pasada 2): delta `c8fadbe..fae5352`. Lo aprobado en la review 1 hasta `fb351e0`
queda dado por bueno, salvo lo que tocan los arreglos (`rachas.py:627`, `_cierres_a_escribir` y el script), que se relee.

# F-062 · Review 2 (reviewer, 2026-10-25)

**Veredicto: APROBADO** (APPROVED). Los 6 bloqueos de la review 1 están arreglados y verificados con evidencia propia, O2
está hecha con su test, la campaña 2 cuadra (RM1-RM6) y T19/T20 son correctos y seguros en seco. **`done` sigue
esperando a T19 y T20** (MANUAL del humano, rigor `critico`: comando exacto y resultado real en `progress/manual_F-062.md`).

**Rigor:** `critico` (`features.json`). Exige RED, cobertura ≥ 80 %, campaña completa con 0 supervivientes salvo
justificación aceptada por el humano, RM1-RM6 (RM5 incluida) y los MANUAL con su comando exacto y su resultado real.

## Lo verificado (resultado real)

- **`bash harness/init.sh`** (tras borrar `.arnes_cache/suite_*.ok`): exit 0, `ENTORNO LISTO`. Raíz 418 passed y 1
  skipped; api 1164; front 376; transfer 1425. `COBERTURA [OK] 99.8% de 923`; tamaños 150/150, 250/250, 215/220.
  ruff: 277 en el árbol; en los 6 `.py` del delta, los mismos que en `c8fadbe` (3, 0, 13, 0, 0, 0): nada nuevo.
- **B1 · R5 literal.** `rachas.py:627` pasa a `_mes(inicio.fecha_int) == mes` (propio o ajeno). El test nuevo
  `test_f062_r5_decidir_el_ciz_solo_va_al_parte_de_un_inicio_de_m` es **RED de verdad**: contra el `rachas.py` de
  `c8fadbe`, en una copia, `assert ('escribir', 20261106, 100) == ('escribir', 20261106, None)`, `1 failed`.
  - Ids del script por mes: `_id_de_prueba(mes, n) = 990101 + (mes−1)·100 + n`, tope de 100 por mes con error de
    argumentos; `verificar` pide los del mes; `limpiar` borra por marca y prefijo, de todos los meses (el `CIZ` de
    cierre también lleva `tex`, `registro_pipeline.py:1299`).
  - **T20 en seco, otra vez** (`sim_t20_r2.py`, con estado, ids sacados de `script._incidencias` y las funciones puras de
    `HEAD`; (3) y (4) con `cierres_mes_anterior` y la regla de `pisar`). Sale lo que dice `current.md`:
    - (1) `CIV` 5 y `CIZ` 9 (991001); luego `fin editar` del **mismo** `ide` al 16 y la 991002 `continua`; repetir: nada.
    - (2) 27-oct: `CIV`, `fin abierta`. 2-6 nov (991101): `ini continua` y `CIZ` el 6 en el **parte de M** (noviembre).
    - (3) `--cierres`: `CIZ` el 31 en el parte de octubre, `porcentajes:inc:991001:fin`, sin `pisar`; repetir: `ya_registrado`.
    - (4) sep 15-30 abierta; oct 1-31 `continua`/`abierta`, nada escrito; nov `--cierres`: `pendiente`, `cierre:{ide}`;
      con `--pisar`, `CIZ` el 31-oct en el parte de octubre (`990901:fin`); repetir: `ya_registrado`.
  - Y el `sim_t20.py` de la review 1 (el mismo id en todos los meses) ya no lleva el `CIZ` a octubre: con `==`, la defensa
    no depende solo de los ids.
- **B2 · `medir` designa.** Con `--cierres`, la primera obra va con `ContextoRachas(cierres_recursos=…)`: en lote, la
  cuádrupla que `RegistroLote.preflight` admite (`registro_lote.py:72-83`); obra a obra, `con_contexto`. Sin `--cierres`,
  `(obra, lineas)`: `test_f055_medicion.py` (fuera de la lista) intacto. **T19 en seco** (`r2t19/test_seco_t19.py`: un doble
  que apunta cada lectura con su nombre real, el script entero): sin `--cierres`, 0 `lectura incidencias_en_ventana:`;
  con `--cierres 200`, **1** en el lote. El `--cierres` que no es `--recurso`, error de argumentos.
- **B3 · el modo, en el proceso que escribe.** T19 y T20 empiezan, desde `services/dedicacion-transfer`, con el
  `python -c "from config.settings import get_settings as g; …"` que pedí: el mismo `get_settings` y el mismo `.env` que
  usa el script. Debe dar `True 0404`; si no, PARAR. El `curl …/health`, solo en T20 (5), donde escribe el servidor.
  Ningún comando lleva `--permitir-modo-real`.
- **B4 · rastro.** `current.md`: cabecera al día; «F-062 · T19 y T20» con un comando por línea; fuera las líneas de
  `red/`; en «Lo que espera al humano», los equivalentes aceptados. `tasks.md`: T21 `[x]` con `ff0acb4`/`fb351e0`.
- **B5** `registro_pipeline.py:1319-1320`, paréntesis en dos líneas. **B6** `ARCHITECTURE.md:132`, «decidir la racha».
- **O2** (desviación aprobada por el humano). `_solo_en_pruebas`: `ejecutar --confirmar` y `limpiar --confirmar`, en modo
  real y sin `--permitir-modo-real`, salen con código 1 **antes** de leer o escribir; el dry-run sigue leyendo. Son los
  dos únicos caminos de escritura del script (`pipeline.ejecutar`, l. 344; `stmt_borrar_linea`, l. 407).
  - Tests: los 4 de `o2_`. Contra el script de `c8fadbe`, los 9 casos nuevos del script fallan (`9 failed`).
  - Tests ajenos tocados en el delta: solo `test_f030_pipeline_incidencias.py` (lista cerrada, design §12); los ids
    esperados pasan a 9907xx y sus `verificar` llevan `--mes 7`. Ningún otro.
- **O3.** `#regla-incidencia` dice que en pruebas también la lectura por `ide` es de la 0404 y que no se mezclan modos.

## Campaña 2 (`progress/mutacion_F-062.md`, HEAD `44841b8`)

- **Recálculo puro** (`recalc_r2.py`: `harness.alcance` + `generar_y_muestrear`): 15 ficheros, **1992** líneas, **609**
  mutantes, sin muestreo. Coincide. Los 11 supervivientes existen tal cual: mismo fichero, línea, operador y texto.
- **Campaña no reejecutada: 4819,9 s según el informe.** RM2: 7,9 s × 4 workers ≈ 31,6 s por mutante, frente a bases de
  35-72 s, con `-x` y un 98 % de muertos: coherente. Sin «NO VÁLIDA», sin veredicto 0, ningún `PENDIENTE`.
- **RM1.** Después de `44841b8` solo hay tests (`2f04d28`) y papeleo: el alcance medido es el que reviso.
- **Los 11, en serie** (`serie_r2.py`, sobre una copia de `HEAD` por `git archive`; base api 1164 passed, transfer 1421
  passed y 4 skipped; suite del servicio con `-x`):
  | Nº | Mutante | En serie | Cae con |
  |---|---|---|---|
  | 1 | `registro_sigrid.py:436` `or []`→`and []` | muerto | `test_f062_r23_traza_ejecutar_pasa_cierres_y_no_coincide` |
  | 2 | `traza_incidencias.py:64` `is not None`→`is None` | muerto | `test_f030_r39_registro_la_registrada_viaja_con_su_traza` |
  | 3 | `traza_incidencias.py:127` `not inc_id`→`inc_id` | muerto | `test_f062_r17_traza_la_quitada_sin_lineas_en_sigrid_se_borra` |
  | 4 | `traza_incidencias.py:138` `is_(True)`→`is_(False)` | muerto | `test_f062_r17_traza_devolver_anula_y_borra_la_quitada_sin_ide` |
  | 5 | `traza_incidencias.py:167` `hechas[0]`→`hechas[1]` | muerto | `test_f030_r39_traza_un_omitir_no_borra_el_ide_de_su_rol` |
  | 6 | `rachas.py:113` `else 1`→`else 2` | **vivo** (1421 passed) | equivalente |
  | 7 | `rachas.py:528` `base[0]`→`base[1]` | **vivo** (1421 passed) | equivalente |
  | 8 | script `:159` `>`→`>=` | muerto | `test_f062_r5_script_caben_cien_incidencias_por_mes` |
  | 9 | script `:328` `exit(1)`→`exit(2)` | muerto | `test_f062_o2_script_en_modo_real_no_escribe[fase0]` |
  | 10-11 | script `:335` y `:391` `= False`→`= True` | muertos | `test_f062_o2_script_las_fases_por_defecto_no_escriben_en_modo_real` |

  Los 1-5 son falsos supervivientes de la campaña paralela (O1); los tests que los matan ya existían, y coinciden uno
  a uno con los que cita el informe. Los 8-11 mueren con los tests de `2f04d28`.
- **RM3.** Ningún equivalente sale muerto. **RM5** (`critico`): los dos equivalentes son **los mismos** de la campaña 1
  (nº 14 → 6, nº 23 → 7) y reproduje la demostración de los dos (`demo_equiv.py` sobre `HEAD`): `emparejar` original ==
  mutado en 20.000 casos; en 9.600 salidas de `decidir_incidencia`, `base[0].motivo == base[1].motivo` (9.582 omiten).
  Ningún equivalente nuevo: se cumple la condición del humano del 2026-10-24.
- **RM4.** Hecho: es la tabla de arriba. **RM6.** No se quitó ninguna guarda: los arreglos añaden defensa.

## Checkpoints

- **C1** [x] `init.sh` · [x] ficheros previstos (más el script y sus tests, que piden B1, B2 y O2).
- **C2** [x] una `in_progress` · [x] rama · [x] `current.md` al día · N/A `history.md`: la feature no está `done`.
- **C3** [x] hexagonal · [x] primera línea · [x] sin debug, secretos ni dependencias · [x] formato (B5) · [x] trampas.
- **C3 bis** N/A: no se toca `docs/referencia/`.
- **C4** [x] trazabilidad · [x] sin red ni BBDD · [x] MANUAL T19 y T20 con su comando exacto en `current.md`.
- **C4 bis** [x] `rigor` · [x] RED (B1, B2, O2 con traza y comprobada aquí) · [x] cobertura · [x] recálculo · [x] 60 s
  · [x] coste por mutante · [x] sin «no válida» · [x] RM1, RM2, RM5, RM6 · [x] «Evidencias» · [x] equivalentes aceptados.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [x] `tasks.md`: todo `[x]` salvo T19 y T20, MANUAL del humano por diseño (C4) · [x] sin temporales · [x]
  `features.json`.

## Cobertura (requisito → test, lo que cambia en esta pasada)

| R | Test |
|---|---|
| R5 (inicio propio de M−1) | `test_f062_r5_decidir_el_ciz_solo_va_al_parte_de_un_inicio_de_m` |
| R5/R12 en el script (ids por mes) | `test_f062_r5_script_ids_de_prueba_estables_por_mes_y_distintos_entre_meses` · `…verificar_pide_las_synckeys_de_su_mes` · `…caben_cien_incidencias_por_mes` |
| R20 (T19 designa) | `test_f062_r20_script_medir_lote_con_cierres_designa_en_la_primera_obra` · `…medir_cierres_que_no_son_recursos_es_error` |
| O2 | `test_f062_o2_script_en_modo_real_no_escribe` (×2) · `…dry_run_y_con_permiso` · `…las_fases_por_defecto_no_escriben_en_modo_real` |

El resto, la tabla de la review 1 (`git show c8fadbe:progress/review_F-062.md`).

## Para el líder (no bloquea)

- Antes de `done`: T19 y T20 por el humano, con su resultado real en `progress/manual_F-062.md`.
- Los comandos de T19/T20 usan `python` a secas; en F-055 era `.venv/Scripts/python`. Si el `python` del PATH no tiene
  las dependencias, falla al importar (falla seguro), pero conviene decir cuál.
- O1 sigue en pie: la campaña paralela dio 5 falsos de la api, y todos caen en serie con tests que ya había.

## Review 1 (resumen; texto completo en `git show c8fadbe:progress/review_F-062.md`)

RECHAZADA el 2026-10-24 sobre `d900f34..fb351e0`, con 6 bloqueos:
B1 T20 escribía el `CIZ` de noviembre en el parte de octubre (mismo id por mes y `<=` en `rachas.py:627`);
B2 T19 no medía R20 (`medir` no designaba); B3 ningún MANUAL comprobaba el modo en el proceso que escribe;
B4 rastro (`current.md`, equivalentes por aceptar, T21); B5 formato en `registro_pipeline.py:1319`;
B6 `ARCHITECTURE.md:132`. Observaciones O1 (campaña paralela, al líder), O2 (aprobada) y O3. Lo demás quedó aprobado:
sin `DELETE`, `UPDATE` con guarda, D17, límite de servicio, lista cerrada, `azure-apps` `ff0acb4`, RM1-RM6 de la campaña 1.
