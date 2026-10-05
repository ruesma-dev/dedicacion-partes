# F-024 · Informe del implementer

> Selector de empresa arriba a la derecha, Construcciones Ruesma por defecto.
> Rigor **estándar**. Rama `feature/F-024-selector-empresa`. Spec:
> `specs/F-024-selector-empresa/` con D1-D7 aprobadas. Estado: **T1-T10 y T14
> hechas**; T11, T12 y T13 son MANUAL (humano), pendientes (ver al final).

## Qué cambió

| Servicio · fichero | Cambio |
|---|---|
| api · `domain/empresas.py` (nuevo) | `visible_en_empresa` (R8) y `linea_de_otra_empresa` (R11): la regla, una sola vez, pura. |
| api · `domain/models.py`, `domain/ports.py` | `FiltroEmpresa(empresa, por_defecto)` (frozen); `Linea.obra_empresa`; `TrabajadorRepository.empresas_activas()`. |
| api · `infrastructure/db/repositories.py` | `_a_linea` mapea `o.empresa`; `empresas_activas()` = `SELECT DISTINCT empresa … WHERE activo AND empresa IS NOT NULL`. `listar_para_periodo` sin cambios. |
| api · `application/use_cases.py` | `_filas_de_empresa` (único punto del filtro); `ObtenerCuadrante(…, filtro)` filtra filas y obras (`o.empresa == E`) y devuelve `empresa`; `filtro` keyword-only en fila, guardar, deshacer y las dos copias; `_resumen_periodo` por empresa; `ListarEmpresas`. |
| api · `application/registro_sigrid.py` | `preflight`/`ejecutar(…, empresa=None)`; E = `empresa or por_defecto`; `_payloads` descarta trabajadores no visibles y pone `empresa = E` en cada línea. Constructor con la misma firma (D6). |
| api · `interface_adapters/api/{routes,schemas,deps}.py` | `EmpresaQ = Annotated[int \| None, Query(gt=0)]` + `_filtro` en cuadrante, PUT asignaciones, deshacer, dos `copiar-anterior`, export, `registro/preflight` y `registro/ejecutar` (por query); `GET /api/v1/empresas`; `empresa` en `CuadranteOut`/`TrabajadorOut`; `obra_empresa`/`otra_empresa` en `LineaOut`; `nombres_empresas` en el contenedor. |
| api · `config/config.yaml` | Bloque `empresas.nombres` (1 y 28, D1); `export.nombre_fichero` con `_emp{empresa}`. |
| api · `config/settings.py`, `.env.example` | Solo comentarios: `EMPRESA_IMPUTACION` es la empresa por defecto (D6). |
| transfer · `registro_pipeline.py` | En el corte por obra de otra empresa, `_todas_omitidas(origen, …)` (R20). Contrato intacto (R21). |
| front · `index.html`, `app.js`, `styles.css` | `<select id="selector-empresa">` primer hijo de `.topbar__meta`; `state.empresa/empresas`, `cargarEmpresas()` antes de `cargarPeriodo`, `conEmpresa()` en `api()` para `/periodos/…` y en el export, `cambiarEmpresa()` con `history.replaceState`; marcas «sin empresa» y `chip-otra-empresa`. Sin filtrar nada. |
| docs · `ARCHITECTURE.md#regla-empresa`, `INTEGRACION.md` | R22: empresa elegida vs por defecto, visibilidad, registro con E, R20, modo pruebas con otra empresa; `GET /empresas` y parámetro `empresa` (§5), variable (§3), §9 y cabecera. |
| tests | Nuevos: `test_f024_visibilidad.py`, `test_f024_cuadrante_empresa.py`, `test_f024_registro_empresa.py`, `test_f024_rutas_empresa.py` (api), `test_f024_obra_destino_otra_empresa.py` (transfer), `test_f024_selector.py` (front). Modificados según design §7: dobles de `test_f022_empresa_en_linea.py` (`empresa=None`, sin tocar asserts) y el assert de `test_f022_r10_r11_pipeline_obra_de_otra_empresa_se_omite`. |

No se tocan `orm_models.py`, `esquema.py`, sync, exporter, proxy del front,
`PeticionIn` ni `infra/`. `azure-apps/` sin tocar (T11 es del líder con el humano).
`progress/current.md` y `harness/features.json` sin tocar.

## Commits (uno por tarea + dos de estilo)

`1b0bc40` T1 · `520c15d` T2 · `83e10b7` T3 · `c7b3e9d` T4 · `de608fb` T5 ·
`89b61a2` T6 · `6146dae` T7 · `1ae3e8e` T8 · `714a762` T9 · `a7fe2c5` T9 (ruff) ·
`a2bcbca` T10 · `fda620d` orden de imports (ruff desde la raíz). Nada de push.

## Decisiones de diseño

- **`filtro` obligatorio** (sin valor por defecto) en los casos de uso: un
  llamante que lo olvide falla en vez de usar en silencio una empresa. La
  por defecto solo se resuelve en la interfaz (`_filtro`) y en `RegistroSigrid`.
