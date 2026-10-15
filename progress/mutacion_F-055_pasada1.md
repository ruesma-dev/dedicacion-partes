<!-- progress/mutacion_F-055_pasada1.md (primera pasada; la final es mutacion_F-055.md) -->
# F-055 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-055` el 2026-10-16 01:33.

## Alcance

Origen del diff: **rama** (`301c5986fb746eacbebdb6509eed8c93837acf73` .. `feature/F-055-preflight-rapido`).

| Fichero | Líneas en alcance |
|---|---|
| `services/dedicacion-api/application/partidas_linea.py` | 12 |
| `services/dedicacion-api/application/propuestas_mes.py` | 194 |
| `services/dedicacion-api/application/registro_sigrid.py` | 61 |
| `services/dedicacion-api/application/use_cases.py` | 19 |
| `services/dedicacion-api/domain/models.py` | 8 |
| `services/dedicacion-api/domain/ports.py` | 14 |
| `services/dedicacion-api/infrastructure/db/orm_models.py` | 10 |
| `services/dedicacion-api/infrastructure/db/repositories.py` | 45 |
| `services/dedicacion-api/infrastructure/transfer/transfer_client.py` | 18 |
| `services/dedicacion-api/interface_adapters/api/deps.py` | 11 |
| `services/dedicacion-api/interface_adapters/api/routes.py` | 47 |
| `services/dedicacion-api/interface_adapters/api/schemas.py` | 32 |
| `services/dedicacion-transfer/application/pipelines/registro_lote.py` | 77 |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py` | 83 |
| `services/dedicacion-transfer/application/services/lecturas_lote.py` | 426 |
| `services/dedicacion-transfer/application/services/propuesta_partida.py` | 19 |
| `services/dedicacion-transfer/config/settings.py` | 5 |
| `services/dedicacion-transfer/domain/models/registro_models.py` | 29 |
| `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py` | 270 |
| `services/dedicacion-transfer/interface_adapters/api/app.py` | 112 |
| `services/dedicacion-transfer/prueba_escritura_porcentajes.py` | 83 |
| **Total** | **1575** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 281 |
| Mutantes evaluados | 281 |
| Muertos | 242 |
| Supervivientes | 39 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 4486.5 s |
| SHA de HEAD medido | `68a5c6bdde7deda1b2c11f9864dcab889f55bf51` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-055_mpf_2f8c/wk_0/services/dedicacion-api` | 85.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-055_mpf_2f8c/wk_0/services/dedicacion-transfer` | 147.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-055_mpf_2f8c/wk_1/services/dedicacion-api` | 86.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-055_mpf_2f8c/wk_1/services/dedicacion-transfer` | 145.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-055_mpf_2f8c/wk_2/services/dedicacion-api` | 82.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-055_mpf_2f8c/wk_2/services/dedicacion-transfer` | 149.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-055_mpf_2f8c/wk_3/services/dedicacion-api` | 85.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-055_mpf_2f8c/wk_3/services/dedicacion-transfer` | 149.0 |
| Media por mutante evaluado (s) | 16.0 |
| Timeout efectivo por mutante (s) | 299 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/dedicacion-api/application/propuestas_mes.py:149` [booleano]

- Original: `mes, anio, exc_info=True)`
- Mutado:   `mes, anio, exc_info=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/dedicacion-api/domain/ports.py:141` [booleano]

- Original: `solo_si_vacia: bool = False,`
- Mutado:   `solo_si_vacia: bool = True,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/dedicacion-api/infrastructure/db/repositories.py:439` [booleano]

- Original: `solo_si_vacia: bool = False,`
- Mutado:   `solo_si_vacia: bool = True,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/dedicacion-api/infrastructure/transfer/transfer_client.py:69` [logico]

- Original: `causa = r.get("error") or "la respuesta del transfer no trae obras"`
- Mutado:   `causa = r.get("error") and "la respuesta del transfer no trae obras"`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `services/dedicacion-api/interface_adapters/api/routes.py:90` [booleano]

- Original: `mes, anio, exc_info=True)`
- Mutado:   `mes, anio, exc_info=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `services/dedicacion-api/interface_adapters/api/schemas.py:140` [booleano]

- Original: `propuestas_en_curso: bool = False`
- Mutado:   `propuestas_en_curso: bool = True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `services/dedicacion-api/interface_adapters/api/schemas.py:177` [booleano]

- Original: `propuestas_en_curso: bool = False`
- Mutado:   `propuestas_en_curso: bool = True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `services/dedicacion-api/interface_adapters/api/schemas.py:191` [booleano]

- Original: `propuestas_en_curso: bool = False       # F-055 (R37)`
- Mutado:   `propuestas_en_curso: bool = True       # F-055 (R37)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 9. `services/dedicacion-api/interface_adapters/api/schemas.py:206` [booleano]

- Original: `propuestas_en_curso: bool = False       # F-055 (R37)`
- Mutado:   `propuestas_en_curso: bool = True       # F-055 (R37)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 10. `services/dedicacion-transfer/application/services/lecturas_lote.py:162` [comparacion]

- Original: `if empresas[i] == emp for l in ls):`
- Mutado:   `if empresas[i] != emp for l in ls):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 11. `services/dedicacion-transfer/application/services/lecturas_lote.py:163` [logico]

- Original: `var = (settings.var_obra_cod or "").strip()`
- Mutado:   `var = (settings.var_obra_cod and "").strip()`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 12. `services/dedicacion-transfer/application/services/lecturas_lote.py:197` [logico]

