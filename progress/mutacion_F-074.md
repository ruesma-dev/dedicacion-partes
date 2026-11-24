<!-- progress/mutacion_F-074.md -->
# F-074 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-074 --workers 4` el 2026-11-24 12:16.

## Alcance

Origen del diff: **rama** (`c44bf6056e13132b78dd6807d29cfbac12dd2a89` .. `feature/F-074-partida-sin-automatica`).

| Fichero | Líneas en alcance | Mutantes generados |
|---|---|---|
| `services/dedicacion-api/application/estado_partida.py` | 104 | 32 |
| `services/dedicacion-api/application/filtros_maestros.py` | 23 | 6 |
| `services/dedicacion-api/application/propuestas_mes.py` | 109 | 30 |
| `services/dedicacion-api/application/registro_sigrid.py` | 60 | 17 |
| `services/dedicacion-api/application/sync_pipeline.py` | 6 | 0 — sin mutantes |
| `services/dedicacion-api/application/use_cases.py` | 15 | 8 |
| `services/dedicacion-api/domain/models.py` | 18 | 0 — sin mutantes |
| `services/dedicacion-api/infrastructure/db/orm_models.py` | 8 | 0 — sin mutantes |
| `services/dedicacion-api/infrastructure/db/repositories.py` | 25 | 1 |
| `services/dedicacion-api/infrastructure/transfer/transfer_client.py` | 9 | 1 |
| `services/dedicacion-api/interface_adapters/api/routes.py` | 48 | 5 |
| `services/dedicacion-api/interface_adapters/api/schemas.py` | 60 | 12 |
| `services/dedicacion-transfer/application/pipelines/registro_lote.py` | 4 | 1 |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py` | 179 | 43 |
| `services/dedicacion-transfer/application/pipelines/registro_vinculados.py` | 73 | 17 |
| `services/dedicacion-transfer/application/services/lecturas_lote.py` | 24 | 5 |
| `services/dedicacion-transfer/application/services/partida_definida.py` | 144 | 19 |
| `services/dedicacion-transfer/application/services/universo_postventa.py` | 32 | 5 |
| `services/dedicacion-transfer/domain/models/registro_models.py` | 7 | 0 — sin mutantes |
| **Total** | **948** | **202** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 202 |
| Mutantes evaluados | 100 |
| Muertos | 84 |
| Supervivientes | 16 (todos medidos: sin mapa no se poda) |
| Timeouts | 0 |
| Indeterminados | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 1321.7 s |
| SHA de HEAD medido | `4aa8d7b2d5e107caa19f18e84b33ce504249bb15` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-074_zj3kgn7w/wk_0/services/dedicacion-api` | 68.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-074_zj3kgn7w/wk_0/services/dedicacion-transfer` | 38.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-074_zj3kgn7w/wk_1/services/dedicacion-api` | 68.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-074_zj3kgn7w/wk_1/services/dedicacion-transfer` | 38.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-074_zj3kgn7w/wk_2/services/dedicacion-api` | 68.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-074_zj3kgn7w/wk_2/services/dedicacion-transfer` | 38.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-074_zj3kgn7w/wk_3/services/dedicacion-api` | 68.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-074_zj3kgn7w/wk_3/services/dedicacion-transfer` | 38.1 |
| Media por mutante evaluado (s) | 13.2 |
| Timeout efectivo por mutante (s) | 138 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Un mutante por línea | sí — 202 generados → 133 candidatos, uno por línea |
| Muestreo | sí — 100 de 133 candidatos, semilla `20261030`, nivel `critico`; tope: 60 % de 133 candidatos, acotado a [100, 300] |
| Selección de tests | desactivada (por defecto): todo con la suite entera, como la 1.9.0 |
| SHA del mapa | n/d |
| Medición del mapa (s) | n/d |
| Tests en la suite | n/d |
| Tamaño medio del subconjunto | n/d |
| Revalidados con la suite entera | n/d |
| Subconjuntos descartados | n/d |
| Podados (sin ejecutar) | n/d |
| Tiempo ahorrado por la poda (s) — derivado: podados × línea base | n/d |
| Media por mutante juzgado con la suite entera (s) | 43.3 (100 mutantes) |

## Cómo se juzgó

- Cada mutante con la **suite entera**, como en la 1.9.0: la selección de tests está apagada por defecto (en la suite del propio arnés costó más de lo que ahorró). Se enciende con `--con-seleccion` en la orden o con `mutacion.seleccion_de_tests: true` en `harness/rigor.local.json`; la orden manda sobre la clave.


## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/dedicacion-api/application/estado_partida.py:33` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis (implementer, 2026-11-24)

