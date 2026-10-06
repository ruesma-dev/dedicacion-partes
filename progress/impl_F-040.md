<!-- progress/impl_F-040.md -->
# F-040 · Informe del implementer

Copia `porcentajes-f040`, rama `feature/F-040-excel-modelo-juan`, rigor
**estándar** y SDD. Spec aprobada por el humano el 2026-10-06 con D1-D6 = A.
Hechas **T1-T5 y T7**. **T6 (M1) es MANUAL** y le toca al humano (§6).

No se ha escrito en Sigrid. No se han tocado `progress/current.md`,
`harness/features.json`, `.env`, `azure-apps/`, la copia principal ni
`porcentajes-f041`. Todos los datos de los tests y de la muestra son
inventados.

## 1. Qué cambió, por tarea (un commit cada una)

| Tarea | Commit | Qué |
|---|---|---|
| T1 | `fad6334` | `tests/test_f040_excel.py`: 16 tests RED de contenido (R7-R9, R14-R19) |
| T2 | `c7c7359` | `infrastructure/excel/contenido.py` (nuevo, sin openpyxl). Tiene `LineaDetalle`, `GrupoTrabajador`, `FilaResumen`, `grupos_detalle`, `filas_resumen`, `texto_pct`, `texto_estado` y `es_entero` |
| T3 | `5016c26` | 17 tests RED del libro (R1-R6, R10-R13, R16, R17, R18). Las combinadas, las bandas y los bordes se leen con `zipfile` sobre el XML de la hoja |
| T4 | `5bd2797` | `exporter.py` reescrito (detalle en §2) |
| T5 | `2b14802` | `docs/ARCHITECTURE.md` (la línea de `excel/`, 2 renglones) y la fila `export.xlsx` de `services/dedicacion-api/README.md` (R21) |
| — | `94854d3` | Estilo ruff de los ficheros nuevos (orden de imports, `Decimal(0)`) y `progress/mutacion_F-040.md` |

Ficheros de producción: `services/dedicacion-api/infrastructure/excel/contenido.py`
(nuevo) y `services/dedicacion-api/infrastructure/excel/exporter.py`.
Test nuevo: `services/dedicacion-api/tests/test_f040_excel.py` (33 tests).
No cambian el puerto `ExcelExporter`, `domain/`, `routes.py`, `deps.py`,
`config.yaml`, `requirements.txt` (openpyxl 3.1.5 ya estaba), el front ni el
transfer.

## 2. Decisiones de diseño (dentro de la spec)

1. **Celdas combinadas con valor (D2 = A).** Se combinan con
   `hoja.merged_cells.add(MergedCellRange(...))` después de escribir el valor
   en todas las filas del grupo, y nunca con `merge_cells()`. Las celdas de A,
   B, F, G y H del grupo llevan `vertical="center"`.
   `MergedCellRange._get_borders` copia en la ancla el borde inferior `medium`
   de la última fila. Se deja así, porque es la semántica de openpyxl y Excel
   no pinta los bordes interiores de una combinada. El aspecto final lo juzga
   el humano en M1.
2. **El fallo «1E+2».** Se arregla en `texto_pct`: si el valor es entero,
   `str(int(v))`; si no, `f"{v:.2f}"` con coma decimal. Ya no queda ningún
   `normalize()`. Con el exportador anterior y los datos de muestra, el
   Resumen salía así (ejecutado hoy, versión `31132a4`):
   `'0105 = 1E+2%'`, `'VAR-29 = 8E+1% + Postv-0702 = 3E+1%'`,
   `'FALTA 1E+1%'`, `'EXCESO 1E+1%'`. Ahora sale
   `0105 Obra Ficticia Centro = 100%` y `FALTA 10%`.
3. **Sin «-0» en el libro.** Con 99,996 la desviación del dominio es
   `Decimal("-0.00")`. `_celda_pct` suma `+ 0.0` para que la celda guarde 0 y
   no -0. El test `test_f040_r16_99996_…` lo fija.
4. **Desviación vacía en SIN CARGA (R9).** El grupo guarda `desviacion=None`
   y el estado sale de `texto_estado(estado, desviacion)` del dominio.
5. **Desviaciones menores respecto a design §3.2:**
   - `_rematar(hoja, anchos, ultima)` no recibe `columnas`, porque las saca
     de `len(anchos)`.
   - Hay un ayudante `_mes(periodo)` para el «Septiembre 2026» de los dos
     títulos.

   El comportamiento no cambia.
6. **El Resumen no lleva relleno ni bordes en los datos.** R13 no los pide,
   así que no se añaden.

## 3. Tests anteriores cambiados

