<!-- progress/impl_F-074.md -->
# F-074 · Informe del implementer (`critico`)

Bloqueada el 2026-11-23 (72 tests fuera de la lista cerrada). El humano aprobó la enmienda el 2026-11-24 (`444f0a1`). Terminada el mismo día y lista para review.

## Hecho

- **Al registrar no se busca partida.** Se usa la **definida**: la elegida, la fija VAR o la propuesta guardada (en postventa, la de su obra, guardada en el sync).
  - Se valida **por `ide`** en una sola lectura, que ahora incluye la postventa.
  - Si no vale, se omite nombrándola (`partida_no_valida`) y la api borra la guardada, solo si sigue sin elegida.
  - Sin definida, va a «sin partida» (Regla C). En postventa se omite con motivo.
  - El preflight ya no lee presupuestos, historial ni cuentas, tampoco en el lote; `partidas_obra` y `partidas_postventa` salen `[]`.
- **La regla solo corre en segundo plano**: la cola, el selector y el universo del sync. `partidas/propuesta(-lote)` devuelve `motivos` y `motivos_vinculados`, y el universo devuelve `motivos`.
- **Api.** La obra guarda su partida de postventa o su motivo. La cola recuerda el motivo de lo que no encuentra partida (línea y subfila), y cuadrante y rutas publican las marcas. Al cambiar la partida del titular, sus subfilas salen de esa memoria.
- **Front.** La celda nunca dice «automática». Enseña, en este orden: la elegida o la fija; la propuesta con su método; «buscando partida…»; «no encuentra partida» con el motivo en el título; «sin calcular»; «—». El filtro «Partida» y el buscador casan con ese texto. El selector y el modal siguen R21 y R22.

## Tareas y commits (rama `feature/F-074-partida-sin-automatica`)

| Tareas | Commit | Qué |
|---|---|---|
| T1-T4 | `8d2c186` | transfer: preflight con la definida, `partida_definida.py`, lote sin lecturas de la regla, `motivos` |
| T5-T9 | `e0893b8` | api: postventa del sync, `estado_partida.py`, marcas, `olvidar_subfilas`, `_borrar_no_validas` |
| T13 | `bfa4883` | docs: `ARCHITECTURE.md` (las cuatro reglas) e `INTEGRACION.md` §5 |
| T10-T12 | `e06dd07` | front: `htmlPartida`, marcas, filtro, selector y modal |
| T14, T19 | (cierre) | este informe, `tasks.md`, `features.json`, `current.md` |

Las tareas se agrupan por servicio porque el código de T1-T12 llegó al árbol antes del bloqueo y comparte ficheros entre tareas. Cada grupo va en verde con su suite completa.

## Ficheros

- **transfer**: `application/services/partida_definida.py` (nuevo), `registro_pipeline.py`, `registro_vinculados.py`, `registro_lote.py`, `lecturas_lote.py`, `universo_postventa.py`, `domain/models/registro_models.py`.
- **api**: `application/estado_partida.py` (nuevo), `propuestas_mes.py`, `registro_sigrid.py`, `use_cases.py`, `filtros_maestros.py`, `sync_pipeline.py`, `domain/models.py`, `orm_models.py`, `repositories.py`, `transfer_client.py`, `schemas.py`, `routes.py`.
- **front**: `static/js/app.js`, `static/css/styles.css` (`.partida-sin`).
- **Tests nuevos**:
  - transfer: `test_f074_preflight_definida.py`, `test_f074_motivos.py` (60);
  - api: `test_f074_postventa.py`, `_estados`, `_memoria_subfilas`, `_no_valida_api` (51);
  - front: `test_f074_celda.py`, `test_f074_selector_modal.py` (38).

## Tests anteriores cambiados (T14), cada uno con su criterio de §6

Todos se anotaron aquí antes de tocarlos.

**La regla del «cómo».** Un test que prueba otra cosa y solo cae en (i) porque su línea no trae partida recibe una **definida** y conserva sus aserciones. La definida es `linea_definida` / `DEFINIDA_*` de `conftest.py`: lo que casaba el preflight, es decir CI.1.10, o la 0678 en postventa.

