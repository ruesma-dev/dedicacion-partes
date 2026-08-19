<!-- progress/impl_F-001.md -->
# F-001 · Informe de implementación

**Feature:** Primera suite de tests de `dedicacion-api`: la regla del 100 %
**Rama:** `feature/F-001-tests-estados-api` · **SDD:** no (mandan los
`acceptance` de `harness/features.json`) · **Rigor:** `estandar`
**Fecha:** 2026-08-19

---

## 1. Qué cambió

Tres ficheros **nuevos**, todos bajo `services/dedicacion-api/tests/`.
**Ningún fichero de producción se ha modificado**: `domain/estados.py` se ha
leído, no se ha tocado (se comprueba abajo, § 6).

| Fichero | Qué es |
|---|---|
| `services/dedicacion-api/tests/__init__.py` | Marca el paquete de la suite. |
| `services/dedicacion-api/tests/conftest.py` | Inserta la raíz del servicio en `sys.path` para que los tests importen `domain...` igual que hace `main.py`. Mismo efecto que el `sys.path.insert` que el transfer repite en la cabecera de cada test, pero en **un único sitio**. |
| `services/dedicacion-api/tests/test_estados.py` | Los 21 tests (13 funciones, 8 casos parametrizados) de `domain/estados.py`. |

Fuera de `tests/`, en el mismo commit de cierre, solo entran cosas que
**genera el propio arnés** al ejecutarse: `BACKLOG.md` regenerado por
`init.sh`, `harness/features.json` con F-001 en `in_progress`,
`progress/mutacion_F-001.md` escrito por la campaña y los `coverage.json` /
`.coverage` que el portero deja al medir (ver § 7, «Deuda que se deja
apuntada»).

### Tareas (derivadas de los `acceptance`; F-001 es `sdd: false`)

| Tarea | Commit | Verificación |
|---|---|---|
| T1 · Crear la suite (`tests/`, `conftest.py`) y el test de que es offline | `5a1b54d` | `pytest -q` → 2 passed |
| T2 · Cubrir los cuatro estados, el borde de la épsilon y la desviación | `fddef04` | `pytest -q` → 16 passed |
| T3 · Cubrir `resumir()` y el descarte de la baja sin líneas | `a2f58aa` | `pytest -q` → 21 passed |
| — · Dejar los ficheros nuevos sin avisos de ruff | `7760080` | `ruff check services/dedicacion-api/tests` → All checks passed |
| T4 · Cierre: portero, fase RED, mutación y este informe | commit de cierre | `bash harness/init.sh` → ENTORNO LISTO (§ 4) |

### Trazabilidad `acceptance` → tests

| Criterio | Tests |
|---|---|
| **R1** · Existe `services/dedicacion-api/tests/` con tests que no tocan red ni BBDD | `test_f001_r1_el_dominio_bajo_prueba_no_toca_red_ni_bbdd[estados.py]` y `[models.py]`: parsean el AST del módulo y exigen que **todo** import sea de la biblioteca estándar o del paquete `domain`. Es una garantía estructural, no una promesa: si mañana alguien mete `httpx` o `psycopg` en el dominio, el test lo caza. |
| **R2** · Los cuatro estados y el borde de la épsilon (99,999 % y 100,001 % son OK) | `..._sin_lineas_es_sin_carga`, `..._sin_lineas_manda_sobre_el_total`, `..._cien_exacto_es_ok`, `..._por_debajo_de_cien_es_falta`, `..._por_encima_de_cien_es_exceso`, `..._dentro_de_la_epsilon_es_ok[99.999 / 100.001 / 99.995 / 100.005]`, `..._fuera_de_la_epsilon_ya_no_es_ok[99.99-FALTA / 100.01-EXCESO]`, más los tres de `calcular_desviacion`. |
| **R3** · `resumir()`: un trabajador de baja y sin líneas no cuenta | `..._r3_baja_sin_lineas_no_cuenta`, `..._r3_baja_con_lineas_si_cuenta`, `..._r3_activo_sin_lineas_si_cuenta_como_sin_carga`, `..._r3_mixto_el_total_es_la_suma_de_los_cuatro_contadores`, `..._r3_resumen_vacio`. |
| **R4** · `init.sh` en verde con la línea «servicio api: pytest en verde» | No es un test: lo verifica el portero. Salida real en § 4. |

