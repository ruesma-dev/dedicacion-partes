<!-- progress/mutacion_F-030.md -->
# F-030 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-030` el 2026-10-22 09:57.

## Alcance

Origen del diff: **rama** (`7ab115a691cb2ed413e9b006f97d033617d1a8de` .. `feature/F-030-dias-bajas-incidencias`).

| Fichero | Líneas en alcance |
|---|---|
| `services/dedicacion-api/application/filtros_maestros.py` | 26 |
| `services/dedicacion-api/application/registro_sigrid.py` | 111 |
| `services/dedicacion-api/application/sync_pipeline.py` | 36 |
| `services/dedicacion-api/application/traza_incidencias.py` | 107 |
| `services/dedicacion-api/application/use_cases.py` | 164 |
| `services/dedicacion-api/domain/errors.py` | 7 |
| `services/dedicacion-api/domain/incidencias.py` | 113 |
| `services/dedicacion-api/domain/models.py` | 56 |
| `services/dedicacion-api/domain/ports.py` | 37 |
| `services/dedicacion-api/infrastructure/db/orm_models.py` | 80 |
| `services/dedicacion-api/infrastructure/db/repositories.py` | 189 |
| `services/dedicacion-api/interface_adapters/api/app.py` | 2 |
| `services/dedicacion-api/interface_adapters/api/deps.py` | 7 |
| `services/dedicacion-api/interface_adapters/api/routes.py` | 49 |
| `services/dedicacion-api/interface_adapters/api/schemas.py` | 61 |
| `services/dedicacion-transfer/application/pipelines/registro_lote.py` | 13 |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py` | 240 |
| `services/dedicacion-transfer/application/services/lecturas_lote.py` | 101 |
| `services/dedicacion-transfer/application/services/reglas_incidencias.py` | 297 |
| `services/dedicacion-transfer/domain/models/registro_models.py` | 82 |
| `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py` | 93 |
| `services/dedicacion-transfer/interface_adapters/api/app.py` | 62 |
| `services/dedicacion-transfer/prueba_escritura_porcentajes.py` | 81 |
| **Total** | **2014** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 406 |
| Mutantes evaluados | 406 |
| Muertos | 405 |
| Supervivientes | 0 |
| Timeouts | 1 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 3240.5 s |
| SHA de HEAD medido | `7a96edc1e6c2c8218f4d7c1c1147f9891d62d8cc` |
| Línea base (s) — `services/dedicacion-api` | 33.9 |
| Línea base (s) — `services/dedicacion-transfer` | 19.2 |
| Media por mutante evaluado (s) | 8.0 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

## Timeouts

- `services/dedicacion-transfer/application/services/reglas_incidencias.py:249` [not] if not ocupadas: -> if ocupadas:


## Historial de campañas (implementer)

Todas se lanzaron en serie (`--workers 1`) y completas, sin muestreo. Ningún
superviviente se dio por equivalente: todos se cerraron con un test nuevo o
con un cambio de código.

| Campaña | HEAD | Mutantes | Supervivientes | Resolución |
|---|---|---|---|---|
| 1.ª | `3b9ab12` | 251 | 31 | Todos eran huecos reales. 30 se cerraron con tests (`42c0fb5`) y 1 con código |
| 2.ª | `42c0fb5` | 250 | 1 | `registro_pipeline.py:826`: test del log con 2 y 4 líneas (`8b17e85`) |
| 3.ª | `8b17e85` | 250 | 0 | fin de T1-T21 |
| 4.ª | `42c1cc8` | 405 | 7 (+1 timeout) | anexo R30 (T22-T36). Los 7, huecos reales, cerrados con tests (`b614b91`); abajo |
| 5.ª | `b614b91` | 405 | 0 (+1 timeout, detectado) | fin del anexo (T22-T37) |
| 6.ª | `7a96edc` | 406 | **0** (+1 timeout, detectado) | esta campaña: T38 (D16, obs. 3, 4 y 6) |

**La 6.ª (T38).** Mismo alcance más lo de T38 (2.014 líneas): un mutante
más, en la guarda nueva (`sigrid_write_client.py:938`, `+ [int(fec_leida)]`
→ `-`: muerto, como el `+ params` → `-`). Las líneas de `_fila_incidencia`
y el `AND fec = ?` del texto no generan mutantes con los operadores de la
herramienta; los cubren `test_f030_r46_el_log_de_cada_edicion` y
`test_f030_r41_sql_editar_la_fec_*`, con su RED en el informe §6. El
timeout es el mismo de la 5.ª (`reglas_incidencias.py:249`, antes `:247`:
solo bajó dos líneas al mover `_TRAZA_ROL`). Tiempo: 3.240,5 s, el doble
que la 5.ª porque las líneas base también lo son (api 33,9 s frente a
13,8 s; transfer 19,2 s frente a 9,2 s): 406 × 8,0 s ≈ 3.248 s, coherente
(RM2).

**Los 7 de la 4.ª (anexo R30) y cómo se cerraron.** Cada mutante, aplicado a
mano tras el test nuevo, da «1 failed».

- `api use_cases.py:286` (`i.id or 0` → `i.id and 0` y → `i.id or 1`): el
  desempate por `id` del snapshot del evento no lo fijaba ningún test (nunca
  había dos iguales salvo el `id`). Lo cubre
  `test_f030_r47_snapshot_iguales_salvo_el_id_por_id_y_la_nueva_primero`
  (ids 2, 1 y nueva, en los dos órdenes: `and 0` compara `None` con `0` y
  revienta; `or 1` empata la nueva con la 1).
- `api domain/incidencias.py:80` (`or` → `and` en `registrada`): todos los
  tests tenían las dos líneas o ninguna. Lo cubre
  `test_f030_r36_registrada_con_cualquiera_de_sus_dos_lineas`.
- `api schemas.py:133` (`quitada = False` → `True`): la salida siempre se
  construía con `quitada` explícito. Lo cubre
  `test_f030_r38_salida_sin_quitada_es_no_quitada`.
- `transfer reglas_incidencias.py:149` (el `ide` de la traza leído de
  `dia_*`): en los tests, lo encontrado por `ide` también se encontraba por
  `synckey`. Con una copia de la línea con la misma `synckey` más abajo en la
  lectura, manda la de la traza:
  `test_f030_r40_por_ide_la_de_la_traza_aunque_haya_otra_con_su_synckey`.
- `transfer reglas_incidencias.py:171` y `:274` (`>=` → `>` y `<` → `<=` en
  la tolerancia del `can`): ningún test usaba justo `0.000001`, el borde de
  la guarda del `UPDATE` (`ABS(can) < 0.000001`). Lo cubre
  `test_f030_r42_can_en_el_borde_de_la_tolerancia_ya_no_es_cero`, en
  `reconciliar` y en `sigue_editable`.
- El timeout (`reglas_incidencias.py:247`, `if not ocupadas` → `if
  ocupadas`) es un mutante **detectado**: el punto fijo de R44 no termina y
  la suite agota los 120 s.


**Los 31 de la 1.ª y cómo se cerraron:**

- **api, preview del catálogo** (`filtros_maestros.py:312`, `or`→`and`): no
  había ninguna fila con solo el `ide` o solo el código. Lo cubre
  `test_f030_r3_preview_sin_ide_o_sin_codigo_no_cuenta`.
- **api, registro**:
  - `registro_sigrid.py:130` (`or 0`→`or 1`): faltaba una asignación sin
    elegida ni propuesta. Se añadió la incidencia 5 en
    `test_f030_r25_partida_elegida_propuesta_o_cero`.
  - `registro_sigrid.py:185-189`, cinco mutantes `==`→`!=` en los JOIN y el
    WHERE: la sesión falsa no filtra. Lo cubre
    `test_f030_r23_la_lectura_de_incidencias_es_la_del_periodo`, que comprueba
    el texto de la consulta.
  - `traza_incidencias.py:58` (`==`→`!=`): solo se miraban los parámetros del
    UPDATE. La sesión anota ahora el WHERE (`incidencia.id = :id_1`).
- **api, modelos y esquema**:
  - `models.py:131` y `models.py:145` (`frozen`): lo cubre
    `test_f030_r17_los_modelos_son_inmutables`.
  - `orm_models.py:214-233`, cinco mutantes: `nullable` de `letra`, `nombre`
    y `sync_en`, el defecto de `activa` y el `autoincrement` del `id`. Lo
    cubre `test_f030_r3_r17_esquema_ddl_y_defectos`, que comprueba el DDL de
    PostgreSQL y los defectos de Python.
- **transfer**:
  - `registro_pipeline.py:826`: el log, ver la 2.ª campaña.
  - `registro_pipeline.py:1106` (`or 0`→`or 1`): lo cubre
    `test_f030_r24_ejecutar_sin_partida_inserta_paride_cero`.
  - `lecturas_lote.py:330-334`, seis mutantes de `_inc_sin_subcuenta`: el
    lote daba el mismo resultado porque el fallo de memoria cae al cliente.
    `test_f030_r33_lote_precarga_la_cuenta_solo_si_falta_subcuenta` comprueba
    el conjunto exacto que se precarga (200 sí; 500 con subcuentas, no; sin
    recurso, no, y con `and` revienta en `int(None)`).
  - `lecturas_lote.py:349` (`[0]`→`[1]`): parecía equivalente, porque
    `decidir_incidencia` decide igual las dos líneas del par (R26). No se
    justificó: se reescribió como `{a.accion for a in …} != {"escribir"}`,
    que no depende de la posición.
  - `registro_models.py:88, 273, 274, 278` y `app.py:99`, defectos a 0: lo
    cubre `test_f030_r24_defectos_de_entrada_y_accion`.
  - `prueba_escritura_porcentajes.py:274` (`or`→`and`, `1`→`2`): lo cubre
    `test_f030_r35_script_verificar_pide_justo_esas_synckeys`, que mira las
    synckeys exactas sin `--incidencia` y con dos.

Antes de relanzar, varios se comprobaron aplicando el mutante a mano:
`lecturas_lote` `and`, `or not` y `and sub`, y el script `max(..., 2)`. Cada
uno dio «1 failed».