**Transfer: solo se cambia el fixture** (i, «cómo»):
- `conftest.py` (helper nuevo), `test_f051_pipeline_cero`, `test_f002_capacidad`;
- `test_f030_pipeline_incidencias`, `test_f030_r30_editar`, `test_f062_pipeline_rachas`, `test_f037_pipeline`;
- `test_f002_pipeline` (r32: la del jefe, CI.1.20);
- `test_f022_obra_por_empresa` (su doble valida contra la obra de la empresa 28), `test_pipeline_offline`;
- `test_f026_recurso_dado`, `test_f054_obra_cero`, `test_f044_sql_vinculados`;
- `test_f044_pipeline_vinculados` (los vinculados con su `ci_tipo` guardada) y `test_f044_mutacion`.

**Transfer: cambian de expectativa o se retiran:**
- `test_f022_obra_por_empresa` r18 app (i): `capitulo_postventa` es None, sin postventa escrita.
- `test_f044_mutacion` r15 (i): la guardada `titular` no cuenta, así que queda sin partida.
- `test_f044_pipeline_vinculados` r29 (vi): lote = suelto, con los `motivos*`. r12 (ii): ninguna lectura de cuentas.
- `test_f044_lote` r27 (ii): ninguna lectura de cuentas.
- `test_f002_postventa`: r15 (i, «cómo»); los dos r17 (iii) pasan a uno parametrizado que espera `partidas_postventa == []`.
- `test_f013_sin_partida`: la premisa, r2 y «pv que casa» (i, «cómo»). En «pv sin partida» (i), el motivo pasa a ser `MOTIVO_PV_SIN_DEFINIDA`.
- `test_f047_tope_filas` a2 y a3 (i, ii): el presupuesto grande se comprueba ahora sobre `proponer` (segundo plano).
- `test_f049_partidas_obra`: «manual y automática» (i, ii): sin partida y sin lecturas. «solo postventa» (i, «cómo»).
- `test_f025_casado_p5` r11 (i): el «no casa» lo da el universo y el preflight omite con su motivo.
- `test_f025_universo_postventa`: r8 (iii): `[]`. r2 (i): el preflight escribe la partida del universo que llega definida. r1 ruta (v): con `motivos`.
- `test_f050_pipeline` (i, ii, iii):
  - r9 pasa a «ya no se propone» y «la guardada se escribe tal cual»;
  - r7 «si la lectura falla»: se escribe la guardada;
  - r9 ejecutar, modo pruebas y r21: con la guardada; r10: sin catálogos;
  - **se retiran dos**: r7 «una sola lectura con los recursos automáticos» y r7 «la ventana del ajuste». En el preflight ya no hay lectura; la ventana se sigue probando en los tests de la propuesta.
- `test_f050_endpoint_propuesta` r9 y `test_f055_orden_propuesta` r38 (i): el preflight recibe la propuesta del selector como guardada y escribe esa.
- `test_f055_pipeline_partidas`: r3 (vii, ii); r6 (i): la que no vale se omite nombrándola; r7 (i, ii); r9 (i, «cómo»); r10 (ii, iii).
- `test_f055_lecturas_lote`: r20 pendientes y postventa (ii); r22 (ii); r20 validación (vii).
- `test_f055_medicion` r2 (ii): sin lectura de historial.
- `test_f055_propuesta_lote` r34 (vi) y el plugin `f055_equivalencia_lote.py` (vi): con `motivos*`.
- `test_f068_pipeline` (i, ii):
  - el preflight escribe la guardada de cada subfila (`_v68_guardadas`), sin leer historial ni cuentas, también en el lote, ni falla si el historial falla;
  - r16 «se recalcula» pasa a «no cuenta» (`titular`, `manual`, sin método) o a «no vale» (se omite);
  - r15 selector = preflight: pasa la del selector como guardada;
  - **se retiran** r7 (CI.4), r18 (nombre), r2/D3 (ventana), r11 (obra de origen) y r12 (cuentas) del preflight. Siguen en los tests del selector.

**Api:**
- `test_f025_sync_postventa` r15 (v): con `partidas`.
- `test_f055_registro_lote` r14 (i): no se guarda nada. **Se retira** «solo si sigue sin elegida» (i): esa guarda se prueba ahora en `test_f074_no_valida_api.py`.
- `test_f044_cuadrante_vinculados` r9 y `test_f068_api` r17 (i): lo que vuelve del preflight no se guarda.
- `test_f055_propuesta_guardada` queda **intacto**: los campos `obra_pv_*` de `Linea` van antes de los `propuesta_*`.

