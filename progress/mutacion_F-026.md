<!-- progress/mutacion_F-026.md -->
# F-026 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-026` el 2026-10-02 11:51.

## Alcance

Origen del diff: **rama** (`5f498cb50576f28d500a08b92e207351be3b2b43` .. `feature/F-026-recursos-sin-ficha-empleado`).

| Fichero | Líneas en alcance |
|---|---|
| `services/dedicacion-api/application/filtros_maestros.py` | 72 |
| `services/dedicacion-api/application/registro_sigrid.py` | 25 |
| `services/dedicacion-api/application/sync_pipeline.py` | 27 |
| `services/dedicacion-api/application/use_cases.py` | 23 |
| `services/dedicacion-api/domain/models.py` | 4 |
| `services/dedicacion-api/domain/vigencia.py` | 48 |
| `services/dedicacion-api/infrastructure/db/orm_models.py` | 7 |
| `services/dedicacion-api/infrastructure/db/repositories.py` | 25 |
| `services/dedicacion-api/interface_adapters/api/deps.py` | 5 |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py` | 9 |
| `services/dedicacion-transfer/application/services/reglas_porcentajes.py` | 4 |
| `services/dedicacion-transfer/domain/models/registro_models.py` | 3 |
| `services/dedicacion-transfer/interface_adapters/api/app.py` | 4 |
| `services/dedicacion-transfer/prueba_escritura_porcentajes.py` | 6 |
| **Total** | **262** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 56 |
| Mutantes evaluados | 56 |
| Muertos | 50 |
| Supervivientes | 6 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 506.4 s |
| SHA de HEAD medido | `5bea52e7adc7fe83558632f24d63942371977867` |
| Línea base (s) — `services/dedicacion-api` | 11.5 |
| Línea base (s) — `services/dedicacion-transfer` | 4.0 |
| Media por mutante evaluado (s) | 9.0 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/dedicacion-transfer/prueba_escritura_porcentajes.py:47` [entero]

- Original: `{"registro_id": 900001, "recurso_ide": 0, "dni": None,`
- Mutado:   `{"registro_id": 900002, "recurso_ide": 0, "dni": None,`

#### Análisis (implementer, 2026-10-02)

> Por qué ningún test lo caza: es un DATO de ejemplo del script manual
> `prueba_escritura_porcentajes.py` (`LINEAS_PRUEBA`, «EDITAR con RECURSOS
> reales»): `registro_id` 9000xx y `recurso_ide` 0 son marcadores que la
> persona sustituye antes de lanzar `preflight`; ningún código de producción
> depende de su valor. Entra en el alcance solo porque F-026 renombró la
> clave `empleado_ide` → `recurso_ide` en esas tres líneas. Reproducido a
> mano (línea 47 con `900002` y `recurso_ide: 1`): suite del transfer
> `329 passed`, igual que sin mutar.
> Decisión: **mutante equivalente a efectos de comportamiento, justificado**;
> sin test nuevo. Fijar los valores de un marcador que hay que editar
> obligaría a cambiar el test cada vez que alguien prepare una prueba. Lo
> que sí importa del bloque, que cada línea lleve `empresa` y pase por
> `LineaEntrada` (ya sin `empleado_ide`), lo prueba `test_f022_r13_script_de_
> pruebas_imputa_a_la_empresa_de_la_0404`.

### 2. `services/dedicacion-transfer/prueba_escritura_porcentajes.py:47` [entero]

- Original: `{"registro_id": 900001, "recurso_ide": 0, "dni": None,`
- Mutado:   `{"registro_id": 900001, "recurso_ide": 1, "dni": None,`

#### Análisis (implementer, 2026-10-02)

