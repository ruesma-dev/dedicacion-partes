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
feature (primera pasada: suite del transfer con `-x`, restaurando con
`git checkout`). **11 mutantes, 10 muertos, 1 equivalente.**

Rutas relativas a `services/dedicacion-transfer/` (`W` =
`infrastructure/sigrid/sigrid_write_client.py`). Fallos contados el
2026-10-07 sobre una copia (`git archive HEAD` en el scratchpad, nunca en el
árbol de trabajo), suite completa del transfer sin `-x`; línea base 651
passed + 4 skipped. M1, M3, M5, M8 y M10 coinciden con los reproducidos por
el reviewer (`review_F-047.md`).

| # | `fichero:línea` | Original → mutado | Fallos | Lo caza (`test_f047_` salvo indicación) |
|---|---|---|---|---|
| M1 | `W:94` | `"max_rows": self._max_rows})` → `"max_rows": 2000})` | 4 | `a1_el_tope_por_defecto_…`, `a1_el_tope_configurado_…`, `a1_todas_las_lecturas_…`, `a3_obra_con_mas_de_2000_…` |
| M2 | `W:84` | `self._max_rows = int(max_rows)` → `self._max_rows = MAX_ROWS_POR_DEFECTO` | 4 | `a1_el_tope_configurado_…`, `a1_todas_las_lecturas_…`, `a1_el_script_de_pruebas_…`, `a2_una_obra_mayor_que_el_tope_…` |
| M3 | `W:84` | `self._max_rows = int(max_rows)` → `self._max_rows = max_rows` | 1 | `a1_el_tope_configurado_…` |
| M4 | `W:74` | `max_rows: int = MAX_ROWS_POR_DEFECTO,` → `max_rows: int = 2000,` | 2 | `a1_el_tope_por_defecto_…`, `a3_obra_con_mas_de_2000_…` |
| M5 | `W:103` | `raise RuntimeError("sigrid-api devolvio una respuesta truncada")` → `pass` | 2 | `test_f037_r16_read_truncado_lanza`, `a2_una_obra_mayor_que_el_tope_…` |
| M6 | `W:101` | `if body.get("truncated"):` → `if False:` | 2 | `test_f037_r16_read_truncado_lanza`, `a2_una_obra_mayor_que_el_tope_…` |
| M7 | `config/settings.py:30` | `Field(200_000, alias="SIGRID_MAX_ROWS")` → `Field(2000, alias="SIGRID_MAX_ROWS")` | 1 | `a1_ajuste_sigrid_max_rows_…` |
| M8 | `config/settings.py:30` | `alias="SIGRID_MAX_ROWS"` → `alias="SIGRID_API_MAX_ROWS"` | 0 | **sobrevive: equivalente** (abajo) |
| M9 | `interface_adapters/api/app.py:108` | `max_rows=settings.sigrid_max_rows,` → (línea borrada) | 1 | `a1_la_app_inyecta_…` |
| M10 | `prueba_escritura_porcentajes.py:74` | `max_rows=st.sigrid_max_rows,` → (línea borrada) | 1 | `a1_el_script_de_pruebas_…` |
| M11 | `.env.example:10` | `SIGRID_MAX_ROWS=200000` → `SIGRID_MAX_ROWS=2000` | 1 | `a1_env_example_…` |

**M8, equivalente:** con `populate_by_name=True`, pydantic-settings lee la
variable de entorno también por el **nombre del campo** (`sigrid_max_rows`,
sin distinguir mayúsculas), así que `SIGRID_MAX_ROWS` sigue leyéndose aunque
el alias cambie: el test lo pone a 350.000 y lo lee. El contrato documentado
(`SIGRID_MAX_ROWS`) se mantiene; el mutante solo añade un nombre aceptado más.
No es un hueco: ningún comportamiento observable del contrato cambia. Pasa lo
mismo con todos los ajustes del transfer (p. ej. `SIGRID_MAX_STATEMENTS`).

**Aceptada por el humano el 2026-10-07** («1 acepto»), con el matiz del reviewer: el
mutante además honraría `SIGRID_API_MAX_ROWS`; riesgo nulo hoy (infra no declara ninguna).
