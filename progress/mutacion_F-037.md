<!-- progress/mutacion_F-037.md -->
# F-037 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-037` el 2026-10-06 11:21.

## Alcance

Origen del diff: **rama** (`1dda05df4b8ba1159029848bc877e4a5d98f5a11` .. `feature/F-037-asiento-analitico-obra`).

| Fichero | Líneas en alcance |
|---|---|
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py` | 176 |
| `services/dedicacion-transfer/application/services/cuenta_analitica.py` | 136 |
| `services/dedicacion-transfer/application/services/estado_parte.py` | 73 |
| `services/dedicacion-transfer/config/settings.py` | 4 |
| `services/dedicacion-transfer/domain/models/registro_models.py` | 46 |
| `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py` | 141 |
| **Total** | **576** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 85 |
| Mutantes evaluados | 85 |
| Muertos | 85 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 423.1 s |
| SHA de HEAD medido | `40b9feb0eda8b697d61799fded994be9b8a7e75e` |
| Línea base (s) — `services/dedicacion-transfer` | 7.9 |
| Media por mutante evaluado (s) | 5.0 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