---

## 2. Decisiones de diseño

1. **`conftest.py` en vez de repetir `sys.path.insert` en cada test.** El
   transfer lo hace en la cabecera de su fichero de test; con un solo fichero
   de test da igual, con varios no. La suite de la api nace con el arreglo
   puesto.
2. **Se añaden 99,995 % y 100,005 % al borde de la épsilon**, además de los
   dos que pide el `acceptance`. Los que pide el criterio (99,999 % y
   100,001 %) caen *dentro* de la tolerancia con holgura y no distinguen `<=`
   de `<`; 99,995 % y 100,005 % caen **justo en el borde**, así que son los
   únicos que cazan ese cambio. Comprobado en § 3, rotura B: sin ellos, ese
   fallo pasaría entero.
3. **Se cubre también `calcular_desviacion`**, que el `acceptance` no nombra
   pero que es la otra mitad de lo que consume el front (estado + desviación)
   y comparte la guarda de «0 líneas».
4. **`test_f001_r1_...` mira el AST, no `sys.modules`.** Comprobar módulos
   importados en tiempo de ejecución habría sido frágil (depende del orden de
   colección de pytest y de lo que hayan importado otros tests). El AST es
   determinista.
5. **`ResumenPeriodo` se compara entero**, no campo a campo: así un cambio que
   mueva un trabajador de un contador a otro falla aunque el `total` cuadre.
6. **Los tests nuevos salen sin avisos de ruff.** Los 164 avisos de deuda
   previa **no se han tocado** (siguen siendo 164 después, § 4), pero tampoco
   se le suman 11 nuevos: los que introdujeron los ficheros nuevos (I001,
   SIM102 y 9 × FURB157) se corrigieron en el commit `7760080`.

### Desviaciones respecto al alcance aprobado

Ninguna en cuanto a ficheros de producción: **cero**. Lo único que no estaba
literalmente en el encargo es el commit `7760080` de lint, que solo toca los
ficheros de test recién creados.

---

## 3. Fase RED (obligatoria, nivel `estandar`)

La fase roja canónica —test que falla antes de existir el código— **no es
posible aquí**: el entregable de F-001 *es* el test, y `domain/estados.py` ya
existía y era correcto. Es exactamente el caso que `CHECKPOINTS.md` C4 bis
contempla: *«Si el entregable de la feature es el propio test, la fase RED se
demuestra rompiendo deliberadamente —en una copia aislada, nunca en el árbol
real— lo que el test vigila, y pegando la traza de ese fallo.»*

**Copia aislada usada** (fuera del repositorio, borrada al terminar):
`…/scratchpad/red_F001/`, con `domain/` y `tests/` copiados. El árbol real
nunca se modificó: se comprueba en § 6 con `git diff`.

**Comando exacto de cada rotura:**

```
python scratchpad/romper.py <rotura>
  # copia domain/estados.py.orig -> domain/estados.py con UNA sustitución,
  # lanza: <venv api>/python.exe -m pytest -q --tb=line -p no:cacheprovider
  # y restaura el original al terminar.
```

### Rotura A · `_EPSILON = Decimal("0.005")` → `Decimal("0")`

```
=== ROTURA: epsilon_a_cero ===
    _EPSILON = Decimal("0.005")  ->  _EPSILON = Decimal("0")
.......FFFF..........                                                    [100%]
================================== FAILURES ===================================
E   AssertionError: assert <EstadoTrabajador.FALTA: 'FALTA'> is <EstadoTrabajador.OK: 'OK'>
     +  where <EstadoTrabajador.FALTA: 'FALTA'> = calcular_estado(Decimal('99.999'), 2)
     +  and   <EstadoTrabajador.OK: 'OK'> = EstadoTrabajador.OK
E   AssertionError: assert <EstadoTrabajador.EXCESO: 'EXCESO'> is <EstadoTrabajador.OK: 'OK'>
     +  where <EstadoTrabajador.EXCESO: 'EXCESO'> = calcular_estado(Decimal('100.001'), 2)
     +  and   <EstadoTrabajador.OK: 'OK'> = EstadoTrabajador.OK
E   AssertionError: assert <EstadoTrabajador.FALTA: 'FALTA'> is <EstadoTrabajador.OK: 'OK'>
     +  where <EstadoTrabajador.FALTA: 'FALTA'> = calcular_estado(Decimal('99.995'), 2)
E   AssertionError: assert <EstadoTrabajador.EXCESO: 'EXCESO'> is <EstadoTrabajador.OK: 'OK'>
     +  where <EstadoTrabajador.EXCESO: 'EXCESO'> = calcular_estado(Decimal('100.005'), 2)
=========================== short test summary info ===========================
FAILED tests/test_estados.py::test_f001_r2_dentro_de_la_epsilon_es_ok[99.999]
FAILED tests/test_estados.py::test_f001_r2_dentro_de_la_epsilon_es_ok[100.001]
FAILED tests/test_estados.py::test_f001_r2_dentro_de_la_epsilon_es_ok[99.995]
FAILED tests/test_estados.py::test_f001_r2_dentro_de_la_epsilon_es_ok[100.005]
4 failed, 17 passed in 0.14s
```

