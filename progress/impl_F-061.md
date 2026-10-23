<!-- progress/impl_F-061.md -->
# Informe del implementer · F-061 (búsqueda predictiva en el desplegable de incidencias)

`sdd: false`, rigor `estandar`. Rama `feature/F-061-busqueda-predictiva-incidencias`
(copia principal). Dos bloqueos previos, resueltos por el humano (ver
`progress/current.md`); esta es la implementación completa tras el segundo.

## Qué cambió

| Tarea | Commit | Qué |
|---|---|---|
| T1 | `d9061e0` | api: `sync.incidencias.palabras_extra` en `config.yaml` (B, AT, M, FJ, F, V, H, lo aprobado); `GET /api/v1/incidencias` publica `palabras` y `orden_busqueda`; una lista mal escrita no deja arrancar la api. Cambio autorizado de `test_f030_r6`. |
| T2 | `1911486` | front: búsqueda predictiva en `montarDesplegableIncidencias` (`app.js`). |
| T3 | `08af118` | front: `sincronizar` recarga el catálogo (`cargarTiposIncidencia`) tras un sync con éxito. |
| T4 | `350ae0e` | `docs/INTEGRACION.md` §5: los dos campos nuevos y la recarga. |
| — | `54ad111` | Sin avisos nuevos de ruff (ISC004 en un test; TRY004 justificado). |

Ficheros:

- `services/dedicacion-api/config/config.yaml`: la lista `palabras_extra`
  (entradas `codigo` + `palabras`, en el orden que desempata).
- `services/dedicacion-api/application/palabras_incidencia.py` (nuevo):
  `palabras_por_codigo(entradas) -> {codigo: (posición, palabras)}`; sin
  clave = `{}`; `ValueError` con la clave y el motivo si no es lista, falta o
  se repite un código, o las palabras no son lista de textos.
- `services/dedicacion-api/interface_adapters/api/routes.py`: la ruta lee la
  config en cada petición (`cargar_config`, con caché) y rellena los campos;
  sin entrada, `[]` y `null`. La lista sigue por letra (F-030 R6 intacta).
- `services/dedicacion-api/interface_adapters/api/schemas.py`:
  `TipoIncidenciaOut.palabras: list[str] = []`, `orden_busqueda: int | None = None`.
- `services/dedicacion-api/interface_adapters/api/deps.py`: valida la lista
  al montar el contenedor (fallo al arrancar, no en el primer GET).
- `services/dedicacion-front/static/js/app.js`: `montarDesplegableIncidencias`
  (filtro y orden) y `sincronizar` (recarga).
- Tests nuevos: `services/dedicacion-api/tests/test_f061_palabras.py` (15),
  `services/dedicacion-front/tests/test_f061_busqueda.py` (7),
  `services/dedicacion-front/tests/test_f061_recarga.py` (3).
- Test ajeno tocado (lista cerrada, autorizado por el humano el 2026-10-23):
  `services/dedicacion-api/tests/test_f030_catalogo.py::test_f030_r6_ruta_incidencias_activas_por_letra`,
  **solo** se añaden `"palabras"` y `"orden_busqueda"` a cada dict esperado
  (CIA 1, CIE 0, CIV 5), con un comentario «F-061 (lista cerrada…)». Ningún
  otro test ajeno cambia.

## Decisiones de diseño

1. **Categorías del desplegable** (menor = antes), en `categoria(t, q, tecleadas)`:
   0 letra exacta · 1 código o letra que empieza por lo tecleado · 2 nombre
   que empieza · 3 toda palabra tecleada empieza alguna palabra del nombre ·
   4 ídem en letra, código, nombre o palabras extra · 5 subcadena de
   «letra nombre» normalizados (la regla de F-030 tal cual, para el
   criterio 3) · 6 cada palabra empieza alguna palabra o, si tiene 4+
   letras, está a distancia OSA 1 del comienzo de alguna. Las aclaraciones
   1 y 6 son las aprobadas el 2026-10-22.
2. **Palabras**: se trocea por lo que no es letra ni dígito
   (`/[^\p{L}\p{N}]+/u`) tras `normalizar` (minúsculas, sin tildes). Las
   palabras extra con espacios («accidente de trabajo») aportan cada palabra.
