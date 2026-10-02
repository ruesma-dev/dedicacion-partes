<!-- progress/impl_F-026.md -->
# F-026 · Informe del implementer (rigor `critico`)

**Estado: T0-T13 hechas y ciclo 2 de la review 1 hecho (§5 bis), `bash
harness/init.sh` en verde. Pendiente: aceptación del humano del superviviente
equivalente (§8), MANUAL T14-T16 y review 2.** Bloqueo previo (2026-10-02, en T2: la lista cerrada de
design §7 se quedaba corta) resuelto por el humano: aprobó A1-A8, B1, C1-C3 y
el cambio de método (tabla de §3). Rama `feature/F-026-recursos-sin-ficha-empleado`.

## 1. Qué cambió (commits `F-026 Tn`)

| T | Commit | Cambio |
|---|---|---|
| T1 | `3627a6b` | `api/domain/vigencia.py`: `inicio_de_mes`, `vigente_en`, `inicio_ventana_baja` |
| T2 | `75271a3` | SQL de `sync.empleados` desde `dbo.res` (design §6, literal), `excluir_baja_anterior_a_ventana: true`, comentarios |
| T3 | `4470eb7` | `filtros_maestros.depurar_empleados`: sin filtro de empresa ni dedupes, `baja_desde`, `_AUXILIARES` nuevo, `incluidos_con_baja`, `posible_misma_persona`; log del step y claves R6 del preview fuera; `deps.py` con la clave nueva |
| T4 | `7430032` | `TrabajadorORM.fecha_baja` (Integer nulable sin default), `Trabajador.fecha_baja`, `sincronizar` la guarda (0 → NULL, su cambio cuenta), `_a_trabajador` |
| T5 | `0401422` | `sync_pipeline.ventana_de_bajas` + `FetchEmpleadosStep(hoy=date.today)` con los `ABIERTO` de `uow.periodos` |
| T6 | `d46f839` | `listar_para_periodo`: `activo = vigente_en(...)` del mes; no vigentes solo si tienen líneas |
| T7 | `c29bcea` | `PreviewSync(uow_factory, hoy)`: UoW solo de lectura; publica `ventana_baja`, `incluidos_con_baja`, `posible_misma_persona`; `deps.py` le pasa la fábrica |
| T8 | `a7c59dd` | `registro_sigrid._payloads`: `recurso_ide = t.ide`, sin `empleado_ide`; no vigentes → `no_vigentes`, ni se mandan ni se trazan |
| T9 | `9de76fb` | transfer: fuera `empleado_ide` (`LineaIn`, `LineaEntrada`, `AccionLinea`), `_horas_de_lineas`, fuera `recursos_de_empleados`, `MOTIVO_SIN_RECURSO` nuevo |
| T10 | `4560769` | `prueba_escritura_porcentajes.py` y README del transfer con `recurso_ide` |
| T11 | `255a1c7` | `infra/vaciar_datos_prueba_dedicacion.ps1` (BOM, CRLF, ASCII; **no ejecutado**) y §3 bis + fila §7 de `infra/README_dedicacion.md` |
| T12 | `be5efd0` | `ARCHITECTURE.md` punto 13 `#regla-recurso` y ajustes; `INTEGRACION.md` (cabecera, avisos, contrato, vaciado, qué se rompe); `ANCLAS` |
| T13 | `5bea52e` | test que mata el superviviente real; campaña en `progress/mutacion_F-026.md` |
| Rev. 1 | `df7e94c`, `cdfbe94` | `test_f026_r20_lineas_de_ejemplo_sin_editar_no_escriben` (transfer, solo test); campaña relanzada |

`dedicacion-front`, `.env`, `esquema.py`, `domain/empresas.py`: sin tocar. Sin
DDL a mano (la columna la deriva `esquema.py`, test R8). Ninguna llamada a
Sigrid, a `sigrid-api` ni a ninguna base; nadie lanzó `registro/ejecutar`.

## 2. Decisiones de diseño

1. **Orden en `_payloads`**: primero visibilidad por empresa, luego vigencia.
   Un no vigente de OTRA empresa no sale en `no_vigentes` (no es candidato en
   esa petición). `no_vigentes` va ordenado por `registro_id`.
