<!-- progress/mutacion_F-026.md -->
# F-026 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-026` el 2026-10-02 12:33.

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
| Muertos | 55 |
| Supervivientes | 1 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 576.9 s |
| SHA de HEAD medido | `df7e94cfb118cf9b876b816a5c79080a7d2796c3` |
| Línea base (s) — `services/dedicacion-api` | 14.5 |
| Línea base (s) — `services/dedicacion-transfer` | 4.5 |
| Media por mutante evaluado (s) | 10.3 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/dedicacion-transfer/prueba_escritura_porcentajes.py:53` [entero]

- Original: `{"registro_id": 900003, "recurso_ide": 0, "dni": None,`
- Mutado:   `{"registro_id": 900004, "recurso_ide": 0, "dni": None,`

#### Análisis (implementer, 2026-10-02, ciclo 2 tras la review 1)

> Reproducido a mano (línea 53 con `900004`, el resto intacto): suite del
> transfer `330 passed`, igual que sin mutar.
> Qué cambia de verdad: solo el literal del tercer `registro_id` de
> ejemplo y, con él, la synckey que llevaría esa línea si alguien la
> escribiera (`porcentajes:900004` en vez de `porcentajes:900003`).
> Qué NO cambia, y lo fija `test_f026_r20_lineas_de_ejemplo_sin_editar_no_
> escriben` (commit `df7e94c`): los tres `registro_id` siguen siendo
> distintos (900001, 900002, 900004), así que las synckey no se pisan en la
> idempotencia ni en `verificar`; los tres siguen con `recurso_ide` 0 y el
> preflight los omite por `MOTIVO_SIN_RECURSO`; siguen en el rango
> `9000xx` que documenta el comentario de la línea 45; `limpiar` busca por
> la marca y el prefijo `porcentajes:`, no por el número. Ningún código
> lee ese valor concreto: es un identificador arbitrario por diseño.
> Decisión: **equivalente**, como dijo la review 1 («solo el nº 5 es
> equivalente de verdad»). Matarlo exigiría fijar el número exacto en un
> test, que no protege ninguna propiedad. **Necesita aceptación escrita del
> humano antes del `done`** (rigor `critico`).



## Notas del implementer

- **Ciclo 2 (tras la review 1)**: esta campaña es en serie (`--workers 1`)
  sobre HEAD `df7e94c`. La anterior (HEAD `5bea52e`, 506,4 s) dio 50/56 y
  seis supervivientes en `prueba_escritura_porcentajes.py`, de los que la
  review demostró que cinco NO eran equivalentes (nº 1 y 3 duplicaban un
  `registro_id` y su synckey; nº 2, 4 y 6 quitaban el centinela
  `recurso_ide: 0`). Los mata `test_f026_r20_lineas_de_ejemplo_sin_editar_
  no_escriben` (mutantes 51-54 y 56 de esta campaña: muertos).
- Campañas anteriores y los falsos supervivientes de la campaña paralela
  (`vigencia.py:21`, `registro_sigrid.py:115`): ver
  `git show 1bdb08b:progress/mutacion_F-026.md`, «Notas del implementer».
