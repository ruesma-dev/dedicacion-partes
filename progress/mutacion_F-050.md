<!-- progress/mutacion_F-050.md -->
# F-050 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-050` el 2026-10-11 02:46.

## Alcance

Origen del diff: **rama** (`82bf8d6f1d9145d40f7a231037f95c32b3177e4b` .. `feature/F-050-subfilas-partida`).

| Fichero | Líneas en alcance |
|---|---|
| `services/dedicacion-api/application/partidas_linea.py` | 99 |
| `services/dedicacion-api/application/registro_sigrid.py` | 15 |
| `services/dedicacion-api/application/use_cases.py` | 98 |
| `services/dedicacion-api/domain/errors.py` | 11 |
| `services/dedicacion-api/domain/models.py` | 8 |
| `services/dedicacion-api/infrastructure/db/orm_models.py` | 7 |
| `services/dedicacion-api/infrastructure/db/repositories.py` | 18 |
| `services/dedicacion-api/infrastructure/transfer/transfer_client.py` | 16 |
| `services/dedicacion-api/interface_adapters/api/app.py` | 4 |
| `services/dedicacion-api/interface_adapters/api/deps.py` | 3 |
| `services/dedicacion-api/interface_adapters/api/routes.py` | 77 |
| `services/dedicacion-api/interface_adapters/api/schemas.py` | 27 |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py` | 106 |
| `services/dedicacion-transfer/application/services/propuesta_partida.py` | 219 |
| `services/dedicacion-transfer/config/settings.py` | 4 |
| `services/dedicacion-transfer/domain/models/registro_models.py` | 5 |
| `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py` | 44 |
| `services/dedicacion-transfer/interface_adapters/api/app.py` | 49 |
| `services/dedicacion-transfer/prueba_escritura_porcentajes.py` | 72 |
| **Total** | **882** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 164 |
| Mutantes evaluados | 164 |
| Muertos | 164 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 1796.6 s |
| SHA de HEAD medido | `ee4c70d86db574a00d049a9a9b8c847d4e9a5040` |
| Línea base (s) — `services/dedicacion-api` | 38.9 |
| Línea base (s) — `services/dedicacion-transfer` | 9.6 |
| Media por mutante evaluado (s) | 11.0 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

