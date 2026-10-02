# F-026 · Informe del implementer — BLOQUEADA

## Motivo del bloqueo (leer primero)

**La lista cerrada de tests que cambian (design §7) se queda corta.** Al hacer
T2 aparecen asserts de tests anteriores que la spec obliga a cambiar y que §7
no declara. La regla del encargo es explícita («cualquier otro cambio de
assert, para y responde `blocked`»), así que paro en T2, igual que pasó en
F-034. Hace falta que el humano **amplíe §7** con la lista de abajo (o decida
otra cosa caso a caso) antes de seguir.

Lo que se encontró es una **consecuencia directa de R1, R6 y R16** de la spec
aprobada, no un fallo del código. Para que solo haya una ronda de ampliación,
repasé de antemano los tests que tocarán T3-T9 (lectura de los tests y del
código; T3-T9 todavía no están implementadas). La lista es mi mejor
predicción, no una ejecución.

## Estado de la rama

- Rama `feature/F-026-recursos-sin-ficha-empleado`, sobre `5a02ddb` (dev con
  F-034, T0).
- **T0 [x]** (ya estaba: `git log dev` contiene `5f498cb`, el merge de F-034;
  `init.sh` en verde al empezar).
- **T1 [x]**, commit `3627a6b`: `services/dedicacion-api/domain/vigencia.py`
  (`inicio_de_mes`, `vigente_en`, `inicio_ventana_baja`) y
  `services/dedicacion-api/tests/test_f026_vigencia.py` (R12, R14: 15 tests).
- **T2 hecha pero SIN commit, guardada en un stash** para que la rama siga en
  verde (si la commiteo, `init.sh` queda en rojo por un test no declarado y el
  siguiente implementer no cumple su precondición):
  `stash@{0}` «F-026 T2 (SQL desde dbo.res + test_f026_sync_recurso.py): en
  espera de ampliar la lista cerrada de design §7». Contiene la SQL nueva de
  `sync.empleados` (design §6, literal), los comentarios de `config.yaml`, la
  clave `excluir_baja_anterior_a_ventana: true` y
  `tests/test_f026_sync_recurso.py` (R1 + clave de R13, 7 tests en verde).
  Para retomarla: `git stash pop` en esta rama.
- T3-T17 sin empezar. `progress/current.md` y `harness/features.json` sin
  tocar (lo pidió el líder): marcar `blocked` lo hace él.

## Tests no declarados que hay que cambiar

### A. `services/dedicacion-api/tests/test_f023_sync_empresa.py`

| # | Test | Por qué cambia (requisito) | Propuesta |
|---|---|---|---|
| A1 | `test_f023_r5_empleados_sin_filtro_de_emphis` | Su 2.º assert prohíbe todo `WHERE` tras `) AS hm`; R1 exige `WHERE res.cla = 1` ahí. **Comprobado**: falla con la SQL de T2 | El 2.º assert pasa a «lo único tras `) AS hm` es `WHERE res.cla = 1` y no menciona `fecbaj`» (ya lo prueba `test_f026_r1_sin_where_de_actividad`); o retirarlo |
| A2 | `test_f023_r16_criterio_vacio_no_descarta_por_estado` | `assert con_criterio.excluidos_otra_empresa == 0`: el atributo desaparece (design §5.1, R6) | Borrar esa línea; `baja_recurso=80000` → `fecha_baja=80000` |
| A3 | `test_f023_r16_criterio_por_defecto_es_vacio` | `criterio.excluir_con_fecha_baja is False`: el campo se renombra (§5.1) | → `criterio.excluir_baja_anterior_a_ventana is False` |
| A4 | `test_f023_r12_interruptor_apagado_no_filtra_por_estado` | Sin cambio de assert: solo `excluir_con_fecha_baja=True` → `excluir_baja_anterior_a_ventana=True` y `baja_recurso` → `fecha_baja` | Aceptar como cambio de construcción |
| A5 | `test_f023_r18_preview_y_sync_aplican_el_mismo_criterio` | `_entrada_r18` trae `_emp(4, empresa_recurso=18)`; sin filtro de empresa (R3, §5.1) el 4 entra | `([1], [1])` → `([1, 4], [1])`; clave del config renombrada |
| A6 | `test_f023_r18_interruptor_general_apagado_llega_a_los_dos` | Ídem | `([1, 2, 3], [1])` → `([1, 2, 3, 4], [1])`; clave renombrada |
| A7 | `test_f023_r18_config_sin_claves_de_recurso_no_filtra_por_estado` | Ídem | `([1, 2, 3], [1])` → `([1, 2, 3, 4], [1])` |
| A8 | `test_f023_r18_filtro_estado_recurso_encendido_por_defecto` | Ídem | `([1, 3], [1])` → `([1, 3, 4], [1])` |

