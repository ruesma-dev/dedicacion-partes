# F-040 · Diseño técnico

Escrito con D1-D6 = A, decididas por el humano el 2026-10-06 (`requirements.md`). Solo cambia
`dedicacion-api/infrastructure/excel/`: es presentación de un dato que ya entrega la API.

## 1. Encaje en la arquitectura y límite de servicio

- La ruta `export.xlsx` (`interface_adapters/api/routes.py`) llama a `ObtenerCuadrante` con el
  filtro de empresa y pasa `cuadrante.periodo` y `cuadrante.filas` (`list[CuadranteTrabajador]`)
  al exportador. Ese contrato **no cambia**: cada `Linea` ya trae `cod`, `descripcion`,
  `es_postventa` y `porcentaje`, y cada `Trabajador`, `nombre` y `categoria`. No hace falta un dato
  nuevo de la API ni una columna nueva.
- El orden lo pone el repositorio (`TrabajadorORM.nombre`; las líneas, por `ObraORM.cod` y
  `es_postventa`). El exportador lo respeta (R7).
- Las cifras salen de `domain/estados.py`, la regla del 100 %. El exportador solo les da formato (R16).
- Límite de servicio: todo cae dentro de `dedicacion-api`. Nada de esto pertenece al front (no
  decide nada) ni al transfer.
- D1 = A: el «nombre corto» editable (la opción C, descartada) **no** cabría aquí, porque necesitaría ORM, endpoint y front.

## 2. Ficheros

**Crear**

| Ruta | Qué |
|---|---|
| `services/dedicacion-api/infrastructure/excel/contenido.py` | Modelo de presentación puro: grupos del Detalle, filas del Resumen, textos de % y de estado (§3.1) |
| `services/dedicacion-api/tests/test_f040_excel.py` | Tests `test_f040_rN_…` de R1-R20 (§7) |

**Modificar**

| Ruta | Qué cambia |
|---|---|
| `services/dedicacion-api/infrastructure/excel/exporter.py` | Se reescribe el pintado (§3.2). Se mantienen la clase `OpenpyxlExcelExporter`, su constructor y `exportar(periodo, filas) -> bytes`. Salen `_texto_estado`, `_pct` y `_formatear`, que pasan a `contenido.py` o a los helpers nuevos |
| `docs/ARCHITECTURE.md` | Línea 78-79: `excel/` («export con el modelo de negocio: Detalle agrupado por trabajador y Resumen») (R21) |
| `services/dedicacion-api/README.md` | Fila `export.xlsx` de la tabla de endpoints (R21) |

**No se tocan**: `domain/ports.py` (el puerto `ExcelExporter`), `domain/estados.py`,
`domain/models.py`, `application/use_cases.py`, `interface_adapters/api/routes.py` y `deps.py`,
`config/config.yaml` (se reutiliza `export.prefijo_postventa`), `requirements.txt` (openpyxl
3.1.5 ya instalado), `orm_models.py`, el front, el transfer, `tests/test_f024_rutas_empresa.py`
y `azure-apps/`. Sin SQL.

## 3. Clases y funciones

### 3.1 `infrastructure/excel/contenido.py` (infrastructure, puro: sin openpyxl)

```python
@dataclass(frozen=True)
class LineaDetalle:
    codigo: str               # «0702», «Postv-0702», «VAR-29»; «» si el trabajador no tiene líneas
    obra: str                 # columna Obra del Detalle (con prefijo si es postventa)
    nombre: str               # descripción sin prefijo, para el Resumen (D1 = A)
    porcentaje: Decimal | None

@dataclass(frozen=True)
class GrupoTrabajador:
    empleado: str
    categoria: str
    lineas: list[LineaDetalle]   # nunca vacía: sin líneas, una LineaDetalle vacía (R9)
    total: Decimal
    desviacion: Decimal | None   # None si SIN CARGA (celda vacía, R9)
    estado: str                  # texto de R19

@dataclass(frozen=True)
class FilaResumen:
    empleado: str
    categoria: str
    obras: str
    total: Decimal
    estado: str

def grupos_detalle(filas: list[CuadranteTrabajador], prefijo: str) -> list[GrupoTrabajador]
def filas_resumen(grupos: list[GrupoTrabajador]) -> list[FilaResumen]
def texto_pct(valor: Decimal) -> str          # «100», «10», «33,33» (R18)
def texto_estado(estado: EstadoTrabajador, desviacion: Decimal) -> str   # R19
def es_entero(valor: Decimal) -> bool         # decide `0%` / `0.00%` (R17)
```

- `grupos_detalle` llama a `calcular_estado(fila.total, len(fila.lineas))` y a
  `calcular_desviacion(...)` de `domain.estados` (R16) y conserva el orden de entrada (R7).