3. **Errata**: OSA (el intercambio contiguo cuenta 1); se compara con los
   comienzos de la palabra de una letra menos a una más; **una errata por
   palabra tecleada** (lectura de «tolerancia a una errata en palabras de 4
   o más letras»; ningún caso de los criterios distingue «una por palabra» de
   «una en total»).
4. **Empate**: `orden_busqueda` ascendente; las `null` (o sin el campo, como
   el catálogo de los tests de F-030) detrás, en el orden del catálogo.
5. **El código de búsqueda vive DENTRO de `montarDesplegableIncidencias`**
   (funciones locales), no en funciones de nivel superior: su único uso es
   ese desplegable y así los arneses de node de F-030, que cargan esa
   función por su nombre, siguen sin cambios.
6. **El front solo filtra y ordena** (criterio 5): lo que se pinta (letra y
   nombre) y lo que se empuja a `state.incidenciasEdicion` al elegir son lo
   de F-030; las palabras extra no se pintan ni viajan.
7. **La ruta lee la config en cada petición** (con la caché de
   `cargar_config`) en vez de guardarla en el `Contenedor`: el contenedor
   doble de los tests de rutas no la tendría. `deps` solo la valida.
8. **Recarga tras el sync**: `await cargarTiposIncidencia()` detrás de
   `cargarPeriodo`, dentro del `try`: un sync fallido no la pide; si falla
   ella, avisa y deja el catálogo que había (la función de F-030, sin
   cambios).

## Fase RED (trazas reales)

**API** — `services/dedicacion-api/.venv/Scripts/python.exe -m pytest tests/test_f061_palabras.py -q --tb=line -p no:warnings`
(antes de `palabras_incidencia.py`, `config.yaml` y la ruta):

```
FFFFFFFFFFFFFFF                                                          [100%]
E   KeyError: 'palabras_extra'
...\tests\test_f061_palabras.py:37: KeyError: 'palabras_extra'
E   ModuleNotFoundError: No module named 'application.palabras_incidencia'
...\tests\test_f061_palabras.py:42: ModuleNotFoundError: No module named 'application.palabras_incidencia'
...
...\tests\test_f061_palabras.py:157: AssertionError: assert {'incidencias...Enfermedad'}]} == {'incidencias...s': [], ...}]}
15 failed in 8.60s
```

**Front, búsqueda** — `services/dedicacion-front/.venv/Scripts/python.exe -m pytest tests/test_f061_busqueda.py -q --tb=line -p no:warnings`
(con el filtro de F-030):

```
FFFFF.F                                                                  [100%]
E   AssertionError: assert [] == ['B', 'AT', 'M']
...\tests\test_f061_busqueda.py:66: AssertionError: assert [] == ['B', 'AT', 'M']
E   AssertionError: assert [] == ['AT']
...\tests\test_f061_busqueda.py:81: AssertionError: assert [] == ['AT']
E   AssertionError: assert [] == ['V']
...\tests\test_f061_busqueda.py:96: AssertionError: assert [] == ['V']
E   AssertionError: assert ['VACA', 'U', 'W'] == ['VACA', 'Y', 'W', 'U', 'R']
...\tests\test_f061_busqueda.py:131: AssertionError
E   AssertionError: assert ['A1', 'A2', 'A3', 'A4'] == ['A4', 'A2', 'A1', 'A3']
...\tests\test_f061_busqueda.py:148: AssertionError
E   assert 'sugerencia v...cia con «baj»' == 'sugerencia i...aboral</span>'
      - sugerencia inc activa|<span class="cod">B</span><span class="desc">Enfermedad/Acc. no laboral</span>
      + sugerencia vacia|Ninguna incidencia con «baj»
6 failed, 1 passed in 1.05s
```

El que pasa en RED es `test_f061_r3_toda_subcadena_…` a propósito: fija lo
que F-030 ya encontraba (criterio 3) y tiene que seguir en verde después.

**Front, recarga** — `… -m pytest tests/test_f061_recarga.py -q --tb=line -p no:warnings`
(sin la línea en `sincronizar`):

```
FF.                                                                      [100%]
E   AssertionError: assert ['/sync', 'cargarPeriodo'] == ['/sync', 'ca.../incidencias']
...\tests\test_f061_recarga.py:51: AssertionError
E   AssertionError: assert ['/sync', 'cargarPeriodo'] == ['/sync', 'ca.../incidencias']
...\tests\test_f061_recarga.py:59: AssertionError
2 failed, 1 passed in 0.45s
```

