<!-- progress/impl_F-022.md -->
# F-022 · El transfer busca cada obra por código y empresa — informe del implementer

Rigor **crítico**. Rama `feature/F-022-transfer-obra-por-empresa`. Spec
aprobada (D1-D4) implementada tal cual; D5 no se toca (es F-026).
Tareas T1-T9 y T11 hechas con un commit cada una; **T10 es MANUAL del
humano y queda pendiente** (ver al final).

## Qué cambió

**Transfer (`services/dedicacion-transfer`)**
- `domain/errores.py` (nuevo): `EmpresasMezcladas(ValueError)`,
  `ObraAmbigua(RuntimeError)`. `LineaEntrada.empresa` y `ObraEntrada.empresa`.
- `sigrid_write_client.py`: constructor sin `empresa`;
  `obra_por_codigo(cod, empresa)` con `con.cod = ? AND con.emp = ?`
  parametrizados; las dos búsquedas leen `con.emp AS emp`; `_obra` filtra
  por empresa también en Python, falla con `ObraAmbigua` ante 2+ fichas y
  nunca toma «la primera»; `stmts_crear_parte` escribe `con.emp` = empresa
  de la obra destino (`ValueError` si no la trae).
- `reglas_porcentajes.py`: `MOTIVO_SIN_EMPRESA`, `MOTIVO_EMPRESA_OBRA`,
  `empresa_valida`, `empresa_de_peticion`, `motivo_empresa` en
  `ReglasPorcentajes`; `decidir` omite por empresa ANTES de la postventa.
- `registro_pipeline.py`: paso 0 (empresa de la petición; sin empresa u obra
  de otra empresa → todas omitidas sin seguir, `_todas_omitidas`);
  `_obra_origen` en los dos modos; pruebas y postventa por (código,
  empresa); `ObraAmbigua` en postventa → motivo; la partida normal usa el
  origen ya resuelto (R14).
- `app.py`: `LineaIn.empresa` opcional; `EmpresasMezcladas` → 422 antes del
  502 genérico. `settings.py` y `.env.example` sin `SIGRID_EMPRESA`.
  `prueba_escritura_porcentajes.py`: `EMPRESA_PRUEBA = 1` en líneas y
  búsquedas; fases y salvaguardas intactas.

**API (`services/dedicacion-api`)**
- `settings.py`: `empresa_imputacion: Annotated[int, Field(gt=0)] = 1`.
- `registro_sigrid.py`: `RegistroSigrid(session_factory, transfer,
  empresa_imputacion)` sin defecto; `empresa` en cada línea. `deps.py` y
  `.env.example` (`EMPRESA_IMPUTACION=1`).

**Documentación e infra**
- `docs/ARCHITECTURE.md`: punto 12 `#regla-empresa`; remisiones en P5,
  `#regla-pruebas` y en la cabecera de la sección. README del transfer
  (tabla de anclas y contrato de la línea). `docs/INTEGRACION.md` §3, §9,
  fecha y commit de origen (`f9b3a46`). `infra/create_transfer_dedicacion.ps1`
  sin `SIGRID_EMPRESA`. `test_f002_fuente_unica.py`: `regla-empresa` en `ANCLAS`.
- `C:\Users\pgris\PycharmProjects\azure-apps\dedicacion.md`: refrescada,
  **sin commit** (lo hace el humano). Ver «Desviaciones», punto 3.

Tests nuevos: `services/dedicacion-transfer/tests/test_f022_obra_por_empresa.py`
(dominio, cliente, reglas, pipeline, app, documentación) y
`services/dedicacion-api/tests/test_f022_empresa_en_linea.py`.

## Decisiones de diseño (dentro de la spec)

- `con.emp` nulo en Sigrid: `int(emp or 0)`. Una ficha sin empresa no casa
  con ninguna pedida (filtro) y, leída por `ide`, sale con empresa 0, que el
  paso 0 trata como «de otra empresa» (R11). No se adivina.
- `empresa_valida` usa `type(valor) is int`: un `bool`, un `float` o un `"1"`
  no son empresa (en el contrato HTTP pydantic ya convierte a `int`).
- El fin anticipado del paso 0 construye las acciones con
  `ReglasPorcentajes({})`: toda línea se omite antes de mirar horas, así que
  no hace falta leer recursos (R3: cero lecturas).
- A `_destino_postventa` se le sigue pasando la obra de ENTRADA para casar
  la partida (design: «resto igual»); solo gana la empresa.

## Desviaciones respecto a la spec (justificadas)

1. **Orden, no alcance.** `empresa=1` en las LÍNEAS de los dobles
   (`conftest.linea()`, `test_pipeline_offline.lineas_entrada()`) entró en
   el commit de T3 y no en el de T4: con las reglas nuevas la suite quedaba
   en rojo (91 fallos) entre los dos commits. Ningún assert cambia.
