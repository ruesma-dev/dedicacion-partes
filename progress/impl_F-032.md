<!-- progress/impl_F-032.md -->
# F-032 · Informe del implementer — Nombres de empresa sincronizados desde Sigrid

Rigor **estándar** (`features.json`), `sdd: false`: mini-spec = descripción y
`acceptance` de F-032 (R1-R7 en su orden). Rama
`feature/F-032-empresas-desde-sigrid`. Servicios: **api** (todo lo de negocio)
y **front** (solo pinta la marca «(de baja)» que decide la API). Transfer
intacto. Ninguna llamada a sigrid-api ni a Sigrid; ningún `.env`; no se lanzó
`POST /sync`.

## Qué cambió (tareas y commits)

| Tarea | Commit | Qué |
|---|---|---|
| T1 | `4e4f070` | `EmpresaORM` (tabla `empresa`, PK `numemp` sin autoincremento; `cod`, `nombre`, `fecbaj`, `desact`, `sync_en`). Regla pura `domain/empresas.py::empresa_de_baja(fecbaj, desact)` = `fecbaj > 0 o desact == 1` |
| T2 | `177f48f` | `config.yaml` → `sync.empresas.sql`: `SELECT aux.numemp, aux.cod, aux.res AS nombre, aux.fecbaj, aux.desact FROM dbo.auxemp AS aux ORDER BY aux.numemp` (alias exactos, sin WHERE) |
| T3 | `1114625` | Puerto `EmpresaRepository` + `UnitOfWork.empresas`; `PgEmpresaRepository.sincronizar` (upsert idempotente por `numemp`) y `listar`; dominio `Empresa(numero, nombre, de_baja)` |
| T4 | `2e07dc2` | `FetchEmpresasStep` / `UpsertEmpresasStep` en el pipeline del sync (misma transacción); `ResultadoSync.empresas` y `SyncOut.empresas`; `deps.py` los compone con la consulta **obligatoria** |
| T5 | `79746bb` | Preview: sección `empresas` (`leidas`, `sin_numero`, `de_baja`, `nombres`) vía `filtros_maestros.resumir_empresas`; misma validación de columnas que el sync |
| T6 | `158e692` | `ListarEmpresas(por_defecto)` lee la tabla; `GET /api/v1/empresas` añade `de_baja`; fuera `empresas.nombres` de `config.yaml` y `nombres_empresas` del contenedor |
| T7 | `8462655` | `app.js`: la opción se pinta `«<nombre> (de baja)»` si `e.de_baja`; nunca se filtra |
| T8 | `4c161ae` | `docs/ARCHITECTURE.md`, `docs/INTEGRACION.md`, `services/dedicacion-api/README.md` |
| ajuste | `8160220` | test del front con `\b` real en la regex (ver Desviaciones) y línea en blanco que pedía ruff |
| ajuste | `fe93a43` | dos tests que matan los dos supervivientes de la mutación |

Ficheros de producción tocados (api): `config/config.yaml`,
`domain/{empresas,models,ports}.py`, `infrastructure/db/{orm_models,repositories}.py`,
`application/{sync_pipeline,use_cases,filtros_maestros}.py`,
`interface_adapters/api/{deps,routes,schemas}.py`. Front: `static/js/app.js`.
Tests: `tests/test_f032_empresas_sigrid.py` (nuevo, 32 tests; 43 casos con
parametrizaciones), `dedicacion-front/tests/test_f032_selector_de_baja.py`
(nuevo, 2), y dobles de F-023/F-024 (ver Desviaciones).

## Decisiones de diseño

1. **Clave `numemp`, no `empresa`.** Es lo que casa con `con.emp`; además el
   test de F-023 `test_f023_r1_empresa_solo_en_trabajador_y_obra` exige que
   solo `trabajador` y `obra` tengan columna `empresa`.
2. **Sin DDL a mano.** La tabla es nueva: la crea `Base.metadata.create_all`
   en `esquema.sincronizar_esquema` (arranque). `alters_faltantes` no emite
   nada para ella (test `..._esquema_la_crea_create_all_y_no_un_alter`).
3. **«De baja» lo decide el dominio**, no la tabla ni el front: la tabla
   guarda `fecbaj`/`desact` tal cual vienen; `_a_empresa` aplica la regla al
   mapear. `desact` cuenta solo con valor 1 («0no 1si» del diccionario).
