<!-- progress/mutacion_F-062.md -->
# F-062 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-062` el 2026-10-24 20:50.

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
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py` | 216 |
| `services/dedicacion-transfer/application/services/lecturas_lote.py` | 119 |
| `services/dedicacion-transfer/application/services/rachas.py` | 1121 |
| `services/dedicacion-transfer/application/services/reglas_incidencias.py` | 29 |
| `services/dedicacion-transfer/config/settings.py` | 4 |
| `services/dedicacion-transfer/domain/models/registro_models.py` | 47 |
| `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py` | 40 |
| `services/dedicacion-transfer/interface_adapters/api/app.py` | 70 |
| `services/dedicacion-transfer/prueba_escritura_porcentajes.py` | 84 |
| **Total** | **1920** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 591 |
| Mutantes evaluados | 591 |
| Muertos | 560 |
| Supervivientes | 31 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 3322.3 s |
| SHA de HEAD medido | `30ef3b41ca990b2abb80b644182c6e2788d73160` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-062_jm_zy5v0/wk_0/services/dedicacion-api` | 48.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-062_jm_zy5v0/wk_0/services/dedicacion-transfer` | 29.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-062_jm_zy5v0/wk_1/services/dedicacion-api` | 48.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-062_jm_zy5v0/wk_1/services/dedicacion-transfer` | 29.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-062_jm_zy5v0/wk_2/services/dedicacion-api` | 48.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-062_jm_zy5v0/wk_2/services/dedicacion-transfer` | 29.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-062_jm_zy5v0/wk_3/services/dedicacion-api` | 48.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-062_jm_zy5v0/wk_3/services/dedicacion-transfer` | 29.4 |
| Media por mutante evaluado (s) | 5.6 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/dedicacion-api/application/traza_incidencias.py:103` [logico]

- Original: `devuelta = devolver is not None and devolver["accion"] in _HECHAS`
- Mutado:   `devuelta = devolver is not None or devolver["accion"] in _HECHAS`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: Reaplicado a mano en un worktree limpio de `30ef3b4` (el HEAD medido) y con el intérprete del árbol principal, la suite de la api cae (15 fallos; el primero `test_f030_r30_identidad.py::test_f030_r39_traza_escrita_guarda_ide_y_dia_por_rol`, y `test_f062_r17_traza_devolver_anula_y_borra_la_quitada_sin_ide` lo caza de lleno). Con el mutante, toda incidencia sin `devolver` hace `None["accion"]`. La campaña lo dio por vivo sin serlo: aviso al líder (posible defecto del arnés).
> Decisión: falso superviviente de la campaña paralela.

### 2. `services/dedicacion-api/application/traza_incidencias.py:127` [logico]

- Original: `if n.get("tipo") != "quitada" or not inc_id or n.get("en_sigrid"):`
- Mutado:   `if n.get("tipo") != "quitada" and not inc_id or n.get("en_sigrid"):`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: Ningún test mandaba un `solo_sigrid` con `incidencia_id`. `test_f062_payload_rachas.py::test_f062_r17_traza_solo_sigrid_nunca_borra_aunque_traiga_incidencia`.
> Decisión: test nuevo.

### 3. `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:195` [entero]

- Original: `o = ObraEntrada(ide=int(obride or 0))`
- Mutado:   `o = ObraEntrada(ide=int(obride or 1))`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: Ningún test pasaba una línea sin obra. `test_f062_pipeline_rachas.py::test_f062_r5_obra_de_linea_sin_obra_ni_centro_es_cero`.
> Decisión: test nuevo.

### 4. `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:196` [entero]

- Original: `o.cenide = int(cenide or 0)         # como `obra_por_ide` (F-037)`
- Mutado:   `o.cenide = int(cenide or 1)         # como `obra_por_ide` (F-037)`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: Ningún test pasaba una línea sin centro. `test_f062_pipeline_rachas.py::test_f062_r5_obra_de_linea_sin_obra_ni_centro_es_cero`.
> Decisión: test nuevo.

### 5. `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:484` [logico]

- Original: `c.hora_ide, c.pre = ciz.horide, float(ciz.pre or 0.0)`
- Mutado:   `c.hora_ide, c.pre = ciz.horide, float(ciz.pre and 0.0)`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: El `CIZ` de `reshor` de los dobles tenía `pre` 0.0. `test_f062_pipeline_rachas.py::test_f062_r12_ejecutar_el_cierre_lleva_el_pre_del_ciz_y_sin_partida_0`.
> Decisión: test nuevo.

