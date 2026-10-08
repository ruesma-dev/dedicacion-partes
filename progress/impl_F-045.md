<!-- progress/impl_F-045.md -->
# F-045 · Informe del implementer

Copia principal, rama `feature/F-045-excel-obras-postventa`, rigor **estándar**
y SDD. Spec aprobada el 2026-10-08 con D1-D9 = A; hechas T1-T5 y T7. Tras la
MANUAL T6 el humano cambió el libro (D1, D2 reescritas; D10 = A) y la spec
revisada se aprobó: hechas **T8-T11** (§8); M1 cumplida. Ampliación con la
columna «Observaciones» (D11 = A, D12 = A): hechas **T12-T15** (§9); **T16
(M2) es MANUAL** del humano (§9.4).

Solo `dedicacion-api` (`infrastructure/excel/` y sus tests) y las dos líneas de
documentación (T5, T10, T14). Ni `.env`, ni Azure, ni Sigrid, ni front, ni transfer,
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
| T12 | `b7e3616` | Tests RED de la columna I: lista cerrada de design §7.2 y r20, r21 nuevos |
| T13 | `927d592` | `exporter.py`: columna I «Observaciones» vacía (design §3.3) |
| T14 | `ca221b5` | Las mismas dos líneas de documentación, con la columna Observaciones (R19) |

Ficheros de producción: `services/dedicacion-api/infrastructure/excel/contenido.py`
y `services/dedicacion-api/infrastructure/excel/exporter.py`. Tests:
`services/dedicacion-api/tests/test_f045_excel_pestanas.py` (nuevo, 30 casos),
`tests/test_f040_excel.py` y `tests/test_f039_registro_var.py` (solo la lista
cerrada). No cambian `domain/`, `application/`, `routes.py`, `deps.py`,
`config.yaml`, `orm_models.py`, `repositories.py` ni `requirements.txt`.

## 2-3. Decisiones de diseño y tests anteriores cambiados (T1-T4)

`grupos_detalle` y `grupos_pestana` comparten `_linea_detalle` y `_grupo`; el
estado sale de `fila.lineas` completas (R10, R11); la agregada suma en
`Decimal` (R7); rótulos en `contenido.py` y la cursiva la decide `agregada`
(R15); bandas por hoja (R14). T3 cambió solo la lista cerrada de entonces (12
tests: hoja e índice, sin relajar nada, `2f84bb6`); T8-T9 en §8, T12 en §9.

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

`AGREGADA_EN_OBRAS` es el primer nombre nuevo importado (misma causa que
pedía tasks.md). Tras T2: f045 + f040 → **47 passed**.

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

26 = 14 nuevos del libro + 12 de la lista cerrada (`KeyError` agrupados por
test). Tras T4: `pytest tests -q` de la api → **717 passed**.

## 5. Mutación (campañas de T5 y T9)

T5 (`77e124b`) y T9 (`9d2e361`): 14 mutantes cada una, **14 muertos, 0
supervivientes**. En T5 una primera ejecución dio un falso superviviente
(`contenido.py:98`) que muere a mano y no se repitió (encargo de `arnes-base`
de falsos supervivientes, `5370838`). La de la ampliación, en §9.3.

## 6-7. MANUAL, qué queda fuera y qué falta

- M1 (T6) cumplida por el humano el 2026-10-08 («todo ok»). M2 (T16), §9.4.

- Fuera (spec): F-038 (cuadro de mando), rótulos configurables, fórmulas,
  esquema de Excel, cualquier cambio de front, transfer, ruta o
  `config.yaml`. `azure-apps/` no describe el Excel (R19): sin cambios.
- Fuera (D11 = A): guardar las observaciones en la app. Lo escrito en la
  columna I vive solo en ese fichero; un export nuevo sale vacío (design §8).
- Falta para cerrar: review 4, M2 del humano (§9.4) y despliegue de la api
  (nueva imagen; ninguna variable de entorno nueva).
