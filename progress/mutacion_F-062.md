<!-- progress/mutacion_F-062.md -->
# F-062 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-062` el 2026-10-24 23:51.

## Alcance

Origen del diff: **rama** (`91648df8b8ba08b40cc6f9ade9455f18485134d5` .. `feature/F-062-rachas-incidencias`).

| Fichero | Líneas en alcance |
|---|---|
| `services/dedicacion-api/application/registro_sigrid.py` | 67 |
| `services/dedicacion-api/application/traza_incidencias.py` | 106 |
| `services/dedicacion-api/domain/models.py` | 2 |
| `services/dedicacion-api/infrastructure/db/orm_models.py` | 4 |
| `services/dedicacion-api/infrastructure/db/repositories.py` | 2 |
| `services/dedicacion-transfer/application/pipelines/registro_lote.py` | 9 |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py` | 217 |
| `services/dedicacion-transfer/application/services/lecturas_lote.py` | 119 |
| `services/dedicacion-transfer/application/services/rachas.py` | 1121 |
| `services/dedicacion-transfer/application/services/reglas_incidencias.py` | 29 |
| `services/dedicacion-transfer/config/settings.py` | 4 |
| `services/dedicacion-transfer/domain/models/registro_models.py` | 47 |
| `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py` | 40 |
| `services/dedicacion-transfer/interface_adapters/api/app.py` | 70 |
| `services/dedicacion-transfer/prueba_escritura_porcentajes.py` | 155 |
| **Total** | **1992** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 609 |
| Mutantes evaluados | 609 |
| Muertos | 598 |
| Supervivientes | 11 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 4819.9 s |
| SHA de HEAD medido | `44841b892b4f1993b13d8390bccd19556420f7af` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-062_6g4kgo43/wk_0/services/dedicacion-api` | 72.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-062_6g4kgo43/wk_0/services/dedicacion-transfer` | 35.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-062_6g4kgo43/wk_1/services/dedicacion-api` | 71.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-062_6g4kgo43/wk_1/services/dedicacion-transfer` | 35.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-062_6g4kgo43/wk_2/services/dedicacion-api` | 72.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-062_6g4kgo43/wk_2/services/dedicacion-transfer` | 35.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-062_6g4kgo43/wk_3/services/dedicacion-api` | 71.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-062_6g4kgo43/wk_3/services/dedicacion-transfer` | 35.8 |
| Media por mutante evaluado (s) | 7.9 |
| Timeout efectivo por mutante (s) | 145 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/dedicacion-api/application/registro_sigrid.py:436` [logico]

- Original: `cierres=r.get("cierres_racha") or [],`
- Mutado:   `cierres=r.get("cierres_racha") and [],`

#### Análisis (implementer)

> Por qué ningún test lo caza: sí lo caza. **Falso superviviente de la campaña paralela** (O1 de la review 1): reaplicado igual, en serie, en un worktree de `44841b8` (el HEAD medido), la suite de la api cae en `test_f062_payload_rachas.py::test_f062_r23_traza_ejecutar_pasa_cierres_y_no_coincide`. En la campaña 1 este mutante salió muerto.
> Decisión: muerto (sin test nuevo); aviso al líder por O1.

### 2. `services/dedicacion-api/application/traza_incidencias.py:64` [comparacion]

- Original: `if antes is not None:`
- Mutado:   `if antes is None:`

#### Análisis (implementer)

> Por qué ningún test lo caza: sí lo caza. **Falso superviviente de la campaña paralela** (O1 de la review 1): reaplicado igual, en serie, en un worktree de `44841b8` (el HEAD medido), la suite de la api cae en `test_f030_r30_identidad.py::test_f030_r39_registro_la_registrada_viaja_con_su_traza`. En la campaña 1 este mutante salió muerto.
> Decisión: muerto (sin test nuevo); aviso al líder por O1.

