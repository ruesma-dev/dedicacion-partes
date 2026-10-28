<!-- progress/impl_F-068.md -->
# F-068 · informe del implementer

La partida del recurso vinculado se propone como la del trabajador
(enmienda de F-044 R15-R16). `sdd: true`, rigor **crítico**. Rama
`feature/F-068-propuesta-vinculado-como-titular` (desde `1188081`), worktree
`porcentajes-f068`, `.venv` enlazados; ningún `.env` leído ni copiado.
**Ninguna escritura en Sigrid** (ni lectura: no hizo falta; todo con dobles).

## Qué cambió (un commit por tarea)

| Commit | Tarea | Qué |
|---|---|---|
| `dedaeb5` | T1 | transfer: `descripcion` en `VinculadoEntrada`/`VinculadoIn`; `tipo_res`/`descripcion` en `VinculadoPropuestaIn` (+ `para_pipeline()`: solo viajan si no son None) (R18) |
| `45271ff` | T2 | `reglas_vinculados`: `hojas_con_subcuenta` (y `partida_ci_del_tipo` sobre ella), `es_capitulo_ci4` (D1 numérico), `puntuar` (casador uno a uno), `desempate_ci4` (R5-R8) |
| `b63bcea` | T3 | `partida_por_cuenta_o_nombre` con `sin_ci`/`varias_ci`/`empate_nombre` y sus textos (R4-R9, D5); texto nuevo de `sin_ci` en un test de F-044 (R9) |
| `9a746cf` | T4 | `partida_por_historial` sobre `previa_en_obra` (importada, no copiada; solo `CI*`, D2) y orden nuevo en `partida_del_vinculado(…, historial=None)`; `origen` en `PartidaElegida`/`PartidaVinculado` (R1-R3, R10) |
| `7dc55d4` | T5 | `SigridWriteClient.historial_de_vinculados` (SQL de design §7, lotes, `m.obride = ?`, cualquier hora) con `_linea_historial` compartido con `historial_partidas`; dobles en `conftest.py` y `test_pipeline_offline.py` (R11, R13) |
| `0610187` | T6 | `PasoVinculados.decidir/_partida`: historial y cuentas perezosos (`_UnaVez`), propuesta guardada con `METODOS_PROPUESTA_PROPIA`; `_preflight` pasa la ventana (R11, R12, R14, R16). Incluye el código de T8 (ver desvíos) |
| `a5ff630` | T7 | `PasoVinculados.proponer` y `RegistroPipeline.proponer`: ventana, `tipo_res`/`descripcion`, `origen` en la respuesta (R15) |
| `64d9332` | T8 | tests del lote (una lectura por obra; lote = suelto) (R15) |
| `606b7d6` | T9 | revisión de los tests de F-044 del transfer: solo cambió el texto de `sin_ci` (ya en T3) |
| `74610a6` | T10 | api: `METODOS_PROPUESTA_VINCULADO` ampliado, `SubfilaVinculado.descripcion`, `_a_subfila`, `_vinculado` y `peticion_de_subfilas` con los textos (R17, R18) |
| `c3a91c8` | T11 | front: `capitulo_ci4: "capítulo CI.4 en empate"` en `rotuloOrigen` (R20) |
| `1e57fd4` | T12 | `ARCHITECTURE.md#regla-vinculado` (Partida, Lecturas, atribución F-068, fila de acceso a datos) e `INTEGRACION.md` §5 (contrato, lectura nueva, orden de publicación) (R21) |
| `e28dbd2` | T13-T14 | MANUAL de solo lectura y pendiente de `azure-apps` en `progress/current.md` |
| `ca11bc7` | — | mutación manual del JS (`progress/mutacion_manual_F-068.md`); avisos de ruff de los tests nuevos |
| `cd8f0be` | — | supervivientes de la campaña 1 (ver «Mutación») |
| `a521399` | — | campaña 2 con el análisis del superviviente |
| (este) | T15 | `init.sh` en verde, este informe, `[x]` de T15 |

