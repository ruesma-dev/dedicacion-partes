<!-- progress/mutacion_F-054_campana1.md -->
# F-054 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-054` el 2026-10-30 09:50.

## Alcance

Origen del diff: **rama** (`1ed18be235f1f6a196737657f4062b4e10f58b4a` .. `feature/F-054-sync-trae-porcentajes`).

| Fichero | Líneas en alcance |
|---|---|
| `services/dedicacion-api/application/registro_sigrid.py` | 42 |
| `services/dedicacion-api/application/traer_sigrid.py` | 210 |
| `services/dedicacion-api/domain/errors.py` | 7 |
| `services/dedicacion-api/domain/models.py` | 46 |
| `services/dedicacion-api/domain/ports.py` | 35 |
| `services/dedicacion-api/domain/traer_sigrid.py` | 269 |
| `services/dedicacion-api/infrastructure/db/orm_models.py` | 3 |
| `services/dedicacion-api/infrastructure/db/repositories.py` | 58 |
| `services/dedicacion-api/infrastructure/transfer/transfer_client.py` | 59 |
| `services/dedicacion-api/interface_adapters/api/app.py` | 2 |
| `services/dedicacion-api/interface_adapters/api/deps.py` | 5 |
| `services/dedicacion-api/interface_adapters/api/routes.py` | 58 |
| `services/dedicacion-api/interface_adapters/api/schemas.py` | 120 |
| `services/dedicacion-transfer/application/pipelines/poner_a_cero.py` | 129 |
| `services/dedicacion-transfer/application/pipelines/registro_lote.py` | 51 |
| `services/dedicacion-transfer/application/services/lecturas_lote.py` | 45 |
| `services/dedicacion-transfer/application/services/porcentajes_existentes.py` | 140 |
| `services/dedicacion-transfer/application/services/reglas_obra_cero.py` | 148 |
| `services/dedicacion-transfer/domain/models/registro_models.py` | 51 |
| `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py` | 56 |
| `services/dedicacion-transfer/interface_adapters/api/app.py` | 92 |
| **Total** | **1626** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 262 |
| Mutantes evaluados | 262 |
| Muertos | 207 |
| Supervivientes | 55 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 2999.0 s |
| SHA de HEAD medido | `95cc089e7962f72659ebd112437253e581d8c155` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_qhzn3gi9/wk_0/services/dedicacion-api` | 60.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_qhzn3gi9/wk_0/services/dedicacion-transfer` | 34.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_qhzn3gi9/wk_1/services/dedicacion-api` | 60.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_qhzn3gi9/wk_1/services/dedicacion-transfer` | 34.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_qhzn3gi9/wk_2/services/dedicacion-api` | 60.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_qhzn3gi9/wk_2/services/dedicacion-transfer` | 35.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_qhzn3gi9/wk_3/services/dedicacion-api` | 60.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_qhzn3gi9/wk_3/services/dedicacion-transfer` | 35.3 |
| Media por mutante evaluado (s) | 11.4 |
| Timeout efectivo por mutante (s) | 121 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/dedicacion-api/application/registro_sigrid.py:422` [booleano]

- Original: `def _preflight_lote(self, payloads: list[dict], *, completo: bool = False`
- Mutado:   `def _preflight_lote(self, payloads: list[dict], *, completo: bool = True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/dedicacion-api/application/traer_sigrid.py:50` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/dedicacion-api/application/traer_sigrid.py:62` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/dedicacion-api/application/traer_sigrid.py:89` [booleano]

- Original: `admite_postventa=False)`
- Mutado:   `admite_postventa=True)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `services/dedicacion-api/application/traer_sigrid.py:110` [booleano]

- Original: `bool(item.get("es_postventa", False)))`
- Mutado:   `bool(item.get("es_postventa", True)))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `services/dedicacion-api/domain/models.py:392` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `services/dedicacion-api/domain/models.py:408` [booleano]

- Original: `en_registro: bool = False`
- Mutado:   `en_registro: bool = True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `services/dedicacion-api/domain/models.py:412` [entero]

- Original: `paride: int = 0`
- Mutado:   `paride: int = 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 9. `services/dedicacion-api/domain/models.py:422` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 10. `services/dedicacion-api/domain/models.py:428` [entero]

- Original: `lineas_leidas: int = 0`
- Mutado:   `lineas_leidas: int = 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 11. `services/dedicacion-api/domain/models.py:429` [entero]

- Original: `excluidas_pruebas: int = 0`
- Mutado:   `excluidas_pruebas: int = 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 12. `services/dedicacion-api/domain/traer_sigrid.py:55` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 13. `services/dedicacion-api/domain/traer_sigrid.py:67` [entero]

- Original: `hmores_ide: int = 0`
- Mutado:   `hmores_ide: int = 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 14. `services/dedicacion-api/domain/traer_sigrid.py:69` [entero]

