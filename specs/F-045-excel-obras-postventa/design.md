# F-045 · Diseño técnico

D1-D11 decididas (`requirements.md`): D3-D9 = A; D1 y D2 las cambió el humano en la MANUAL T6
del 2026-10-08 (libro «Obras», «Postventa» y «Detalle», sin «Resumen»); D10 = A (§8); D11 = A,
la columna «Observaciones» vacía (§3.3). **D12 = A**, decidida por el humano el 2026-10-08 (la celda
también en la agregada y en «SIN CARGA», vacía); la B descartada queda en §3.3. Parte del
Excel de F-040 (`specs/F-040-excel-modelo-juan/`): se reutiliza su pintado de grupos; cambian
**qué líneas** lleva cada grupo, **qué hojas** se pintan y, desde D11, **una columna más**.

## 1. Encaje en la arquitectura y límite de servicio

- **Solo `dedicacion-api`, capa `infrastructure/excel/`.** La ruta `export.xlsx` sigue igual:
  llama a `ObtenerCuadrante` con el filtro de empresa y pasa `periodo` y `filas`
  (`list[CuadranteTrabajador]`) al exportador. Cada `Linea` trae ya `es_postventa`, `cod`,
  `descripcion` y `porcentaje`, así que no hace falta ningún dato nuevo de la API, ni ORM, ni SQL.
- **El agregado lo calcula la api**, en `contenido.py`, sumando `Decimal` sobre las líneas de la
  otra parte. Es presentación: el total del trabajador sigue siendo `CuadranteTrabajador.total` y
  el estado sigue saliendo de `domain.estados` (F-040 R16). El front no interviene, porque el
  botón «Exportar» solo descarga el fichero.
- **Observaciones (D11)** es solo formato del libro: la app no las guarda ni las lee, así que no
  hay dato, esquema, ruta ni pantalla nuevos. Guardarlas en la app sería otra feature (§8).
- **Transfer y front**: no se tocan. No hay responsabilidad nueva fuera de la api.
- **F-038** (el cuadro de mando «que sea el Excel») va detrás. Le conviene reutilizar
  `grupos_pestana` y `grupos_detalle` (§3.1) para que la pantalla y el Excel desglosen igual.

## 2. Ficheros

**Crear**: ninguno. `tests/test_f045_excel_pestanas.py` ya existe y se amplía.

**Modificar** (T1-T16 hechas, la ampliación D11 incluida)

| Ruta | Qué cambia |
|---|---|
| `services/dedicacion-api/infrastructure/excel/contenido.py` | Hecho (T2, T9). La ampliación D11 **no** lo toca: la columna no tiene contenido |
| `services/dedicacion-api/infrastructure/excel/exporter.py` | Hecho: Obras, Postventa y Detalle (T4, T9). Ampliación: columna I «Observaciones» (§3.3) |
| `services/dedicacion-api/tests/test_f045_excel_pestanas.py` | Ampliación: lista cerrada de §7.2 y dos tests nuevos (§7.3) |
| `services/dedicacion-api/tests/test_f040_excel.py` | Ampliación: lista cerrada de §7.2 |
| `docs/ARCHITECTURE.md` | Línea 79, `excel/`: añadir «, las tres con una columna Observaciones vacía para escribir» (R19) |
| `services/dedicacion-api/README.md` | Fila `export.xlsx` (línea 41): ídem, «columna Observaciones vacía en las tres hojas» (R19) |

**No se tocan**: `domain/` (ni `ports.py` ni `estados.py` ni `models.py`), `application/`,
`interface_adapters/api/routes.py` y `deps.py`, `config/config.yaml` (se reutiliza
`export.prefijo_postventa`; los rótulos de la agregada y la cabecera «Observaciones» van en
código, como los colores de F-040), `orm_models.py`, `repositories.py`, `contenido.py` (en la
ampliación), `requirements.txt`, los tests de F-024 (exportador falso que devuelve `b"xlsx"`),
`tests/test_f039_registro_var.py` (lee `[2:5]`, que la columna I no mueve), el front, el
transfer y `azure-apps/`. Sin SQL.

## 3. Clases y funciones

### 3.1 `infrastructure/excel/contenido.py` (infrastructure, puro: sin openpyxl) — hecho

```python
@dataclass(frozen=True)
class LineaDetalle:
    codigo: str
    obra: str
    nombre: str                   # descripción sin prefijo (D10, §8)
    porcentaje: Decimal | None
    agregada: bool = False        # la línea «RESTO …» de la otra parte (R7, R15)

AGREGADA_EN_OBRAS = ("POSTVENTA", "RESTO POSTVENTA")
AGREGADA_EN_POSTVENTA = ("OBRAS", "RESTO OBRAS")

def grupos_detalle(filas, prefijo) -> list[GrupoTrabajador]                   # hoja «Detalle»
def grupos_pestana(filas, prefijo, postventa: bool) -> list[GrupoTrabajador]  # Obras / Postventa
```