Ficheros de producción: transfer `application/services/reglas_vinculados.py`,
`application/pipelines/registro_vinculados.py`,
`application/pipelines/registro_pipeline.py`,
`application/services/lecturas_lote.py`,
`infrastructure/sigrid/sigrid_write_client.py`,
`domain/models/registro_models.py`, `interface_adapters/api/app.py`; api
`application/registro_sigrid.py`, `application/partidas_linea.py`,
`domain/models.py`, `infrastructure/db/repositories.py`; front
`static/js/app.js`. Tests nuevos: transfer `test_f068_reglas.py`,
`test_f068_sql.py`, `test_f068_pipeline.py`; api `test_f068_api.py`; front
`test_f068_front.py`. Ni `partida_catalog.py`, ni `partida_matcher.py`, ni
`text_match.py` se tocan (se usan). Sin dependencias nuevas.

## Decisiones de diseño

- **Una sola regla para preflight, selector y lote**: `_partida` (preflight)
  y `proponer` (selector/cola) llaman a las mismas `partida_por_historial` y
  `partida_por_cuenta_o_nombre` vía `partida_del_vinculado`; el método sale
  del segundo elemento de `ci()`, no de una constante.
- **Lecturas perezosas**: el historial se lee una vez por petición con TODOS
  los recursos vinculados, solo si alguno llega a ese paso; las cuentas,
  solo si alguno llega al de su cuenta. La ventana (`_ventana`, la del
  trabajador con el periodo, D3) también se calcula solo entonces (cambio
  de la campaña 1: antes era `(0, 0)` sin vinculados, mutante equivalente).
- **Textos opcionales**: `descripcion` y `tipo_res` solo viajan si tienen
  valor (api y `para_pipeline()` del transfer): sin ellos, el payload es
  byte a byte el de F-044 (tests R18 «la entrada de hoy»).
- **Empate a 6 decimales**: el desempate CI.4 filtra con el mismo redondeo
  que `_maximo_unico` (importada de `propuesta_partida`), fijado por un test.

## Desvíos respecto a la spec (justificados)

1. **Tests de F-044 cambiados: 4, no los de design §10.** Lista cerrada:
   - transfer `test_f044_mutacion.py::test_f044_r16_por_que_sin_ci_en_palabras_o_tal_cual`:
     texto nuevo del motivo `sin_ci` (R9).
   - api `test_f044_cuadrante_vinculados.py::test_f044_r9_metodos_de_propuesta_de_subfila`:
     `auto_nombre` pasa a guardarse (R17).
   - api `…::test_f044_r9_selector_de_la_subfila_propone_y_guarda` y
     `…::test_f044_r9_en_segundo_plano_se_proponen_las_subfilas`: el payload
     lleva `tipo_res` (R18).
   R22 dice «los que fijan el orden viejo»; estos tres de la api fijan el
   contrato viejo (lista de métodos y payload), que R17/R18 cambian a
   propósito. Los de design §10 (`test_f044_pipeline_vinculados.py`,
   `test_f044_lote.py`, `r16_sin_ci…`, `r9_titular_sin_propuesta…`) pasan
   **sin tocarlos**: el doble de `conftest.py` devuelve historial vacío y los
   códigos de sus fixtures (`CIVE20`/`CIVE21`) no son del CI.4.
2. **El código de T8 (`LecturasDelLote.historial_de_vinculados`) entró en
   el commit de T6**: los tests de lote de F-044 usan la memoria del lote
   como cliente y sin ese método caían. La RED de T8 se demostró en una
   copia aislada sin el método (traza abajo; copia borrada).
3. **Clave de la memoria del lote**: (obra, desde, hasta, recursos). Dos
   peticiones de la misma obra con vinculados distintos leerían dos veces;
   la api manda una petición por obra, así que es «una vez por obra» (R15).

## Fase RED (trazas reales, antes del código de cada tarea)

Comandos desde `services/dedicacion-transfer` (T1-T8), `services/dedicacion-api`
(T10) y `services/dedicacion-front` (T11), con
`.venv/Scripts/python.exe -m pytest <fichero> -q -p no:cacheprovider`.

Intérprete `.venv/Scripts/python.exe -m pytest` del servicio, desde su carpeta
(transfer salvo T10, api, y T11, front). Salida recortada con `tail`, sin
editar las líneas.