Alternativa a A5-A8: quitar la fila 4 de `_entrada_r18` (ya no representa
nada) y dejar los asserts como están. Elige el humano; yo prefiero cambiar los
asserts, porque fijan que el filtro de empresa ya no existe.

### B. `services/dedicacion-api/tests/test_f024_registro_empresa.py`

| # | Test | Por qué cambia | Propuesta |
|---|---|---|---|
| B1 | `test_f024_r18_trabajador_no_visible_no_llama_al_transfer` | `assert r == {"ok": True, "obras": []}`; con R16 la respuesta lleva siempre `no_vigentes` («vacía si no hay», design §5.4). §7 dice de este fichero «ningún assert cambia» | → `{"ok": True, "obras": [], "no_vigentes": []}` |

### C. Cambios de DOBLES (sin assert) que conviene dejar aceptados ya

No son cambios de assert, pero tocan dobles o tests que §7 no nombra; los
listo para no volver a parar en T5-T8:

- **C1.** `_UowEspia` de `test_f023_sync_empresa.py` y de
  `test_f032_empresas_sigrid.py` ganan `periodos` (un doble con `listar()`
  que devuelve `[]`): `FetchEmpleadosStep` lee los periodos `ABIERTO` (design
  §5.3). Afecta a los `r6` de F-023 y a los `r1` de F-032, sin tocar asserts.
- **C2.** `_contenedor` de `test_f023_sync_empresa.py` construye el contenedor
  con `session_factory=None`; con la fábrica de UoW que pide §5.3 para
  `PreviewSync`, el preview abriría `SqlAlchemyUnitOfWork(None)`. El doble
  sustituye `deps.SqlAlchemyUnitOfWork` por una UoW falsa de solo lectura.
  Afecta a los seis `r18`.
- **C3.** Los trabajadores `SimpleNamespace` de `test_f022_empresa_en_linea.py`
  y `test_f024_registro_empresa.py` (este lo reutiliza `test_f034_*`) ganan
  `activo=True` además de `fecha_baja=None`: `vigente_en` lee los dos (R14,
  R16). §7 solo nombra `fecha_baja`.

### D. Revisado y sin cambios previstos

`test_f024_cuadrante_empresa.py` (sus `Trabajador` toman `fecha_baja=None`
por defecto), `test_f024_rutas_empresa.py` y `test_f034_rutas.py` (el
registro es un doble), `test_f003_esquema.py`, `test_f008_*`; en el transfer,
la lista de §7 cuadra con lo que encontré (`grep empleado_ide`: `conftest.py`,
`test_f002_reglas.py`, `test_f002_pipeline.py`, `test_f013_sin_partida.py`,
`test_f022_obra_por_empresa.py`, `test_pipeline_offline.py`).

## Qué cambió (lo commiteado)

| Fichero | Cambio |
|---|---|
| `api/domain/vigencia.py` (nuevo) | `inicio_de_mes` (`AAAAMM01`), `vigente_en` (`activo and (not fecha_baja or fecha_baja >= AAAAMM01)`), `inicio_ventana_baja` (mín. del mes anterior a `hoy`, enero → diciembre, y de cada abierto) |
| `api/tests/test_f026_vigencia.py` (nuevo) | R14 (sin baja, 0, día 1, último día, posterior, mes anterior ×2, inactivo ×2), R12 (sin abiertos, enero, abierto más antiguo, abierto posterior, iterable) |
| `specs/F-026-.../tasks.md` | T0 y T1 marcadas |

