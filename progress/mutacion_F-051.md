<!-- progress/mutacion_F-051.md -->
# F-051 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-051` el 2026-10-21 00:45.

## Alcance

Origen del diff: **rama** (`708236f5d1fd1ac0fcd1b20846b163faa357790f` .. `feature/F-051-pisar-lineas-cero`).

| Fichero | Líneas en alcance |
|---|---|
| `services/dedicacion-api/application/registro_sigrid.py` | 21 |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py` | 278 |
| `services/dedicacion-transfer/application/services/lecturas_lote.py` | 23 |
| `services/dedicacion-transfer/application/services/reglas_porcentajes.py` | 99 |
| `services/dedicacion-transfer/domain/models/registro_models.py` | 31 |
| `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py` | 137 |
| `services/dedicacion-transfer/interface_adapters/api/app.py` | 9 |
| `services/dedicacion-transfer/prueba_escritura_porcentajes.py` | 27 |
| **Total** | **625** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 134 |
| Mutantes evaluados | 134 |
| Muertos | 134 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 1635.8 s |
| SHA de HEAD medido | `7a5f801387e7973fd1a520c7a53e998edfe0971c` |
| Línea base (s) — `services/dedicacion-api` | 86.9 |
| Línea base (s) — `services/dedicacion-transfer` | 47.4 |
| Media por mutante evaluado (s) | 12.2 |
| Timeout efectivo por mutante (s) | 174 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.


## Historial de campañas (implementer)

| Campaña | HEAD | Mutantes | Supervivientes | Resolución |
|---|---|---|---|---|
| 1.ª | `e74dbe7` | 138 | 16 | 12 con tests nuevos (cada uno comprobado contra su mutante aplicado a mano), 3 desaparecen con dos simplificaciones del paso 10 (`despues` con `a.can`/`a.tot`; `usadas` vacío), 1 dado por equivalente (`4dea061`) |
| 2.ª | `4dea061` | 134 | 1 | `registro_pipeline.py:1095` `>=` → `>`: **no era equivalente** (review 1, RM5): con un porcentaje < 0,00005 `can` vale 0 y una relectura de `1e-6` cae justo en la frontera. Test `test_f051_r13_editada_a_una_millonesima_de_lo_escrito_no_cuenta` (`d807cce`), que falla con el mutante aplicado a mano («1 failed») |
| 3.ª | `7a5f801` | 134 | **0** | esta campaña, completa, `--workers 1` |
