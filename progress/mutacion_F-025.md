<!-- progress/mutacion_F-025.md -->
# F-025 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-025` el 2026-10-03 12:06.

## Alcance

Origen del diff: **rama** (`b03a7a52ac698eafc746bcc99cb4732b150ee786` .. `feature/F-025-obras-postventa-postv2`).

| Fichero | Líneas en alcance |
|---|---|
| `services/dedicacion-api/application/filtros_maestros.py` | 20 |
| `services/dedicacion-api/application/sync_pipeline.py` | 49 |
| `services/dedicacion-api/application/use_cases.py` | 48 |
| `services/dedicacion-api/domain/errors.py` | 5 |
| `services/dedicacion-api/domain/models.py` | 26 |
| `services/dedicacion-api/domain/normalizacion.py` | 11 |
| `services/dedicacion-api/domain/ports.py` | 17 |
| `services/dedicacion-api/infrastructure/db/orm_models.py` | 8 |
| `services/dedicacion-api/infrastructure/db/repositories.py` | 34 |
| `services/dedicacion-api/infrastructure/transfer/transfer_client.py` | 20 |
| `services/dedicacion-api/interface_adapters/api/app.py` | 2 |
| `services/dedicacion-api/interface_adapters/api/deps.py` | 10 |
| `services/dedicacion-api/interface_adapters/api/schemas.py` | 9 |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py` | 32 |
| `services/dedicacion-transfer/application/services/partida_resolver.py` | 19 |
| `services/dedicacion-transfer/application/services/universo_postventa.py` | 115 |
| `services/dedicacion-transfer/interface_adapters/api/app.py` | 33 |
| **Total** | **458** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 56 |
| Mutantes evaluados | 56 |
| Muertos | 56 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 649.9 s |
| SHA de HEAD medido | `be3d3aeb460e63a3a379b5439848c58ca8885c02` |
| Línea base (s) — `services/dedicacion-api` | 21.3 |
| Línea base (s) — `services/dedicacion-transfer` | 6.2 |
| Media por mutante evaluado (s) | 11.6 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