**Front (iv):**
- `test_f050_subfilas` r24 y r28: la rama «automática» pasa a `htmlPartida` y «automatica» ya no casa.
- `test_f055_propuesta_celda`: r27 «—»; `construirCelda` delega en `htmlPartida`; r36: el arnés carga además `aplicarNoEncontradas` y `aplicarMarcasSubfilas`.
- `test_f057_buscando_pendientes` r1: «—».
- `test_f067_ver_vinculados` r3: «automatica» ya no casa con nadie, y su arnés carga `rotuloOrigen`.

## Vuelta de la review, pasada 1 (CHANGES_REQUESTED, `17514ee`)

Corrección en el commit `7b2df8b`; pasada 2 incremental desde `7f6ddc8`.
- **H1**: las cabeceras de módulo de `registro_pipeline.py` (pasos 1 y 4), `registro_vinculados.py` y `lecturas_lote.py` dicen ahora que el preflight usa la definida, sin leer presupuestos, historial ni cuentas, y que `proponer` solo corre en segundo plano.
- **H3**: `ARCHITECTURE.md` l. 108, 769 y 1220, «automática» pasa a «sin elegida».
- **H6**: arriba, las cuatro secciones de `azure-apps` (§2, §4, §5, §7).
- **H4**: tests renombrados, sin tocar sus aserciones:

| Antes | Ahora | Criterio §6 |
|---|---|---|
| `test_f055_pipeline_partidas::test_f055_r6_propuesta_que_no_vale_se_recalcula` | `test_f055_r6_propuesta_que_no_vale_se_omite_nombrandola` | (i) |
| `test_f068_pipeline::test_f068_r13_si_el_historial_falla_el_preflight_falla` | `test_f068_r13_el_preflight_no_lee_el_historial_aunque_falle` | (ii) |
| `test_f068_pipeline::test_f068_r16_la_que_no_vale_o_de_titular_se_recalcula` | `test_f068_r16_la_que_no_vale_se_omite_y_la_de_titular_no_cuenta` | (i) |

`bash harness/init.sh` tras la corrección (2026-11-24): `exit 0`, **0 `[KO]`**, «ENTORNO LISTO». Raíz 2319 passed / 47 skipped (782 s); transfer 2009 passed (42,0 s); api y front en verde por caché (sin cambios desde su verde de las 11:22 y 11:24). `PUERTA COBERTURA` 100,0 % (310/310) y `PUERTA TAMAÑO` impl 203/220 · `CARRIL` y `CAPA E2E` N/A.

## Fase RED (tests nuevos contra el código de `9fb1092`)

Desde la carpeta de cada servicio, con su `.venv`:

```
services/dedicacion-transfer$ .venv/Scripts/python -m pytest tests/test_f074_preflight_definida.py tests/test_f074_motivos.py -q -p no:cacheprovider -rf
41 failed, 19 passed, 1 warning in 4.08s
E  AssertionError: assert ('escribir', ...terior', None) == ('escribir', ...confirmación')
E    At index 1 diff: 80003 != 0          # R1: hoy el preflight propone CI.1.9 (parte anterior)
E  AttributeError: 'AccionLinea' object has no attribute 'partida_no_valida'   # R4
E  assert [[80001, 80002]] == [[70001, 80001, 80002]]                         # R3: postventa fuera de la validación
E  AssertionError: assert not ({'capitulos_de_obra', 'cuentas_del_presupuesto', 'historial_de_vinculados', 'historial_partidas'} & {...})   # C1
E  KeyError: 'motivos'                                                       # R9, R10
```

```
services/dedicacion-api$ .venv/Scripts/python -m pytest tests/test_f074_postventa.py tests/test_f074_estados.py tests/test_f074_memoria_subfilas.py tests/test_f074_no_valida_api.py -q -p no:cacheprovider -rf
41 failed, 10 passed, 1 warning in 9.53s
E  TypeError: ResultadoUniverso.__init__() got an unexpected keyword argument 'partidas'   # R11
E  KeyError: 'postventa_partida_ide'                                                       # R11
E  AttributeError: 'PropuestasDelMes' object has no attribute 'encolar_marcas'             # R13, R14
E  TypeError: CambiarPartida() takes no arguments                                          # R15
E  AttributeError: 'RegistroSigrid' object has no attribute '_borrar_no_validas'           # R16
```