4. **Upsert**: alta o actualización por `numemp`; una empresa que deja de
   llegar **no se borra** (su nombre sigue sirviendo); fila sin `numemp` se
   omite con aviso en log; `numemp` repetido no da dos altas.
5. **Consulta obligatoria en `deps.py`** (`config["sync"]["empresas"]["sql"]`,
   como empleados/obras): si alguien la borra, la api no arranca, en vez de
   dejar de actualizar nombres en silencio. En cambio `PreviewSync` recibe
   `sql_empresas` opcional (por defecto `None` → no lee ni publica la
   sección) para no cambiar la firma posicional que usan los tests de F-023;
   el contenedor la pasa siempre (test `..._el_preview_real_usa_la_consulta_de_config`).
6. **Pipeline**: el `assert` de empleados/obras se conserva; si un pipeline se
   compone sin los pasos de empresas, `ResultadoSync.empresas` sale a cero
   (nunca `None`). `ResultadoSync.empresas` va al final con valor por defecto.
7. **Selector**: el conjunto NO cambia (activos + la por defecto). Nombre de
   la tabla; «Empresa N» si no está en la tabla **o** su nombre viene vacío.
   La de baja (incluida la por defecto) sale con `de_baja: true`; el front
   añade « (de baja)» al texto de la opción y nada más.
8. **`POST /sync` responde además `empresas`** (`recibidos/altas/…`), aditivo.
   El mensaje del front tras sincronizar no se tocó (fuera de alcance).

## Desviaciones (justificadas)

- **Tests de F-024 que fijaban `empresas.nombres`**, sustituidos por su
  equivalente sobre la tabla (mismos nombres «Construcciones Ruesma» / «Porsan»):
  - `test_f024_cuadrante_empresa.py`: el doble `_Uow` gana un repositorio
    `_Empresas` en memoria. `test_f024_r2_nombre_de_config_o_empresa_n` →
    `test_f024_r2_nombre_de_la_tabla_o_empresa_n` (mismo resultado esperado,
    nombres sembrados en la tabla). `test_f024_r2_config_yaml_trae_los_nombres_de_d1`
    **eliminado**: lo sustituye `test_f032_r3_config_yaml_sin_empresas_nombres`.
    En `test_f024_r1_empresas_ordenadas_con_la_por_defecto` solo cambian la
    llamada (`ListarEmpresas({}, 1)` → `ListarEmpresas(1)`; el `{}` era
    `empresas.nombres`) y la forma de leer el número (`e for e, _` →
    `e.numero for e`): **los valores esperados `[1, 18, 28]` y `[1, 5, 18, 28]`
    no cambian**.
  - `test_f024_rutas_empresa.py`: fuera `NOMBRES`/`nombres_empresas`; la UoW
    del fixture siembra la tabla con los mismos dos nombres; el JSON esperado
    de `test_f024_r1_r2_get_empresas` gana `"de_baja": false` en cada empresa
    (mismos números y nombres). `test_f024_r2_el_contenedor_lleva_los_nombres_de_config`
    **eliminado**: lo sustituye `test_f032_r3_el_contenedor_no_lleva_nombres_de_config`.
- **Dobles de F-023** (`test_f023_sync_empresa.py`), **sin tocar ningún assert**:
  `_SigridFalso` devuelve `[]` para `dbo.auxemp`, `_UowEspia` gana
  `empresas`, `_config_prueba` gana `sync.empresas.sql` (obligatoria desde
  T4). Sin esto, los cinco tests R18 caían por `KeyError`/columnas.
- El primer test del front miraba `"desact" not in JS` y casaba con la
  palabra existente «desactivada»; se pasó a `\b…\b`. Al reescribir esa línea
  se coló un carácter de retroceso en vez de `\b` (lo cazó ruff, PLE2510): con
  él el test pasaba en vacío. Corregido en `8160220` y comprobado que
  `\bdesact\b` casa `x.desact` y no `desactivada`.

## Fase RED (trazas reales, test antes que código)

Comando en todas: `cd services/dedicacion-api && .venv/Scripts/python.exe -m pytest -q tests/test_f032_empresas_sigrid.py -k <filtro>`.