- Original: `if pv is not None and any(l.es_postventa for l in ls):`
- Mutado:   `if pv is not None or any(l.es_postventa for l in ls):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 13. `services/dedicacion-transfer/application/services/lecturas_lote.py:218` [logico]

- Original: `if not l.es_postventa and l.var_paride is None]`
- Mutado:   `if not l.es_postventa or l.var_paride is None]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 14. `services/dedicacion-transfer/application/services/lecturas_lote.py:226` [logico]

- Original: `l.paride or l.propuesta_paride or l.var_paride for l in todas`
- Mutado:   `l.paride or l.propuesta_paride and l.var_paride for l in todas`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 15. `services/dedicacion-transfer/application/services/lecturas_lote.py:234` [logico]

- Original: `if hmoides and resides:`
- Mutado:   `if hmoides or resides:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 16. `services/dedicacion-transfer/application/services/lecturas_lote.py:249` [not]

- Original: `if not o.ide and o.codigo:`
- Mutado:   `if o.ide and o.codigo:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 17. `services/dedicacion-transfer/application/services/lecturas_lote.py:249` [logico]

- Original: `if not o.ide and o.codigo:`
- Mutado:   `if not o.ide or o.codigo:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 18. `services/dedicacion-transfer/application/services/lecturas_lote.py:299` [logico]

- Original: `if self._horas is None or not recurso:`
- Mutado:   `if self._horas is None and not recurso:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 19. `services/dedicacion-transfer/application/services/lecturas_lote.py:300` [booleano]

- Original: `return False`
- Mutado:   `return True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 20. `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py:95` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 21. `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py:581` [logico]

- Original: `ide=int(f["ide"]), reside=int(f["reside"] or 0),`
- Mutado:   `ide=int(f["ide"]), reside=int(f["reside"] and 0),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 22. `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py:581` [entero]

- Original: `ide=int(f["ide"]), reside=int(f["reside"] or 0),`
- Mutado:   `ide=int(f["ide"]), reside=int(f["reside"] or 1),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 23. `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py:582` [logico]

- Original: `fecha_int=int(f["fec"] or 0),`
- Mutado:   `fecha_int=int(f["fec"] and 0),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 24. `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py:582` [entero]

- Original: `fecha_int=int(f["fec"] or 0),`
- Mutado:   `fecha_int=int(f["fec"] or 1),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 25. `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py:583` [logico]

- Original: `horide=int(f["horide"] or 0) or None,`
- Mutado:   `horide=int(f["horide"] and 0) or None,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 26. `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py:583` [entero]

- Original: `horide=int(f["horide"] or 0) or None,`
- Mutado:   `horide=int(f["horide"] or 1) or None,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 27. `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py:583` [logico]

- Original: `horide=int(f["horide"] or 0) or None,`
- Mutado:   `horide=int(f["horide"] or 0) and None,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 28. `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py:587` [logico]

- Original: `paride=int(f["paride"] or 0))`
- Mutado:   `paride=int(f["paride"] and 0))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 29. `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py:587` [entero]

- Original: `paride=int(f["paride"] or 0))`
- Mutado:   `paride=int(f["paride"] or 1))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 30. `services/dedicacion-transfer/interface_adapters/api/app.py:154` [booleano]

- Original: `"ok": True,`
- Mutado:   `"ok": False,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 31. `services/dedicacion-transfer/prueba_escritura_porcentajes.py:73` [entero]

- Original: `REGISTRO_MEDIR = 990000`
- Mutado:   `REGISTRO_MEDIR = 990001`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 32. `services/dedicacion-transfer/prueba_escritura_porcentajes.py:302` [entero]

- Original: `porcentaje = round(1 / len(obras), 4)`
- Mutado:   `porcentaje = round(2 / len(obras), 4)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 33. `services/dedicacion-transfer/prueba_escritura_porcentajes.py:302` [entero]

- Original: `porcentaje = round(1 / len(obras), 4)`
- Mutado:   `porcentaje = round(1 / len(obras), 5)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 34. `services/dedicacion-transfer/prueba_escritura_porcentajes.py:308` [aritmetico]

- Original: `registro_id=REGISTRO_MEDIR + 100 * i + j, ano=ano, mes=mes,`
- Mutado:   `registro_id=REGISTRO_MEDIR - 100 * i + j, ano=ano, mes=mes,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 35. `services/dedicacion-transfer/prueba_escritura_porcentajes.py:308` [entero]

- Original: `registro_id=REGISTRO_MEDIR + 100 * i + j, ano=ano, mes=mes,`
- Mutado:   `registro_id=REGISTRO_MEDIR + 101 * i + j, ano=ano, mes=mes,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 36. `services/dedicacion-transfer/prueba_escritura_porcentajes.py:308` [aritmetico]

- Original: `registro_id=REGISTRO_MEDIR + 100 * i + j, ano=ano, mes=mes,`
- Mutado:   `registro_id=REGISTRO_MEDIR + 100 * i - j, ano=ano, mes=mes,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 37. `services/dedicacion-transfer/prueba_escritura_porcentajes.py:319` [aritmetico]

- Original: `segundos = time.perf_counter() - t_obra`
- Mutado:   `segundos = time.perf_counter() + t_obra`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 38. `services/dedicacion-transfer/prueba_escritura_porcentajes.py:321` [comparacion]

- Original: `filas = "error" if x.filas is None else f"{x.filas} filas"`
- Mutado:   `filas = "error" if x.filas is not None else f"{x.filas} filas"`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 39. `services/dedicacion-transfer/prueba_escritura_porcentajes.py:330` [aritmetico]

- Original: `f"{time.perf_counter() - t0:.2f} s en total")`
- Mutado:   `f"{time.perf_counter() + t0:.2f} s en total")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

