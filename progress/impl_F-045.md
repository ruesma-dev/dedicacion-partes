<!-- progress/impl_F-045.md -->
# F-045 · Informe del implementer

Copia principal, rama `feature/F-045-excel-obras-postventa`, rigor **estándar**
y SDD. Spec aprobada por el humano el 2026-10-08 con D1-D9 = A. Hechas **T1-T5
y T7**. **T6 (M1) es MANUAL** y le toca al humano (§6).

Solo `dedicacion-api`: `infrastructure/excel/`, sus tests y las dos líneas de
documentación de T5. No se ha tocado `.env`, ni Azure, ni Sigrid, ni el front,
ni el transfer, ni `config.yaml`, ni `azure-apps/`. Sin push. Todos los datos
de los tests son inventados.

## 1. Qué cambió, por tarea (un commit cada una)

| Tarea | Commit | Qué |
|---|---|---|
| T1 | `2017b20` | `tests/test_f045_excel_pestanas.py`: 14 tests RED de contenido (R4-R12, R18) |
| T2 | `cd490cf` | `contenido.py`: `LineaDetalle.agregada`, `AGREGADA_EN_OBRAS` / `AGREGADA_EN_POSTVENTA`, `grupos_pestana`, helpers `_linea_detalle` y `_grupo` |
| T3 | `2f84bb6` | 14 tests RED del libro (R1-R3, R11-R18) y los 12 tests de la lista cerrada de design §7 |
| T4 | `3957525` | `exporter.py`: tres hojas, `_hoja_detalle` → `_hoja_grupos`, `_CURSIVA`, docstring. Incluye la corrección de dos tests nuevos de T3 (§3) |
| T5 | `77e124b` | `docs/ARCHITECTURE.md` (línea de `excel/`) y fila `export.xlsx` de `services/dedicacion-api/README.md` (R19) |

Ficheros de producción: `services/dedicacion-api/infrastructure/excel/contenido.py`
y `services/dedicacion-api/infrastructure/excel/exporter.py`. Tests:
`services/dedicacion-api/tests/test_f045_excel_pestanas.py` (nuevo, 28 casos),
`tests/test_f040_excel.py` y `tests/test_f039_registro_var.py` (solo la lista
cerrada). No cambian `domain/`, `application/`, `routes.py`, `deps.py`,
`config.yaml`, `orm_models.py`, `repositories.py` ni `requirements.txt`.

## 2. Decisiones de diseño (dentro de la spec)

1. **`grupos_detalle` reescrito sobre los helpers, sin cambiar su
   comportamiento.** La comprensión de líneas pasa a `_linea_detalle(ln,
   prefijo)` y el cálculo de total, desviación y estado a `_grupo(fila,
   lineas)`, que comparten `grupos_detalle` y `grupos_pestana` (design §3.1,
   R11). Los 16 tests de contenido de F-040 siguen en verde sin tocarlos.
2. **El estado se calcula siempre sobre `fila.lineas` completas** (`num =
   len(fila.lineas)` en `_grupo`), no sobre las líneas de la pestaña: así
   GAMMA (solo postventa) sale «OK» en Obras y no «SIN CARGA», y DELTA sale
   «SIN CARGA» en las dos (R10, R11).
3. **La agregada suma con `sum(otras, Decimal(0))`**: arranca en `Decimal`,
   como `CuadranteTrabajador.total`, y nunca pasa por `float` (R7). El
   `float` solo aparece al escribir la celda, en `_celda_pct` de F-040.
4. **Rótulos como tuplas en `contenido.py`**, no en `config.yaml` (design §8).
   El campo `agregada`, no el texto, decide la cursiva.
5. **`exportar`**: «Obras» es `libro.active`, «Postventa» `create_sheet()` y
   «Resumen» `create_sheet("Resumen")`, así que los XML son `sheet1`, `sheet2`
   y `sheet3`. El Resumen sale de `filas_resumen(grupos_detalle(...))`, como
   en F-040 (R17). Las bandas se cuentan por hoja porque el `enumerate` es el
   de cada llamada a `_hoja_grupos` (R14).
6. **Cursiva**: `_CURSIVA = Font(italic=True)` en C, D y E de la agregada,
   después de bandas y bordes, que no tocan la fuente (R15). Sin negrita.

## 3. Tests anteriores cambiados y correcciones

**Lista cerrada de design §7, y solo ella** (12 tests). El `git diff` de
`test_f040_excel.py` y `test_f039_registro_var.py` solo cambia el nombre o el
índice de la hoja y las dos celdas de GAMMA:

- `test_f040_r1` `["Obras", "Postventa", "Resumen"]`; `r2` títulos «OBRAS · …»
  (también enero); `r3`, `r6`, `r9`, `r16_99996`, `r17` y `test_f039_r21`
  `"Detalle"` → `"Obras"`; `r4` el dict de anchos lleva `"Obras"` y
  `"Postventa"` (la Postventa queda comprobada también: es más estricto);
  `r7_r8` C10 `"POSTVENTA"` y D10 `"RESTO POSTVENTA"`; `r11` Resumen en
  `sheet3`; `r13` `_xml_hoja(contenido, 3)`.
- Ninguna aserción se relaja ni se borra. Los nombres de los tests no cambian
  (trazabilidad con F-040). El docstring del módulo de test_f040 explica el
  cambio de hoja.

**Corrección de dos tests nuevos de F-045** (no anteriores): en T3,
`test_f045_r4_r10_filas_de_la_pestana_{obras,postventa}` leían la columna A
con `load_workbook`, que vacía las celdas no ancla de las combinadas (F-040
§5). En T4 fallaban con `At index 1 diff: None != 'ALFA PRUEBA UNO'` contra el
exportador nuevo; pasan a leerla del XML con `_xml_hoja` (helper
`_empleados`). Va en el commit de T4 y queda dicho en su mensaje.

## 4. Fase RED (trazas reales)

Todos los comandos, desde `services/dedicacion-api` con su `.venv`.

