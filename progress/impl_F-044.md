<!-- progress/impl_F-044.md -->
# F-044 · informe del implementer (PARCIAL: bloqueado antes de T7)

Rama `feature/F-044-recursos-vinculados`, worktree `porcentajes-f044`.
Estado: **T1-T6 hechas** (bloque 1 salvo el front), **parada obligatoria
antes de T7** (tasks.md: «antes de T7 el implementer lista los tests del
front que aseveran las columnas o el `colspan` del cuadrante y PARA»), y con
dos preguntas más que han salido por el camino. Feature en `blocked`.
Ninguna escritura en Sigrid, ni real ni de pruebas.

## Qué cambió (por tarea; commit de cada una)

| T | Commit | Qué |
|---|---|---|
| T1 | `bb059a7` | api `domain/vinculados.py`: `vincular` (campo = trabajador → vinculado; vacío, hacia un no trabajador o tipo excluido, aparte) y `RecursoVinculado` |
| T2 | `8b3f6a2` | api ORM `recurso_vinculado` y `asignacion_vinculado` (único `asignacion_id`+`vinculado_ide`, `ON DELETE CASCADE`); `PgVinculadoRepository.sincronizar` (nunca borra), `upsert_asignacion_vinculado` |
| T3 | `8a57ec6` | api `sync.vinculados` en `config.yaml` (campo `5`, `desde: 2026-10`, `tipos_excluidos: [VP]`, SQL de §7.1 con `dbo.` y `?`); `FetchVinculadosStep`/`UpsertVinculadosStep`; bloque `vinculados` del preview; `SigridGateway.leer(sql, parametros)`. **Sin cablear en `deps.py`** (ver P2) |
| T4 | `9285ee6` | transfer `VinculadoEntrada`, `LineaEntrada.vinculados`; `reglas_vinculados.py` (`partida_ci_del_tipo`, `partida_del_vinculado`); `cuentas_del_presupuesto` |
| T5 | `ff989ba` | transfer `PasoVinculados.proponer` (`registro_vinculados.py`) en `partidas/propuesta` y `propuesta-lote`; salida `vinculados` solo si la petición los trae |
| T6 | `eb3ceb1` | api: subfilas en el cuadrante, partida y propuesta de subfila (detalle abajo) |

Ficheros de producción tocados (api): `domain/models.py`, `domain/ports.py`,
`domain/vinculados.py` (nuevo), `infrastructure/db/orm_models.py`,
`infrastructure/db/repositories.py`, `infrastructure/sigrid/sigrid_client.py`,
`application/sync_pipeline.py`, `application/use_cases.py`,
`application/partidas_linea.py`, `application/propuestas_mes.py`,
`application/registro_sigrid.py`, `interface_adapters/api/routes.py`,
`interface_adapters/api/schemas.py`, `config/config.yaml`. Transfer:
`domain/models/registro_models.py`, `application/services/reglas_vinculados.py`
(nuevo), `application/pipelines/registro_vinculados.py` (nuevo),
`registro_pipeline.py`, `registro_lote.py`, `application/services/lecturas_lote.py`,
`infrastructure/sigrid/sigrid_write_client.py`, `interface_adapters/api/app.py`.
Front: nada todavía. Tests nuevos: `test_f044_vinculo.py`,
`test_f044_sync_vinculados.py`, `test_f044_cuadrante_vinculados.py` (api);
`test_f044_reglas_vinculados.py`, `test_f044_sql_vinculados.py`,
`test_f044_pipeline_vinculados.py` (transfer). **Ningún test anterior tocado.**

## Decisiones de diseño (y desviaciones, justificadas)

1. **Desviación (T2)**: las columnas `empresa`/`fecha_baja` de
   `recurso_vinculado` (design §7.2) se llaman `empresa_recurso` y
   `fecha_baja_recurso`. Motivo: `test_f023_r1_empresa_solo_en_trabajador_y_obra`
   y `test_f026_r8_fecha_baja_solo_en_trabajador` aseveran que ninguna otra
   tabla tiene esas columnas y no están en la lista cerrada (P3).
2. **T3 sin cablear en `deps.py`**: cableado, rompe 11 tests ajenos (P2). El
   código y sus tests están; el sync real todavía NO trae vinculados.
