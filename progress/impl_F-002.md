<!-- progress/impl_F-002.md -->
# F-002 · Informe de implementación — Fase 1 (T1–T5)

- **Rama:** `feature/F-002-reglas-postventa-conflicto`
- **Rigor:** `critico` (fase RED + cobertura ≥ 80 % + mutación con 0 supervivientes)
- **Alcance de este informe:** **solo T1–T5** de
  `specs/F-002-reglas-postventa-conflicto/tasks.md`, las tareas declaradas
  independientes de la respuesta de Administración.
- **Dónde paré:** en la **⛔ PARADA** de `tasks.md`, justo después de T5.
  **T6 no está hecha** (es `MANUAL (humano)`) y no se ha abierto ninguna
  tarea de la Fase 2 ni de la Fase 3. La feature **no** queda marcada
  `blocked`: no está atascada, está esperando una respuesta que el líder ya
  sabe que falta.

> **Aviso al líder.** Durante el trabajo llegaron dos datos que la spec
> todavía no recoge y que condicionan la Fase 2 (ver §7): D1 está cerrada
> (obra `POSTV2`, partida **hoja**, casado por código exacto — verificado
> contra Sigrid, volcado en `progress/sigrid_F-002.md`) y D2 se ha
> contestado con una **tercera opción** que no está diseñada en el
> repositorio. **Nada de eso está implementado.** T3 replica exactamente la
> conducta actual, como manda la spec.

---

## 1. Qué se ha hecho, tarea a tarea

| Tarea | Estado | Commit |
|---|---|---|
| T1 · fixtures parametrizables | hecha | `04fbd9b` |
| T2 · tests R6–R9 y R12 | hecha | `60d5319` |
| T3 · función pura del conflicto | hecha | `22328fb` |
| T4 · tests R14 y R10/R11/R13 | hecha | `20280c7` |
| T5 · fuente única (parte no bloqueada) | hecha | `beba73b` |
| T6 · volcar preguntas y consultas | **NO hecha** — `MANUAL (humano)` | — |
| T7–T17 | **NO abiertas** — bajo la PARADA | — |

Un commit adicional, `F-002: quita un noqa inutil del conftest`, es un ajuste
de lint sin cambio de conducta.

### T1 — `tests/conftest.py`

`ClienteFalso` parametrizable y `SettingsFalso`, sin red, sin BBDD y sin
`.env`. Lo que la feature necesita variar está en el constructor y no
cableado: `presupuesto_postventa` (`"hojas"` | `"capitulos"` — la variable de
D1.2), `lineas_parte`, `synckeys`, `parte_existe` y
`obra_postventa_existe`. Añade además dos ayudas de aserción
(`inserts()`, `borrados()`) y dos constructores de datos con valores por
defecto (`linea()`, `linea_previa()`).

`test_pipeline_offline.py` **no** se ha migrado a estas fixtures: es la red
de seguridad de T3 y tenía que quedarse intacto.

### T2 — `tests/test_f002_reglas.py` (R6–R9, R12)

25 tests contra `ReglasPorcentajes` directamente, sin pipeline. Cada regla
lleva su **control positivo**, para que no la satisfaga una decisión
constante (una regla que omitiera siempre pasaría los tests de omisión).
R7 se prueba con seis periodos, incluidos febrero común, febrero bisiesto y
un mes de un solo dígito.

### T3 — la decisión del conflicto, en una sola función

En `application/services/reglas_porcentajes.py`:

- `CAMPOS_CLAVE` — la tupla de la que sale todo.
- `IMPLICITOS_DEL_PARTE` — los campos que el propio parte ya fija (el
  periodo) y que por eso no se comparan contra la línea de Sigrid. Está
  declarado a propósito: un campo que no esté ni aquí ni en `_DE_LINEA` hace
  fallar a `criterio_choque` con `KeyError` en vez de dejar de compararse en
  silencio, que es exactamente la avería que trae la feature.
