<!-- progress/review_F-062.md -->
Revisión completa (pasada 1): `d900f34..fb351e0` (alcance de mutación desde `91648df`, la base con `dev`; entre los dos solo hay commits de spec).

# F-062 · Review 1 (reviewer, 2026-10-24)

**Veredicto: RECHAZADO** (CHANGES_REQUESTED), con 6 bloqueos. El riesgo principal en el código está bien: no hay
ningún `DELETE`, el `UPDATE` lleva la guarda con `can` y `synckey` leídos, `ejecutar` relee lo que mueve y D17 se
cumple. Pero **los MANUAL T19 y T20, tal como están escritos, no son correctos ni seguros**. T20 haría una escritura
equivocada en la 0404; T19 no mide lo que dice; y ninguno de los dos comprueba el modo del proceso que escribe.

**Rigor:** `critico`, declarado en `features.json`. Exige fase RED, cobertura ≥ 80 %, campaña completa con 0
supervivientes salvo justificación aceptada por el humano, RM1-RM6 (también RM5) y los MANUAL con su comando exacto.

## Lo verificado (resultado real)

- `bash harness/init.sh` (tras borrar `.arnes_cache/suite_*.ok`): exit 0, `ENTORNO LISTO`.
  - Suites: raíz 418 passed y 1 skipped; api 1164; front 376; transfer 1415.
  - Puertas: `COBERTURA [OK] 99.8% de 898`; tamaño del informe del implementer 203/220.
  - ruff: 127 avisos en los `.py` tocados, tanto en `HEAD` como en `91648df` (deuda previa).
- **Mutación.** Recálculo puro con `harness.alcance` y `generar_y_muestrear`: 15 ficheros, 1920 líneas y **591** mutantes, sin muestreo. Coincide con el informe.
  - Los mutantes nº 1, 7-10, 14, 23 y 25 existen tal cual: mismo operador y mismo texto.
  - **Campaña no reejecutada: 3322,3 s según el informe.**
  - RM1: el SHA medido es `30ef3b4`, y desde entonces solo hay tests y papeleo; nada del alcance.
  - RM2: 5,6 s × 4 workers = 22,5 s por mutante, frente a bases de 29-48 s, con `-x` y un 95 % de muertos: coherente.
  - Sin «NO VÁLIDA», sin «sin veredicto» y ningún mutante en `PENDIENTE`.
- **RM5: los dos equivalentes, comprobados.** Demostrador: `demo_equiv.py`, en el scratchpad del reviewer.
  - nº 14 (`rachas.py:113`): `emparejar` da lo mismo con el original y con el mutado en 20.000 entradas aleatorias.
  - nº 23 (`rachas.py:528`): en 9.600 salidas de `decidir_incidencia` salen siempre dos acciones y, si alguna omite, las
    dos omiten con el mismo motivo (9.582 casos). `base` solo nace ahí: `_cuentas` y las partidas no tocan `accion`.
  - Sobre una copia limpia de `HEAD` (base 1411 passed y 4 skipped), los dos sobreviven.
  - RM3: ningún equivalente sale muerto.
  - RM4: 3 mutantes del transfer al azar mueren en serie (10, 1 y 146 fallos).
  - RM6: no se tocó producción tras la campaña.
  - **El nº 1, «falso superviviente», queda reproducido:** con él, la api cae con 15 fallos (O1).
- **Sigrid.**
  - Ningún `DELETE` nuevo: `stmt_borrar_linea` solo está en `limpiar`.
  - El `UPDATE` es `_guarda` + `fec = ?`, con el `can` leído si es ajeno y 0 si es propio (`registro_pipeline.py:1253`).
  - `_planear_ediciones` relee antes de escribir y `no_editar_el_par` va por cadena.
  - El `CIZ` va al parte del inicio (`_al_parte_de`); el de D14, al de M−1 de mayor `ide` (`_parte_de_m1`).
  - R31 se cumple con `_cierres_a_escribir`. Los `INSERT` salen del preflight que relanza el propio `ejecutar`.
  - `con_contexto` crea un pipeline nuevo, sin estado compartido.
- **Límite de servicio.** `app.js` solo pinta: la casilla usa la `clave` que le llega. No se copia nada entre servicios, y
  `rachas.py` no importa infraestructura.
- **Lista cerrada.** Los tests ajenos tocados son exactamente los de design §12 + D18, más `test_f002` (design §4 y
  T18, que solo añade un test). Lo que se borró de `test_f030_*` está reemplazado en `test_f062_cliente_ventana.py` y
  `test_f062_lote.py`, con su marca.
