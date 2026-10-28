<!-- progress/mutacion_F-068.md -->
# F-068 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-068` el 2026-10-28 17:10.

## Alcance

Origen del diff: **rama** (`d95b3ab4a373230aed65fa7493941dd29c862357` .. `feature/F-068-propuesta-vinculado-como-titular`).

| Fichero | Líneas en alcance |
|---|---|
| `services/dedicacion-api/application/partidas_linea.py` | 14 |
| `services/dedicacion-api/application/registro_sigrid.py` | 9 |
| `services/dedicacion-api/domain/models.py` | 4 |
| `services/dedicacion-api/infrastructure/db/repositories.py` | 2 |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py` | 16 |
| `services/dedicacion-transfer/application/pipelines/registro_vinculados.py` | 66 |
| `services/dedicacion-transfer/application/services/lecturas_lote.py` | 11 |
| `services/dedicacion-transfer/application/services/reglas_vinculados.py` | 170 |
| `services/dedicacion-transfer/domain/models/registro_models.py` | 3 |
| `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py` | 46 |
| `services/dedicacion-transfer/interface_adapters/api/app.py` | 18 |
| **Total** | **359** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 54 |
| Mutantes evaluados | 54 |
| Muertos | 53 |
| Supervivientes | 1 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 1405.8 s |
| SHA de HEAD medido | `cd8f0be709461c91e774e65bb99e1b77f28f76cc` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-068_awadc_hg/wk_0/services/dedicacion-api` | 132.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-068_awadc_hg/wk_0/services/dedicacion-transfer` | 75.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-068_awadc_hg/wk_1/services/dedicacion-api` | 131.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-068_awadc_hg/wk_1/services/dedicacion-transfer` | 75.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-068_awadc_hg/wk_2/services/dedicacion-transfer` | 88.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-068_awadc_hg/wk_3/services/dedicacion-transfer` | 90.1 |
| Media por mutante evaluado (s) | 26.0 |
| Timeout efectivo por mutante (s) | 266 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:202` [booleano]

- Original: `p = partida_del_vinculado(titular, None, True, ci, previa)`
- Mutado:   `p = partida_del_vinculado(titular, None, False, ci, previa)`

#### Análisis (implementer)

> Por qué ningún test lo caza: `partida_del_vinculado` solo lee `elegida_valida` dentro de `if elegida is not None`, y en `proponer` (el selector y la cola) `elegida` es siempre `None`: la propuesta no tiene elegida. El valor es indiferente. Es el MISMO mutante que el nº 4 de `progress/mutacion_F-044.md` (la línea solo gana el argumento `previa` de F-068).
> Decisión: mutante equivalente (argumento no leído con `elegida=None`). Aceptado por el humano para F-044 el 2026-10-26 («1 ok»); **aceptado por el humano para F-068 el 2026-10-28** («acepto como equivalente»; rigor crítico: `supervivientes_maximos` 0).


## Campaña 1 (antes de esta)

Sobre `e28dbd2ac4f827fdc870285ae39c5f2bd037bb4b`: 56 mutantes, 51 muertos, 5 supervivientes, 0 timeouts, 1149,7 s, 4 workers. Tratamiento (commit `cd8f0be`):

- `registro_pipeline.py:756` `else (0, 0)` → `(0, 1)` y → `(1, 0)` (2): la ventana sin vinculados no se usaba (equivalentes). Se quitan de raíz: `decidir` recibe `ventana`, un invocable que solo se llama si se lee el historial; la constante desaparece.
- `reglas_vinculados.py:263` `max(round(v, 6) …)` → `round(v, 7)` y `:265` `if round(v, 6) == mejor` → `round(v, 7)` (2): ningún test daba un casi-empate. Los mata `test_f068_r7_el_empate_es_el_del_maximo_unico_a_6_decimales` (casador falso con la forma de `PartidaMatch`; comprobado a mano con el mutante de `:265`: `1 failed`).
- `registro_vinculados.py:202` (1): el equivalente de arriba.