- `campos_identidad(destino)` — **el único punto donde vive la decisión D2**.
- `clave_conflicto(accion)` y `criterio_choque(existente, accion, *, mias)`.

En `application/pipelines/registro_pipeline.py`, el filtro de choque (ocho
líneas de comprensión con la condición repartida en cuatro cláusulas) pasa a
ser una llamada. En `domain/models/registro_models.py` desaparece la
property `AccionLinea.clave_conflicto`.

**Desviación respecto a la lista de ficheros de la spec.** La spec (§3) no
menciona `interface_adapters/api/app.py`, pero era el otro consumidor de la
property (`app.py:103`), así que se actualiza con ella. Sin ese cambio el
servicio no arranca. Es un cambio de una línea más su import.

**Verificación de T3, que es la que importa:** `tests/test_pipeline_offline.py`
pasa **sin tocarlo**, incluida la aserción `c.clave == "200|202607|5|80001"`.
Comprobado con `git diff --stat` sobre ese fichero: vacío.

> **Nota de diseño que el reviewer debe mirar con lupa.** La spec pide
> (R14) que clave y criterio «no puedan divergir», y a la vez (T3) que la
> conducta no cambie. Hoy la clave lleva `paride` **siempre** y el criterio
> **no** lo compara en la obra normal: las dos cosas juntas solo son posibles
> si la clave y el criterio salen de la misma declaración pero no son la
> misma lista. La solución adoptada es que `CAMPOS_CLAVE` sea la fuente
> única y que `campos_identidad()` **se derive de ella**: tocar la tupla
> mueve las dos cosas a la vez (lo prueba
> `test_f002_r14_cambiar_la_tupla_cambia_la_clave_y_el_criterio`), y la
> asimetría que queda —clave más fina que el criterio en obra normal— es
> justo el defecto R13, que se arregla en T4 deduplicando los borrados. Si
> el reviewer considera que esto no satisface R14, la alternativa era
> cambiar `test_pipeline_offline.py`, que T3 prohíbe expresamente.

### T4 — R14, R10, R11 y **un defecto real (R13)**

`tests/test_f002_conflicto.py` (17 tests) fija el mecanismo: la identidad es
subconjunto de la clave, todo campo comparado sabe leerse de las dos partes,
quitar `paride` de `CAMPOS_CLAVE` cambia la clave **y** el criterio, y un
campo nuevo sin lector revienta en alto.

`tests/test_f002_pipeline.py` (10 tests) cubre R10 (idempotencia por
`synckey`, y que `ejecutar` no mande ni un INSERT), R11 (modo pruebas: el
parte va a la obra de pruebas pero la partida se resuelve contra la obra de
postventa real, y lo escrito lleva la marca en `tex`) y R13.

**R13 era un defecto real, no una hipótesis.** Dos líneas pendientes del
mismo recurso y mes con partidas distintas chocan las dos con la **misma**
línea previa del parte (en obra normal la partida no distingue), generan dos
`Conflicto` con claves distintas y, al confirmar los dos pisados, emitían
**dos `DELETE` del mismo `hmores.ide`** con `res.borradas` contando 2. El
segundo `DELETE` no borra nada y el recuento le miente al humano. Arreglado
en `ejecutar()` deduplicando por `ide`.

### T5 — fuente única (lo que no depende de Administración)

- `docs/ARCHITECTURE.md`: anclas `#regla-p1` … `#regla-p5`,
  `#regla-conflicto` y `#regla-pruebas`; los puntos **5** y **6** pasan de la
  marca ⚠ a decir `PENDIENTE · decisión D1/D2 de F-002`, con qué falta
  exactamente y dónde está la pregunta; la nota de cabecera se reduce a esos
  dos puntos.