- Riesgos de design §8: quien leía «Resumen» la pierde (D2); con I dentro, la
  escala de impresión a una página de ancho baja un ~23 % (M2 lo mira).
- Ruff: 237 avisos de deuda previa en el repositorio, como al empezar.

## 8. Cambio del libro tras la MANUAL T6 (T8-T11)

Obras, Postventa y Detalle (F-040, tercera), sin Resumen: `exportar` pinta
Detalle con `_hoja_grupos` y `grupos_detalle`; fuera `_hoja_resumen`,
`_CABECERA_RESUMEN`, `_ANCHOS_RESUMEN`, `FilaResumen`, `filas_resumen`; D10 = A.
Tests de la lista cerrada de entonces: 6 de F-045, 13 de F-040 (con
`_HOJA_DETALLE = 3`) y `test_f039_r21`; solo salen aserciones que leían el
Resumen, y en T9 se borran los 4 «Se borra».

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

19 = 6 de F-045 + 12 de F-040 + 1 de F-039 (`test_f040_r18_…` pasa en RED:
solo cambia el texto de muestra). Tras T9: api → **713 passed** (717 − 4);
`git grep` de `filas_resumen|FilaResumen|_hoja_resumen|_RESUMEN` → nada.

## 9. Ampliación: columna «Observaciones» (T12-T16, D11 = A, D12 = A)

### 9.1 Qué cambió

Solo `exporter.py` (design §3.3): «Observaciones» en `_CABECERA_DETALLE`, 50 en
`_ANCHOS_DETALLE` (autofiltro `A2:I<n>` solo, por `len(anchos)`),
`_OBSERVACIONES = 9`, `_AJUSTE` (ajuste, arriba), bucle de banda y bordes hasta
`len(_CABECERA_DETALLE)` y `_AJUSTE` en I. Ningún valor en I; `_COMBINADAS` y
la cursiva, sin tocar. `contenido.py` y `test_f039_…`, sin diff.

Tests: solo la lista cerrada de design §7.2 (`_CABECERA`; F-045 r3, r4_r10 ×2,
r17; F-040 r3, r4, r6, r9), todo elementos AÑADIDOS (I en rangos, el 50,
«Observaciones», `None` final): ninguna comprobación quitada. Nuevos r20 y r21
(design §7.3; r21 por XML en las tres hojas: I existe sin valor, banda,
`medium`/`thin`; por openpyxl: ajuste, arriba, sin cursiva; sin combinar).

### 9.2 Fase RED (T12), contra el exportador de `a3578c0`

```
$ .venv/Scripts/python.exe -m pytest tests/test_f045_excel_pestanas.py tests/test_f040_excel.py tests/test_f039_registro_var.py -q --tb=line
tests/test_f045_excel_pestanas.py:308: AssertionError: assert ['Empleado', ...mpleado', ...] == ['Empleado', ...mpleado', ...]   (×2: [Obras], [Postventa])
tests/test_f045_excel_pestanas.py:340: AssertionError: assert [None, None, ..., 'SIN CARGA'] == [None, None, ...N CARGA', ...]
tests/test_f045_excel_pestanas.py:359: AssertionError: assert [None, None, ..., 'SIN CARGA'] == [None, None, ...N CARGA', ...]
tests/test_f045_excel_pestanas.py:478: AssertionError: assert ['Empleado', ...mpleado', ...] == ['Empleado', ...mpleado', ...]
tests/test_f045_excel_pestanas.py:527: AssertionError: Obras
tests/test_f045_excel_pestanas.py:552: AssertionError: ('Obras', 3)
tests/test_f040_excel.py:272: AssertionError: assert 'A2:H12' == 'A2:I12'
tests/test_f040_excel.py:291: assert (34.0, 22.0, ....0, 15.0, ...) == (34, 22, 12, 44, 13, 15, ...)
tests/test_f040_excel.py:306: AssertionError: assert ['Empleado', ...mpleado', ...] == ['Empleado', ...mpleado', ...]
tests/test_f040_excel.py:325: AssertionError: assert [None, None, ..., 'SIN CARGA'] == [None, None, ...N CARGA', ...]
11 failed, 58 passed, 1 warning in 15.58s        (exit=1)
```

