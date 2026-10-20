# F-051 · Informe del implementer (2026-10-20) · TERMINADA

Spec: `specs/F-051-pisar-lineas-cero/`. Copia `porcentajes-f051`, rama
`feature/F-051-pisar-lineas-cero`. Rigor `critico`. **Estado: implementer
terminado**, a falta de la review, de T15 (MANUAL, humano) y de T16 (líder).
Bloqueos resueltos por el humano: T3 opción A, T12 opción B (`current.md`).

## 1. Qué cambió

| Tarea | Commit |
|---|---|
| T1-T2 reglas puras (`es_linea_al_cero`, `pisables_al_cero`, `emparejar_ceros`, `synckey_tras_editar`…) | `5f0e759` |
| T3 modelos (`Conflicto.edita_ide`/`a_cero_ides`, `ResultadoRegistro.editadas`…) | `b5ddc3a` |
| T4 `lineas_registradas` (cliente y lote) y dobles con edición | `fa2bc45` |
| T5 paso 6 por `hmores_ide` | `4a088fb` |
| T6 paso 7: `linea_cero`, aviso, pisado con `edita_ide` | `0b3156d` |
| T7 `lineas_para_editar`, `stmt_editar_linea`, `stmt_poner_a_cero` | `2cd6b09` |
| T8 paso 10 sin `DELETE` (+ arreglo de T6, §2) | `d3d3b97` |
| T9 respuesta, script y tests de la lista cerrada | `34a17ed` |
| T10 lote = suelto, mismas lecturas | `8fcb74d` |
| T11 api: `hmores_ide` de ida y `ya_registradas_ide` de vuelta | `6788bfa` |
| T12 front: «se edita la línea X (…)[; quedan a 0: …] y se escribe N%» | `24ba7aa` |
| T13 documentación (`#regla-cero`, INTEGRACION §1, §5, §7) | `e74dbe7` |
| T14 tests contra supervivientes + campaña de mutación | `4dea061`, `f8a79b7` |
| T17 `init.sh` en verde e informe | este commit |

Ficheros de producción, por servicio:

- **transfer**: `application/services/reglas_porcentajes.py`;
  `domain/models/registro_models.py`; `interface_adapters/api/app.py`
  (`LineaIn.hmores_ide`; `ejecutar` publica `editadas`, `a_cero`,
  `ya_registradas_ide`); `infrastructure/sigrid/sigrid_write_client.py`
  (`lineas_registradas`, `lineas_para_editar`, `_guarda`, `_ENLACES`,
  `stmt_editar_linea`, `stmt_poner_a_cero`; `stmt_borrar_linea` queda solo
  para `limpiar`); `application/services/lecturas_lote.py`
  (`lineas_registradas` en la ronda A);
  `application/pipelines/registro_pipeline.py` (pasos 6, 7, 9 bis, 10 y
  relectura R13; helpers `_fila`, `_traza`, `_escrita`,
  `_comprobar_escrito`); `prueba_escritura_porcentajes.py` (estado,
  preflight, ejecutar).
- **api**: `application/registro_sigrid.py` (`_payloads`, `_trazar`).
- **front**: `static/js/app.js` (`rotuloConflicto`, pisado).
- **docs**: `docs/ARCHITECTURE.md` (regla 20 `#regla-cero`; «editar» en el
  transfer, `#regla-conflicto`, `#regla-analitica` y la tabla de
  sigrid-api); `docs/INTEGRACION.md` §1, §5 (contrato de F-051) y §7.

Tests nuevos: transfer `test_f051_reglas_cero.py`, `test_f051_sql_cero.py`,
`test_f051_pipeline_cero.py`; api `test_f051_hmores_ide.py` (6); front
`test_f051_modal_pisado.py` (5). **Dobles** (sin cambiar aserciones):
`conftest.py` gana el mixin `EdicionesFalsas` (lectura previa, ediciones que
se APLICAN a las líneas del doble con la misma guarda que el SQL, relectura
por `ide`, `guarda_falla`, `enlazadas`); `test_pipeline_offline.py` lo usa.

**Lista cerrada tocada** (y nada más): `test_f002_pipeline.py` (178-231 y
408-421), `test_f013_sin_partida.py` (576-590 y `…r4_no_hace_falta_ningun_campo_nuevo`,
opción A), `test_f037_pipeline.py` (535-550), `test_pipeline_offline.py`
(238-262), `test_f024_obra_destino_otra_empresa.py` (claves nuevas),
`test_f002_fuente_unica.py` (`ANCLAS` + `"regla-cero"`) y
`test_f049_avisos_registro.py::test_f049_r1_…` («se edita»). Los dos
`test_f049_r2_…` **no se tocaron** (opción B) y pasan.

