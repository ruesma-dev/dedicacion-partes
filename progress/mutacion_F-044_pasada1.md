<!-- progress/mutacion_F-044_pasada1.md (primera pasada; la final es mutacion_F-044.md) -->
# F-044 · Campaña de mutación (primera pasada)

> **Resueltos en T22:** de los 81 supervivientes de esta pasada, 74 tienen un test que los mata (`tests/test_f044_mutacion.py` de la api y del transfer) y 7 son equivalentes. La comprobación, mutante a mutante (aplicado en el worktree, solo esos dos ficheros de tests, `git checkout` después), va en el anexo del final; el análisis de los equivalentes, en la pasada final, `progress/mutacion_F-044.md`. Las secciones «PENDIENTE» de abajo son históricas.

Generado por `python -m harness.mutacion --feature F-044` el 2026-10-26 15:40.

## Alcance

Origen del diff: **rama** (`ba6b575457aa725d61112ddc22b51bea670fd52a` .. `feature/F-044-recursos-vinculados`).

| Fichero | Líneas en alcance |
|---|---|
| `services/dedicacion-api/application/partidas_linea.py` | 85 |
| `services/dedicacion-api/application/propuestas_mes.py` | 142 |
| `services/dedicacion-api/application/registro_sigrid.py` | 96 |
| `services/dedicacion-api/application/sync_pipeline.py` | 116 |
| `services/dedicacion-api/application/traza_vinculados.py` | 57 |
| `services/dedicacion-api/application/use_cases.py` | 109 |
| `services/dedicacion-api/domain/models.py` | 55 |
| `services/dedicacion-api/domain/ports.py` | 15 |
| `services/dedicacion-api/domain/vinculados.py` | 98 |
| `services/dedicacion-api/infrastructure/db/orm_models.py` | 81 |
| `services/dedicacion-api/infrastructure/db/repositories.py` | 245 |
| `services/dedicacion-api/infrastructure/sigrid/sigrid_client.py` | 5 |
| `services/dedicacion-api/interface_adapters/api/deps.py` | 15 |
| `services/dedicacion-api/interface_adapters/api/routes.py` | 8 |
| `services/dedicacion-api/interface_adapters/api/schemas.py` | 37 |
| `services/dedicacion-transfer/application/pipelines/registro_lote.py` | 4 |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py` | 132 |
| `services/dedicacion-transfer/application/pipelines/registro_vinculados.py` | 713 |
| `services/dedicacion-transfer/application/services/lecturas_lote.py` | 39 |
| `services/dedicacion-transfer/application/services/reglas_porcentajes.py` | 60 |
| `services/dedicacion-transfer/application/services/reglas_vinculados.py` | 286 |
| `services/dedicacion-transfer/domain/models/registro_models.py` | 79 |
| `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py` | 28 |
| `services/dedicacion-transfer/interface_adapters/api/app.py` | 79 |
| `services/dedicacion-transfer/prueba_escritura_porcentajes.py` | 19 |
| **Total** | **2603** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 422 |
| Mutantes evaluados | 422 |
| Muertos | 341 |
| Supervivientes | 81 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 3355.1 s |
| SHA de HEAD medido | `bd38dc5e36f5db069738392a6f95353cf00f0a9d` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-044_jzsywjtf/wk_0/services/dedicacion-api` | 76.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-044_jzsywjtf/wk_0/services/dedicacion-transfer` | 41.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-044_jzsywjtf/wk_1/services/dedicacion-api` | 77.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-044_jzsywjtf/wk_1/services/dedicacion-transfer` | 40.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-044_jzsywjtf/wk_2/services/dedicacion-api` | 77.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-044_jzsywjtf/wk_2/services/dedicacion-transfer` | 40.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-044_jzsywjtf/wk_3/services/dedicacion-api` | 77.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-044_jzsywjtf/wk_3/services/dedicacion-transfer` | 40.1 |
| Media por mutante evaluado (s) | 8.0 |
| Timeout efectivo por mutante (s) | 155 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/dedicacion-api/application/propuestas_mes.py:100` [entero]

