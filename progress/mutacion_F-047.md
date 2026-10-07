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

## Campaña manual

Añadida a mano por el implementer (no la genera la herramienta). La automática solo generó dos mutantes
(los literales 200.000), así que muté a mano las líneas que sostienen la
feature: suite del transfer con `-x` por mutante, restaurando con
`git checkout` (árbol limpio al final). **11 mutantes, 10 muertos, 1
equivalente:**

| # | Mutación | Lo caza |
|---|---|---|
| M1 | `_read`: `self._max_rows` → `2000` | `a1_..._por_defecto_...` |
| M2 | `self._max_rows = MAX_ROWS_POR_DEFECTO` (ignora el parámetro) | `a1_el_tope_configurado_...` |
| M3 | quitar `int()` | `a1_el_tope_configurado_...` |
| M4 | defecto del constructor → `2000` | `a1_..._por_defecto_...` |
| M5 | `raise` del truncado → `pass` | `test_f037_r16_read_truncado_lanza` |
| M6 | `if body.get("truncated")` → `if False` | `test_f037_r16_read_truncado_lanza` |
| M7 | defecto del ajuste → `2000` | `a1_ajuste_sigrid_max_rows_...` |
| M8 | alias `SIGRID_MAX_ROWS` → `SIGRID_API_MAX_ROWS` | **sobrevive: equivalente** |
| M9 | `build_app` sin `max_rows=` | `a1_la_app_inyecta_...` |
| M10 | script sin `max_rows=` | `a1_el_script_de_pruebas_...` |
| M11 | `.env.example` con `2000` | `a1_env_example_...` |

**M8, equivalente:** con `populate_by_name=True`, pydantic-settings lee la
variable de entorno también por el **nombre del campo** (`sigrid_max_rows`,
sin distinguir mayúsculas), así que `SIGRID_MAX_ROWS` sigue leyéndose aunque
el alias cambie: el test lo pone a 350.000 y lo lee. El contrato documentado
(`SIGRID_MAX_ROWS`) se mantiene; el mutante solo añade un nombre aceptado más.
No es un hueco: ningún comportamiento observable del contrato cambia. Pasa lo
mismo con todos los ajustes del transfer (p. ej. `SIGRID_MAX_STATEMENTS`).
