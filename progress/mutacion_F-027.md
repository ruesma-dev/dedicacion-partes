<!-- progress/mutacion_F-027.md -->
# F-027 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-027` el 2026-10-04 14:26.

## Alcance

Origen del diff: **rama** (`68e884e850806e86ddda6c5c09be2748a576efa7` .. `feature/F-027-deshacer-por-usuario`).

| Fichero | Líneas en alcance |
|---|---|
| `services/dedicacion-api/application/use_cases.py` | 35 |
| `services/dedicacion-api/domain/deshacer.py` | 29 |
| `services/dedicacion-api/domain/errors.py` | 6 |
| `services/dedicacion-api/domain/models.py` | 11 |
| `services/dedicacion-api/domain/ports.py` | 7 |
| `services/dedicacion-api/infrastructure/db/repositories.py` | 18 |
| `services/dedicacion-api/interface_adapters/api/app.py` | 2 |
| `services/dedicacion-api/interface_adapters/api/routes.py` | 9 |
| **Total** | **117** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 8 |
| Mutantes evaluados | 8 |
| Muertos | 7 |
| Supervivientes | 1 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 67.3 s |
| SHA de HEAD medido | `3d2db3b6cb87a3324f7b16e55ff18332867a5282` |
| Línea base (s) — `services/dedicacion-api` | 12.3 |
| Media por mutante evaluado (s) | 8.4 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/dedicacion-api/domain/models.py:134` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis del implementer

> Por qué ningún test lo caza: `EventoPendiente` es un valor que el
> repositorio construye y el caso de uso solo LEE (`id`, `usuario`,
> `snapshot_antes`); ningún código de producción lo modifica, así que con
> `frozen=False` el comportamiento observable es idéntico.
> Decisión: **mutante equivalente**. `frozen=True` es una salvaguarda de
> diseño (igual que el resto de valores de `domain/models.py`, que tampoco
> tienen un test de inmutabilidad); un test que solo comprobara
> `FrozenInstanceError` probaría el decorador, no la regla de F-027.

## Campaña anterior (misma rama, HEAD `cc91bca`)

La primera campaña (`--workers 1`, 8 mutantes, 6 muertos) dejó además vivo
`use_cases.py:186` `permitir_inactivas=True -> False`: **hueco real**, ningún
test deshacía un `snapshot_antes` con una obra que ya no existe (comportamiento
anterior a F-027, en una línea que F-027 reescribió). Se cerró con
`test_f027_r6_deshacer_lo_mio_con_una_obra_que_ya_no_existe` (commit
`F-027 T6`), comprobado a mano contra el mutante (`ObraNoValida: Obras
inexistentes: [777]`), y esta campaña lo da por muerto.
