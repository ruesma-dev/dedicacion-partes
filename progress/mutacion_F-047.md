<!-- progress/mutacion_F-047.md -->
# F-047 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-047` el 2026-10-07 18:25.

## Alcance

Origen del diff: **rama** (`622ef0034f6b3646f51d8fb53866772789172397` .. `feature/F-047-tope-filas-transfer`).

| Fichero | Líneas en alcance |
|---|---|
| `services/dedicacion-transfer/config/settings.py` | 5 |
| `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py` | 13 |
| `services/dedicacion-transfer/interface_adapters/api/app.py` | 1 |
| `services/dedicacion-transfer/prueba_escritura_porcentajes.py` | 1 |
| **Total** | **20** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 2 |
| Mutantes evaluados | 2 |
| Muertos | 2 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 27.5 s |
| SHA de HEAD medido | `354ddbba39d4f7281a5a16b9d71e7ed881097c2e` |
| Línea base (s) — `services/dedicacion-transfer` | 8.4 |
| Media por mutante evaluado (s) | 13.7 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

