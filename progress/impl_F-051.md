# F-051 · Informe del implementer (2026-10-20) · BLOQUEADA en T12

Spec: `specs/F-051-pisar-lineas-cero/`. Copia `porcentajes-f051`, rama
`feature/F-051-pisar-lineas-cero`. Rigor `critico`. **Estado: `blocked`**
(motivo y opciones en `progress/current.md`, «F-051 · BLOQUEO en T12»).
El primer bloqueo (T3, test de F-013) lo resolvió el humano con la opción A.

## 1. Qué está hecho

| Tarea | Estado | Commit |
|---|---|---|
| T1-T2 reglas puras (`es_linea_al_cero`, `pisables_al_cero`, `emparejar_ceros`…) | hecha | `5f0e759` |
| T3 modelos (`Conflicto.edita_ide`/`a_cero_ides`, `ResultadoRegistro.editadas`…) | hecha | `b5ddc3a` |
| T4 `lineas_registradas` (cliente y lote) y dobles con edición | hecha | `fa2bc45` |
| T5 paso 6 por `hmores_ide` | hecha | `4a088fb` |
| T6 paso 7: `linea_cero`, aviso, pisado con `edita_ide` | hecha | `0b3156d` |
| T7 `lineas_para_editar`, `stmt_editar_linea`, `stmt_poner_a_cero` | hecha | `2cd6b09` |
| T8 paso 10 sin `DELETE` (+ arreglo de T6, §2) | hecha | `d3d3b97` |
| T9 respuesta, script y tests de la lista cerrada | hecha | `34a17ed` |
| T10 lote = suelto, mismas lecturas | hecha | `8fcb74d` |
| T11 api: `hmores_ide` de ida y `ya_registradas_ide` de vuelta | hecha | `6788bfa` |
| T12 front | **parada**: dos tests de F-049 fuera de la lista | — (parche guardado) |
| T13-T14, T17 | sin empezar | — |
| T15 (MANUAL, humano) / T16 (`azure-apps`, líder) | no son del implementer | — |

Ficheros tocados (commiteados), por servicio:

- **transfer**: `application/services/reglas_porcentajes.py` (T1-T2);
  `domain/models/registro_models.py` (T3); `interface_adapters/api/app.py`
  (`LineaIn.hmores_ide`, claves nuevas de `ejecutar`);
  `infrastructure/sigrid/sigrid_write_client.py` (`lineas_registradas`,
  `lineas_para_editar`, `_guarda`, `stmt_editar_linea`, `stmt_poner_a_cero`,
  `_ENLACES`; `stmt_borrar_linea` solo para `limpiar`);
  `application/services/lecturas_lote.py` (`lineas_registradas` en la ronda
  A); `application/pipelines/registro_pipeline.py` (pasos 6, 7, 9 bis, 10 y
  relectura); `prueba_escritura_porcentajes.py` (estado, preflight,
  ejecutar).
- **api**: `application/registro_sigrid.py` (`_payloads`, `_trazar`).
- **tests nuevos**: transfer `test_f051_reglas_cero.py` (55),
  `test_f051_sql_cero.py` (23), `test_f051_pipeline_cero.py` (57); api
  `test_f051_hmores_ide.py` (5).
- **Dobles** (sin cambiar aserciones): `conftest.py` gana el mixin
  `EdicionesFalsas` (lectura previa, sentencias de edición que se APLICAN a
  las líneas del doble con la misma guarda que el SQL, relectura por `ide`,
  `guarda_falla`, `enlazadas`, `ediciones()`, `a_ceros()`);
  `test_pipeline_offline.py` lo usa en su `ClienteFalso`.
- **Lista cerrada** tocada: `test_f002_pipeline.py` (178-231 y 408-421),
  `test_f013_sin_partida.py` (576-590 y `…r4_no_hace_falta_ningun_campo_nuevo`),
  `test_f037_pipeline.py` (535-550), `test_pipeline_offline.py` (238-262),
  `test_f024_obra_destino_otra_empresa.py` (claves nuevas). Pasan de esperar
  el `DELETE` a esperar la edición del mismo `ide` con `borradas == 0`; los
  nombres de los tests se conservan y su docstring lo dice.

## 2. Decisiones de diseño

- **`repartir_choques`** y **`es_nuestra_de_otra`**: puras nuevas (reparto
  R4-R5 por `registro_id` ↔ choques por `ide`; condición de R15).
- **`lineas_registradas(claves, ides)` sin `ides` delega en
  `lineas_por_synckey`** (la consulta y el nombre medido de hoy): los tests
  de F-055 que nombran `lineas_por_synckey` no cambian. En el doble, igual.
