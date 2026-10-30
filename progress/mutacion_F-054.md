<!-- progress/mutacion_F-054.md -->
# F-054 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-054` el 2026-10-30 19:33.

## Alcance

Origen del diff: **rama** (`1ed18be235f1f6a196737657f4062b4e10f58b4a` .. `feature/F-054-sync-trae-porcentajes`).

| Fichero | Líneas en alcance |
|---|---|
| `services/dedicacion-api/application/registro_sigrid.py` | 42 |
| `services/dedicacion-api/application/traer_sigrid.py` | 210 |
| `services/dedicacion-api/domain/errors.py` | 7 |
| `services/dedicacion-api/domain/models.py` | 46 |
| `services/dedicacion-api/domain/ports.py` | 35 |
| `services/dedicacion-api/domain/traer_sigrid.py` | 270 |
| `services/dedicacion-api/infrastructure/db/orm_models.py` | 3 |
| `services/dedicacion-api/infrastructure/db/repositories.py` | 58 |
| `services/dedicacion-api/infrastructure/transfer/transfer_client.py` | 59 |
| `services/dedicacion-api/interface_adapters/api/app.py` | 2 |
| `services/dedicacion-api/interface_adapters/api/deps.py` | 5 |
| `services/dedicacion-api/interface_adapters/api/routes.py` | 58 |
| `services/dedicacion-api/interface_adapters/api/schemas.py` | 120 |
| `services/dedicacion-transfer/application/pipelines/poner_a_cero.py` | 130 |
| `services/dedicacion-transfer/application/pipelines/registro_lote.py` | 51 |
| `services/dedicacion-transfer/application/services/lecturas_lote.py` | 45 |
| `services/dedicacion-transfer/application/services/porcentajes_existentes.py` | 141 |
| `services/dedicacion-transfer/application/services/reglas_obra_cero.py` | 156 |
| `services/dedicacion-transfer/application/services/reglas_porcentajes.py` | 12 |
| `services/dedicacion-transfer/domain/models/registro_models.py` | 52 |
| `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py` | 56 |
| `services/dedicacion-transfer/interface_adapters/api/app.py` | 93 |
| **Total** | **1651** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 266 |
| Mutantes evaluados | 266 |
| Muertos | 266 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 3696.2 s |
| SHA de HEAD medido | `a781d251c6a649775987b1ecafdd150be0ba11c3` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_a9mfsi9j/wk_0/services/dedicacion-api` | 104.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_a9mfsi9j/wk_0/services/dedicacion-transfer` | 65.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_a9mfsi9j/wk_1/services/dedicacion-api` | 105.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_a9mfsi9j/wk_1/services/dedicacion-transfer` | 67.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_a9mfsi9j/wk_2/services/dedicacion-api` | 105.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_a9mfsi9j/wk_2/services/dedicacion-transfer` | 66.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_a9mfsi9j/wk_3/services/dedicacion-api` | 105.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_a9mfsi9j/wk_3/services/dedicacion-transfer` | 65.8 |
| Media por mutante evaluado (s) | 13.9 |
| Timeout efectivo por mutante (s) | 211 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.


## Nota del implementer (T22, D19)

Campaña reejecutada en `a781d25` (HEAD con T22 entera: `abd5514`, `fd56da6`,
`69647cf`; `a781d25` solo añade la copia de la campaña 2). El alcance gana
`reglas_porcentajes.py` (12 líneas), pero **ningún operador genera mutantes
en ellas** (no hay comparaciones, enteros, booleanos ni lógicos: solo
`**resuelta` y un `dict`). Por eso, RM4 a mano sobre cada línea cambiada, en
una copia `git archive HEAD` en el scratchpad, con
`pytest tests/test_f054_obra_cero.py` (base `40 passed`):

| Mutante | Resultado |
|---|---|
| `omitir` sin `**resuelta` | muerto, 7 failed |
| sin recurso sin `**resuelta` | muerto, 1 failed |
| % no numérico sin `**resuelta` | muerto, 1 failed |
| % fuera de rango sin `**resuelta` | muerto, 4 failed |
| sin `M*` sin `**resuelta` | muerto, 2 failed |
| `resuelta` con `destino="obra"` | muerto, 6 failed |
| `resuelta` con `paride=0` | muerto, 7 failed |
| `resuelta` con `partida_cod=None` | muerto, 6 failed |

8/8 muertos. Campañas anteriores: `progress/mutacion_F-054_campana1.md`
(`95cc089`) y `progress/mutacion_F-054_campana2.md` (`c70eb61`, 266/266).
