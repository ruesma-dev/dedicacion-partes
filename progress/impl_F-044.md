<!-- progress/impl_F-044.md -->
# F-044 · informe del implementer (T1-T20, T22 y T24 hechas)

Rama `feature/F-044-recursos-vinculados`, worktree `porcentajes-f044`.
Rigor **crítico**. T1-T20, T22 y T24 hechas, una por commit; **T21 es MANUAL del humano**
(comandos en `progress/current.md`, «F-044 · T21»), T22 es la campaña de
abajo, T23 es del líder al desplegar y T24 es `init.sh` (resultado al final).
No se ha hecho ninguna escritura en Sigrid, ni real ni de pruebas.

## Qué cambió (por tarea)

| T | Commit | Qué |
|---|---|---|
| T1 | `bb059a7` | api `domain/vinculados.py`: `vincular`, una función pura (campo → trabajador; vacío, hacia un no trabajador o tipo excluido, aparte) |
| T2 | `8b3f6a2`, `01827e2` | api ORM `recurso_vinculado` (`empresa`, `fecha_baja`, decisión 3) y `asignacion_vinculado`; `PgVinculadoRepository`, `upsert_asignacion_vinculado` |
| T3 | `8a57ec6`, `22f84a4` | api `sync.vinculados` en `config.yaml`, pasos del sync y bloque del preview, **cableados en `deps.py`** (decisión 2) |
| T4 | `9285ee6` | transfer `VinculadoEntrada`, `reglas_vinculados.py` (partida del vinculado, CI del tipo), `cuentas_del_presupuesto` |
| T5 | `ff989ba` | transfer `PasoVinculados.proponer` en `partidas/propuesta(-lote)` |
| T6 | `eb3ceb1` | api: subfilas en el cuadrante, `CambiarPartida(vinculado_ide)`, propuesta de subfila (selector, preflight, cola) |
| T7 | `e2978ad` | front: columna «Tipo recurso», subfilas y su selector (`data-vinculado`) |
| T8 | `489f238` | cierre del bloque 1: las tres suites en verde |
| T9 | `f0930b4` | transfer: `AccionVinculado`, `Preflight/ResultadoRegistro.vinculados`, `Conflicto.vinculado`, `LineaIn.vinculados` |
| T10 | `6d74f00` | `decidir_vinculados` (hora, `pre`, `tot`, «sin importe mensual», «sigue al trabajador»), `synckey_vinculado`, `es_linea_de` |
| T11 | `4e983e8` | `evaluar_capacidad(es_jornada)`, `pisables_al_cero(hora)`, `emparejar_ceros(clave, hora)` con el valor de hoy por defecto |
| T12 | `9626265` | `stmt_editar_linea`/`stmt_poner_a_cero` con `hora` (sin ella, el SQL de hoy carácter a carácter) |
| T13 | `5a1d701` | preflight: `PasoVinculados` (partida, cuenta, parte, ya registrado, sin partida, pisado, cero, cerrado, capacidad) |
| T14 | `bcef052` | `ejecutar`: `EscrituraVinculados` tras el titular (ediciones con su hora, a 0, inserción, relectura) |
| T15 | `0c47d9d` | lote: precarga de horas, líneas, `synckey`/`hmores.ide` y partidas de los vinculados |
| T16 | `88c40d3` | respuesta de preflight y `ejecutar` con `vinculados`; `vinculado` solo en su conflicto |
| T17 | `49f1904` | script de pruebas: `estado` resume las `porcentajes:vin:`; `limpiar` ya las cubría (test) |
| T18 | `7758201` | api: `_payloads` manda `vinculados` (periodo ≥ `desde`) y `trazar_vinculados` guarda la traza |
| T19 | `86a5ada` | front: vinculados en el modal de registro con su selector; avisos con tipo y código |
| T20 | `bd38dc5` | `#regla-vinculado` (ARCHITECTURE) y sus remisiones; INTEGRACION §1, §5 y §7; ANCLAS |

Producción tocada: los tres servicios y `docs/` (`git diff dev --stat -- services docs`: 50 ficheros, tests incluidos).

**Tests ajenos tocados, todos de la lista cerrada**: api `test_f023_sync_empresa.py`,
`test_f026_vigencia.py`, `test_f030_catalogo.py`, `test_f032_empresas_sigrid.py`
(decisiones 2 y 3: solo dobles o admitir `recurso_vinculado`); front
`test_f050_subfilas.py`, `test_f050_m2_arreglos.py` (decisión 1: solo la
columna); transfer `conftest.py` (T12: el doble respeta `hora` y tiene
`cuentas_del_presupuesto`), `test_f013_sin_partida.py` (T9: el campo
`vinculado`) y `test_f002_fuente_unica.py` (T20: ANCLAS). Ninguna aserción
ajena se ha relajado.

