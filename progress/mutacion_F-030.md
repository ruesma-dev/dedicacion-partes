<!-- progress/mutacion_F-030.md -->
# F-030 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-030` el 2026-10-21 14:40.

## Alcance

Origen del diff: **rama** (`20a8e0631105f70c9416917bd6b1ae6d3c1b80c9` .. `feature/F-030-dias-bajas-incidencias`).

| Fichero | Líneas en alcance |
|---|---|
| `services/dedicacion-api/application/filtros_maestros.py` | 26 |
| `services/dedicacion-api/application/registro_sigrid.py` | 54 |
| `services/dedicacion-api/application/sync_pipeline.py` | 36 |
| `services/dedicacion-api/application/traza_incidencias.py` | 58 |
| `services/dedicacion-api/application/use_cases.py` | 146 |
| `services/dedicacion-api/domain/errors.py` | 7 |
| `services/dedicacion-api/domain/incidencias.py` | 73 |
| `services/dedicacion-api/domain/models.py` | 49 |
| `services/dedicacion-api/domain/ports.py` | 37 |
| `services/dedicacion-api/infrastructure/db/orm_models.py` | 68 |
| `services/dedicacion-api/infrastructure/db/repositories.py` | 171 |
| `services/dedicacion-api/interface_adapters/api/app.py` | 2 |
| `services/dedicacion-api/interface_adapters/api/deps.py` | 7 |
| `services/dedicacion-api/interface_adapters/api/routes.py` | 49 |
| `services/dedicacion-api/interface_adapters/api/schemas.py` | 57 |
| `services/dedicacion-transfer/application/pipelines/registro_lote.py` | 13 |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py` | 156 |
| `services/dedicacion-transfer/application/services/lecturas_lote.py` | 87 |
| `services/dedicacion-transfer/application/services/reglas_incidencias.py` | 154 |
| `services/dedicacion-transfer/domain/models/registro_models.py` | 66 |
| `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py` | 44 |
| `services/dedicacion-transfer/interface_adapters/api/app.py` | 55 |
| `services/dedicacion-transfer/prueba_escritura_porcentajes.py` | 72 |
| **Total** | **1487** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 250 |
| Mutantes evaluados | 250 |
| Muertos | 250 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 1888.2 s |
| SHA de HEAD medido | `8b17e8515656e29ccb609667d16f3969a4ea7f6c` |
| Línea base (s) — `services/dedicacion-api` | 33.5 |
| Línea base (s) — `services/dedicacion-transfer` | 24.9 |
| Media por mutante evaluado (s) | 7.6 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.



## Historial de campañas (implementer)

Todas se lanzaron en serie (`--workers 1`) y completas, sin muestreo. Ningún
superviviente se dio por equivalente: todos se cerraron con un test nuevo o
con un cambio de código.

| Campaña | HEAD | Mutantes | Supervivientes | Resolución |
|---|---|---|---|---|
| 1.ª | `3b9ab12` | 251 | 31 | Todos eran huecos reales. 30 se cerraron con tests (`42c0fb5`) y 1 con código (abajo) |
| 2.ª | `42c0fb5` | 250 | 1 | `registro_pipeline.py:826`: el test del log usaba 2 líneas a escribir y 2 a omitir, así que `==` y `!=` daban lo mismo. Ahora usa 2 y 4 (`8b17e85`); con el mutante aplicado a mano da «1 failed» |
| 3.ª | `8b17e85` | 250 | **0** | esta campaña |

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
