<!-- progress/mutacion_F-032.md -->
# F-032 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-032` el 2026-10-01 15:12.

## Alcance

Origen del diff: **rama** (`56e79f3d0c1295ffc29a1f332db6cc8bf7690fa3` .. `feature/F-032-empresas-desde-sigrid`).

| Fichero | Líneas en alcance |
|---|---|
| `services/dedicacion-api/application/filtros_maestros.py` | 32 |
| `services/dedicacion-api/application/sync_pipeline.py` | 42 |
| `services/dedicacion-api/application/use_cases.py` | 35 |
| `services/dedicacion-api/domain/empresas.py` | 13 |
| `services/dedicacion-api/domain/models.py` | 16 |
| `services/dedicacion-api/domain/ports.py` | 14 |
| `services/dedicacion-api/infrastructure/db/orm_models.py` | 25 |
| `services/dedicacion-api/infrastructure/db/repositories.py` | 64 |
| `services/dedicacion-api/interface_adapters/api/deps.py` | 8 |
| `services/dedicacion-api/interface_adapters/api/routes.py` | 5 |
| `services/dedicacion-api/interface_adapters/api/schemas.py` | 4 |
| **Total** | **258** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 30 |
| Mutantes evaluados | 20 |
| Muertos | 18 |
| Supervivientes | 2 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 118.2 s |
| SHA de HEAD medido | `8160220959553e53fce7fddc768d7b6a48b37f7c` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-032_gu_ub9bc/wk_0/services/dedicacion-api` | 18.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-032_gu_ub9bc/wk_1/services/dedicacion-api` | 18.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-032_gu_ub9bc/wk_2/services/dedicacion-api` | 18.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-032_gu_ub9bc/wk_3/services/dedicacion-api` | 18.0 |
| Media por mutante evaluado (s) | 5.9 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | sí — 20 de 30 mutantes, semilla `20260820`, nivel `estandar` |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/dedicacion-api/domain/models.py:92` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (completado por el implementer)

> Por qué ningún test lo caza: ningún test intentaba modificar una `Empresa`;
> todos la construyen y la comparan, que funciona igual con o sin `frozen`.
> Reproducido a mano en una copia aislada (`git archive HEAD`): con
> `frozen=False` la suite del servicio dio `340 passed`.
> Decisión: **hueco real, test nuevo** `test_f032_r2_la_empresa_del_dominio_es_inmutable`
> (asignar un campo lanza `FrozenInstanceError`). Con el mutante aplicado en la
> copia: `1 failed, 341 passed`, falla exactamente ese test. Commit `fe93a43`.

### 2. `services/dedicacion-api/infrastructure/db/orm_models.py:91` [booleano]

- Original: `DateTime(timezone=True), nullable=False, server_default=func.now()`
- Mutado:   `DateTime(timezone=True), nullable=True, server_default=func.now()`

#### Análisis (completado por el implementer)

> Por qué ningún test lo caza: `test_f032_r1_tabla_empresa_declarada_en_el_orm`
> fijaba nombres y tipos de las columnas, no su nulabilidad. Reproducido a mano
> en una copia aislada: con `nullable=True` en `sync_en` la suite dio
> `340 passed`.
> Decisión: **hueco real, test nuevo** `test_f032_r1_nulabilidad_de_la_tabla_empresa`
> (solo `numemp` y `sync_en` son NOT NULL; `sync_en` con `server_default`).
> Con el mutante aplicado en la copia: `1 failed, 341 passed`, falla
> exactamente ese test. No se ha quitado código defensivo (RM6 N/A). Commit `fe93a43`.