## Decisiones de diseño y desviaciones

1. **Contratos por asignación intactos.** Un vinculado escrito no va a
   `escritas` ni a `ya_registradas`: solo a `vinculados`. Su entrada en
   `omitidas` lleva `vinculado_ide`; la api la guarda en su subfila y no en la
   asignación del titular. El toast del front la cuenta aparte.
2. **`PasoVinculados` en varios puntos del preflight** (R27: sus lecturas van
   con las de los titulares): `decidir` tras la partida del paso 4,
   `_cuentas` del 4 bis, parte del 5, `registradas`/`idempotencia` en la
   lectura del 6, `sin_partida` en el 6 bis, `conflictos_del_parte` dentro
   del bucle del 7 (la misma `lineas_del_parte`) y `cerrar` al final.
3. **R26: claves distintas.** El aviso de un vinculado retiene solo a ese
   vinculado, nunca al titular. El titular ya no toma como suyo el pisado
   confirmado de un vinculado: `_planear_ediciones` salta `c.vinculado`. El
   fallo apareció al pasar T14 a verde: el titular se omitía por «línea
   cambiada».
4. **Funciones generalizadas con el valor de hoy por defecto** (T11, T12):
   sin `hora`, la guarda y el SQL de F-051 no cambian. Lo comprueba un test
   carácter a carácter.
5. **T12 → T15.** La precarga del lote para los vinculados se hizo en T15.
   El superconjunto de partidas válidas incluye las líneas VAR, igual que
   `_validas` del pipeline (corregido en T18).
6. **T16.** Desde T9, `asdict(Conflicto)` publicaba `"vinculado": null` en
   todos los conflictos. `_conflicto` lo quita: sin vinculados, la respuesta
   es la de siempre.
7. **T18.** La traza va en `application/traza_vinculados.py`, con el mismo
   precedente que `traza_incidencias.py`: `test_f003` vigila que los
   `sigrid_*` de `registro_sigrid.py` sean columnas de `asignacion`, y la
   subfila usa `sigrid_parte`.
   - `subfilas_de` pasa a nivel de módulo y la usan el cuadrante y el
     registro.
   - La asignación va por subconsulta, así que sin línea no inserta: un
     `reemplazar` a mitad no tumba la traza del titular.
   - Un vinculado `ya_registrado` traza solo su estado y su `hmores.ide`,
     como el titular.
   - En VAR la subfila no manda partida: va con la del titular.
8. **T19.** `rotuloConflicto` evita `.filter(`, porque `test_f049_r3` vigila
   que el rótulo no filtre.
9. «Partida `CI*`» del titular significa que el código empieza por `CI`, no
   `clasifica_categoria`, que da `OTRO` a `CICO13`.

## Fase RED (salida real del fallo; comando en el directorio del servicio)

Cada test se escribió y se ejecutó antes que su código. Las líneas `E` son
las del fallo, sin otra edición que cortar las líneas largas.

