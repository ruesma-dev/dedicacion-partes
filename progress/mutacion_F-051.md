<!-- progress/mutacion_F-051.md -->
# F-051 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-051` el 2026-10-20 23:31.

## Alcance

Origen del diff: **rama** (`2c75a1c332776f736ccd6bc78131aa47db228579` .. `feature/F-051-pisar-lineas-cero`).

| Fichero | Líneas en alcance |
|---|---|
| `services/dedicacion-api/application/registro_sigrid.py` | 21 |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py` | 277 |
| `services/dedicacion-transfer/application/services/lecturas_lote.py` | 21 |
| `services/dedicacion-transfer/application/services/reglas_porcentajes.py` | 99 |
| `services/dedicacion-transfer/domain/models/registro_models.py` | 31 |
| `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py` | 137 |
| `services/dedicacion-transfer/interface_adapters/api/app.py` | 9 |
| `services/dedicacion-transfer/prueba_escritura_porcentajes.py` | 27 |
| **Total** | **622** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 134 |
| Mutantes evaluados | 134 |
| Muertos | 133 |
| Supervivientes | 1 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 1791.9 s |
| SHA de HEAD medido | `4dea0612f250ae8c98b1ff37f4879206a0ea2da7` |
| Línea base (s) — `services/dedicacion-api` | 57.5 |
| Línea base (s) — `services/dedicacion-transfer` | 23.6 |
| Media por mutante evaluado (s) | 13.4 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:1095` [comparacion]

- Original: `- t["despues"]["can"]) >= 0.000001 \`
- Mutado:   `- t["despues"]["can"]) > 0.000001 \`

#### Análisis (implementer, 2026-10-20)

> Por qué ningún test lo caza: es la comprobación de R13 tras escribir
> (`_comprobar_escrito`): la editada cuenta como nuestra si
> `abs(hit.can - despues.can) < 0.000001`. `>=` y `>` solo difieren cuando la
> diferencia vale **exactamente** el `float` 1e-6. `despues.can` es el `can`
> de la acción, que las reglas redondean a 4 decimales
> (`reglas_porcentajes.py`, `can = round(porcentaje, 4)`), y la relectura
> trae lo que hay en Sigrid. Búsqueda exhaustiva (scratchpad del
> implementer): para los 9.999 valores `p = k/10000` y, para cada uno, los
> 81 `float` alrededor de `p + 1e-6` (±40 ulp) y `p - 1e-6`, ninguno da
> `abs(v - p) == 1e-6`. No hay entrada alcanzable que separe al mutante del
> original: los tests de R13 (`…r13_editada_con_otro_can_…`, `…guarda_fallida…`)
> cubren los dos lados lejos de la frontera.
> Decisión: **mutante equivalente**, justificado; sin test nuevo (no existe
> entrada que lo mate). Pendiente de que el humano acepte la justificación
> (rigor `critico`, `tasks.md`).

#### Primera campaña (para la traza)

La primera campaña (HEAD `e74dbe7`, 138 mutantes, `--workers 1`, 3162,8 s)
dejó **16 supervivientes**. Quince se resolvieron así (commit `4dea061`), y
la segunda campaña, la de arriba, los da por muertos o ya no existen:

| Mutante (1.ª campaña) | Resolución |
|---|---|
| api `registro_sigrid.py:274` `==` → `!=` | test `…r16_el_ide_va_a_su_asignacion_y_a_ninguna_otra` |
| pipeline `:567` `hmores_ide or 0` → `or 1` | test `…r15_sin_ide_no_se_mira_la_fila_de_otro_ide` |
| pipeline `:952-953` redondeo de `can`/`tot` en `despues` (4→5, 2→3) | código: `despues` usa `a.can` y `a.tot`, ya redondeados por las reglas (el mutante deja de existir) |
| pipeline `:955` y `:962` `paride or 0` → `or 1` (×2) | test `…r8_edita_sin_partida_confirmada_con_partida_cero` |
| pipeline `:955` y `:962` `caa_ide or 0` → `or 1` (×2) | test `…r8_edita_sin_cuenta_con_cuenta_cero` |
| pipeline `:1019` `usadas = {pz[1] …}` → `pz[2]` | código: `usadas` arranca vacío (una línea al 0 % nunca es choque; el mutante deja de existir) |
| pipeline `:1090` `>=` → `>` | equivalente: el de arriba |
| `lecturas_lote.py:399` `<=` → `<` | test: `…r15_lote_sigue_sirviendo_lineas_por_synckey` pide justo las precargadas |
| `registro_models.py:182` `enlazada = False` → `True` | test `…r12_una_linea_leida_sin_enlaces_no_es_enlazada` |
| cliente `:698` `hmoide or 0` → `or 1` | test `…r15_fila_sin_parte_queda_con_hmoide_cero` |
| cliente `:870` `round(…, 2)` → `3` | test `…r8_redondeos_como_el_insert` (cifras con tercera cifra) |
| cliente `:871` `paride or 0` / `caaide or 0` → `or 1` | test `…r8_sin_partida_ni_cuenta_van_a_cero` |

Cada test nuevo se comprobó contra su mutante aplicado a mano (12 de 12
**muertos**, script del scratchpad del implementer).