- Original: `n_lineas: int = 0`
- Mutado:   `n_lineas: int = 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 15. `services/dedicacion-api/domain/traer_sigrid.py:77` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 16. `services/dedicacion-api/domain/traer_sigrid.py:89` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 17. `services/dedicacion-api/domain/traer_sigrid.py:93` [entero]

- Original: `fuera_maestro: int = 0`
- Mutado:   `fuera_maestro: int = 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 18. `services/dedicacion-api/domain/traer_sigrid.py:94` [entero]

- Original: `de_vinculados: int = 0`
- Mutado:   `de_vinculados: int = 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 19. `services/dedicacion-api/domain/traer_sigrid.py:97` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 20. `services/dedicacion-api/domain/traer_sigrid.py:160` [entero]

- Original: `parides = {int(l.paride or 0) for l in lineas}`
- Mutado:   `parides = {int(l.paride or 1) for l in lineas}`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 21. `services/dedicacion-api/infrastructure/db/repositories.py:412` [booleano]

- Original: `).execution_options(populate_existing=True)`
- Mutado:   `).execution_options(populate_existing=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 22. `services/dedicacion-api/infrastructure/transfer/transfer_client.py:75` [logico]

- Original: `f"sobrantes: {r.get('error') or r}")`
- Mutado:   `f"sobrantes: {r.get('error') and r}")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 23. `services/dedicacion-api/infrastructure/transfer/transfer_client.py:120` [entero]

- Original: `lineas_leidas=int(r.get("lineas_leidas") or 0),`
- Mutado:   `lineas_leidas=int(r.get("lineas_leidas") or 1),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 24. `services/dedicacion-api/infrastructure/transfer/transfer_client.py:121` [entero]

- Original: `excluidas_pruebas=int(r.get("excluidas_pruebas") or 0),`
- Mutado:   `excluidas_pruebas=int(r.get("excluidas_pruebas") or 1),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 25. `services/dedicacion-api/interface_adapters/api/routes.py:590` [not]

- Original: `if not isinstance(valor, list) or not all(`
- Mutado:   `if isinstance(valor, list) or not all(`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 26. `services/dedicacion-api/interface_adapters/api/routes.py:590` [logico]

- Original: `if not isinstance(valor, list) or not all(`
- Mutado:   `if not isinstance(valor, list) and not all(`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 27. `services/dedicacion-api/interface_adapters/api/routes.py:590` [not]

- Original: `if not isinstance(valor, list) or not all(`
- Mutado:   `if not isinstance(valor, list) or all(`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 28. `services/dedicacion-api/interface_adapters/api/routes.py:591` [logico]

- Original: `isinstance(x, dict) and isinstance(x.get("hmores_ide"), int)`
- Mutado:   `isinstance(x, dict) or isinstance(x.get("hmores_ide"), int)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 29. `services/dedicacion-api/interface_adapters/api/routes.py:592` [logico]

- Original: `and not isinstance(x.get("hmores_ide"), bool) for x in valor):`
- Mutado:   `or not isinstance(x.get("hmores_ide"), bool) for x in valor):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 30. `services/dedicacion-api/interface_adapters/api/routes.py:592` [not]

- Original: `and not isinstance(x.get("hmores_ide"), bool) for x in valor):`
- Mutado:   `and isinstance(x.get("hmores_ide"), bool) for x in valor):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 31. `services/dedicacion-api/interface_adapters/api/schemas.py:103` [entero]

- Original: `max_length=5000)`
- Mutado:   `max_length=5001)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 32. `services/dedicacion-api/interface_adapters/api/schemas.py:546` [booleano]

- Original: `propuestas_en_curso: bool = False       # F-055 (R37), R26`
- Mutado:   `propuestas_en_curso: bool = True       # F-055 (R37), R26`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 33. `services/dedicacion-api/interface_adapters/api/schemas.py:566` [entero]

- Original: `n_lineas=e.n_lineas if e else 0, motivo=c.motivo)`
- Mutado:   `n_lineas=e.n_lineas if e else 1, motivo=c.motivo)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 34. `services/dedicacion-transfer/application/pipelines/poner_a_cero.py:65` [entero]

- Original: `if (abs(float(ls.can or 0) - float(p["can"] or 0)) >= _EPS`
- Mutado:   `if (abs(float(ls.can or 1) - float(p["can"] or 0)) >= _EPS`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 35. `services/dedicacion-transfer/application/pipelines/poner_a_cero.py:65` [entero]

- Original: `if (abs(float(ls.can or 0) - float(p["can"] or 0)) >= _EPS`
- Mutado:   `if (abs(float(ls.can or 0) - float(p["can"] or 1)) >= _EPS`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 36. `services/dedicacion-transfer/application/pipelines/poner_a_cero.py:65` [comparacion]

- Original: `if (abs(float(ls.can or 0) - float(p["can"] or 0)) >= _EPS`
- Mutado:   `if (abs(float(ls.can or 0) - float(p["can"] or 0)) > _EPS`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 37. `services/dedicacion-transfer/application/pipelines/poner_a_cero.py:80` [logico]

- Original: `if obra is None or not obra.ide:`
- Mutado:   `if obra is None and not obra.ide:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 38. `services/dedicacion-transfer/application/pipelines/poner_a_cero.py:109` [entero]

- Original: `trazas.append(_traza("pone a 0", 0, ls,`
- Mutado:   `trazas.append(_traza("pone a 0", 1, ls,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 39. `services/dedicacion-transfer/application/pipelines/poner_a_cero.py:112` [booleano]

- Original: `return {"ok": True, "puestas": [], "omitidas": omitidas}`
- Mutado:   `return {"ok": False, "puestas": [], "omitidas": omitidas}`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 40. `services/dedicacion-transfer/application/pipelines/poner_a_cero.py:119` [comparacion]

- Original: `if r is None or abs(float(r.can or 0)) >= _EPS:`
- Mutado:   `if r is None or abs(float(r.can or 0)) > _EPS:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 41. `services/dedicacion-transfer/application/pipelines/registro_lote.py:124` [logico]

- Original: `cod_var=(getattr(self._st, "var_obra_cod", "") or "").strip(),`
- Mutado:   `cod_var=(getattr(self._st, "var_obra_cod", "") and "").strip(),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 42. `services/dedicacion-transfer/application/services/porcentajes_existentes.py:77` [entero]

- Original: `casan = inverso.get(int(linea.paride or 0), [])`
- Mutado:   `casan = inverso.get(int(linea.paride or 1), [])`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 43. `services/dedicacion-transfer/application/services/porcentajes_existentes.py:92` [entero]

- Original: `int(linea.paride or 0), int(desde))`
- Mutado:   `int(linea.paride or 1), int(desde))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 44. `services/dedicacion-transfer/application/services/porcentajes_existentes.py:125` [entero]

- Original: `desde=int(getattr(self._st, "var_partida_desde", 0) or 0),`
- Mutado:   `desde=int(getattr(self._st, "var_partida_desde", 1) or 0),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 45. `services/dedicacion-transfer/application/services/porcentajes_existentes.py:125` [entero]

- Original: `desde=int(getattr(self._st, "var_partida_desde", 0) or 0),`
- Mutado:   `desde=int(getattr(self._st, "var_partida_desde", 0) or 1),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 46. `services/dedicacion-transfer/application/services/reglas_obra_cero.py:39` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 47. `services/dedicacion-transfer/application/services/reglas_obra_cero.py:60` [logico]

- Original: `recurso = a.recurso_ide or (linea.recurso_ide if linea else None)`
- Mutado:   `recurso = a.recurso_ide and (linea.recurso_ide if linea else None)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 48. `services/dedicacion-transfer/application/services/reglas_obra_cero.py:69` [logico]

- Original: `obra, v.destino, int(v.paride or 0),`
- Mutado:   `obra, v.destino, int(v.paride and 0),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 49. `services/dedicacion-transfer/application/services/reglas_obra_cero.py:97` [entero]

- Original: `paride = int(linea.paride or 0)`
- Mutado:   `paride = int(linea.paride or 1)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 50. `services/dedicacion-transfer/application/services/reglas_obra_cero.py:145` [entero]

- Original: `parte_est=l.parte_est, hora=l.hora, paride=int(l.paride or 0),`
- Mutado:   `parte_est=l.parte_est, hora=l.hora, paride=int(l.paride or 1),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 51. `services/dedicacion-transfer/domain/models/registro_models.py:428` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 52. `services/dedicacion-transfer/domain/models/registro_models.py:447` [entero]

- Original: `paride: int = 0`
- Mutado:   `paride: int = 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 53. `services/dedicacion-transfer/domain/models/registro_models.py:453` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 54. `services/dedicacion-transfer/interface_adapters/api/app.py:494` [entero]

- Original: `return JSONResponse(status_code=502,`
- Mutado:   `return JSONResponse(status_code=503,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 55. `services/dedicacion-transfer/interface_adapters/api/app.py:495` [booleano]

- Original: `content={"ok": False, "error": str(exc)})`
- Mutado:   `content={"ok": True, "error": str(exc)})`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