T1 (`-k "r1_tabla or r5_empresa_de_baja and 0-1"`):
```
E       ImportError: cannot import name 'EmpresaORM' from 'infrastructure.db.orm_models'
E       ImportError: cannot import name 'empresa_de_baja' from 'domain.empresas'
FAILED tests/test_f032_empresas_sigrid.py::test_f032_r1_tabla_empresa_declarada_en_el_orm
FAILED tests/test_f032_empresas_sigrid.py::test_f032_r5_empresa_de_baja[0-1-True]
2 failed, 10 deselected in 1.17s
```
T2 (`-k config`):
```
E       KeyError: 'empresas'
FAILED tests/test_f032_empresas_sigrid.py::test_f032_r1_config_lee_auxemp_con_los_alias_exactos
FAILED tests/test_f032_empresas_sigrid.py::test_f032_r1_config_consulta_de_solo_lectura
2 failed, 12 deselected in 1.32s
```
T3 (`-k repo`): 10 fallos, todos `ImportError: cannot import name 'PgEmpresaRepository'
from 'infrastructure.db.repositories'` (y `'Empresa' from 'domain.models'`):
```
FAILED tests/test_f032_empresas_sigrid.py::test_f032_r1_repo_es_idempotente
FAILED tests/test_f032_empresas_sigrid.py::test_f032_r2_repo_actualiza_cambios_de_sigrid[nombre-NUEVO NOMBRE SL-NUEVO NOMBRE SL]
FAILED tests/test_f032_empresas_sigrid.py::test_f032_r2_r5_repo_listar_mapea_nombre_y_baja
10 failed, 14 deselected in 0.98s
```
T4 (`-k "pipeline or sin_numemp_o or sync_real or respuesta_del_sync"`):
```
E       AttributeError: module 'application.sync_pipeline' has no attribute 'FetchEmpresasStep'. Did you mean: 'FetchEmpleadosStep'?
E       assert 'SELECT aux.numemp AS numemp,\n ... FROM dbo.auxemp AS aux\nORDER BY aux.numemp\n' in ["SELECT emp.ide ...", "...ORDER BY con.emp, con.cod\n"]
E       TypeError: ResultadoSync.__init__() got an unexpected keyword argument 'empresas'
4 failed, 24 deselected in 3.13s
```
T5 (`-k r4`):
```
E       TypeError: PreviewSync.__init__() got an unexpected keyword argument 'sql_empresas'
E       AssertionError: assert 'SELECT obr.i...mp, con.cod\n' == 'SELECT aux.n... aux.numemp\n'
FAILED tests/test_f032_empresas_sigrid.py::test_f032_r4_preview_informa_de_las_empresas_leidas
4 failed, 29 deselected in 2.60s
```
T6 (`-k "r2 or r3 or r5"`) — R2/R3/R5 centrales:
```
E       TypeError: ListarEmpresas.__init__() missing 1 required positional argument: 'por_defecto'
E       AttributeError: 'types.SimpleNamespace' object has no attribute 'nombres_empresas'
E       assert 'empresas' not in {... 'empresas': {'nombres': {1: 'Construcciones Ruesma', 28: 'Porsan'}}}
E       AssertionError: assert not True   (hasattr(Contenedor(...), 'nombres_empresas'))
FAILED tests/test_f032_empresas_sigrid.py::test_f032_r5_empresa_de_baja_con_trabajadores_sale_marcada
FAILED tests/test_f032_empresas_sigrid.py::test_f032_r2_r5_alta_cambio_de_nombre_y_baja_llegan_tras_el_sync
FAILED tests/test_f032_empresas_sigrid.py::test_f032_r2_r5_get_empresas_expone_nombre_y_baja
8 failed, 14 passed, 19 deselected, 1 warning in 4.33s
```
T7 (front, `cd services/dedicacion-front && .venv/Scripts/python.exe -m pytest -q tests/test_f032_selector_de_baja.py`):
```
E       assert 'e.de_baja' in 'function pintarSelectorEmpresa() {\n  const sel = $("#selector-empresa");\n ...'
FAILED tests/test_f032_selector_de_baja.py::test_f032_r5_el_selector_marca_de_baja_con_el_campo_de_la_api
1 failed, 1 passed in 0.09s
```
Tras cada código, la misma orden en verde (p. ej. T6: suite api `340 passed`).

