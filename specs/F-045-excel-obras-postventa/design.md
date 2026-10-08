# F-045 · Diseño técnico

D1-D9 decididas (`requirements.md`): D3-D9 = A; D1 y D2 las cambió el humano en la MANUAL T6
del 2026-10-08 (libro «Obras», «Postventa» y «Detalle», sin «Resumen»). D10 está **abierta**
(§8). Parte del Excel de F-040 (`specs/F-040-excel-modelo-juan/`): se reutiliza su pintado de
grupos; cambian **qué líneas** lleva cada grupo y **qué hojas** se pintan.

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
  `grupos_pestana` y `grupos_detalle` (§3.1) para que la pantalla y el Excel desglosen igual.
  Eso no se diseña aquí.

## 2. Ficheros

**Crear**: ninguno más. `tests/test_f045_excel_pestanas.py` ya existe (T1, T3) y se modifica.

**Modificar**

| Ruta | Qué cambia |
|---|---|
| `services/dedicacion-api/infrastructure/excel/contenido.py` | Hecho: `LineaDetalle.agregada`, `grupos_pestana`, rótulos. Cambio: se borran `FilaResumen` y `filas_resumen` (D2) y se ajusta el docstring (§3.1) |
| `services/dedicacion-api/infrastructure/excel/exporter.py` | `exportar` pinta Obras, Postventa y **Detalle**; se borran `_hoja_resumen`, `_CABECERA_RESUMEN` y `_ANCHOS_RESUMEN` (§3.2) |
| `services/dedicacion-api/tests/test_f045_excel_pestanas.py` | Lista cerrada de §7.1 |
| `services/dedicacion-api/tests/test_f040_excel.py` | Lista cerrada de §7.2: casi todo vuelve a su forma de `dev` |
| `services/dedicacion-api/tests/test_f039_registro_var.py` | `test_f039_r21_…` (§7.3) |
| `docs/ARCHITECTURE.md` | Línea 79, `excel/`: «Obras y Postventa agrupadas por trabajador, cada una con la otra parte en una línea, y Detalle con todas las líneas» (R19) |
| `services/dedicacion-api/README.md` | Fila `export.xlsx` (línea 41): Obras, Postventa y Detalle; fuera «Resumen con "código nombre = NN%"» (R19) |

**No se tocan**: `domain/` (ni `ports.py` ni `estados.py` ni `models.py`), `application/`,
`interface_adapters/api/routes.py` y `deps.py`, `config/config.yaml` (se reutiliza
`export.prefijo_postventa`; los rótulos de la agregada van en código, como los colores de
F-040), `orm_models.py`, `repositories.py` (el orden de las líneas no cambia),
`requirements.txt`, los tests de F-024 (`test_f024_rutas_empresa.py` usa un exportador falso
que devuelve `b"xlsx"`: ningún test de F-024 lee una hoja), el front, el transfer y `azure-apps/`.
Sin SQL.

## 3. Clases y funciones

### 3.1 `infrastructure/excel/contenido.py` (infrastructure, puro: sin openpyxl)

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

def grupos_detalle(filas, prefijo) -> list[GrupoTrabajador]               # sin cambio (R17)
def grupos_pestana(filas, prefijo, postventa: bool) -> list[GrupoTrabajador]  # sin cambio
```

`grupos_pestana(filas, prefijo, postventa)` (ya implementada, no cambia) hace, por trabajador:

1. Las **propias** son las líneas con `ln.es_postventa == postventa`, en su orden y pasadas por
   `_linea_detalle` (prefijo, F-040 R8) (R5, R6). Las **otras** son las demás.
2. Si hay otras, se añade al final una `LineaDetalle(…, agregada=True)` con los rótulos de la
   pestaña y la suma de sus % arrancada en `Decimal(0)` (R7). Sin otras, nada (R8).
3. Sin líneas, la línea vacía de F-040 R9 (`_LINEA_VACIA`) (R10).
4. Total, desviación y estado salen de `_grupo`, los del trabajador completo, iguales a los de
   `grupos_detalle` (R11). Por construcción, la suma de los % del grupo es el total (R12).

**Cambio (D2):** se borran `FilaResumen` y `filas_resumen`, que no tienen otro consumidor que
la hoja Resumen. Se quedan `texto_pct` (lo usa `texto_estado`) y `es_entero` (lo usa el
exportador). El docstring del módulo deja de citar el Resumen: `grupos_detalle` es el de la
hoja «Detalle».

### 3.2 `infrastructure/excel/exporter.py` (infrastructure, openpyxl)

```python
class OpenpyxlExcelExporter:
    def __init__(self, prefijo_postventa: str = "Postv-") -> None       # sin cambio
    def exportar(self, periodo, filas) -> bytes                          # Obras, Postventa, Detalle (R1)
    def _hoja_grupos(self, hoja, nombre: str, titulo: str, grupos) -> None   # sin cambio