- **azure-apps `ff0acb4`.** Leído; árbol limpio. Cubre §1, §3, §5 y §7, con el orden de despliegue. El aviso a `partes`
  está en `current.md` (l. 250-257).

## Checkpoints

- **C1** [x] `init.sh` · [x] ficheros.
- **C2** [x] una `in_progress` · [x] rama · [ ] `current.md` (bloqueo 4) · N/A `history.md`: la feature no está `done`.
- **C3**
  - [x] hexagonal · [x] primera línea · [x] sin debug, secretos ni dependencias (los prints son la salida del script).
  - [ ] formato (bloqueo 5).
  - [x] las tres trampas: sin escala nueva, sin postventa y escritura solo del transfer, con `synckey` y modo pruebas.
- **C3 bis** N/A: no se toca `docs/referencia/`.
- **C4** [x] trazabilidad (tabla) · [x] sin red ni BBDD · [ ] MANUAL con su comando exacto en `current.md` (bloqueos 1-4).
- **C4 bis**
  - [x] `rigor` · [x] fase RED: trazas reales de T1-T18 y T5c; dice dónde no la hay (T16 rota adrede, T22).
  - [x] cobertura · [x] recálculo · [x] 60 s · [x] coste por mutante · [x] sin «no válida» · [x] RM1, RM2, RM5 y RM6.
  - [x] «Evidencias», con los workers.
  - [ ] Equivalentes aceptados por el humano: no consta para los 2. Es condición de `done` (bloqueo 4).
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5**
  - [ ] `tasks.md`: T21 está hecha (`fb351e0`) y sigue `[ ]`. T19 y T20, pendientes del humano.
  - [x] sin temporales · [x] `features.json`.

## Cobertura (requisito → test; uno de varios)

| R | Test |
|---|---|
| R1-R3 | `test_f062_r1_previa_del_mismo_codigo_e_inicio_no_posterior` · `test_f030_r27_f062_r2_sin_previa_ni_nada_en_el_tramo_se_escribe` · `test_f030_r27_f062_r3_r5_sin_la_nuestra_continua_la_de_administracion` |
| R4-R7 | `…r4_decidir_un_ciz_ajeno_nunca_se_acorta` · `…r5_preflight_el_ciz_va_al_parte_del_inicio` · `…r6_decidir_lo_escrito_lleva_la_base_de_la_duena` · `…c3_r7_decidir_a_fin_de_mes_queda_abierta` |
| R8-R11 | `…r8_cadenas_por_codigo_y_por_recurso` · `…r9_c7_decidir_una_ajena_en_el_tramo_omite_la_cadena` · `…r10_c8_previa_no_con_ciz_del_mes_anterior_y_avisa` · `…r11_cadenas_la_que_tiene_traza_no_se_une_a_la_anterior` |
| R12, R13, R31 | `…c12_cierres_inicio_anterior_a_m1_en_el_parte_de_m1_de_su_obra` · `…r13_cierres_parte_del_inicio_que_no_vale_solo_avisa` · `…c13_ejecutar_sin_su_clave_el_cierre_d14_queda_pendiente` |
| R14-R16 | `…r14_ejecutar_ninguna_sentencia_delete` · `…r14_d12_update_de_la_fec_con_el_can_leido` · `…r15_esquema_columna_dia_fin_antes` · `…r16_decidir_si_ya_no_lo_continua_devuelve_el_ciz_ajeno` |
| R17, R18, R30 | `…r17_traza_devolver_anula_y_borra_la_quitada_sin_ide` · `…r18_cierres_ya_cerrada_el_ultimo_dia_con_nuestra_synckey` · `…c11_no_coincide_solo_en_sigrid_por_racha_y_solo_designados` |
| R19-R21 | `…r19_ventana_de_m_menos_n_a_m_mas_1` · `…r20_lote_una_lectura_y_lo_mismo_que_suelto` · `…r21_decidir_con_ciz_en_m1_no_escribe_y_avisa` |
| R22-R26 | `…r22_contrato_sin_las_claves_nuevas_responde_como_f030` · `…r23_traza_continua_y_abierta_registrado_sin_ide` · `…r24_payload_incidencias_mes_quitadas_y_cierres` · `…r25_modal_una_linea_por_racha` · `…r26_lote_sin_nada_que_escribir_cerrar_ni_devolver_no_lee` |
| R27-R29 | `test_f062_r27_la_regla_incidencia_cuenta_la_racha` · la suite entera, sin red ni BBDD · T20 MANUAL, pendiente (bloqueos 1-3) |

