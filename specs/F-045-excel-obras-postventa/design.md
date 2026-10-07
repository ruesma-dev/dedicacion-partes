# F-045 · Diseño técnico

Escrito con D1-D9 = A (recomendadas, **pendientes del humano**: `requirements.md`). Parte del
Excel de F-040 (`specs/F-040-excel-modelo-juan/`): se reutiliza su pintado de grupos y solo
cambia **qué líneas** lleva cada grupo y **cuántas hojas** se pintan.

## 1. Encaje en la arquitectura y límite de servicio

- **Solo `dedicacion-api`, capa `infrastructure/excel/`.** La ruta `export.xlsx` sigue igual:
  llama a `ObtenerCuadrante` con el filtro de empresa y pasa `periodo` y `filas`
  (`list[CuadranteTrabajador]`) al exportador. Cada `Linea` trae ya `es_postventa`, `cod`,
  `descripcion` y `porcentaje`, así que no hace falta ningún dato nuevo de la API, ni ORM, ni SQL.
- **El agregado lo calcula la api**, en `contenido.py`, sumando `Decimal` sobre las líneas de la
  otra parte. Es presentación: el total del trabajador sigue siendo `CuadranteTrabajador.total` y
  el estado sigue saliendo de `domain.estados` (F-040 R16). El front no interviene, porque el
  botón «Exportar» solo descarga el fichero.
- **Transfer y front**: no se tocan. No hay responsabilidad nueva fuera de la api.
- **F-038** (el cuadro de mando «que sea el Excel») va detrás. Le conviene reutilizar
  `grupos_pestana` (§3.1) para que la pantalla y el Excel desglosen igual. Eso no se diseña
  aquí.

## 2. Ficheros

**Crear**

| Ruta | Qué |
|---|---|
| `services/dedicacion-api/tests/test_f045_excel_pestanas.py` | Tests `test_f045_rN_…` de R1-R18 (§7) |

**Modificar**

| Ruta | Qué cambia |
|---|---|
| `services/dedicacion-api/infrastructure/excel/contenido.py` | `LineaDetalle.agregada`, `grupos_pestana`, constantes de la agregada; `grupos_detalle` sin cambio de comportamiento (§3.1) |
| `services/dedicacion-api/infrastructure/excel/exporter.py` | `exportar` pinta Obras, Postventa y Resumen; `_hoja_detalle` → `_hoja_grupos(hoja, nombre, titulo, grupos)`; cursiva de la agregada (§3.2) |
| `services/dedicacion-api/tests/test_f040_excel.py` | Solo la lista cerrada de §7 |
| `services/dedicacion-api/tests/test_f039_registro_var.py` | `test_f039_r21_…`: `libro["Detalle"]` → `libro["Obras"]` (§7) |
| `docs/ARCHITECTURE.md` | Línea 78-79, `excel/`: «Obras y Postventa agrupadas por trabajador, cada una con la otra parte en una línea, y Resumen» (R19) |
| `services/dedicacion-api/README.md` | Fila `export.xlsx` (línea 41) (R19) |

**No se tocan**: `domain/` (ni `ports.py` ni `estados.py` ni `models.py`), `application/`,
`interface_adapters/api/routes.py` y `deps.py`, `config/config.yaml` (se reutiliza
`export.prefijo_postventa`; los rótulos de la agregada van en código, como los colores de
F-040), `orm_models.py`, `repositories.py` (el orden de las líneas no cambia),
`requirements.txt`, `tests/test_f024_rutas_empresa.py`, el front, el transfer y `azure-apps/`.
Sin SQL.

## 3. Clases y funciones

### 3.1 `infrastructure/excel/contenido.py` (infrastructure, puro: sin openpyxl)

```python
@dataclass(frozen=True)
class LineaDetalle:
    codigo: str
    obra: str
    nombre: str
    porcentaje: Decimal | None
    agregada: bool = False        # NUEVO: la línea «RESTO …» de la otra parte (R7, R15)

#: Rótulos (Código, Obra) de la agregada según la pestaña (D6 = A).
AGREGADA_EN_OBRAS = ("POSTVENTA", "RESTO POSTVENTA")
AGREGADA_EN_POSTVENTA = ("OBRAS", "RESTO OBRAS")

def grupos_pestana(
    filas: list[CuadranteTrabajador], prefijo: str, postventa: bool
) -> list[GrupoTrabajador]
```

