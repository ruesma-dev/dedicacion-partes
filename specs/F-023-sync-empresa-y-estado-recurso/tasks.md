<!-- specs/F-023-sync-empresa-y-estado-recurso/tasks.md -->
# F-023 · Tareas

Rama: `feature/F-023-sync-empresa-y-estado-recurso`. Un commit por tarea:
`F-023 Tn: descripción`. Rutas relativas a `services/dedicacion-api/`.

> **Rigor `critico`.** T1 es la fase RED y va antes que el código: la traza
> real del fallo se pega en `progress/impl_F-023.md`. Prohibido tocar
> `harness/features.json` y `progress/current.md` (los lleva el líder).
> Comando de tests: `cd services/dedicacion-api && .venv/Scripts/python -m pytest tests/test_f023_sync_empresa.py -q`.

- [x] T1: Crear `tests/test_f023_sync_empresa.py` con los tests de design §6 (`test_f023_rN_*`, R1-R18), sin red ni BBDD  |  Verificación: el comando de tests falla (RED) por `empresa` ausente del ORM, `CriterioActivoRecurso` inexistente y alias ausentes; salida real pegada en `progress/impl_F-023.md`
- [x] T2: Añadir `empresa` a `TrabajadorORM`, `ObraORM` (`orm_models.py`) y a `Trabajador`, `Obra` (`domain/models.py`)  |  Verificación: `pytest tests/test_f023_sync_empresa.py -q -k "r1 or r2"` en verde y `pytest tests/test_f003_esquema.py -q` en verde
- [x] T3: `repositories.py`: `_entero`, `empresa` en alta, actualización, `cambio` y mapeos a dominio  |  Verificación: `pytest tests/test_f023_sync_empresa.py -q -k "r7 or r8"` en verde
- [x] T4: `filtros_maestros.py`: `CriterioActivoRecurso`, campos nuevos de `ResultadoDepuracion`, paso 0 fila a fila, clave de persona con empresa, `con_baja_laboral` y limpieza de columnas auxiliares (design §2)  |  Verificación: `pytest tests/test_f023_sync_empresa.py -q -k "r9 or r10 or r11 or r12 or r13 or r14 or r15 or r16"` en verde
- [x] T5: `config.yaml`: consultas de obras y empleados de design §3 y claves `filtro_estado_recurso`, `estados_recurso_excluidos: []`, `excluir_recurso_con_fecha_baja: false` con comentario y citas a `sigrid_tablas.md`  |  Verificación: `pytest tests/test_f023_sync_empresa.py -q -k "r3 or r4 or r5"` en verde
- [x] T6: `sync_pipeline.py`: `criterio` en `FetchEmpleadosStep`, columnas requeridas con `empresa` en los dos steps, log con los recuentos nuevos  |  Verificación: `pytest tests/test_f023_sync_empresa.py -q -k "r6"` en verde
- [ ] T7: `use_cases.py::PreviewSync`: `criterio`, validación de columnas y claves de R17  |  Verificación: `pytest tests/test_f023_sync_empresa.py -q -k "r6 or r17"` en verde
- [ ] T8: `deps.py`: un único `CriterioActivoRecurso` leído de `config.yaml` para step y preview  |  Verificación: `pytest tests/test_f023_sync_empresa.py -q -k "r18"` en verde y suite completa `pytest -q` del servicio en verde
- [ ] T9: MANUAL (humano) · cerrar D1: lanzar Q1 de design §4 por `POST /api/sql/read` contra `ruesma_rep` y fijar en `config.yaml` los literales de `estados_recurso_excluidos` y el valor de `excluir_recurso_con_fecha_baja`; el implementer solo copia los valores decididos  |  Verificación: MANUAL (humano) — resultado de Q1 y decisión anotados en `progress/impl_F-023.md`
- [ ] T10: MANUAL (humano) · R19 y D6: con la API local apuntando a Sigrid, `GET http://localhost:8090/api/v1/sync/preview`; comprobar que la respuesta no llega truncada, que los recursos de la lista D5 salen en `excluidos_por_estado_recurso` y no en los incluidos (Q2 de design §4 para contrastar), y revisar `por_empresa`  |  Verificación: MANUAL (humano) — recuentos anotados en `progress/impl_F-023.md`
- [ ] T11: MANUAL (humano) · arrancar la API contra la BBDD local `dedicacion` y comprobar que `sincronizar_esquema` añade `empresa` a `trabajador` y `obra`; lanzar `POST /api/v1/sync` y verificar `SELECT empresa, COUNT(*) FROM obra GROUP BY empresa` (y lo mismo en `trabajador`) sin NULL tras el sync  |  Verificación: MANUAL (humano) — salida anotada en `progress/impl_F-023.md`
- [ ] T12: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh` termina en verde