`grupos_pestana(filas, prefijo, postventa)` hace, por trabajador:

1. Las **propias** son las líneas con `ln.es_postventa == postventa`, en su orden y pasadas por
   `_linea_detalle` (prefijo, F-040 R8) (R5, R6). Las **otras** son las demás.
2. Si hay otras, se añade al final una `LineaDetalle(…, agregada=True)` con los rótulos de la
   pestaña y la suma de sus % arrancada en `Decimal(0)` (R7). Sin otras, nada (R8).
3. Sin líneas, la línea vacía de F-040 R9 (`_LINEA_VACIA`) (R10).
4. Total, desviación y estado salen de `_grupo`, los del trabajador completo, iguales a los de
   `grupos_detalle` (R11). Por construcción, la suma de los % del grupo es el total (R12).

`FilaResumen` y `filas_resumen` ya no existen (D2, T9).

### 3.2 `infrastructure/excel/exporter.py` (infrastructure, openpyxl) — hecho

```python
class OpenpyxlExcelExporter:
    def __init__(self, prefijo_postventa: str = "Postv-") -> None
    def exportar(self, periodo, filas) -> bytes                          # Obras, Postventa, Detalle (R1)
    def _hoja_grupos(self, hoja, nombre: str, titulo: str, grupos) -> None
```

`exportar` pinta con `_hoja_grupos` «Obras» (`grupos_pestana(…, postventa=False)`),
«Postventa» (`postventa=True`) y «Detalle» (`grupos_detalle`, título «DETALLE DE DEDICACIÓN ·
…»). `_hoja_grupos` con `grupos_detalle` **es** el `_hoja_detalle` de F-040; ninguna línea de
`grupos_detalle` es `agregada`, así que el Detalle no lleva cursiva (R15, R17).

### 3.3 Ampliación D11: columna I «Observaciones» en `exporter.py` — hecho (T13)

Todo en `exporter.py`; ni firmas nuevas ni cambios en `contenido.py`:

1. `_CABECERA_DETALLE` gana un noveno elemento, `"Observaciones"`. `_titulo_y_cabecera` ya
   pinta I2 con el relleno, la fuente y la alineación del resto de la cabecera (R20).
2. `_ANCHOS_DETALLE = (34, 22, 12, 44, 13, 15, 12, 16, 50)`. `_rematar` deriva la última columna
   de `len(anchos)`, así que el autofiltro pasa solo a `A2:I<n>` (y `A2:I2` sin trabajadores);
   la impresión no cambia de código: horizontal, una página de ancho, que ahora incluye I (R20).
3. Constantes nuevas: `_OBSERVACIONES = 9` (columna) y
   `_AJUSTE = Alignment(wrap_text=True, vertical="top")`.
4. En `_hoja_grupos`, el bucle de relleno y bordes pasa de `range(1, 9)` a
   `range(1, len(_CABECERA_DETALLE) + 1)`: I lleva la banda del grupo, `_BORDE` o
   `_BORDE_ULTIMA` como las demás. Después, `hoja.cell(r, _OBSERVACIONES).alignment = _AJUSTE`.
   **No se escribe ningún valor** en I, y `_COMBINADAS` sigue siendo `(1, 2, 6, 7, 8)`: I nunca
   se combina. La cursiva de la agregada sigue en `(3, 4, 5)`: I no la lleva (R15, R21).
5. Docstring del módulo: las tres hojas acaban en una columna «Observaciones» vacía, una celda
   por línea, para escribir en el Excel.

Con **D12 = B**, el punto 4 pintaría I solo si `not linea.agregada and linea.porcentaje is not
None`; el resto, igual. Con la A no hace falta mirar el tipo de línea.

## 4. Formato

Igual en las tres hojas: anchos `34, 22, 12, 44, 13, 15, 12, 16, 50`, `freeze_panes = "A3"`,
autofiltro `A2:I<última>` con mínimo de fila 2 e impresión horizontal a una página de ancho con
las filas 1-2 repetidas. La agregada solo cambia la fuente (cursiva) de C, D y E. La columna I:
vacía, ajuste de texto, alineada arriba, banda y bordes del grupo, sin combinar. Al escribir en
ella, Excel ajusta solo la altura de la fila (openpyxl no fija alturas). «Detalle» queda como en
F-040 más la columna I, sin cursiva.

## 5. Prototipo: filtro y combinación con la línea agregada (2026-10-07)