**T1** (contenido), con `contenido.py` de `e301e0c`:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f045_excel_pestanas.py -q
tests\test_f045_excel_pestanas.py:21: in <module>
    from infrastructure.excel.contenido import (
E   ImportError: cannot import name 'AGREGADA_EN_OBRAS' from 'infrastructure.excel.contenido'
ERROR tests/test_f045_excel_pestanas.py
1 error in 0.36s        (exit=2)
```

El `ImportError` lo da `AGREGADA_EN_OBRAS`, el primer nombre nuevo de la
importación, que va antes de `grupos_pestana`: es la misma causa que pedía
tasks.md. Tras T2: `pytest tests/test_f045_excel_pestanas.py
tests/test_f040_excel.py -q` → **47 passed in 1.02s**.

**T3** (libro + lista cerrada), con el `exporter.py` de F-040:

```
$ .venv/Scripts/python.exe -m pytest tests/test_f045_excel_pestanas.py tests/test_f040_excel.py tests/test_f039_registro_var.py -q
FAILED test_f045_r1_tres_hojas_obras_postventa_y_resumen
E       AssertionError: assert ['Detalle', 'Resumen'] == ['Obras', 'Po...a', 'Resumen']
FAILED test_f045_r2_titulos_cabecera_en_2_y_datos_desde_3      KeyError: 'Worksheet Obras does not exist.'
FAILED test_f045_r3_…[Obras] / [Postventa]                     KeyError: 'Worksheet Obras|Postventa does not exist.'
FAILED test_f045_r4_r10_filas_de_la_pestana_obras / _postventa  KeyError: 'Worksheet … does not exist.'
FAILED test_f045_r11_… / r12_… / r15_… / r16_… / r18_…           KeyError: 'Worksheet … does not exist.'
FAILED test_f045_r13_valor_en_todas_las_filas_y_combinadas_con_la_agregada
E       AssertionError: ('Obras', 'A', 10, {'DELTA PRUEBA CUATRO', 'EPSILON PRUEBA CINCO'})
FAILED test_f045_r14_bandas_por_hoja_y_linea_gruesa_bajo_cada_trabajador
E       AssertionError: ('Obras', 'A')
E       assert ('thin', 'FFBFBFBF') == ('medium', 'FF000000')
FAILED test_f045_r17_resumen_igual_que_en_f040
E       KeyError: "There is no item named 'xl/worksheets/sheet3.xml' in the archive"
FAILED test_f040_r1_dos_hojas_detalle_y_resumen                assert ['Detalle', 'Resumen'] == ['Obras', …]
FAILED test_f040_r2_… r3_… r6_… r7_r8_… r9_… r11_… r16_99996_… r17_…   KeyError: 'Worksheet Obras does not exist.'
FAILED test_f040_r4_impresion_y_anchos                         KeyError: 'Detalle'
FAILED test_f040_r13_resumen_una_fila_por_trabajador_sin_bandas  KeyError: "… 'xl/worksheets/sheet3.xml' …"
FAILED test_f039_r21_el_excel_lleva_el_codigo_de_la_entrada    KeyError: 'Worksheet Obras does not exist.'
26 failed, 45 passed, 1 warning in 5.23s        (exit=1)
```

26 = los 14 nuevos del libro + los 12 de la lista cerrada; los 45 en verde son
los 14 de contenido de F-045 y los tests de F-040/F-039 que no cambian. (Las
líneas de `KeyError` están agrupadas por test para caber en el tope; la
traza completa se generó en el scratchpad de la sesión.) Tras T4:
`pytest tests -q` de la api → **717 passed, 1 warning in 9.86s**.

## 5. Mutación

`python -m harness.mutacion --feature F-045 --workers 1` →
`progress/mutacion_F-045.md`, medida en `77e124b` (HEAD de T5; nada de
producción cambia después). 99 líneas en alcance, 14 mutantes (por debajo
del tope de 20 del muestreo: campaña completa).

**Campaña definitiva (la del informe): 14 evaluados, 14 muertos, 0
supervivientes**, 0 timeouts, en 160.9 s.

**Aviso para el líder: la primera campaña dio un veredicto que no se
reproduce.** La primera ejecución, idéntica y sobre el mismo SHA, dio 13
muertos y **1 superviviente**: `contenido.py:98`, `agregada=True` →
`agregada=False` (en 176.1 s, exit 1). No cuadraba, porque ese mutante deja
la agregada sin marca y `test_f045_r7` compara la tupla con `True`. Lo
comprobé a mano con el mismo comando y el mismo entorno que usa
`EjecutorPytest.correr`, con el `.pyc` de `contenido` borrado:

```
$ sed -i '98s/agregada=True,/agregada=False,/' infrastructure/excel/contenido.py
$ PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe -m pytest -x -q --tb=no -p no:cacheprovider tests
FAILED tests/test_f045_excel_pestanas.py::test_f045_r7_agregada_unica_al_final_con_rotulos_y_suma
1 failed, 692 passed, 1 warning in 9.19s        rc=1
$ git checkout infrastructure/excel/contenido.py
```

Sin `-x` caen 4 tests (r7, r9, r15 y r18 de F-045). Al repetir la campaña,
ese mutante salió **muerto**. Así que no es un hueco de los tests, sino un
veredicto de la herramienta que no se reproduce. Diferencia entre las dos
ejecuciones: antes de la primera había en `infrastructure/excel/__pycache__/`
un `contenido.cpython-312.pyc` de mis ejecuciones de pytest, y antes de la
segunda no. `_purgar_bytecode` se traga el `OSError` al borrar en Windows. No
he podido confirmar la causa y no he tocado `harness/`. Si el líder lo ve
oportuno, merece un aviso al arnés (`arnes-base`). El informe de la primera
campaña lo sobrescribió la segunda; tengo copia en el scratchpad de la sesión.

## 6. Verificación MANUAL pendiente (T6 / M1, humano)

Con la api local (`python main.py` en `services/dedicacion-api`, BBDD local con
un periodo que tenga postventa):

```powershell
curl.exe -o "$env:TEMP\f045.xlsx" "http://127.0.0.1:8090/api/v1/periodos/AAAA/MM/export.xlsx?empresa=1"
start "$env:TEMP\f045.xlsx"
```

Los 6 puntos de design §6: abre sin reparación con Obras, Postventa y
Resumen; filtrar un Empleado con obras y postventa da el grupo entero y la
misma Suma de E en las dos; Código = POSTVENTA (Obras) / OBRAS (Postventa)
saca solo las agregadas; Estado ≠ OK saca filas completas; bandas, línea
gruesa y cursiva; Resumen como en F-040. No comprobado aquí por COM: la
imagen de la cursiva y una combinada con la primera fila oculta (design §5).

## 7. Qué queda fuera y qué falta

- Fuera (spec): F-038 (cuadro de mando), rótulos configurables, fórmulas,
  esquema de Excel, cualquier cambio de front, transfer, ruta o
  `config.yaml`. `azure-apps/` no describe el Excel (R19): sin cambios.
- Falta para cerrar: M1 del humano, review y despliegue de la api (nueva
  imagen; ninguna variable de entorno nueva).
- Riesgo de design §8: quien lea el libro por el nombre «Detalle» o por
  posición se rompe; M1 lo confirma con el humano.
- Ruff: los ficheros de F-045 pasan `ruff check` desde la raíz; el total del
  repositorio sigue en 237 avisos de deuda previa.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests de la api | **717 passed**, 1 warning (deprecación de starlette, previa), en 19.63 s (`bash harness/init.sh`, servicio api) |
| Tests de la raíz | **418 passed, 1 skipped**, en 37.38 s |
| Tests de F-045 | 28 casos en `tests/test_f045_excel_pestanas.py` (14 de contenido, 14 del libro) |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: 100.0% de 30 líneas cambiadas cubiertas (30/30, umbral 80%, nivel estandar)` |
| Mutación | `python -m harness.mutacion --feature F-045 --workers 1`: 14 generados, **14 evaluados, 14 muertos, 0 supervivientes**, 0 timeouts, en 160.9 s (campaña completa: 14 < tope 20). Detalle en `progress/mutacion_F-045.md`. Una primera ejecución dio 1 superviviente que no se reproduce (§5) |
| Línea base por mutante | 12.1 s; timeout efectivo de 120 s |
| `bash harness/init.sh` | **ENTORNO LISTO**, cobertura OK, tamaño OK. Ruff 237 avisos de deuda previa (igual que al empezar) |