**Ninguno.** La lista cerrada de la spec era «ninguno» y se cumple:

- `python -m pytest tests -q` de la api pasa de 586 a **619 passed**
  (586 + 33 nuevos), sin tocar ningún test anterior.
- `tests/test_f024_rutas_empresa.py` sigue en verde sin cambios (R20).
- Los tests de la raíz siguen igual: **418 passed, 1 skipped**.

## 4. Fase RED (trazas reales)

**T1.** Comando lanzado desde `services/dedicacion-api`:
`.venv/Scripts/python.exe -m pytest tests/test_f040_excel.py -q`

```
__________________ ERROR collecting tests/test_f040_excel.py __________________
ImportError while importing test module '...\tests\test_f040_excel.py'.
tests\test_f040_excel.py:22: in <module>
    from infrastructure.excel.contenido import (
E   ModuleNotFoundError: No module named 'infrastructure.excel.contenido'
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.33s
```

Después de T2: `16 passed in 0.11s`.

**T3**, contra el exportador anterior. Mismo comando, con `-rf`. Extracto de
los `E` y del resumen:

```
E   AssertionError: assert None == 'Empleado'          (A2 en blanco: cabecera en la fila 3)
E   assert None == 'A2:H12'                             (sin autofiltro)
E   assert None == 'landscape'                          (sin ajustes de impresión)
E   AssertionError: ('A', 3, {'ALFA PRUEBA UNO', 'Empleado'})
E   AssertionError: assert (set() == {'A3:A6', 'A7...'B9:B10', ...}   (sin combinadas)
E   assert 'FF1F3864' == 'FFFFFFFF'                     (sin bandas)
E   assert '0101 = 33.33...0102 = 56.67%' == 'VAR-29 Vario...ventado = 30%'
E   assert ('Obra(código)', 'General') == (0.55, '0%')
FAILED tests/test_f040_excel.py::test_f040_r2_titulo_en_fila_1_cabecera_en_2_datos_desde_3
FAILED tests/test_f040_excel.py::test_f040_r3_autofiltro_y_paneles - assert N...
FAILED tests/test_f040_excel.py::test_f040_r4_impresion_y_anchos - assert Non...
FAILED tests/test_f040_excel.py::test_f040_r5_cabecera_azul_con_texto_blanco_en_negrita
FAILED tests/test_f040_excel.py::test_f040_r6_cabecera_del_detalle_sin_obra_codigo
FAILED tests/test_f040_excel.py::test_f040_r7_r8_filas_del_detalle_en_orden_y_con_su_codigo
FAILED tests/test_f040_excel.py::test_f040_r9_sin_carga_en_el_libro - Asserti...
FAILED tests/test_f040_excel.py::test_f040_r10_valor_en_todas_las_filas_del_grupo
FAILED tests/test_f040_excel.py::test_f040_r11_combinadas_solo_en_grupos_de_varias_filas
FAILED tests/test_f040_excel.py::test_f040_r12_bandas_alternas_y_linea_gruesa_bajo_cada_trabajador
FAILED tests/test_f040_excel.py::test_f040_r13_resumen_una_fila_por_trabajador_sin_bandas
FAILED tests/test_f040_excel.py::test_f040_r14_r15_obras_total_y_estado_en_el_resumen
FAILED tests/test_f040_excel.py::test_f040_r16_99996_sale_ok_y_desviacion_cero_en_el_libro
FAILED tests/test_f040_excel.py::test_f040_r17_fraccion_y_formato_segun_sea_entero
FAILED tests/test_f040_excel.py::test_f040_r18_ningun_texto_en_notacion_cientifica
15 failed, 18 passed in 1.07s
```

Los 18 que pasaban eran los 16 de contenido y dos que el exportador anterior
ya cumplía: `r1` (dos hojas) y `r16_sin_formulas`.

Después de T4, con
`.venv/Scripts/python.exe -m pytest tests/test_f040_excel.py tests/test_f024_rutas_empresa.py -q`:
`89 passed, 1 warning in 13.41s`. El aviso es el
`StarletteDeprecationWarning` de `fastapi.testclient`, que ya estaba antes.

## 5. Comprobación extra en Excel 16 (COM, solo lectura, sobre la muestra inventada)

La muestra se abrió por COM (`Workbooks.Open`, solo lectura) y se probaron
los filtros con `Range("A2:H12").AutoFilter`:

