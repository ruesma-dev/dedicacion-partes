<!-- progress/mutacion_F-023.md -->
# F-023 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-023` el 2026-09-30 18:28.

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
| Tiempo total | 51.0 s |
| SHA de HEAD medido | `fd2831cc50518208d8de95c3b76b3d2924684202` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-023_2edunhld/wk_0/services/dedicacion-api` | 4.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-023_2edunhld/wk_1/services/dedicacion-api` | 4.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-023_2edunhld/wk_2/services/dedicacion-api` | 4.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-023_2edunhld/wk_3/services/dedicacion-api` | 4.6 |
| Media por mutante evaluado (s) | 1.5 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