`grupos_pestana(filas, prefijo, postventa)` hace, por trabajador y en el orden de entrada:

1. Parte del `GrupoTrabajador` de `grupos_detalle([fila], prefijo)` o de un helper común
   `_grupo(fila, lineas)`, para no duplicar el cálculo de total, desviación y estado (R11).
   Se reutiliza el helper privado `_linea_detalle(ln, prefijo)`, extraído de la comprensión
   actual de `grupos_detalle`.
2. Las **propias** son las líneas con `ln.es_postventa == postventa`, en su orden (R5, R6).
   Las **otras** son las demás.
3. Si hay otras, se añade al final
   `LineaDetalle(codigo=…, obra=…, nombre="", porcentaje=sum(ln.porcentaje for ln in otras), agregada=True)`
   con los rótulos de la pestaña (R7). La suma se arranca en `Decimal("0")`, como
   `CuadranteTrabajador.total`.
4. Si no hay propias ni otras, la línea vacía de F-040 R9 (`_LINEA_VACIA`) (R10).
5. Total, desviación y estado son los del trabajador completo, iguales a los de
   `grupos_detalle` (R11). Por construcción, la suma de los % del grupo es el total (R12).

`grupos_detalle` y `filas_resumen` conservan su comportamiento: el Resumen sigue saliendo de
`filas_resumen(grupos_detalle(...))` (R17), y los tests de contenido de F-040 no cambian.

### 3.2 `infrastructure/excel/exporter.py` (infrastructure, openpyxl)

```python
class OpenpyxlExcelExporter:
    def __init__(self, prefijo_postventa: str = "Postv-") -> None       # sin cambio
    def exportar(self, periodo, filas) -> bytes                          # 3 hojas (R1)
    def _hoja_grupos(self, hoja, nombre: str, titulo: str, grupos) -> None   # antes _hoja_detalle
    def _hoja_resumen(self, hoja, periodo, resumen) -> None              # sin cambio
```

- `exportar` hace `libro.active` → «Obras» con `grupos_pestana(filas, p, False)`,
  `create_sheet()` → «Postventa» con `grupos_pestana(filas, p, True)` y `create_sheet("Resumen")`
  con `filas_resumen(grupos_detalle(filas, p))`. Los títulos son `f"OBRAS · {_mes(periodo)}"` y
  `f"POSTVENTA · {_mes(periodo)}"` (R2).
- `_hoja_grupos` es el `_hoja_detalle` de F-040 parametrizado por nombre y título, con la misma
  cabecera `_CABECERA_DETALLE`, los mismos anchos, bandas, bordes y combinadas (R3, R13, R14).
  La banda se cuenta por hoja (`n` del `enumerate` de esa hoja).
- Única novedad del pintado: si `linea.agregada`, las celdas 3, 4 y 5 llevan
  `Font(italic=True)` en una constante `_CURSIVA` (R15). El % se escribe con `_celda_pct`, sin
  fórmula (R16).
- Se actualiza el docstring del módulo (tres hojas).

## 4. Formato

Igual que el Detalle de F-040 §4 en las dos pestañas: anchos `34, 22, 12, 44, 13, 15, 12, 16`,
`freeze_panes = "A3"`, autofiltro `A2:H<última>` con mínimo de fila 2 e impresión horizontal a una
página de ancho con las filas 1-2 repetidas. El Resumen no cambia. La agregada solo cambia la
fuente (cursiva) de C, D y E.

## 5. Prototipo: filtro y combinación con la línea agregada

`proto_f045.py` (desechable, en el scratchpad del 2026-10-07, fuera del repositorio) usa
`grupos_detalle` y los helpers reales de `exporter.py` y pinta «Obras» y «Postventa» con cinco
trabajadores inventados: ALFA (dos obras y una postventa), BETA (solo obras), GAMMA (solo
postventa), DELTA (sin carga) y EPSILON (`VAR-29` y dos postventas, EXCESO 10 %). Se sacaron dos
variantes de D6, se abrieron en **Excel 16 por COM** y se filtró contando filas visibles, con
`SUBTOTAL(109, E)` como suma de lo visible:

| Filtro | Obras | Postventa |
|---|---|---|
| Empleado = ALFA | 3 filas (2 obras + RESTO POSTVENTA), suma 100 % | 2 filas (Postv- + RESTO OBRAS), suma 100 % |
| Empleado = GAMMA | 1 fila (RESTO POSTVENTA 100 %) | 2 filas, suma 100 % |
| Empleado = EPSILON | 2 filas (VAR-29 + RESTO POSTVENTA), suma 110 % | 3 filas, suma 110 % |
| Empleado = DELTA | 1 fila SIN CARGA | 1 fila SIN CARGA |
| Estado = OK | 6 filas, todas con Empleado y Estado | 5 filas, ídem |
| Código = POSTVENTA / OBRAS (D6 = A) | solo las 3 agregadas | solo las 3 agregadas |
| Código = (Vacías) (D6 = B) | 3 agregadas **+ DELTA SIN CARGA** | ídem |

Conclusiones:

- La combinación con valor en todas las filas de F-040 (§5 de su diseño) sigue funcionando con la
  agregada como una fila más del grupo: el rango combinado de A3 es `A3:A5` en Obras y `A3:A4`
  en Postventa, y el filtro por Empleado devuelve el grupo entero.
- La suma de lo visible por trabajador coincide en las dos pestañas y con su Total (R12).
- Con el Código vacío (D6 = B), las agregadas no se separan de los SIN CARGA: por eso se
  recomienda D6 = A.
- No se comprobó por COM la imagen de la cursiva ni cómo se ve una combinada con la primera fila
  oculta. Eso queda para M1.

## 6. Verificación manual M1 (humano)

Con la api local (`python main.py` en `services/dedicacion-api`, BBDD local con un periodo que
tenga postventa):

```powershell
curl.exe -o "$env:TEMP\f045.xlsx" "http://127.0.0.1:8090/api/v1/periodos/2026/10/export.xlsx?empresa=1"
start "$env:TEMP\f045.xlsx"
```

Qué mirar:

1. Abre sin aviso de reparación, con las hojas Obras, Postventa y Resumen.
2. En las dos pestañas, filtrar un Empleado con obras y postventa: sale el grupo entero, y la
   barra de estado de Excel (Suma de la columna E) da lo mismo en las dos.
3. En Obras, Código = POSTVENTA; en Postventa, Código = OBRAS: solo salen las agregadas.
4. Estado ≠ OK: filas completas.
5. Aspecto: bandas, línea gruesa y cursiva de la agregada.
6. El Resumen, como en F-040.

El resultado se anota en `progress/`.

## 7. Tests (sin red ni BBDD)

`tests/test_f045_excel_pestanas.py`. Usa datos inventados con `Trabajador`, `Linea` y
`CuadranteTrabajador` construidos a mano, con los mismos cinco casos que el prototipo (§5). Para
las combinadas reutiliza `_xml_hoja` con `from tests.test_f040_excel import _xml_hoja`, que tiene
precedente en `test_f039` → `test_f029`.

- **Contenido** (`grupos_pestana`): propias en su orden y con prefijo (R5, R6); una sola
  agregada, al final, con sus rótulos y la suma exacta en `Decimal` (R7); ninguna sin otra
  parte (R8); solo la agregada (R9); SIN CARGA (R10); total, desviación y estado iguales a los de
  `grupos_detalle` (R11); mismos trabajadores y orden en las dos pestañas (R4); suma del grupo =
  total, en las dos (R12, como propiedad sobre los cinco casos y uno con decimales); `VAR-29` en
  Obras y sumado en RESTO OBRAS (R5, D5); prefijo «PV_» (R18).
- **Libro**: `sheetnames`, títulos y enero (R1, R2); cabecera, autofiltro, paneles, anchos e
  impresión de las dos pestañas (R3); filas de cada pestaña (R4-R10); con `_xml_hoja`, valores
  en todas las filas y `<mergeCell>` esperados, agregada incluida (R13); bandas por hoja y borde
  `medium` (R14); cursiva solo en C, D y E de la agregada (R15); fracción y formato `0%` o
  `0.00%` del agregado, sin fórmulas (R16); Resumen igual que el de F-040 con los mismos datos
  (R17).