```
Hojas: Detalle,Resumen
Combinadas A3: $A$3:$A$6
Filtro Empleado=ALFA -> visibles: 4                     (el grupo entero)
Filtro Obra=Obra Ficticia Sur -> 4=ALFA PRUEBA UNO|OK; 8=BETA PRUEBA DOS|FALTA 10%
Filtro Estado<>OK -> visibles: 5                        (2 + 2 + 1, los tres grupos no OK)
Texto E3: 55% / F7: 90% / E7: 33.33%
Resumen C7: 0105 Obra Ficticia Centro = 100%
```

Excel muestra «33.33%» con punto por la configuración regional de la
máquina: la celda guarda 0,3333 con formato `0.00%`. Lo que el COM no deja
ver es la imagen ni si sale el aviso de reparación (con `DisplayAlerts`
apagado, Excel repara sin preguntar). Eso queda para M1.

## 6. Verificación MANUAL pendiente (T6 / M1, humano)

**Muestra con datos inventados**, ya generada y lista para abrir:
`C:\Users\pgris\AppData\Local\Temp\f040\f040_muestra.xlsx` (`$env:TEMP\f040\`).
Tiene cinco trabajadores ficticios:

- uno con 4 obras;
- uno en FALTA;
- uno con VAR-29 y Postv-0702 en EXCESO;
- uno sin carga;
- uno con una sola obra.

Se regenera desde `services\dedicacion-api` con
`.\.venv\Scripts\python.exe $env:TEMP\f040\muestra_f040.py $env:TEMP\f040\f040_muestra.xlsx`.

**El real, en local desde la app.** En PowerShell, con la BBDD local y un
periodo que tenga carga, desde una copia con esta rama:

```powershell
cd C:\Users\pgris\PycharmProjects\porcentajes-f040\services\dedicacion-api
.\.venv\Scripts\python.exe main.py
# en otra terminal (cambia AAAA/MM por el periodo con carga):
curl.exe -o "$env:TEMP\f040.xlsx" "http://127.0.0.1:8090/api/v1/periodos/AAAA/MM/export.xlsx?empresa=1"
start "$env:TEMP\f040.xlsx"
```

También vale el botón «Exportar» del front local.

Hay que recorrer los 7 puntos de design §6:

1. Abre sin aviso de reparación.
2. Filtrar por un Empleado saca todas sus filas.
3. Filtrar por una Obra: cada fila visible enseña quién es y su Estado.
4. Filtrar por Estado ≠ OK.
5. Se ven las bandas y la línea gruesa entre trabajadores.
6. El Resumen enseña «código nombre = NN%».
7. La vista previa de impresión sale en horizontal, a una página de ancho y
   con la cabecera repetida.

Mirar también cómo se ve una combinada cuya primera fila oculta el filtro.
El humano da el visto bueno a los colores, la línea y los anchos, y el
resultado se anota en `progress/`.

## 7. Qué queda fuera y qué falta

- **Fuera de alcance (lo dice la spec):**
  - el nombre corto editable de la obra (D1-C);
  - la hoja «Datos» plana (D5-B, irá en F-038 si hace falta);
  - poder ordenar con «Ordenar» de Excel en el Detalle, que es el precio
    asumido de D2 = A.
- **`azure-apps/` no cambia**, porque no describe el Excel (R21).
- **Falta para cerrar:** M1 (humano), la review y el `done` del líder.
- **Convivencia con F-039**, que también toca el export de VAR: la línea
  `VAR-29` se trata como una obra normal y está probada aquí con datos
  inventados. Si F-039 trae algún test que lea el xlsx real, se ajusta al
  fusionar (design §8).

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests de la api | **619 passed**, 1 warning, en 21.63 s (`bash harness/init.sh`, servicio api) |
| Tests de la raíz | **418 passed, 1 skipped**, en 49.33 s |
| Tests nuevos de F-040 | 33, en `tests/test_f040_excel.py` (~1 s) |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: 100.0% de 132 líneas cambiadas cubiertas (132/132, umbral 80%, nivel estandar)` |
| Mutación | `python -m harness.mutacion --feature F-040 --workers 1`. 77 generados, **20 evaluados (muestreo, semilla 20260820), 20 muertos, 0 supervivientes**, 0 timeouts, en 439.9 s. Detalle en `progress/mutacion_F-040.md` |
| Línea base por mutante | 20.8 s; timeout efectivo de 120 s |
| `bash harness/init.sh` | **ENTORNO LISTO**, con la cobertura OK y el tamaño OK. Ruff: 235 avisos de deuda previa (237 al empezar), ninguno en los ficheros de F-040 |

La mutación se midió en `2b14802`. El commit siguiente (`94854d3`) solo
reordena imports y cambia literales `Decimal("0")` por `Decimal(0)` (ruff), y
no toca ninguna de las líneas mutadas. Sin supervivientes no hay análisis
pendiente.
