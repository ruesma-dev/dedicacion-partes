<!-- progress/impl_F-045.md -->
# F-045 · Informe del implementer

Copia principal, rama `feature/F-045-excel-obras-postventa`, rigor **estándar**
y SDD. Spec aprobada el 2026-10-08 con D1-D9 = A; hechas T1-T5 y T7. Tras la
MANUAL T6 el humano cambió el libro (D1, D2 reescritas; D10 = A) y la spec
revisada se aprobó: hechas **T8-T11** (§8). **T6 (M1) es MANUAL** (§6).

Solo `dedicacion-api` (`infrastructure/excel/` y sus tests) y las dos líneas de
documentación (T5, T10). Ni `.env`, ni Azure, ni Sigrid, ni front, ni transfer,
ni `config.yaml`, ni `azure-apps/`. Sin push. Datos de test inventados.

## 1. Qué cambió, por tarea (un commit cada una)

| Tarea | Commit | Qué |
|---|---|---|
| T1 | `2017b20` | `tests/test_f045_excel_pestanas.py`: 14 tests RED de contenido (R4-R12, R18) |
| T2 | `cd490cf` | `contenido.py`: `LineaDetalle.agregada`, `AGREGADA_EN_OBRAS` / `AGREGADA_EN_POSTVENTA`, `grupos_pestana`, helpers `_linea_detalle` y `_grupo` |
| T3 | `2f84bb6` | 14 tests RED del libro (R1-R3, R11-R18) y los 12 tests de la lista cerrada de design §7 |
| T4 | `3957525` | `exporter.py`: tres hojas, `_hoja_detalle` → `_hoja_grupos`, `_CURSIVA`, docstring. Incluye la corrección de dos tests nuevos de T3 (§3) |
| T5 | `77e124b` | `docs/ARCHITECTURE.md` (línea de `excel/`) y fila `export.xlsx` de `services/dedicacion-api/README.md` (R19) |
| T8 | `24b2dae` | Tests RED del libro nuevo: solo los «adaptados» de design §7.1-§7.3 |
| T9 | `3b5ef24` | `exportar` pinta Obras, Postventa y **Detalle**; fuera `_hoja_resumen`, `FilaResumen`, `filas_resumen` y los 4 tests «Se borra» |
| T10 | `9d2e361` | Las mismas dos líneas de documentación, con Detalle y sin Resumen (R19) |

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
5. **`exportar`** (tras T9): «Obras» es `libro.active`, «Postventa» y
   «Detalle» `create_sheet()` (`sheet1`-`sheet3`). Las bandas se cuentan por
   hoja: el `enumerate` es el de cada llamada a `_hoja_grupos` (R14).
6. **Cursiva**: `_CURSIVA = Font(italic=True)` en C, D y E de la agregada,
   después de bandas y bordes, que no tocan la fuente (R15). Sin negrita.

## 3. Tests anteriores cambiados y correcciones (T3; los de T8-T9 en §8)

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

## 5. Mutación (campaña de T5)

`python -m harness.mutacion --feature F-045 --workers 1` sobre `77e124b`: 14
mutantes (campaña completa, tope 20), **14 muertos, 0 supervivientes**, en
160.9 s. Una primera ejecución idéntica dio 1 superviviente
(`contenido.py:98`, `agregada=True` → `False`) que no se reproduce: a mano,
con el `.pyc` borrado, ese mutante tumba r7, r9, r15 y r18 de F-045. Única
diferencia: un `contenido.cpython-312.pyc` en `infrastructure/excel/__pycache__/`
antes de la primera (`_purgar_bytecode` se traga el `OSError` en Windows).
Anotado en el encargo de `arnes-base` de falsos supervivientes (`5370838`).
La campaña de T9 está en §8.

## 6. Verificación MANUAL pendiente (T6 / M1, humano)

Con el libro nuevo: comando exacto y los 8 pasos en `progress/current.md`
(octubre de 2026, `empresa=1`, api local) y design §6: abre sin reparación con
Obras, Postventa y Detalle y sin Resumen; filtro por Empleado con la misma Suma
de E en las tres; Código = POSTVENTA / OBRAS saca solo las agregadas; Estado
≠ OK; bandas, línea gruesa y cursiva; Detalle como en F-040, sin «RESTO …».

## 7. Qué queda fuera y qué falta

- Fuera (spec): F-038 (cuadro de mando), rótulos configurables, fórmulas,
  esquema de Excel, cualquier cambio de front, transfer, ruta o
  `config.yaml`. `azure-apps/` no describe el Excel (R19): sin cambios.
- Falta para cerrar: M1 del humano, review y despliegue de la api (nueva
  imagen; ninguna variable de entorno nueva).
- Riesgo de design §8: quien leía la hoja «Resumen» la pierde (D2, decidido
  por el humano) y quien lea por posición ve Obras primero; M1 lo confirma.
- Ruff: los ficheros de F-045 pasan `ruff check` desde la raíz; el total del
  repositorio sigue en 237 avisos de deuda previa.