11 = r3 ×2, r4_r10 ×2, r17, r20 (`Obras`: I2 vacía) y r21 (`('Obras', 3)`: I3
no existe en el XML) de F-045, y r3, r4, r6, r9 de F-040. `test_f040_r4`
también falla (ancho de I `None` ≠ 50), aunque tasks.md solo pedía ampliarlo.
Tras T13: los tres ficheros → **69 passed**; `pytest tests -q` de la api →
**715 passed** (713 + r20 + r21).

### 9.3 Mutación

`__pycache__` de `infrastructure/excel` borrado antes de cada campaña; `python
-m harness.mutacion --feature F-045 --workers 1` sobre `ca221b5` (112 líneas, 28
mutantes, muestra de 20, semilla `20260820`). Tres ejecuciones, todas con
supervivientes **distintos** que **mueren a mano** (`-B`, sin caché): 1.ª, 17
muertos y 3 (`contenido.py:116`, `:118`, `exporter.py:110`); 2.ª, 19 y 1
(`exporter.py:110`, cazado a mano por r14, r17 y r21 de F-045 y r12 de F-040);
3.ª (la del informe), **19 muertos, 1 superviviente** (`contenido.py:84`, muerto
en las otras dos), 678.3 s. Análisis en `progress/mutacion_F-045.md`: falsos
supervivientes. Durante las campañas otros procesos importaron esta copia sin
`PYTHONDONTWRITEBYTECODE` (la api local arrancada a las 14:01:18; algo que
compiló la app entera a las 14:20:13). Causa exacta sin cerrar.

### 9.4 MANUAL M2 (humano, en local, nada contra Azure)

**Antes, reiniciar la api local**: la que corre desde esta copia (`main.py`,
arrancada a las 14:01:18) se levantó en mitad de una campaña de mutación y
puede tener en memoria un `exporter.py` mutado (§9.3).

1. Parar esa api (Ctrl+C) y arrancarla: `cd C:\Users\pgris\PycharmProjects\porcentajes\services\dedicacion-api`
   y `.venv\Scripts\python main.py` (8090, BBDD local).
2. PowerShell: `curl.exe -o "$env:TEMP\f045.xlsx" "http://127.0.0.1:8090/api/v1/periodos/2026/10/export.xlsx?empresa=1"`
   y `start "$env:TEMP\f045.xlsx"`.
3. En las tres hojas, la última columna es «Observaciones», cabecera azul, ancha.
4. Texto largo en una celda de I de un grupo de varias filas: se ajusta, la
   fila crece y la celda es de una sola fila.
5. Filtro de Observaciones → «(No vacías)»: solo esa fila. Quitar el filtro.
6. Vista previa de impresión: una página de ancho, con I dentro y legible.

## Evidencias

| Evidencia | Valor real (tras T12-T15) |
|---|---|
| Tests de la api | **715 passed**, 1 warning (deprecación de starlette, previa), en 54.78 s (`bash harness/init.sh`, servicio api) |
| Tests de la raíz | **418 passed, 1 skipped**, en 68.01 s |
| Tests de F-045 | 30 casos en `tests/test_f045_excel_pestanas.py` (14 de contenido, 16 del libro) |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: 100.0% de 38 líneas cambiadas cubiertas (38/38, umbral 80%, nivel estandar)` |
| Mutación | 28 generados, 20 evaluados, **19 muertos, 1 superviviente falso** (muere a mano), 0 timeouts, 678.3 s (§9.3) |
| `bash harness/init.sh` | **ENTORNO LISTO**, exit 0, cobertura y tamaño OK (impl 219/220). Ruff 237 avisos de deuda previa (igual que al empezar) |
