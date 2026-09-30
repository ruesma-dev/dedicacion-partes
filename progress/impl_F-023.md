# F-023 · Informe del implementer

> Sync de maestros: todas las empresas y activo según el estado del recurso.
> Rigor **crítico**. Rama `feature/F-023-sync-empresa-y-estado-recurso`.
> Spec: `specs/F-023-sync-empresa-y-estado-recurso/`. Estado: **T1-T9 y T12
> hechas (T9: D1 cerrada, ver al final); T10 y T11 MANUAL (humano) pendientes**.

## Qué cambió (solo `services/dedicacion-api/`)

| Fichero | Cambio |
|---|---|
| `infrastructure/db/orm_models.py` | `empresa: Mapped[int \| None] = mapped_column(Integer)` en `TrabajadorORM` y `ObraORM` (nulable, sin default, sin índice). Sin DDL a mano: el `ADD COLUMN` lo deriva `esquema.alters_faltantes`. |
| `domain/models.py` | `empresa: int \| None = None` como último campo de `Trabajador` y `Obra`. |
| `infrastructure/db/repositories.py` | `_entero()`; `empresa` en alta, actualización, `cambio` y en `_a_trabajador` / `_a_obra`. `listar_para_periodo` sin cambios. |
| `application/filtros_maestros.py` | `CriterioActivoRecurso` (frozen) + singleton `CRITERIO_VACIO`; `ResultadoDepuracion` gana `excluidos_otra_empresa`, `excluidos_estado_recurso`, `con_baja_laboral`; paso 0 fila a fila antes de los dedupes; clave de persona `"{empresa}\|dni:…"`; recuento de baja laboral; se retiran las columnas auxiliares antes del upsert. `depurar_obras` intacto. |
| `config/config.yaml` | Consultas de design §3 (obras con `con.emp AS empresa`; empleados con los cinco alias y **sin** `WHERE COALESCE(uh.fecbaj, 0) = 0`); claves `filtro_estado_recurso: true`, `estados_recurso_excluidos: []`, `excluir_recurso_con_fecha_baja: false` (T9 lo pasa a `true`), con citas a `sigrid_tablas.md` l. 5657-5658 y 6083-6089 (comprobadas). |
| `application/sync_pipeline.py` | `COLUMNAS_EMPLEADOS` / `COLUMNAS_OBRAS` (con `empresa`); `criterio` en `FetchEmpleadosStep`; log con los tres recuentos nuevos. |
| `application/use_cases.py` | `PreviewSync(criterio=…)`, valida columnas con el mismo `_validar_columnas` y las mismas constantes que el pipeline, y publica las claves de R17. |
| `interface_adapters/api/deps.py` | Un único `CriterioActivoRecurso` leído de `config.yaml` para step y preview. |
| `tests/test_f023_sync_empresa.py` | 53 tests `test_f023_rN_*` (R1-R18), sin red ni BBDD. |

No se tocan front, transfer, `schemas.py`, `routes.py`, `esquema.py`, `main.py`,
`sigrid_client.py` ni ningún `.env`/`.env.example` (la spec no lo pide).
`azure-apps/dedicacion.md` y `docs/ARCHITECTURE.md` no describen el criterio de
activo ni las columnas de los maestros: sin cambios (design §0).

## Commits (uno por tarea + dos de ajuste)

`5ae53d1` T1 · `d6b9dfc` T2 · `1ec0c14` T3 · `4cd9a2f` T4 · `75c67b7` T5 ·
`ebd78ab` T6 · `37dbce9` T7 · `35273f2` T8 · `7e1bf24` tests de los
supervivientes · `fd2831c` singleton `CRITERIO_VACIO` (ruff B008) y orden de
imports. Nada de push.

## Decisiones de diseño

- **Descarte por empresa del recurso (R9) siempre**, no bajo el interruptor
  `filtro_estado_recurso`: design §2 lo pone en el paso 0 fuera del
  `si criterio.activo`. Tiene test propio (`r9_…_aun_sin_criterio_activo`).
- **R12 y R13 bajo el interruptor general** `filtro_estado_recurso`: design §2
  anida los dos puntos tras «si `criterio.activo`:». Con el interruptor
  apagado ni los literales ni la fecha de baja descartan (test `r12_interruptor_apagado`).
- Fila con estado excluido **y** fecha de baja: se cuenta una sola vez, bajo
  el literal (el estado se evalúa antes).
