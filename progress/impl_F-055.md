# F-055 · Informe del implementer

Rama `feature/F-055-preflight-rapido` (copia `porcentajes-f041`). Rigor
`critico`. Spec aprobada por el humano el 2026-10-13 (D9-D10 el 2026-10-14).
Hechas: **T1, T2b, T2c, T3**. **T4 implementada pero BLOQUEADA** (abajo).
T2 (MANUAL) sigue sin marcar: el humano tomará aparte las cifras de navegador.

## BLOQUEO en T4 (2026-10-15)

Con T4 la suite del transfer da **834 passed, 1 failed**, y el que falla está
**fuera de la lista cerrada** de `tasks.md`:

```
$ cd services/dedicacion-transfer && .venv/Scripts/python -m pytest -q --tb=line
FAILED tests/test_pipeline_offline.py::test_override_manual - AttributeError:...
E   AttributeError: 'ClienteFalso' object has no attribute 'validar_partidas'
1 failed, 834 passed, 1 warning in 7.79s
```

`test_pipeline_offline.py` tiene su **propio** `ClienteFalso` (no el de
`conftest.py`), y `test_override_manual` manda una línea con partida elegida
(80002). R3 obliga a validarla con `validar_partidas` (una lectura por `ide`);
ese doble no tiene el método. **No falla ninguna aserción.**

- **Propuesta:** añadir `test_pipeline_offline.py` a la lista cerrada **solo
  para su doble**: un `validar_partidas` derivado de sus dos presupuestos
  (`capitulos`, `partidas_origen`), como el de `conftest.py` (T3). Ninguna
  aserción cambia.
- Alternativa (no recomendada): que el pipeline lea el presupuesto si el
  cliente no tiene `validar_partidas`: una rama que solo existiría para ese
  doble y que la mutación dejaría sin test.
- Barrido hacia delante (para no volver a parar por lo mismo): en el transfer
  no hay otro doble propio que reciba líneas con partida (`test_f022` hereda
  de `conftest` y no manda elegidas; `test_f047` tampoco). En la api, los
  transfer falsos están en `test_f022_empresa_en_linea` y
  `test_f024_registro_empresa` (en la lista), y los demás los importan de
  ahí; no lo puedo asegurar del todo hasta implementar T10-T12b.

Estado del árbol: T4 en el commit «F-055: T4 a medias, bloqueada», sin marcar
en `tasks.md`; `features.json` en `blocked`; motivo en `progress/current.md`.

## T1 · Medición (R1, R2, C2 «antes») — resumen

| Fichero (transfer) | Cambio |
|---|---|
| `infrastructure/sigrid/sigrid_write_client.py` | `medir_lecturas()` (contextvar anidable con `Lock`), `apuntar_lectura` (log `[sigrid-read] <método> filas=<n\|error> segundos=<s>`, sin SQL ni parámetros) y `_lectura(nombre, sql, params)`, por la que pasan todos los métodos de lectura |
| `application/pipelines/registro_pipeline.py` | `preflight` mide y loguea `[registro] lecturas preflight obra=… lecturas=… segundos_leyendo=… segundos_totales=…`, también si falla |
| `prueba_escritura_porcentajes.py` | fase `medir` (R2): `--obra`/`--recurso` repetibles, `--partida OBRA:PARIDE`, `--lote` (aún sin efecto) |
| `tests/test_f055_medicion.py` | 35 tests (R1, R2, C2) |

**Desviación de design §5.1:** `_read` conserva su firma `(sql, params)`; la
medición va en `_lectura`. Con `nombre` en `_read` se rompían 35 tests
anteriores (F-022, F-024, F-037, F-050) que sustituyen `_read` por dobles de
dos argumentos. Lo fija `test_f055_r1_read_conserva_su_contrato_y_sus_dobles`.
C2 «antes»: 8 lecturas en serie con elegidas (9 sin subcuenta).

RED de T1 (`pytest tests/test_f055_medicion.py -q --tb=line`): primero
`ImportError: cannot import name 'apuntar_lectura'`; con el esqueleto,
`30 failed, 5 passed` (`assert [] == ['[sigrid-rea...egundos=1.50']`,
`invalid choice: 'medir'`, `assert 0 == 9`…); verde `35 passed`.

## T2 · Cifras «antes» (script del humano, 2026-10-15)

`medir --ano 2026 --mes 9 --obra 0694 --obra 0696 --recurso 1705036
--partida 0694:384155` (modo pruebas, solo lectura): 0694, **8 lecturas ·
32.24 s leyendo**; 0696, **9 lecturas · 21.92 s**; `TOTAL: 2 obras · 17
lecturas · 54.15 s leyendo · 55.28 s en total`. La que más pesa,
`horas_de_recursos` (7.99 s); el presupuesto pesa poco (1.6-1.75 s). Es
latencia por lectura en serie: el diseño agrupa y paraleliza (R20-R23). El
líder decidió no parar. **Navegador:** pendiente del humano (no bloquea).

## T2b · Orden a → c → b (R38, D10)

- `propuesta_partida.py`: `proponer_partida` llama a `previa_en_obra` (a),
  luego `resolver_normal` (c) y, solo si no casa, `ultima_de_recurso` (b);
  docstring del módulo con el orden y la fecha. Nada más del módulo cambia.
- Lista cerrada: `test_f050_r1_sin_paso1_va_al_paso2` pasa a esperar
  `(2108, "auto_nombre")` (con docstring que remite al test nuevo).