### Rotura B · `abs(total - _CIEN) <= _EPSILON` → `< _EPSILON`

```
=== ROTURA: menor_igual_por_menor ===
    abs(total - _CIEN) <= _EPSILON  ->  abs(total - _CIEN) < _EPSILON
.........FF..........                                                    [100%]
================================== FAILURES ===================================
E   AssertionError: assert <EstadoTrabajador.FALTA: 'FALTA'> is <EstadoTrabajador.OK: 'OK'>
     +  where <EstadoTrabajador.FALTA: 'FALTA'> = calcular_estado(Decimal('99.995'), 2)
E   AssertionError: assert <EstadoTrabajador.EXCESO: 'EXCESO'> is <EstadoTrabajador.OK: 'OK'>
     +  where <EstadoTrabajador.EXCESO: 'EXCESO'> = calcular_estado(Decimal('100.005'), 2)
=========================== short test summary info ===========================
FAILED tests/test_estados.py::test_f001_r2_dentro_de_la_epsilon_es_ok[99.995]
FAILED tests/test_estados.py::test_f001_r2_dentro_de_la_epsilon_es_ok[100.005]
2 failed, 19 passed in 0.10s
```

> Esta es la rotura que justifica la decisión 2: la cazan **solo** los dos
> casos del borde exacto que se añadieron de más.

### Rotura C · guarda de `calcular_estado`: `if num_lineas == 0` → `< 0`

```
=== ROTURA: sin_guarda_de_lineas ===
    if num_lineas == 0:  ->  if num_lineas < 0:
=========================== short test summary info ===========================
FAILED tests/test_estados.py::test_f001_r2_sin_lineas_es_sin_carga - Assertio...
FAILED tests/test_estados.py::test_f001_r2_sin_lineas_manda_sobre_el_total - ...
FAILED tests/test_estados.py::test_f001_r3_activo_sin_lineas_si_cuenta_como_sin_carga
FAILED tests/test_estados.py::test_f001_r3_mixto_el_total_es_la_suma_de_los_cuatro_contadores
4 failed, 17 passed in 0.09s
```

### Rotura D · `if total < _CIEN` → `if total > _CIEN`

```
=== ROTURA: falta_por_exceso ===
    if total < _CIEN:  ->  if total > _CIEN:
=========================== short test summary info ===========================
FAILED tests/test_estados.py::test_f001_r2_por_debajo_de_cien_es_falta - Asse...
FAILED tests/test_estados.py::test_f001_r2_por_encima_de_cien_es_exceso - Ass...
FAILED tests/test_estados.py::test_f001_r2_fuera_de_la_epsilon_ya_no_es_ok[99.99-FALTA]
FAILED tests/test_estados.py::test_f001_r2_fuera_de_la_epsilon_ya_no_es_ok[100.01-EXCESO]
FAILED tests/test_estados.py::test_f001_r3_baja_con_lineas_si_cuenta - Assert...
5 failed, 16 passed in 0.10s
```

### Rotura E · quitar el filtro de bajas de `resumir()`

`if not fila.trabajador.activo and not fila.lineas:` → nunca se cumple
(prefijado con `False and`), es decir: la baja sin líneas pasa a contar.

```
=== ROTURA: sin_filtro_de_bajas ===
=========================== short test summary info ===========================
FAILED tests/test_estados.py::test_f001_r3_baja_sin_lineas_no_cuenta - Assert...
FAILED tests/test_estados.py::test_f001_r3_mixto_el_total_es_la_suma_de_los_cuatro_contadores
2 failed, 19 passed in 0.09s
```