```
T1 $ .venv/Scripts/python -m pytest tests/test_f044_vinculo.py -k "r2 or r3 or r4" -q          (api)
E   ImportError: cannot import name 'RecursoVinculado' from 'domain.models'      | 1 error in 0.65s
T2 $ .venv/Scripts/python -m pytest tests/test_f044_sync_vinculados.py -q                        (api)
E   ImportError: cannot import name 'AsignacionVinculadoORM' from 'infrastructure.db.orm_models'
T3 $ ... tests/test_f044_sync_vinculados.py -q -k "r1_el_step or r1_el_cliente or r3_preview_publica"
E   ImportError: cannot import name 'FetchVinculadosStep' from 'application.sync_pipeline'
E   TypeError: SigridApiClient.leer() takes 2 positional arguments but 3 were given
E   ImportError: cannot import name 'ConfigVinculados' from 'application.sync_pipeline' | 3 failed
T3 (deps) $ ... tests/test_f044_sync_vinculados.py -q -k contenedor_real
E   assert ("SELECT r.ide AS ide, x.valn AS principal_ide, ... WHERE RTRIM(x.cod) = ? ...", ['5']) in [...]
T4 $ .venv/Scripts/python -m pytest tests/test_f044_sql_vinculados.py -q                         (transfer)
E   AttributeError: 'SigridWriteClient' object has no attribute 'cuentas_del_presupuesto' (x4) | 4 failed
T5 $ .venv/Scripts/python -m pytest tests/test_f044_pipeline_vinculados.py -q
E   KeyError: 'vinculados'   (x10)                                              | 10 failed, 3 passed
T6 $ .venv/Scripts/python -m pytest tests/test_f044_cuadrante_vinculados.py -q                    (api)
E   AttributeError: 'PgAsignacionRepository' object has no attribute 'guardar_propuesta_vinculado'
E   TypeError: CambiarPartida.ejecutar() got an unexpected keyword argument 'vinculado_ide'
E   AttributeError: 'PartidaIn' object has no attribute 'vinculado_ide'          | 28 failed, 9 passed
T7 $ .venv/Scripts/python -m pytest tests/test_f044_vinculados_front.py -q                        (front)
E   AssertionError: assert '' == 'Persona'
E   AssertionError: no existe la función construirFilaVinculado en app.js       | 18 failed
T9 $ ... tests/test_f044_sql_vinculados.py -q --tb=line -k "r25 or r10 or r11"                    (transfer)
tests/test_f044_sql_vinculados.py:139: AssertionError: assert [] == [VinculadoEnt...  | 2 failed, 1 passed
T10 $ ... tests/test_f044_reglas_vinculados.py -q --tb=line -k "r12 or r13 or r14 or r18 or r19"
E   ImportError: cannot import name 'MOTIVO_SIGUE_AL_TRABAJADOR' from 'application.services.reglas_vinculados'
T11 $ ... tests/test_f044_reglas_vinculados.py -q --tb=line -k "r19 or r20 or r21 or r23"
E   TypeError: pisables_al_cero() got an unexpected keyword argument 'hora'
E   TypeError: emparejar_ceros() got an unexpected keyword argument 'clave'
E   TypeError: evaluar_capacidad() got an unexpected keyword argument 'es_jornada' | 3 failed, 5 passed
T12 $ ... tests/test_f044_sql_vinculados.py -q --tb=line -k r24
E   TypeError: SigridWriteClient.stmt_editar_linea() got an unexpected keyword argument 'hora' | 2 failed
T13 $ ... tests/test_f044_pipeline_vinculados.py -q --tb=line -k "r12 or r15 or r16 or r17 or r20 or r21 or r22 or r23 or r25 or r26"
E   AssertionError: assert [] == [(10, 'escrib...13, 'omitir')]
E   AssertionError: assert set() == {(70001, '0678', 'titular')}
E   AssertionError: assert {'200|202607|5|80001': None} == {'200|202607|...od': 'TF-10'}} | 16 failed
T14 $ ... tests/test_f044_pipeline_vinculados.py -q --tb=line -k "r24 or r28 or r26 or r16 or r18"
E   IndexError: list index out of range
E   ValueError: not enough values to unpack (expected 2, got 1)                  | 11 failed, 5 passed
T15 $ .venv/Scripts/python -m pytest tests/test_f044_lote.py -q --tb=short
E   AssertionError: assert {'horas_de_re...del_parte': 1} == {}
E     {'horas_de_recursos': 1, 'lineas_del_parte': 1, 'lineas_registradas': 1}  | 2 failed, 5 passed
T16 $ ... tests/test_f044_sql_vinculados.py -q --tb=short -k respuesta
E   KeyError: 'vinculados'
E   AssertionError: assert ('vinculado' not in {'clave': '200|202607|5|80001', ...}) | 4 failed
T17 $ ... tests/test_f044_sql_vinculados.py -q --tb=short -k script
E   assert 'Líneas de vinculados (porcentajes:vin:): 1' in 'Obra pruebas: 0404 · PRUEBAS ...' | 2 failed, 1 passed
T18 $ .venv/Scripts/python -m pytest tests/test_f044_payload_traza.py -q --tb=line              (api)
E   TypeError: RegistroSigrid.__init__() got an unexpected keyword argument 'vinculados_desde'  (x7)
E   assert [1, 2, 1, 2] == [1, 2]      (el omitido del vinculado tocaba al titular)
E   assert set() == {(1, 10), (1,... 12), (2, 10)}                               | 13 failed, 2 passed
T19 $ .venv/Scripts/python -m pytest tests/test_f044_vinculados_front.py -q --tb=line -k r31      (front)
E   assert 2 == 4
E   assert 'OTEL de TF TF-10 de GONZALEZ PANIAGUA' in '<div class="conflicto">...'
E   assert 'vinculado_ide' in 'async function registroEjecutar() {...'             | 7 failed, 2 passed
```

