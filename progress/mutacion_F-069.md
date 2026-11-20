<!-- progress/mutacion_F-069.md -->
# F-069 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-069 --workers 4` el 2026-11-20 11:12.

## Alcance

Origen del diff: **rama** (`538124397f4cc1c78b23d40fd22715111cbdc30a` .. `feature/F-069-importe-caja-km`).

| Fichero | Líneas en alcance | Mutantes generados |
|---|---|---|
| `services/dedicacion-api/application/registro_sigrid.py` | 58 | 17 |
| `services/dedicacion-api/application/sync_pipeline.py` | 20 | 4 |
| `services/dedicacion-api/application/traer_sigrid.py` | 165 | 52 |
| `services/dedicacion-api/application/use_cases.py` | 328 | 96 |
| `services/dedicacion-api/domain/errors.py` | 8 | 0 — sin mutantes |
| `services/dedicacion-api/domain/importes.py` | 187 | 58 |
| `services/dedicacion-api/domain/models.py` | 46 | 3 |
| `services/dedicacion-api/domain/ports.py` | 45 | 0 — sin mutantes |
| `services/dedicacion-api/infrastructure/db/orm_models.py` | 42 | 16 |
| `services/dedicacion-api/infrastructure/db/repositories.py` | 121 | 27 |
| `services/dedicacion-api/infrastructure/transfer/transfer_client.py` | 9 | 1 |
| `services/dedicacion-api/interface_adapters/api/app.py` | 2 | 1 |
| `services/dedicacion-api/interface_adapters/api/deps.py` | 12 | 0 — sin mutantes |
| `services/dedicacion-api/interface_adapters/api/routes.py` | 54 | 1 |
| `services/dedicacion-api/interface_adapters/api/schemas.py` | 83 | 26 |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py` | 125 | 53 |
| `services/dedicacion-transfer/application/pipelines/registro_vinculados.py` | 31 | 5 |
| `services/dedicacion-transfer/application/services/lecturas_lote.py` | 21 | 18 |
| `services/dedicacion-transfer/application/services/porcentajes_existentes.py` | 29 | 1 |
| `services/dedicacion-transfer/application/services/reglas_vinculados.py` | 135 | 34 |
| `services/dedicacion-transfer/application/services/texto_linea.py` | 94 | 24 |
| `services/dedicacion-transfer/domain/models/registro_models.py` | 51 | 3 |
| `services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py` | 69 | 31 |
| `services/dedicacion-transfer/interface_adapters/api/app.py` | 13 | 2 |
| `services/dedicacion-transfer/prueba_escritura_porcentajes.py` | 6 | 0 — sin mutantes |
| **Total** | **1754** | **473** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 473 |
| Mutantes evaluados | 159 |
| Muertos | 130 |
| Supervivientes | 29 (todos medidos: sin mapa no se poda) |
| Timeouts | 0 |
| Indeterminados | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 2941.2 s |
| SHA de HEAD medido | `6b6d637d614ec152d5a91d04ea2984323a5e043c` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_c6hynsi7/wk_0/services/dedicacion-api` | 118.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_c6hynsi7/wk_0/services/dedicacion-transfer` | 60.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_c6hynsi7/wk_1/services/dedicacion-api` | 118.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_c6hynsi7/wk_1/services/dedicacion-transfer` | 63.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_c6hynsi7/wk_2/services/dedicacion-api` | 118.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_c6hynsi7/wk_2/services/dedicacion-transfer` | 61.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_c6hynsi7/wk_3/services/dedicacion-api` | 118.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_c6hynsi7/wk_3/services/dedicacion-transfer` | 61.9 |
| Media por mutante evaluado (s) | 18.5 |
| Timeout efectivo por mutante (s) | 238 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Un mutante por línea | sí — 473 generados → 264 candidatos, uno por línea |
| Muestreo | sí — 159 de 264 candidatos, semilla `20261030`, nivel `critico`; tope: 60 % de 264 candidatos, acotado a [100, 300] |
| Selección de tests | desactivada (por defecto): todo con la suite entera, como la 1.9.0 |
| SHA del mapa | n/d |
| Medición del mapa (s) | n/d |
| Tests en la suite | n/d |
| Tamaño medio del subconjunto | n/d |
| Revalidados con la suite entera | n/d |
| Subconjuntos descartados | n/d |
| Podados (sin ejecutar) | n/d |
| Tiempo ahorrado por la poda (s) — derivado: podados × línea base | n/d |
| Media por mutante juzgado con la suite entera (s) | 65.0 (159 mutantes) |

## Cómo se juzgó

- Cada mutante con la **suite entera**, como en la 1.9.0: la selección de tests está apagada por defecto (en la suite del propio arnés costó más de lo que ahorró). Se enciende con `--con-seleccion` en la orden o con `mutacion.seleccion_de_tests: true` en `harness/rigor.local.json`; la orden manda sobre la clave.


## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/dedicacion-api/application/registro_sigrid.py:169` [booleano]