## 8. Cambio del libro tras la MANUAL T6 (T8-T11)

Libro «Obras», «Postventa» y «Detalle» (F-040 sin cambios, tercera), sin
«Resumen». `exportar` llama a `_hoja_grupos` con `grupos_detalle` y «DETALLE DE
DEDICACIÓN · …» (design §3.2). Fuera `_hoja_resumen`, `_CABECERA_RESUMEN`,
`_ANCHOS_RESUMEN`, `FilaResumen` y `filas_resumen`; D10 = A: se conserva
`LineaDetalle.nombre` (comentario ajustado). Docstrings de ambos módulos al día.

**Tests (solo la lista cerrada de design §7):** 6 de F-045 (r1 renombrado a
`…_y_detalle`, r2, r11 contra `_GRUPOS_DETALLE`, r13 con las combinadas de
Detalle, r17 → `test_f045_r17_detalle_igual_que_en_f040`, r18 `Detalle!C5`);
13 adaptados de F-040, casi todos a su forma de `dev` con `_HOJA_DETALLE = 3`,
y `test_f039_r21` (Detalle fila 3, y la misma comprobación en Obras, D5). Solo
salen aserciones que leían el Resumen. En T9 se borran los 4 «Se borra» (r13,
r14_r15 del libro; r14, r15 de contenido) y la importación de `filas_resumen`.

**RED de T8**, con el exportador de T4 (Obras, Postventa, Resumen):

```
$ .venv/Scripts/python.exe -m pytest tests/test_f045_excel_pestanas.py tests/test_f040_excel.py tests/test_f039_registro_var.py -q
FAILED test_f045_r1_tres_hojas_obras_postventa_y_detalle   assert ['Obras', 'Po...a', 'Resumen'] == ['Obras', 'Po...a', 'Detalle']
FAILED test_f045_r2_… / r11_… / r17_detalle_igual_que_en_f040 / r18_…   KeyError: 'Worksheet Detalle does not exist.'
FAILED test_f045_r13_valor_en_todas_las_filas_y_combinadas_con_la_agregada   assert set() == {'A11:A13', '... 'B3:B5', ...}
FAILED test_f040_r1_dos_hojas_detalle_y_resumen            assert ['Obras', 'Po...a', 'Resumen'] == ['Obras', 'Po...a', 'Detalle']
FAILED test_f040_r2_ r3_ r6_ r7_r8_ r9_ r10_ r11_ r12_ r16_99996_ r17_   KeyError: 'Worksheet Detalle does not exist.'
FAILED test_f040_r4_impresion_y_anchos                     KeyError: 'Resumen'
FAILED test_f039_r21_el_excel_lleva_el_codigo_de_la_entrada  KeyError: 'Worksheet Detalle does not exist.'
19 failed, 52 passed, 1 warning in 20.76s        (exit=1)
```

19 = 6 de F-045 + 12 de F-040 + 1 de F-039. El 13.º de F-040,
`test_f040_r18_ningun_texto_en_notacion_cientifica`, pasa en RED: solo cambia
el texto de muestra (el del Resumen → «EXCESO 10%», que también está en Obras).
Tras T9: `pytest tests -q` de la api → **713 passed** (717 − 4 borrados).
`git grep -e filas_resumen -e FilaResumen -e _hoja_resumen -e _RESUMEN --
services/dedicacion-api` → sin resultados (el `grep -rn` de tasks.md solo
encuentra `coverage.json`, ignorado por git, y `.pyc` viejos).

**Mutación** (`__pycache__` de `infrastructure/excel` borrado antes;
`progress/mutacion_F-045.md`, HEAD `9d2e361`): 100 líneas en alcance, 14
mutantes, **14 muertos, 0 supervivientes**, 0 timeouts, 745.7 s (línea base
62.8 s, la máquina iba cargada). Sin supervivientes que analizar. Las líneas
nuevas de Detalle en `exportar` son llamada y literal: no generan mutante; las
cubren r1, r2 y r17 de F-045 y los de F-040.

## Evidencias

| Evidencia | Valor real (tras T9-T11) |
|---|---|
| Tests de la api | **713 passed**, 1 warning (deprecación de starlette, previa), en 70.03 s (`bash harness/init.sh`, servicio api) |
| Tests de la raíz | **418 passed, 1 skipped**, en 103.24 s |
| Tests de F-045 | 28 casos en `tests/test_f045_excel_pestanas.py` (14 de contenido, 14 del libro) |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: 100.0% de 33 líneas cambiadas cubiertas (33/33, umbral 80%, nivel estandar)` |
| Mutación | 14 generados, **14 evaluados, 14 muertos, 0 supervivientes**, 0 timeouts, en 745.7 s (§8; `progress/mutacion_F-045.md`) |
| `bash harness/init.sh` | **ENTORNO LISTO**, exit 0, cobertura OK, tamaño OK. Ruff 237 avisos de deuda previa (igual que al empezar) |