Traza completa del test central de R3 (`--tb=short`):

```
___________________ test_f001_r3_baja_sin_lineas_no_cuenta ____________________
tests\test_estados.py:190: in test_f001_r3_baja_sin_lineas_no_cuenta
    assert resumir(filas) == ResumenPeriodo(total=1, ok=1, falta=0, exceso=0,
E   AssertionError: assert ResumenPeriod..., sin_carga=1) == ResumenPeriod..., sin_carga=0)
E     Omitting 3 identical items, use -vv to show
E     Differing attributes:
E     ['total', 'sin_carga']
E     Drill down into differing attribute total:
E       total: 2 != 1...
=========================== short test summary info ===========================
FAILED tests/test_estados.py::test_f001_r3_baja_sin_lineas_no_cuenta - Assert...
1 failed, 20 deselected in 0.17s
```

### Rotura F · el filtro descarta a TODA baja (`and not fila.lineas` fuera)

```
=== ROTURA: filtro_solo_por_baja ===
    if not fila.trabajador.activo and not fila.lineas:  ->  if not fila.trabajador.activo:
=========================== short test summary info ===========================
FAILED tests/test_estados.py::test_f001_r3_baja_con_lineas_si_cuenta - Assert...
1 failed, 20 passed in 0.10s
```

### Rotura G · guarda de `calcular_desviacion`: `if num_lineas == 0` → `< 0`

```
=== ROTURA: desviacion_sin_guarda ===
    if num_lineas == 0:  ->  if num_lineas < 0:
================================== FAILURES ===================================
E   AssertionError: assert Decimal('-100.00') == Decimal('0')
     +  where Decimal('-100.00') = calcular_desviacion(Decimal('0'), 0)
=========================== short test summary info ===========================
FAILED tests/test_estados.py::test_f001_r2_desviacion_sin_lineas_es_cero - As...
1 failed, 20 passed in 0.10s
```

**Resultado: 7 roturas deliberadas, 7 cazadas.** Las dos mitades de la
condición de bajas (roturas E y F) están cubiertas por separado, que es donde
un test escrito a la ligera se habría quedado corto.

---

## 4. Portero completo (`bash harness/init.sh`, sin pipes ni tail)

Ejecutado tal cual desde la raíz, en la rama de la feature. **Exit code 0.**

```
[OK] Arnés v1.5.2 (2026-08-18)
[OK] Python: Python 3.12.7
[OK] Existe CLAUDE.md
[OK] Existe CHECKPOINTS.md
[OK] Existe harness/features.json
[OK] Existe harness/rigor.json
[OK] Existe specs/SPECS.md
[OK] Existe progress/current.md
[OK] Existe progress/history.md
[OK] Existe docs/ARCHITECTURE.md
[OK] Existe docs/CONVENTIONS.md
    8 features, 8 abiertas, en curso: ['F-001'], bloqueadas: ninguna
[OK] features.json válido
[AVISO] BACKLOG.md regenerado desde features.json: inclúyelo en el commit
    niveles: critico, documental, estandar; por defecto critico; umbral de cobertura 80%
[OK] harness/rigor.json y niveles declarados: válidos
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 164 avisos (deuda previa, no bloquea). Detalle: python -m ruff check .
...........                                                              [100%]
11 passed in 0.19s
[OK] pytest en verde (con medición de cobertura)
    3 servicio(s): api (python), front (python), transfer (python)
[OK] harness/servicios.json válido
.....................                                                    [100%]
21 passed in 0.17s
[OK] servicio api (services/dedicacion-api): pytest en verde
[AVISO] servicio front (services/dedicacion-front): sin directorio de tests — NADIE está comprobando los tests de front
[OK] servicio transfer (services/dedicacion-transfer): pytest en verde (caché: árbol sin cambios desde el último verde)
[OK] PUERTA COBERTURA: N/A (F-001 no cambia líneas Python de producción frente a dev)
[OK] Ningún .env versionado
[OK] config.yaml de dedicacion-api: válido
[OK] Los tres servicios tienen .env.example
[OK] Rama actual: feature/F-001-tests-estados-api
----------------------------------------
ENTORNO LISTO. Puedes trabajar.
```

