<!-- progress/review_F-044.md -->
Revisión completa (pasada 1), `ba6b575..e223d22` (rama `feature/F-044-recursos-vinculados`, worktree `porcentajes-f044`)

# F-044 · Review 1 · **RECHAZADO** (CHANGES_REQUESTED)

**El código está bien; lo que falla es el guion de T21 y el rastro de quién
la ejecuta.** Revisados los tres servicios (contrato, preflight, `ejecutar`,
guardas, lote, traza y front), no hay ningún bloqueo en el código. Se
rechaza por dos cambios **solo de documentación** (`progress/` y
`tasks.md`): T21 escribe en Sigrid y la lanzará el líder justo después de
esta review. La pasada 2 será incremental desde `e223d22`.

**Nivel de rigor:** `critico`, declarado en `features.json`. Exige fase RED,
cobertura ≥ 80 %, campaña completa con cero supervivientes sin
justificación aceptada por el humano, RM1-RM6 y MANUAL con comando exacto.

## Bloqueos (cambios requeridos)

1. **El primer paso de T21 no comprueba el modo del proceso que escribe.**
   - **Dónde:** `current.md:148-150` e `impl_F-044.md:157-159`.
   - **Qué falla:** `python -c "…get_settings…"` solo lee el `.env` en un
     proceso nuevo. El que escribe es el **uvicorn del transfer** al que
     llama la api local, y el transfer **desplegado está en modo real**
     desde el 2026-10-01. Si la api local apuntara a Azure, o el uvicorn
     corriera con otro entorno, el `python -c` daría igualmente `True 0404`.
   - **Qué hay que añadir antes de escribir nada**, y PARAR si falla
     cualquiera de los tres:
     - (a) `curl http://127.0.0.1:8006/health` ⇒ `"modo_pruebas":true`,
       `"obra_pruebas":"0404"`, `"database":"ruesma"` (precedente:
       `manual_F-062.md:109-111`; endpoint en `app.py:367`);
     - (b) desde `services/dedicacion-api`,
       `.venv/Scripts/python -c "from config.settings import get_settings as g; print(g().transfer_base_url)"`
       ⇒ `http://127.0.0.1:8006`;
     - (c) el modal muestra «MODO PRUEBAS: se escribirá en la obra 0404»
       antes de confirmar (`app.js:3215`, a partir del `forzada_pruebas`
       del mismo proceso).
   - El `python -c` actual puede quedarse como paso adicional.
2. **El rastro se contradice sobre quién ejecuta T21.**
   - **Lo que dice cada sitio:**
     - `current.md:10`: «la hace el líder a petición expresa del humano»;
     - `current.md:145`: «MANUAL del humano (ningún agente lo ejecuta)»;
     - `tasks.md:4`: «Ningún agente escribe en Sigrid: T21 la ejecuta el
       humano», y `tasks.md:33`: «MANUAL (humano)»;
     - `impl_F-044.md:5` y `:156`: «T21 es MANUAL del humano».
   - **Qué hay que hacer:** alinearlo todo con la decisión del humano del
     2026-10-26 («haz tu la prueba»), con la cita. Para tocar `tasks.md`
     hace falta el visto bueno del humano; si no, nota de enmienda.
   - **De paso:** el título de `current.md:44` («T1-T6 hechas, retomado en
     T7») está desfasado.

## Observaciones (no bloquean; recogerlas en el mismo delta)

1. Avisar en el guion de T21: `limpiar --confirmar` borrará también la
   `OTEL` y la `OGAS` que el humano crea a mano, porque tras editarlas
   llevan `tex = PRUEBA-PORC` y `porcentajes:vin:…`
   (`registro_vinculados.py:554-562`). Además, el filtro es marca + prefijo,
   no la obra (`prueba_escritura_porcentajes.py:413-416`).
2. El resumen de `estado` da `hora` y `can`, pero no `paride` ni `tot`. Para
   que Administración valide importes y partidas, copiar a
   `manual_F-044.md` la línea JSON completa.

## Checkpoints

