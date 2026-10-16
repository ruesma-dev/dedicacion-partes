<!-- progress/mutacion_F-055.md -->
# F-055 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-055` el 2026-10-16 03:20.

## Alcance

Origen del diff: **rama** (`301c5986fb746eacbebdb6509eed8c93837acf73` .. `feature/F-055-preflight-rapido`).

| Fichero | Líneas en alcance |
|---|---|
| `services/dedicacion-api/application/partidas_linea.py` | 12 |
| `services/dedicacion-api/application/propuestas_mes.py` | 194 |
| `services/dedicacion-api/application/registro_sigrid.py` | 61 |
| `services/dedicacion-api/application/use_cases.py` | 19 |
| `services/dedicacion-api/domain/models.py` | 8 |
| `services/dedicacion-api/domain/ports.py` | 14 |
| `services/dedicacion-api/infrastructure/db/orm_models.py` | 10 |
| `services/dedicacion-api/infrastructure/db/repositories.py` | 45 |
| `services/dedicacion-api/infrastructure/transfer/transfer_client.py` | 18 |
| `services/dedicacion-api/interface_adapters/api/deps.py` | 11 |
| `services/dedicacion-api/interface_adapters/api/routes.py` | 47 |
| `services/dedicacion-api/interface_adapters/api/schemas.py` | 32 |
| `services/dedicacion-transfer/application/pipelines/registro_lote.py` | 77 |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py` | 83 |
| `services/dedicacion-transfer/application/services/lecturas_lote.py` | 426 |
| `services/dedicacion-transfer/application/services/propuesta_partida.py` | 19 |
| `services/dedicacion-transfer/config/settings.py` | 5 |
| `services/dedicacion-transfer/domain/models/registro_models.py` | 29 |
| `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py` | 270 |
| `services/dedicacion-transfer/interface_adapters/api/app.py` | 112 |
| `services/dedicacion-transfer/prueba_escritura_porcentajes.py` | 112 |
| **Total** | **1604** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 284 |
| Mutantes evaluados | 284 |
| Muertos | 284 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 3666.2 s |
| SHA de HEAD medido | `9d9ebb1fa5fc723d061d9ba879a9bca35ee60cec` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-055_3d_6vfa6/wk_0/services/dedicacion-api` | 126.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-055_3d_6vfa6/wk_0/services/dedicacion-transfer` | 105.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-055_3d_6vfa6/wk_1/services/dedicacion-api` | 111.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-055_3d_6vfa6/wk_1/services/dedicacion-transfer` | 94.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-055_3d_6vfa6/wk_2/services/dedicacion-api` | 125.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-055_3d_6vfa6/wk_2/services/dedicacion-transfer` | 102.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-055_3d_6vfa6/wk_3/services/dedicacion-api` | 126.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-055_3d_6vfa6/wk_3/services/dedicacion-transfer` | 95.1 |
| Media por mutante evaluado (s) | 12.9 |
| Timeout efectivo por mutante (s) | 253 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

