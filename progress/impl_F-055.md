# F-055 · Informe del implementer

Rama `feature/F-055-preflight-rapido` (copia `porcentajes-f041`). Rigor
`critico`. Spec aprobada por el humano el 2026-10-13 (D9-D10 el 2026-10-14).
Hechas: **T1, T2b, T2c, T3-T8** (transfer entero). **T9 implementada pero
BLOQUEADA** (abajo). T2 (MANUAL) sigue sin marcar: el humano tomará aparte
las cifras de navegador.

## BLOQUEO en T9 (2026-10-15)

```
$ cd services/dedicacion-api && .venv/Scripts/python -m pytest -q
FAILED tests/test_f050_partida_linea.py::test_f050_r12_r18_el_repositorio_mapea_la_partida
FAILED tests/test_f050_partida_linea.py::test_f050_r12_r18_las_lineas_del_trabajador_llevan_su_partida
E   AttributeError: 'types.SimpleNamespace' object has no attribute 'propuesta_ide'
2 failed, 798 passed, 1 warning in 72.46s
```

Fuera de la lista cerrada: sus filas de `asignacion` son `SimpleNamespace` a
mano sin las columnas `propuesta_*`, que el repositorio ya lee (R13). En T10
caerá igual su `_fila_r19` (`_payloads` leerá `propuesta_ide`, R16). No falla
ninguna aserción. **Propuesta:** lista cerrada para esas filas falsas
(`propuesta_*=None` en los tres `SimpleNamespace` de asignación), sin tocar
aserciones; alternativa no recomendada, `getattr(…, None)` en el código solo
para esos dobles. Barrido T10-T12b: los transfer falsos, `_fila`, `_Uow`,
fixtures `api`/`_cliente` y `CAMPOS_*` ya están en la lista; las rutas de
sync que fallan con 502 no tocan `propuestas_mes`; las respuestas exactas de
rutas que he visto (selector, registro) no cambian. Lo confirmo al implementar.

**Bloqueo de T4 resuelto (2026-10-15):** el humano añadió
`test_pipeline_offline.py` a la lista cerrada («añade test_pipeline_offline.py
a la lista cerrada»): solo su `ClienteFalso` gana `validar_partidas`.

## T1 · Medición (R1, R2, C2 «antes») — resumen

Cliente: `medir_lecturas()` (contextvar anidable), `apuntar_lectura` (log
`[sigrid-read] <método> filas=<n|error> segundos=<s>`, sin SQL ni
parámetros) y `_lectura(nombre, sql, params)` en todas las lecturas;
`preflight` loguea `[registro] lecturas preflight obra=… lecturas=…
segundos_leyendo=… segundos_totales=…`; fase `medir` del script (R2).
`tests/test_f055_medicion.py` (35). **Desviación de design §5.1:** `_read`
conserva su firma y la medición va en `_lectura` (con `nombre` en `_read` se
rompían 35 tests anteriores con dobles de dos argumentos). RED:
`ImportError: cannot import name 'apuntar_lectura'`; con el esqueleto `30
failed, 5 passed`; verde 35.

## T2 · Cifras «antes» (script del humano, 2026-10-15)

`medir … --obra 0694 --obra 0696 --recurso 1705036 --partida 0694:384155`
(modo pruebas): 0694, **8 lecturas · 32.24 s**; 0696, **9 · 21.92 s**;
`TOTAL: 2 obras · 17 lecturas · 54.15 s leyendo · 55.28 s en total`; la que
más pesa, `horas_de_recursos` (7.99 s). Es latencia en serie: el diseño
agrupa y paraleliza; el líder no paró. **Navegador:** pendiente del humano.

## T2b · Orden a → c → b (R38, D10)

`proponer_partida`: `previa_en_obra` (a) → `resolver_normal` (c) →
`ultima_de_recurso` (b), docstring con el orden. Lista cerrada:
`test_f050_r1_sin_paso1_va_al_paso2` espera `(2108, "auto_nombre")`.
`tests/test_f055_orden_propuesta.py` (8): a > c, c > b, sin c sale b con su
`origen`, sin nada None, (a) que empata pasa a (c), selector = preflight.
RED (`pytest tests/test_f055_orden_propuesta.py -q --tb=line`):
```
E   AssertionError: assert Propuesta(par... · obra 0696') == Propuesta(par..., origen=None)
E   AssertionError: assert (2110, 'ultimo_parte') == (2108, 'auto_nombre')
E   AssertionError: assert (80003, 'ulti... · obra 0678') == (80001, 'auto_nombre', None)
3 failed, 5 passed in 3.04s
```
Verde 8; suite 793.

