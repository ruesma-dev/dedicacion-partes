<!-- specs/F-076-excel-sin-resto-de/tasks.md -->
# F-076 · Tareas

Solo `dedicacion-api`. Tests sin red ni BBDD, con el intérprete de `services/dedicacion-api/.venv`. Decisiones cerradas por el humano el 2026-11-24 («d1 b, lo demas a»): D1 = (b), D2-D5 = (a) (design §10). Tests anteriores que cambian: lista CERRADA de design §6 (25 items: 24 de F-045 y 1 de F-040); fuera de ella o de su criterio, **PARA**.

- [x] T1: `tests/test_f076_excel_sin_resto.py` con los 14 tests de design §5, en rojo contra el código actual (fase RED; anotar la traza en `progress/impl_F-076.md`)  |  Verificación: `pytest tests/test_f076_excel_sin_resto.py` falla por las agregadas, los trabajadores de la otra parte y los totales (r14 por los docs), no por errores de import
- [x] T2: `contenido.py`: `_grupo(fila, lineas, total, num)`; `grupos_detalle` con el completo; `grupos_pestana` sin agregada, sin los trabajadores de R5, con «SIN CARGA» en las dos y con total y estado de la parte; fuera `LineaDetalle.agregada` y `AGREGADA_EN_*`; docstrings (design §3.1)  |  Verificación: `pytest tests/test_f076_excel_sin_resto.py -k "r2 or r3 or r4 or r5 or r6 or r7 or r8 or r12"`
- [x] T3: `exporter.py`: fuera `_CURSIVA` y el bloque `if linea.agregada`; docstring del módulo (design §3.2)  |  Verificación: `pytest tests/test_f076_excel_sin_resto.py -k "r1 or r9 or r10 or r11 or r13"`
- [x] T4: `test_f045_excel_pestanas.py` según design §6.1 (12 funciones borradas, 8 adaptadas, 3 solo por los comunes, 5 sin tocar; comunes y docstring)  |  Verificación: `pytest tests/test_f045_excel_pestanas.py` en verde y diff limitado a la lista de §6.1
- [x] T5: `test_f040_excel.py` según design §6.2 (solo `test_f040_r2_…` y el docstring)  |  Verificación: `pytest tests/test_f040_excel.py tests/test_f039_registro_var.py tests/test_f024_rutas_empresa.py` en verde; F-039 y F-024 sin tocar
- [ ] T6: docs: línea `excel/` de `docs/ARCHITECTURE.md`, fila `export.xlsx` de `services/dedicacion-api/README.md` y nota de sustitución en `specs/F-045-excel-obras-postventa/requirements.md` (R14, design §2)  |  Verificación: `pytest tests/test_f076_excel_sin_resto.py -k r14`
- [ ] T7: M1, Excel de octubre de 2026 abierto en Excel por el humano (design §7)  |  Verificación: MANUAL (humano): `curl.exe -o "$env:TEMP\f076.xlsx" "http://127.0.0.1:8090/api/v1/periodos/2026/10/export.xlsx?empresa=1"` con la api local y resultado anotado en `progress/`
- [ ] T8: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh` sin ningún [KO]
