<!-- progress/mutacion_F-044.md -->
# F-044 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-044` el 2026-10-26 17:03.

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
| Muertos | 415 |
| Supervivientes | 7 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 3350.8 s |
| SHA de HEAD medido | `38a53d0f3f0a095ef752eae80d884b8abe5bf4b2` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-044_mztn4hmj/wk_0/services/dedicacion-api` | 70.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-044_mztn4hmj/wk_0/services/dedicacion-transfer` | 38.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-044_mztn4hmj/wk_1/services/dedicacion-api` | 70.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-044_mztn4hmj/wk_1/services/dedicacion-transfer` | 38.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-044_mztn4hmj/wk_2/services/dedicacion-api` | 70.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-044_mztn4hmj/wk_2/services/dedicacion-transfer` | 37.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-044_mztn4hmj/wk_3/services/dedicacion-api` | 70.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-044_mztn4hmj/wk_3/services/dedicacion-transfer` | 38.0 |
| Media por mutante evaluado (s) | 7.9 |
| Timeout efectivo por mutante (s) | 142 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/dedicacion-api/infrastructure/db/repositories.py:533` [booleano]

- Original: `for linea, orm in zip(lineas, creadas, strict=True)`
- Mutado:   `for linea, orm in zip(lineas, creadas, strict=False)`

#### Análisis (implementer)

> Por qué ningún test lo caza: `creadas` se llena en el bucle de justo encima con un `AsignacionORM` por cada `linea`, en su orden: las dos listas tienen siempre la misma longitud y `strict` solo vigila un error de programación que no puede darse.
> Decisión: mutante equivalente (`strict` de un `zip` de longitudes iguales por construcción). **Aceptada por el humano el 2026-10-26** («1 ok», a los 7 equivalentes; rigor crítico, `tasks.md`).

### 2. `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:274` [booleano]

- Original: `vinculados=[av for a, l in zip(acciones, lineas, strict=True)`
- Mutado:   `vinculados=[av for a, l in zip(acciones, lineas, strict=False)`

#### Análisis (implementer)

> Por qué ningún test lo caza: `acciones = [reglas.decidir(l) for l in lineas]`, dos líneas más arriba: una acción por línea, en su orden. El `zip` nunca recibe listas de distinta longitud.
> Decisión: mutante equivalente (`strict` de un `zip` de longitudes iguales por construcción). **Aceptada por el humano el 2026-10-26** («1 ok», a los 7 equivalentes; rigor crítico, `tasks.md`).

### 3. `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:761` [logico]

- Original: `if escribir or inc_escribir or vin_escribir:`
- Mutado:   `if escribir or inc_escribir and vin_escribir:`

#### Análisis (implementer)

> Por qué ningún test lo caza: el mutante solo cambia algo si `escribir` está vacío y `vin_escribir` no. No puede darse: en el paso 4 bis las acciones de los titulares solo son `escribir` u `omitir` (el «ya registrado» se decide en el paso 6), y `decidir_vinculados` omite todos los vinculados de un titular omitido (R18). Por tanto, `vin_escribir` no vacío implica `escribir` no vacío, y con ambas expresiones se entra.
> Decisión: mutante equivalente (`vin_escribir` no vacío ⇒ `escribir` no vacío). **Aceptada por el humano el 2026-10-26** («1 ok», a los 7 equivalentes; rigor crítico, `tasks.md`).

### 4. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:188` [booleano]

- Original: `p = partida_del_vinculado(titular, None, True, ci)`
- Mutado:   `p = partida_del_vinculado(titular, None, False, ci)`

#### Análisis (implementer)

> Por qué ningún test lo caza: `partida_del_vinculado` solo lee `elegida_valida` dentro de `if elegida is not None`, y aquí `elegida` es `None` (la propuesta no tiene elegida). El valor es indiferente.
> Decisión: mutante equivalente (argumento no leído con `elegida=None`). **Aceptada por el humano el 2026-10-26** («1 ok», a los 7 equivalentes; rigor crítico, `tasks.md`).

### 5. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:223` [booleano]

- Original: `strict=True):`
- Mutado:   `strict=False):`

#### Análisis (implementer)

> Por qué ningún test lo caza: `decidir_vinculados(a, linea, horas)` devuelve exactamente una acción por cada `linea.vinculados`, en su orden (un `append` por vuelta del bucle, con `continue` tras cada uno). Las longitudes son siempre iguales.
> Decisión: mutante equivalente (`strict` de un `zip` de longitudes iguales por construcción). **Aceptada por el humano el 2026-10-26** («1 ok», a los 7 equivalentes; rigor crítico, `tasks.md`).

### 6. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:252` [booleano]

- Original: `elegida, valida = None, True`
- Mutado:   `elegida, valida = None, False`

#### Análisis (implementer)

> Por qué ningún test lo caza: `valida` solo llega a `partida_del_vinculado`, que la lee únicamente si `elegida` no es `None`, y en esta rama queda en `None` (solo la rama `if v.paride` asigna `elegida` y `valida` a la vez).
> Decisión: mutante equivalente (valor inicial que solo se lee junto con una `elegida` que lo sustituye). **Aceptada por el humano el 2026-10-26** («1 ok», a los 7 equivalentes; rigor crítico, `tasks.md`).

### 7. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:604` [logico]

- Original: `if not (p.existe and p.ide):`
- Mutado:   `if not (p.existe or p.ide):`

#### Análisis (implementer)

> Por qué ningún test lo caza: `and` y `or` solo difieren cuando uno de los dos, `existe` o `ide`, es verdadero y el otro no. `ParteDestino` los pone siempre a la vez: `estado_parte.elegir_parte` da `existe=True` junto con el `ide` del parte leído (o deja `False`/`None`), y `_crear_parte` los fija juntos tras el alta. El `ide` de Sigrid nunca es 0.
> Decisión: mutante equivalente (invariante `existe` ⇔ `ide` de `ParteDestino`). **Aceptada por el humano el 2026-10-26** («1 ok», a los 7 equivalentes; rigor crítico, `tasks.md`).

## Pasadas (implementer, 2026-10-26)

Primera pasada (HEAD `bd38dc5`): 422 mutantes, 81 supervivientes. 74 los matan los tests nuevos de T22 (`tests/test_f044_mutacion.py`, api y transfer, commit `38a53d0`); la comprobación uno a uno va en `progress/mutacion_F-044_pasada1.md`. Esta segunda pasada, sobre `38a53d0`, deja exactamente los 7 equivalentes que había previsto la comprobación.