- Original: `subfilas = any(c[0] == periodo_id for c in self._en_cola_sub)`
- Mutado:   `subfilas = any(c[1] == periodo_id for c in self._en_cola_sub)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/dedicacion-api/application/propuestas_mes.py:100` [comparacion]

- Original: `subfilas = any(c[0] == periodo_id for c in self._en_cola_sub)`
- Mutado:   `subfilas = any(c[0] != periodo_id for c in self._en_cola_sub)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/dedicacion-api/application/propuestas_mes.py:327` [comparacion]

- Original: `if v.propuesta_ide is not None and v.partida_ide is None]`
- Mutado:   `if v.propuesta_ide is None and v.partida_ide is None]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/dedicacion-api/application/propuestas_mes.py:327` [logico]

- Original: `if v.propuesta_ide is not None and v.partida_ide is None]`
- Mutado:   `if v.propuesta_ide is not None or v.partida_ide is None]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `services/dedicacion-api/application/propuestas_mes.py:327` [comparacion]

- Original: `if v.propuesta_ide is not None and v.partida_ide is None]`
- Mutado:   `if v.propuesta_ide is not None and v.partida_ide is not None]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `services/dedicacion-api/application/sync_pipeline.py:81` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `services/dedicacion-api/application/sync_pipeline.py:112` [entero]

- Original: `if (len(partes) == 2 and len(partes[0]) == 4 and partes[0].isdigit()`
- Mutado:   `if (len(partes) == 2 and len(partes[0]) == 4 and partes[1].isdigit()`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `services/dedicacion-api/application/sync_pipeline.py:113` [entero]

- Original: `and partes[1].isdigit() and 1 <= int(partes[1]) <= 12):`
- Mutado:   `and partes[1].isdigit() and 2 <= int(partes[1]) <= 12):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 9. `services/dedicacion-api/application/sync_pipeline.py:113` [comparacion]

- Original: `and partes[1].isdigit() and 1 <= int(partes[1]) <= 12):`
- Mutado:   `and partes[1].isdigit() and 1 < int(partes[1]) <= 12):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 10. `services/dedicacion-api/application/sync_pipeline.py:113` [comparacion]

- Original: `and partes[1].isdigit() and 1 <= int(partes[1]) <= 12):`
- Mutado:   `and partes[1].isdigit() and 1 <= int(partes[1]) < 12):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 11. `services/dedicacion-api/application/traza_vinculados.py:35` [comparacion]

- Original: `select(AsignacionORM.id).where(AsignacionORM.id == int(rid)),`
- Mutado:   `select(AsignacionORM.id).where(AsignacionORM.id != int(rid)),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 12. `services/dedicacion-api/domain/models.py:65` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 13. `services/dedicacion-api/domain/models.py:84` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 14. `services/dedicacion-api/infrastructure/db/orm_models.py:341` [booleano]

- Original: `activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)`
- Mutado:   `activo: Mapped[bool] = mapped_column(Boolean, nullable=True, default=True)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 15. `services/dedicacion-api/infrastructure/db/orm_models.py:341` [booleano]

- Original: `activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)`
- Mutado:   `activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 16. `services/dedicacion-api/infrastructure/db/orm_models.py:342` [booleano]

- Original: `estado_vinculo: Mapped[str] = mapped_column(Text, nullable=False)`
- Mutado:   `estado_vinculo: Mapped[str] = mapped_column(Text, nullable=True)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 17. `services/dedicacion-api/infrastructure/db/orm_models.py:344` [booleano]

- Original: `DateTime(timezone=True), nullable=False, server_default=func.now(),`
- Mutado:   `DateTime(timezone=False), nullable=False, server_default=func.now(),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 18. `services/dedicacion-api/infrastructure/db/orm_models.py:344` [booleano]