2. **`baja_desde=None` no excluye por baja** aunque el criterio lo pida
   (design §5.1, «con él y `baja_desde`»). Step y preview siempre la pasan.
3. **`posible_misma_persona`**: grupos ordenados de `cod` ordenados; clave
   (empresa, documento); el documento se toma de la fila bruta (el `cif` no
   llega al upsert).
4. **`ventana_de_bajas`** vive en `application/sync_pipeline.py` y la
   comparten step y preview (una sola definición de «abiertos»).
5. **`-Local` del vaciado**: `psql -h localhost -d dedicacion -U $env:PGUSER`
   (o `postgres` si no está), contraseña por `Read-Host -AsSecureString` a
   `PGPASSWORD` solo durante la llamada. En Azure, rol `$PG_APP_USER`.
6. **`git diff` intermedio**: los commits T2-T6 dejaron en rojo tests
   DECLARADOS que dependen de pasos posteriores (r17 y r18 de F-023 necesitan
   la ventana en step y preview; `test_f022_r13` del transfer, el script de
   T10). Desde T7 (api) y T10 (transfer) todo en verde.

## 3. Tests anteriores cambiados (para el reviewer, uno a uno)

Lista aprobada (design §7 + A1-A8, B1, C1-C3) y los nuevos por el método del
2026-10-02 (marcados **M**). Ningún assert se quita sin sustituto.