- **C1** [x] `init.sh` exit 0, con `suite_*.ok` borrados antes: harness 418+1s, api 1308, front 403, transfer 1585; sin `[KO]`; aviso ruff 307 (deuda previa). [x] Ficheros base.
- **C2** [x] Una sola `in_progress`. [x] Rama de la feature. [ ] `current.md` coherente: bloqueo 2. [x] `history.md`.
- **C3** [x] Hexagonal: `domain/vinculados.py` y `reglas_vinculados.py` son puros; `traza_vinculados.py` importa el ORM, como `traza_incidencias.py`. [x] Primera línea con la ruta en los 15 ficheros nuevos. [x] Sin `print`, TODO, secretos ni dependencias. [x] Trampas: `can` sobre 1 (front `can*100`, como el titular: `app.js:3250`, `:3289`); postventa al destino PV y a la partida del titular; solo escribe el transfer, con `synckey`, `tex` de pruebas e `ide` por `stmt_insert_linea`, sin `DELETE`.
- **C3 bis** N/A: 0 ficheros en `docs/referencia/` y 0 PDF u ofimática (`--diff-filter=A`). Barrido propio de spec, `explore`, `impl` y `mutacion` con correo, IPv4, GUID y `password|secret|api_key|function_key = '…'`: 0 coincidencias.
- **C4** [x] R1-R31 con tests `test_f044_rN_*` en verde (tabla abajo); R32 en `test_f002_fuente_unica.py` (ANCLAS); R33 (T21) y R34 (T23) N/A hasta la MANUAL y el despliegue, por spec. [x] Sin red ni BBDD. [ ] MANUAL listada, pero su primer paso no es seguro: bloqueo 1.
- **C4 bis** [x] `rigor` declarado. [x] RED real de T1-T7 y T9-T19 (`impl:92-147`); T8 y T20 justificadas. [x] Cobertura `[OK]` 99,3 % (1100/1108). [x] Totales verificados (abajo). [x] > 60 s: **campaña no reejecutada** (3350,8 s según el informe); recálculo puro + RM. [x] Coste por mutante: 3350,8 × 4 ÷ 422 = 31,8 s. [x] Sin «NO VÁLIDA»; «Sin veredicto» = 0. [x] RM1 [x] RM2 [x] RM5. [x] RM6 N/A: entre pasadas solo cambian tests (`bd38dc5..38a53d0`); no se quitó ninguna guarda. [x] Manual N/A (422 automáticos). [x] Ningún `PENDIENTE`; 7 equivalentes aceptados («1 ok»). [x] «Evidencias» con los 4 números y los workers.
- **C4 ter** N/A: no hay `harness/rutas_sensibles.json` (solo el `.ejemplo`).
- **C5** [x] T1-T20, T22 y T24 `[x]`, con su commit `F-044 Tn:`; T21 y T23 abiertas por spec. [x] Árbol limpio tras `init.sh` (`coverage.json` ignorado). [x] `features.json` = `in_progress`.

## Mutación: verificación independiente

- **Totales**: `alcance_de_feature` + `generar_mutantes` dan 25 ficheros,
  **2603 líneas y 422 mutantes**, igual que el informe fichero a fichero.
  Los 7 supervivientes existen con su operador y su texto exacto.
- **RM1**: medido en `38a53d0`; después solo cambian `progress/` y `tasks.md`.
- **RM2**: 7,9 s × 4 workers = 31,8 s por mutante, frente a una base de
  38-70 s; coherente con `-x` y 415 muertos (422 × 7,9 ≈ 3334 s).
- **RM3**: los 7 análisis son ciertos. Los `strict` comparan listas iguales
  por construcción. En `:761` el titular solo es `escribir` u `omitir`
  antes del paso 6 (`registro_pipeline.py:667-697`, `:818`). En `:188` y
  `:252`, `elegida_valida` solo se lee con `elegida`. En `:604`,
  `elegir_parte` y `_crear_parte` fijan `existe` e `ide` a la vez.
- **RM4**, en una copia en el scratchpad: mueren `registro_pipeline.py:1412`
  (`or`→`and`, por `test_f044_r28_titular_ya_registrado_el_vinculado_da_de_alta_el_parte`)
  y `registro_vinculados.py:477` (`True`→`False`, por
  `test_f044_r26_motivo_de_la_sobrecarga_y_del_sin_partida`).
- **RM5** (muestra de uno: `:604`, `and`→`or`): la suite del transfer en la
  copia da lo mismo con y sin el mutante. Pasan 1476 en los dos casos; los
  96 fallos y 2 errores son de la copia sin el monorepo, y son idénticos.

## No regresión de F-062 y F-051, y T21 en seco

