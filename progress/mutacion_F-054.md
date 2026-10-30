<!-- progress/mutacion_F-054.md -->
# F-054 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-054` el 2026-10-30 10:58.

## Alcance

Origen del diff: **rama** (`1ed18be235f1f6a196737657f4062b4e10f58b4a` .. `feature/F-054-sync-trae-porcentajes`).

| Fichero | Líneas en alcance |
|---|---|
| `services/dedicacion-api/application/registro_sigrid.py` | 42 |
| `services/dedicacion-api/application/traer_sigrid.py` | 210 |
| `services/dedicacion-api/domain/errors.py` | 7 |
| `services/dedicacion-api/domain/models.py` | 46 |
| `services/dedicacion-api/domain/ports.py` | 35 |
| `services/dedicacion-api/domain/traer_sigrid.py` | 269 |
| `services/dedicacion-api/infrastructure/db/orm_models.py` | 3 |
| `services/dedicacion-api/infrastructure/db/repositories.py` | 58 |
| `services/dedicacion-api/infrastructure/transfer/transfer_client.py` | 59 |
| `services/dedicacion-api/interface_adapters/api/app.py` | 2 |
| `services/dedicacion-api/interface_adapters/api/deps.py` | 5 |
| `services/dedicacion-api/interface_adapters/api/routes.py` | 58 |
| `services/dedicacion-api/interface_adapters/api/schemas.py` | 120 |
| `services/dedicacion-transfer/application/pipelines/poner_a_cero.py` | 129 |
| `services/dedicacion-transfer/application/pipelines/registro_lote.py` | 51 |
| `services/dedicacion-transfer/application/services/lecturas_lote.py` | 45 |
| `services/dedicacion-transfer/application/services/porcentajes_existentes.py` | 140 |
| `services/dedicacion-transfer/application/services/reglas_obra_cero.py` | 148 |
| `services/dedicacion-transfer/domain/models/registro_models.py` | 51 |
| `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py` | 56 |
| `services/dedicacion-transfer/interface_adapters/api/app.py` | 92 |
| **Total** | **1626** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 262 |
| Mutantes evaluados | 262 |
| Muertos | 262 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 3767.0 s |
| SHA de HEAD medido | `c614be38d67bac7f98ee03f236cfb766421a1479` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_gz5_i8vy/wk_0/services/dedicacion-api` | 78.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_gz5_i8vy/wk_0/services/dedicacion-transfer` | 40.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_gz5_i8vy/wk_1/services/dedicacion-api` | 78.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_gz5_i8vy/wk_1/services/dedicacion-transfer` | 39.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_gz5_i8vy/wk_2/services/dedicacion-api` | 79.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_gz5_i8vy/wk_2/services/dedicacion-transfer` | 39.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_gz5_i8vy/wk_3/services/dedicacion-api` | 78.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_gz5_i8vy/wk_3/services/dedicacion-transfer` | 39.8 |
| Media por mutante evaluado (s) | 14.4 |
| Timeout efectivo por mutante (s) | 158 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

