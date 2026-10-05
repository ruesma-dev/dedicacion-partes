<!-- progress/mutacion_F-022.md -->
# F-022 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-022` el 2026-09-30 00:11.

## Alcance

Origen del diff: **rama** (`01671a9d10a7b0acb05b4574c8342c1b466f9333` .. `feature/F-022-transfer-obra-por-empresa`).

| Fichero | Líneas en alcance |
|---|---|
| `services/dedicacion-api/application/registro_sigrid.py` | 5 |
| `services/dedicacion-api/config/settings.py` | 8 |
| `services/dedicacion-api/interface_adapters/api/deps.py` | 2 |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py` | 73 |
| `services/dedicacion-transfer/application/services/reglas_porcentajes.py` | 47 |
| `services/dedicacion-transfer/domain/errores.py` | 16 |
| `services/dedicacion-transfer/domain/models/registro_models.py` | 7 |
| `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py` | 39 |
| `services/dedicacion-transfer/interface_adapters/api/app.py` | 17 |
| `services/dedicacion-transfer/prueba_escritura_porcentajes.py` | 12 |
| **Total** | **226** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 28 |
| Mutantes evaluados | 28 |
| Muertos | 28 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 174.0 s |
| SHA de HEAD medido | `dfe079d44d791dcb9ae1e2321ea7792ff52619f0` |
| Línea base (s) — `services/dedicacion-api` | 16.0 |
| Línea base (s) — `services/dedicacion-transfer` | 9.0 |
| Media por mutante evaluado (s) | 6.2 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