- `services/dedicacion-transfer/README.md`: P1, P2 y P3 dejan de enunciarse y
  remiten a las anclas. P4 y P5 se quedan **bajo un bloque marcado como NO
  normativo** hasta T12: retirarlos ahora dejaría el servicio sin ninguna
  descripción de la regla mientras se espera la respuesta.
- **R5 aplicada:** el literal del código de la obra de postventa sale de
  docstrings y comentarios de `reglas_porcentajes.py`, `partida_resolver.py`
  y `registro_pipeline.py`; ahora se cita el ajuste `POSTVENTA_OBRA_COD`. El
  valor solo vive en `.env` / `.env.example` / el defecto de `settings.py`.
  El `'postventa-2'` del docstring era además **falso** (lo confirma
  `progress/sigrid_F-002.md`).
- `tests/test_f002_fuente_unica.py` (38 tests) vigila lo anterior leyendo los
  ficheros del repositorio. Las frases prohibidas se buscan sobre el texto
  con los espacios colapsados: si no, rewrapear un docstring haría la frase
  invisible al test sin haber retirado nada.

**Lo que espera a Administración queda como `xfail(strict=True)`** (5 tests):
la remisión de los docstrings de P4/P5, sus frases prohibidas y la línea de
procedencia fechada de R4. `strict=True` significa que si algún día pasan sin
que nadie lo espere, la suite lo dice en vez de callarse.

---

## 2. Ficheros tocados

**Producción (5):**