> Reproducido EN SERIE el 2026-11-24 (mutante aplicado en el árbol, suite entera del servicio con `pytest -q -x`): código 0, la suite pasa entera.
>
> Por qué ningún test lo caza: ningún test intentaba modificar una `Marcas`; su inmutabilidad (la foto de la cola que comparten cuadrante y rutas) no se comprobaba.
>
> Decisión: **test nuevo** `tests/test_f074_mutacion_api.py::test_f074_mut_las_marcas_son_inmutables`. Con el mutante aplicado, el test falla (código 1, comprobado a mano); sin él, pasa.

### 2. `services/dedicacion-api/application/estado_partida.py:75` [veracidad]

- Original: `tiene = ln.obra_pv_ide is not None`
- Mutado:   `tiene = ln.obra_pv_ide`
- Juicio: MEDIDO

#### Análisis (implementer, 2026-11-24)

> Reproducido EN SERIE el 2026-11-24 (mutante aplicado en el árbol, suite entera del servicio con `pytest -q -x`): código 0, la suite pasa entera.
>
> Por qué ningún test lo caza: `tiene` solo cambia si `obra_pv_ide` vale 0. Ese valor sale de `obra.postventa_partida_ide`, que el sync guarda desde las partidas del universo de postventa del transfer: `ide` de hojas reales de `obrparpar` (identidad de Sigrid, siempre > 0), o None si la obra no casa. Un 0 no puede llegar.
>
> Decisión: **mutante equivalente**, justificado por escrito. PENDIENTE de la aceptación del humano (nivel `critico`): no se da por aceptado aquí.

### 3. `services/dedicacion-api/application/use_cases.py:405` [veracidad]

- Original: `and self._al_borrar_subfilas is not None`
- Mutado:   `and self._al_borrar_subfilas`
- Juicio: MEDIDO

#### Análisis (implementer, 2026-11-24)

> Reproducido EN SERIE el 2026-11-24 (mutante aplicado en el árbol, suite entera del servicio con `pytest -q -x`): código 0, la suite pasa entera.
>
> Por qué ningún test lo caza: `_al_borrar_subfilas` es None o el método ligado `PropuestasDelMes.olvidar_subfilas` (la ruta lo pasa con `getattr`); una función o un método ligado siempre es verdadero. No hay entrada que los distinga.
>
> Decisión: **mutante equivalente**, justificado por escrito. PENDIENTE de la aceptación del humano (nivel `critico`): no se da por aceptado aquí.

### 4. `services/dedicacion-api/interface_adapters/api/schemas.py:154` [veracidad]

- Original: `default=None, exclude_if=lambda v: v is None)`
- Mutado:   `default=None, exclude_if=lambda v: not v)`
- Juicio: MEDIDO

#### Análisis (implementer, 2026-11-24)

> Reproducido EN SERIE el 2026-11-24 (mutante aplicado en el árbol, suite entera del servicio con `pytest -q -x`): código 0, la suite pasa entera.
>
> Por qué ningún test lo caza: `estado_de_subfila` solo pone `propuesta_no_encontrada` a True, así que ningún test serializaba un False: el contrato del esquema (excluir solo None, como `copiado` de F-069) no estaba fijado.
>
> Decisión: **test nuevo** `tests/test_f074_mutacion_api.py::test_f074_mut_subfila_solo_excluye_none`. Con el mutante aplicado, el test falla (código 1, comprobado a mano); sin él, pasa.

### 5. `services/dedicacion-api/interface_adapters/api/schemas.py:486` [veracidad]

- Original: `marcas = marcas if marcas is not None else Marcas(`
- Mutado:   `marcas = marcas if marcas else Marcas(`
- Juicio: MEDIDO

#### Análisis (implementer, 2026-11-24)

> Reproducido EN SERIE el 2026-11-24 (mutante aplicado en el árbol, suite entera del servicio con `pytest -q -x`): código 0, la suite pasa entera.
>
> Por qué ningún test lo caza: el valor es `None` o una instancia de `Marcas` (`application/estado_partida.py`), una dataclass sin `__bool__` ni `__len__`: toda instancia es verdadera, así que `x is None` y `not x` (o `is not None` y la veracidad) dan siempre lo mismo. No hay entrada que los distinga.
>
> Decisión: **mutante equivalente**, justificado por escrito. PENDIENTE de la aceptación del humano (nivel `critico`): no se da por aceptado aquí.

### 6. `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:217` [veracidad]

- Original: `if obra_pv is None:`
- Mutado:   `if not obra_pv:`
- Juicio: MEDIDO