- `tests/test_f055_orden_propuesta.py` (8 tests): a gana a c; c gana a b;
  sin c, b con su `origen`; sin nada, None; (a) gana aunque no case; (a) que
  empata pasa a (c), no a (b); selector y preflight dan lo mismo (2 casos).

RED (`pytest tests/test_f055_orden_propuesta.py -q --tb=line`):
```
E   AssertionError: assert Propuesta(par... · obra 0696') == Propuesta(par..., origen=None)
E   AssertionError: assert (2110, 'ultimo_parte') == (2108, 'auto_nombre')
E   AssertionError: assert (80003, 'ulti... · obra 0678') == (80001, 'auto_nombre', None)
3 failed, 5 passed in 3.04s
```
(los 5 que pasaban describen casos que el orden no cambia). Verde: `8 passed`;
suite del transfer `793 passed`.

## T2c · `#regla-partida` con el orden nuevo

`docs/ARCHITECTURE.md` (fuente única): (1) parte anterior → (2) casamiento →
(3) último parte, viñeta nueva con D10 y la nota de que el último parte solo
actúa si el casamiento no da nada, y la línea de decisión con fecha y cita.
`pytest tests/test_f002_fuente_unica.py`: **72 passed**; `grep -n casamiento
docs/ARCHITECTURE.md` → líneas 665, 672, 674, 676 con el orden nuevo.

## T3 · `validar_partidas` y `PartidaValida` (R3, R4)

- `domain/models/registro_models.py`: `PartidaValida(ide, obride, cod, res,
  es_hoja, activa)` inmutable, con `vale_en(obra_ide)` (obra, hoja y alta).
- Cliente: `validar_partidas(parides)`, SQL de design §6 con alias, trozos de
  `LOTE_PARAMETROS = 500`, sin partidas no lee, medida como
  `validar_partidas`; `truncated` → `RuntimeError`.
- `conftest.py` (lista cerrada): `ClienteFalso.validar_partidas` derivado de
  sus dos presupuestos sin contar como lectura de presupuesto; anota cada
  llamada en `validadas`.
- `tests/test_f055_validar_partidas.py` (18 tests): SQL, trozos, mapeo,
  medición, truncado, inmutable y **R4** con una Sigrid emulada sobre dos
  obras: hoja activa, baja, capítulo, capítulo de baja, hoja bajo capítulo de
  baja, raíz con hija de otra obra, otra obra e inexistente dan el mismo
  veredicto que `construir_catalogo`; el doble ≡ `construir_catalogo`.
  `test_f055_medicion` gana `validar_partidas` en su lista de métodos.

RED (`pytest tests/test_f055_validar_partidas.py -q --tb=line`):
```
E   ImportError: cannot import name 'PartidaValida' from 'domain.models.registro_models'
1 error in 0.66s
```
Verde: `18 passed`; suite del transfer `812 passed`.

## T4 · Pipeline sin búsquedas de partidas (R3-R12) — implementada, bloqueada

- Modelos: `LineaEntrada.propuesta_paride/_cod/_res/_metodo/_origen`,
  `LineaIn` igual (contrato HTTP), `AccionLinea.partida_res`.
- `registro_pipeline.py`: `_validas` lee UNA vez `validar_partidas` con la
  elegida de cada línea de obra normal o, sin ella, su propuesta guardada
  (postventa y VAR fuera); elegida que no vale → omitir con
  `MOTIVO_PARTIDA_NO_HOJA` (R5); propuesta guardada que vale → sus
  `partida_cod/_res/_metodo/_origen` tal como llegan (R8, «se escribe lo que
  enseña el cuadrante», design §10); si no, pendiente (R6/R7): presupuesto e
  historial solo de las pendientes. `partida_res` en manual (de la
  validación), guardada, propuesta, postventa (casada o manual) y VAR (R9).
  Sale la lectura forzada de F-049 d: `partidas_obra` `[]` sin pendientes
  (R10).
- Tests: `tests/test_f055_pipeline_partidas.py` (23 tests, R3-R12 y el
  contrato HTTP); lista cerrada: los dos `test_f049_d_*` esperan
  `partidas_obra == []` y ninguna lectura; propios de F-055:
  `test_f055_c2_antes_*` y el resumen del preflight cuentan `validar_partidas`
  en lugar de `capitulos_de_obra` (previsto en T1).

RED (`pytest tests/test_f055_pipeline_partidas.py -q --tb=line`):
```
E   assert ([555001] == []        (la elegida aún leía el presupuesto)
E   TypeError: LineaEntrada.__init__() got an unexpected keyword argument 'propuesta_paride'
E   AttributeError: 'AccionLinea' object has no attribute 'partida_res'.
E   KeyError: 'partida_res'      (respuesta HTTP del preflight)
21 failed, 2 passed in 3.90s
```
(los 2 que pasaban: «sin partidas no valida» y la VAR, que no cambian).
Verde: `23 passed`; suite del transfer **834 passed, 1 failed** (el bloqueo).

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests transfer (tras T4) | **834 passed, 1 failed** (`test_pipeline_offline::test_override_manual`, el bloqueo), 7.79 s |
| Tests de F-055 hasta aquí | medición 36, orden 8, validar 18, pipeline 23: **85 passed** |
| Cobertura de las líneas cambiadas | se medirá con `bash harness/init.sh` al desbloquear (con la suite en rojo la puerta no vale) |
| Mutantes | campaña completa en T16 (no empezada) |
| `bash harness/init.sh` | ver la línea final de este informe (tras el commit del bloqueo) |