## 2. Decisiones de diseño

- **`repartir_choques`** y **`es_nuestra_de_otra`**: puras nuevas (reparto
  R4-R5 por `registro_id` ↔ choques por `ide`; condición de R15).
- **`lineas_registradas` sin `ides` delega en `lineas_por_synckey`**: los
  tests de F-055 no cambian.
- **Paso 9 bis antes del alta de partes**: solo las acciones que INSERTAN dan
  de alta parte o leen `max_pos`; la que edita no crea parte y la que cae por
  «línea cambiada» no deja uno vacío.
- **R12** con las mismas reglas que el preflight (`pisables_al_cero`,
  `criterio_choque`, `M*`, sin enlaces, `parte_est` activo). Si falla un
  choque, cae el pisado entero.
- **Una misma línea en dos pisados** se reparte una vez. `usadas` arranca
  vacío: una línea al 0 % nunca es choque (simplificación de T14, mató un
  superviviente).
- **R13**: una sola relectura, `lineas_registradas(claves escritas, ides
  editados y puestos a 0)`. Editada sin nuestra `can` o sin la `synckey` de R9
  → sale de `escritas`/`editadas` y va a `omitidas`; puesta a 0 que no quedó
  a 0 → aviso al log.
- **Log R18** «[registro] edita / pone a 0 ide=… parte=… registro=…
  antes=… despues=…»; `despues` usa `a.can`/`a.tot`, ya redondeados por las
  reglas (simplificación de T14).
- **Desviación justificada (T9)**: la fase `estado` del script lee además
  `pos`, `paride` y `tex` (solo lectura), para que T15 compruebe que la
  edición no mueve `pos` ni el parte y deja la marca en `tex`.
- **api (T11)**: `getattr(a, "sigrid_hmores_ide", None)`: los dobles
  anteriores no traen la columna.
- **Defecto propio cazado en T8**: `en_cerrado` (T6) pisaba una variable
  existente; renombrada a `lineas_cerradas`, con test de regresión.

## 3. Fase RED (trazas reales)