- `por_empresa` del preview con **claves en texto** (`"1"`, `"28"`) y
  `"(sin empresa)"` para NULL, como el resto de desgloses (`por_categoria`…);
  en JSON las claves son texto de todos modos.
- Columnas requeridas en **constantes compartidas** por step y preview (R18:
  «la misma» validación, no dos copias).
- `CRITERIO_VACIO` como valor por defecto (instancia inmutable compartida) en
  vez de `CriterioActivoRecurso()` en la firma: ruff B008, y el `frozen` lo
  vigila un test (fue superviviente, ver «Evidencias»).

## Desviaciones respecto a la spec

1. **Comandos `-k` de tasks.md.** `pytest -k` casa por subcadena: `-k "r1 or r2"`
   (T2) selecciona también `r10`…`r18`, que en T2 aún no pueden pasar. Se
   verificó T2 con `-k "r1_ or r2_"` (4 passed), que es lo que la tarea
   pretende. En T6, `-k "r6"` incluye los tests R6 del **preview**, que son
   de T7 (su verificación repite `r6`): se verificó con
   `-k "r6 and pipeline"` (2 passed) y en T7 `-k "r6 or r17"` pasó entero (7 passed).
2. **`_entero` existe dos veces** (una línea cada una): en `repositories.py`
   (donde lo pide design §1) y en `filtros_maestros.py`, porque design §2 lo
   usa ahí y `application/` no puede importar de `infrastructure/`. Si se
   prefiere uno solo, su sitio sería `domain/normalizacion.py` (fichero que
   la spec no lista; por eso no se tocó).
3. **Tests adicionales** a la tabla de design §6: inmutabilidad del criterio,
   valores por defecto de `deps.py` con un `config.yaml` sin las claves nuevas,
   R8 con empresa en texto/nula y con fila previa a NULL, mapeo a dominio.

## Fase RED (T1, antes de escribir código)

Comando: `cd services/dedicacion-api && .venv/Scripts/python -m pytest tests/test_f023_sync_empresa.py -q -p no:cacheprovider --tb=line`
(commit `5ae53d1`, con el código de producción de `dev`). Salida real;
se pegan tal cual la barra, la primera aparición de cada error distinto (sin
las rutas de fichero ni las repeticiones) y el resumen. Los errores repetidos
son las mismas líneas para los demás tests del mismo requisito.

```
FFFFFFFFFFFFFFFFFFFFFFFFFFF...FFFFFFFFFFFFFFFFFFFF                       [100%]
E   KeyError: 'empresa'
E   AssertionError: assert set() == {'obra', 'trabajador'}
E   AssertionError: assert [] == ['ALTER TABLE...resa INTEGER']
      Right contains 2 more items, first extra item: 'ALTER TABLE trabajador ADD COLUMN IF NOT EXISTS empresa INTEGER'
E   AssertionError: assert 'con.emp AS empresa,' in 'SELECT obr.ide AS ide, con.cod AS cod, con.res AS descripcion, COALESCE(est.res, CAST(con.est AS VARCHAR(16))) AS est...on AS con ON con.ide = obr.ide LEFT JOIN dbo.conest AS est ON est.tip = con.tip AND est.est = con.est ORDER BY con.cod'
E   AssertionError: con.emp AS empresa,
E   AssertionError: assert 'COALESCE(uh.fecbaj' not in 'SELECT emp....res, res.ide'
      'COALESCE(uh.fecbaj' is contained here:
         hm WHERE COALESCE(uh.fecbaj, 0) = 0 ORDER BY con.res, res.ide
E   KeyError: 'filtro_estado_recurso'
E   AttributeError: module 'application.filtros_maestros' has no attribute 'CriterioActivoRecurso'
E   AttributeError: 'ObraORM' object has no attribute 'empresa'
E   AttributeError: 'TrabajadorORM' object has no attribute 'empresa'
E   TypeError: 'empresa' is an invalid keyword argument for ObraORM
E   TypeError: 'empresa' is an invalid keyword argument for TrabajadorORM
E   assert [2] == [1, 2]
E   assert ([1, 2, 3, 4], [1]) == ([1], [1])
E   assert ([1, 2, 3, 4], [1]) == ([1, 2, 3], [1])
E   assert [1, 2, 3, 4] == [1, 2, 3]
47 failed, 3 passed in 1.89s
```