> Por qué ningún test lo caza: es un DATO de ejemplo del script manual
> `prueba_escritura_porcentajes.py` (`LINEAS_PRUEBA`, «EDITAR con RECURSOS
> reales»): `registro_id` 9000xx y `recurso_ide` 0 son marcadores que la
> persona sustituye antes de lanzar `preflight`; ningún código de producción
> depende de su valor. Entra en el alcance solo porque F-026 renombró la
> clave `empleado_ide` → `recurso_ide` en esas tres líneas. Reproducido a
> mano (línea 47 con `900002` y `recurso_ide: 1`): suite del transfer
> `329 passed`, igual que sin mutar.
> Decisión: **mutante equivalente a efectos de comportamiento, justificado**;
> sin test nuevo. Fijar los valores de un marcador que hay que editar
> obligaría a cambiar el test cada vez que alguien prepare una prueba. Lo
> que sí importa del bloque, que cada línea lleve `empresa` y pase por
> `LineaEntrada` (ya sin `empleado_ide`), lo prueba `test_f022_r13_script_de_
> pruebas_imputa_a_la_empresa_de_la_0404`.

### 3. `services/dedicacion-transfer/prueba_escritura_porcentajes.py:50` [entero]

- Original: `{"registro_id": 900002, "recurso_ide": 0, "dni": None,`
- Mutado:   `{"registro_id": 900003, "recurso_ide": 0, "dni": None,`

#### Análisis (implementer, 2026-10-02)

> Por qué ningún test lo caza: es un DATO de ejemplo del script manual
> `prueba_escritura_porcentajes.py` (`LINEAS_PRUEBA`, «EDITAR con RECURSOS
> reales»): `registro_id` 9000xx y `recurso_ide` 0 son marcadores que la
> persona sustituye antes de lanzar `preflight`; ningún código de producción
> depende de su valor. Entra en el alcance solo porque F-026 renombró la
> clave `empleado_ide` → `recurso_ide` en esas tres líneas. Reproducido a
> mano (línea 47 con `900002` y `recurso_ide: 1`): suite del transfer
> `329 passed`, igual que sin mutar.
> Decisión: **mutante equivalente a efectos de comportamiento, justificado**;
> sin test nuevo. Fijar los valores de un marcador que hay que editar
> obligaría a cambiar el test cada vez que alguien prepare una prueba. Lo
> que sí importa del bloque, que cada línea lleve `empresa` y pase por
> `LineaEntrada` (ya sin `empleado_ide`), lo prueba `test_f022_r13_script_de_
> pruebas_imputa_a_la_empresa_de_la_0404`.

### 4. `services/dedicacion-transfer/prueba_escritura_porcentajes.py:50` [entero]

- Original: `{"registro_id": 900002, "recurso_ide": 0, "dni": None,`
- Mutado:   `{"registro_id": 900002, "recurso_ide": 1, "dni": None,`

#### Análisis (implementer, 2026-10-02)

> Por qué ningún test lo caza: es un DATO de ejemplo del script manual
> `prueba_escritura_porcentajes.py` (`LINEAS_PRUEBA`, «EDITAR con RECURSOS
> reales»): `registro_id` 9000xx y `recurso_ide` 0 son marcadores que la
> persona sustituye antes de lanzar `preflight`; ningún código de producción
> depende de su valor. Entra en el alcance solo porque F-026 renombró la
> clave `empleado_ide` → `recurso_ide` en esas tres líneas. Reproducido a
> mano (línea 47 con `900002` y `recurso_ide: 1`): suite del transfer
> `329 passed`, igual que sin mutar.
> Decisión: **mutante equivalente a efectos de comportamiento, justificado**;
> sin test nuevo. Fijar los valores de un marcador que hay que editar
> obligaría a cambiar el test cada vez que alguien prepare una prueba. Lo
> que sí importa del bloque, que cada línea lleve `empresa` y pase por
> `LineaEntrada` (ya sin `empleado_ide`), lo prueba `test_f022_r13_script_de_
> pruebas_imputa_a_la_empresa_de_la_0404`.

### 5. `services/dedicacion-transfer/prueba_escritura_porcentajes.py:53` [entero]

- Original: `{"registro_id": 900003, "recurso_ide": 0, "dni": None,`
- Mutado:   `{"registro_id": 900004, "recurso_ide": 0, "dni": None,`