**Central (R1, el caso de la 0678), T6**:
`pytest "tests/test_f068_pipeline.py::test_f068_r1_preflight_el_caso_de_la_0678" -q --tb=short`
```
tests\test_f068_pipeline.py:229: in test_f068_r1_preflight_el_caso_de_la_0678
    assert _partidas(pf) == {
E   AssertionError: assert {20: (0, None..., None, None)} == {20: (82413, ..., None, None)}
E     {20: (0, None, None, None)} != {20: (82413, 'CI.4.13', 'parte_anterior', 'parte PT26/00300 · 06/2026 · obra 0678')}
E     {21: (0, None, None, None)} != {21: (82401, 'CI.4.1', 'parte_anterior', 'parte PT26/00300 · 06/2026 · obra 0678')}
FAILED tests/test_f068_pipeline.py::test_f068_r1_preflight_el_caso_de_la_0678
1 failed in 3.76s
```
**T6 entero**, `pytest tests/test_f068_pipeline.py -q --tb=line`: `20 failed,
11 passed in 2.75s` (R7 sin historial ⇒ CI.4, R18, R11, R2/D3, R12, R14,
R13 y R16 ×9; lista completa en la traza, `FAILED …r16_guardada_con_metodo_propio_se_escribe_tal_cual[capitulo_ci4]`…).

**T1**, `pytest tests/test_f068_pipeline.py -q --tb=line` (solo los R18):
```
E … 'vinculados': [{'recurso_ide': 10, 'tipo': 'TF', 'categoria': None, 'cod': 'TF-10'}]}] != [… 'cod': 'TF-10', 'tipo_res': 'TELEFONO', 'descripcion': 'MOVIL 600'}]}]
7 failed, 1 passed in 2.87s
```
**T2, T3 y T4**, `pytest tests/test_f068_reglas.py -q --tb=short` (cae la colección, `1 error` cada vez):
```
E   ImportError: cannot import name 'desempate_ci4' from 'application.services.reglas_vinculados'
E   ImportError: cannot import name 'METODO_CAPITULO_CI4' from 'application.services.reglas_vinculados'
E   ImportError: cannot import name 'partida_por_historial' from 'application.services.reglas_vinculados'
```
**T5**, `pytest tests/test_f068_sql.py -q --tb=line`:
```
E   AttributeError: 'SigridWriteClient' object has no attribute 'historial_de_vinculados'
10 failed in 1.01s
```
**T7**, `pytest tests/test_f068_pipeline.py -q --tb=short -k "selector or ruta_devuelve_el_origen"`:
```
E   assert [] == [([20, 21, 22...2407, 202607)]
E   assert [555001] == []
E   AssertionError: assert {'a': {'20': None}} == {'a': {'20': {'paride': 82413, 'cod': 'CI.4.13', 'res': 'TELEFONIA', 'metodo': 'parte_anterior', ...}}}
8 failed, 1 passed, 31 deselected in 4.72s
```
**T8** (copia aislada sin `LecturasDelLote.historial_de_vinculados`),
`pytest tests/test_f068_pipeline.py -q --tb=short -p no:cacheprovider -k "lote"`:
```
E   TypeError: '<=' not supported between instances of 'str' and 'int'
E     Left contains one more item: ([20, 21, 22], 555001, 202407, 202607)
4 failed, 3 passed, 40 deselected in 6.99s
```
**T10** (api), `pytest tests/test_f068_api.py -q --tb=line -p no:cacheprovider`:
```
E   TypeError: SubfilaVinculado.__init__() got an unexpected keyword argument 'descripcion'
FAILED tests/test_f068_api.py::test_f068_r17_se_guardan[capitulo_ci4] - Asser...
16 failed, 13 passed in 7.07s
```
**T11** (front), `pytest tests/test_f068_front.py -q --tb=line -p no:cacheprovider -rs`:
```
      At index 0 diff: 'capitulo_ci4' != 'capítulo CI.4 en empate'
3 failed, 4 passed in 1.96s
```
Después, con el código de cada tarea, en verde (y las suites enteras).

## Mutación

**Python** (`python -m harness.mutacion --feature F-068`, completa, sin
muestreo, **4 workers**), informe `progress/mutacion_F-068.md`:

- **Campaña 1** (HEAD `e28dbd2`): 56 generados/evaluados, 51 muertos, **5
  supervivientes**, 0 timeouts, 1149,7 s. Dos equivalentes (`(0, 0)` de la
  ventana sin vinculados) se quitaron de raíz (ventana perezosa); dos
  (redondeo del empate, `round(v, 6)` → `7`) los mata un test nuevo; el
  quinto, abajo.
- **Campaña 2** (HEAD `cd8f0be`, la final del código): **54 generados y
  evaluados, 53 muertos, 1 superviviente**, 0 timeouts, 0 sin veredicto,
  1405,8 s (26,0 s por mutante; la máquina tenía otras campañas en marcha).
- **El superviviente** (`registro_vinculados.py:202`, `True` → `False` en
  `partida_del_vinculado(titular, None, True, ci, previa)`): equivalente,
  `elegida_valida` no se lee con `elegida=None`. Es el nº 4 de F-044, que el
  humano aceptó el 2026-10-26; **para F-068 necesita su visto bueno** (rigor
  crítico, máximo 0 supervivientes).

**JS** (`progress/mutacion_manual_F-068.md`, sobre
`e28dbd2ac4f827fdc870285ae39c5f2bd037bb4b`, 1 worker, 233,4 s): **5
mutantes de la entrada `capitulo_ci4` de `rotuloOrigen`, 5 muertos**, por los
tres tests de R20.

## Verificación

`rm -f .arnes_cache/suite_*.ok` y después `bash harness/init.sh`, solo y sin
tubería, sobre `a521399`: **«ENTORNO LISTO. Puedes trabajar.», exit 0, ningún
`[KO]`**. Un único `[AVISO]`: ruff, 309 avisos de deuda previa (los de los
ficheros de F-068 son los mismos que en `dev`; los 6 de los tests nuevos se
corrigieron en `ca11bc7`). Detalle: raíz `418 passed, 1 skipped`; api
`1337 passed`; front `458 passed` (con `node`, sin saltos); transfer `1737
passed`; `PUERTA COBERTURA: 100.0% de 126 líneas cambiadas cubiertas`;
`PUERTA TAMAÑO` dentro de los topes. Repetido tras escribir este informe:
ver «Evidencias».

## Pendiente (MANUAL, del humano)

- **T13** (solo lectura, local, sin «Registrar»): comandos exactos en
  `progress/current.md`, «⚠ Lo que espera al humano», entrada F-068.
- **T14** (al desplegar, transfer → api → front): `azure-apps/dedicacion.md`
  si lista las lecturas del transfer; D4-A, sin limpieza.
- Visto bueno del humano al equivalente de la campaña 2 (ver «Mutación»):
  el mismo argumento que aceptó en F-044 (nº 4).

## Fuera del alcance

- Las propuestas `ci_tipo` ya guardadas se quedan (D4-A).
- 0692/0693 sin historial y el vehículo de la 0678 sin historial quedan
  «sin partida» a propósito (design §10).

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests ejecutados (`init.sh`, `a521399`) | raíz 418 passed + 1 skipped; api 1337; front 458; transfer 1737: **3950 passed, 0 failed** |
| Tests nuevos de F-068 | transfer 152 (`reglas` 95, `sql` + `pipeline` 57), api 29, front 7 (ejecuciones de pytest, con parametrizados) |
| Tests de F-044 cambiados | 4 (lista cerrada en «Desvíos», 1) |
| Cobertura de las líneas cambiadas | **100,0 %** (126/126, umbral 80 %, nivel crítico) |
| Mutación Python, campaña final | 54 generados, 53 muertos, **1 superviviente equivalente** (pendiente del humano), 0 timeouts, 4 workers, 1405,8 s |
| Mutación JS (manual) | 5 generados, 5 muertos, 1 worker, 233,4 s |
| Tiempo de las suites (`init.sh`) | raíz 115,5 s; api 181,3 s; front 202,7 s; transfer 71,9 s (bajo cobertura, máquina cargada) |
| Lecturas/escrituras en Sigrid | 0 / 0 |
