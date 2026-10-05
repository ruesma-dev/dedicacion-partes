<!-- progress/mutacion_F-029.md -->
# F-029 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-029` el 2026-10-05 12:35.

## Alcance

Origen del diff: **rama** (`9f20dd55258880388661e826e92e9dfca69fc811` .. `feature/F-029-seleccion-multiple-completar-100`).

| Fichero | Líneas en alcance |
|---|---|
| `services/dedicacion-api/application/use_cases.py` | 126 |
| `services/dedicacion-api/domain/estados.py` | 46 |
| `services/dedicacion-api/domain/models.py` | 31 |
| `services/dedicacion-api/interface_adapters/api/routes.py` | 29 |
| `services/dedicacion-api/interface_adapters/api/schemas.py` | 40 |
| **Total** | **272** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 20 |
| Mutantes evaluados | 20 |
| Muertos | 20 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 398.2 s |
| SHA de HEAD medido | `53e3f7954462d271ca0e47d564702a7752d79755` |
| Línea base (s) — `services/dedicacion-api` | 36.1 |
| Media por mutante evaluado (s) | 19.9 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.


## Historial (añadido por el implementer)

Primera campaña (serie, `--workers 1`, SHA `21ec1ee`, misma semilla y mismos
20 mutantes): 17 muertos, 3 supervivientes.

- `models.py:112` y `:121` (`frozen=True` → `False` en `Completado` y
  `ResultadoCompletarTrabajador`): hueco real y barato. Muertos con
  `test_f029_r25_dominio_resultados_inmutables` (commit `53e3f79`),
  comprobado a mano mutante a mutante antes de relanzar.
- `use_cases.py:380` (`is` → `is not` en YA_AL_100/EXCESO): **falso
  superviviente**. Aplicado a mano en el mismo SHA y con la misma orden
  (`python -m pytest -x -q -p no:cacheprovider`, `PYTHONDONTWRITEBYTECODE=1`,
  desde `services/dedicacion-api`) muere en
  `test_f029_r17_caso_ok_y_exceso_no_se_tocan_ni_dejan_evento` (y en las dos
  rutas de R25/R14). En esta segunda campaña, con el mismo código de
  producción, sale muerto. No se ha encontrado la causa en el arnés: queda
  avisado al líder.