## Cambios requeridos

1. **T20 escribe mal en la 0404.**
   - El script da a cada `--incidencia` el id `990101 + n` en todos los meses (`prueba_escritura_porcentajes.py:155`).
   - Y `rachas.py:627` acepta `_mes(inicio) <= mes` si el inicio es propio, contra R5 («si es de M»).
   - Resultado en (2): el registro de noviembre toma por `synckey` el `CIV` del 27-oct como propio. Con las funciones puras
     (`sim_t20.py` del scratchpad del reviewer), el `CIZ` del **6-nov se inserta en el parte de octubre**.
   - Con otro id sale `continua` y el `CIZ` va a noviembre (C3). Si se cambia `<=` por `==`, la suite sigue verde: esa
     rama no la fija ningún test.
   - **Arreglar:** R5 literal también para el inicio propio, con su test RED; ids de prueba por mes, estables dentro del
     mes (C2), con `verificar` y `limpiar` al día; y revisar lo esperado en (2)-(4).
2. **T19 no mide R20.**
   - `fase_medir --lote` (l. 479) manda `(obra, lineas)` sin contexto, así que `_decidir_rachas` no lee: daría cero
     lecturas de incidencias y un +0 % vacío.
   - En producción la api designa cada recurso (`registro_sigrid.py:321`).
   - **Arreglar:** que `medir` designe los recursos en la primera obra, como `_designar_cierres` (o `--cierres` en
     lote), con su test, y poner el comando nuevo.
3. **El modo, en el proceso que escribe.**
   - El script ejecuta el pipeline en su propio proceso, con el `.env` de su carpeta: el `curl …/health` de T19 mira otro
     proceso.
   - T20 (1)-(4) no comprueban nada, y `fase_ejecutar` (l. 312) solo avisa.
   - **Primer paso** de T19 y T20, desde `services/dedicacion-transfer`:
     `python -c "from config.settings import get_settings as g; s=g(); print(s.obra_pruebas_forzar, s.obra_pruebas_cod)"`.
     Debe dar `True 0404`; si no, **PARAR**. El `curl`, solo para T20 (5), el navegador.
4. **Rastro.**
   - `current.md`: T19 y T20 con su comando exacto, ya corregido (C4; hoy remite al informe).
   - Quitar las líneas 29-32: la fase RED «en `red/` del scratchpad» ya está en el informe.
   - En «Lo que espera al humano»: **aceptar los 2 equivalentes** (nº 14 y 23).
   - `tasks.md`: T21 `[x]`, con `ff0acb4` / `fb351e0`.
5. **Formato** en `registro_pipeline.py:1319`: continuación aplastada, 108 caracteres con 20 espacios dentro (`c.requiere_confirmar                     and …`). Es el defecto de F-051 `7a5f801`; van paréntesis en dos líneas.
6. **Docs** (design §4): `docs/ARCHITECTURE.md:132` sigue diciendo «decidir el par de líneas de cada incidencia» y debe
   decir «decidir la racha».

**Tras 1 y 2** cambia código del alcance, así que por RM1 la campaña completa se repite sobre el `HEAD` nuevo. Cada
equivalente que se mantenga trae una demostración ejecutable que compare el original con el mutado, no solo que
«sobrevive en serie».

## Observaciones (no bloquean; recoger en `current.md`)

- **O1 · Arnés.** `mutacion_paralela.py` vuelve a dar un superviviente falso: el nº 1 aquí, y 4 en F-057, «2.ª tanda».
  - La causa no está localizada, y la misma podría dar también muertos falsos.
  - Que el líder lo investigue y lo porte a `arnes-base`. Hasta entonces, en `critico`, los supervivientes se reproducen
    en serie.
- **O2.** En modo real, `fase_ejecutar` solo avisa y escribe igual. Viene de antes. Propuesta: abortar salvo con un
  indicador explícito.
- **O3.** En pruebas, la lectura por `ide` filtra por la 0404.
  - Una quitada con líneas en una obra real daría `en_sigrid` vacío, y la api la borraría (solo PostgreSQL).
  - Solo pasa mezclando modos sobre la misma base. Decirlo en `#regla-incidencia`, o no borrar en pruebas.

**Automejora (sin aplicar), para `reviewer.md` y C4:** ejecutar en seco los MANUAL contra las funciones puras, o leer el
código del script que invocan; los dos fallos de arriba solo se veían así. Y comprobar el modo en el proceso que escribe,
no en un `/health`.