`proto_f045.py` (desechable, fuera del repositorio) pintó «Obras» y «Postventa» con cinco
trabajadores inventados (dos obras y una postventa; solo obras; solo postventa; sin carga; VAR
con EXCESO) y se filtró en **Excel 16 por COM** contando filas visibles con `SUBTOTAL(109, E)`.
Resultado: la combinación con valor en todas las filas de F-040 sigue funcionando con la
agregada como una fila más del grupo; filtrar un Empleado saca el grupo entero y la suma de lo
visible coincide en las dos pestañas y con su Total (R12); con Código «POSTVENTA» / «OBRAS»
(D6 = A) salen solo las agregadas, y con el Código vacío (D6 = B) se mezclaban con los «SIN
CARGA». La tabla completa, en `git show 628b9bb:specs/F-045-excel-obras-postventa/design.md` §5.
La columna I no necesita prototipo: es una columna sin combinar dentro del autofiltro, que es
lo que Excel filtra sin sorpresas; lo confirma M2.

## 6. Verificación manual (humano)

Con la api local (`python main.py` en `services/dedicacion-api`, BBDD local; octubre de 2026 es
el mes con postventa):

```powershell
curl.exe -o "$env:TEMP\f045.xlsx" "http://127.0.0.1:8090/api/v1/periodos/2026/10/export.xlsx?empresa=1"
start "$env:TEMP\f045.xlsx"
```

**M1** (T6, cumplida el 2026-10-08, «todo ok»): hojas Obras, Postventa y Detalle sin aviso de
reparación; filtro por Empleado con la misma Suma de E en las tres; Código = POSTVENTA / OBRAS
saca solo las agregadas; Estado distinto de OK; bandas, línea gruesa y cursiva; Detalle como
F-040.

**M2** (T16, la columna, mismo fichero):

1. En las tres hojas, la última columna es «Observaciones», con la cabecera azul y ancha.
2. Escribir un texto largo (dos o tres frases) en una celda de I: se ajusta en varias líneas y
   la fila crece; la celda es de una sola fila, también en un grupo de varias.
3. Filtro de Observaciones → «(No vacías)»: sale solo esa fila. Quitar el filtro.
4. Vista previa de impresión: una página de ancho, con la columna I dentro y legible.

El resultado se anota en `progress/`.

## 7. Tests (sin red ni BBDD)

### 7.1 Lo ya hecho (T1-T11)

Los tests de F-045 y las adaptaciones de F-040 y F-039 al libro Obras, Postventa y Detalle
(6 tests de F-045, 17 de F-040 —13 adaptados y 4 borrados del Resumen— y 1 de F-039) están
implementados y revisados (review 3). Su lista cerrada, en
`git show 628b9bb:specs/F-045-excel-obras-postventa/design.md` §7, y la traza en
`progress/impl_F-045.md` §8.

### 7.2 Lista cerrada de tests anteriores que cambian por la columna I (D11)

Recalculada el 2026-10-08 contra el código de la rama (HEAD `628b9bb`). Causa común: con I2
escrita, `hoja.max_column` pasa a 9, así que `hoja[n]` devuelve **nueve** celdas en cualquier
fila (con D12 = A o B por igual) y el autofiltro llega a I. Ninguna aserción se relaja.

| Fichero · test | Cambio |
|---|---|
| test_f045 · constante `_CABECERA` | Añade `"Observaciones"` (la usan r3 y r17) |
| test_f045 · `test_f045_r3_cabecera_autofiltro_paneles_anchos_e_impresion` | `A2:H11` → `A2:I11`; vacío `A2:H2` → `A2:I2`; anchos sobre `"ABCDEFGHI"` con el 50 |
| test_f045 · `test_f045_r4_r10_filas_de_la_pestana_obras` | `obras[9]][2:]` acaba en `"SIN CARGA", None]` |
| test_f045 · `test_f045_r4_r10_filas_de_la_pestana_postventa` | `postv[8]][2:]` acaba en `"SIN CARGA", None]` |
| test_f045 · `test_f045_r17_detalle_igual_que_en_f040` | `A2:H13` → `A2:I13` (la cabecera, por `_CABECERA`) |
| test_f040 · `test_f040_r3_autofiltro_y_paneles` | `A2:H12` → `A2:I12`; vacío `A2:H2` → `A2:I2` |
| test_f040 · `test_f040_r4_impresion_y_anchos` | Las tres tuplas ganan el 50 y `letras` pasa a `"ABCDEFGHI"` |
| test_f040 · `test_f040_r6_cabecera_del_detalle_sin_obra_codigo` | La lista acaba en `"Observaciones"` |
| test_f040 · `test_f040_r9_sin_carga_en_el_libro` | `fila[2:]` acaba en `"SIN CARGA", None]` |

