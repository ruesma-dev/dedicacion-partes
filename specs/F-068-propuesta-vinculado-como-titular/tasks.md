<!-- specs/F-068-propuesta-vinculado-como-titular/tasks.md -->
# F-068 · Tareas

Orden de despliegue: transfer → api → front (design §8). Tests sin red ni BBDD.
Las decisiones D1-D5 del design §9 están cerradas por el humano (2026-10-28, la A en las cinco).

- [x] T1: transfer, contrato de entrada: `VinculadoEntrada.descripcion`, `VinculadoIn.descripcion`, `VinculadoPropuestaIn.tipo_res`/`.descripcion` (opcionales; sin ellos, la entrada de hoy) (R18)  |  Verificación: `test_f068_pipeline.py::test_f068_r18_*` y `pytest services/dedicacion-transfer/tests/test_f044_*`
- [x] T2: transfer, piezas puras: `es_capitulo_ci4`, `hojas_con_subcuenta` (y `partida_ci_del_tipo` sobre ella), `puntuar`, `desempate_ci4` (R5-R8)  |  Verificación: `test_f068_reglas.py::test_f068_r5_*..r8_*` y `test_f044_reglas_vinculados.py` intacto
- [ ] T3: transfer, `partida_por_cuenta_o_nombre` con sus motivos `sin_ci`, `varias_ci`, `empate_nombre` (R4-R9, D1, D5)  |  Verificación: `test_f068_reglas.py::test_f068_r4_*`, `r9_*`
- [ ] T4: transfer, `partida_por_historial` sobre `previa_en_obra` (D2, D3) y el orden de `partida_del_vinculado` con `historial=None` compatible (R1-R3, R10)  |  Verificación: `test_f068_reglas.py::test_f068_r1_*..r3_*`, `r10_*` (incluye «la misma función que el trabajador» y «la regla no lee»)
- [ ] T5: transfer, `SigridWriteClient.historial_de_vinculados` (§7) con `_linea_historial` compartido; doble en `conftest.py` y en `test_pipeline_offline.py` (R11, R13)  |  Verificación: `test_f068_sql.py` (SQL, parámetros, lotes, sin `LIKE 'M%'`, `m.obride = ?`, `truncated` lanza) y `test_f050_*` del historial intactos
- [ ] T6: transfer, `PasoVinculados.decidir/_partida`: historial y cuentas perezosos y una vez por petición, propuesta guardada con `METODOS_PROPUESTA_PROPIA`; `registro_pipeline._preflight` pasa la ventana (R11, R12, R14, R16)  |  Verificación: `test_f068_pipeline.py::test_f068_r11_*`, `r12_*`, `r14_*` (lecturas contadas con y sin vinculados), `r16_*`
- [ ] T7: transfer, `PasoVinculados.proponer` y `RegistroPipeline.proponer` con la ventana y el `origen` (R15)  |  Verificación: `test_f068_pipeline.py::test_f068_r15_selector_igual_que_preflight`
- [ ] T8: transfer, `LecturasDelLote.historial_de_vinculados` por `_una_vez` (R15)  |  Verificación: `test_f068_pipeline.py::test_f068_r15_lote_igual_que_suelto` y `…_una_lectura_por_obra`
- [ ] T9: transfer, ajustar los tests de F-044 que fijan el orden viejo (design §10), cada cambio con su requisito en el informe (R22)  |  Verificación: `pytest services/dedicacion-transfer/tests` en verde
- [ ] T10: api, `METODOS_PROPUESTA_VINCULADO` ampliado, `_vinculado` con `descripcion`, `SubfilaVinculado.descripcion` en `_a_subfila`, `peticion_de_subfilas` con `tipo_res` y `descripcion` (R17, R18)  |  Verificación: `services/dedicacion-api/tests/test_f068_api.py` (payload de registro y de propuesta, guardado en preflight y en la cola del mes) y `test_f044_*` de la api
- [ ] T11: front, rótulo `capitulo_ci4` en `rotuloOrigen` (R20)  |  Verificación: `services/dedicacion-front/tests/test_f068_front.py` y `test_f044_vinculados_front.py`
- [ ] T12: docs, `#regla-vinculado` (Partida y Lecturas) y `INTEGRACION.md` §5 (R21)  |  Verificación: `test_f002_fuente_unica.py` y revisión del reviewer
- [ ] T13: MANUAL (humano), solo lectura, con el transfer y la api de la rama en local: abrir el selector de partida de las subfilas del caso de la 0678 (periodo 2026-10) y lanzar el preflight de esa obra SIN «Registrar»; esperado: `CI.4.13`, `CI.4.1` y `CI.4.15` con método «parte anterior» y su origen (R23)  |  Verificación: MANUAL (humano): UI del cuadrante → subfila → selector; modal de registro → Cancelar
- [ ] T14: al desplegar (transfer → api → front): comprobar si `azure-apps/dedicacion.md` lista las lecturas del transfer contra `sigrid-api` y, si las lista, añadir `historial_de_vinculados`; si se eligió D4-B, el humano limpia las propuestas guardadas (comando en `progress/manual_F-068.md`)  |  Verificación: MANUAL (humano)
- [ ] T15: ejecutar `bash harness/init.sh` en verde (incluye mutación completa, rigor crítico)  |  Verificación: `bash harness/init.sh`
