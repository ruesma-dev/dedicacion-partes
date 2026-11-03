<!-- progress/mutacion_F-054.md -->
# F-054 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-054` el 2026-11-03 19:24.

## Alcance

Origen del diff: **rama** (`1ed18be235f1f6a196737657f4062b4e10f58b4a` .. `feature/F-054-sync-trae-porcentajes`).

| Fichero | Líneas en alcance |
|---|---|
| `services/dedicacion-api/application/registro_sigrid.py` | 49 |
| `services/dedicacion-api/application/traer_sigrid.py` | 212 |
| `services/dedicacion-api/domain/errors.py` | 7 |
| `services/dedicacion-api/domain/models.py` | 46 |
| `services/dedicacion-api/domain/obras.py` | 11 |
| `services/dedicacion-api/domain/ports.py` | 40 |
| `services/dedicacion-api/domain/traer_sigrid.py` | 279 |
| `services/dedicacion-api/infrastructure/db/orm_models.py` | 3 |
| `services/dedicacion-api/infrastructure/db/repositories.py` | 65 |
| `services/dedicacion-api/infrastructure/transfer/transfer_client.py` | 59 |
| `services/dedicacion-api/interface_adapters/api/app.py` | 2 |
| `services/dedicacion-api/interface_adapters/api/deps.py` | 5 |
| `services/dedicacion-api/interface_adapters/api/routes.py` | 58 |
| `services/dedicacion-api/interface_adapters/api/schemas.py` | 124 |
| `services/dedicacion-transfer/application/pipelines/poner_a_cero.py` | 130 |
| `services/dedicacion-transfer/application/pipelines/registro_lote.py` | 51 |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py` | 9 |
| `services/dedicacion-transfer/application/services/lecturas_lote.py` | 45 |
| `services/dedicacion-transfer/application/services/porcentajes_existentes.py` | 144 |
| `services/dedicacion-transfer/application/services/reglas_obra_cero.py` | 156 |
| `services/dedicacion-transfer/application/services/reglas_porcentajes.py` | 12 |
| `services/dedicacion-transfer/application/services/universo_var.py` | 19 |
| `services/dedicacion-transfer/domain/models/registro_models.py` | 52 |
| `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py` | 56 |
| `services/dedicacion-transfer/interface_adapters/api/app.py` | 93 |
| **Total** | **1727** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 287 |
| Mutantes evaluados | 287 |
| Muertos | 287 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 2676.1 s |
| SHA de HEAD medido | `086983ada163a73dbd17497dd7a66a119b1d6f62` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_yzo80h9a/wk_0/services/dedicacion-api` | 83.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_yzo80h9a/wk_0/services/dedicacion-transfer` | 42.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_yzo80h9a/wk_1/services/dedicacion-api` | 83.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_yzo80h9a/wk_1/services/dedicacion-transfer` | 41.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_yzo80h9a/wk_2/services/dedicacion-api` | 83.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_yzo80h9a/wk_2/services/dedicacion-transfer` | 42.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_yzo80h9a/wk_3/services/dedicacion-api` | 82.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_yzo80h9a/wk_3/services/dedicacion-transfer` | 42.4 |
| Media por mutante evaluado (s) | 9.3 |
| Timeout efectivo por mutante (s) | 167 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