## T2c · `#regla-partida` con el orden nuevo

`docs/ARCHITECTURE.md`: (1) parte anterior → (2) casamiento → (3) último
parte, viñeta de D10 (el último parte solo actúa si no casa nada) y la línea
de decisión. `test_f002_fuente_unica.py`: 72 passed; `grep -n casamiento`:
líneas 665, 672, 674, 676.

## T3 · `validar_partidas` y `PartidaValida` (R3, R4)

`PartidaValida(ide, obride, cod, res, es_hoja, activa)` inmutable con
`vale_en(obra)`; `validar_partidas` (SQL de design §6, trozos de
`LOTE_PARAMETROS = 500`, `truncated` → error); el doble de `conftest.py`
(lista cerrada) lo deriva de sus presupuestos sin contar lectura.
`tests/test_f055_validar_partidas.py` (18): SQL, trozos, mapeo y **R4** con
una Sigrid emulada (hoja activa, baja, capítulo, capítulo de baja, hija de
otra obra, otra obra, inexistente: mismo veredicto que `construir_catalogo`).
RED: `ImportError: cannot import name 'PartidaValida' from
'domain.models.registro_models'`; verde 18; suite 812.

## T4 · Pipeline sin búsquedas de partidas (R3-R12)

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
Verde: `23 passed`; con el doble de `test_pipeline_offline.py` (lista
cerrada, decisión del humano) la suite del transfer da **835 passed**.

## T5 · Lecturas agrupadas del cliente (R20)

`obras_por_ide`, `partes_de_periodos` (clave `(obride, ano, mes)`, cada
clave pedida sale aunque esté vacía) y `lineas_de_partes` (por `hmoide`):
el SQL de la suelta con `IN`, la clave en la salida, el mismo orden y
`_trozos` de 500 (`lineas_de_partes` trocea partes y recursos);
`horas_de_recursos` en trozos de 500. `conftest.py` (lista cerrada): las tres
del doble se derivan de sus sueltas. `tests/test_f055_cliente_agrupado.py`
(17): SQL = suelta con `IN`, misma salida por clave, trozos, truncado,
medición y doble. RED: `17 failed` (`AttributeError: … no attribute
'obras_por_ide'`/`'partes_de_periodos'`/`'lineas_de_partes'`, `assert [1101]
== [500, 500, 101]`); verde 17; suite 852.

## T6 · `LecturasDelLote` y `SIGRID_LECTURAS_PARALELAS` (R20, R22-R24)

`application/services/lecturas_lote.py`: precarga en rondas A (obras por
`ide` y por código —origen, pruebas, postventa, VAR—, horas, `synckey`,
`validar_partidas`, historial de las peticiones con alguna pendiente segura),
B (partes de los destinos × periodos, presupuestos de postventa/VAR/origen
con pendientes, `partidas_de_lineas` solo de recursos con alguna hora sin
subcuenta) y C (`lineas_de_partes`). Responde de memoria solo si la consulta
está dentro (subconjunto, misma clave o ventana); si no, cliente real +
`fallos_de_memoria` + log. Un solo vuelo por clave (`Lock` + `Future`) para
obra por código, presupuesto, cuentas y siguiente PT; `escribir` lanza; la
agrupada que falla tumba la precarga, la compartida vuelve a quien la pide;
`contextvars.copy_context` en cada hilo. Ajuste
`SIGRID_LECTURAS_PARALELAS` (4, `ge=1, le=8`) y `.env.example`.
`tests/test_f055_lecturas_lote.py` (34). **RED honesta:** el borrador del
módulo se escribió antes que sus tests; la fase RED se tomó apartándolo
(`ModuleNotFoundError: No module named 'application.services.lecturas_lote'`)
y luego fallaron 3 tests por el propio doble (contaba lecturas anidadas: el
doble del test se arregló). Verde 34 (tres veces seguidas); suite 886.

## T7 · Preflight en lote (R19, R21, R24, R25; C1, C2)