3. «Partida `CI*`» del titular = el código empieza por `CI` (no
   `clasifica_categoria`, que da `OTRO` a `CICO13`).
4. Titular con elegida que no es hoja activa ⇒ sus subfilas sin propuesta
   (en el preflight se omitiría con él).
5. T6 · dominio: `SubfilaVinculado`; `Linea.vinculados` va tras
   `partida_fija` porque `test_f055_r13` fija que los 5 últimos campos de
   `Linea` son los `propuesta_*`. `TipoEvento.PARTIDA_VINCULADO`.
6. T6 · lectura: `lineas_de_trabajador`/`lineas_del_periodo` leen los
   vinculados ACTIVOS de los trabajadores de esas líneas, vigentes en el mes
   (`vigente_en` con su `fecha_baja_recurso`, R4), y sus filas de
   `asignacion_vinculado`. Dos lecturas más en total; ninguna si no hay
   vinculados o las asignaciones no traen `id`.
7. T6 · escritura: `reemplazar` vuelve a insertar, tras el flush, las
   subfilas con elegida o propuesta (fila solo cuando hay algo, §7.2). La
   traza `sigrid_*` de la subfila, como la del titular, no sobrevive a
   guardar la fila.
8. T6 · R8: `CambiarPartida(vinculado_ide=…)`; vinculado ajeno a la línea ⇒
   `LineaNoEncontrada` (404); línea VAR ⇒ `ObraNoValida` («fija»). El
   snapshot de los eventos gana `vinculados` (solo las elegidas, y solo si
   hay alguna: los eventos de hoy no cambian de forma); deshacer, guardar la
   fila (`_conservar_partidas`) y copiar el mes (`_sin_propuesta`: copia la
   elegida, no la propuesta) las incluyen.
9. T6 · R9: cambiar la partida del TITULAR borra la propuesta guardada de sus
   subfilas (se calcula con la del titular) y conserva su elegida.
10. T6 · selector: con `vinculado_ide`, la línea va al transfer con `paride`
    (elegida del titular) y ese vinculado (`peticion_de_subfilas`, contrato
    de T5); la propuesta `ci_tipo`/`titular` se guarda si no hay elegida;
    `ambito` = mayor de la elegida o de la propuesta, si no «CI» (normal) o
    «Todas» (postventa). Sin `vinculado_ide`, la ruta de F-050 intacta (el
    parámetro ni se pasa).
11. T6 · preflight: `_guardar_propuestas` guarda también las de subfila desde
    `r["vinculados"]` con la forma `{registro_id, recurso_ide, paride,
    partida_cod, partida_res, partida_metodo, partida_origen}`.
    **Compromiso para T13**: el transfer debe devolver esa forma.
12. T6 · cola del mes: cola y memoria «sin propuesta» APARTE para subfilas
    (también bajo líneas de postventa, que el titular no encola);
    `pendientes()` sigue siendo de líneas (F-057 intacto); `en_curso` cuenta
    las dos, de una sola foto de la cola (`_foto`). `estado` gana `subfilas`
    solo si hay alguna.
13. T6 · salida: `SubfilaOut` (sin %, R7; `partida_fija` = la de la línea);
    `LineaOut.vinculados` con `exclude_if` vacío, así la línea sin vinculados
    es la de siempre (`CAMPOS_LINEA` de `test_f034_rutas` intacto). Las
    subfilas se muestran sin la puerta `desde`: `desde` solo gobierna el
    registro (R10, T18).

## Fase RED (trazas reales)

