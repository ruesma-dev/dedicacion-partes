<!-- progress/mutacion_F-054.md -->
# F-054 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-054` el 2026-11-04 10:21.

## Alcance

Origen del diff: **rama** (`d317edb73adbd3164e9ba1ed5cebb4c7ebca5dbe` .. `feature/F-054-sync-trae-porcentajes`).

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
| `services/dedicacion-transfer/application/services/universo_var.py` | 36 |
| `services/dedicacion-transfer/domain/models/registro_models.py` | 52 |
| `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py` | 56 |
| `services/dedicacion-transfer/interface_adapters/api/app.py` | 93 |
| **Total** | **1744** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 289 |
| Mutantes evaluados | 289 |
| Muertos | 289 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 2936.3 s |
| SHA de HEAD medido | `353d2904087d9e6060aab221c6b528d8a573f42e` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_i7ek_jda/wk_0/services/dedicacion-api` | 89.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_i7ek_jda/wk_0/services/dedicacion-transfer` | 38.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_i7ek_jda/wk_1/services/dedicacion-api` | 89.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_i7ek_jda/wk_1/services/dedicacion-transfer` | 37.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_i7ek_jda/wk_2/services/dedicacion-api` | 89.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_i7ek_jda/wk_2/services/dedicacion-transfer` | 37.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_i7ek_jda/wk_3/services/dedicacion-api` | 89.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_i7ek_jda/wk_3/services/dedicacion-transfer` | 36.9 |
| Media por mutante evaluado (s) | 10.2 |
| Timeout efectivo por mutante (s) | 180 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