| Test | Viejo → nuevo | Req. |
|---|---|---|
| f023 `r4_..._cinco_alias` | `con.emp AS empresa`, `rcon.emp AS empresa_recurso`, `rcon.fecbaj AS baja_recurso`, `LEFT JOIN dbo.con AS rcon` → `rcon.emp AS empresa`, `NULLIF(rcon.fecbaj, 0) AS fecha_baja`, `JOIN dbo.con AS rcon ON rcon.ide = res.ide` (+ conest y baja_laboral iguales) | R1 §7 |
| f023 `r5_sin_filtro_de_emphis` (A1) | «ningún `WHERE` tras `) AS hm`» → «tras `) AS hm` solo `WHERE res.cla = 1 ORDER BY …` y sin `fecbaj`» | R1 |
| f023 `r5_config_...` | `excluir_recurso_con_fecha_baja is True` → `excluir_baja_anterior_a_ventana is True` | R13 §7 |
| f023 `FECHA_BAJA`, `AUXILIARES`, `_emp` | «(fecha de baja del recurso)» → «(baja anterior a la ventana)»; `(recurso_ide, empresa_recurso, estado_recurso, baja_recurso, baja_laboral)` → `(cif, estado_recurso, baja_laboral)`; `_emp` sin `recurso_ide`/`empresa_recurso`, `baja_recurso: 0` → `fecha_baja: None` | R1 R13 §7 |
| f023 `r9` ×3, `r10` ×3, `r11` ×3, `r14` ×3 | **retirados** (12); los sustituyen `test_f026_r3_*` (4) y `test_f026_r4_*` (7) | R3 R6 §7 |
| f023 `r12_interruptor_apagado` (A4) | solo construcción (`fecha_baja`, clave nueva, `baja_desde`) | — |
| f023 `r13` ×2 | construcción + `baja_desde=VENTANA`; asserts iguales (`[2, 3]`, `{FECHA_BAJA: 2}`, `{"Baja": 1}`) | R13 §7 |
| f023 `r16_criterio_vacio` (A2) | fuera `excluidos_otra_empresa == 0` (el atributo no existe: lo prueba `test_f026_r6_*`) | R6 |
| f023 `r16_por_defecto` (A3) | `excluir_con_fecha_baja is False` → `excluir_baja_anterior_a_ventana is False` | §5.1 |
| f023 `r17_preview_...` | claves R6 → `not in`; `por_empresa {"1":2,"18":1}` → `{"1":4,"18":1}`; `total`/`por_codigo_mes`/`por_categoria` 3 → 5; `muestra [1,2,3]` → `[1,2,2,3,4]`; **+** `posible_misma_persona == [["E2","E2"]]`; fila 6 `baja_recurso` → `fecha_baja` | R3 R4 R6 §7 |
| f023 `r18_preview_y_sync…` (A5) | `([1],[1])` → `([1, 4],[1])`, clave renombrada | R3 |
| f023 `r18_interruptor…` (A6), `r18_config_sin_claves` (A7) | `([1,2,3],[1])` → `([1,2,3,4],[1])` | R3 |
| f023 `r18_filtro…_por_defecto` (A8) | `([1,3],[1])` → `([1,3,4],[1])` | R3 |
| f023 `r18_con_el_config_real` | `([1,2],[1])` → `([1,2,4],[1])`; `excluidos_recurso_otra_empresa == 1` → `not in emp` | R3 R6 R13 |
| f023 `_UowEspia` (C1), `_contenedor` (C2) | + `periodos` vacío; `deps.SqlAlchemyUnitOfWork` → UoW de lectura | R12 R17 |
| f032 fixture de `_SigridFalso` | sin `recurso_ide`/`empresa_recurso`, `baja_recurso` → `fecha_baja` | §7 |
| f032 `_UowEspia` (C1) | + `periodos` vacío | R12 |
| **M** f032 `_contenedor` | + `deps.SqlAlchemyUnitOfWork` → UoW de lectura (mismo motivo que C2: `r4_el_preview_real_usa_la_consulta_de_config` construye el preview real con `session_factory=None`); sin cambio de assert | R17 §5.3 |
| f022 `_fila`, f024 `_fila` (C3) | trabajador + `activo=True, fecha_baja=None` | R14 R16 |
| f024 `r18_trabajador_no_visible` (B1) | `{"ok": True, "obras": []}` → `+ "no_vigentes": []` | R16 |
| transfer `conftest.linea()` | `empleado_ide=10` → `recurso_ide=200`; dobles sin `recursos_de_empleados` ni `self.recursos` | R19 §7 |
| transfer `test_f002_reglas` (14 llamadas) | `, empleado_ide=None` borrado; `linea(recurso_ide=None, empleado_ide=10)` → `linea(recurso_ide=None)` (mismo assert: omitida por recurso) | R20 §7 |
| transfer `test_f002_pipeline` ×2, `test_f022_obra_por_empresa` ×2 | `empleado_ide=12` → `recurso_ide=400` | §7 |
| transfer `test_f013_sin_partida` ×3 | `empleado_ide=12` → `recurso_ide=400`; `empleado_ide=10` → `recurso_ide=200` | §7 |
| transfer `test_pipeline_offline` | 5 líneas `empleado_ide` → `recurso_ide` (10→200, 11→300); `a1.recurso_ide == 200` ahora prueba que el recurso dado se respeta | R19 §7 |
| transfer `test_f002_fuente_unica.ANCLAS` | + `regla-recurso` | R23 |

## 4. Verificación (resultado real)

- `bash harness/init.sh` (HEAD `cdfbe94`, ciclo 2): **ENTORNO LISTO**. Raíz
  `374 passed, 1 skipped in 44.68s`; transfer `330 passed, 1 warning in
  4.82s`; api y front en verde (caché; api `440 passed` en el ciclo 1, sin
  cambios desde entonces); `PUERTA COBERTURA` y `PUERTA TAMAÑO` en verde (§8).
- Criterio de cada tarea: T2-T12 con sus `test_f026_*` en verde; F-023,
  F-032, F-022, F-024, F-034, `test_f003_esquema` y `test_f008_*` en verde.
  `grep -rn empleado_ide services/dedicacion-transfer` (T10): solo en
  `tests/test_f026_recurso_dado.py`, que prueba que el campo se ignora.
- `infra/vaciar_datos_prueba_dedicacion.ps1`: **no ejecutado**; parseado con
  `[System.Management.Automation.Language.Parser]::ParseFile` → `errores: 0`.

## 5. Fase RED (trazas reales; comando desde el servicio, con su `.venv`)

T1 y T2: trazas del informe del bloqueo (`git show 6b53a65:progress/impl_F-026.md`):
`15 failed` (`ImportError: cannot import name 'vigencia'`) y `7 failed`
(`assert ' FROM dbo.res AS res JOIN dbo.con AS rcon ...' in "SELECT emp.ide AS ide, con.cod ...`).