- **Rutas de registro**: pasan a `RegistroSigrid` la E ya resuelta por
  `_filtro`; `RegistroSigrid` conserva su propio `empresa or por_defecto`
  (design §4.3) para los llamantes sin empresa (scripts).
- **Copia del mes (R14)**: `con_carga_previa` y la lista de activos salen de
  `_filas_de_empresa` del periodo destino, así los contadores son solo de E.
- **Front**: `cargarEmpresas` comprueba si la `?empresa=` de la URL está en la
  lista que da la API (lo exige R4); no hay otra decisión en `app.js`. Si
  `/empresas` falla, `state.empresa` queda `null` y la API usa la por defecto.
- **`typing.Self`** en los dobles con `__enter__` (ruff PYI034), sin depender
  de `typing_extensions`.

## Desviaciones y notas

1. **Commits intermedios T3-T5**: las rutas llaman a los casos de uso sin
   `filtro` hasta T6 (no había tests de rutas que lo cazaran). Es el orden de
   `tasks.md`; desde `89b61a2` está todo cableado y en verde.
2. **Assert de F-022 (design §7)**: `assert pf.obra_destino is obra and
   pf.forzada_pruebas is forzar` se parte en dos; la mitad de `forzada_pruebas`
   no cambia, la otra pasa a `(ide, empresa) == (555028, 28)`. Es el único
   assert anterior modificado.
3. **Cabecera de `INTEGRACION.md`**: fecha 2026-10-01 y origen «rama F-024,
   pendiente de merge»; no invento un SHA de origen que aún no existe.
4. **Aviso nuevo en la suite de la api**: `StarletteDeprecationWarning` de
   `fastapi.testclient` (librería), porque `test_f024_rutas_empresa.py` es el
   primer `TestClient` de la api. El transfer ya lo emitía. No es fallo.

## Fase RED (tests antes del código, salida real)

Comandos desde la carpeta de cada servicio, con su `.venv`:
`.venv/Scripts/python -m pytest tests/<fichero> -q -p no:cacheprovider --tb=line`.
Las trazas se pegan resumidas por mensaje (`sort | uniq -c`), sin rutas.

**T1 · R8/R10/R11** (`test_f024_visibilidad.py`, sin `domain/empresas.py`):
```
E   ModuleNotFoundError: No module named 'domain.empresas'
ERROR tests/test_f024_visibilidad.py
1 error in 0.18s
```
**T2 · R1/R11** (`test_f024_cuadrante_empresa.py`):
```
E   AttributeError: 'PgTrabajadorRepository' object has no attribute 'empresas_activas'
E   AssertionError: assert None == 28          (_a_linea no mapeaba o.empresa)
2 failed in 0.83s
```
**T3 · R7/R9/R10/R13/R14** (mismo fichero):
```
11 E   TypeError: ObtenerCuadrante.ejecutar() takes 4 positional arguments but 5 were given
 4 E   TypeError: CopiarPeriodoAnterior.ejecutar() got an unexpected keyword argument 'filtro'
 2 E   TypeError: ObtenerFilaTrabajador.ejecutar() got an unexpected keyword argument 'filtro'
17 failed, 2 passed in 0.70s
```
**T4 · R1/R2**: `E   ImportError: cannot import name 'ListarEmpresas' from 'application.use_cases'`.