**R4 cumplido**: la línea `[OK] servicio api (services/dedicacion-api): pytest
en verde` está ahí, y por primera vez con tests de verdad detrás (antes de
F-001 esa línea era `[AVISO] … sin directorio de tests`).

Los **164 avisos de ruff son exactamente los mismos que antes** de F-001: los
ficheros nuevos no suman ninguno (`ruff check services/dedicacion-api/tests`
→ `All checks passed!`).

---

## 5. Puertas de cobertura y de mutación

### Puerta de cobertura → **N/A con motivo impreso**

```
[OK] PUERTA COBERTURA: N/A (F-001 no cambia líneas Python de producción frente a dev)
```

**No es un fallo de la herramienta ni un workaround**, y por eso no se ha
marcado la feature `blocked`: `harness/alcance.py` excluye por diseño los
segmentos de ruta `tests`, `specs`, `progress` y `docs` (constante
`DIRECTORIOS_EXCLUIDOS`), y F-001 **solo** añade ficheros bajo
`services/dedicacion-api/tests/`. Comprobado a mano:

```
>>> alcance_de_feature('F-001', base='dev')
F-001: 0 fichero(s), 0 línea(s) de producción
       (origen rama, d6a72a1..feature/F-001-tests-estados-api)
ficheros de producción: []
ficheros del diff sin filtrar:
  ['services/dedicacion-api/tests/__init__.py',
   'services/dedicacion-api/tests/conftest.py',
   'services/dedicacion-api/tests/test_estados.py']
```

Como la puerta automática no tiene nada que medir, se aporta el número que sí
significa algo en esta feature: **la cobertura del código que la feature viene
a cubrir**, leída de `services/dedicacion-api/coverage.json` (el que deja el
propio portero):

| Módulo | Cobertura | Líneas |
|---|---|---|
| `domain/estados.py` | **100 %** | 26 / 26, ninguna sin cubrir |
| `domain/models.py` | 98 % | 79 / 81 (faltan las líneas 58 y 73: `Periodo.clave` y `Linea.clave`, fuera del alcance de F-001) |

### Puerta de mutación → campaña ejecutada, **0 mutantes** por el mismo motivo

`python -m harness.mutacion --feature F-001` → informe en
`progress/mutacion_F-001.md`:

```
F-001: 0 fichero(s), 0 línea(s) de producción (origen rama, d6a72a1..feature/F-001-tests-estados-api)
Sin líneas de producción en el alcance: nada que mutar.
Campaña paralela: hasta 16 workers, uno por worktree.
0 mutantes evaluados, 0 muertos, 0 supervivientes, 0 timeouts en 0.0 s
Informe: progress/mutacion_F-001.md
```

**Supervivientes: 0. No hay ninguna sección de análisis en `PENDIENTE`**,
porque no hay ningún superviviente que analizar: la campaña no generó
mutantes al no haber líneas de producción en el alcance.

Ese cero automático no demuestra nada por sí solo, y aquí está la parte
honesta del informe: **lo que en esta feature sustituye a la campaña es la
mutación manual de § 3**, 7 mutantes escritos a mano sobre `domain/estados.py`
en una copia aislada, **7 muertos, 0 supervivientes**. Se eligieron los
operadores que una campaña automática habría generado sobre ese fichero
(constante numérica, `<=`↔`<`, `<`↔`>`, `==`↔`<`, condición booleana a
`False`, eliminación de un operando de un `and`).

**Mutante equivalente conocido** (no probado porque es inmatable por
construcción): `if total < _CIEN` → `if total <= _CIEN` en la línea 29 de
`estados.py`. Los dos se comportan igual siempre: el único valor que los
distingue es `total == 100`, y ese caso ya ha vuelto por `OK` en la guarda de
la épsilon dos líneas antes, así que nunca llega a esa comparación. Ningún
test puede matarlo y ninguno debería intentarlo.

---

## 6. Comprobación de que no se tocó producción

```
$ git diff dev..HEAD --stat -- services/dedicacion-api/domain
   (sin salida: ningún fichero de dominio cambiado)

$ git diff dev..HEAD --name-only
   services/dedicacion-api/tests/__init__.py
   services/dedicacion-api/tests/conftest.py
   services/dedicacion-api/tests/test_estados.py
   (+ los ficheros del arnés del commit de cierre)
```

La copia rota vivió siempre en el scratchpad de la sesión, fuera del
repositorio, y se borró al terminar.