**T3** `python -m pytest tests/test_f026_sync_recurso.py -q -p no:cacheprovider` → `14 failed, 10 passed`:
```
E       assert [736] == [61, 736]
E       AttributeError: 'ResultadoDepuracion' object has no attribute 'posible_misma_persona'
E           AssertionError: duplicados_recurso
E       TypeError: depurar_empleados() got an unexpected keyword argument 'baja_desde'
```
(Pasaban ya R1 ×7, `r2` y dos `r3` que el código viejo también cumplía.)

**T4** `python -m pytest tests/test_f026_vigencia.py -q -p no:cacheprovider` → `14 failed, 15 passed`:
```
E       AssertionError: assert [] == ['ALTER TABLE...baja INTEGER']
E               TypeError: 'fecha_baja' is an invalid keyword argument for TrabajadorORM
E       AttributeError: 'Trabajador' object has no attribute 'fecha_baja'
```
**T5** `... tests/test_f026_sync_recurso.py -k "r12 or r5"` → `6 failed`:
`TypeError: FetchEmpleadosStep.__init__() got an unexpected keyword argument 'hoy'`.

**T6** `... tests/test_f026_vigencia.py -k r15` → fallos como:
```
E         Differing items:
E         {4: True} != {4: False}
E         Left contains 2 more items:
E         {3: True, 6: False}
E       assert [1, 2, 3, 7] == [1, 2, 7]
E       AssertionError: assert 5 == 3
```
**T7** `... -k "r17 or r6_preview or r5_preview"` → `8 failed`:
`TypeError: PreviewSync.__init__() got an unexpected keyword argument 'hoy'`.

**T8** `... tests/test_f026_registro_recurso.py` → `10 failed`:
```
E   KeyError: 'recurso_ide'
E       assert [1, 2, 3, 4, 5, 6] == [1, 2, 6]
E       KeyError: 'no_vigentes'
```
**T9** (transfer) `... tests/test_f026_recurso_dado.py` → `6 failed, 4 passed`:
```
E        +  where True = hasattr(SigridWriteClient, 'recursos_de_empleados')
E         - la línea no trae el recurso del trabajador
E         + sin recurso en Sigrid para el empleado
E       AssertionError: el transfer no debe resolver el recurso
E       AssertionError: assert 'empleado_ide' not in {'registro_id': FieldInfo(...
```
(Los 4 que pasaban: el recurso dado ya se respetaba antes; R21 y R22.)

**T11** (raíz) `python -m pytest tests/test_f026_vaciado.py -q -p no:cacheprovider`
→ `19 failed in 0.80s`: el `.ps1` no existía (el último, `assert
'vaciar_datos_prueba_dedicacion.ps1' in '<!-- infra/README_dedicacion.md -->…'`).

**T13** test que mata el superviviente real, con la mutación aplicada a mano:
`E       AssertionError: assert 0 == 1` (`incluidos_con_baja`); sin ella, `1 passed`.

## 5 bis. Ciclo 2 (review 1): RED con los mutantes aplicados a mano

La review probó que 5 de los 6 «equivalentes» no lo eran. Vía (a): test R20
que fija sobre `LINEAS_PRUEBA` `registro_id` (y synckey) únicos, `recurso_ide`
0 en todas y el preflight omitiéndolas por `MOTIVO_SIN_RECURSO`. Sin mutar:
`1 passed`. Cada mutante con `sed` sobre el script y `git checkout` después;
comando `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
tests/test_f026_recurso_dado.py -k lineas_de_ejemplo`:
```
nº1 (47: 900001→900002)  E       AssertionError: [900002, 900002, 900003]
                         E       assert 2 == 3        -> 1 failed, 10 deselected
nº6 (53: recurso_ide 0→1) E       assert [0, 0, 1] == [0, 0, 0]  -> 1 failed
nº3 (50: 900002→900003)  E       AssertionError: [900001, 900003, 900003]
nº2 / nº4 (47 / 50: 0→1) E       assert [1, 0, 0] == [0, 0, 0] / [0, 1, 0] == ...
nº5 (53: 900003→900004)  1 passed, 10 deselected   (equivalente, §8)
```