```
## T1  $ (services/dedicacion-api) .venv/Scripts/python -m pytest tests/test_f044_vinculo.py -k "r2 or r3 or r4" -q
E   ImportError: cannot import name 'RecursoVinculado' from 'domain.models'
1 error in 0.65s
## T2  $ cd services/dedicacion-api && .venv/Scripts/python -m pytest tests/test_f044_sync_vinculados.py -q
E   ImportError: cannot import name 'AsignacionVinculadoORM' from 'infrastructure.db.orm_models'
1 error in 2.19s
## T3  $ cd services/dedicacion-api && .venv/Scripts/python -m pytest tests/test_f044_sync_vinculados.py -q -k "r1 or r3 or r5"
26 failed, 21 passed in 4.89s   (los 21 que pasan son los de T2)
$ ... -k "r1_el_step or r1_el_cliente or r3_preview_publica"
E       ImportError: cannot import name 'FetchVinculadosStep' from 'application.sync_pipeline'
E       TypeError: SigridApiClient.leer() takes 2 positional arguments but 3 were given
E       ImportError: cannot import name 'ConfigVinculados' from 'application.sync_pipeline'
3 failed, 44 deselected in 3.12s
## T4  $ cd services/dedicacion-transfer && .venv/Scripts/python -m pytest tests/test_f044_reglas_vinculados.py tests/test_f044_sql_vinculados.py -q
E   ModuleNotFoundError: No module named 'application.services.reglas_vinculados'
1 error in 1.14s
$ .venv/Scripts/python -m pytest tests/test_f044_sql_vinculados.py -q
E       AttributeError: 'SigridWriteClient' object has no attribute 'cuentas_del_presupuesto'   (x4)
4 failed in 0.82s
## T5  $ cd services/dedicacion-transfer && .venv/Scripts/python -m pytest tests/test_f044_pipeline_vinculados.py -q
E       KeyError: 'vinculados'   (x10)
10 failed, 3 passed in 3.14s   (los 3 que pasan: sin vinculados, la respuesta de hoy)
(rutas, tras el pipeline) $ .venv/Scripts/python -m pytest tests/test_f044_pipeline_vinculados.py -q
E       KeyError: 'vinculados'
E       AssertionError: ... At index 1 diff: [{'clave': 'a', ..., 'es_postventa': False}] != [{..., 'paride': 80001, 'vinculados': [...]}]
3 failed, 13 passed in 3.03s
## T6 (con el dominio ya en su sitio: SubfilaVinculado, Linea.vinculados)
$ cd services/dedicacion-api && .venv/Scripts/python -m pytest tests/test_f044_cuadrante_vinculados.py -q
E           AssertionError: assert [] == [(11, 'CO', '...VE', 'VE-13')]
E       ValueError: not enough values to unpack (expected 1, got 0)
E       assert [] == [10]
E       AssertionError: assert [] == [(500, 10, No..., None, None)]
E       AttributeError: 'PgAsignacionRepository' object has no attribute 'guardar_propuesta_vinculado'
E       TypeError: CambiarPartida.ejecutar() got an unexpected keyword argument 'vinculado_ide'
E       assert [] == [(100, 10, 81002, 81001)]
E       AssertionError: assert () == (SubfilaVincu...es_ide=None),)
E       AssertionError: assert {'cod', 'desc...empresa', ...} == {'cod', 'desc...empresa', ...}
E                   AttributeError: 'PartidaIn' object has no attribute 'vinculado_ide'
28 failed, 9 passed, 1 warning in 9.01s   (los 9: sin vinculados, la línea de hoy)
```

Verde tras cada tarea: el fichero de la tarea y la suite entera del
servicio. T6: `pytest tests/test_f044_cuadrante_vinculados.py` → 40 passed
(37 de la RED + 3 de rutas añadidos en verde, que comprueban que el
`vinculado_ide` llega a los casos de uso y la subfila sale en el JSON).

## Por qué paro (las tres preguntas están en `progress/current.md`)

- **P1 · T7 (parada prevista en tasks.md).** Tests del front que aseveran
  las columnas del cuadrante (ninguno asevera `colspan`):
  - `test_f050_subfilas.py`: literal de `ORDEN_COLUMNAS_DEFECTO` (l. 65-66)
    y de `COLUMNAS_POR_LINEA = ["asignaciones", "partida"]` (l. 109-110):
    **rompen seguro** al añadir «Tipo recurso».
  - `test_f050_m2_arreglos.py::test_f050_m2_1_cada_columna_tiene_su_minimo`
    (claves exactas de `COLUMNAS`/`MINIMO_COLUMNA`, 5 columnas) y su
    `PREFERIDOS`: **rompe seguro**.
  - `test_f050_t15f_total.py` (`ORDEN` de 5 columnas, reparto de anchos),
    `test_f050_t15d_sombreado.py` y `test_f050_t15e_sombreado.py`
    (evalúan `construirFila` con `COLUMNAS_POR_LINEA`/
    `ORDEN_COLUMNAS_DEFECTO`), `test_f030_tabla_incidencias.py` (l. 327,
    `COLUMNAS_POR_LINEA`) y `test_f041_filtro_obra.py` (l. 115, una lista de
    columnas de entrada): **pueden** romper según cómo entre la columna.
  - `test_f062_modal_rachas.py` asevera `<th>` de los modales, no del
    cuadrante: no afectado.
