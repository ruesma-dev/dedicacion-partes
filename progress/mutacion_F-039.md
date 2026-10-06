<!-- progress/mutacion_F-039.md -->
# F-039 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-039` el 2026-10-06 18:10.

## Alcance

Origen del diff: **rama** (`8a012d78c933461f34295ee447665daa9ae0fbc5` .. `feature/F-039-obras-var-y-seis-digitos`).

| Fichero | Líneas en alcance |
|---|---|
| `services/dedicacion-api/application/filtros_maestros.py` | 55 |
| `services/dedicacion-api/application/registro_sigrid.py` | 16 |
| `services/dedicacion-api/application/sync_pipeline.py` | 73 |
| `services/dedicacion-api/application/use_cases.py` | 20 |
| `services/dedicacion-api/domain/errors.py` | 5 |
| `services/dedicacion-api/domain/models.py` | 22 |
| `services/dedicacion-api/domain/obras.py` | 32 |
| `services/dedicacion-api/domain/ports.py` | 15 |
| `services/dedicacion-api/infrastructure/db/orm_models.py` | 6 |
| `services/dedicacion-api/infrastructure/db/repositories.py` | 13 |
| `services/dedicacion-api/infrastructure/transfer/transfer_client.py` | 24 |
| `services/dedicacion-api/interface_adapters/api/app.py` | 2 |
| `services/dedicacion-api/interface_adapters/api/deps.py` | 10 |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py` | 27 |
| `services/dedicacion-transfer/application/services/universo_var.py` | 137 |
| `services/dedicacion-transfer/config/settings.py` | 5 |
| `services/dedicacion-transfer/domain/models/registro_models.py` | 6 |
| `services/dedicacion-transfer/interface_adapters/api/app.py` | 27 |
| **Total** | **495** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 60 |
| Mutantes evaluados | 60 |
| Muertos | 60 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 1274.4 s |
| SHA de HEAD medido | `6ab6588dd0541ba301badc020d0d0af71ba18925` |
| Línea base (s) — `services/dedicacion-api` | 37.8 |
| Línea base (s) — `services/dedicacion-transfer` | 14.0 |
| Media por mutante evaluado (s) | 21.2 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