Las de r3 de F-045 y r4 de F-040 (anchos) no fallarían sin tocarlas, porque solo miran A-H: se
amplían para que la anchura de I quede fijada también en los tests de F-040 R4. Los demás tests
de los tres ficheros **no cambian** y siguen en verde: r5 de F-040 (recorre toda la fila 2: ya
exige que I2 tenga el formato de cabecera), r15 de F-045 (recorre todas las celdas: ya exige I
sin cursiva), r13 de F-045 y r11 de F-040 (igualdad exacta de rangos combinados: ya exigen I sin
combinar), r16 (sin fórmulas), las bandas de r14 y r12 (A-H) y `test_f039_r21_…` (`[2:5]`). Los
docstrings de los dos módulos de test mencionan la columna I.

### 7.3 Tests nuevos en `tests/test_f045_excel_pestanas.py`

| Test | Qué fija |
|---|---|
| `test_f045_r20_observaciones_a_la_derecha_en_las_tres_hojas` | En las tres hojas: `I2 == "Observaciones"`, relleno `1F3864`, negrita blanca, ancho 50, autofiltro `A2:I<max_row>` (y `A2:I2` con `_exportar([])`), `fitToWidth == 1` |
| `test_f045_r21_celda_de_observaciones_vacia_por_linea` | En las tres hojas (`_GRUPOS` y `_GRUPOS_DETALLE`), por `_xml_hoja`: para cada fila de 3 a la última, I existe con `v is None`, la banda de su grupo y borde inferior `medium` en la última del grupo y `thin` en las demás; por openpyxl, `wrap_text` y `vertical == "top"`, sin cursiva; ningún rango combinado empieza por `I` |

Con D12 = B, r21 cambiaría a: I con formato solo en las filas de línea real, y en las agregadas
(`_AGREGADAS`) y la «SIN CARGA» (Obras 9, Postventa 8, Detalle 10) sin relleno.

## 8. Riesgos y alternativas descartadas

- **Lo escrito en Observaciones no vuelve a la app**: vive en ese fichero. Un export nuevo del
  mismo mes sale con la columna vacía, y lo escrito en «Obras» no aparece en «Detalle» (son
  tablas distintas). Es lo que el humano eligió (D11 = A), avisado de que la app no guarda
  observaciones. Si negocio necesita conservarlas, es otra feature (dato por línea en la BBDD,
  API, front y export): no se diseña aquí.
- **Celda de Observaciones combinada por trabajador**: descartada. El humano pidió una por
  línea (sin combinar), y una combinada solo guarda texto en la primera fila: al filtrar se
  perdería en las demás (F-040 §5).
- **Impresión**: con I dentro, el ancho total pasa de 168 a 218 caracteres y la escala de
  impresión a una página de ancho baja un ~23 %. Se acepta (el humano pidió la columna dentro de
  la tabla); M2 mira que sea legible. Alternativa, si no lo es: área de impresión `A:H`.
- **Quien lea la hoja «Resumen»** (Juan la pidió en F-040) deja de tenerla; el humano lo decidió
  avisado (D2). Quien lea el libro **por posición** ve Obras en la primera; Detalle conserva su
  nombre. Quien lo lea **por columnas** no se ve afectado: I se añade a la derecha de todo.
- **D10 (DECIDIDA por el humano el 2026-10-08: A) · `LineaDetalle.nombre`.** Sin el Resumen,
  nadie lo lee; se conserva (la descripción sin prefijo, barata, y le servirá a F-038).
- **Conservar `filas_resumen` sin pintarlo**: descartado. Código sin consumidor; git lo guarda.
- **Postventa intercalada en el orden de entrada**: al separarla por `es_postventa` se conserva
  el orden relativo de cada parte, sin reordenar (F-040 R7).
- **Fórmulas** (`=SUMA` o `SUBTOTALES` en la agregada): descartadas por F-040 R16. Además, la
  fórmula de la agregada apuntaría a filas de la otra hoja, y se rompe al filtrar.
- **Esquema «agrupar» de Excel (outline) para plegar la otra parte**: descartado, por lo mismo
  que en F-040 §8: se pierde al filtrar y no es lo que se pidió.
- **Rótulos en `config.yaml`** (también «Observaciones»): descartado, para no abrir otra
  superficie de configuración.
- **Un código de obra que se llame «OBRAS» o «POSTVENTA»**: hoy los códigos son números,
  `VAR-NN` o códigos con letras de Sigrid, y el campo `agregada` (no el texto) decide la
  cursiva. Si apareciera uno, el filtro por Código los mezclaría; se acepta.