## Trazabilidad acceptance → tests

| R | Tests |
|---|---|
| R1 | `test_f032_r1_*` (ORM, nulabilidad, `create_all`, config, repo, UoW, pipeline, sync real, respuesta del sync) |
| R2 | `test_f032_r2_*` (nombres de tabla, mismo conjunto, por defecto, cambios de Sigrid, punta a punta tras sync, `GET /empresas`, inmutabilidad) |
| R3 | `test_f032_r3_*` («Empresa N» solo fuera de tabla o sin nombre; config y contenedor sin nombres) |
| R4 | `test_f032_r4_*` (preview informa, valida columnas, sin consulta no lee, preview real) |
| R5 | `test_f032_r5_*` (regla de baja, selector marcado nunca oculto, front) |
| R6 | MANUAL (abajo) |
| R7 | review |

## Verificaciones MANUAL pendientes (humano; NO ejecutadas)

1. **Sync real en local** (api de esta rama con `python main.py` desde
   `services/dedicacion-api`, para que `create_all` cree la tabla `empresa`):
   `GET http://localhost:8090/api/v1/sync/preview` → comprobar
   `empresas.nombres["18"] == "RUESMA SERVICIOS SL"` y
   `empresas.nombres["31"] == "UTE RUESMA-INESCO TOLEDO"` (contraste:
   `progress/explore_nombres_empresas.md`) y ver qué sale en `empresas.de_baja`.
   Después `POST http://localhost:8090/api/v1/sync` → `empresas.recibidos` ≈ nº
   de filas de `auxemp`.
2. **Selector**: `GET http://localhost:8090/api/v1/empresas` y, en
   `http://localhost:8080`, que el selector enseña 18 = RUESMA SERVICIOS SL y
   31 = UTE RUESMA-INESCO TOLEDO, y 1 = CONSTRUCCIONES RUESMA (antes
   «Construcciones Ruesma» de `config.yaml`: el literal cambia al de Sigrid).
   Si alguna con trabajadores activos está de baja, debe salir «(de baja)».
3. **Copia a `azure-apps/dedicacion.md`** (la hace el líder): cambian la
   cabecera, la fila de `sigrid-api` de §1, el árbol de §2 (tabla `empresa`),
   el párrafo de `GET /api/v1/empresas` (`de_baja`) y una fila nueva en la tabla
   de «qué se rompe» (`auxemp`).

## Fuera del alcance

- El mensaje del front tras `POST /sync` no enseña las empresas.
- No se borran de la tabla las empresas que dejen de llegar de Sigrid.
- `desact` distinto de 0/1 no se trata como baja (el diccionario solo define 0/1).

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests | api **342 passed**; front **20 passed**; transfer **317 passed**; suite raíz de `init.sh` **355 passed, 1 skipped**. F-032: 32 tests api (43 casos) + 2 front |
| Cobertura líneas cambiadas | `PUERTA COBERTURA: 100.0% de 106 líneas cambiadas cubiertas (106/106, umbral 80%, nivel estandar)` |
| Mutación | `python -m harness.mutacion --feature F-032`, **4 workers**: 30 generados, 20 evaluados (muestreo estándar, semilla 20260820), **18 muertos, 2 supervivientes**, 0 timeouts, 0 sin veredicto; 118,2 s; línea base 18,0-18,1 s; media 5,9 s/mutante (×4 workers = 23,6 s ≥ base: coherente). SHA medido `8160220`; el commit posterior `fe93a43` solo añade tests (mismo alcance de producción). Detalle: `progress/mutacion_F-032.md` |
| Supervivientes | los 2 **reproducidos a mano** en copia aislada (`340 passed` con cada mutante) → huecos reales → tests nuevos que los matan (`1 failed, 341 passed` con cada mutante). Análisis completo en el informe de mutación; ninguno PENDIENTE; sin quitar código defensivo |
| Tiempo de la suite | api 8,9-14,4 s; front 3,1 s; raíz 43,1 s (`init.sh`) |
| `bash harness/init.sh` | **ENTORNO LISTO** (todas las puertas OK; ruff 193 avisos = deuda previa, los mismos que en `dev`) |