## 6. Verificaciones MANUAL pendientes (no ejecutadas por nadie)

Comandos exactos y resultado esperado en `progress/current.md` («T14», «T15»).

1. **T14 (R24), local, con autorización del humano para el vaciado.**
   `.\vaciar_datos_prueba_dedicacion.ps1 -Local` (solo plan) y luego
   `-Local -Confirmar` (recuento 0/0/0/0); API de la rama, `GET
   /api/v1/sync/preview` (`ventana_baja`, `posible_misma_persona` con
   `MO/0061` y `MO/0736`) y `POST /api/v1/sync`; en la base, los diez de
   la lista activos con `ide` = su `res.ide`, ninguno con `fecha_baja <
   ventana_baja`, y vigencia por mes en dos meses abiertos.
2. **T15 (R25), preflight de SOLO LECTURA** con el transfer local en modo
   pruebas (`OBRA_PRUEBAS_FORZAR=true`): Eusebio (`1-MO/0772`) sale
   `escribir` con `recurso_ide` = su `res.ide`, nadie omitido «sin recurso»,
   `no_vigentes: []`. **NO lanzar `registro/ejecutar`.**
3. **T16**: copiar a `azure-apps/dedicacion.md` las piezas de T12 de
   `docs/INTEGRACION.md` (cabecera, avisos, vaciado en §2, contrato de la
   línea en §9, dos filas en cada tabla de §7) — lo hace el líder.
4. **Despliegue (D7)**: `infra/README_dedicacion.md` §3 bis, con F-034:
   republicar transfer y api juntos → vaciado (plan y `-Confirmar`, con
   autorización expresa) → `sync/preview` → `sync`. El transfer desplegado
   escribe de verdad: nada de `registro/ejecutar` hasta terminar.

## 7. Fuera de alcance y observaciones para el líder

- **Fila tras guardar.** `ObtenerFilaTrabajador` (respuesta de guardar y
  deshacer) usa `trabajadores.obtener`, que no conoce el mes: un trabajador
  NO vigente con líneas, si se edita, vuelve con el `activo` del ORM hasta
  recargar el cuadrante. `use_cases.py` queda fuera de la spec salvo
  `PreviewSync` (design §11): no se ha tocado. Candidato a feature pequeña.
- **El front no enseña `no_vigentes`** (el front no se toca): esas líneas no
  se registran ni se trazan y el usuario no ve el motivo en pantalla.
- **Arnés**: la campaña con `workers > 1` dio dos falsos supervivientes
  (`git show 1bdb08b:progress/mutacion_F-026.md`, «Notas»); la review lo
  confirma por tercera vez. F-034 sigue `blocked` en `features.json` (no lo toco).

## 8. Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados | raíz `374 passed, 1 skipped`; api `440 passed`; transfer `330 passed`; front en verde. Nuevos de F-026: api 84 (`sync_recurso` 39 + `vigencia` 35 + `registro_recurso` 10), transfer 11, raíz 19 |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 92 líneas cambiadas cubiertas (92/92, umbral 80%, nivel critico)` |
| Mutación (`critico`, en serie, `--workers 1`, campaña completa, HEAD `df7e94c`) | **56 generados, 55 muertos, 1 superviviente**, 0 timeouts, 0 sin veredicto; base api 14,5 s, transfer 4,5 s; media 10,3 s/mutante. Ciclo 1 (HEAD `5bea52e`): 50/56; los 5 no equivalentes que señaló la review, muertos por el test R20 (§5 bis) |
| Superviviente (nº 5 del ciclo 1) | `prueba_escritura_porcentajes.py:53` `900003→900004`: reproducido a mano, transfer `330 passed`. Equivalente: solo cambia un identificador arbitrario; unicidad, centinela y omisión siguen fijados por el test R20. Análisis en `progress/mutacion_F-026.md`. **Pide aceptación escrita del humano antes del `done`** |
| Tiempo de la suite | raíz 44.68 s; api 21.64 s (ciclo 1); transfer 4.82 s; mutación 576.9 s |