Qué requisito cae en cada línea, en orden: R1 (columna ausente del ORM, y
ninguna tabla con `empresa`); R2 (`alters_faltantes` no emite nada); R3 (la
SQL de obras sin `con.emp AS empresa`); R4 (la de empleados sin los alias);
R5 (el `WHERE COALESCE(uh.fecbaj, 0) = 0` sigue, y faltan las claves D1);
R6, R9, R12-R17 (`CriterioActivoRecurso` no existe); R7-R8 (`empresa` ni se
guarda ni se acepta); R11 (`[2] == [1, 2]`: dos fichas con el mismo DNI en las
empresas 1 y 18 colapsan en una); R18 (el criterio no llega ni al sync ni al
preview, y con el config real entra el recurso de otra empresa).

Los 3 que pasaban son los de **R10** («mismo DNI y misma empresa → una
ficha»): R10 pide **conservar** el comportamiento de hoy, así que su test es
de caracterización y debe pasar antes y después. El cambio de dedupe lo
demuestran en rojo los tres tests de R11.

Verde tarea a tarea: T2 `-k "r1_ or r2_"` 4 passed + `test_f003_esquema.py`
63 passed · T3 `-k "r7 or r8"` 11 passed · T4 `-k "r9 … r16"` 20 passed ·
T5 `-k "r3 or r4 or r5"` 4 passed · T6 2 passed · T7 7 passed · T8
`-k "r18"` 4 passed y suite del servicio 173 passed.

## Verificaciones MANUAL (humano) pendientes

No ejecutadas por el implementer (fuera de alcance por instrucción del líder;
descritas en `progress/current.md` y en tasks.md):

- ~~**T9**~~ · cerrada el 2026-10-01 sin lanzar Q1 (sección «T9 · D1 cerrada»).
- **T10** · R19 y D6: `GET http://localhost:8090/api/v1/sync/preview` con la
  API apuntando a Sigrid; comprobar que no llega truncada, que la lista D5
  sale en `excluidos_por_estado_recurso` y revisar `por_empresa`. Depende de
  T9 y de la lista D5 de negocio.
- **T11** · arrancar la API contra la BBDD local y comprobar que
  `sincronizar_esquema` emite los dos `ALTER … ADD COLUMN IF NOT EXISTS empresa INTEGER`;
  tras `POST /api/v1/sync`, `SELECT empresa, COUNT(*) FROM obra GROUP BY empresa`
  (y en `trabajador`) sin NULL.

## Fuera de alcance / lo que falta

- **D4**: no desplegar a usuarios sin F-024. Con R11, una persona con fichas en
  dos empresas sale dos veces y aparecen obras y trabajadores de otras
  empresas (hasta ahora se mezclaban con los de Ruesma).
- **D6**: sin el filtro de `emphis` la consulta de empleados devuelve más
  filas; si la respuesta de sigrid-api llega truncada, el cliente falla (no
  pierde filas). Paginar queda fuera (T10 lo comprueba).
- F-024 (filtro de empresa en pantalla), F-025 (postventa y estados de obra),
  F-026 (recursos sin ficha de empleado) y `obra_por_codigo` del transfer: no
  se han tocado.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests de F-023 | **53 passed** en 1.97 s (`tests/test_f023_sync_empresa.py`) |
| Suite de `dedicacion-api` | **176 passed** en 4.77 s (dentro de `bash harness/init.sh`) |
| Suite raíz (`init.sh`) | **355 passed, 1 skipped** en 34.91 s |
| Cobertura de líneas cambiadas | **100.0 %** (67/67, umbral 80 %, nivel crítico) — `PUERTA COBERTURA` de `init.sh` |
| Mutación | **33 generados, 33 muertos, 0 supervivientes**, 0 timeouts, 0 sin veredicto; campaña completa (sin muestreo) |
| Tiempo de la campaña | 51.0 s de reloj, **4 workers**; línea base 4.6 s; coste por mutante = 51.0 × 4 ÷ 33 = **6.2 s** (> 1 s) |
| SHA medido | `fd2831c` — informe `progress/mutacion_F-023.md` |
| `bash harness/init.sh` | **ENTORNO LISTO**, todas las puertas en `[OK]`; ruff 193 avisos = los de `dev` (ninguno nuevo) |

**Historia de la campaña (tres ejecuciones, vale la última):**