- Original: `"copiado": bool(getattr(fuente, "copiado", False)`
- Mutado:   `"copiado": bool(getattr(fuente, "copiado", True)`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `fuente` es `None` (no hay cantidad del mes) o un `ImporteMes`/`SubfilaVinculado`, que siempre tienen `copiado`: el valor por defecto de `getattr` solo se usa con `fuente` `None`, y entonces `cantidad` es `None` y `... and cantidad is not None` da `False` con cualquier defecto.
> Decisión: **mutante equivalente**. No hay entrada que distinga `False` de `True` como defecto.

### 2. `services/dedicacion-api/application/traer_sigrid.py:154` [logico]

- Original: `if x.synckey and (x.synckey not in por_clave`
- Mutado:   `if x.synckey or (x.synckey not in por_clave`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: El único test de «el de menor `ide` por `synckey`» daba las líneas en orden descendente: con `or`, la última pisa siempre y acertaba por casualidad.
> Decisión: **test nuevo** (commit `2fe6031`). Reproducido a mano (aplicado con `sed` y descartado con `git checkout`): `test_f069_r32_titular_por_su_synckey_el_de_menor_ide_en_cualquier_orden` cae (`('linea', 10, (694, False), 'b') != (... 'a')`).

### 3. `services/dedicacion-api/application/traer_sigrid.py:342` [veracidad]

