<!-- specs/F-024-selector-empresa/design.md -->
# F-024 · Diseño técnico

Requisitos: [`requirements.md`](requirements.md). Regla de dominio:
[`docs/ARCHITECTURE.md#regla-empresa`](../../docs/ARCHITECTURE.md#regla-empresa).
El diseño asume las propuestas de D1-D7; si el humano elige otra opción, se
rehace la sección afectada antes de implementar.

## 1. Límite de servicio

| Servicio | Qué hace en F-024 | Por qué ahí |
|---|---|---|
| `dedicacion-api` | lista de empresas, regla de visibilidad, filtro del cuadrante, resumen, copia, export y empresa de cada línea | es el dueño del dato y de las reglas; el front no decide |
| `dedicacion-front` | selector, `?empresa=N` en la URL y en cada llamada, marcas visuales | presentación pura (`docs/CONVENTIONS.md`, JS) |
| `dedicacion-transfer` | en el corte por obra de otra empresa, publicar la obra de origen resuelta | es quien la resuelve; el contrato no cambia (R21) |

Nada exige un servicio nuevo. No se duplica lógica: la regla de
visibilidad vive en **una** función de dominio que usan el cuadrante y el
registro.

## 2. Ficheros a crear

- `services/dedicacion-api/domain/empresas.py` — regla de visibilidad (§4.1).
- `services/dedicacion-api/tests/test_f024_visibilidad.py` — R8, R10, R11.
- `services/dedicacion-api/tests/test_f024_cuadrante_empresa.py` — R7, R9,
  R13, R14, R15 sobre una UoW falsa en memoria.
- `services/dedicacion-api/tests/test_f024_rutas_empresa.py` — R1, R2, R6,
  R18 con `TestClient` y `dependency_overrides[obtener_contenedor]` (sin
  BBDD: el engine de SQLAlchemy no conecta hasta usarse).
- `services/dedicacion-api/tests/test_f024_registro_empresa.py` — R16-R19.
- `services/dedicacion-transfer/tests/test_f024_obra_destino_otra_empresa.py` — R20, R21.
- `services/dedicacion-front/tests/test_f024_selector.py` — R3-R5 y R12
  como comprobación estática de `index.html` y `app.js` (§6).

## 3. Ficheros a modificar

| Fichero | Cambio |
|---|---|
| `dedicacion-api/domain/models.py` | `Linea.obra_empresa: int \| None = None`; dataclass `FiltroEmpresa(empresa: int, por_defecto: int)` |
| `dedicacion-api/domain/ports.py` | `TrabajadorRepository.empresas_activas() -> set[int]` |
| `dedicacion-api/infrastructure/db/repositories.py` | `_a_linea` mapea `o.empresa`; `PgTrabajadorRepository.empresas_activas()` |
| `dedicacion-api/application/use_cases.py` | `filtro: FiltroEmpresa` en cuadrante, fila, guardar, deshacer, copias y `_resumen_periodo`; caso de uso `ListarEmpresas` |
| `dedicacion-api/application/registro_sigrid.py` | `preflight`/`ejecutar` reciben `empresa`; `_payloads` filtra por visibilidad y pone `empresa = E` |
| `dedicacion-api/interface_adapters/api/routes.py` | parámetro `empresa`, `GET /empresas`, nombre del export |
| `dedicacion-api/interface_adapters/api/schemas.py` | `EmpresaOut`, `EmpresasOut`; `empresa` en `CuadranteOut` y `TrabajadorOut`; `obra_empresa`, `otra_empresa` en `LineaOut` |
| `dedicacion-api/interface_adapters/api/deps.py` | nombres de `config.yaml` al contenedor |
| `dedicacion-api/config/config.yaml` | bloque `empresas.nombres`; `{empresa}` en `export.nombre_fichero` |
| `dedicacion-api/config/settings.py` y `.env.example` | solo el comentario de `empresa_imputacion` (D6) |
| `dedicacion-api/tests/test_f022_empresa_en_linea.py` | los dobles `_fila` ganan `empresa=None` en trabajador y obra (§7) |
| `dedicacion-transfer/application/pipelines/registro_pipeline.py` | `preflight`, rama de obra de otra empresa: `_todas_omitidas(origen, …)` |
| `dedicacion-transfer/tests/test_f022_obra_por_empresa.py` | un assert de R10/R11 (§7) |
| `dedicacion-front/templates/index.html` | `<select id="selector-empresa">` en `.topbar__meta` |
| `dedicacion-front/static/js/app.js` | estado `empresa`, carga de la lista, `conEmpresa()`, URL, marcas |
| `dedicacion-front/static/css/styles.css` | estilo del selector y de las dos marcas |
| `docs/ARCHITECTURE.md`, `docs/INTEGRACION.md` | R22 |

## 4. Clases y funciones

### 4.1 Dominio (`domain/empresas.py`)

```python
def visible_en_empresa(empresa_trabajador: int | None,
                       empresas_obras: Iterable[int | None],
                       filtro: FiltroEmpresa) -> bool
```

- Con `empresa_trabajador` no nulo: `== filtro.empresa`.
- Con NULL: `conocidas = {e for e in empresas_obras if e is not None}`;
  si hay, `filtro.empresa in conocidas`; si no, `filtro.empresa ==
  filtro.por_defecto`.

```python
def linea_de_otra_empresa(obra_empresa: int | None, empresa: int) -> bool
```

`obra_empresa is not None and obra_empresa != empresa` (R11). Las dos son
puras y sin dependencias: se prueban con tablas de casos.

### 4.2 Aplicación (`use_cases.py`)

- `_filas_de_empresa(uow, periodo_id, filtro) -> list[CuadranteTrabajador]`:
  `listar_para_periodo` + `lineas_del_periodo` (sin cambiar sus consultas) y
  se queda con las filas que cumplen `visible_en_empresa(t.empresa,
  [ln.obra_empresa for ln in lineas], filtro)`. Único punto del filtro de
  trabajadores; lo usan `ObtenerCuadrante`, `_resumen_periodo` y
  `CopiarPeriodoAnterior` (este, además, `t.activo`).
- `ObtenerCuadrante.ejecutar(uow, anio, mes, filtro)`: filas de
  `_filas_de_empresa`; obras = `listar_para_periodo` con `o.empresa ==
  filtro.empresa` (R9). `Cuadrante` gana `empresa: int`.
- `ObtenerFilaTrabajador`, `GuardarAsignaciones`,
  `DeshacerUltimaModificacion`, `CopiarTrabajadorAnterior`: `filtro`
  keyword-only, que solo llega a `_resumen_periodo` (R13). La fila del
  trabajador no se filtra: lleva todas sus líneas (R10).
- `ListarEmpresas(nombres: dict[int, str], por_defecto: int).ejecutar(uow)
  -> tuple[int, list[tuple[int, str]]]`: `uow.trabajadores.empresas_activas()
  | {por_defecto}`, ordenada, nombre de `nombres` o `f"Empresa {n}"` (R1, R2).

### 4.3 Registro (`registro_sigrid.py`)

- El constructor no cambia de firma; su tercer argumento pasa a ser la
  empresa por defecto (D6). Atributo `_por_defecto`.
- `preflight(anio, mes, overrides=None, trabajador_ide=None, empresa=None)`
  y lo mismo en `ejecutar`: `E = empresa or self._por_defecto`.
- `_payloads(..., filtro)`: la consulta no cambia. Tras leer las filas,
  agrupa `o.empresa` por `t.ide` y descarta las de trabajadores con
  `not visible_en_empresa(t.empresa, empresas_de[t.ide], filtro)`. Cada
  línea lleva `"empresa": filtro.empresa` (R16). Las de obra de otra empresa
  **se mandan** (R17); el transfer las omite y `_trazar` ya persiste las
  omitidas.
- R18 sale solo: sin filas visibles no hay payloads, y `preflight` y
  `ejecutar` ya devuelven `{"ok": True, "obras": []}`.
- R19 no exige código: `TransferClient._post` ya convierte el 502 en
  `{"ok": False, "error": …}` y `_trazar` solo corre con `ok`. Se fija con
  un test.

### 4.4 Interfaz (`routes.py`, `schemas.py`)

- `EmpresaQ = Annotated[int | None, Query(gt=0)]` (422 si no es > 0, R6), y
  `_filtro(contenedor, empresa) -> FiltroEmpresa` con
  `contenedor.settings.empresa_imputacion` como por defecto.
- Lo reciben: `cuadrante`, `asignaciones` (PUT), `deshacer`, las dos
  `copiar-anterior`, `export.xlsx`, `registro/preflight` y
  `registro/ejecutar`. En el registro va por **query**, como en el resto, y
  no en el cuerpo: un solo mecanismo para todo el front.
- `GET /api/v1/empresas` → `EmpresasOut(por_defecto: int, empresas:
  list[EmpresaOut(empresa: int, nombre: str)])`.
- `a_trabajador_out(fila, empresa)` añade `empresa` del trabajador y, por
  línea, `obra_empresa` y `otra_empresa = linea_de_otra_empresa(...)`.
- Export: `nombre_fichero: "dedicacion_{anio}{mes:02d}_emp{empresa}.xlsx"`.
  El exportador no cambia: recibe ya las filas filtradas.

### 4.5 Repositorio

- `empresas_activas()`: `select(distinct(TrabajadorORM.empresa)).where(
  TrabajadorORM.activo.is_(True), TrabajadorORM.empresa.is_not(None))`.
- `listar_para_periodo` de trabajadores y obras **no cambia**: el filtro va
  en aplicación para que la regla de R8 tenga un único dueño y se pruebe sin
  BBDD.

### 4.6 Transfer (`registro_pipeline.py`)

En `preflight`, la rama `origen.empresa != empresa` pasa `origen` (ya
resuelto por `_obra_origen`) a `_todas_omitidas` en vez de la obra de
entrada. `ejecutar` reutiliza `pf.obra_destino`, así que hereda el cambio.
La rama sin empresa (R3 de F-022) sigue con la de entrada (R20). Ni
`PeticionIn` ni la respuesta cambian de campos (R21).

## 5. SQL

No hay SQL nuevo contra Sigrid ni columnas nuevas: `empresa` ya está en
`obra` y `trabajador` (F-023, `orm_models.py`). La única consulta nueva es
`empresas_activas()`, construida con el ORM. Sin DDL.

## 6. Front

- `index.html`: `<select id="selector-empresa" class="selector-empresa"
  title="Empresa">` como primer hijo de `.topbar__meta` (esquina superior
  derecha). Opciones vacías: las pinta `app.js`.
- `app.js`:
  - `state.empresa = null` y `state.empresas = []`.
  - `init()`: antes de `cargarPeriodo`, `GET /empresas`; elige
    `?empresa=` de la URL si está en la lista, si no `por_defecto` (R3, R4).
  - `conEmpresa(ruta)` añade `empresa=<state.empresa>` a la ruta; la usan
    `api()` para toda ruta que empiece por `/periodos/` y el `href` del
    export (R5).
  - `change` del selector: `history.replaceState` con `?empresa=N` y
    `cargarPeriodo(state.anio, state.mes)`.
  - `construirCelda`: clase `chip-otra-empresa` y `title` en las líneas con
    `otra_empresa`; insignia «sin empresa» si `t.empresa === null` (R12).
- El proxy del front ya reenvía la query (`interface_adapters/web/app.py`,
  `params=request.query_params`): no se toca.
- `test_f024_selector.py` lee los dos ficheros y comprueba: el `select`
  dentro de `.topbar__meta`; que `app.js` pide `/empresas`, usa
  `por_defecto` y define `conEmpresa`; que no compara `.empresa` contra
  `state.empresa` para filtrar filas. La apariencia la verifica el humano
  (T13).

## 7. Tests existentes que cambian (y por qué)

- `test_f022_obra_por_empresa.py::test_f022_r10_r11_pipeline_obra_de_otra_empresa_se_omite`:
  `assert pf.obra_destino is obra` pasa a comprobar `ide == 555028` y
  `empresa == 28`. Es exactamente lo que pide R20 (criterio 5 de F-024,
  recogido de la review 1 de F-022). El resto de asserts no cambia.
- `test_f022_empresa_en_linea.py`: los dobles `_fila` no tienen `empresa`; se
  añade `empresa=None` a trabajador y obra. Con NULL y sin obras con
  empresa, el trabajador es visible en la por defecto (R8), que es la que
  usan esos tests: **ningún assert cambia**. Los nombres R20/R21 de F-022
  siguen siendo ciertos con D6.

## 8. Ficheros que NO se tocan

- `orm_models.py`, `esquema.py`: sin columnas nuevas.
- `sync_pipeline.py`, `filtros_maestros.py`, `config.yaml` → `sync`: la
  empresa ya llega del sync (F-023).
- `infrastructure/excel/exporter.py` (lo toca F-020).
- `dedicacion-transfer`: `PeticionIn`, `interface_adapters/api/app.py`,
  `reglas_porcentajes.py`, `_obra_destino` y el modo pruebas (D3).
- `dedicacion-front/interface_adapters/web/app.py` (proxy).
- `infra/`: `EMPRESA_IMPUTACION` conserva nombre (D6).

## 9. Riesgos y decisiones

- **Filtrar en Python y no en SQL.** Con ~180 trabajadores activos y un
  periodo, traer todo y filtrar es trivial, y deja la regla en una función
  pura. Si el volumen creciera, se baja a SQL manteniendo la función como
  referencia de los tests.
- **Una persona, dos filas.** Con fichas en dos empresas sale en las dos,
  cada una con su 100 % (D7). Es el comportamiento de hoy, solo que
  separado.
- **El resumen depende de E.** Un cliente viejo sin `empresa` ve la por
  defecto: mismo comportamiento que un front de antes de F-024 en una base
  con una sola empresa, y distinto (filtrado) en una mezclada, que es justo
  lo que F-023 pide para desplegar.
- **Modo pruebas.** Con E ≠ 1 no se escribe nada (D3): es lo prudente
  mientras `OBRA_PRUEBAS_FORZAR=true`.
- **`azure-apps`.** Cambia lo que exponemos (`GET /empresas`, parámetro
  `empresa`) y el sentido de una variable: va en el mismo trabajo (T11); el
  commit en `azure-apps` lo hace el humano.

## 10. Fuera de alcance

- Validar en la API que una línea nueva sea de una obra de la empresa del
  trabajador: el front solo ofrece obras de E (R9) y el transfer ya omite
  las de otra empresa (R17).
- Que «copiar mes anterior» descarte las líneas de obras de otra empresa:
  se copian como hoy y salen marcadas (R11, R12).
- El recurso por empresa (F-026), el filtro por obra (F-021) y la selección
  múltiple (F-029).