### 6. `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:1290` [aritmetico]

- Original: `pos_por_parte[hmoide] += int(self._st.paso_pos)`
- Mutado:   `pos_por_parte[hmoide] -= int(self._st.paso_pos)`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: Nadie miraba la `pos` del cierre. `test_f062_pipeline_rachas.py::test_f062_r12_ejecutar_el_cierre_con_la_partida_y_la_cuenta_del_inicio` (pos 192).
> Decisión: test nuevo.

### 7. `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:1300` [logico]

- Original: `paride=int(c.paride or 0), caaide=int(c.caaide or 0)))`
- Mutado:   `paride=int(c.paride and 0), caaide=int(c.caaide or 0)))`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: Los inicios de los tests tenían partida 0. `test_f062_pipeline_rachas.py::test_f062_r12_ejecutar_el_cierre_con_la_partida_y_la_cuenta_del_inicio`.
> Decisión: test nuevo.

### 8. `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:1300` [entero]

- Original: `paride=int(c.paride or 0), caaide=int(c.caaide or 0)))`
- Mutado:   `paride=int(c.paride or 1), caaide=int(c.caaide or 0)))`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: Sin partida en el inicio, 0. `test_f062_pipeline_rachas.py::test_f062_r12_ejecutar_el_cierre_lleva_el_pre_del_ciz_y_sin_partida_0`.
> Decisión: test nuevo.

### 9. `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:1300` [logico]

- Original: `paride=int(c.paride or 0), caaide=int(c.caaide or 0)))`
- Mutado:   `paride=int(c.paride or 0), caaide=int(c.caaide and 0)))`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: Los inicios de los tests tenían cuenta 0. `test_f062_pipeline_rachas.py::test_f062_r12_ejecutar_el_cierre_con_la_partida_y_la_cuenta_del_inicio`.
> Decisión: test nuevo.

### 10. `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:1300` [entero]

- Original: `paride=int(c.paride or 0), caaide=int(c.caaide or 0)))`
- Mutado:   `paride=int(c.paride or 0), caaide=int(c.caaide or 1)))`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: Sin cuenta en el inicio, 0. `test_f062_pipeline_rachas.py::test_f062_r12_ejecutar_el_cierre_lleva_el_pre_del_ciz_y_sin_partida_0`.
> Decisión: test nuevo.

### 11. `services/dedicacion-transfer/application/services/lecturas_lote.py:570` [comparacion]

- Original: `and int(desde) <= l.fecha_int <= int(hasta)`
- Mutado:   `and int(desde) < l.fecha_int <= int(hasta)`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: Ninguna línea caía en el primer día de la ventana pedida. `test_f062_lote.py::test_f062_r19_lote_la_ventana_de_memoria_incluye_sus_dos_extremos`.
> Decisión: test nuevo.

### 12. `services/dedicacion-transfer/application/services/lecturas_lote.py:570` [comparacion]

- Original: `and int(desde) <= l.fecha_int <= int(hasta)`
- Mutado:   `and int(desde) <= l.fecha_int < int(hasta)`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: Ninguna línea caía en el último día de la ventana pedida. `test_f062_lote.py::test_f062_r19_lote_la_ventana_de_memoria_incluye_sus_dos_extremos`.
> Decisión: test nuevo.

### 13. `services/dedicacion-transfer/application/services/rachas.py:93` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: Nadie comprobaba que una `Racha` leída no se cambia. `test_f062_rachas.py::test_f062_d5_una_racha_leida_no_se_cambia`.
> Decisión: test nuevo.

### 14. `services/dedicacion-transfer/application/services/rachas.py:113` [entero]

- Original: `0 if es_inicio(x) else 1,`
- Mutado:   `0 if es_inicio(x) else 2,`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: La clave de orden de `emparejar` solo compara el 0 del inicio con el valor del `CIZ`: con 1 o con 2 el orden es el mismo (inicio antes que `CIZ` el mismo día). Ningún test puede distinguirlos.
> Decisión: mutante equivalente, justificado.

### 15. `services/dedicacion-transfer/application/services/rachas.py:142` [comparacion]

- Original: `and 1 <= inc.desde <= inc.hasta <= ultimo):`
- Mutado:   `and 1 <= inc.desde < inc.hasta <= ultimo):`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: Ninguna incidencia de un solo día. `test_f062_rachas.py::test_f062_r11_fechas_de_un_solo_dia_y_los_extremos_del_mes`.
> Decisión: test nuevo.

### 16. `services/dedicacion-transfer/application/services/rachas.py:160` [entero]