- `filas_resumen` sale de los grupos: «Obras» = `" + ".join(f"{l.codigo} {l.nombre} = {texto_pct(l.porcentaje)}%")`
  sobre las líneas con porcentaje (R14), y el Estado es el del grupo (R15).
- `texto_pct`: si es entero, `str(int(valor))`; si no, `f"{valor:.2f}".replace(".", ",")`. Se usa
  formato fijo y nunca `normalize()` (el fallo de «1E+2»).

### 3.2 `infrastructure/excel/exporter.py` (infrastructure, openpyxl)

```python
class OpenpyxlExcelExporter:
    def __init__(self, prefijo_postventa: str = "Postv-") -> None
    def exportar(self, periodo: Periodo, filas: list[CuadranteTrabajador]) -> bytes
    def _hoja_detalle(self, hoja, periodo, grupos: list[GrupoTrabajador]) -> None
    def _hoja_resumen(self, hoja, periodo, resumen: list[FilaResumen]) -> None

def _titulo_y_cabecera(hoja, titulo: str, cabecera: list[str]) -> None    # R2, R5
def _combinar_con_valor(hoja, columna: int, desde: int, hasta: int) -> None   # R10-R11, §5
def _celda_pct(celda, valor: Decimal | None) -> None   # fracción + `0%` / `0.00%` (R17)
def _rematar(hoja, columnas: int, anchos: tuple[int, ...], ultima: int) -> None  # R3, R4
```

Constantes del módulo: `_CABECERA_FILL = "1F3864"`, `_BANDAS = ("FFFFFF", "DDEBF7")`, borde
`_FINO = Side("thin", "BFBFBF")`, `_GRUESO = Side("medium", "000000")`, `_COMBINADAS = (1, 2, 6, 7, 8)`.
Son de presentación y van en código, no en `config.yaml`, para no abrir otra superficie de
configuración. D3 decidida: si negocio pide retocar los colores, son dos literales.

Pintado del Detalle, por grupo `g` con índice `n`, filas `ini..fin`:

1. Una fila por `LineaDetalle` con los 8 valores. A, B, F, G y H se escriben en **todas** las
   filas (R10).
2. Relleno `_BANDAS[n % 2]` en las 8 celdas. Borde fino, salvo el inferior de la fila `fin`,
   que es `_GRUESO` (R12).
3. Si `fin > ini`, `_combinar_con_valor` en A, B, F, G y H, con alineación vertical centrada (R11).

## 4. Formato y anchos (R4)

| Hoja | Anchos A… | Otros |
|---|---|---|
| Detalle | 34, 22, 12, 44, 13, 15, 12, 16 | — |
| Resumen | 34, 22, 90, 10, 16 | C con `wrap_text=True` y alineación arriba |

En las dos hojas: `freeze_panes = "A3"` y `auto_filter.ref = "A2:<última col><última fila>"`, con
fila mínima 2 (R3). Impresión: `page_setup.orientation = "landscape"`,
`sheet_properties.pageSetUpPr.fitToPage = True`, `page_setup.fitToWidth = 1`,
`fitToHeight = 0` y `print_title_rows = "1:2"`.

## 5. Celdas combinadas con autofiltro: evidencia de D2 = A (decidida)

`ws.merge_cells()` de openpyxl convierte las celdas no ancla en `MergedCell`, de valor `None` y
solo lectura. Al guardar, solo la primera fila del grupo tiene valor, y por eso el filtro pierde
el resto. La técnica del modelo es la contraria: **dejar el valor en todas las celdas y
declarar el rango combinado**. En openpyxl se consigue añadiendo el rango sin «limpiarlo»:

```python
from openpyxl.worksheet.merge import MergedCellRange
hoja.merged_cells.add(MergedCellRange(hoja, f"{letra}{desde}:{letra}{hasta}"))
```

El escritor (`WorksheetWriter.write_merged_cells`) emite `<mergeCell>` y conserva los `<c>` con
valor. Ojo: al **leer**, `load_workbook` sí limpia (`bind_merged_cells` llama a
`_clean_merge_range`). Por eso los tests de R10 y R11 leen el XML de la hoja, no el libro.

Prototipo desechable, generado el 2026-10-06 fuera del repositorio (`proto_f040.py` en el
scratchpad). Tiene cinco trabajadores inventados: un grupo de 4 líneas
(55/20/20/5), uno de 2, uno con `VAR-29` y `Postv-0702`, uno sin carga y uno de una línea. Se
generaron tres hojas y se abrieron en **Excel 16 por COM**, filtrando y contando filas visibles:

| Variante | Empleado = el de 4 líneas | Obra = una de las del grupo | Estado = OK | Ordenar por A |
|---|---|---|---|---|
| A: combinada con valor en todas | 4 de 4 filas | la fila sale con Empleado y Estado | todas las de los OK | error de Excel |
| Combinación normal (`merge_cells`) | **1 de 4** | la fila sale **sin** Empleado ni Estado | **solo la 1.ª** de cada grupo | error de Excel |
| B: sin combinar, banda + línea | 4 de 4 | con Empleado y Estado | todas | sí |

Conclusiones:
- A filtra igual que B y se ve como el modelo.
- La combinación normal no sirve.
- El precio de A es que no se puede ordenar con «Ordenar» de Excel, lo mismo que en el modelo
  de negocio.
- Lo que el COM no deja comprobar es la imagen: cómo se pinta una combinada cuya primera fila
  queda oculta por el filtro. Lo comprueba el humano en M1.

Riesgo de A: depende de cómo escribe openpyxl 3.1.x. No se fija la versión en
`requirements.txt`, pero un test lee el `<mergeCells>` y los `<c>` del XML: si una versión
futura limpia al escribir, se pone en rojo.

## 6. Verificación manual M1 (humano)

Con la api local (`python main.py` en `services/dedicacion-api`, BBDD local con un periodo
que tenga carga):

```powershell
curl.exe -o "$env:TEMP\f040.xlsx" "http://127.0.0.1:8090/api/v1/periodos/2026/9/export.xlsx?empresa=1"
start "$env:TEMP\f040.xlsx"
```

(O el botón «Exportar» del front local.) Qué mirar:
1. Abre sin aviso de reparación.
2. En el Detalle, filtrar por un Empleado con varias obras saca todas sus filas.
3. Filtrar por una Obra: cada fila visible enseña quién es y su Estado.
4. Filtrar Estado ≠ OK.
5. Bandas y línea gruesa entre trabajadores.
6. Resumen con «código nombre = NN%».
7. Vista previa de impresión en horizontal, a una página de ancho, con la cabecera repetida.

Resultado en `progress/`.

## 7. Tests (sin red ni BBDD)

`tests/test_f040_excel.py`. Usa `Trabajador`, `Linea` y `CuadranteTrabajador` de
`domain.models` construidos a mano. Hay dos niveles:

- **Contenido** (`contenido.py`):
  - orden conservado (R7);
  - prefijo de postventa y `VAR-29` como normal (R8);
  - sin líneas (R9);
  - «Obras» con nombre y « + » (R14);
  - Estado igual en las dos hojas (R15);
  - 99,996 → OK, que prueba que el exportador no tiene épsilon propia (R16);
  - `texto_pct` con 100, 10, 33,33 y 0,5, y nunca «E+» (R18);
  - FALTA y EXCESO (R19).
- **Libro**: `exportar()` y luego `load_workbook` para hojas, títulos, cabeceras, autofiltro,
  paneles, formatos, rellenos, bordes e impresión (R1-R6, R12, R13, R17). Además se lee con
  `zipfile` el `xl/worksheets/sheet1.xml`, para comprobar los rangos `<mergeCell>` esperados y
  que las celdas no ancla de A, B, F, G y H tienen valor (R10, R11). Un grupo de una fila no
  sale en `<mergeCells>`.
- R20: los tests de F-024 (`test_f024_r15_…` y el parametrizado R6 con `/export.xlsx`) siguen en
  verde sin tocarlos.

**Lista cerrada de tests anteriores que cambian: ninguno.** Comprobado ejecutando el
2026-10-06: `coverage run --include="infrastructure/excel/*" -m pytest tests` (586 passed) deja
`exporter.py` al 26 %. Solo se ejecutan las líneas de módulo: ningún test llama a `exportar()`, y
el único que pasa por la ruta (`test_f024_rutas_empresa.py`) usa un exportador falso.
`tests/` de la raíz no lo menciona.

## 8. Riesgos y alternativas descartadas

- **Convivencia con F-039**, que está en curso en paralelo. F-039 declara `exporter.py` como «no
  se toca» y prueba el export de `VAR-29` con el exportador falso de F-024, así que no hay
  conflicto de ficheros. Si al fusionar algún test de F-039 leyera el xlsx real, se ajusta a las
  columnas nuevas en esa fusión.
- **Fórmulas en Total y Desviación** (`=SUM(...)`): descartadas. Las cifras son las de la regla
  del 100 % (R16), y una fórmula sobre celdas combinadas o filtradas engaña.
- **Columna en blanco o «agrupar» de Excel (esquema `outline`)**: descartado. No es lo que enseña
  el modelo, y el esquema se pierde al filtrar.
- **Colores en `config.yaml`**: descartado (§3.2).
- **Ordenar en el exportador**: descartado. El orden es el del repositorio, el mismo que ve el
  cuadrante.