**T5 · R16-R19** (`test_f024_registro_empresa.py`), en dos pasos para que la
RED sea de comportamiento y no solo de firma. Paso 1, sin el parámetro:
```
7 E   TypeError: RegistroSigrid.ejecutar() got an unexpected keyword argument 'empresa'
6 E   TypeError: RegistroSigrid.preflight() got an unexpected keyword argument 'empresa'
13 failed in 1.30s
```
Paso 2, con `empresa` aceptada y puesta en la línea pero SIN filtro de visibilidad:
```
4 E   assert [(1, 1), (2, ...4, 1), (5, 1)] == [(1, 1), (2, 1), (5, 1)]
2 E   assert [(1, 28), (2,... 28), (5, 28)] == [(3, 28), (4, 28)]
2 E   assert [(1, 18), (2,... 18), (5, 18)] == []
2 E   AssertionError: assert {'ok': True, ... 'ok': True}]} == {'ok': True, 'obras': []}   (R18)
2 E   assert [678, 9, 500] == [9]                                                       (R19)
1 E   assert [(2, 1), (3, 1), (4, 1)] == [(2, 1)]                                       (R17)
13 failed in 1.63s
```
**T6 · R1/R2/R6/R11/R15/R18** (`test_f024_rutas_empresa.py`):
```
14 E   TypeError: ObtenerCuadrante.ejecutar() missing 1 required positional argument: 'filtro'
10 E   TypeError: GuardarAsignaciones.ejecutar() missing 1 required keyword-only argument: 'filtro'
 8 E   AssertionError: {"ok":true,"obras":[]}     (registro aceptaba empresa=0/-3/abc/1.5: sin 422)
 4 E   KeyError: 'empresa'                        (el registro no recibía la empresa)
 1 E   AttributeError: 'Contenedor' object has no attribute 'nombres_empresas'
 1 E   AssertionError: {"detail":"Not Found"}     (no existía GET /empresas)
56 failed, 1 warning in 5.37s
```
**T7 · R20** (transfer, `test_f024_obra_destino_otra_empresa.py`):
```
2 E   AssertionError: assert (555028, '0678', None) == (555028, '0678', 28)   (preflight)
2 E   assert (555028, None) == (555028, 28)                                  (ejecutar)
4 failed, 2 passed in 0.70s     (los 2 que pasan: corte sin empresa, que no cambia)
```
**T8 · R21**: el test vigila que el contrato NO cambie, así que pasa desde el
principio. Se demostró que muerde en una **copia aislada** del servicio (fuera
del árbol, borrada después) añadiendo `"obra_origen"` a la respuesta del preflight:
```
E   AssertionError: assert {'acciones', ..._origen', ...} == {'acciones', ...stventa', ...}
1 failed, 1 passed, 6 deselected in 2.03s
```
**T9 · R3/R4/R5/R12** (front, `test_f024_selector.py`):
```
E   ValueError: not enough values to unpack (expected 1, got 0)      (no había select)
E   AssertionError: assert 'cargarEmpresas()' in 'async function init() {…'
E   AssertionError: no existe la función cambiarEmpresa en app.js
E   AssertionError: no existe la función conEmpresa en app.js
E   assert None                                                      (export sin empresa)
E   assert ('t.empresa === null' in 'function construirCelda(t, clave) {…')
6 failed, 1 passed in 0.09s     (el que pasa: «el front no filtra», guarda)
```
Después de cada implementación, el mismo comando en verde (resultados abajo).

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests de F-024 | api 125, transfer 8, front 7: **140 passed** |
| Suites por servicio (`init.sh`) | api **301 passed** (9.93 s) · front **18 passed** (1.82 s) · transfer **317 passed** (3.22 s) |
| Suite de raíz (`init.sh`) | **355 passed, 1 skipped** en 38.16 s |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 105 líneas cambiadas cubiertas (105/105, umbral 80%, nivel estandar)` |
| Mutación (`python -m harness.mutacion --feature F-024`) | **17 generados, 17 muertos, 0 supervivientes, 0 timeouts**, 93.9 s, 4 workers, SHA `fda620d`; muestreo no aplicado (17 < 20). Detalle: `progress/mutacion_F-024.md` |
| ruff | 193 avisos, igual que `dev` (comprobado con `diff` de la salida de ambos árboles) |
| `node --check static/js/app.js` | sin errores de sintaxis |

Supervivientes: **ninguno**, no hay análisis pendiente. Nota de alcance: el
cambio del transfer (`obra` → `origen`, 4 líneas) no genera mutantes con los
operadores de la herramienta; R20 lo sostienen la RED de T7, sus 6 tests y el
assert R20 dentro del test de contrato R21 a través de la app.

**`bash harness/init.sh` (final, tal cual)**: `ENTORNO LISTO. Puedes trabajar.`
con `[OK]` en pytest de raíz y de los tres servicios, `PUERTA COBERTURA` 100 %
(105/105), `PUERTA TAMAÑO` dentro de los topes (impl 192/220), ningún `.env` versionado,
`config.yaml` válido y rama correcta. Único `[AVISO]`: ruff 193 (deuda previa).

## Fuera del alcance (design §10)

Validar en la API que una línea nueva sea de una obra de la empresa del
trabajador; que «copiar mes anterior» descarte líneas de obras de otra empresa
(se copian y salen marcadas); recurso por empresa (F-026), filtro por obra
(F-021), selección múltiple (F-029).

## Verificaciones MANUAL pendientes (humano)

- **T11 · `azure-apps/dedicacion.md`**: copiar literales, sin reescribir el
  resto, las piezas de T10 de `docs/INTEGRACION.md`: la fila
  `EMPRESA_IMPUTACION` de §3, el párrafo nuevo de §5 (`GET /api/v1/empresas` y
  parámetro `empresa`), el párrafo «Una línea sin empresa no se registra» de §9
  y la cabecera. Revisar el `diff` en `azure-apps` y hacer allí el commit.
- **T12 · nombres (D1)**: lectura de solo lectura vía `sigrid-api`
  (`POST /api/sql/read`): `SELECT numemp, res FROM dbo.auxemp WHERE numemp IN
  (1, 18, 28, 31)`; confirmar y dar de alta en `empresas.nombres` de
  `services/dedicacion-api/config/config.yaml`. Sin ella el selector enseña
  «Empresa 18» y «Empresa 31» (R2). No se ha inventado ningún nombre.
- **T13 · prueba en local** (API de la rama contra la BBDD `dedicacion`,
  transfer en modo pruebas): entrar sin `?empresa` → Construcciones Ruesma
  seleccionada; cambiar a 18 y volver (la URL queda con `?empresa=N`); julio
  2026 con la 1 → las líneas de 0009 y 0025 con `otra_empresa: true`, marcadas,
  y omitidas en el preflight con `obra_destino.empresa == 28`; preflight con la
  18 → error de obra de pruebas por obra, nada escrito. **NO lanzar
  `registro/ejecutar`**. Resultado a anotar en `progress/`.