- Original: `(x[0].codigo or "").strip(), x[1][0],`
- Mutado:   `(x[0].codigo or "").strip(), x[1][1],`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: El orden por el último día solo difiere con incidencias que se solapan (la api no las deja pasar). `test_f062_rachas.py::test_f062_d11_cadenas_por_su_primer_dia`.
> Decisión: test nuevo.

### 17. `services/dedicacion-transfer/application/services/rachas.py:226` [entero]

- Original: `return mes - 1 if mes % 100 > 1 else (mes // 100 - 1) * 100 + 12`
- Mutado:   `return mes - 1 if mes % 100 > 2 else (mes // 100 - 1) * 100 + 12`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: Ningún test registraba febrero. `test_f062_rachas.py::test_f062_r12_mes_anterior_en_cada_frontera`.
> Decisión: test nuevo.

### 18. `services/dedicacion-transfer/application/services/rachas.py:239` [aritmetico]

- Original: `return ultimo_dia(cadena.hasta // 10000, cadena.hasta // 100 % 100)`
- Mutado:   `return ultimo_dia(cadena.hasta * 10000, cadena.hasta // 100 % 100)`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: El destino solo cuenta si el `CIZ` de la previa ya está el último día y no se puede mover. `test_f062_rachas.py::test_f062_r10_previa_que_ya_cierra_el_ultimo_dia_del_mes_no_se_mueve`.
> Decisión: test nuevo.

### 19. `services/dedicacion-transfer/application/services/rachas.py:434` [entero]

- Original: `a.paride, a.caa_ide = int(inicio.paride or 0), int(inicio.caaide or 0)`
- Mutado:   `a.paride, a.caa_ide = int(inicio.paride or 1), int(inicio.caaide or 0)`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: Los inicios de los tests tenían partida. `test_f062_rachas.py::test_f062_r5_decidir_el_ciz_en_el_parte_del_inicio_con_su_partida`.
> Decisión: test nuevo.

### 20. `services/dedicacion-transfer/application/services/rachas.py:434` [entero]

- Original: `a.paride, a.caa_ide = int(inicio.paride or 0), int(inicio.caaide or 0)`
- Mutado:   `a.paride, a.caa_ide = int(inicio.paride or 0), int(inicio.caaide or 1)`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: Los inicios de los tests tenían cuenta. `test_f062_rachas.py::test_f062_r5_decidir_el_ciz_en_el_parte_del_inicio_con_su_partida`.
> Decisión: test nuevo.

### 21. `services/dedicacion-transfer/application/services/rachas.py:443` [logico]

- Original: `"mes": int(m.mes), "paride": int(m.paride or 0),`
- Mutado:   `"mes": int(m.mes), "paride": int(m.paride and 0),`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: Las que continúan la cadena tenían partida 0. `test_f062_rachas.py::test_f062_r8_decidir_la_que_continua_la_cadena_lleva_su_partida`.
> Decisión: test nuevo.

### 22. `services/dedicacion-transfer/application/services/rachas.py:443` [entero]

- Original: `"mes": int(m.mes), "paride": int(m.paride or 0),`
- Mutado:   `"mes": int(m.mes), "paride": int(m.paride or 1),`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: Las que continúan la cadena tenían partida. `test_f062_rachas.py::test_f062_r8_decidir_la_que_continua_la_cadena_lleva_su_partida`.
> Decisión: test nuevo.

### 23. `services/dedicacion-transfer/application/services/rachas.py:528` [entero]

- Original: `return _omitir_todo(cadena, base, base[0].motivo)`
- Mutado:   `return _omitir_todo(cadena, base, base[1].motivo)`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: `decidir_incidencia` omite «LAS DOS, con el mismo motivo» (su docstring y cada `return omitir(motivo)` de `reglas_incidencias.py`): cuando alguna de la base omite, `base[0].motivo == base[1].motivo`. Distinguirlas exigiría una base que el código no produce.
> Decisión: mutante equivalente, justificado.

### 24. `services/dedicacion-transfer/application/services/rachas.py:665` [comparacion]

- Original: `or _mes(racha.cierre.fecha_int) <= mes:`
- Mutado:   `or _mes(racha.cierre.fecha_int) < mes:`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: Ningún `CIZ` suelto del mismo mes cerraba el inicio propio. `test_f062_rachas.py::test_f062_r21_un_ciz_suelto_del_mismo_mes_no_hace_seguir_la_racha`.
> Decisión: test nuevo.

### 25. `services/dedicacion-transfer/application/services/rachas.py:738` [logico]