Comandos desde `services/dedicacion-<servicio>`, con
`.venv/Scripts/python -m pytest <fichero> -q -p no:cacheprovider [-k …]`,
tests escritos y código aún sin escribir. Trazas completas en el scratchpad
del implementer (`f051/red_t*.txt`). T1-T2 (55 tests):

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
3 failed, 5 passed in 4.12s
```
T6, `-k "r3 or r4 or r5 or r7 or r1_"`:
```
E   escribir and [Conflicto(cl...cero_ides=[])] == []      (la línea a 0 era choque)
E   assert [410600, 5002] == [5002]                         (la pisable en el contexto)
E   AssertionError: assert ('pisado', None, []) == ('pisado', 5009, [])
11 failed, 1 passed, 8 deselected in 4.10s
```
T7, `-k "r5 or r6 or r8 or r10 or r11 or r12"`:
```
E   AttributeError: 'SigridWriteClient' object has no attribute 'stmt_editar_linea'. Did you mean: 'stmt_borrar_linea'?
10 failed, 11 deselected in 4.18s
```
T8, fichero entero (los de T5-T6 ya en verde):
```
E     Left contains 3 more items, first extra item: {'sql': 'delete', 'parameters': [5003]}
E   assert [128, 192] == [128]                              (la editada consumía pos)
32 failed, 23 passed in 7.36s
```
Regresión de `en_cerrado`: `E AssertionError: assert ['sin_partida'] == []`
· `1 failed, 54 deselected`. T9, `-k respuesta` y `-k script`:
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
T12 con la opción B (front), `tests/test_f051_modal_pisado.py
tests/test_f049_avisos_registro.py`:
```
E   - 00319: se edita la línea 8001 (MADM 40%, fec 20260930); quedan a 0: línea 8002 (MADM 25%, fec 20260915), línea 8003 (MADM 10%, fec 20260901) y se escribe 60%
E   + 00319: se borran línea 8001 (MADM 40%, fec 20260930), línea 8002 (MADM 25%, fec 20260915), línea 8003 (MADM 10%, fec 20260901) y se escribe 60%
E   assert 'borr' not in 'madm de gon... escribe 60%'
6 failed, 17 passed in 5.77s
```
Sin fase RED propia: T3 (modelos), T10 (no-regresión de R19) y T13 (docs).
Tests de T14: cada uno contra su mutante a mano, **12 de 12 muertos**.

## 4. Mutación (T14, rigor crítico)

Detalle y análisis en `progress/mutacion_F-051.md`.

- **1.ª campaña** (HEAD `e74dbe7`, `--workers 1`): 138 mutantes, 122
  muertos, **16 supervivientes**, 3162,8 s. Doce se mataron con tests nuevos
  (redondeos y `or 0` de la edición, `hmoide`/`hmores_ide` nulos, lote con
  las claves justas, `enlazada` por defecto, igualdad del `ide` en la api);
  tres dejaron de existir con dos simplificaciones (`despues` con
  `a.can`/`a.tot`; `usadas` vacío). Tabla en el informe de mutación.
- **2.ª campaña** (HEAD `4dea061`, `--workers 1`, completa): **134
  mutantes, 133 muertos, 1 superviviente, 0 timeouts**, 1791,9 s.
- **Superviviente**: `registro_pipeline.py:1095`, `>= 0.000001` → `>` en la
  comprobación de R13. **Equivalente**: solo difiere si la diferencia vale
  exactamente el `float` 1e-6, y con `can` redondeado a 4 decimales ninguna
  entrada lo alcanza (búsqueda exhaustiva de los 9.999 valores ±40 ulp, sin
  un solo caso). Sin test posible; **pide que el humano acepte la
  justificación** (rigor crítico).

## 5. `bash harness/init.sh` (T17, worktree, HEAD `abb5638`)

Sin ningún `[KO]` («ENTORNO LISTO. Puedes trabajar.»): raíz 418 passed, 1
skipped; api 949; front 310; transfer 1075. **PUERTA COBERTURA 99,2 %** de
255 líneas cambiadas (253/255, umbral 80 %, crítico); PUERTA TAMAÑO dentro.
`abb5638` (tras la campaña) solo quita avisos de ruff propios (imports,
paréntesis en la cadena de la guarda, sin cambio de SQL); ruff 277 avisos (258
en `2c75a1c`): los 19 de más son `Optional[...]` como el resto de esos
ficheros, `dict()` en tests y un `PYI034` en un doble.

## 6. Verificaciones MANUAL pendientes

- **T15 (humano, modo pruebas, 0404)**. Preparación y pasos completos en
  `tasks.md` T15 (líneas `M*` a `can = 0` creadas a mano en el parte En
  registro de la 0404 de noviembre de 2026; transfer, api y front locales con
  `OBRA_PRUEBAS_FORZAR=true`). Lectura, en Git Bash:
  `cd services/dedicacion-transfer && .venv/Scripts/python prueba_escritura_porcentajes.py estado --ano 2026 --mes 11`
  (solo lectura; anotar `ide` y `pos`). Esperado: mismo `ide` y `pos`, con
  el %, la partida, `PRUEBA-PORC` y `porcentajes:…`, sin línea nueva, la otra
  a 0; tras cambiar el %, «se edita» y la misma línea con el % nuevo; tercera
  vez, «ya registrada»; ningún `DELETE` en el log. **Ojo con la limpieza**:
  `limpiar --confirmar` borra también las líneas de Administración EDITADAS
  en la 0404 (quedan con `PRUEBA-PORC` y nuestra `synckey`, D15 = A); la del
  segundo recurso la quita el humano a mano.

## 7. Fuera del alcance y pendiente

- **T16 (líder, al desplegar, orden transfer → api → front)**: refrescar
  `azure-apps/dedicacion.md` desde `docs/INTEGRACION.md` §1, §5 y §7. Lo que
  cambia: el transfer **edita en su sitio** líneas `M*` de partes
  compartidos (`UPDATE` con guarda: reside, `can` y `synckey` leídas, sin
  enlaces, parte activo) y **no borra** ninguna en el registro (`borradas`
  = 0); de ida, `lineas[].hmores_ide`; de vuelta, `ya_registradas_ide`,
  `editadas`, `a_cero` y `escritas[].editada`. Avisar a `partes` de que el
  transfer edita líneas `M*` de sus partes sin borrarlas.
- Aceptación del humano del mutante equivalente (§4). Ningún agente ha
  escrito en Sigrid; ningún `push`.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados | 2.752 passed, 1 skipped, 0 failed: raíz 418 (+1 skipped), api 949, front 310, transfer 1075 |
| Cobertura de líneas cambiadas | 99,2 % (253/255), PUERTA COBERTURA de `init.sh` |
| Mutación | 134 generados, 133 muertos, **1 superviviente equivalente justificado**, 0 timeouts; `--workers 1`; 1791,9 s (1.ª campaña: 138 / 16 supervivientes, resueltos) |
| Tiempo de la suite | raíz 74,89 s; api 102,55 s; front 85,40 s; transfer 58,18 s (pytest, en `init.sh`) |