- **P2 · cablear T3 en `deps.py`** rompe 11 tests ajenos que construyen el
  contenedor real con un Sigrid falso sin `parametros` y una UoW sin
  `vinculados`: `test_f023_sync_empresa.py` ×5 (`r18_*`),
  `test_f025_sync_postventa.py::test_f025_r12_el_contenedor_comparte_un_solo_transfer`,
  `test_f030_catalogo.py::test_f030_r3_el_sync_y_el_preview_reales_usan_la_consulta_de_config`,
  `test_f032_empresas_sigrid.py` ×2 (`r1_el_sync_real…`, `r4_el_preview_real…`),
  `test_f039_sync_var.py` ×2 (`r10_el_contenedor_pasa_el_numero…`).
- **P3 · nombres de columna** (decisión 1): ¿se quedan `empresa_recurso`/
  `fecha_baja_recurso`, o se añaden `test_f023_r1…` y `test_f026_r8…` a la
  lista cerrada para usar los nombres del design?

## Qué falta

- T7 (front) en adelante: T7-T8 del bloque 1, T9-T19 (registro), T20
  (documentación), T21 MANUAL, T22 (mutación), T23 (despliegue, líder,
  `azure-apps/dedicacion.md` desde `docs/INTEGRACION.md`), T24.
- El cableado de `deps.py` (P2).
- `azure-apps/dedicacion.md`: lo expuesto ya cambió en la rama (rutas de
  partida con `vinculado_ide`, `LineaOut.vinculados`, `estado.subfilas`,
  contrato `vinculados` api ↔ transfer) pero **nada está desplegado**; el
  plan (T20 → `docs/INTEGRACION.md`, T23 → `azure-apps`) se mantiene.

## Verificaciones MANUAL pendientes

- **T21** (R33), en modo pruebas con Administración: aún no preparada (su
  comando exacto y el ensayo en seco se escriben cuando existan T13-T17). Su
  primer paso será comprobar el modo con el `.venv` del transfer:
  `.venv/Scripts/python -c "from config.settings import get_settings as g; s=g(); print(s.obra_pruebas_forzar, s.obra_pruebas_cod)"`
  → debe dar `True 0404`; si no, PARAR. La ejecuta el humano, no el agente.

## Evidencias (medidas el 2026-10-26, HEAD `eb3ceb1` + este informe)

| Evidencia | Valor |
|---|---|
| Tests ejecutados (`bash harness/init.sh`) | raíz 418 passed + 1 skipped; api **1273** passed; front **376** passed; transfer **1478** passed; 0 fallos |
| Tests nuevos de F-044 | api 40 (T6) + los de T1-T3; transfer los de T4-T5; ver ficheros arriba |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 99.3% de 582 líneas cambiadas cubiertas (578/582, umbral 80%, nivel critico)` |
| Mutantes generados / supervivientes | **No lanzada**: la feature está a medias (bloque 1 sin front, bloque 2 sin empezar); la campaña completa es T22, al terminar. No es `PENDIENTE` de análisis: no hay campaña que analizar |
| Tiempo de la suite | api 98.9 s, front 52.3 s, transfer 32.3 s, raíz 55.1 s (con cobertura, dentro de `init.sh`) |
| `bash harness/init.sh` | `ENTORNO LISTO. Puedes trabajar.` sin `[KO]`; avisos: F-044 `blocked` (esperado), `BACKLOG.md` regenerado (va en el commit), ruff 277 avisos de deuda previa (ninguno nuevo en las líneas tocadas: diff de ruff antes/después vacío en los ficheros de T6) |