- **Paso 9 bis antes del alta de partes**: la lectura previa (R12) va antes
  de `_crear_parte`, y solo las acciones que INSERTAN dan de alta parte o
  leen `max_pos`: la que edita no necesita parte nuevo y la que cae por
  «línea cambiada» no deja uno vacío.
- **Comprobación de R12** con las mismas reglas que el preflight:
  pisable = `pisables_al_cero([fila], acción)`; choque = `criterio_choque`;
  las dos, además, `M*`, sin enlaces y `parte_est == est_parte_activo`. Si
  falla un choque, cae el pisado entero (todos sus registros escribibles).
- **Una misma línea en dos pisados**: se reparte una vez (`usadas`), como
  hacía el `DELETE` único de hoy (R13 de F-002).
- **R13**: la relectura de hoy pasa a `lineas_registradas(claves de las
  escritas, ides editados y puestos a 0)`: una lectura, la misma de siempre.
  Una editada sin nuestra `can` o sin la `synckey` de R9 sale de `escritas` y
  `editadas` y va a `omitidas`; una puesta a 0 que no quedó a 0, al log.
- **`escritas[]`** lleva `editada` (true/false); la editada, el `hmoide` y
  el parte de la fila editada y su `hmores_ide`.
- **Desviación justificada (T9)**: la fase `estado` del script lee además
  `pos`, `paride` y `tex` (solo lectura), para que T15 compruebe que una
  edición no mueve `pos` ni el parte y deja la marca en `tex`.
- **api (T11)**: `getattr(a, "sigrid_hmores_ide", None)` en `_payloads`: los
  dobles de los tests de la api anteriores a F-051 no traen la columna y
  tocarlos no está en la lista cerrada; el ORM siempre la tiene.
- **Defecto propio cazado y corregido en T8**: en T6 llamé `en_cerrado` a las
  líneas de partes cerrados y pisé la variable del mismo nombre que acumula
  los registros omitidos por un cerrado (filtra el «sin partida»). Renombrada
  a `lineas_cerradas`, con test (`…r7_el_cerrado_de_un_periodo_no_se_olvida…`)
  que fallaba antes del arreglo.

## 3. Fase RED (trazas reales)

Comandos desde `services/dedicacion-<servicio>`, con
`.venv/Scripts/python -m pytest <fichero> -q -p no:cacheprovider [-k …]`,
tests escritos y código aún sin escribir. T1-T2 (55 tests):

```
E   ImportError: cannot import name 'emparejar_ceros' from 'application.services.reglas_porcentajes'
(con stubs triviales) 29 failed, 26 passed in 1.93s
```

T4, `tests/test_f051_sql_cero.py`:
```
E   AttributeError: 'SigridWriteClient' object has no attribute 'lineas_registradas'
10 failed, 1 passed in 7.62s
```
T5, `tests/test_f051_pipeline_cero.py`:
```
E   AssertionError: assert ('escribir', None) == ('ya_registrado', 410931)
E   AttributeError: 'Anota' object has no attribute 'pedidas'
E   assert [2] == [1, 2]
3 failed, 5 passed in 4.12s
```
T6, `-k "r3 or r4 or r5 or r7 or r1_"`:
```
E   escribir and [Conflicto(cl...cero_ides=[])] == []      (la línea a 0 era choque)
E   TypeError: 'NoneType' object is not subscriptable       (sin linea_cero)
E   assert [410600, 5002] == [5002]                         (la pisable en el contexto)
E   AssertionError: assert ('pisado', None, []) == ('pisado', 5009, [])
11 failed, 1 passed, 8 deselected in 4.10s
```
T7, `-k "r5 or r6 or r8 or r10 or r11 or r12"`:
```
E   AttributeError: 'SigridWriteClient' object has no attribute 'stmt_editar_linea'. Did you mean: 'stmt_borrar_linea'?
E   AttributeError: 'SigridWriteClient' object has no attribute 'stmt_poner_a_cero'
10 failed, 11 deselected in 4.18s
```
T8, fichero entero (los de T5-T6 ya en verde):
```
E   AssertionError: assert ([{'sql': 'del...': 128, ...}}] == []
E     Left contains 3 more items, first extra item: {'sql': 'delete', 'parameters': [5003]}
E   AssertionError: assert [] == [{'registro_i...a registrar'}]
E   assert [128, 192] == [128]                              (la editada consumía pos)
32 failed, 23 passed in 7.36s
```
Regresión de `en_cerrado` (antes del arreglo):
`E AssertionError: assert ['sin_partida'] == []` · `1 failed, 54 deselected`.
T9, `-k respuesta` y `-k script`:
```
E   KeyError: 'ya_registradas_ide'                                    1 failed
E   AssertionError: assert 'linea_cero=410600' in 'Obra destino: 0404 …'  1 failed
```
T11 (api), `tests/test_f051_hmores_ide.py`:
```
E   KeyError: 'hmores_ide'
E   AssertionError: assert [] == [(2, {'sigrid_hmores_ide': 9002})]
2 failed, 3 passed in 8.97s
```
T12 (front, en el parche): `5 failed in 4.60s` (`… se borran línea 8001 … y
se escribe 60%` frente a `… se edita la línea 8001 … y queda 60%`).