`application/pipelines/registro_lote.py` (`RegistroLote.preflight`: precarga
y luego el mismo `RegistroPipeline.preflight` por obra en el pool;
excepción de una obra en su posición), `_respuesta_preflight` extraída en
`app.py` (la suelta da lo mismo: sus tests siguen verdes), `LoteIn` y
`def preflight_lote` (502 si falla la precarga). Tests
`tests/test_f055_lote.py` (17) y el plugin `tests/f055_equivalencia_lote.py`,
que en un pytest aparte repite **cada preflight** de `test_f037_pipeline`,
`test_f050_pipeline`, `test_f002_pipeline` y `test_f039_preflight_var` en un
lote sobre una copia del doble y exige la misma respuesta HTTP (o la misma
excepción): ≥ 100 iguales y ≥ 1 error igual.
**Decisiones para el reviewer:** (1) el plugin no compara, con nombre, un
escenario cuyo doble da un código distinto en cada `siguiente_cod_pt` (el
lote lo lee una vez por año y empresa, design §2; en Sigrid es `MAX+1`): lo
cubre `test_f055_r21_siguiente_cod_pt_una_vez_y_lo_mismo`; (2) **C2**: una
obra con elegidas hace en lote 8 lecturas en pruebas (7 en real) en **≤ 4
rondas**; contadas como C1 (sin `cuentas_de_centro`, una por centro, ni la
obra de pruebas, una por lote) son **6**: así lo fija el test. Si C2 quería
6 lecturas en total, no se puede con el diseño (cada tipo es una lectura).
RED: `ModuleNotFoundError: … 'application.pipelines.registro_lote'`
(borrador apartado) y `ImportError: cannot import name
'_respuesta_preflight'`; verde 17; suite 902.

## T8 · Propuestas en lote (R34, R21, R24, R25; C7)

`LecturasDelLote.precargar_propuestas` (A: obras e historial de todos los
recursos por ventana; B: presupuesto de cada obra, en paralelo),
`RegistroLote.proponer` (`{ok: true, propuestas}` o el `{ok: false, error}`
de la suelta), `PropuestaLoteIn` y `def propuesta_lote` (periodos distintos
422; empresa no válida u obra de otra empresa o no encontrada, solo su
entrada; fallo compartido 502). El plugin compara también cada `proponer`
de `test_f050_endpoint_propuesta` y `test_f055_orden_propuesta` (11 iguales,
2 errores iguales); no compara, con nombre, los `test_f050_script_propuesta_*`
(el script envuelve el doble con cierres sobre el original). C7: 10 obras →
1 lectura de obras, 1 de historial, 10 de presupuesto, ≤ 4 rondas, ≤ 4 a la
vez. `tests/test_f055_propuesta_lote.py` (15). RED: `15 failed`
(`'RegistroLote' object has no attribute 'proponer'`, rutas 404); verde 15;
suite del transfer **917 passed** (72.5 s).

## T9 · La propuesta guardada en la api (R13, R17) — implementada, bloqueada

ORM `AsignacionORM.propuesta_ide` (BigInteger) y `_cod/_res/_metodo/_origen`
(Text), nulables; `Linea.propuesta_*` al final; `_a_linea_con_partida` y
`reemplazar` con ellas; `guardar_propuesta(periodo, trabajador, clave,
propuesta, *, solo_si_vacia=False) -> bool` (puerto y repositorio: `UPDATE`
del ORM con `partida_ide IS NULL` y, si se pide, `propuesta_ide IS NULL`);
`_conservar_partidas` copia la propuesta; copiar el mes y F8 la quitan
(`_sin_propuesta`); `_snapshot` y `_validar_lineas` no la llevan. Lista
cerrada: `test_f003_r8_…` (+5 columnas). `tests/test_f055_propuesta_guardada.py`
(20, R13 y R17). RED: `20 failed` (`Linea.__init__() got an unexpected
keyword argument 'propuesta_ide'`, `KeyError: 'propuesta_cod'`, `no attribute
'guardar_propuesta'`); verde 20 + `test_f003_esquema` (83 en total).

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests transfer (tras T8) | **917 passed** (72.52 s) |
| Tests api (con T9) | **798 passed, 2 failed** (el bloqueo de T9), 72.46 s |
| Tests de F-055 | transfer **167** (`test_f055_*`, más el plugin de equivalencia); api 20 |
| Cobertura de las líneas cambiadas | última medida: 100 % de 184 (tras T4); se repite al desbloquear |
| Mutantes | campaña completa en T16 (no empezada) |
| `bash harness/init.sh` | no se ha repetido tras T4 (con la api en rojo no vale) |
