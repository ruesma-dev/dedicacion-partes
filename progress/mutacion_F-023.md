<!-- progress/mutacion_F-023.md -->
# F-023 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-023` el 2026-10-01 00:40.

## Alcance

Origen del diff: **rama** (`6fb5147aa88e6193123ac36357c7dd8af7956ee2` .. `feature/F-023-sync-empresa-y-estado-recurso`).

| Fichero | Líneas en alcance |
|---|---|
| `services/dedicacion-api/application/filtros_maestros.py` | 88 |
| `services/dedicacion-api/application/sync_pipeline.py` | 23 |
| `services/dedicacion-api/application/use_cases.py` | 35 |
| `services/dedicacion-api/domain/models.py` | 2 |
| `services/dedicacion-api/infrastructure/db/orm_models.py` | 8 |
| `services/dedicacion-api/infrastructure/db/repositories.py` | 13 |
| `services/dedicacion-api/interface_adapters/api/deps.py` | 13 |
| **Total** | **182** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 33 |
| Mutantes evaluados | 33 |
| Muertos | 33 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 255.6 s |
| SHA de HEAD medido | `ef38fa840c14188dc3a7757b5d16beba6b017a9a` |
| Línea base (s) — `services/dedicacion-api` | 14.5 |
| Media por mutante evaluado (s) | 7.7 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