- Original: `if vid is None:`
- Mutado:   `if not vid:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `vid` es el `vinculado_ide` de la subfila (el `res.ide` de Sigrid, siempre > 0) o `None` para la línea del titular: nunca `0`.
> Decisión: **mutante equivalente**. `is None` y `not` solo difieren en `0`, que no existe.

### 4. `services/dedicacion-api/application/use_cases.py:1070` [veracidad]

- Original: `return None if valor is None else Decimal(str(valor))`
- Mutado:   `return None if not valor else Decimal(str(valor))`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `_decimal_o_none` solo lee snapshots de eventos, donde la cantidad se guarda como texto (`str(Decimal)` en `_cantidad_de_subfila` y `_snapshot_importes`) o `None`: `"0.00"` es verdadero, y la cadena vacía no se escribe nunca.
> Decisión: **mutante equivalente**. Mismo resultado para todo lo que puede haber en un snapshot.

### 5. `services/dedicacion-api/application/use_cases.py:1256` [veracidad]

- Original: `if v.partida_ide is not None or _cantidad_de_subfila(v)`
- Mutado:   `if v.partida_ide or _cantidad_de_subfila(v)`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `partida_ide` es un `obrparpar.ide` de Sigrid (> 0) o `None`.
> Decisión: **mutante equivalente**. `is not None` y la veracidad solo difieren en `0`, que no existe.

### 6. `services/dedicacion-api/application/use_cases.py:1304` [entero]

- Original: `foto.items(), key=lambda kv: (kv[0][0], kv[0][1] or 0, kv[0][2]))]`
- Mutado:   `foto.items(), key=lambda kv: (kv[0][0], kv[1][1] or 0, kv[0][2]))]`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: Ningún test tenía dos cajas del mismo vinculado en dos obras con `copiado` distinto: ordenar por `copiado` daba el mismo orden.
> Decisión: **test nuevo** (commit `2fe6031`). Reproducido a mano (aplicado con `sed` y descartado con `git checkout`): `test_f069_r7_el_snapshot_ordena_por_vinculado_y_obra` cae.

### 7. `services/dedicacion-api/application/use_cases.py:1312` [booleano]

- Original: `bool(b.get("es_postventa", False))):`
- Mutado:   `bool(b.get("es_postventa", True))):`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: Los snapshots `IMPORTES` nacen en F-069 y los escribe siempre `_snapshot_importes`, que pone `es_postventa` en cada elemento: el defecto de `get` no se usa nunca.
> Decisión: **mutante equivalente**. Código defensivo sin entrada que lo alcance.

### 8. `services/dedicacion-api/application/use_cases.py:1329` [booleano]

- Original: `cambio = False`
- Mutado:   `cambio = True`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: El booleano que devuelve `_aplicar_foto` no lo lee nadie: deshacer (l. 442) y `GuardarImportes` (l. 1404) lo descartan; `GuardarImportes` decide por `despues != antes`.
> Decisión: **mutante equivalente**. Valor de retorno muerto. Propuesta para el humano (no toco producción): quitarlo o usarlo.

### 9. `services/dedicacion-api/application/use_cases.py:1335` [booleano]

- Original: `cambio = True`
- Mutado:   `cambio = False`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: Igual que el de la l. 1329: el valor de retorno de `_aplicar_foto` no lo usa ningún llamador.
> Decisión: **mutante equivalente**. Valor de retorno muerto (misma propuesta).

### 10. `services/dedicacion-api/domain/importes.py:36` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: Ningún test comprobaba que `TipoCantidad` fuera inmutable.
> Decisión: **test nuevo** (commit `2fe6031`). Reproducido a mano (aplicado con `sed` y descartado con `git checkout`): `test_f069_r1_r3_tipo_e_importe_del_mes_son_inmutables` cae.

### 11. `services/dedicacion-api/domain/importes.py:107` [logico]

- Original: `if isinstance(valor, bool) or not isinstance(`
- Mutado:   `if isinstance(valor, bool) and not isinstance(`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: Con `and`, un booleano o un no número (lista, dict) se salta el primer `if`, pero `Decimal(str(valor))` falla (`"True"`, `"[1]"`, `"{}"`) y lanza el mismo `ImporteInvalido` con el mismo mensaje «no es un número».
> Decisión: **mutante equivalente**. Mismo error y mismo texto para toda entrada JSON.

### 12. `services/dedicacion-api/domain/importes.py:133` [veracidad]

- Original: `if texto is None:`
- Mutado:   `if not texto:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: Con `""`, el original sigue: `strip()` da `""` y `return limpio or None` devuelve `None`, lo mismo que el mutante.
> Decisión: **mutante equivalente**. Mismo resultado para todo texto vacío.

### 13. `services/dedicacion-api/domain/models.py:128` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: Ningún test comprobaba que `ImporteMes` fuera inmutable (y hashable).
> Decisión: **test nuevo** (commit `2fe6031`). Reproducido a mano (aplicado con `sed` y descartado con `git checkout`): `test_f069_r1_r3_tipo_e_importe_del_mes_son_inmutables` cae.

### 14. `services/dedicacion-api/infrastructure/db/repositories.py:574` [comparacion]

- Original: `AsignacionORM.trabajador_ide == trabajador_ide,`
- Mutado:   `AsignacionORM.trabajador_ide != trabajador_ide,`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `poner_comentario` no tenía test de su SQL (los de uso van con dobles del repositorio).
> Decisión: **test nuevo** (commit `2fe6031`). Reproducido a mano (aplicado con `sed` y descartado con `git checkout`): `test_f069_r32_poner_comentario_solo_en_esa_linea` cae.

### 15. `services/dedicacion-api/infrastructure/db/repositories.py:575` [comparacion]

- Original: `AsignacionORM.obra_ide == obra_ide,`
- Mutado:   `AsignacionORM.obra_ide != obra_ide,`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: Como el de la l. 574.
> Decisión: **test nuevo** (commit `2fe6031`). Reproducido a mano (aplicado con `sed` y descartado con `git checkout`): `test_f069_r32_poner_comentario_solo_en_esa_linea` cae.

### 16. `services/dedicacion-api/infrastructure/db/repositories.py:576` [comparacion]

- Original: `AsignacionORM.es_postventa == bool(es_postventa),`
- Mutado:   `AsignacionORM.es_postventa != bool(es_postventa),`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: Como el de la l. 574.
> Decisión: **test nuevo** (commit `2fe6031`). Reproducido a mano (aplicado con `sed` y descartado con `git checkout`): `test_f069_r32_poner_comentario_solo_en_esa_linea` cae.

### 17. `services/dedicacion-api/infrastructure/db/repositories.py:819` [veracidad]

- Original: `cantidad=None if f.cantidad is None`
- Mutado:   `cantidad=None if not f.cantidad`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: Ningún test leía una cantidad `0` de la base: 0 € es «a 0, nada que escribir», no «sin cantidad».
> Decisión: **test nuevo** (commit `2fe6031`). Reproducido a mano (aplicado con `sed` y descartado con `git checkout`): `test_f069_r3_una_cantidad_cero_se_lee_como_cero` cae.

### 18. `services/dedicacion-api/infrastructure/db/repositories.py:834` [comparacion]

- Original: `.where(PeriodoORM.anio == anio, PeriodoORM.mes == mes,`
- Mutado:   `.where(PeriodoORM.anio != anio, PeriodoORM.mes == mes,`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: El test de `importes_del_mes_de` miraba el `JOIN` y el `IN`, no el filtro por año.
> Decisión: **test nuevo** (commit `2fe6031`). Reproducido a mano (aplicado con `sed` y descartado con `git checkout`): `test_f069_r16_importes_del_mes_de_ese_anio_y_mes` cae.

### 19. `services/dedicacion-api/infrastructure/db/repositories.py:850` [comparacion]

- Original: `== ImporteVinculadoORM.vinculado_ide)`
- Mutado:   `!= ImporteVinculadoORM.vinculado_ide)`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: La consulta de `PgImporteRepository` no tenía test de su SQL.
> Decisión: **test nuevo** (commit `2fe6031`). Reproducido a mano (aplicado con `sed` y descartado con `git checkout`): `test_f069_r3_las_del_mes_se_cruzan_con_su_vinculado` cae.

### 20. `services/dedicacion-api/interface_adapters/api/schemas.py:151` [veracidad]

- Original: `unidad: str | None = Field(default=None, exclude_if=lambda v: v is None)`
- Mutado:   `unidad: str | None = Field(default=None, exclude_if=lambda v: not v)`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `unidad` sale de un `TipoCantidad` validado al cargar `config.yaml` (`eur` | `km`): nunca `""`.
> Decisión: **mutante equivalente**. `is None` y `not` solo difieren en la cadena vacía, que no llega.

### 21. `services/dedicacion-api/interface_adapters/api/schemas.py:153` [veracidad]

- Original: `exclude_if=lambda v: v is None)`
- Mutado:   `exclude_if=lambda v: not v)`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: Ningún test pintaba una caja a 0: con `not v`, la cantidad `0` desaparecía del JSON.
> Decisión: **test nuevo** (commit `2fe6031`). Reproducido a mano (aplicado con `sed` y descartado con `git checkout`): `test_f069_r10_una_caja_a_cero_y_sin_copiado_sale_con_sus_claves` cae.

### 22. `services/dedicacion-api/interface_adapters/api/schemas.py:156` [veracidad]

- Original: `exclude_if=lambda v: v is None)`
- Mutado:   `exclude_if=lambda v: not v)`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: Es el `comentario` de la subfila: un vacío nunca llega (`validar_comentario` da `None` y la base guarda `None`), y uno no vacío es verdadero.
> Decisión: **mutante equivalente**. `is None` y `not` solo difieren en `""`, que no llega.

### 23. `services/dedicacion-api/interface_adapters/api/schemas.py:500` [veracidad]

- Original: `if tipo is None:`
- Mutado:   `if not tipo:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `tipo` es un `TipoCantidad` (dataclass sin `__bool__` ni `__len__`: siempre verdadero) o `None`.
> Decisión: **mutante equivalente**. Mismo resultado para todo valor posible.

### 24. `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:577` [entero]

- Original: `obride = int(destino.ide or 0) if forzada else None`
- Mutado:   `obride = int(destino.ide or 1) if forzada else None`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: Con `forzada`, `destino` viene de `_obra_destino`: `obra_por_codigo` devuelve una obra leída de Sigrid con su `ide` (clave primaria) o lanza `RuntimeError`. El `or 0` no se usa nunca, ni el `or 1`.
> Decisión: **mutante equivalente**. Rama inalcanzable con `forzada`.

### 25. `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:1498` [entero]

- Original: `obride = (int(pf.obra_destino.ide or 0) if pf.forzada_pruebas`
- Mutado:   `obride = (int(pf.obra_destino.ide or 1) if pf.forzada_pruebas`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: Como el de la l. 577: en modo pruebas `pf.obra_destino` es la obra de pruebas leída de Sigrid, con `ide`.
> Decisión: **mutante equivalente**. Rama inalcanzable con `forzada_pruebas`.

### 26. `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:1511` [veracidad]

- Original: `hora=p.hora_codigo if vinculado is not None else None,`
- Mutado:   `hora=p.hora_codigo if vinculado else None,`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `vinculado` es el `recurso_ide` del vinculado (`res.ide` de Sigrid, > 0) o `None` para el titular: nunca `0`.
> Decisión: **mutante equivalente**. `is not None` y la veracidad solo difieren en `0`, que no existe.

### 27. `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:1518` [booleano]

- Original: `[], [ls.ide for *_, ls in enviadas], con_tex=True)`
- Mutado:   `[], [ls.ide for *_, ls in enviadas], con_tex=False)`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: Hueco del doble, no del código: `ClienteFalso.lineas_registradas` daba `tex` y `obride` también sin `con_tex`, y la comprobación posterior al `UPDATE` pasaba igual. El SQL real sin `con_tex` no lee el `tex` (`sigrid_write_client.py`): sin él, la comprobación fallaría siempre y `tex_actualizadas` saldría vacío.
> Decisión: **test corregido** (el doble de `tests/conftest.py` imita el SQL: sin `con_tex`, `tex` y `obride` a `None`; commit `2fe6031`). Reproducido a mano: `test_f069_tex_registrada.py` cae (`assert [] == [5302, 5303]`, `assert [] == [{'registro_i... caja nueva'}]`). Suite del transfer: 1956 passed con el doble nuevo.

### 28. `services/dedicacion-transfer/application/services/lecturas_lote.py:515` [booleano]

- Original: `con_tex: bool = False) -> None:`
- Mutado:   `con_tex: bool = True) -> None:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: El único llamador de `_cargar_registradas` (l. 218) pasa siempre `con_tex`: el valor por defecto no se usa.
> Decisión: **mutante equivalente**. Defecto muerto.