```
services/dedicacion-front$ .venv/Scripts/python -m pytest tests/test_f074_celda.py tests/test_f074_selector_modal.py -q -p no:cacheprovider
30 failed, 8 passed in 13.25s
E  - <span class="partida-sin" title="ningún paso de la regla da partida">no encuentra partida</span>
E  + <span class="partida-auto">automática</span>                                       # R17, R18
```

Los dos módulos nuevos, `partida_definida.py` y `estado_partida.py`, ya estaban en el árbol durante el RED. Por eso sus unit tests pasan ahí. El resto de los «passed» son controles.

Algunos tests de api y front que se corrigieron después del RED no fallaban por la regla, sino por su propio montaje: dobles de `Trabajador` sin `cod`/`dni`, `BASE` sin `/v1`, `_Universo` sin `universo_var` y `rotuloOrigen` ausente del arnés. El test de ruta de R15 se rehízo con un espía de `CambiarPartida`, porque el de antes no ejercía nada.

## Suites completas (2026-11-24, antes de `init.sh`)

| Servicio | Resultado | Tiempo | Ruff F |
|---|---|---|---|
| transfer | 2009 passed | 29,3 s | limpio |
| api | 1689 passed + 1 que falló y luego pasó en su fichero | 84,9 s | limpio en lo tocado |
| front | 611 passed | 358 s | limpio |

En la api, ruff F señala 9 avisos en ficheros que esta rama no toca (`traer_sigrid.py`, `use_cases.py:173`, `test_f029`, `test_f069`): son anteriores, no se tocan.

## Salida de `bash harness/init.sh`

`bash harness/init.sh` (2026-11-24, tras el reinicio del equipo; `exit 0`, **0 `[KO]`**, «ENTORNO LISTO»):
- raíz 2319 passed / 47 skipped (1109 s) · api 1690 passed (99,4 s) · front 611 passed (104,5 s) · transfer 2009 passed (27,6 s).
- `PUERTA COBERTURA: 100.0% de 310 líneas cambiadas cubiertas (310/310, umbral 90% (del nivel critico)…)`.
- `PUERTA TAMAÑO: F-074 dentro de los topes (requirements 143/150, design 217/250, impl 180/220)` · `PUERTA CARRIL: N/A` · `CAPA E2E: N/A (ningún servicio declara el bloque e2e)`.

## Desviaciones (para el reviewer)

- **`motivo_sin_propuesta`** vive en `partida_definida.py`, y P5 usa un `ReglasPorcentajes` por línea de postventa. El líder prohibió tocar `propuesta_partida.py` y `reglas_porcentajes.py`.
- **`routes.py`** lee `encolar_marcas` y `olvidar_subfilas` con `getattr` (sin ellos, se comporta como antes). Los dobles de `test_f024_rutas_empresa.py`, fuera de la lista, no los tienen.
- **`repositories.py`** (`_a_obra`, `_a_linea`) lee las columnas nuevas con `getattr`. Los dobles `SimpleNamespace` de tests fuera de la lista no las traen.
- **Texto de la celda en dos sitios.** El texto vive en `htmlPartida` y en `textoCeldaPartida`, en línea dentro de `trabajadoresVisibles`. Unificarlo no es posible sin tocar arneses fuera de la lista: los arneses node de F-030, F-041 y F-063 cargan `trabajadoresVisibles` pero no `htmlPartida`, y cualquier función común de primer nivel les faltaría.
  - Lo ata `test_f074_celda.py::test_f074_r20_el_filtro_y_la_celda_dicen_lo_mismo`, estado a estado.
  - `textoCeldaPartida` llama a `rotuloOrigen` solo con una propuesta. Esos arneses pasan porque sus datos no la traen.
- **El «·» de la celda** no cuenta al filtrar (`sinPunto`, en filtro y buscador). Sin eso, F-050 R28 («ci.1.9 admin» casa con «CI.1.9 · ADMINISTRATIVO») se rompía, y ese test no está en ningún criterio. Lo cubre un caso nuevo en `test_f074_r20_casan_con_el_texto_de_la_celda`.
- **Campos `obra_pv_*` de `Linea`**: van antes de los `propuesta_*`, para no tocar el orden que fija F-055 R13.
- **Las líneas de postventa** nunca mandan una propuesta guardada, solo la de su obra.

