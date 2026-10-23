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
- Tests nuevos: `services/dedicacion-api/tests/test_f061_palabras.py` (19 tras la review 1),
  `services/dedicacion-front/tests/test_f061_busqueda.py` (9),
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

## Review 1 (CHANGES_REQUESTED): lo corregido

1. **Dos tests nuevos** en `test_f061_busqueda.py` (`61369dd`). Pasan con
   el código y cada uno falla con su mutante, aplicado a mano en `app.js` y
   revertido después. Comando:
   `.venv/Scripts/python.exe -m pytest tests/test_f061_busqueda.py::<test> -q --tb=line`.
   ```
   == mutante A: for (let n = w.length - 1; n <= Math.min(p.length, w.length); n++) {
   E   AssertionError: assert [] == ['B']
   ...\tests\test_f061_busqueda.py:108: AssertionError: assert [] == ['B']
   FAILED tests/test_f061_busqueda.py::test_f061_r2_errata_por_letra_que_falta
   == mutante B: if (normalizar(t.letra + " " + t.nombre).includes(q)) return 7;
   E   AssertionError: assert ['R', 'S'] == ['S', 'R']
   ...\tests\test_f061_busqueda.py:119: AssertionError: assert ['R', 'S'] == ['S', 'R']
   FAILED tests/test_f061_busqueda.py::test_f061_r2_la_subcadena_va_antes_que_la_errata
   ```
   Con `app.js` restaurado: `2 passed`.
2. **O1** (`e7a9371`). `palabras_por_codigo` solo toma por lista vacía la
   clave **que falta**. Un valor presente que no sea lista (`""`, `0`,
   `false` o `null`, también `palabras:` vacío en el YAML) da el `ValueError`
   de siempre. Un caso propio de F-061 que usaba `None` pasa a `[]`. Fase RED
   con `-m pytest tests/test_f061_palabras.py -q --tb=line`, antes del cambio:
   ```
   E   Failed: DID NOT RAISE ValueError
   ...\tests\test_f061_palabras.py:81: Failed: DID NOT RAISE ValueError
   FAILED tests/test_f061_palabras.py::test_f061_r1_una_config_mal_escrita_avisa_con_su_motivo[entradas9-palabras]
   … (entradas10, 11 y 12, igual)
   4 failed, 15 passed in 3.76s
   ```
   Después: `88 passed` (`test_f061_palabras`, `test_f030_catalogo` y `test_f023_sync_empresa`).
3. Las Evidencias se actualizan: la campaña Python se repite (cambió la línea
   35) y queda anotada la campaña manual de JS de la review.

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

Medidas el 2026-10-23 sobre `e7a9371` (código final tras la review 1).

| Evidencia | Valor |
|---|---|
| `bash harness/init.sh` (cachés `.arnes_cache/suite_*.ok` borradas) | **ENTORNO LISTO**, ningún `[KO]` |
| Tests raíz / api / front / transfer | 418 + 1 saltado (53,4 s) / **1145** (62,6 s; 1126 antes, +19) / **371** (40,4 s; 359 antes, +12) / 1230 (21,5 s) |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 32 líneas cambiadas cubiertas (32/32, umbral 80%, nivel estandar)` |
| Mutación Python (`python -m harness.mutacion --feature F-061`, 4 workers) | **9 generados, 9 muertos, 0 supervivientes**, 0 timeouts, 205,9 s → `progress/mutacion_F-061.md` (repetida tras O1; la 1.ª, 10/10 muertos) |
| Mutación JS (manual, review 1, `app.js`) | **24 mutantes: 22 muertos** con los tests de entonces; los **2 supervivientes** (`w.length + 1` → `w.length`; `return 5` → `return 7`) los matan los dos tests nuevos (trazas arriba) |
| ruff | 277 avisos previos; los 2 de F-061 corregidos (ISC004) o justificados (TRY004, `noqa` con motivo) |

- La muestra Python admitía hasta 20 mutantes, pero en las 63 líneas de
  producción solo hay 9 candidatos, todos en `palabras_incidencia.py`. No hay
  supervivientes que analizar.
- El JS queda fuera de la puerta de cobertura y de la mutación del arnés,
  que solo miden Python. Lo cubren los tests de node (casos de los criterios,
  categorías, desempate, erratas y más de 1000 subcadenas del criterio 3) y
  la campaña manual de la review.