### 3. `services/dedicacion-api/application/traza_incidencias.py:127` [not]

- Original: `if n.get("tipo") != "quitada" or not inc_id or n.get("en_sigrid"):`
- Mutado:   `if n.get("tipo") != "quitada" or inc_id or n.get("en_sigrid"):`

#### Análisis (implementer)

> Por qué ningún test lo caza: sí lo caza. **Falso superviviente de la campaña paralela** (O1 de la review 1): reaplicado igual, en serie, en un worktree de `44841b8` (el HEAD medido), la suite de la api cae en `test_f062_payload_rachas.py::test_f062_r17_traza_la_quitada_sin_lineas_en_sigrid_se_borra`. En la campaña 1 este mutante salió muerto.
> Decisión: muerto (sin test nuevo); aviso al líder por O1.

### 4. `services/dedicacion-api/application/traza_incidencias.py:138` [booleano]

- Original: `IncidenciaORM.quitada.is_(True)]`
- Mutado:   `IncidenciaORM.quitada.is_(False)]`

#### Análisis (implementer)

> Por qué ningún test lo caza: sí lo caza. **Falso superviviente de la campaña paralela** (O1 de la review 1): reaplicado igual, en serie, en un worktree de `44841b8` (el HEAD medido), la suite de la api cae en `test_f062_payload_rachas.py::test_f062_r17_traza_devolver_anula_y_borra_la_quitada_sin_ide`. En la campaña 1 este mutante salió muerto.
> Decisión: muerto (sin test nuevo); aviso al líder por O1.

### 5. `services/dedicacion-api/application/traza_incidencias.py:167` [entero]

- Original: `"sigrid_parte_cod": hechas[0].get("parte_cod"),`
- Mutado:   `"sigrid_parte_cod": hechas[1].get("parte_cod"),`

#### Análisis (implementer)

> Por qué ningún test lo caza: sí lo caza. **Falso superviviente de la campaña paralela** (O1 de la review 1): reaplicado igual, en serie, en un worktree de `44841b8` (el HEAD medido), la suite de la api cae en `test_f030_r30_identidad.py::test_f030_r39_traza_un_omitir_no_borra_el_ide_de_su_rol`. En la campaña 1 este mutante salió muerto.
> Decisión: muerto (sin test nuevo); aviso al líder por O1.

### 6. `services/dedicacion-transfer/application/services/rachas.py:113` [entero]

- Original: `0 if es_inicio(x) else 1,`
- Mutado:   `0 if es_inicio(x) else 2,`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: La clave de orden de `emparejar` solo compara el 0 del inicio con el valor del `CIZ`: con 1 o con 2 el orden es el mismo (inicio antes que `CIZ` el mismo día). Ningún test puede distinguirlos.
> Decisión: mutante equivalente, justificado.

> **Sigue siendo el mismo y sigue siendo equivalente en la campaña 2** (HEAD `44841b8`): mismo fichero, línea, operador y texto; vive también en serie con la suite de `2f04d28`; y la demostración ejecutable (abajo) da original == mutado. **Aceptado por el humano el 2026-10-24** («ok a 1 y 2»).

### 7. `services/dedicacion-transfer/application/services/rachas.py:528` [entero]

- Original: `return _omitir_todo(cadena, base, base[0].motivo)`
- Mutado:   `return _omitir_todo(cadena, base, base[1].motivo)`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: `decidir_incidencia` omite «LAS DOS, con el mismo motivo» (su docstring y cada `return omitir(motivo)` de `reglas_incidencias.py`): cuando alguna de la base omite, `base[0].motivo == base[1].motivo`. Distinguirlas exigiría una base que el código no produce.
> Decisión: mutante equivalente, justificado.

> **Sigue siendo el mismo y sigue siendo equivalente en la campaña 2** (HEAD `44841b8`): mismo fichero, línea, operador y texto; vive también en serie con la suite de `2f04d28`; y la demostración ejecutable (abajo) da original == mutado. **Aceptado por el humano el 2026-10-24** («ok a 1 y 2»).

