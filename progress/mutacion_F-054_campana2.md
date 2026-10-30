<!-- progress/mutacion_F-054_campana2.md -->
# F-054 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-054` el 2026-10-30 15:24.

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
| `services/dedicacion-transfer/domain/models/registro_models.py` | 52 |
| `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py` | 56 |
| `services/dedicacion-transfer/interface_adapters/api/app.py` | 93 |
| **Total** | **1639** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 266 |
| Mutantes evaluados | 266 |
| Muertos | 266 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 4837.3 s |
| SHA de HEAD medido | `c70eb61a1a59d05edc1b274ff477e8401c2d325e` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_2e4ul6m9/wk_0/services/dedicacion-api` | 136.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_2e4ul6m9/wk_0/services/dedicacion-transfer` | 100.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_2e4ul6m9/wk_1/services/dedicacion-api` | 132.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_2e4ul6m9/wk_1/services/dedicacion-transfer` | 99.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_2e4ul6m9/wk_2/services/dedicacion-api` | 133.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_2e4ul6m9/wk_2/services/dedicacion-transfer` | 93.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_2e4ul6m9/wk_3/services/dedicacion-api` | 133.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_2e4ul6m9/wk_3/services/dedicacion-transfer` | 90.8 |
| Media por mutante evaluado (s) | 18.2 |
| Timeout efectivo por mutante (s) | 274 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