1. Sobre `35273f2` (tras T8): 33 mutantes, 29 muertos, **4 supervivientes**.
   Cada uno se **reprodujo a mano** (mutación aplicada al árbol, suite entera
   del servicio con `python -B -m pytest -q -p no:cacheprovider`, fichero
   restaurado): los cuatro sobrevivieron también a mano (173 passed), así que
   eran huecos reales, no artefactos de caché. Ninguno era equivalente:
   - `@dataclass(frozen=True)` → `frozen=False`: nada vigilaba que el criterio
     compartido como valor por defecto sea inmutable → `test_f023_r16_criterio_es_inmutable`.
   - `baja_laboral … > 0` → `> 1`: ningún incluido tenía `baja_laboral == 1` →
     fila añadida a `test_f023_r15_…`.
   - `deps.py`: default de `excluir_recurso_con_fecha_baja` `False` → `True`, y
     de `filtro_estado_recurso` `True` → `False`: ningún test usaba un
     `config.yaml` sin esas claves → `test_f023_r18_config_sin_claves_…` y
     `test_f023_r18_filtro_estado_recurso_encendido_por_defecto`.
   Con los tests nuevos, reproducidos a mano otra vez: **los cuatro mueren**
   (1-2 failed cada uno). Commit `7e1bf24`.
2. Purgados `__pycache__` y `.pytest_cache`, campaña entera sobre `7e1bf24`:
   33/33 muertos, 65.4 s. Descartada solo porque después cambió el código.
3. Tras `fd2831c` (singleton `CRITERIO_VACIO`, sin cambio de comportamiento),
   caché purgada otra vez y campaña entera: **33/33 muertos en 51.0 s**. Es el
   informe vigente. Al durar menos de 60 s, el reviewer debe reejecutarla
   (CHECKPOINTS C4 bis).

## T9 · D1 cerrada (2026-10-01)

Decidida por el humano con el hallazgo de `progress/explore_estado_recurso.md`, **sin lanzar
Q1**: INACTIVO = recurso con fecha de baja de su concepto (`con.fecbaj > 0`), el criterio que
publica el data mart (`personal.recursos.activo`). Solo cambia configuración y tests; ningún
cambio de código de producción.

- `config/config.yaml`: `excluir_recurso_con_fecha_baja: true`; `estados_recurso_excluidos: []`
  sigue vacía **a propósito**, con comentario: el tipo 33 no tiene estados en `conest`
  (`estado_recurso` llega como el número de `con.est`), no meter «BAJA» ni «2» (estado del
  EMPLEADO, tipo 43) y la comparación por subcadena haría que «1» casara «10» y «21». Recoge la
  observación 1 de `progress/review_F-023.md`.
- Tests renombrados: `r5_config_inactivo_es_la_fecha_de_baja_del_recurso` (interruptor `True`,
  lista vacía, fecha de baja `True`) y `r18_con_el_config_real_cae_el_recurso_con_fecha_de_baja`
  (config real: netos `([1, 2], [1])` iguales en preview y sync; `excluidos_por_estado_recurso ==
  {"(fecha de baja del recurso)": 1}`; el 2 sigue aunque su estado diga «Baja»; sigue cayendo el
  de otra empresa, `excluidos_recurso_otra_empresa == 1`).

**Fase RED** (tests nuevos, `config.yaml` anterior), comando
`cd services/dedicacion-api && .venv/Scripts/python -m pytest tests/test_f023_sync_empresa.py -q -k "r5_config_inactivo or r18_con_el_config_real"`:
```
>       assert cfg["excluir_recurso_con_fecha_baja"] is True
E       assert False is True
>       assert _mismos_netos(contenedor) == ([1, 2], [1])
E       assert ([1, 2, 3], [1]) == ([1, 2], [1])
2 failed, 51 deselected in 5.20s
```
Con el config nuevo: `2 passed`; suite del servicio **176 passed** en 5.41 s.

**Evidencias T9.** `bash harness/init.sh`: **ENTORNO LISTO**; raíz **355 passed, 1 skipped** en
57.35 s; api 176 passed en 5.82 s; `PUERTA COBERTURA` 100.0 % (67/67); ruff 193 avisos (los de
`dev`). Mutación repetida sobre el disco (`--workers 1`, porque `progress/current.md` del líder
estaba sin commitear): **33 generados, 33 muertos, 0 supervivientes**, 255.6 s; mismos 33
mutantes (el cambio es de YAML y tests, no de producción). Informe: `progress/mutacion_F-023.md`.