- Original: `if (sk.startswith(PREFIJO_SYNCKEY_INCIDENCIA) and len(resto) == 2`
- Mutado:   `if (sk.startswith(PREFIJO_SYNCKEY_INCIDENCIA) or len(resto) == 2`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: Ninguna `synckey` ajena con la cola `{n}:ini`. `test_f062_rachas.py::test_f062_r12_synckey_de_cierre_de_un_inicio_ajeno_que_lo_parece`.
> Decisión: test nuevo.

### 26. `services/dedicacion-transfer/application/services/rachas.py:739` [logico]

- Original: `and resto[0].isdigit() and resto[1] == "ini"):`
- Mutado:   `or resto[0].isdigit() and resto[1] == "ini"):`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: Ninguna `synckey` ajena con la cola `{n}:ini`. `test_f062_rachas.py::test_f062_r12_synckey_de_cierre_de_un_inicio_ajeno_que_lo_parece`.
> Decisión: test nuevo.

### 27. `services/dedicacion-transfer/application/services/rachas.py:846` [entero]

- Original: `ini, partes_m1.get((int(ini.obride or 0), m1 // 100,`
- Mutado:   `ini, partes_m1.get((int(ini.obride or 1), m1 // 100,`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: Ningún inicio sin obra. `test_f062_rachas.py::test_f062_c12_cierres_un_inicio_sin_obra_no_busca_parte_de_otra`.
> Decisión: test nuevo.

### 28. `services/dedicacion-transfer/application/services/rachas.py:867` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: Nadie comprobaba que una `LineaVista` no se cambia. `test_f062_rachas.py::test_f062_r30_la_linea_vista_no_se_cambia`.
> Decisión: test nuevo.

### 29. `services/dedicacion-transfer/application/services/rachas.py:898` [booleano]

- Original: `designado: bool = True) -> list[NoCoincide]:`
- Mutado:   `designado: bool = False) -> list[NoCoincide]:`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: El pipeline y los tests pasaban siempre `designado`. `test_f062_rachas.py::test_f062_c11_no_coincide_por_defecto_el_recurso_es_el_designado`.
> Decisión: test nuevo.

### 30. `services/dedicacion-transfer/interface_adapters/api/app.py:219` [booleano]

- Original: `def _respuesta_preflight(pf, con_rachas: bool = False) -> dict:`
- Mutado:   `def _respuesta_preflight(pf, con_rachas: bool = True) -> dict:`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: Los tests de equivalencia comparaban dos respuestas con el mismo defecto. `test_f062_pipeline_rachas.py::test_f062_r22_contrato_sin_pedirlas_la_respuesta_no_lleva_rachas`.
> Decisión: test nuevo.

### 31. `services/dedicacion-transfer/prueba_escritura_porcentajes.py:164` [aritmetico]

- Original: `return [LineaEntrada(registro_id=REGISTRO_TESTIGO + n, recurso_ide=r,`
- Mutado:   `return [LineaEntrada(registro_id=REGISTRO_TESTIGO - n, recurso_ide=r,`

#### Análisis (implementer)

> Por qué ningún test lo cazaba: Los tests del script usaban un solo `--cierres`. `test_f062_pipeline_rachas.py::test_f062_r12_script_una_linea_testigo_por_recurso_de_cierres`.
> Decisión: test nuevo.


## Reverificación de los supervivientes (implementer, 2026-10-24)

Tras los tests nuevos (`3e2cee8`, `6266a9f`), cada uno de los 31 se volvió a
aplicar **en serie**, en un `git worktree` limpio de `6266a9f`, con el
intérprete del árbol principal y `pytest -x -q --tb=no -p no:cacheprovider`
(lo mismo que la campaña), restaurando el fichero tras cada uno:

| Resultado | Cuántos | Cuáles (nº de esta lista) |
|---|---|---|
| Muerto por un test nuevo | 28 | 2-13, 15-22, 24-31 |
| Muerto por los tests que ya había (falso superviviente) | 1 | 1 |
| Vivo: equivalente justificado | 2 | 14 (`rachas.py:113`), 23 (`rachas.py:528`) |

Cada «muerto» nombra el test que cae en la traza de la reverificación; el
del nº 1 ya caía en `30ef3b4` (`test_f030_r30_identidad.py::test_f030_r39_…`).
**Aviso para el líder (arnés):** la campaña paralela dio el nº 1 por vivo y,
reaplicado igual en serie en un worktree del mismo HEAD, la suite cae. No se
ha localizado la causa; no se tocó `harness/`.
