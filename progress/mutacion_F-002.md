<!-- progress/mutacion_F-002.md -->
# F-002 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-002` el 2026-08-19 17:05.

## Alcance

Origen del diff: **rama** (`c43a12fd730805a107985e0962a8134e8cbc1678` .. `feature/F-002-reglas-postventa-conflicto`).

| Fichero | Líneas en alcance |
|---|---|
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py` | 143 |
| `services/dedicacion-transfer/application/services/partida_resolver.py` | 21 |
| `services/dedicacion-transfer/application/services/reglas_porcentajes.py` | 237 |
| `services/dedicacion-transfer/domain/models/registro_models.py` | 36 |
| `services/dedicacion-transfer/interface_adapters/api/app.py` | 2 |
| **Total** | **439** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 34 |
| Mutantes evaluados | 34 |
| Muertos | 33 |
| Supervivientes | 1 |
| Timeouts | 0 |
| Tiempo total | 35.3 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/dedicacion-transfer/application/services/reglas_porcentajes.py:233` [comparacion]

- Original: `exceso=exceso, sobrecarga=exceso > EPSILON_CAPACIDAD,`
- Mutado:   `exceso=exceso, sobrecarga=exceso >= EPSILON_CAPACIDAD,`

#### Análisis

**Por qué ningún test lo caza: porque el caso que los distinguiría no existe
en aritmética de coma flotante.** `>` y `>=` solo difieren cuando
`exceso == EPSILON_CAPACIDAD` **exactamente**, y ese valor no es alcanzable:

- `exceso = total - 1.0`. Para `total` en `[1, 2)` esa resta es **exacta**
  (Sterbenz), así que su resultado solo puede ser un múltiplo del ULP de esa
  franja, `2⁻⁵²` ≈ 2,22e-16.
- El `double` más cercano a `0,00005` **no** es múltiplo de `2⁻⁵²`. Se
  comprueba de un tirón: `(1.0 + 0.00005) - 1.0` vale
  `5.0000000000105516e-05`, que **no** es igual a `0.00005`.
- Para `total ≥ 2` el exceso es ≥ 1, muy por encima de la épsilon, y las dos
  comparaciones responden lo mismo.

**Decisión: mutante EQUIVALENTE, justificado.** No se añade un test que lo
mate porque no puede existir. Lo que sí se ha añadido es un test que deja la
demostración escrita y ejecutable, para que el próximo que lea este informe
no tenga que rehacer el razonamiento:
`tests/test_f002_capacidad.py::test_f002_r26_el_borde_exacto_de_la_tolerancia_no_existe`.

La conducta del borde **sí** está probada por los dos lados con
`test_f002_r26_la_tolerancia_decide_el_borde[...]` (media épsilon no avisa,
el doble sí) y con `test_f002_r26_justo_uno_no_es_sobrecarga`.

> Los otros **siete** supervivientes de la primera pasada de esta campaña
> (8 en total, ver `progress/impl_F-002_fase2.md` §5) **se mataron**: tres
> con tests nuevos, tres quitando un `round(..., 4)` que ningún test
> ejercitaba en su cuarto decimal, y uno simplificando dos `or 0` defensivos
> que P1 hace imposibles.

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

