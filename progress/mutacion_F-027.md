<!-- progress/mutacion_F-027.md -->
# F-027 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-027` el 2026-10-04 14:34.

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
| Muertos | 8 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 58.2 s |
| SHA de HEAD medido | `ea95a294aa96d448e0a8fb6eaa8a0dc0d3947925` |
| Línea base (s) — `services/dedicacion-api` | 8.5 |
| Media por mutante evaluado (s) | 7.3 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.


## Campañas anteriores (misma rama, todas con `--workers 1`)

- **1.ª** (HEAD `cc91bca`): 8 / 6 muertos / 2 supervivientes.
  `use_cases.py:186` `permitir_inactivas=True -> False` era un **hueco real**
  (ningún test deshacía un `snapshot_antes` con una obra que ya no existe):
  cerrado con `test_f027_r6_deshacer_lo_mio_con_una_obra_que_ya_no_existe`
  (`F-027 T6`, `3d2db3b`), comprobado a mano contra el mutante
  (`ObraNoValida: Obras inexistentes: [777]`).
- **2.ª** (HEAD `3d2db3b`): 8 / 7 / 1. Quedaba `models.py:134`
  `@dataclass(frozen=True) -> frozen=False` en `EventoPendiente`, que se dio
  por equivalente. Por coherencia con F-025 (el mismo mutante sobre
  `CatalogoPostventa` se mató con un test de inmutabilidad), se cerró con
  `test_f027_r3_evento_pendiente_es_inmutable` (`F-027 T8`, `ea95a29`),
  comprobado a mano contra el mutante (`Failed: DID NOT RAISE
  FrozenInstanceError`). Esta 3.ª campaña lo da por muerto.