- **`registro_pipeline.py`** solo añade o sustituye por equivalente:
  `_decidir_rachas` intacto; `_planear_ediciones` gana `or c.vinculado` (el
  titular no edita el pisado de un vinculado); los tres `return res` de
  `ejecutar` pasan por `_ejecutar_vinculados`, que sin vinculados no hace
  nada. `lecturas_lote.py` y `registro_lote.py` solo añaden.
- **`_guarda`** sin `hora` da el SQL de F-051 carácter a carácter (test
  r24); con ella, `a.cod = ?` parametrizado. Sin `DELETE`. `f051` y `f062`,
  en verde.
- **T21 en seco**: `main()` real, con `get_settings` y `_cliente` dobles.
  `estado --ano 2026 --mes 11` solo lee (0 escrituras); `limpiar` es
  DRY-RUN; `limpiar --confirmar` con forzar=False da `ABORTADO`, exit 1;
  con forzar=True borra lo marcado. Ninguno lleva `--permitir-modo-real`.

## Cobertura: requisito → test (uno por R; hay más)

| R | Test | R | Test |
|---|---|---|---|
| 1 | sync `r1_config_versionada` | 17 | pipeline `r17_titular_en_postventa_o_no_ci_va_con_su_partida` |
| 2 | vinculo `r2_el_valor_del_campo_es_el_trabajador` | 18 | pipeline `r18_titular_omitido_sus_vinculados_le_siguen` |
| 3 | sync `r3_preview_publica_contadores_y_codigos_sin_nombres` | 19 | pipeline `r19_una_mesve_del_vinculado_no_es_jornada_del_trabajador` |
| 4 | vinculo `r4_vigencia_por_su_propia_baja` | 20 | reglas `r20_la_identidad_del_vinculado_es_la_de_siempre` |
| 5 | api mutacion `r5_r30_esquema_ddl_y_defectos` | 21 | mutacion `r21_aviso_de_la_linea_al_cero_con_su_partida` |
| 6 | cuadrante `r6_sin_vinculados_la_linea_de_hoy` | 22 | pipeline `r22_choque_en_un_parte_cerrado_se_omite` |
| 7 | front `r7_el_porcentaje_es_el_de_la_linea_y_no_se_edita` | 23 | mutacion `r23_sobrecarga_redondeada_a_cuatro_decimales` |
| 8 | cuadrante `r8_reemplazar_guarda_lo_de_cada_subfila` | 24 | mutacion `r24_editar_lleva_partida_cuenta_y_tex_de_la_linea` |
| 9 | cuadrante `r9_guardar_propuesta_de_subfila` | 25 | pipeline `r25_cada_conflicto_con_su_clave_y_el_del_titular_aparte` |
| 10 | api mutacion `r10_desde_admite_de_enero_a_diciembre` | 26 | mutacion `r26_motivo_de_la_sobrecarga_y_del_sin_partida` |
| 11 | lote `r11_sin_vinculados_la_salida_y_las_lecturas_de_hoy` | 27 | lote `r27_con_vinculados_el_lote_no_tiene_fallos_de_memoria` |
| 12 | pipeline `r12_una_linea_por_vinculado_con_el_can_y_la_fec_del_titular` | 28 | pipeline `r28_reejecutar_no_duplica` |
| 13 | reglas `r13_synckey_exacta` | 29 | lote `r29_con_vinculados_lote_igual_que_suelto` |
| 14 | reglas `r14_la_hora_por_defecto` | 30 | `test_f044_payload_traza.py` (18 tests `r30`) |
| 15 | reglas `r15_la_unica_hoja_con_la_subcuenta` | 31 | front `r31_los_vinculados_bajo_la_linea_de_su_trabajador` |
| 16 | mutacion `r16_por_que_sin_ci_en_palabras_o_tal_cual` | 32 | `test_f002_fuente_unica.py` (ANCLAS) |

**Lista cerrada de tests ajenos:** solo los autorizados y solo en lo
autorizado (dobles, columna «Tipo recurso», `recurso_vinculado`, `vinculado`
en `asdict(Conflicto)`, ANCLAS). Ninguna aserción se relaja.

## Automejora (propuesta para el humano, no aplicada)

`CHECKPOINTS.md` C4, en las features que escriben en Sigrid: «la MANUAL
empieza comprobando **el proceso que escribe** (`/health` del transfer
local) y **adónde apunta la api** (`transfer_base_url`), no solo los
ajustes leídos en un proceso nuevo». Desde el 2026-10-01 el desplegado está
en modo real.