| Fichero | Qué cambia |
|---|---|
| `services/dedicacion-transfer/application/services/reglas_porcentajes.py` | +`CAMPOS_CLAVE`, `IMPLICITOS_DEL_PARTE`, `_entero`, `_DE_ACCION`, `_DE_LINEA`, `campos_identidad`, `clave_conflicto`, `criterio_choque`; docstring sin el literal de la obra |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py` | el filtro de choque pasa a llamada; deduplicación de borrados por `ide` (R13); comentarios que remiten en vez de reenunciar |
| `services/dedicacion-transfer/domain/models/registro_models.py` | se elimina la property `AccionLinea.clave_conflicto` |
| `services/dedicacion-transfer/interface_adapters/api/app.py` | consumía la property: pasa a llamar a la función |
| `services/dedicacion-transfer/application/services/partida_resolver.py` | docstrings sin el literal de la obra de postventa |

**Documentación (2):** `docs/ARCHITECTURE.md`,
`services/dedicacion-transfer/README.md`.

**Tests (5 nuevos):** `tests/conftest.py`, `tests/test_f002_reglas.py`,
`tests/test_f002_conflicto.py`, `tests/test_f002_pipeline.py`,
`tests/test_f002_fuente_unica.py`, todos en
`services/dedicacion-transfer/`.

**Intacto a propósito:** `tests/test_pipeline_offline.py` (criterio de T3),
`partida_catalog.py` / `partida_matcher.py` / `text_match.py` (copias de
`partes-persistencia`, lista cerrada de `CLAUDE.md`),
`sigrid_write_client.py`, `dedicacion-api/**`, `dedicacion-front/**`,
`harness/**`, `harness/features.json`, `progress/current.md`, y los ficheros
de F-003 de la otra sesión (`specs/F-003-orm-columnas-sigrid/`,
`progress/spec_F-003.md`), que no entran en ningún commit de esta feature.

---

## 3. Fase RED (obligatoria en `critico`)

Dos métodos, según lo que había:

- **RED real** cuando el entregable era código que aún no existía: R13 (el
  defecto) y R1–R5 (el árbol no tenía anclas ni remisiones).
- **RED por rotura en copia aislada** cuando el entregable era el test sobre
  código ya escrito (R6–R12, R14). La copia se hace en el scratchpad, **nunca
  en el árbol real**, con un script que copia el servicio sin `.venv`, rompe
  UNA línea y ejecuta el test que la vigila.

### 3.1 · R13 — RED real, contra el código de producción

```
$ cd services/dedicacion-transfer
$ python -m pytest tests/test_f002_pipeline.py -q --no-header
.......F..                                                               [100%]
================================== FAILURES ===================================
_____________________ test_f002_r13_borrado_unico_por_ide _____________________

    def test_f002_r13_borrado_unico_por_ide():
        cli, lineas = _dos_lineas_contra_la_misma()
        claves = {c.clave for c in
                  _pipeline(cli).preflight(obra=OBRA, lineas=lineas).conflictos}

        cli2, lineas2 = _dos_lineas_contra_la_misma()
        res = _pipeline(cli2).ejecutar(obra=OBRA, lineas=lineas2,
                                       pisar_claves=claves)

>       assert cli2.borrados() == [5001], cli2.borrados()
E       AssertionError: [5001, 5001]
E       assert [5001, 5001] == [5001]
E
E         Left contains one more item: 5001
E         Use -v to get more diff

tests\test_f002_pipeline.py:158: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_f002_pipeline.py::test_f002_r13_borrado_unico_por_ide - Ass...
1 failed, 9 passed in 0.68s
```

Tras el arreglo (deduplicación por `ide` en `ejecutar()`): `10 passed`.

### 3.2 · R1–R5 — RED real, contra el árbol antes de T5

```
$ cd services/dedicacion-transfer
$ python -m pytest tests/test_f002_fuente_unica.py -q --no-header -rf
...
FAILED tests/test_f002_fuente_unica.py::test_f002_r1_fuente_unica_tiene_ancla_por_regla[regla-p1]
FAILED tests/test_f002_fuente_unica.py::test_f002_r1_fuente_unica_tiene_ancla_por_regla[regla-p2]
FAILED tests/test_f002_fuente_unica.py::test_f002_r1_fuente_unica_tiene_ancla_por_regla[regla-p3]
FAILED tests/test_f002_fuente_unica.py::test_f002_r1_fuente_unica_tiene_ancla_por_regla[regla-p4]
FAILED tests/test_f002_fuente_unica.py::test_f002_r1_fuente_unica_tiene_ancla_por_regla[regla-p5]
FAILED tests/test_f002_fuente_unica.py::test_f002_r1_fuente_unica_tiene_ancla_por_regla[regla-conflicto]
FAILED tests/test_f002_fuente_unica.py::test_f002_r1_fuente_unica_tiene_ancla_por_regla[regla-pruebas]
FAILED tests/test_f002_fuente_unica.py::test_f002_r1_fuente_unica_el_ancla_no_esta_repetida[regla-p1]
   ... (los siete anclas, dos tests cada uno)
FAILED tests/test_f002_fuente_unica.py::test_f002_r1_los_puntos_sin_cerrar_estan_marcados
FAILED tests/test_f002_fuente_unica.py::test_f002_r2_el_readme_remite_a_las_anclas[regla-p1]
FAILED tests/test_f002_fuente_unica.py::test_f002_r2_el_readme_remite_a_las_anclas[regla-p2]
FAILED tests/test_f002_fuente_unica.py::test_f002_r2_el_readme_remite_a_las_anclas[regla-p3]
FAILED tests/test_f002_fuente_unica.py::test_f002_r3_frases_prohibidas_fase1[ruta0-**P1** Solo recursos con c\xf3digo de hora]
FAILED tests/test_f002_fuente_unica.py::test_f002_r3_frases_prohibidas_fase1[ruta1-**P2** La l\xednea va SIEMPRE al]
FAILED tests/test_f002_fuente_unica.py::test_f002_r3_frases_prohibidas_fase1[ruta2-**P3** `can` = porcentaje]
FAILED tests/test_f002_fuente_unica.py::test_f002_r3_frases_prohibidas_fase1[ruta3-postventa-2]
FAILED tests/test_f002_fuente_unica.py::test_f002_r5_sin_literal_de_la_obra_de_postventa[partida_resolver.py]
FAILED tests/test_f002_fuente_unica.py::test_f002_r5_sin_literal_de_la_obra_de_postventa[registro_pipeline.py]
25 failed, 4 passed, 4 xfailed in 0.58s
```

Tras aplicar T5: `38 passed, 5 xfailed`.

> El listado de arriba destapó además un fallo del propio test: una frase
> prohibida partida en dos líneas por el ajuste del docstring no se
> encontraba, y el `xfail(strict=True)` lo delató como XPASS. De ahí que las
> frases se busquen sobre el texto con los espacios colapsados.

### 3.3 · R6 — sin código `M*` no se registra

```
### fichero roto : application/services/reglas_porcentajes.py
###   'if h.es_mensual'  ->  'if True'
$ python -m pytest tests/test_f002_reglas.py -k test_f002_r6 -q
F.F                                                                      [100%]
______________________ test_f002_r6_sin_mensual_se_omite ______________________
    def test_f002_r6_sin_mensual_se_omite():
        a = _reglas().decidir(linea(recurso_ide=300, empleado_ide=None))
>       assert a.accion == "omitir", a
E       AssertionError: AccionLinea(registro_id=1, accion='escribir', ...)
E       assert 'escribir' == 'omitir'
E         - omitir
E         + escribir
_____________________ test_f002_r6_con_mensual_se_escribe _____________________
>       assert a.accion == "escribir" and a.hora_codigo == "MENC", a
E       AssertionError: ...
E         assert ('escribir' == 'escribir'
E           escribir and 'HEGR' == 'MENC'
E         - MENC
E         + HEGR)
2 failed, 1 passed, 22 deselected in 0.26s
```

### 3.4 · R7 — la línea va al último día del mes

```
### fichero roto : domain/models/registro_models.py
###   '{ultimo:02d}'  ->  '01'
$ python -m pytest tests/test_f002_reglas.py -k test_f002_r7 -q
FFFFFFF                                                                  [100%]
_____________ test_f002_r7_fecha_ultimo_dia_mes[2026-7-20260731] ______________
>       assert a.fecha_int == esperado, (ano, mes, a.fecha_int)
E       AssertionError: (2026, 7, 20260701)
E       assert 20260701 == 20260731
_____________ test_f002_r7_fecha_ultimo_dia_mes[2024-2-20240229] ______________
E       AssertionError: (2024, 2, 20240201)
E       assert 20240201 == 20240229
   ... (los seis periodos + el test de independencia del día de captura)
7 failed in 0.30s
```

### 3.5 · R8 — la escala del porcentaje

```
### fichero roto : application/services/reglas_porcentajes.py
###   'can = round(porcentaje, 4)'  ->  'can = round(porcentaje * 100, 4)'
$ python -m pytest tests/test_f002_reglas.py -k test_f002_r8 -q
>       assert a.can == 0.4
E       AssertionError: assert 40.0 == 0.4
>       assert a.can == 0.3333               # el porcentaje, a cuatro decimales
E       AssertionError: assert 33.3333 == 0.3333
>       assert a.can == 0.4 and a.tot == 3600.0
E       AssertionError: assert (40.0 == 0.4)
3 failed, 22 deselected in 0.37s
```

### 3.6 · R9 — porcentaje fuera de `(0, 1]`

```
### fichero roto : application/services/reglas_porcentajes.py
###   'if not (0.0 < porcentaje <= 1.0):'  ->  'if not (0.0 <= porcentaje <= 100.0):'
$ python -m pytest tests/test_f002_reglas.py -k test_f002_r9 -q
>       assert a.accion == "omitir", (porcentaje, a)
E       AssertionError: (0.0, AccionLinea(... accion='escribir' ...))
E       assert 'escribir' == 'omitir'
   ... (idem con 1.0001, 40 y 100)
FAILED tests/test_f002_reglas.py::test_f002_r9_porcentaje_fuera_de_rango[0.0]
FAILED tests/test_f002_reglas.py::test_f002_r9_porcentaje_fuera_de_rango[1.0001]
FAILED tests/test_f002_reglas.py::test_f002_r9_porcentaje_fuera_de_rango[40]
FAILED tests/test_f002_reglas.py::test_f002_r9_porcentaje_fuera_de_rango[100]
4 failed, 5 passed, 16 deselected in 0.34s
```

### 3.7 · R12 — postventa desactivada

```
### fichero roto : application/services/reglas_porcentajes.py
###   'if not self._postventa:'  ->  'if False:'
$ python -m pytest tests/test_f002_reglas.py -k test_f002_r12 -q
>       assert a.accion == "omitir", a
E       AssertionError: AccionLinea(... es_postventa=True, destino='postventa',
E                                    paride=70001, partida_cod='0678' ...)
E       assert 'escribir' == 'omitir'
1 failed, 2 passed, 22 deselected in 0.28s
```

### 3.8 · R14 — clave y criterio derivan de la misma tupla

```
### fichero roto : application/services/reglas_porcentajes.py
###   CAMPOS_CLAVE pierde "paride"
$ python -m pytest tests/test_f002_conflicto.py -k test_f002_r14 -q
>       assert clave_conflicto(a) == "200|202607|5|70001"
E       AssertionError: assert '200|202607|5' == '200|202607|5|70001'
>       assert clave_conflicto(accion()) == "200|202607|5|80001"
E       AssertionError: assert '200|202607|5' == '200|202607|5|80001'
>       assert clave_conflicto(a) == "0|202607|0|0"
E       AssertionError: assert '0|202607|0' == '0|202607|0|0'
>       assert criterio_choque(linea_previa(paride=70002), a, mias=set()) is False
E       AssertionError: assert True is False
5 failed, 12 passed in 0.38s
```

Es la prueba de que la tupla manda de verdad sobre **las dos** cosas: al
tocarla se caen a la vez las aserciones de la clave y la del criterio.

### 3.9 · R11 — el modo pruebas no falsea el casado

```
### fichero roto : application/pipelines/registro_pipeline.py
###   'destino = destino_pruebas if forzada else obra_pv'  ->  'destino = obra_pv'
$ python -m pytest tests/test_f002_pipeline.py -k test_f002_r11 -q
>       assert getattr(pf, "obra_postventa").codigo == OBRA_PRUEBAS
E       AssertionError: assert 'POSTV2' == '0404'
1 failed, 2 passed, 7 deselected in 0.65s
```

### 3.10 · R10 — idempotencia por `synckey`

```
### fichero roto : application/pipelines/registro_pipeline.py
###   'a.accion = "ya_registrado"'  ->  'a.accion = "escribir"'
$ python -m pytest tests/test_f002_pipeline.py -k test_f002_r10 -q
>       assert a.accion == "ya_registrado", a
E       AssertionError: AccionLinea(... accion='escribir' ... hmores_ide=9001)
E       assert 'escribir' == 'ya_registrado'
```

---

## 4. Evidencias

| Evidencia | Valor real | Cómo se obtuvo |
|---|---|---|
| **Tests ejecutados** (servicio `transfer`) | **90 passed, 5 xfailed, 1 warning** | `bash harness/init.sh`, sección 7 bis |
| Tests de la raíz | 11 passed | `bash harness/init.sh`, sección 7 |
| Tests del servicio `api` | 21 passed (no lo toca esta feature) | `python -m pytest -q` desde `services/dedicacion-api` |
| **Cobertura de las líneas cambiadas** | **96,8 % — 30/31 (umbral 80 %, nivel `critico`)** | línea `PUERTA COBERTURA` de `bash harness/init.sh` |
| **Mutantes generados / evaluados** | **9 / 9** | `python -m harness.mutacion --feature F-002 --workers 1` |
| **Supervivientes** | **0** (y 0 timeouts) | `progress/mutacion_F-002.md` |
| **Tiempo de la suite** | transfer **1,41 s**; raíz 0,45 s; api 0,39 s | salida de pytest |
| Tiempo de la campaña de mutación | 11,9 s | `progress/mutacion_F-002.md` |

### 4.1 · La línea cambiada que no está cubierta

La única de las 31 es
`services/dedicacion-transfer/interface_adapters/api/app.py:19`, el `import`
de `clave_conflicto`. Ese módulo **no lo importa ningún test** porque
construye la app de FastAPI y necesita `settings` con la function key, así
que sale como «no medido» y sus líneas cambiadas cuentan como no cubiertas
(que es la verdad). Las otras dos líneas de `app.py` en el diff no son
sentencias ejecutables. No se ha añadido un test de arranque de la app: sería
un test nuevo de infraestructura fuera del alcance de la Fase 1, y la puerta
pasa con holgura sin él.

### 4.2 · Los mutantes, uno a uno

Los 9 caen sobre las funciones nuevas de `reglas_porcentajes.py`, que es
exactamente donde el diseño quiso concentrar la carga lógica:

| # | Línea | Mutación | Veredicto |
|---|---|---|---|
| 1 | 72 | `int(valor or 0)` → `int(valor and 0)` | muerto |
| 2 | 72 | `int(valor or 0)` → `int(valor or 1)` | muerto |
| 3 | 100 | `destino == "postventa"` → `!=` | muerto |
| 4 | 102 | `campo != "paride"` → `==` | muerto |
| 5 | 125 | `synckey and synckey in mias` → `or` | muerto |
| 6 | 126 | `return False` → `return True` | muerto |
| 7 | 130 | `_DE_LINEA[...] != _DE_ACCION[...]` → `==` | muerto |
| 8 | 131 | `return False` → `return True` | muerto |
| 9 | 132 | `return True` → `return False` | muerto |

`registro_pipeline.py` (18 líneas en alcance), `partida_resolver.py` (6),
`registro_models.py` (4) y `app.py` (2) generan **0 mutantes**: sus líneas
cambiadas son comentarios, docstrings, una llamada y un `in` sobre un
conjunto, y el mutador solo toca comparaciones, aritméticos, lógicos, `not`,
booleanos y enteros. No es un hueco de los tests, es que ahí no hay nada
mutable; su conducta la vigilan igualmente `test_f002_pipeline.py` y
`test_pipeline_offline.py`.

### 4.3 · Dos cosas que el reviewer debe reproducir a mano

1. **La campaña duró 11,9 s (< 5 min)**, así que `CHECKPOINTS.md` C4 bis
   obliga al reviewer a **reejecutarla** con `--salida` fuera del
   repositorio y comparar totales.
2. **La campaña hay que lanzarla con `--workers 1`.** La paralela crea
   worktrees desde HEAD y aborta si el árbol tiene cambios sin commitear; en
   este árbol hay ficheros sin versionar que **no son míos**
   (`specs/F-003-orm-columnas-sigrid/`, `progress/spec_F-003.md`: los está
   escribiendo otro subagente) y que no debo commitear. Con `--workers 1`
   funciona y los 9 mutantes tardan 12 s.

---

## 5. Verificación de cierre

`bash harness/init.sh` tal cual, en verde (exit 0):

```
[OK] PUERTA COBERTURA: 96.8% de 31 líneas cambiadas cubiertas (30/31, umbral 80%, nivel critico)
[OK] servicio transfer (services/dedicacion-transfer): pytest en verde
[OK] servicio api (services/dedicacion-api): pytest en verde (caché: árbol sin cambios desde el último verde)
[AVISO] servicio front (services/dedicacion-front): sin directorio de tests
[AVISO] ruff: 175 avisos (deuda previa, no bloquea)
ENTORNO LISTO. Puedes trabajar.
```

Dos avisos heredados que **no** son de esta feature: el front sigue sin
tests, y `ruff` pasa de 164 a 175 avisos. Los 11 nuevos son del mismo tipo
que la deuda previa del repositorio (`I001` orden de imports, `C408`
`dict()` en vez de literal, `B009` `getattr` con nombre constante en los
tests que leen los atributos que el pipeline adjunta con `setattr`). No he
reordenado imports ni cambiado el estilo del repositorio para bajarlos:
sería ruido en el diff de una feature de rigor crítico. El único aviso que
era estrictamente mío, un `# noqa: E402` inútil, sí está corregido.

**El servicio `api` salió de caché.** No lo toca esta feature; aun así lo he
ejecutado a mano: `21 passed in 0.39s`.

---

## 6. Verificaciones `MANUAL (humano)` pendientes

Ninguna de la Fase 1 lo era. Las que quedan están todas **bajo la PARADA** y
no se han intentado:

| Tarea | Qué es | Comando |
|---|---|---|
| T6 | llevar a Administración las preguntas D1.1, D1.2 y D2 y las consultas C1–C5 | copiar de `requirements.md` §2 a `progress/current.md` |
| T7 | ejecutar C1–C5 contra `sigrid-api` (**solo lectura**) | `Invoke-RestMethod` de `tasks.md` T7, con la function key fuera del repositorio |
| T13 | casado real contra Sigrid **sin escribir** | `python prueba_escritura_porcentajes.py capitulos` / `estado` / `preflight` |
| T14 | escritura real en la obra de pruebas `0404` | `ejecutar --confirmar` → `verificar` → `limpiar --confirmar`. **Exige autorización expresa del humano para esa acción concreta.** Ningún agente la lanza |

`OBRA_PRUEBAS_FORZAR` sigue a `true` y esta fase no ha tocado ningún `.env`.

---

## 7. Qué queda para la Fase 2, y una advertencia

La Fase 1 ha dejado el terreno preparado: la decisión D2 se aplica en
**`campos_identidad()` y en ningún otro sitio**, y la D1 en
`resolver_postventa` + `_destino_postventa` + el filtro de `_cat`.

Pero **el diseño de `design.md` ya no cubre lo que va a hacer falta**, y esto
es lo que el líder tiene que llevar al humano antes de abrir T7:

- **D1 está cerrada y confirma la versión A** (obra `POSTV2`, partida
  **hoja**, casado por código exacto), verificada contra Sigrid con una
  lectura real cuyo volcado está en `progress/sigrid_F-002.md`. T8 y T10 se
  pueden escribir en cuanto el líder lo autorice. Con ese dato, la variable
  `hojas` de `partida_resolver.py:54`, que hoy **no filtra `es_hoja`**, es un
  defecto real: puede devolver un capítulo que el desplegable del front nunca
  ofrece (R17). El caso «capítulos» ya está en la fixture de T1 esperando su
  test.
- **D2 se ha contestado con la opción (c)**, que `requirements.md` §2
  contempla como la respuesta que invalida el diseño: varias líneas `M*` del
  mismo recurso con partidas distintas pueden convivir, pero **la suma de sus
  cantidades en el mes no puede pasar de 1**. Eso no es ninguna de las dos
  versiones enfrentadas: es una regla nueva (validar la suma) que no existe
  en el transfer y que podría corresponder a la API, que es quien conoce el
  cuadrante completo del trabajador. **No la he implementado ni anticipado**:
  T3 replica la conducta de hoy, como manda la spec, y `design.md` §7
  Riesgo 2 dice exactamente que en este caso hay que parar y volver a
  proponer. Lo propondrá el líder.

Cuando D2 se implemente, los tests que habrá que revisar son
`test_f002_r14_en_obra_normal_la_partida_no_distingue` (fija la conducta de
hoy, por eso existe) y, si la conducta del pipeline cambia, las aserciones de
`test_pipeline_offline.py` — que entonces sí se tocan, **justificando por
escrito cada una**, según T11.