### 29. `services/dedicacion-transfer/application/services/reglas_vinculados.py:500` [veracidad]

- Original: `if p.hora is None:`
- Mutado:   `if not p.hora:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `p.hora` es una `HoraRecurso` (dataclass sin `__bool__` ni `__len__`: siempre verdadera) o `None`.
> Decisión: **mutante equivalente**. Mismo resultado para todo valor posible.

## No muertos: código de salida

| Fichero:línea | Operador | Veredicto | Código |
|---|---|---|---|
| `services/dedicacion-api/application/registro_sigrid.py:169` | booleano | superviviente | 0 |
| `services/dedicacion-api/application/traer_sigrid.py:154` | logico | superviviente | 0 |
| `services/dedicacion-api/application/traer_sigrid.py:342` | veracidad | superviviente | 0 |
| `services/dedicacion-api/application/use_cases.py:1070` | veracidad | superviviente | 0 |
| `services/dedicacion-api/application/use_cases.py:1256` | veracidad | superviviente | 0 |
| `services/dedicacion-api/application/use_cases.py:1304` | entero | superviviente | 0 |
| `services/dedicacion-api/application/use_cases.py:1312` | booleano | superviviente | 0 |
| `services/dedicacion-api/application/use_cases.py:1329` | booleano | superviviente | 0 |
| `services/dedicacion-api/application/use_cases.py:1335` | booleano | superviviente | 0 |
| `services/dedicacion-api/domain/importes.py:36` | booleano | superviviente | 0 |
| `services/dedicacion-api/domain/importes.py:107` | logico | superviviente | 0 |
| `services/dedicacion-api/domain/importes.py:133` | veracidad | superviviente | 0 |
| `services/dedicacion-api/domain/models.py:128` | booleano | superviviente | 0 |
| `services/dedicacion-api/infrastructure/db/repositories.py:574` | comparacion | superviviente | 0 |
| `services/dedicacion-api/infrastructure/db/repositories.py:575` | comparacion | superviviente | 0 |
| `services/dedicacion-api/infrastructure/db/repositories.py:576` | comparacion | superviviente | 0 |
| `services/dedicacion-api/infrastructure/db/repositories.py:819` | veracidad | superviviente | 0 |
| `services/dedicacion-api/infrastructure/db/repositories.py:834` | comparacion | superviviente | 0 |
| `services/dedicacion-api/infrastructure/db/repositories.py:850` | comparacion | superviviente | 0 |
| `services/dedicacion-api/interface_adapters/api/schemas.py:151` | veracidad | superviviente | 0 |
| `services/dedicacion-api/interface_adapters/api/schemas.py:153` | veracidad | superviviente | 0 |
| `services/dedicacion-api/interface_adapters/api/schemas.py:156` | veracidad | superviviente | 0 |
| `services/dedicacion-api/interface_adapters/api/schemas.py:500` | veracidad | superviviente | 0 |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:577` | entero | superviviente | 0 |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:1498` | entero | superviviente | 0 |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:1511` | veracidad | superviviente | 0 |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:1518` | booleano | superviviente | 0 |
| `services/dedicacion-transfer/application/services/lecturas_lote.py:515` | booleano | superviviente | 0 |
| `services/dedicacion-transfer/application/services/reglas_vinculados.py:500` | veracidad | superviviente | 0 |

## Ficheros sin mutantes

Cada uno tiene líneas en alcance y el generador no ha sacado de ellas ni un mutante: la campaña no las ha juzgado. Declara por qué no hay nada que mutar (solo declaraciones, cadenas, imports) o qué test de la fase RED cubre el cambio. El reviewer hace la prueba de control (`generar_mutantes` sin exclusión de alcance) y ninguna declaración puede quedarse en `PENDIENTE` al cerrar la feature.

### `services/dedicacion-api/domain/errors.py` — 8 líneas en alcance, 0 mutantes

#### Declaración

> Solo la declaración de la clase `ImporteInvalido` (docstring). Su uso lo cubren los tests de R5/R6 de `test_f069_importes_dominio.py` y `test_f069_importes_api.py` (422 con el motivo).

### `services/dedicacion-api/domain/ports.py` — 45 líneas en alcance, 0 mutantes

#### Declaración

> Solo firmas de `Protocol` (`ImporteRepository`, `guardar_subfila_importe`, `poner_comentario`, `registradas`): no hay lógica que mutar. Las implementaciones están en la campaña (`repositories.py`).

### `services/dedicacion-api/interface_adapters/api/deps.py` — 12 líneas en alcance, 0 mutantes

#### Declaración

> Cableado por argumentos con nombre, sin operadores. Mutado a mano (`{}` en lugar de los tipos, l. 161, 172 y 173): la l. 161 la cazaba `test_f069_r15_el_contenedor_pasa_tipos_y_precio`; la 172 y la 173 sobrevivían, y ese test ahora comprueba también `contenedor.importes` y `contenedor.traer_sigrid._importes` (commit `2fe6031`): las tres caen.

### `services/dedicacion-transfer/prueba_escritura_porcentajes.py` — 6 líneas en alcance, 0 mutantes

#### Declaración

> Una cadena SQL y sus parámetros (la marca como prefijo, `LIKE`). La cubre `test_f069_pipeline_importe.py` (l. 299-301: `CAST(tex AS NVARCHAR(400)) LIKE ?` y `PRUEBA-PORC%`).