#### Análisis (implementer, 2026-11-24)

> Reproducido EN SERIE el 2026-11-24 (mutante aplicado en el árbol, suite entera del servicio con `pytest -q -x`): código 0, la suite pasa entera.
>
> Por qué ningún test lo caza: el valor es `None` o una instancia de `ObraEntrada` (`domain/models/registro_models.py`; la devuelve `obra_de_postventa`), una dataclass sin `__bool__` ni `__len__`: toda instancia es verdadera, así que `x is None` y `not x` (o `is not None` y la veracidad) dan siempre lo mismo. No hay entrada que los distinga.
>
> Decisión: **mutante equivalente**, justificado por escrito. PENDIENTE de la aceptación del humano (nivel `critico`): no se da por aceptado aquí.

### 7. `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:220` [entero]

- Original: `return {"ide": 0, "cod": None}, None`
- Mutado:   `return {"ide": 1, "cod": None}, None`
- Juicio: MEDIDO

#### Análisis (implementer, 2026-11-24)

> Reproducido EN SERIE el 2026-11-24 (mutante aplicado en el árbol, suite entera del servicio con `pytest -q -x`): código 0, la suite pasa entera.
>
> Por qué ningún test lo caza: el test de F-039 R6 (postventa con `var_paride`) comprueba la acción y el motivo de la omitida, no su `paride`: el 0 de «sin partida» no se miraba.
>
> Decisión: **test nuevo** `tests/test_f074_mutacion.py::test_f074_mut_postventa_con_var_se_omite_sin_partida`. Con el mutante aplicado, el test falla (código 1, comprobado a mano); sin él, pasa.

### 8. `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:637` [veracidad]

- Original: `if obra_pv is not None:`
- Mutado:   `if obra_pv:`
- Juicio: MEDIDO

#### Análisis (implementer, 2026-11-24)

> Reproducido EN SERIE el 2026-11-24 (mutante aplicado en el árbol, suite entera del servicio con `pytest -q -x`): código 0, la suite pasa entera.
>
> Por qué ningún test lo caza: el valor es `None` o una instancia de `ObraEntrada`, una dataclass sin `__bool__` ni `__len__`: toda instancia es verdadera, así que `x is None` y `not x` (o `is not None` y la veracidad) dan siempre lo mismo. No hay entrada que los distinga.
>
> Decisión: **mutante equivalente**, justificado por escrito. PENDIENTE de la aceptación del humano (nivel `critico`): no se da por aceptado aquí.

### 9. `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:686` [entero]

- Original: `v = validas.get(int(paride or 0))`
- Mutado:   `v = validas.get(int(paride or 1))`
- Juicio: MEDIDO

#### Análisis (implementer, 2026-11-24)

> Reproducido EN SERIE el 2026-11-24 (mutante aplicado en el árbol, suite entera del servicio con `pytest -q -x`): código 0, la suite pasa entera.
>
> Por qué ningún test lo caza: `vale_pv` solo se llama en la rama `a.destino == "postventa"` de una acción `escribir` (l. 727), y justo antes (l. 724) se hace `int(a.paride)`. Ahí `a.paride` es siempre la definida de la línea (la elegida o la propuesta, > 0): `_definida_pv` no deja pasar a `escribir` una línea sin ella, y la línea VAR (la única con `ide` 0) sale antes por su rama (l. 698-706). `paride or 0` y `paride or 1` nunca se evalúan con un `paride` falso.
>
> Decisión: **mutante equivalente**, justificado por escrito. PENDIENTE de la aceptación del humano (nivel `critico`): no se da por aceptado aquí.

### 10. `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:687` [veracidad]

- Original: `return v is not None and v.vale_en(obra_pv.ide)`
- Mutado:   `return v and v.vale_en(obra_pv.ide)`
- Juicio: MEDIDO

#### Análisis (implementer, 2026-11-24)

> Reproducido EN SERIE el 2026-11-24 (mutante aplicado en el árbol, suite entera del servicio con `pytest -q -x`): código 0, la suite pasa entera.
>
> Por qué ningún test lo caza: `v` es None o una `PartidaValida` (dataclass congelada sin `__bool__` ni `__len__`, siempre verdadera). Con None, el mutante devuelve None en vez de False, pero el único uso es `if not vale_pv(...)` (l. 727), un contexto booleano en el que None y False son lo mismo.
>
> Decisión: **mutante equivalente**, justificado por escrito. PENDIENTE de la aceptación del humano (nivel `critico`): no se da por aceptado aquí.

### 11. `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:781` [veracidad]

