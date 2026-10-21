<!-- progress/mutacion_F-051.md -->
# F-051 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-051` el 2026-10-21 07:55.

## Alcance

Origen del diff: **rama** (`708236f5d1fd1ac0fcd1b20846b163faa357790f` .. `feature/F-051-pisar-lineas-cero`).

| Fichero | Líneas en alcance |
|---|---|
| `services/dedicacion-api/application/registro_sigrid.py` | 21 |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py` | 280 |
| `services/dedicacion-transfer/application/services/lecturas_lote.py` | 23 |
| `services/dedicacion-transfer/application/services/reglas_porcentajes.py` | 99 |
| `services/dedicacion-transfer/domain/models/registro_models.py` | 31 |
| `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py` | 137 |
| `services/dedicacion-transfer/interface_adapters/api/app.py` | 9 |
| `services/dedicacion-transfer/prueba_escritura_porcentajes.py` | 27 |
| **Total** | **627** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 136 |
| Mutantes evaluados | 136 |
| Muertos | 136 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 946.3 s |
| SHA de HEAD medido | `d5d61ac1f92c88405a354b27f73240366c2266bb` |
| Línea base (s) — `services/dedicacion-api` | 56.2 |
| Línea base (s) — `services/dedicacion-transfer` | 22.9 |
| Media por mutante evaluado (s) | 7.0 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.


## Historial de campañas (implementer)

Todas en serie, `--workers 1` y completas.

| Campaña | HEAD | Mutantes | Supervivientes | Resolución |
|---|---|---|---|---|
| 1.ª | `e74dbe7` | 138 | 16 | 12 con tests nuevos (cada uno comprobado contra su mutante aplicado a mano), 3 desaparecen con dos simplificaciones del paso 10 (`despues` con `a.can`/`a.tot`; `usadas` vacío), 1 dado por equivalente (`4dea061`) |
| 2.ª | `4dea061` | 134 | 1 | `registro_pipeline.py:1095` `>=` → `>`: **no era equivalente** (review 1, RM5): con un porcentaje < 0,00005 `can` vale 0 y una relectura de `1e-6` cae justo en la frontera. Test `test_f051_r13_editada_a_una_millonesima_de_lo_escrito_no_cuenta` (`d807cce`), que falla con el mutante aplicado a mano («1 failed») |
| 3.ª | `7a5f801` | 134 | 0 | — |
| 4.ª | `d5d61ac` | 136 | **0** | esta campaña, tras T18 (`not es_linea_mensual(hit)` en el paso 6: sus dos mutantes, `and` y sin `not`, muertos) |