T10 (lote = suelto) no tiene fase RED propia: es la no-regresión de R19
sobre lo ya hecho en T4-T6 (verde al escribirse).

## 4. Por qué se para (T12)

T12 cambia el texto del pisado en `rotuloConflicto` (`app.js`) al de design
§1/§3: «se edita la línea X (…) y queda N%; quedan a 0: …». Con el parche
aplicado, la suite del front da **2 failed** fuera de la lista cerrada:

```
FAILED tests/test_f049_avisos_registro.py::test_f049_r2_el_porcentaje_sale_de_nuevas_no_cero
E   AssertionError: assert False
E    +  where False = '…: se edita la línea 8001 (MADM 40%, fec 20260930) y queda 60%'.endswith('se escribe 60%')
FAILED tests/test_f049_avisos_registro.py::test_f049_r2_decimales_y_sin_nuevas
E    +  where False = '…: se edita la línea 8001 (MADM 40%, fec 20260930) y queda 43,3%'.endswith('se escribe 43,3%')
2 failed, 21 passed in 12.18s
```

Esos dos tests comprueban que el % sale de `nuevas` (F-049 R2) mirando que
el detalle del pisado TERMINE en «se escribe N%». La lista cerrada solo
incluye `test_f049_r1_pisado_ensena_lo_que_se_borra_y_el_nuevo`. Orden:
parar, sin tocarlos. **El trabajo de T12 no está en el árbol**: está
guardado como parche (`app.js`, el test de F-049 de la lista y
`test_f051_modal_pisado.py`, 5 tests) en el scratchpad,
`…/scratchpad/f051/t12_front.patch` (`git apply --check` OK), y se reaplica
en cuanto el humano decida. El árbol queda en `6788bfa`, en verde.

## 5. Verificación del estado entregado

- Línea base (HEAD `1ecb9f5`): raíz 418 passed, 1 skipped; api 943; front
  305; transfer 932.
- Tras T11: transfer **1067 passed** (932 + 135), api **948 passed** (943 +
  5), front 305 (sin cambios en el árbol).
- `bash harness/init.sh` en el worktree tras el bloqueo: ver §6.

## 6. `bash harness/init.sh` (worktree, tras el bloqueo)

Sin ningún `[KO]` («ENTORNO LISTO. Puedes trabajar.»): raíz 418 passed, 1
skipped; api 948 passed; front 305 passed; transfer 1067 passed. **PUERTA
COBERTURA: 99,2 % de 255 líneas cambiadas** (253/255, umbral 80 %, nivel
crítico). PUERTA TAMAÑO dentro. Avisos: F-051 `blocked`, `BACKLOG.md`
regenerado, ruff 284 (deuda previa).

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados | transfer 1067 passed; api 948 passed; front 305 passed (en el árbol) |
| Cobertura de líneas cambiadas | 99,2 % (253/255), PUERTA COBERTURA de init.sh |
| Mutación | no lanzada: T14 no alcanzada por el bloqueo; se lanzará en serie, `--workers 1` |
| Tiempo de la suite | en init.sh: transfer 85,22 s; api 171,21 s; front 96,71 s; raíz 144,00 s |

## Pendiente

- Decisión del humano sobre los dos tests de F-049 (opciones en
  `current.md`). Después: reaplicar el parche de T12, T13 (documentación),
  T14 (cobertura y mutación en serie, cero supervivientes), T17.
- T15 (MANUAL, modo pruebas en la 0404) la ejecuta el humano; el comando
  exacto, en `current.md` y en `tasks.md` T15. Nota: `limpiar` (D15) borra
  también las líneas de Administración EDITADAS en la 0404, porque quedan
  con `PRUEBA-PORC` y nuestra `synckey`.
- T16 (líder, al desplegar): `azure-apps/dedicacion.md` (el transfer edita
  líneas de otros sistemas en su sitio; contrato `hmores_ide` de ida y
  `ya_registradas_ide`/`editadas`/`a_cero` de vuelta) y aviso a `partes`.