- Original: `obra_pv_ide=int(obra_pv.ide) if obra_pv is not None else None,`
- Mutado:   `obra_pv_ide=int(obra_pv.ide) if obra_pv else None,`
- Juicio: MEDIDO

#### Análisis (implementer, 2026-11-24)

> Reproducido EN SERIE el 2026-11-24 (mutante aplicado en el árbol, suite entera del servicio con `pytest -q -x`): código 0, la suite pasa entera.
>
> Por qué ningún test lo caza: el valor es `None` o una instancia de `ObraEntrada`, una dataclass sin `__bool__` ni `__len__`: toda instancia es verdadera, así que `x is None` y `not x` (o `is not None` y la veracidad) dan siempre lo mismo. No hay entrada que los distinga.
>
> Decisión: **mutante equivalente**, justificado por escrito. PENDIENTE de la aceptación del humano (nivel `critico`): no se da por aceptado aquí.

### 12. `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:1137` [veracidad]

- Original: `if p is None:`
- Mutado:   `if not p:`
- Juicio: MEDIDO

#### Análisis (implementer, 2026-11-24)

> Reproducido EN SERIE el 2026-11-24 (mutante aplicado en el árbol, suite entera del servicio con `pytest -q -x`): código 0, la suite pasa entera.
>
> Por qué ningún test lo caza: el valor es `None` o una instancia de `Propuesta` (`propuesta_partida.py`, congelada; la devuelve `proponer_partida`), una dataclass sin `__bool__` ni `__len__`: toda instancia es verdadera, así que `x is None` y `not x` (o `is not None` y la veracidad) dan siempre lo mismo. No hay entrada que los distinga.
>
> Decisión: **mutante equivalente**, justificado por escrito. PENDIENTE de la aceptación del humano (nivel `critico`): no se da por aceptado aquí.

### 13. `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:289` [booleano]

- Original: `guardada, guardada_valida = None, True`
- Mutado:   `guardada, guardada_valida = None, False`
- Juicio: MEDIDO

#### Análisis (implementer, 2026-11-24)

> Reproducido EN SERIE el 2026-11-24 (mutante aplicado en el árbol, suite entera del servicio con `pytest -q -x`): código 0, la suite pasa entera.
>
> Por qué ningún test lo caza: el valor inicial de `guardada_valida` solo se lee si `guardada` no es None (`partida_definida_del_vinculado`, l. 123-124 de `partida_definida.py`: `if guardada is not None and …: if not guardada_valida`). Cuando `guardada` existe, `guardada_valida` se reasigna con la validación (l. 291). El True inicial nunca se lee.
>
> Decisión: **mutante equivalente**, justificado por escrito. PENDIENTE de la aceptación del humano (nivel `critico`): no se da por aceptado aquí.

### 14. `services/dedicacion-transfer/application/services/partida_definida.py:81` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis (implementer, 2026-11-24)

> Reproducido EN SERIE el 2026-11-24 (mutante aplicado en el árbol, suite entera del servicio con `pytest -q -x`): código 0, la suite pasa entera.
>
> Por qué ningún test lo caza: ningún test intentaba retocar una `DefinidaVinculado` ya decidida.
>
> Decisión: **test nuevo** `tests/test_f074_mutacion.py::test_f074_mut_definida_del_vinculado_es_inmutable`. Con el mutante aplicado, el test falla (código 1, comprobado a mano); sin él, pasa.

### 15. `services/dedicacion-transfer/application/services/partida_definida.py:108` [veracidad]

- Original: `if elegida is not None:`
- Mutado:   `if elegida:`
- Juicio: MEDIDO

#### Análisis (implementer, 2026-11-24)

> Reproducido EN SERIE el 2026-11-24 (mutante aplicado en el árbol, suite entera del servicio con `pytest -q -x`): código 0, la suite pasa entera.
>
> Por qué ningún test lo caza: el valor es `None` o una instancia de `PartidaElegida` (`reglas_vinculados.py`, congelada), una dataclass sin `__bool__` ni `__len__`: toda instancia es verdadera, así que `x is None` y `not x` (o `is not None` y la veracidad) dan siempre lo mismo. No hay entrada que los distinga.
>
> Decisión: **mutante equivalente**, justificado por escrito. PENDIENTE de la aceptación del humano (nivel `critico`): no se da por aceptado aquí.

### 16. `services/dedicacion-transfer/application/services/universo_postventa.py:59` [veracidad]

- Original: `if obra_pv is None:`
- Mutado:   `if not obra_pv:`
- Juicio: MEDIDO

#### Análisis (implementer, 2026-11-24)