2. **Dato de doble.** `conftest.ClienteFalso` conoce la obra `0001`
   (`OBRA_SIN_PARTIDA_PV`): `test_f013_la_postventa_sin_partida_se_sigue_omitiendo`
   la usa como origen y, desde R10, el origen se resuelve también en
   pruebas (riesgo asumido en design §8). El test no cambia. Las tres
   construcciones de `RegistroSigrid` en `test_f003_esquema.py` pasan
   `empresa_imputacion=1` (la firma no tiene defecto); ningún assert cambia.
3. **T8, lo decide el humano.** La copia de `azure-apps` ya divergía del
   cuerpo de `INTEGRACION.md` antes de F-022 en 4 bloques ajenos: §1
   `ruesma_rep` (corrección hecha EN la copia por `sigrid-api`, commit
   `a40684f` de azure-apps), §5 tarjeta del Portal, §5 «Quién puede entrar»
   y §6 filas de FQDN. Copiar el cuerpo entero habría borrado la corrección
   de `ruesma_rep`. Se hizo lo no destructivo: cabecera nueva + las tres
   piezas de F-022 copiadas literales. El `diff` del cuerpo ya no tiene
   ninguna diferencia de F-022 pero sí esos 4 bloques, así que el criterio
   literal de T8 («sin diferencias») **no se cumple por causas previas**.
   Pendiente: commit en `azure-apps` y decidir si `ruesma_rep` se porta a
   `INTEGRACION.md`.

## Fuera de alcance y lo que falta

- Fuera (spec): recurso por empresa (D5 → F-026), numeración `PTaa/nnnnn`,
  F-023/F-024/F-018. El front no se toca.
- Falta: **T10** (MANUAL, abajo); **commit en `azure-apps`** de
  `dedicacion.md` (humano); decidir lo de `ruesma_rep` (Desviación 3); mirar
  en `arnes-base` el falso superviviente de la primera campaña (Evidencias).
- `ruff`: 185 → 193 avisos en todo el repo; los nuevos siguen el estilo ya
  existente de los ficheros tocados (`Optional`, orden de imports). No bloquea.

## Fase RED (trazas reales, antes del código)

Comandos desde el servicio con su venv (`.venv/Scripts/python.exe -m pytest ...`).