## Decisiones

1. **`vigente_en` trata `0` como sin baja** (`not fecha_baja`), igual que
   Sigrid, aunque el repositorio guardará `NULL`: así la función no depende de
   que alguien haya normalizado antes.
2. **T2: `test_f026_r1_sin_empleado_ide_ni_alias_antiguos`** comprueba que no
   queda ningún `con.` de la ficha de empleado con
   `(?<![\w.])con\.` (un `in "con.emp AS empresa"` casaba con `rcon.emp`).
3. **Intérprete.** Los tests se lanzan con el `.venv` de cada servicio
   (`harness/servicios.json`); el `python` de la raíz no tiene `pydantic`.

## Fase RED (trazas reales)

**T1 · R12/R14.** Comando (desde `services/dedicacion-api`):
`python -m pytest tests/test_f026_vigencia.py -q -p no:cacheprovider`
→ `15 failed in 0.31s`. Extracto (`-k "r12_ventana_en_enero or
vigente_en_octubre and True-20261001"`):

```
E       ImportError: cannot import name 'vigencia' from 'domain' (C:\Users\pgris\PycharmProjects\porcentajes\services\dedicacion-api\domain\__init__.py)
tests\test_f026_vigencia.py:23: ImportError
FAILED tests/test_f026_vigencia.py::test_f026_r14_vigente_en_octubre[True-20261001-True]
FAILED tests/test_f026_vigencia.py::test_f026_r12_ventana_en_enero_es_diciembre_del_anio_anterior
```

Tras escribir `vigencia.py`: `15 passed in 0.08s`.

**T2 · R1 (en el stash).** Comando:
`.venv/Scripts/python -m pytest tests/test_f026_sync_recurso.py -q -p no:cacheprovider`
con el `config.yaml` de `dev`:

```
E       assert ' FROM dbo.res AS res JOIN dbo.con AS rcon ON rcon.ide = res.ide ' in "SELECT emp.ide AS ide, con.cod AS cod, con.res AS nombre, emp.dni AS dni, con.emp AS empresa, tip.res AS categoria
E       assert 'LEFT JOIN dbo.emp AS emp ON emp.ide = res.conide AND res.conide > 0' in "SELECT emp.ide AS ide, con.cod AS cod, ...
E       AssertionError: assert [('emp.ide', ...egoria'), ...] == [('res.ide', ...mpresa'), ...]
E           AssertionError: recurso_ide
E       AssertionError: assert False
E       assert False
E       KeyError: 'excluir_baja_anterior_a_ventana'
7 failed in 1.01s
```

Con la SQL nueva: `7 passed in 0.95s`. Suite de la API con T2 aplicada:
`4 failed, 386 passed` — `test_f023_r4_…` y `test_f023_r5_config_…`
(declarados, se adaptan en T2/T3), `test_f023_r18_con_el_config_real_…`
(declarado, verde cuando lleguen T3 y T5) y **`test_f023_r5_empleados_sin_
filtro_de_emphis` (no declarado: A1, el que dispara el bloqueo)**.

## Verificaciones MANUAL pendientes

Las de la spec (T14 vaciado + sync real en local, T15 preflight de solo
lectura, T16 copia a `azure-apps`, despliegue de design §8) siguen intactas y
se escribirán con su comando exacto al terminar la feature. Nada de esta
sesión ha llamado a Sigrid, a `sigrid-api` ni a ninguna base, ni ha lanzado
`registro/ejecutar`.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados | `init.sh`: raíz `355 passed, 1 skipped in 46.35s`; servicio api `383 passed, 1 warning in 23.94s`; front y transfer en verde (caché) |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 12 líneas cambiadas cubiertas (12/12, umbral 80%, nivel critico)` (`vigencia.py`) |
| Mutación | **No lanzada**: es T13 y la feature está bloqueada en T2 |
| Tiempo de la suite | 46.35 s (raíz) y 23.94 s (api) |

`bash harness/init.sh` tras escribir este informe (con T2 en el stash):
**ENTORNO LISTO**; `PUERTA TAMAÑO: ... impl 166/220`.