(El que pasa es «un sync fallido no recarga»: ya era así.) Después, los tres
ficheros en verde: 15, 7 y 3 passed.

## Criterios y su test

| Criterio | Tests |
|---|---|
| 1 api: `palabras`, `orden_busqueda`; sin entrada `[]`/`null`; entrada sin código en el catálogo no aparece | `test_f061_r1_*` (config real aprobada y su orden, lectura, config mal escrita, arranque, ruta con CIX sin entrada y CIF/CIH ausentes, ruta sin la clave) |
| 2 casos `baj`, `enf`, `enf pro`, `acc lab`, `vac`, `civ`, `ci`, `b`, `vacasiones`, `enfremedad`, tildes | `test_f061_r2_los_casos_…`, `…_cualquier_orden_tildes_…`, `…_errata_…`, `…_orden_por_categoria_…`, `…_empate_…` |
| 3 nada de lo de hoy se pierde; con número, lo de hoy | `test_f061_r3_toda_subcadena_…` (todas las subcadenas con letra de «letra nombre» de las 7, >1000 búsquedas) + los tests de F-030 R1 y R8-R13 sin cambios, en verde |
| 4 recarga tras sync; si falla, avisa y queda el que había | `test_f061_r4_*` |
| 5 el front no decide nada | `test_f061_r5_…` (pinta y elige lo de F-030) |
| 6 `INTEGRACION.md` §5 | T4 |
| 7 tests sin red ni BBDD; `init.sh` verde | ver Evidencias |

## Fuera del alcance / pendiente

- **`azure-apps/dedicacion.md`** (campos nuevos de `GET /incidencias`): lo
  hace el líder al desplegar (api → front), como dice la feature.
- **MANUAL tras desplegar** (no se puede en local sin BBDD con el catálogo):
  Ctrl+F5 en el front; en la celda del % de una línea teclear `baj` → B, AT,
  M (B arriba); `civ` → V; `vacasiones` → V; luego «Sincronizar Sigrid» y
  comprobar que el desplegable sigue saliendo sin recargar la página.
- No se pintan las palabras extra en el desplegable (no lo pide ningún
  criterio): con `baj`, AT sale sin que se vea por qué. Si molesta, es una
  feature aparte.

## Evidencias

Medidas el 2026-10-23 sobre `54ad111` (código final; luego solo papeleo).

| Evidencia | Valor |
|---|---|
| `bash harness/init.sh` (cachés `.arnes_cache/suite_*.ok` borradas antes) | **ENTORNO LISTO**, ningún `[KO]` |
| Tests: raíz | 418 passed, 1 skipped (61,2 s) |
| Tests: api | 1141 passed (73,5 s); antes de F-061, 1126: **+15** |
| Tests: front | 369 passed (45,2 s); antes, 359: **+10** |
| Tests: transfer | 1230 passed (25,7 s), sin cambios |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 32 líneas cambiadas cubiertas (32/32, umbral 80%, nivel estandar)` |
| Mutación (`python -m harness.mutacion --feature F-061`) | **10 generados, 10 muertos, 0 supervivientes**, 0 timeouts, 259 s → `progress/mutacion_F-061.md` |
| ruff | 277 avisos previos; los 2 que añadía F-061 corregidos (ISC004) o justificados (TRY004, `noqa` con motivo) |

- **Mutación**: el muestreo pedía hasta 20, pero solo salen 10 de las
  61 líneas Python de producción, todos de `palabras_incidencia.py`. No hay
  supervivientes que analizar.
- **El JavaScript** (`app.js`: búsqueda y recarga) queda fuera de la
  cobertura y de la mutación del arnés, que son solo Python. Lo cubren los
  tests de node: los 10 casos de los criterios, la escalera de categorías,
  el desempate y más de 1000 subcadenas del criterio 3.
- Última ejecución de `init.sh`, con el informe ya escrito y las cachés
  borradas: **ENTORNO LISTO**. Tests: 418 + 1 saltado, 1141, 369 y 1230.
  Cobertura de líneas cambiadas, 100 % (32/32). Tamaño del informe, 181/220.
  ruff, 277 avisos (los de antes).