**Lista cerrada de tests anteriores que cambian (con D1 = A).** Comprobado leyendo
`test_f040_excel.py` con su muestra. En la hoja Obras, GAMMA pasa de `VAR-29` + `Postv-0702` a
`VAR-29` + RESTO POSTVENTA: mismos grupos y filas (3-6, 7-8, 9-10, 11 y 12), así que casi todo
es el nombre de la hoja.

| Test | Cambio |
|---|---|
| `test_f040_r1_dos_hojas_detalle_y_resumen` | `["Obras", "Postventa", "Resumen"]` |
| `test_f040_r2_titulo_en_fila_1_cabecera_en_2_datos_desde_3` | `"Detalle"` → `"Obras"` y títulos «OBRAS · …» (también enero) |
| `test_f040_r3_autofiltro_y_paneles` | `libro["Detalle"]` → `libro["Obras"]` |
| `test_f040_r4_impresion_y_anchos` | clave `"Detalle"` del dict de anchos → `"Obras"` y `"Postventa"` |
| `test_f040_r6_cabecera_del_detalle_sin_obra_codigo` | `"Detalle"` → `"Obras"` |
| `test_f040_r7_r8_filas_del_detalle_en_orden_y_con_su_codigo` | `"Obras"`; C10 `"POSTVENTA"`, D10 `"RESTO POSTVENTA"` (lo de `Postv-` pasa a test_f045) |
| `test_f040_r9_sin_carga_en_el_libro` | `"Detalle"` → `"Obras"` |
| `test_f040_r11_combinadas_solo_en_grupos_de_varias_filas` | `"Obras"`; el «Resumen sin combinadas» pasa de `sheet2` a `sheet3` |
| `test_f040_r13_resumen_una_fila_por_trabajador_sin_bandas` | `_xml_hoja(contenido, 2)` → `3` |
| `test_f040_r16_99996_sale_ok_y_desviacion_cero_en_el_libro` | `"Detalle"` → `"Obras"` |
| `test_f040_r17_fraccion_y_formato_segun_sea_entero` | `"Detalle"` → `"Obras"` (mismos valores) |
| `test_f039_r21_el_excel_lleva_el_codigo_de_la_entrada` | `libro["Detalle"]` → `libro["Obras"]` |

No cambian: los tests de contenido de F-040 (r7, los dos r8, r9, r14, r15, r16, r17, r18 y r19
sobre `contenido.py`), y del libro r5, r10, r12, r14_r15, r16_sin_formulas y r18. Tampoco los de
F-024. Las aserciones no se relajan: solo cambian el nombre o el índice de la hoja y las dos
celdas de GAMMA. El docstring del módulo de test_f040 se ajusta («Detalle» → «Obras»).

## 8. Riesgos y alternativas descartadas

- **Quien lea el libro por posición o por el nombre «Detalle»** (macros o consultas de negocio)
  se rompe con D1 = A. F-020 ya dejó escrito que la plantilla solo la lee negocio; M1 lo
  confirma con el humano. Si no, D1 = B.
- **Postventa intercalada en el orden de entrada**: al separarla por `es_postventa` se conserva
  el orden relativo de cada parte, sin reordenar (F-040 R7).
- **Fórmulas** (`=SUMA` o `SUBTOTALES` en la agregada): descartadas por F-040 R16. Además, la
  fórmula de la agregada apuntaría a filas de la otra hoja, y se rompe al filtrar.
- **Esquema «agrupar» de Excel (outline) para plegar la otra parte**: descartado, por lo mismo
  que en F-040 §8: se pierde al filtrar y no es lo que se pidió.
- **Rótulos en `config.yaml`**: descartado, para no abrir otra superficie de configuración. Son
  dos tuplas en `contenido.py`.
- **Un código de obra que se llame «OBRAS» o «POSTVENTA»**: hoy los códigos son números,
  `VAR-NN` o códigos con letras de Sigrid, y el campo `agregada` (no el texto) decide la
  cursiva. Si apareciera uno, el filtro por Código los mezclaría; se acepta.