## MANUAL pendiente (humano; nada contra Sigrid lo hace el agente)

- **T15 (M1, local, `OBRA_PRUEBAS_FORZAR=true`, periodo ABIERTO).**
  1. «Sincronizar Sigrid» y esperar a la cola.
  2. Ctrl+F `automática`: cero resultados. Ctrl+F `no encuentra partida`: aparece con su motivo.
  3. «⇪ Sigrid» de un trabajador con postventa y de otro con una línea sin partida: el modal escribe lo que enseña cada celda y lista la que no la tiene.
  4. **Cancelar**. Anotar en `progress/manual_F-074.md`.
- **T16 (M2, solo lectura).** Ejecutar `cd services/dedicacion-transfer` y después `python prueba_escritura_porcentajes.py medir --ano <A> --mes <M> --obra 0694 --obra 0696 --recurso <R> --lote`, en `dev` (antes) y en esta rama (después). Anotar lecturas y segundos en `progress/manual_F-074.md`.
- **T17 (M3, base `dedicacion` LOCAL, nunca Sigrid).**
  1. Ejecutar `psql -h localhost -d dedicacion -c "UPDATE asignacion SET propuesta_ide = 1 WHERE id = <ID>"` sobre una línea con propuesta.
  2. Lanzar el preflight: la línea sale omitida, nombrando la partida y con selector. **Cancelar**.
  3. Recargar: «buscando partida…» y después la nueva, o «no encuentra partida».
- **T18 (M4, producción).**
  1. Desplegar la api; «Sincronizar Sigrid»; desplegar el transfer y después el front. Este orden es obligatorio.
  2. Ctrl+F5. En el mes abierto: ninguna «automática», y las de postventa con su partida.
  3. Si se abre el modal: solo preflight y **Cancelar**.
- **`azure-apps/dedicacion.md`** (design §11): no se ha tocado, lo actualiza el líder en un commit aparte. Cambian cuatro secciones:
  - §2: las cuatro columnas `postventa_*` de `obra`;
  - §4: menos lecturas del preflight;
  - §5: el preflight sin propuesta y con `partida_no_valida`; `partidas/propuesta(-lote)` y `postventa/universo` con motivos; cuadrante, escrituras y `…/propuestas` con las claves y listas nuevas;
  - §7: la postventa sin sync no se registra; orden de despliegue api → sync → transfer → front.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados (`init.sh`) | raíz 2319 (+47 skipped) · transfer 2009 · api 1690 · front 611, todos en verde; nuevos de F-074: 60 + 51 + 38 = 149 |
| Cobertura de líneas cambiadas | 100,0 % (310/310 líneas cambiadas; umbral 90 %, nivel critico) |
| Mutación | `critico`, semilla 20261030, uno por línea, 100 de 133 candidatos (202 generados). Campaña 1 sobre `4aa8d7b`: 84 muertos, 16 supervivientes, 0 timeouts, 0 sin veredicto, 1321,7 s. Los 16, reproducidos EN SERIE (todos reales): 4 muertos con tests nuevos (`66d91e3` transfer, `532b994` api: `test_f074_mutacion*.py`, cada uno comprobado contra su mutante) y 12 equivalentes (veracidad sobre dataclasses siempre verdaderas, `ide` 0 imposible, valor inicial nunca leído), justificados uno a uno en `progress/mutacion_F-074.md`, **pendientes de la aceptación del humano**. Repetición `--incremental` sobre el HEAD `671ac43`: 25 reevaluados (16 + 9 de control) y 75 reutilizados, **88 muertos, 12 supervivientes (los 12 equivalentes)**, 0 timeouts, 0 sin veredicto, sin «CAMPAÑA NO VÁLIDA», 665,6 s |
| Tiempo de las suites (`init.sh`) | raíz 1109 s · transfer 27,6 s · api 99,4 s · front 104,5 s |
| Capa e2e | N/A (`CAPA E2E: N/A`, ningún servicio declara el bloque e2e) |