---

## 7. Evidencias

| Evidencia | Valor real | Cómo se obtuvo |
|---|---|---|
| **Tests ejecutados y resultado** | **21 passed, 0 failed** en el servicio api (13 funciones de test, 8 de ellas parametrizadas). En el portero completo: 11 passed en la suite de la raíz, 21 en api, 4 en transfer (caché). | `services/dedicacion-api/.venv/Scripts/python.exe -m pytest -q` y `bash harness/init.sh` |
| **Cobertura de las líneas cambiadas** | **N/A con motivo impreso** por la puerta: «F-001 no cambia líneas Python de producción frente a dev» (solo añade ficheros en `tests/`, excluidos por `DIRECTORIOS_EXCLUIDOS`). Dato sustitutivo medido: `domain/estados.py` al **100 %** (26/26 sentencias). | línea `PUERTA COBERTURA` de `bash harness/init.sh` + `services/dedicacion-api/coverage.json` |
| **Mutantes generados y supervivientes** | Campaña oficial: **0 generados, 0 evaluados, 0 supervivientes** (alcance vacío, mismo motivo). Mutación manual de § 3: **7 generados, 7 muertos, 0 supervivientes**. 1 mutante equivalente identificado y no ejecutado (`<` → `<=` en la línea 29), justificado en § 5. | `python -m harness.mutacion --feature F-001` → `progress/mutacion_F-001.md`; § 3 de este informe |
| **Tiempo de ejecución de la suite** | **0,10 s** (tres medidas consecutivas: 0,10 s / 0,11 s / 0,10 s). Bajo `coverage`, 0,17 s. | salida de `pytest -q` |

### Entorno

`services/dedicacion-api/.venv` **ya traía** `pytest 9.1.1` y
`coverage 7.15.4`: **no ha hecho falta instalar nada**, ni se ha tocado
`requirements.txt` ni `requirements-dev.txt`. Ninguna dependencia nueva.

---

## 8. Qué queda fuera y qué falta

**Fuera del alcance a propósito** (no es deuda de F-001, es lo que el humano
aprobó no tocar):

- `domain/estados.py` y cualquier otro fichero de producción: **cero
  cambios**.
- El resto de `dedicacion-api` sigue sin tests (`application/`,
  `infrastructure/`, `interface_adapters/`). F-001 es el calentamiento del
  circuito, no la cobertura del servicio.
- `dedicacion-front` sigue **sin directorio de tests**; el portero lo dice en
  cada arranque («NADIE está comprobando los tests de front»).
- Los **164 avisos de ruff** de deuda previa: intactos.

**Verificaciones `MANUAL (humano)` pendientes:** ninguna. F-001 no toca
producción, no escribe en Sigrid, no toca la BBDD y no cambia ningún
comportamiento: todo lo que había que comprobar se comprueba con la suite y
con el portero, y su salida real está en este informe.

### Deuda que se deja apuntada (no se ha tocado: fuera del alcance)

1. **Artefactos de cobertura versionados.** El repositorio ya trae
   `.coverage` y `coverage.json` de la raíz y del transfer **trackeados en
   git** (`git ls-files | grep coverage`), sin estar en `.gitignore`. Son
   binarios/JSON que el portero reescribe en cada ejecución, así que generan
   ruido en `git status` y en cada diff. F-001 añade los dos del api
   siguiendo el precedente existente, para no dejar ficheros sin trackear que
   ensucien el árbol del reviewer. **Lo correcto sería lo contrario**:
   ignorarlos y sacarlos del índice con `git rm --cached`. Es candidato a una
   feature de higiene; no se hace aquí porque tocaría `.gitignore` y ficheros
   fuera del alcance aprobado.
2. **La puerta de cobertura queda sin estrenar de verdad.** Es la primera vez
   que se ejerce en este repositorio y ha salido `N/A` legítimo. La primera
   feature que toque código de producción (F-002 o F-003) será la que la
   pruebe con datos reales.

---

## 9. Cómo reproducirlo

```bash
# suite del servicio
cd services/dedicacion-api && .venv/Scripts/python.exe -m pytest -q

# lint de lo nuevo
.venv/Scripts/python.exe -m ruff check services/dedicacion-api/tests

# portero completo
bash harness/init.sh

# campaña de mutación
python -m harness.mutacion --feature F-001
```