Verde tras cada tarea (fichero de la tarea y suite del servicio): transfer 1527 (T13), 1540, 1547, 1551, 1554 (T17); api 1289 (T18); front 403 (T19).

T8 y T20 no tienen RED. T8 cierra el bloque. T20 solo amplía ANCLAS: el
ancla no existía, así que su test `r1` fallaba antes de escribir la regla.

## Qué quedó fuera y qué falta

- **T21 (MANUAL, humano)**: el guion de `tasks.md` T21, en modo pruebas.
  - **Primer paso**:
    `.venv/Scripts/python -c "from config.settings import get_settings as g; s=g(); print(s.obra_pruebas_forzar, s.obra_pruebas_cod)"`
    tiene que dar `True 0404`; si no, PARAR.
  - Los comandos `prueba_escritura_porcentajes.py estado --ano 2026 --mes 11`,
    `limpiar` y `limpiar --confirmar` están **ensayados en seco**: el
    `argparse` real los acepta, sustituyendo `get_settings` para no leer
    ajustes ni Sigrid.
  - El resultado va en `progress/manual_F-044.md`.
- **T23 (líder, al desplegar)**:
  - orden **transfer → api → front**;
  - `azure-apps/dedicacion.md` desde `docs/INTEGRACION.md`;
  - el **aviso a `partes`** de design §10, que transmite el humano.
- Fuera por spec: mensajería (F-052), traer % de Sigrid (F-054), deshacer en
  Sigrid (F-033), Excel con vinculados (D14) y tocar `partes`.
- **Los 7 equivalentes de la mutación, ACEPTADOS por el humano el 2026-10-26** («1 ok»;
  rigor crítico); el análisis está en `progress/mutacion_F-044.md`.

## Evidencias (medidas el 2026-10-26)

| Evidencia | Valor real |
|---|---|
| Tests (`init.sh`, T24) | harness 418 + 1 skip (74,7 s) · api **1308** (97,7 s) · front **403** (63,7 s) · transfer **1585** (45,8 s); todo verde |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 99.3% de 1108 líneas cambiadas cubiertas (1100/1108, umbral 80%, nivel critico)` |
| Mutación, 1.ª pasada (`bd38dc5`) | 422 generados · 341 muertos · **81 supervivientes** · 0 timeouts (3355 s) |
| Mutación, final (`38a53d0`, 4 workers) | 422 · 415 muertos · **7 supervivientes, todos equivalentes** · 0 timeouts · 0 sin veredicto (3350,8 s) |

**T22, los 81 de la primera pasada: 74 eran huecos reales y ya tienen test.**

- **Tests nuevos**: `tests/test_f044_mutacion.py` de la api (19) y del
  transfer (29). Cada uno nombra el fichero y la línea que caza.
- **Comprobación**: cada mutante, aplicado en el worktree con solo ese
  fichero de tests, cae; `git checkout` lo deshace. El anexo está en
  `progress/mutacion_F-044_pasada1.md`.
- **Qué cubren**:
  - api: cola y `estado` de subfilas, `desde` AAAA-MM, `frozen`, DDL de las
    dos tablas, subconsulta de la traza, `solo_si_vacia` y `gt=0`;
  - transfer, `EscrituraVinculados`: partida, cuenta y `tex` de la edición;
    parte y `pos` de la inserción; solo los pisados confirmados y suyos;
    línea que ya no vale; relectura de lo editado y de lo puesto a 0;
  - preflight: validar solo con titular vivo; titular sin partida; elegida
    en postventa; propuesta guardada; `hmores_ide`; contexto del pisado;
    cero de un omitido; redondeo de la sobrecarga; aviso de la línea al 0 %;
  - alta del parte desde un vinculado.

**Los 7 equivalentes:**

- tres `strict` de `zip` sobre listas iguales por construcción
  (`repositories.py:533`, `registro_pipeline.py:274`,
  `registro_vinculados.py:223`);
- `registro_pipeline.py:761`: `vin_escribir` no vacío implica `escribir` no
  vacío;
- `registro_vinculados.py:188` y `:252`: `elegida_valida` no se lee con
  `elegida=None`;
- `:604`: `existe` ⇔ `ide` en `ParteDestino`.

**`bash harness/init.sh` (T24)**, con `.arnes_cache/suite_*.ok` borrados
antes: ningún `[KO]`.

- `PUERTA TAMAÑO` y `ENTORNO LISTO. Puedes trabajar.`
- Único aviso: `ruff: 307 avisos (deuda previa)`. Los ficheros de F-044 no
  añaden ninguno respecto de `dev`.