> Reproducido EN SERIE el 2026-11-24 (mutante aplicado en el árbol, suite entera del servicio con `pytest -q -x`): código 0, la suite pasa entera.
>
> Por qué ningún test lo caza: el valor es `None` o una instancia de `ObraEntrada` (la devuelve `cliente.obra_por_codigo`), una dataclass sin `__bool__` ni `__len__`: toda instancia es verdadera, así que `x is None` y `not x` (o `is not None` y la veracidad) dan siempre lo mismo. No hay entrada que los distinga.
>
> Decisión: **mutante equivalente**, justificado por escrito. PENDIENTE de la aceptación del humano (nivel `critico`): no se da por aceptado aquí.

## No muertos: código de salida

| Fichero:línea | Operador | Veredicto | Código |
|---|---|---|---|
| `services/dedicacion-api/application/estado_partida.py:33` | booleano | superviviente | 0 |
| `services/dedicacion-api/application/estado_partida.py:75` | veracidad | superviviente | 0 |
| `services/dedicacion-api/application/use_cases.py:405` | veracidad | superviviente | 0 |
| `services/dedicacion-api/interface_adapters/api/schemas.py:154` | veracidad | superviviente | 0 |
| `services/dedicacion-api/interface_adapters/api/schemas.py:486` | veracidad | superviviente | 0 |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:217` | veracidad | superviviente | 0 |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:220` | entero | superviviente | 0 |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:637` | veracidad | superviviente | 0 |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:686` | entero | superviviente | 0 |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:687` | veracidad | superviviente | 0 |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:781` | veracidad | superviviente | 0 |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py:1137` | veracidad | superviviente | 0 |
| `services/dedicacion-transfer/application/pipelines/registro_vinculados.py:289` | booleano | superviviente | 0 |
| `services/dedicacion-transfer/application/services/partida_definida.py:81` | booleano | superviviente | 0 |
| `services/dedicacion-transfer/application/services/partida_definida.py:108` | veracidad | superviviente | 0 |
| `services/dedicacion-transfer/application/services/universo_postventa.py:59` | veracidad | superviviente | 0 |

## Ficheros sin mutantes

Cada uno tiene líneas en alcance y el generador no ha sacado de ellas ni un mutante: la campaña no las ha juzgado. Declara por qué no hay nada que mutar (solo declaraciones, cadenas, imports) o qué test de la fase RED cubre el cambio. El reviewer hace la prueba de control (`generar_mutantes` sin exclusión de alcance) y ninguna declaración puede quedarse en `PENDIENTE` al cerrar la feature.

### `services/dedicacion-api/application/sync_pipeline.py` — 6 líneas en alcance, 0 mutantes

#### Declaración (implementer, 2026-11-24)

> Solo docstring, comentarios y dos argumentos con nombre (`partidas=`, `motivos=`) pasados a `depurar_obras`: no hay operador que mutar. Lo cubren `test_f074_postventa.py::test_f074_r11_el_sync_las_guarda_con_la_misma_llamada` y `test_f074_r11_depurar_obras_pone_la_partida_o_el_motivo`, ambos de la fase RED de R11 (en rojo contra `9fb1092`).

### `services/dedicacion-api/domain/models.py` — 18 líneas en alcance, 0 mutantes

#### Declaración (implementer, 2026-11-24)

> Solo declaraciones de campos con default None o `field(default_factory=dict)` y comentarios. Las cubren `test_f074_postventa.py` (RED: `ResultadoUniverso.__init__() got an unexpected keyword argument 'partidas'`), `test_f074_estados.py` y `test_f055_propuesta_guardada.py::test_f055_r13_linea_sin_propuesta_por_defecto_al_final` (orden de los campos de `Linea`).

### `services/dedicacion-api/infrastructure/db/orm_models.py` — 8 líneas en alcance, 0 mutantes

#### Declaración (implementer, 2026-11-24)

> Solo cuatro columnas nulables (`mapped_column(BigInteger | Text)`) y un comentario. Las cubre `test_f074_postventa.py::test_f074_r11_el_repositorio_guarda_actualiza_y_anula`, de la fase RED de R11 (en rojo contra `9fb1092`).

### `services/dedicacion-transfer/domain/models/registro_models.py` — 7 líneas en alcance, 0 mutantes

#### Declaración (implementer, 2026-11-24)

> Solo dos campos `partida_no_valida: Optional[str] = None` y comentarios. Los cubre `test_f074_preflight_definida.py` (`test_f074_r4_*`; RED: `AttributeError: 'AccionLinea' object has no attribute 'partida_no_valida'`).
