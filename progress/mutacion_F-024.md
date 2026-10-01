<!-- progress/mutacion_F-024.md -->
# F-024 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-024` el 2026-10-01 13:20.

## Alcance

Origen del diff: **rama** (`9ea9a81b07cb24e1cf13a814a6fd87b06a056278` .. `feature/F-024-selector-empresa`).

| Fichero | Líneas en alcance |
|---|---|
| `services/dedicacion-api/application/registro_sigrid.py` | 29 |
| `services/dedicacion-api/application/use_cases.py` | 98 |
| `services/dedicacion-api/config/settings.py` | 5 |
| `services/dedicacion-api/domain/empresas.py` | 36 |
| `services/dedicacion-api/domain/models.py` | 14 |
| `services/dedicacion-api/domain/ports.py` | 4 |
| `services/dedicacion-api/infrastructure/db/repositories.py` | 9 |
| `services/dedicacion-api/interface_adapters/api/deps.py` | 8 |
| `services/dedicacion-api/interface_adapters/api/routes.py` | 84 |
| `services/dedicacion-api/interface_adapters/api/schemas.py` | 21 |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py` | 4 |
| **Total** | **312** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 17 |
| Mutantes evaluados | 17 |
| Muertos | 17 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 93.9 s |
| SHA de HEAD medido | `fda620d5d142251debf81108d160905a09e9126d` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-024_sd56wqpu/wk_0/services/dedicacion-api` | 18.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-024_sd56wqpu/wk_1/services/dedicacion-api` | 18.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-024_sd56wqpu/wk_2/services/dedicacion-api` | 18.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-024_sd56wqpu/wk_3/services/dedicacion-api` | 18.7 |
| Media por mutante evaluado (s) | 5.5 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