### 8. `services/dedicacion-transfer/prueba_escritura_porcentajes.py:159` [comparacion]

- Original: `if len(valores) > MAX_INCIDENCIAS_MES:`
- Mutado:   `if len(valores) >= MAX_INCIDENCIAS_MES:`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: ningún test pasaba justo 100 `--incidencia` (el tope de la centena del mes, B1).
> Decisión: test nuevo, `test_f062_r5_script_caben_cien_incidencias_por_mes` (`2f04d28`); reaplicado en serie en un worktree de `44841b8` con ese test, cae.

### 9. `services/dedicacion-transfer/prueba_escritura_porcentajes.py:328` [entero]

- Original: `sys.exit(1)`
- Mutado:   `sys.exit(2)`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: el test de O2 solo pedía un código distinto de 0; ahora fija el 1.
> Decisión: test nuevo, `test_f062_o2_script_en_modo_real_no_escribe` (`2f04d28`); reaplicado en serie en un worktree de `44841b8` con ese test, cae.

### 10. `services/dedicacion-transfer/prueba_escritura_porcentajes.py:335` [booleano]

- Original: `permitir_modo_real: bool = False) -> None:`
- Mutado:   `permitir_modo_real: bool = True) -> None:`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: los tests llamaban a la fase por `main()`, que siempre pasa la opción; nadie llamaba a `fase_ejecutar` sin ella.
> Decisión: test nuevo, `test_f062_o2_script_las_fases_por_defecto_no_escriben_en_modo_real` (`2f04d28`); reaplicado en serie en un worktree de `44841b8` con ese test, cae.

### 11. `services/dedicacion-transfer/prueba_escritura_porcentajes.py:391` [booleano]

- Original: `permitir_modo_real: bool = False) -> None:`
- Mutado:   `permitir_modo_real: bool = True) -> None:`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: igual que el anterior, para `fase_limpiar`.
> Decisión: test nuevo, `test_f062_o2_script_las_fases_por_defecto_no_escriben_en_modo_real` (`2f04d28`); reaplicado en serie en un worktree de `44841b8` con ese test, cae.

## Reproducción en serie y equivalentes (implementer, 2026-10-25)

Por O1 (rigor `critico`), los 11 se reaplicaron uno a uno en un worktree
desacoplado de `44841b8`, con la suite del servicio (`-x`) y el intérprete
del árbol principal (`verificar_supervivientes.py` y `verificar_informe.py`
del scratchpad del implementer):

| Resultado | Nº | Cuáles |
|---|---|---|
| Falso superviviente (cae en serie) | 5 | 1-5 (api) |
| Muerto con test nuevo (`2f04d28`) | 4 | 8-11 (script) |
| Vivo: equivalente aceptado por el humano | 2 | 6 (`rachas.py:113`), 7 (`rachas.py:528`) |

Ningún equivalente nuevo. **Demostración ejecutable** de los dos
(`demo_equivalentes_impl.py`, carga `rachas.py` original y mutado por
sustitución exacta del texto del mutante y compara):

```
nº 14 (rachas.py:113): emparejar original == mutado en 30000 casos
nº 23 (rachas.py:528): decidir_cadena original == mutado en 558 de 9582 bases que omiten; en las 9582, base[0].motivo == base[1].motivo
```

(Los números «14» y «23» son los de la campaña 1; aquí son el 6 y el 7. Las
9024 bases que omiten sin cadena no llegan a `decidir_cadena`: sin recurso o
sin días posibles, `cadenas` no las forma.)

**Aviso para el líder (arnés, O1):** la campaña paralela volvió a dar 5
supervivientes falsos, todos de la api (en la campaña 1, uno). Con `-x`, en
serie, cada uno cae con un test que ya existía. No se tocó `harness/`.