```

- `exportar` hace `libro.active` → «Obras» con `grupos_pestana(filas, p, postventa=False)`,
  `create_sheet()` → «Postventa» con `grupos_pestana(filas, p, postventa=True)` y
  `create_sheet()` → «Detalle» con `_hoja_grupos(hoja, "Detalle",
  f"DETALLE DE DEDICACIÓN · {_mes(periodo)}", grupos_detalle(filas, p))` (R1, R2, R17).
- `_hoja_grupos` con `grupos_detalle` **es** el `_hoja_detalle` de F-040: misma cabecera, anchos,
  bandas, bordes, combinadas y remate. Ninguna línea de `grupos_detalle` es `agregada`, así que el
  Detalle no lleva cursiva (R15, R17). No hace falta código propio para la hoja.
- Se borran `_hoja_resumen`, `_CABECERA_RESUMEN`, `_ANCHOS_RESUMEN` y las importaciones de
  `FilaResumen` y `filas_resumen`. `_titulo_y_cabecera`, `_rematar` y `_celda_pct` no cambian.
- El docstring del módulo pasa a: «Obras» y «Postventa» (como hoy) y «Detalle»: todas las líneas
  agrupadas por trabajador, la postventa intercalada, como F-040. Sin Resumen.

## 4. Formato

Igual que el Detalle de F-040 §4 en las tres hojas: anchos `34, 22, 12, 44, 13, 15, 12, 16`,
`freeze_panes = "A3"`, autofiltro `A2:H<última>` con mínimo de fila 2 e impresión horizontal a una
página de ancho con las filas 1-2 repetidas. La agregada solo cambia la fuente (cursiva) de C,
D y E. «Detalle» queda como en F-040, sin cursiva.

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

Conclusiones: la combinación con valor en todas las filas de F-040 sigue funcionando con la
agregada como una fila más del grupo (`A3:A5` en Obras, `A3:A4` en Postventa); la suma de lo
visible por trabajador coincide en las dos pestañas y con su Total (R12); con el Código vacío
(D6 = B) las agregadas no se separan de los SIN CARGA. «Detalle» no necesita prototipo: es la
hoja de F-040, ya validada en su M1.

## 6. Verificación manual M1 (humano)

Con la api local (`python main.py` en `services/dedicacion-api`, BBDD local; octubre de 2026 es
el mes con postventa):

```powershell
curl.exe -o "$env:TEMP\f045.xlsx" "http://127.0.0.1:8090/api/v1/periodos/2026/10/export.xlsx?empresa=1"
start "$env:TEMP\f045.xlsx"
```

Qué mirar:

1. Abre sin aviso de reparación, con las hojas Obras, Postventa y Detalle, en ese orden, y sin
   Resumen.
2. En las tres hojas, filtrar un Empleado con obras y postventa: sale el grupo entero, y la
   barra de estado de Excel (Suma de la columna E) da lo mismo en las tres.
3. En Obras, Código = POSTVENTA; en Postventa, Código = OBRAS: solo salen las agregadas.
4. Estado distinto de OK: filas completas (en octubre, solo los «SIN CARGA»).
5. Aspecto: bandas, línea gruesa y cursiva de la agregada.
6. «Detalle», como el de F-040: título «DETALLE DE DEDICACIÓN · Octubre 2026», la postventa
   intercalada con `Postv-`, sin líneas «RESTO …» ni cursiva.

El resultado se anota en `progress/`.

## 7. Tests (sin red ni BBDD)

Recalculado el 2026-10-08 contra el código de la rama (HEAD `77d9496`). Las aserciones no se
relajan: lo que se quita es lo que leía la hoja Resumen o probaba `filas_resumen`, que dejan de
existir (D2). Detalle es ahora `sheet3.xml` (`_xml_hoja(contenido, 3)`), detrás de Obras y
Postventa; se recomienda una constante `_HOJA_DETALLE = 3` en test_f040. Los nombres de los tests
de F-040 se conservan (trazabilidad con su spec).

### 7.1 `tests/test_f045_excel_pestanas.py`

| Test | Cambio |
|---|---|
| `_N_HOJA` y constantes | `"Resumen": 3` → `"Detalle": 3`; nuevo `_GRUPOS_DETALLE = [(3, 5), (6, 7), (8, 9), (10, 10), (11, 13)]`; fuera la importación de `filas_resumen` |
| `test_f045_r1_tres_hojas_obras_postventa_y_resumen` | Pasa a `…_y_detalle`: `["Obras", "Postventa", "Detalle"]`, también vacío |
| `test_f045_r2_titulos_cabecera_en_2_y_datos_desde_3` | Título de Detalle «DETALLE DE DEDICACIÓN · Septiembre 2026» en vez del Resumen; enero, las tres |
| `test_f045_r11_…_iguales_en_las_tres_hojas` | Compara A, F, G y H de la primera fila de cada grupo con las de `_GRUPOS_DETALLE` en Detalle, no con el Resumen |
| `test_f045_r13_…_combinadas_con_la_agregada` | La última línea (Resumen sin combinadas) pasa a: las combinadas de Detalle son exactamente las de `_GRUPOS_DETALLE` en A, B, F, G y H |
| `test_f045_r17_resumen_igual_que_en_f040` | Pasa a `test_f045_r17_detalle_igual_que_en_f040`: título, cabecera, `max_row == 13`, autofiltro `A2:H13`; C, D y E de las filas 3-13 iguales a `grupos_detalle(_muestra(), _PREFIJO)` (Postv- intercalada, ningún «POSTVENTA» / «RESTO …»); A, F y H por grupo; bandas por `_GRUPOS_DETALLE` |
| `test_f045_r18_el_prefijo_…_llega_al_libro` | La línea del Resumen pasa a `libro["Detalle"]["C5"].value == "PV_0702"` |

Sin cambio: los tests de contenido (r4-r12, r18), r3, los dos r4_r10, r12 del libro, r14, r15
(con `_AGREGADAS.get(hoja.title, set())` ya exige Detalle sin cursiva: R15) y r16. El docstring
del módulo: «hojas» incluye Detalle (R17).

### 7.2 `tests/test_f040_excel.py`

| Test | Cambio |
|---|---|
| `test_f040_r1_dos_hojas_detalle_y_resumen` | `["Obras", "Postventa", "Detalle"]` |
| `test_f040_r2_titulo_en_fila_1_cabecera_en_2_datos_desde_3` | Detalle como en `dev` (título, `max_row == 12`, enero); fuera las tres del Resumen; el bucle de formato pasa de `(det, res)` a `libro.worksheets` |
| `test_f040_r3_autofiltro_y_paneles` | Detalle como en `dev` (`A2:H12`, vacío `A2:H2`); fuera las dos del Resumen |
| `test_f040_r4_impresion_y_anchos` | Claves `"Obras"`, `"Postventa"` y `"Detalle"` con los anchos del Detalle; sin `"Resumen"` |
| `test_f040_r6_…`, `test_f040_r9_sin_carga_en_el_libro` | Como en `dev` (`"Detalle"`) |
| `test_f040_r7_r8_filas_del_detalle_en_orden_y_con_su_codigo` | Como en `dev`: C10 `Postv-0702`, D10 `Postv-Hotel Inventado` |
| `test_f040_r10_…`, `test_f040_r12_…` | `_xml_hoja(…, 1)` → `3` (no cambiaron en F-045; ahora sí) |
| `test_f040_r11_combinadas_solo_en_grupos_de_varias_filas` | `_xml_hoja(contenido, 3)` y `libro["Detalle"]`; fuera la última línea (Resumen sin combinadas) |
| `test_f040_r16_99996_sale_ok_y_desviacion_cero_en_el_libro` | `"Detalle"` y `_xml_hoja(contenido, 3)` |
| `test_f040_r17_fraccion_y_formato_segun_sea_entero` | `"Detalle"`; fuera `res["D4"]` y `res2["D3"]` |
| `test_f040_r18_ningun_texto_en_notacion_cientifica` | `"0105 Obra Ficticia Centro = 100%"` (texto del Resumen) → `"EXCESO 10%"` (Estado de GAMMA) |
| `test_f040_r13_resumen_una_fila_por_trabajador_sin_bandas` | Se borra |
| `test_f040_r14_r15_obras_total_y_estado_en_el_resumen` | Se borra |
| `test_f040_r14_obras_con_codigo_nombre_y_mas` (contenido) | Se borra (`filas_resumen`) |
| `test_f040_r15_resumen_con_total_y_el_mismo_estado_que_el_detalle` (contenido) | Se borra |

Sin cambio: contenido r7, los dos r8, r9, r16, r17_es_entero, r18 (`texto_pct`) y r19; libro r5
y r16_sin_formulas. El docstring del módulo: Detalle es la tercera hoja (`sheet3.xml`) y no hay
Resumen; fuera la importación de `filas_resumen`.

### 7.3 `tests/test_f039_registro_var.py`

`test_f039_r21_el_excel_lleva_el_codigo_de_la_entrada`: `libro["Obras"][3]` → `libro["Detalle"][3]`
(como en `dev`), y la aserción del Resumen (`C3`) pasa a la misma comprobación sobre
`libro["Obras"][3]` (`["VAR-29", "ACOND. NAVE MODUL-A", 0.455]`: VAR en Obras, D5).

En total: 6 tests de F-045, 17 de F-040 (13 adaptados y 4 borrados) y 1 de F-039.

## 8. Riesgos y alternativas descartadas

- **Quien lea la hoja «Resumen»** (Juan la pidió en F-040) deja de tenerla; el humano lo decidió
  avisado (D2). Quien lea el libro **por posición** ve Obras en la primera; Detalle conserva su
  nombre. F-020 dejó escrito que la plantilla solo la lee negocio; M1 lo confirma.
- **D10 (ABIERTA) · `LineaDetalle.nombre`.** Sin el Resumen, nadie lo lee. **A (recomendada):**
  se conserva (es la descripción sin prefijo, barata, y le servirá a F-038), con el comentario
  ajustado; ningún test más cambia. B: se borra; cambian además F-040 r8 y r9 y F-045 r5, r6,
  r7 y r10, que lo comprueban, sin cambio de comportamiento.
- **Conservar `filas_resumen` sin pintarlo**: descartado. Código sin consumidor; git lo guarda.
- **Postventa intercalada en el orden de entrada**: al separarla por `es_postventa` se conserva
  el orden relativo de cada parte, sin reordenar (F-040 R7).
- **Fórmulas** (`=SUMA` o `SUBTOTALES` en la agregada): descartadas por F-040 R16. Además, la
  fórmula de la agregada apuntaría a filas de la otra hoja, y se rompe al filtrar.
- **Esquema «agrupar» de Excel (outline) para plegar la otra parte**: descartado, por lo mismo
  que en F-040 §8: se pierde al filtrar y no es lo que se pidió.
- **Rótulos en `config.yaml`**: descartado, para no abrir otra superficie de configuración.
- **Un código de obra que se llame «OBRAS» o «POSTVENTA»**: hoy los códigos son números,
  `VAR-NN` o códigos con letras de Sigrid, y el campo `agregada` (no el texto) decide la
  cursiva. Si apareciera uno, el filtro por Código los mezclaría; se acepta.
