<!-- specs/F-037-asiento-analitico-obra/tasks.md -->
# F-037 · Tareas

**Condición de entrada (humano, 2026-10-06): no se empieza T1 hasta que la F-031 de `partes` (rama `feature/F-031-asiento-analitico`) esté mergeada en su `dev`.** Se comprueba con este comando exacto, que debe listar un commit de F-031 sobre `cuenta_analitica.py` (el 2026-10-06 solo lista `b038943` y `9947927`, de F-021):

```
git -C C:\Users\pgris\PycharmProjects\partes log dev --oneline -- services/partes-transfer/application/services/cuenta_analitica.py
```

Mientras no lo liste, F-037 sigue en `spec_ready` y no se lanza el implementer. Si la F-031 final cambia la regla respecto a design §13, se revisa la spec antes de T1.

Rama `feature/F-037-asiento-analitico-obra`. Un commit por tarea (`F-037 Tn: …`). Tests `test_f037_rN_…`, sin red ni BBDD, escritos antes del código con su fase RED pegada en `progress/impl_F-037.md`. Spec aprobada por el humano el 2026-10-06 (D1-D16 decididas). Ninguna tarea automática lanza `registro/ejecutar`; R20-R21 las hace el humano con autorización expresa.

- [x] T0: decisiones D8, D10 y D12-D15 tomadas por el humano el 2026-10-06 (todas A; D15 autoriza la copia de `cuenta_analitica.py`, cuya línea en `CLAUDE.md` pone el líder). La confirmación de Administración queda en R21 (T12)  |  Verificación: requirements §6
- [x] T0b: D16 = A, decidida por el humano el 2026-10-06 (cualquier estado distinto de En registro va al complementario, como `partes`)  |  Verificación: requirements §6
- [ ] T1: `registro_models.py`: `HoraRecurso.caa_cod`/`defecto`, `AccionLinea.caa_ide`/`caa_cod`/`caa_origen`, `ParteDestino.estado`/`complementario`/`cerrados`/`ides_mes`, todos con defecto  |  Verificación: `pytest services/dedicacion-transfer/tests` en verde sin tocar ningún test
- [ ] T2: copiar `cuenta_analitica.py` de la versión vigente en `dev` de `partes` (design §13.1), ya con la F-031 mergeada (trae `subcuenta_de_partida`), con el commit en su docstring y en `progress/impl_F-037.md`  |  Verificación: `pytest services/dedicacion-transfer/tests/test_f037_cuenta_analitica.py` (R2-R5 y la comparación con `partes`)
- [ ] T3: `domain/parte_del_mes.py` con `elegir_parte` (D16: cerrado = `est != est_activo`) (design §5.2)  |  Verificación: `pytest services/dedicacion-transfer/tests/test_f037_complementario.py -k elegir` (R10, R11)
- [ ] T4: dobles de `tests/conftest.py` y `tests/test_pipeline_offline.py` según design §9.2, sin cambiar ningún assert  |  Verificación: `pytest services/dedicacion-transfer/tests` en verde y `git diff` de los dos ficheros sin líneas `assert` tocadas
- [ ] T5: `SigridWriteClient`: `_read` con `truncated`, `horas_de_recursos`, `cuentas_de_centro`, `cuentas_de_partidas`, `partes_existentes` con `con.est`, `stmt_insert_linea(caaide=…)`, docstring (design §5.3 y §6)  |  Verificación: `pytest services/dedicacion-transfer/tests/test_f037_cliente_sigrid.py` (R1, R8-R10, R15) y `test_f026_recurso_dado.py` en verde
- [ ] T6: pipeline paso 4 bis y `ejecutar` con `caaide` y `caa_cod` (design §7)  |  Verificación: `pytest services/dedicacion-transfer/tests/test_f037_pipeline.py` (R1, R3-R9, R16, R17)
- [ ] T7: pipeline pasos 5 y 7, creación y relectura del complementario, `MOTIVO_PARTE_CERRADO` (design §7)  |  Verificación: `pytest services/dedicacion-transfer/tests/test_f037_complementario.py` (R11-R14) y suite completa del transfer en verde
- [ ] T8: `docs/ARCHITECTURE.md`: punto 16 `#regla-analitica`, anclas, alcance de `#regla-conflicto` y `#regla-capacidad`, frase de `#regla-sin-partida`, «Acceso a datos»; `"regla-analitica"` en `ANCLAS`  |  Verificación: `pytest services/dedicacion-transfer/tests/test_f002_fuente_unica.py` y `git diff docs/ARCHITECTURE.md` revisado (R18)
- [ ] T9: `docs/INTEGRACION.md`: fecha y origen, §1 y §7 (R19)  |  Verificación: `pytest tests/test_f008_infra_sin_secretos.py` en verde y `git diff docs/INTEGRACION.md` revisado
- [ ] T10: campaña de mutación `critico` sobre las líneas cambiadas (design §10), cero supervivientes sin test o sin justificación aceptada por el humano  |  Verificación: `python -m harness.mutacion --feature F-037` con el informe en `progress/mutacion_F-037.md`
- [ ] T11: preflight de solo lectura en local (transfer de la rama con `OBRA_PRUEBAS_FORZAR=true`, api local): un trabajador MENC o MJEFO en un periodo de prueba y `POST http://localhost:8090/api/v1/periodos/AAAA/MM/registro/preflight` con `-d "{}"`; esperado `escribir` con `caa_cod` = `0404.CIMO03` o `0404.CIMO02`, `caa_origen` = `recurso`; uno MPRL con aviso de obra sin cuenta (0404 no tiene `CIMO16`). NO lanzar `registro/ejecutar`  |  Verificación: MANUAL (humano), resultado anotado en `progress/`
- [ ] T12: con autorización expresa del humano y Administración avisada, R20-R21 en local en modo pruebas, mes sin actividad en 0404: `ejecutar` de la línea; leer `SELECT hmores.caaide, con.cod, hmores.cenide, hmores.tot FROM hmores JOIN con ON con.ide = hmores.caaide WHERE hmores.synckey = 'porcentajes:<id>'`; Administración pulsa «Contabiliza parte…» (esperado `con.est = 10` y ANA con debe a `0404.CIMOxx` = `tot` y haber a `CP.<persona>`) y confirma que la línea se ve como una tecleada; otra línea del mismo mes va a un parte `(complementario)` nuevo que se contabiliza aparte; limpieza con `python prueba_escritura_porcentajes.py limpiar --confirmar` y anulación de los ANA y del complementario por Administración  |  Verificación: MANUAL (humano + Administración), resultado anotado en `progress/`
- [ ] T13: copiar a `azure-apps/dedicacion.md` las piezas de T9, literales, sin reescribir el resto (lo hace el líder)  |  Verificación: MANUAL (humano): revisar el `diff` y hacer el commit en `azure-apps`
- [ ] T14: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh`