**T1 · dominio (R1, R9)** — `python -m pytest tests/test_f022_obra_por_empresa.py -q -k dominio` (transfer)

    E       AssertionError: assert 'empresa' in {'registro_id': Field(name='registro_id',type='int',...
    E       AssertionError: assert 'empresa' in {'ide': Field(name='ide',type='Optional[int]',default=None,...
    E       ModuleNotFoundError: No module named 'domain.errores'
    3 failed in 0.31s

**T2 · cliente (R5-R9, R17; R7 = POSTV2 en 1 y 28, dos órdenes)** — `... -k cliente`

    E       TypeError: SigridWriteClient.obra_por_codigo() takes 2 positional arguments but 3 were given   (x8)
    E       AssertionError: assert (ObraEntrada(ide=9028, codigo='POSTV2', nombre='POSTVENTA emp 28', empresa=None) is not None and None == 28)
    E       assert 1 == 28                                   (R17: con.emp salía del ajuste, no de la obra)
    E       Failed: DID NOT RAISE ValueError
    E       assert 'empresa' not in mappingproxy(OrderedDict({'self': ..., 'base_url': ...
    FAILED ...test_f022_r7_cliente_postv2_elige_la_empresa_pedida[pide_1-filas_1_28]  (y los otros 3 casos)
    13 failed, 2 passed, 3 deselected in 1.44s

**T3 · reglas (R2, R4, R11)** — `... -k reglas`

    E       AttributeError: module 'application.services.reglas_porcentajes' has no attribute 'empresa_valida'   (x9)
    E       AttributeError: module 'application.services.reglas_porcentajes' has no attribute 'empresa_de_peticion'   (x6)
    E       AttributeError: ... has no attribute 'MOTIVO_SIN_EMPRESA'. Did you mean: 'MOTIVO_SIN_RECURSO'?
    E       AssertionError: assert 'escribir' == 'omitir'     (x3: la línea sin empresa se escribía)
    21 failed, 1 passed, 19 deselected in 1.53s

**T4 · pipeline (R3, R4, R10-R17)** — `... -k pipeline`

    E           TypeError: ClienteEmpresas.obra_por_codigo() missing 1 required positional argument: 'empresa'   (x21)
    E       AssertionError: assert [('ide', 5550...ide', 555001)] == [('ide', 555001)]
    E         Left contains one more item: ('ide', 555001)      (R14: la obra de origen se buscaba dos veces)
    22 failed, 41 deselected in 2.10s

**T5 · app (R1, R4, R8, R18)** — `... -k app`, ya sin `SIGRID_EMPRESA` en el constructor

    E       AssertionError: assert ['la línea ll...o se escribe'] == ['sin recurso...o se escribe']   (R1: el campo no llegaba)
    E       assert 200 == 422      (x2: R4, preflight y ejecutar)
    E       assert 200 == 502      (x2: R8)
    E       assert None == 1       (x2: R18)
    7 failed, 1 passed, 64 deselected in 2.32s

**T6 · API (R20, R21)** — `python -m pytest tests/test_f022_empresa_en_linea.py -q` (api)

    E       TypeError: RegistroSigrid.__init__() takes 3 positional arguments but 4 were given   (x4)
    E       Failed: DID NOT RAISE TypeError
    E                   AttributeError: 'Settings' object has no attribute 'empresa_imputacion'   (x2)
    E       Failed: DID NOT RAISE ValidationError   (x3: 0, -1, "x")
    E       AssertionError: assert 'EMPRESA_IMPUTACION=1' in '# .env.example ...
    11 failed in 3.97s

**T7 · documentación (R22, D4)** — `python -m pytest tests/test_f002_fuente_unica.py -q` y `... -k "r22 or r23"`

    E       AssertionError: regla-empresa
    E       assert 0 == 1
    2 failed, 60 passed in 0.47s
    E       assert '(#regla-empresa)' in '<a id="regla-p5"></a>**Postventa es una obra, no una marca (P5).** ...
    E       assert 'SIGRID_EMPRESA' not in '# infra/cre... Yellow\n}\n'
    2 failed, 72 deselected in 1.25s

Tras el código, cada bloque en verde (ver «Evidencias»).

## Verificación MANUAL pendiente (humano) — T10 / M1

Preflight real, **solo lectura**, con el transfer en modo pruebas (API 8090
y transfer 8006 en local) sobre un periodo con una línea de postventa:

    curl -s -X POST http://127.0.0.1:8090/api/v1/periodos/AAAA/MM/registro/preflight -H "Content-Type: application/json" -H "X-Usuario: <usuario>" -d "{}"

Comprobar, en la obra con postventa: `obra_postventa.empresa == 1`,
`obra_destino.codigo == "0404"`, `obra_destino.empresa == 1`. Resultado real
a anotar en `progress/current.md`. **NO** se lanza `registro/ejecutar`. No
ejecutada por el agente (regla: ninguna llamada a sigrid-api).

## Evidencias

Medido el 2026-09-30 sobre HEAD `9bb8d6b` (código de producción igual que en
`dfe079d`, el SHA de la campaña: después solo cambian `progress/` y `tasks.md`).

| Evidencia | Valor real |
|---|---|
| Tests del transfer | **309 passed**, 0 fallos, 9,76 s (75 de F-022) |
| Tests de la API | **123 passed**, 0 fallos, 11,47 s (11 de F-022) |
| Tests de la raíz (`init.sh`) | **355 passed, 1 skipped**, 56,88 s |
| `bash harness/init.sh` | **ENTORNO LISTO**, exit 0 (T11) |
| Cobertura de líneas cambiadas | **97,4 %** (76/78, umbral 80 %) — `PUERTA COBERTURA` |
| Mutación | **28 generados, 28 muertos, 0 supervivientes**, 0 timeouts, 0 sin veredicto — `progress/mutacion_F-022.md` |
| Workers de la campaña | **1** (en serie). Tiempo total 174,0 s; media 6,2 s/mutante; líneas base 16,0 s (api) y 9,0 s (transfer) |
| Tamaño del papeleo | dentro de los topes (`PUERTA TAMAÑO`) |

**Campaña descartada, por escrito.** La primera pasada (SHA `c4d9c3e`, 29
mutantes, 230,8 s, 1 worker) dio 5 supervivientes. Tres eran reales y se
arreglaron: `sigrid_write_client.py:140` (`filas[0]['cod']` → `filas[1]`,
equivalente en la práctica: el mensaje de obra ambigua ahora usa el código
PEDIDO y el índice desaparece) y los dos de `prueba_escritura_porcentajes.py`
(`EMPRESA_PRUEBA = 1 → 2`, `es_postventa True → False`: test nuevo
`test_f022_r13_script_de_pruebas_imputa_a_la_empresa_de_la_0404`). Los otros
dos (`registro_pipeline.py:109` `is None → is not None` y `:116`
`return destino, True → False`) eran **falsos supervivientes**: aplicados a
mano en el árbol, con el mismo comando que la campaña
(`PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe -m pytest -x -q --tb=no
-p no:cacheprovider`), mueren (`FAILED test_f002_r11_modo_pruebas_destino_y_partida`;
en una copia aislada, 9 fallos incluidos `test_f022_r13_...` y
`test_pipeline_offline`). Causa no aislada; sospecha: `__pycache__` de mis
ejecuciones previas en el árbol. Se borraron `__pycache__` y `.pytest_cache`
y se relanzó: esos dos mutantes salen **muertos** en la segunda pasada, que
es la válida. Defecto candidato del arnés, a mirar en `arnes-base`.