- Original: `DateTime(timezone=True), nullable=False, server_default=func.now(),`
- Mutado:   `DateTime(timezone=True), nullable=True, server_default=func.now(),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 19. `services/dedicacion-api/infrastructure/db/orm_models.py:370` [booleano]

- Original: `ForeignKey("asignacion.id", ondelete="CASCADE"), nullable=False`
- Mutado:   `ForeignKey("asignacion.id", ondelete="CASCADE"), nullable=True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 20. `services/dedicacion-api/infrastructure/db/orm_models.py:373` [booleano]

- Original: `ForeignKey("recurso_vinculado.ide"), nullable=False`
- Mutado:   `ForeignKey("recurso_vinculado.ide"), nullable=True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 21. `services/dedicacion-api/infrastructure/db/orm_models.py:384` [entero]

- Original: `sigrid_estado: Mapped[str | None] = mapped_column(String(16))`
- Mutado:   `sigrid_estado: Mapped[str | None] = mapped_column(String(17))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 22. `services/dedicacion-api/infrastructure/db/orm_models.py:386` [entero]

- Original: `sigrid_parte: Mapped[str | None] = mapped_column(String(24))`
- Mutado:   `sigrid_parte: Mapped[str | None] = mapped_column(String(25))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 23. `services/dedicacion-api/infrastructure/db/repositories.py:533` [booleano]

- Original: `for linea, orm in zip(lineas, creadas, strict=True)`
- Mutado:   `for linea, orm in zip(lineas, creadas, strict=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 24. `services/dedicacion-api/infrastructure/db/repositories.py:549` [booleano]

- Original: `solo_si_vacia: bool = False,`
- Mutado:   `solo_si_vacia: bool = True,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 25. `services/dedicacion-api/interface_adapters/api/routes.py:357` [entero]

- Original: `vinculado_ide: Annotated[int | None, Query(gt=0)] = None,`
- Mutado:   `vinculado_ide: Annotated[int | None, Query(gt=1)] = None,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 26. `services/dedicacion-api/interface_adapters/api/schemas.py:78` [entero]

- Original: `vinculado_ide: int | None = Field(default=None, gt=0)`
- Mutado:   `vinculado_ide: int | None = Field(default=None, gt=1)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 27. `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:274` [booleano]

- Original: `vinculados=[av for a, l in zip(acciones, lineas, strict=True)`
- Mutado:   `vinculados=[av for a, l in zip(acciones, lineas, strict=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 28. `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:645` [logico]

- Original: `if a.accion == "escribir" and a.destino != "postventa"`
- Mutado:   `if a.accion == "escribir" or a.destino != "postventa"`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 29. `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:761` [logico]

- Original: `if escribir or inc_escribir or vin_escribir:`
- Mutado:   `if escribir or inc_escribir and vin_escribir:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 30. `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:1412` [logico]

- Original: `p, d, f"Parte {d.nombre or d.codigo}{marca}"),`
- Mutado:   `p, d, f"Parte {d.nombre and d.codigo}{marca}"),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 31. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:188` [booleano]

- Original: `p = partida_del_vinculado(titular, None, True, ci)`
- Mutado:   `p = partida_del_vinculado(titular, None, False, ci)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 32. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:219` [entero]

- Original: `destino=a.destino, paride=int(a.paride or 0),`
- Mutado:   `destino=a.destino, paride=int(a.paride or 1),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 33. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:223` [booleano]

- Original: `strict=True):`
- Mutado:   `strict=False):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 34. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:239` [logico]

- Original: `return (bool(nodo and nodo.es_hoja and nodo.activa),`
- Mutado:   `return (bool(nodo or nodo.es_hoja and nodo.activa),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 35. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:239` [logico]

- Original: `return (bool(nodo and nodo.es_hoja and nodo.activa),`
- Mutado:   `return (bool(nodo and nodo.es_hoja or nodo.activa),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 36. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:252` [booleano]

- Original: `elegida, valida = None, True`
- Mutado:   `elegida, valida = None, False`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 37. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:257` [logico]

- Original: `elif (v.propuesta_paride and v.propuesta_metodo == METODO_CI_TIPO`
- Mutado:   `elif (v.propuesta_paride or v.propuesta_metodo == METODO_CI_TIPO`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 38. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:264` [logico]

- Original: `av.partida_res = v.propuesta_res or res`
- Mutado:   `av.partida_res = v.propuesta_res and res`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 39. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:303` [entero]

- Original: `or 0))`
- Mutado:   `or 1))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 40. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:305` [logico]

- Original: `or not es_de_la_hora(hit, av.hora_codigo)`
- Mutado:   `and not es_de_la_hora(hit, av.hora_codigo)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 41. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:306` [logico]

- Original: `or es_nuestra_de_otra(hit.synckey, propia)):`
- Mutado:   `and es_nuestra_de_otra(hit.synckey, propia)):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 42. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:369` [comparacion]

- Original: `if ls.reside == av.recurso_ide`
- Mutado:   `if ls.reside != av.recurso_ide`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 43. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:370` [logico]

- Original: `and ls not in choques`
- Mutado:   `or ls not in choques`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 44. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:371` [logico]

- Original: `and es_de_la_hora(ls, av.hora_codigo)`
- Mutado:   `or es_de_la_hora(ls, av.hora_codigo)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 45. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:372` [logico]

- Original: `and ls.ide not in suyas],`
- Mutado:   `or ls.ide not in suyas],`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 46. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:385` [logico]

- Original: `and clave_de(av) not in en_pisado],`
- Mutado:   `or clave_de(av) not in en_pisado],`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 47. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:412` [entero]

- Original: `motivo="sobrecarga", suma_existente=round(cap.existente, 4),`
- Mutado:   `motivo="sobrecarga", suma_existente=round(cap.existente, 5),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 48. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:413` [entero]

- Original: `suma_total=round(cap.total, 4), exceso=round(cap.exceso, 4),`
- Mutado:   `suma_total=round(cap.total, 5), exceso=round(cap.exceso, 4),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 49. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:413` [entero]

- Original: `suma_total=round(cap.total, 4), exceso=round(cap.exceso, 4),`
- Mutado:   `suma_total=round(cap.total, 4), exceso=round(cap.exceso, 5),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 50. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:436` [comparacion]

- Original: `partida = (av.partida_cod if ls.paride == av.paride`
- Mutado:   `partida = (av.partida_cod if ls.paride != av.paride`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 51. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:470` [logico]

- Original: `tipo, cod = (c.vinculado or {}).get("tipo"), (c.vinculado or {}).get(`
- Mutado:   `tipo, cod = (c.vinculado and {}).get("tipo"), (c.vinculado or {}).get(`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 52. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:470` [logico]

- Original: `tipo, cod = (c.vinculado or {}).get("tipo"), (c.vinculado or {}).get(`
- Mutado:   `tipo, cod = (c.vinculado or {}).get("tipo"), (c.vinculado and {}).get(`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 53. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:474` [comparacion]

- Original: `if c.motivo == "sobrecarga":`
- Mutado:   `if c.motivo != "sobrecarga":`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 54. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:477` [booleano]

- Original: `existente=c.suma_existente, nueva=c.nueva_can), True`
- Mutado:   `existente=c.suma_existente, nueva=c.nueva_can), False`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 55. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:559` [logico]

- Original: `"hora_codigo": av.hora_codigo, "paride": int(av.paride or 0),`
- Mutado:   `"hora_codigo": av.hora_codigo, "paride": int(av.paride and 0),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 56. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:559` [entero]

- Original: `"hora_codigo": av.hora_codigo, "paride": int(av.paride or 0),`
- Mutado:   `"hora_codigo": av.hora_codigo, "paride": int(av.paride or 1),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 57. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:560` [logico]

- Original: `"caaide": int(av.caa_ide or 0), "fecha_int": av.fecha_int,`
- Mutado:   `"caaide": int(av.caa_ide and 0), "fecha_int": av.fecha_int,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 58. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:560` [entero]

- Original: `"caaide": int(av.caa_ide or 0), "fecha_int": av.fecha_int,`
- Mutado:   `"caaide": int(av.caa_ide or 1), "fecha_int": av.fecha_int,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 59. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:561` [comparacion]

- Original: `"synckey": sk, "tex": ls.tex if self._tex is None`
- Mutado:   `"synckey": sk, "tex": ls.tex if self._tex is not None`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 60. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:567` [logico]

- Original: `paride=int(av.paride or 0), caaide=int(av.caa_ide or 0),`
- Mutado:   `paride=int(av.paride and 0), caaide=int(av.caa_ide or 0),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 61. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:567` [entero]

- Original: `paride=int(av.paride or 0), caaide=int(av.caa_ide or 0),`
- Mutado:   `paride=int(av.paride or 1), caaide=int(av.caa_ide or 0),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 62. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:567` [logico]

- Original: `paride=int(av.paride or 0), caaide=int(av.caa_ide or 0),`
- Mutado:   `paride=int(av.paride or 0), caaide=int(av.caa_ide and 0),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 63. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:567` [entero]

- Original: `paride=int(av.paride or 0), caaide=int(av.caa_ide or 0),`
- Mutado:   `paride=int(av.paride or 0), caaide=int(av.caa_ide or 1),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 64. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:603` [logico]

- Original: `and (x.ano, x.mes) == (av.ano, av.mes))`
- Mutado:   `or (x.ano, x.mes) == (av.ano, av.mes))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 65. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:604` [logico]

- Original: `if not (p.existe and p.ide):`
- Mutado:   `if not (p.existe or p.ide):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 66. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:609` [aritmetico]

- Original: `pos[hmoide] += self._paso`
- Mutado:   `pos[hmoide] -= self._paso`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 67. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:616` [entero]

- Original: `paride=int(av.paride or 0), caaide=int(av.caa_ide or 0)))`
- Mutado:   `paride=int(av.paride or 0), caaide=int(av.caa_ide or 1)))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 68. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:636` [logico]

- Original: `if not c.vinculado or c.clave not in pisar or not regs:`
- Mutado:   `if not c.vinculado and c.clave not in pisar or not regs:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 69. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:636` [logico]

- Original: `if not c.vinculado or c.clave not in pisar or not regs:`
- Mutado:   `if not c.vinculado or c.clave not in pisar and not regs:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 70. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:663` [logico]

- Original: `if (ls is None or ls.enlazada`
- Mutado:   `if (ls is None and ls.enlazada`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 71. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:664` [logico]

- Original: `or not es_de_la_hora(ls, av.hora_codigo)`
- Mutado:   `and not es_de_la_hora(ls, av.hora_codigo)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 72. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:665` [logico]

- Original: `or ls.parte_est != self._est):`
- Mutado:   `and ls.parte_est != self._est):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 73. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:666` [booleano]

- Original: `return False`
- Mutado:   `return True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 74. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:688` [logico]

- Original: `if hit is None or abs(float(hit.can or 0.0)`
- Mutado:   `if hit is None and abs(float(hit.can or 0.0)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 75. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:689` [comparacion]

- Original: `- t["despues"]["can"]) >= 0.000001 \`
- Mutado:   `- t["despues"]["can"]) > 0.000001 \`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 76. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:690` [logico]

- Original: `or (hit.synckey or "").strip() != t["despues"]["synckey"]:`
- Mutado:   `and (hit.synckey or "").strip() != t["despues"]["synckey"]:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 77. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:700` [logico]

- Original: `if hit is None or float(hit.can or 0.0) != 0.0:`
- Mutado:   `if hit is None and float(hit.can or 0.0) != 0.0:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 78. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:700` [logico]

- Original: `if hit is None or float(hit.can or 0.0) != 0.0:`
- Mutado:   `if hit is None or float(hit.can and 0.0) != 0.0:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 79. `services/dedicacion-transfer/application/services/reglas_vinculados.py:88` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 80. `services/dedicacion-transfer/application/services/reglas_vinculados.py:278` [logico]

- Original: `return _POR_QUE_SIN_CI.get(motivo or "", motivo or "")`
- Mutado:   `return _POR_QUE_SIN_CI.get(motivo and "", motivo or "")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 81. `services/dedicacion-transfer/application/services/reglas_vinculados.py:278` [logico]

- Original: `return _POR_QUE_SIN_CI.get(motivo or "", motivo or "")`
- Mutado:   `return _POR_QUE_SIN_CI.get(motivo or "", motivo and "")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?


## Anexo: comprobación uno a uno (implementer, 2026-10-26)

`MUERTO`: el test nuevo de su servicio falla con el mutante aplicado; `VIVE`: equivalente (análisis en `mutacion_F-044.md`).

```
MUERTO api/application/propuestas_mes.py:100 [entero] subfilas = any(c[1] == periodo_id for c in self._en_cola_sub)
MUERTO api/application/propuestas_mes.py:100 [comparacion] subfilas = any(c[0] != periodo_id for c in self._en_cola_sub)
MUERTO api/application/propuestas_mes.py:327 [comparacion] if v.propuesta_ide is not None and v.partida_ide is not None]
MUERTO api/application/propuestas_mes.py:327 [logico] if v.propuesta_ide is not None or v.partida_ide is None]
MUERTO api/application/propuestas_mes.py:327 [comparacion] if v.propuesta_ide is None and v.partida_ide is None]
MUERTO api/application/sync_pipeline.py:81 [booleano] @dataclass(frozen=False)
MUERTO api/application/traza_vinculados.py:35 [comparacion] select(AsignacionORM.id).where(AsignacionORM.id != int(rid)),
MUERTO api/application/sync_pipeline.py:113 [comparacion] and partes[1].isdigit() and 1 < int(partes[1]) <= 12):
MUERTO api/application/sync_pipeline.py:112 [entero] if (len(partes) == 2 and len(partes[0]) == 4 and partes[1].isdigit()
MUERTO api/application/sync_pipeline.py:113 [comparacion] and partes[1].isdigit() and 1 <= int(partes[1]) < 12):
MUERTO api/application/sync_pipeline.py:113 [entero] and partes[1].isdigit() and 2 <= int(partes[1]) <= 12):
MUERTO api/domain/models.py:65 [booleano] @dataclass(frozen=False)
MUERTO api/domain/models.py:84 [booleano] @dataclass(frozen=False)
MUERTO api/infrastructure/db/orm_models.py:344 [booleano] DateTime(timezone=False), nullable=False, server_default=func.now(),
MUERTO api/infrastructure/db/orm_models.py:370 [booleano] ForeignKey("asignacion.id", ondelete="CASCADE"), nullable=True
MUERTO api/infrastructure/db/orm_models.py:342 [booleano] estado_vinculo: Mapped[str] = mapped_column(Text, nullable=True)
MUERTO api/infrastructure/db/orm_models.py:341 [booleano] activo: Mapped[bool] = mapped_column(Boolean, nullable=True, default=True)
MUERTO api/infrastructure/db/orm_models.py:386 [entero] sigrid_parte: Mapped[str | None] = mapped_column(String(25))
MUERTO api/infrastructure/db/orm_models.py:344 [booleano] DateTime(timezone=True), nullable=True, server_default=func.now(),
MUERTO api/infrastructure/db/orm_models.py:341 [booleano] activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
VIVE   api/infrastructure/db/repositories.py:533 [booleano] for linea, orm in zip(lineas, creadas, strict=False)
MUERTO api/infrastructure/db/orm_models.py:373 [booleano] ForeignKey("recurso_vinculado.ide"), nullable=True
MUERTO api/infrastructure/db/orm_models.py:384 [entero] sigrid_estado: Mapped[str | None] = mapped_column(String(17))
MUERTO api/infrastructure/db/repositories.py:549 [booleano] solo_si_vacia: bool = True,
MUERTO api/interface_adapters/api/routes.py:357 [entero] vinculado_ide: Annotated[int | None, Query(gt=1)] = None,
MUERTO api/interface_adapters/api/schemas.py:78 [entero] vinculado_ide: int | None = Field(default=None, gt=1)
26 mutantes, 1 siguen vivos
MUERTO transfer/application/pipelines/registro_pipeline.py:1412 [logico] p, d, f"Parte {d.nombre and d.codigo}{marca}"),
VIVE   transfer/application/pipelines/registro_pipeline.py:274 [booleano] vinculados=[av for a, l in zip(acciones, lineas, strict=False)
VIVE   transfer/application/pipelines/registro_vinculados.py:188 [booleano] p = partida_del_vinculado(titular, None, False, ci)
MUERTO transfer/application/pipelines/registro_pipeline.py:645 [logico] if a.accion == "escribir" or a.destino != "postventa"
VIVE   transfer/application/pipelines/registro_pipeline.py:761 [logico] if escribir or inc_escribir and vin_escribir:
VIVE   transfer/application/pipelines/registro_vinculados.py:223 [booleano] strict=False):
MUERTO transfer/application/pipelines/registro_vinculados.py:239 [logico] return (bool(nodo and nodo.es_hoja or nodo.activa),
MUERTO transfer/application/pipelines/registro_vinculados.py:257 [logico] elif (v.propuesta_paride or v.propuesta_metodo == METODO_CI_TIPO
MUERTO transfer/application/pipelines/registro_vinculados.py:264 [logico] av.partida_res = v.propuesta_res and res
MUERTO transfer/application/pipelines/registro_vinculados.py:372 [logico] or ls.ide not in suyas],
MUERTO transfer/application/pipelines/registro_vinculados.py:219 [entero] destino=a.destino, paride=int(a.paride or 1),
MUERTO transfer/application/pipelines/registro_vinculados.py:303 [entero] or 1))
MUERTO transfer/application/pipelines/registro_vinculados.py:239 [logico] return (bool(nodo or nodo.es_hoja and nodo.activa),
MUERTO transfer/application/pipelines/registro_vinculados.py:412 [entero] motivo="sobrecarga", suma_existente=round(cap.existente, 5),
MUERTO transfer/application/pipelines/registro_vinculados.py:305 [logico] and not es_de_la_hora(hit, av.hora_codigo)
VIVE   transfer/application/pipelines/registro_vinculados.py:252 [booleano] elegida, valida = None, False
MUERTO transfer/application/pipelines/registro_vinculados.py:436 [comparacion] partida = (av.partida_cod if ls.paride != av.paride
MUERTO transfer/application/pipelines/registro_vinculados.py:306 [logico] and es_nuestra_de_otra(hit.synckey, propia)):
MUERTO transfer/application/pipelines/registro_vinculados.py:371 [logico] or es_de_la_hora(ls, av.hora_codigo)
MUERTO transfer/application/pipelines/registro_vinculados.py:470 [logico] tipo, cod = (c.vinculado or {}).get("tipo"), (c.vinculado and {}).get(
MUERTO transfer/application/pipelines/registro_vinculados.py:369 [comparacion] if ls.reside != av.recurso_ide
MUERTO transfer/application/pipelines/registro_vinculados.py:477 [booleano] existente=c.suma_existente, nueva=c.nueva_can), False
MUERTO transfer/application/pipelines/registro_vinculados.py:370 [logico] or ls not in choques
MUERTO transfer/application/pipelines/registro_vinculados.py:559 [entero] "hora_codigo": av.hora_codigo, "paride": int(av.paride or 1),
MUERTO transfer/application/pipelines/registro_vinculados.py:413 [entero] suma_total=round(cap.total, 5), exceso=round(cap.exceso, 4),
MUERTO transfer/application/pipelines/registro_vinculados.py:470 [logico] tipo, cod = (c.vinculado and {}).get("tipo"), (c.vinculado or {}).get(
MUERTO transfer/application/pipelines/registro_vinculados.py:385 [logico] or clave_de(av) not in en_pisado],
MUERTO transfer/application/pipelines/registro_vinculados.py:567 [logico] paride=int(av.paride and 0), caaide=int(av.caa_ide or 0),
MUERTO transfer/application/pipelines/registro_vinculados.py:474 [comparacion] if c.motivo != "sobrecarga":
MUERTO transfer/application/pipelines/registro_vinculados.py:413 [entero] suma_total=round(cap.total, 4), exceso=round(cap.exceso, 5),
MUERTO transfer/application/pipelines/registro_vinculados.py:559 [logico] "hora_codigo": av.hora_codigo, "paride": int(av.paride and 0),
MUERTO transfer/application/pipelines/registro_vinculados.py:560 [logico] "caaide": int(av.caa_ide and 0), "fecha_int": av.fecha_int,
MUERTO transfer/application/pipelines/registro_vinculados.py:636 [logico] if not c.vinculado and c.clave not in pisar or not regs:
MUERTO transfer/application/pipelines/registro_vinculados.py:561 [comparacion] "synckey": sk, "tex": ls.tex if self._tex is not None
MUERTO transfer/application/pipelines/registro_vinculados.py:567 [entero] paride=int(av.paride or 1), caaide=int(av.caa_ide or 0),
MUERTO transfer/application/pipelines/registro_vinculados.py:567 [entero] paride=int(av.paride or 0), caaide=int(av.caa_ide or 1),
MUERTO transfer/application/pipelines/registro_vinculados.py:560 [entero] "caaide": int(av.caa_ide or 1), "fecha_int": av.fecha_int,
MUERTO transfer/application/pipelines/registro_vinculados.py:664 [logico] and not es_de_la_hora(ls, av.hora_codigo)
VIVE   transfer/application/pipelines/registro_vinculados.py:604 [logico] if not (p.existe or p.ide):
MUERTO transfer/application/pipelines/registro_vinculados.py:567 [logico] paride=int(av.paride or 0), caaide=int(av.caa_ide and 0),
MUERTO transfer/application/pipelines/registro_vinculados.py:666 [booleano] return True
MUERTO transfer/application/pipelines/registro_vinculados.py:636 [logico] if not c.vinculado or c.clave not in pisar and not regs:
MUERTO transfer/application/pipelines/registro_vinculados.py:603 [logico] or (x.ano, x.mes) == (av.ano, av.mes))
MUERTO transfer/application/pipelines/registro_vinculados.py:689 [comparacion] - t["despues"]["can"]) > 0.000001 \
MUERTO transfer/application/pipelines/registro_vinculados.py:609 [aritmetico] pos[hmoide] -= self._paso
MUERTO transfer/application/pipelines/registro_vinculados.py:663 [logico] if (ls is None and ls.enlazada
MUERTO transfer/application/pipelines/registro_vinculados.py:616 [entero] paride=int(av.paride or 0), caaide=int(av.caa_ide or 1)))
MUERTO transfer/application/pipelines/registro_vinculados.py:688 [logico] if hit is None and abs(float(hit.can or 0.0)
MUERTO transfer/application/pipelines/registro_vinculados.py:690 [logico] and (hit.synckey or "").strip() != t["despues"]["synckey"]:
MUERTO transfer/application/pipelines/registro_vinculados.py:665 [logico] and ls.parte_est != self._est):
MUERTO transfer/application/pipelines/registro_vinculados.py:700 [logico] if hit is None and float(hit.can or 0.0) != 0.0:
MUERTO transfer/application/pipelines/registro_vinculados.py:700 [logico] if hit is None or float(hit.can and 0.0) != 0.0:
MUERTO transfer/application/services/reglas_vinculados.py:278 [logico] return _POR_QUE_SIN_CI.get(motivo or "", motivo and "")
MUERTO transfer/application/services/reglas_vinculados.py:88 [booleano] @dataclass(frozen=False)
MUERTO transfer/application/services/reglas_vinculados.py:278 [logico] return _POR_QUE_SIN_CI.get(motivo and "", motivo or "")
55 mutantes, 6 siguen vivos
```