#### Análisis (implementer, 2026-10-02)

> Por qué ningún test lo caza: es un DATO de ejemplo del script manual
> `prueba_escritura_porcentajes.py` (`LINEAS_PRUEBA`, «EDITAR con RECURSOS
> reales»): `registro_id` 9000xx y `recurso_ide` 0 son marcadores que la
> persona sustituye antes de lanzar `preflight`; ningún código de producción
> depende de su valor. Entra en el alcance solo porque F-026 renombró la
> clave `empleado_ide` → `recurso_ide` en esas tres líneas. Reproducido a
> mano (línea 47 con `900002` y `recurso_ide: 1`): suite del transfer
> `329 passed`, igual que sin mutar.
> Decisión: **mutante equivalente a efectos de comportamiento, justificado**;
> sin test nuevo. Fijar los valores de un marcador que hay que editar
> obligaría a cambiar el test cada vez que alguien prepare una prueba. Lo
> que sí importa del bloque, que cada línea lleve `empresa` y pase por
> `LineaEntrada` (ya sin `empleado_ide`), lo prueba `test_f022_r13_script_de_
> pruebas_imputa_a_la_empresa_de_la_0404`.

### 6. `services/dedicacion-transfer/prueba_escritura_porcentajes.py:53` [entero]

- Original: `{"registro_id": 900003, "recurso_ide": 0, "dni": None,`
- Mutado:   `{"registro_id": 900003, "recurso_ide": 1, "dni": None,`

#### Análisis (implementer, 2026-10-02)

> Por qué ningún test lo caza: es un DATO de ejemplo del script manual
> `prueba_escritura_porcentajes.py` (`LINEAS_PRUEBA`, «EDITAR con RECURSOS
> reales»): `registro_id` 9000xx y `recurso_ide` 0 son marcadores que la
> persona sustituye antes de lanzar `preflight`; ningún código de producción
> depende de su valor. Entra en el alcance solo porque F-026 renombró la
> clave `empleado_ide` → `recurso_ide` en esas tres líneas. Reproducido a
> mano (línea 47 con `900002` y `recurso_ide: 1`): suite del transfer
> `329 passed`, igual que sin mutar.
> Decisión: **mutante equivalente a efectos de comportamiento, justificado**;
> sin test nuevo. Fijar los valores de un marcador que hay que editar
> obligaría a cambiar el test cada vez que alguien prepare una prueba. Lo
> que sí importa del bloque, que cada línea lleve `empresa` y pase por
> `LineaEntrada` (ya sin `empleado_ide`), lo prueba `test_f022_r13_script_de_
> pruebas_imputa_a_la_empresa_de_la_0404`.

## Notas del implementer

- **Campaña anterior (paralela, 4 workers, HEAD `be5efd0`)**: 56 evaluados,
  47 muertos, 9 supervivientes. Además de estos seis daba tres que, al
  reproducirlos a mano, **no sobreviven**:
  - `filtros_maestros.py:124` `> 0` → `> 1`: superviviente REAL (con la
    mutación a mano, `439 passed`). Hueco: nada fijaba que `fecha_baja = 1`
    cuenta en `incluidos_con_baja`. Lo mata
    `test_f026_r17_cualquier_fecha_de_baja_positiva_cuenta_como_con_baja`
    (commit `5bea52e`; contra el mutante `assert 0 == 1`).
  - `vigencia.py:21` `*` → `//` y `registro_sigrid.py:115` `or` → `and`:
    **falsos supervivientes de la campaña paralela**. A mano los matan 12 y
    15 tests respectivamente; una campaña en serie solo de `vigencia.py`
    dio 18/18 muertos y esta campaña en serie los da por muertos. Posible
    fallo del arnés con `workers > 1` (aviso para el líder; no se toca aquí).
- Esta campaña es en serie (`--workers 1`) sobre HEAD `5bea52e`, para que
  los números no dependan de ese fallo.
