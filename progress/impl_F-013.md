<!-- progress/impl_F-013.md -->
# F-013 · Informe de implementación — Una línea sin partida no se escribe en silencio

- **Rama:** `feature/F-013-linea-sin-partida-confirma`
- **Rigor:** `critico` (fase RED con traza + cobertura ≥ 80 % + mutación con
  0 supervivientes)
- **Modo:** `sdd: false` — no hay spec; mandan los criterios `acceptance` de
  `harness/features.json`, que aquí se numeran **R1-R6** por su orden.
- **Servicio tocado:** **solo `dedicacion-transfer`**. `dedicacion-api` y
  `dedicacion-front` no se han tocado (verificado en el diff, §7).
- **Estado:** terminado. `bash harness/init.sh` en verde (§6).
- **Verificaciones MANUAL pendientes:** ninguna nueva de F-013. Sigue
  pendiente la del proyecto entero (escritura real contra Sigrid con
  `OBRA_PRUEBAS_FORZAR=false`), que no es de esta feature y exige
  autorización expresa del humano.

---

## 1. Qué cambia, en una frase

Antes, si el casado automático de partida fallaba en obra normal, la línea
**se escribía igual** con `paride = 0` y un aviso informativo que no retenía
nada. Ahora viaja como **conflicto con motivo propio** (`sin_partida`), no se
escribe sin confirmación explícita, y queda **omitida con su motivo** si
nadie confirma. Confirmarla la escribe con `paride = 0`, que es exactamente
lo que hacía antes.

El mecanismo **no se ha inventado**: es el de la Regla B de F-002 (la
sobrecarga del 100 %) aplicado a un tercer caso. Ni un campo nuevo en el
contrato, ni un canal nuevo de confirmación.

## 2. Tareas y commits

| Tarea | Qué | Commit |
|---|---|---|
| T1 | Tests de F-013 escritos ANTES del código (fase RED) + vocabulario de la regla en `reglas_porcentajes.py` | `5962ae0` |
| T2 | El pipeline emite el conflicto y `ejecutar` retiene y lista la línea | `abf51f6` |
| T3 | La regla, en la fuente única con procedencia; README y modelo remiten | `cea2a3f` |
| T4 | `next()` en vez de slice en los tests (cero avisos de ruff nuevos por ese motivo) | `3285fd9` |
| T5 | El conflicto lleva el parte al que iba la línea, sin guarda muerta | `89e0d29` |

Ningún `git add -A`; ningún `git push`; `harness/features.json` y
`progress/current.md` no se han tocado (los lleva el líder).

## 3. Decisiones de diseño, y por qué

### 3.1 El patrón de F-002 SÍ encajaba

Se leyó la Regla B antes de escribir nada (`reglas_porcentajes.py`,
`registro_pipeline.py`, `registro_models.py`, `test_f002_capacidad.py`,
`test_f002_conflicto.py`, `test_f002_pipeline.py`) y encaja sin forzar
nada: el `Conflicto` ya tenía `motivo`, la confirmación ya viajaba por
`pisar_claves`, la serialización HTTP ya es `asdict(c)` genérica, y la traza
en `omitidas` ya existía para la sobrecarga. **No hizo falta añadir ni un
campo** al `Conflicto` (lo cubre el test
`test_f013_r4_no_hace_falta_ningun_campo_nuevo`, que fija el conjunto exacto
de campos): eso es la señal de que el patrón valía, y si hubiera hecho falta
uno habría tocado replantear.

### 3.2 La clave de confirmación es POR LÍNEA

`clave_sin_partida(accion) = "sin_partida:{registro_id}"`.

- El **pisado** se identifica por la línea del parte (recurso|periodo|hora|
  partida) y la **sobrecarga** por recurso y parte, porque es propiedad del
  *conjunto* de líneas del trabajador.
- Que el casado falle es propiedad de **una** línea: su categoría y su
  nombre no casaron. Si la clave agrupara, confirmar la línea que el humano
  ha mirado arrastraría a otra suya que no ha visto — y eso es exactamente
  el silencio que la feature viene a romper.
- `registro_id` es el `id` de la asignación en PostgreSQL: identidad estable
  entre ejecuciones, no un índice de lista.
- No colisiona: la de pisado empieza por el `ide` del recurso (un entero) y
  la de sobrecarga por `sobrecarga:`. Cubierto por
  `test_f013_r1_la_clave_no_colisiona_con_las_otras_dos`.

### 3.3 El predicado mira `paride`, no el método de casado

`sin_partida(accion)` es `accion == "escribir" and paride == 0`. Se mira lo
que **acabaría en `hmores.paride`**, no `partida_metodo`: cualquier camino
que deje la partida a cero cae aquí, hoy y el día que haya otro. Preguntar
por el método dejaría fuera al camino nuevo sin que nada avisara.

### 3.4 Postventa y obra normal siguen siendo dos caminos distintos

Lo pedía el encargo explícitamente y está escrito en tres sitios (docstring
de `sin_partida`, `ARCHITECTURE.md#regla-sin-partida` y el test
`test_f013_la_postventa_sin_partida_se_sigue_omitiendo`):

- **Postventa sin partida ⇒ se OMITE** (P5, en `ReglasPorcentajes.decidir`),
  y ni siquiera llega a ser una acción de escritura, así que no hay nada que
  confirmar. Motivo: la obra de postventa es un presupuesto **ajeno** al de
  la obra original; escribir ahí «sin partida» no significaría nada.
- **Obra normal sin partida ⇒ se PREGUNTA.** Aquí sí hay destino —la propia
  obra— y lo único que falta es la imputación analítica. Por eso se puede
  escribir, y por eso tiene sentido preguntar.

Hay además un control positivo
(`test_f013_la_postventa_que_si_casa_se_escribe_sin_preguntar`) para que el
test de arriba no pueda pasar por el motivo equivocado.

### 3.5 Interacción con la sobrecarga del 100 % (y con el pisado)

**Qué se le enseña al usuario: los DOS (o los tres) avisos, cada uno con su
clave.** Una misma línea puede caer en varios y cada uno es una decisión
distinta («impútalo sin partida» ≠ «acepto que se pase del 100 %»). Esconder
uno haría que el humano confirmara el otro sin saber lo que firma.

**Orden: `sin_partida` → `pisado` → `sobrecarga`.** No es estético: cada
aviso **da por hecho** el anterior. La identidad del pisado usa el
`paride = 0` de esta línea, y la suma de la sobrecarga incluye su `can`. Es
el mismo criterio con el que F-002 puso el pisado antes que la sobrecarga
(R30/R31), extendido un escalón hacia arriba. Tests:
`test_f013_los_dos_avisos_se_ensenan_a_la_vez`,
`test_f013_el_orden_es_sin_partida_primero`,
`test_f013_pisado_y_sin_partida_a_la_vez`.

**Cada uno retiene por separado.** Confirmar solo uno no escribe nada
(`test_f013_confirmar_solo_la_sobrecarga_no_escribe` y su simétrico); con
todos confirmados se escribe una sola vez y con `paride = 0`.

**La hipótesis de la sobrecarga no cambia.** Su suma sigue calculándose con
todas las acciones `escribir`, es decir, **suponiendo que el «sin partida»
se confirma**. Es la misma hipótesis segura que F-002 documenta para los
pisados: cualquier otra combinación escribe estrictamente menos, porque
denegar el «sin partida» retira esa línea de la suma. Por eso no hizo falta
tocar `evaluar_capacidad`.

**Riesgo real cazado con un test:** confirmar el **pisado** sin confirmar el
«sin partida» podría borrar la línea vieja de Sigrid **sin escribir la que
la sustituye** (el borrado se emite por conflicto confirmado y la escritura
se bloquea por registro). La guarda R32 de F-002 ya cubre este tercer caso
—no hizo falta código nuevo—, pero **no estaba probada para él**, así que
ahora lo está: `test_f013_confirmar_el_pisado_sin_la_partida_no_borra`, con
su control positivo `test_f013_confirmando_las_dos_si_se_pisa`.

### 3.6 Una línea retenida por dos avisos sale UNA vez en `omitidas`

`dedicacion-api` hace un `UPDATE` por entrada de `omitidas` sobre la **misma**
asignación: dos entradas serían dos escrituras de las que solo sobrevive la
última, y un recuento de omitidas inflado en el front. Se emite una sola, con
el motivo del **primer** aviso que la retuvo (el que los demás presuponen).
Lo que el usuario tiene que decidir no se pierde: los avisos completos siguen
en `pendientes_confirmacion`, que es donde se decide. Test:
`test_f013_la_omision_no_se_duplica_con_los_dos_avisos`.

La condición de `ejecutar` se escribió **por lo que excluye** (`if motivo ==
"pisado": continue`) y no por lo que incluye: así un motivo futuro deja
rastro por defecto, que es el lado seguro del error.

### 3.7 El aviso de la acción dejó de mentir

`AccionLinea.aviso` decía «se imputa sin partida (editable)». Con F-013 eso
es **falso**: no se imputa nada mientras nadie confirme. Ahora dice que no se
escribe sin confirmarlo. El campo sigue siendo el mismo y el front lo pinta
igual (`test_f013_r1_el_aviso_de_la_accion_ya_no_promete_que_se_escribe`).

### 3.8 Sin guardas que ningún test pueda ejercitar

En el paso 6 bis, `partes[...]` en vez de `partes.get(...)` y `int(a.recurso_ide)`
sin `or 0`: el paso 5 deja una entrada por cada acción `escribir` y ninguna
acción *pasa* a serlo después (el paso 6 solo las saca), y P1 omite toda
línea sin recurso. Una rama de respaldo inalcanzable es una rama que ningún
test mata y que nadie mantiene — el mismo criterio que ya aplica el bloque de
capacidad de F-002.

## 4. Fase RED (obligatoria, nivel `critico`)

### 4.1 Primera ejecución: los tests no compilan porque el vocabulario no existe

Comando (desde `services/dedicacion-transfer/`):

```
.venv/Scripts/python.exe -m pytest tests/test_f013_sin_partida.py -q --tb=line
```

Salida real:

```
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests\test_f013_sin_partida.py:33: in <module>
    from application.services.reglas_porcentajes import (
E   ImportError: cannot import name 'AVISO_SIN_PARTIDA' from 'application.services.reglas_porcentajes' (C:\Users\pgris\PycharmProjects\porcentajes\services\dedicacion-transfer\application\services\reglas_porcentajes.py)
=========================== short test summary info ===========================
ERROR tests/test_f013_sin_partida.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.30s
```

### 4.2 Segunda ejecución: con el vocabulario y SIN la conducta, 26 fallos reales

Tras añadir solo las constantes y las dos funciones puras (nada del
pipeline), la misma orden con `--tb=short`. Extractos literales de los
requisitos centrales:

```
_____________ test_f013_r1_una_linea_sin_partida_emite_conflicto ______________
tests\test_f013_sin_partida.py:122: in test_f013_r1_una_linea_sin_partida_emite_conflicto
    assert len(pf.conflictos) == 1, pf.conflictos
E   AssertionError: []
E   assert 0 == 1
E    +  where 0 = len([])
E    +    where [] = Preflight(obra_destino=ObraEntrada(ide=828942, codigo='0404', nombre='PRUEBAS'), obra_origen=ObraEntrada(ide=None, cod...o='partida no localizada para la categoría/nombre: se imputa sin partida (editable)', hmores_ide=None)], conflictos=[]).conflictos
```

```
__________________ test_f013_r2_sin_confirmar_no_se_escribe ___________________
tests\test_f013_sin_partida.py:217: in test_f013_r2_sin_confirmar_no_se_escribe
    assert cli.inserts() == [] and res.escritas == []
E   AssertionError: assert ([{'hmoide': 7...s': 128, ...}] == []
E     
E     Left contains one more item: {'hmoide': 777, 'obra': ObraEntrada(ide=828942, codigo='0404', nombre='PRUEBAS'), 'reside': 400, 'pos': 128, ...}
E     Use -v to get more diff)
```

> Este es **el fallo que da sentido a la feature**: hoy el pipeline emite el
> `INSERT` de una línea que nadie ha confirmado.

```
______________ test_f013_r2_queda_listada_en_omitidas_con_motivo ______________
tests\test_f013_sin_partida.py:232: in test_f013_r2_queda_listada_en_omitidas_con_motivo
    assert [o["registro_id"] for o in res.omitidas] == [1]
E   assert [] == [1]
E     
E     Right contains one more item: 1
```

```
________________ test_f013_r2_lo_que_si_casa_se_escribe_igual _________________
tests\test_f013_sin_partida.py:253: in test_f013_r2_lo_que_si_casa_se_escribe_igual
    assert [e["registro_id"] for e in res.escritas] == [2]
E   assert [1, 2] == [2]
E     
E     At index 0 diff: 1 != 2
```

```
____________ test_f013_confirmar_el_pisado_sin_la_partida_no_borra ____________
tests\test_f013_sin_partida.py:534: in test_f013_confirmar_el_pisado_sin_la_partida_no_borra
    assert cli.borrados() == [], cli.borrados()
E   AssertionError: [5001]
E   assert [5001] == []
```

```
_______ test_f013_r1_el_aviso_de_la_accion_ya_no_promete_que_se_escribe _______
tests\test_f013_sin_partida.py:205: in test_f013_r1_el_aviso_de_la_accion_ya_no_promete_que_se_escribe
    assert pf.acciones[0].aviso == AVISO_SIN_PARTIDA
E   AssertionError: assert 'partida no l...da (editable)' == 'partida no l... confirmación'
E     - a/nombre: no se escribe sin confirmarlo — elige una partida o marca la confirmación
E     + a/nombre: se imputa sin partida (editable)
```

Resumen de esa ejecución:

```
26 failed, 18 passed in 0.50s
```

Los 18 que pasaban son las funciones puras recién escritas (predicado y
claves), los dos controles positivos del escenario y los documentales que ya
se cumplían. Los 26 fallos incluyen los cinco documentales de R6 (la regla
todavía no estaba en `ARCHITECTURE.md`).

### 4.3 Tercera ejecución: en verde

```
232 passed, 1 warning in 0.46s
```

(El único `warning` es previo a F-013:
`PytestReturnNotNoneWarning` en `test_pipeline_offline.py::test_preflight`.)

## 5. Ficheros tocados

| Fichero | Qué |
|---|---|
| `services/dedicacion-transfer/application/services/reglas_porcentajes.py` | `PREFIJO_CLAVE_SIN_PARTIDA`, `MOTIVO_SIN_PARTIDA`, `AVISO_SIN_PARTIDA`, `sin_partida()`, `clave_sin_partida()` — funciones puras, sin I/O |
| `services/dedicacion-transfer/application/pipelines/registro_pipeline.py` | paso **6 bis** (emite el conflicto), aviso de la acción, y en `ejecutar` la retención + la entrada única en `omitidas` |
| `services/dedicacion-transfer/domain/models/registro_models.py` | docstrings: el `Conflicto` tiene TRES motivos; el `aviso` ya no implica que se escriba |
| `services/dedicacion-transfer/README.md` | tabla de reglas (Regla C) y retirada de la regla reenunciada, que además ya era falsa |
| `docs/ARCHITECTURE.md` | punto **8** nuevo con ancla `regla-sin-partida` + enlace desde `#regla-conflicto`; renumerados 8/9/10 → 9/10/11 |
| `services/dedicacion-transfer/tests/test_f013_sin_partida.py` | **nuevo**, 44 tests |
| `services/dedicacion-transfer/tests/test_f002_fuente_unica.py` | una línea: `range(1, 11)` → `range(1, 12)` |
| `progress/mutacion_F-013.md` | generado por la campaña |

**Sobre el único cambio en un test de F-002**: el documento pasó de 10 a 11
puntos, y `test_f002_r1_ningun_punto_sigue_pendiente` recorría 1-10. Sin
subir el rango, el punto nuevo habría quedado sin vigilar por una guarda que
existe justo para eso. No se tocó su tupla `ANCLAS`: la propiedad que esa
lista aporta (el ancla existe y no está duplicada) la comprueba ya
`test_f013_r6_la_regla_tiene_su_ancla_en_la_fuente_unica`, y ampliar una
estructura de una feature `blocked` sin necesidad solo añade superficie de
revisión.

## 6. Verificación: `bash harness/init.sh`

Ejecutado tal cual, en verde. Líneas relevantes de la última ejecución:

```
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 178 avisos (deuda previa, no bloquea)
[OK] pytest en verde (con medición de cobertura)          <- suite raíz, 11
[OK] servicio api (services/dedicacion-api): pytest en verde
[AVISO] servicio front: sin directorio de tests
[OK] servicio transfer (services/dedicacion-transfer): pytest en verde   <- 232
[OK] PUERTA COBERTURA: 100.0% de 24 líneas cambiadas cubiertas (24/24, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-013-linea-sin-partida-confirma
----------------------------------------
ENTORNO LISTO. Puedes trabajar.
```

El `[AVISO]` del front («sin directorio de tests») es **anterior a F-013** y
no es el residuo de `__pycache__` que menciona `progress/current.md`: aquí
directamente no existe `services/dedicacion-front/tests/`.

## 7. Criterios `acceptance`, uno a uno

| # | Criterio | Dónde se cumple |
|---|---|---|
| 1 | Conflicto con motivo propio, distinguible del pisado y de la sobrecarga | `motivo="sin_partida"` + clave con prefijo propio. Tests `test_f013_r1_*` |
| 2 | Sin confirmación: omitida y listada con su motivo | `ejecutar` la bloquea y la lista. Tests `test_f013_r2_*` |
| 3 | Con confirmación: se escribe con `paride=0` | Tests `test_f013_r3_*`; el `INSERT` lleva `paride == 0` |
| 4 | Degradación elegante; no se toca la API ni el front | Ni un campo nuevo; `asdict(c)` ya serializa `motivo`. `git diff --stat dev...HEAD` no lista ningún fichero de `dedicacion-api` ni de `dedicacion-front`. El test parametrizado `test_f013_r4_ni_la_api_ni_el_front_enumeran_los_motivos` deja la promesa **vigilada**: ninguno de los dos ramifica por el motivo |
| 5 | Tests offline, sin red ni BBDD, con las fixtures de `conftest.py` | Todo el fichero usa `ClienteFalso`/`SettingsFalso`/`linea`/`linea_previa`; ningún socket, ningún `.env` |
| 6 | La regla en la fuente única, con procedencia | `docs/ARCHITECTURE.md#regla-sin-partida`, con *«Confirmado por Pablo Gris (responsable del proyecto) el 2026-08-20 · preflight real del periodo 2026-07»*. **Nada atribuido a Administración** — hay un test que lo comprueba. Tests `test_f013_r6_*` |
| 7 | `bash harness/init.sh` en verde | §6 |

> **Precisión sobre el criterio 4.** «Degradación elegante» significa que el
> front sigue funcionando sin cambios: pinta el conflicto nuevo con el mismo
> código con el que pinta los otros dos (una casilla y su `clave`), y la API
> lo pasa y persiste `omitidas` sin mirar el tipo. **No significa** que la
> línea se siga escribiendo si nadie confirma: si el usuario ignora el aviso,
> la línea **no se escribe**. Eso es el objetivo de la feature, no una
> regresión.

## 8. Qué queda fuera (a propósito)

- **El texto de la casilla en el front.** Hoy el front pinta cualquier
  conflicto como «Pisar MJEFO de Fulano: se borran ___ y se escribe 40,00 %»
  (`pintarModalPreflight`, `static/js/app.js`).
  Con `lineas` vacío, el «se borran» queda colgando — igual que ya le pasa a
  la sobrecarga desde F-002. **Funciona y se puede confirmar**, pero el texto
  es pobre. Redactarlo por motivo es trabajo de `dedicacion-front`, y F-013
  tiene por criterio explícito **no** tocarlo: es una feature aparte, y
  ahora es más rentable que antes porque afecta a dos motivos de tres.
- **Contar en el modal cuántas líneas quedan retenidas por cada motivo.**
  Mismo servicio, misma razón.
- **Que el usuario elija la partida en vez de confirmar** ya funciona hoy: el
  preflight publica `partidas_obra` y el front las ofrece en un desplegable.
  No hacía falta tocar nada; queda dicho en la regla para que nadie lea
  «confirmar sin partida» como la única salida.
- **Mejorar el casado automático** para que la jefa de obra del caso real
  encuentre su partida. Es otro problema (el presupuesto de la obra `0025` no
  tiene una partida que case con su categoría/nombre) y otra feature.
- **Ninguna escritura real contra Sigrid.** No se ha arrancado ningún
  servicio, no se ha tocado ningún `.env` y el transfer sigue con
  `OBRA_PRUEBAS_FORZAR=true`.

## 9. Evidencias

| Evidencia | Valor real | Cómo se obtuvo |
|---|---|---|
| **Tests ejecutados y resultado** | **327 pasan, 0 fallan** — 232 (`dedicacion-transfer`, de los cuales **44 nuevos de F-013**) + 84 (`dedicacion-api`) + 11 (suite de la raíz) | `python -m pytest -q` con el intérprete de cada servicio; los mismos que ejecuta `harness/init.sh` |
| **Cobertura de las líneas cambiadas** | **100,0 % — 24/24 líneas** (umbral 80 %, nivel `critico`) | línea `PUERTA COBERTURA` de `bash harness/init.sh` |
| **Mutantes generados y supervivientes** | **7 generados, 7 evaluados, 7 muertos, 0 supervivientes, 0 timeouts** (campaña completa, sin muestreo) | `python -m harness.mutacion --feature F-013` → `progress/mutacion_F-013.md` |
| **Tiempo de ejecución de la suite** | transfer **0,46 s** · api **1,34 s** · raíz **0,09 s**; campaña de mutación **3,1 s** con 16 workers | lo que imprime cada suite |
| **Avisos de `ruff`** | 176 → **178** (+2) | `python -m ruff check .` |

### 9.1 Supervivientes

**Ninguno.** No hay nada que justificar: el nivel `critico` exige cero y la
campaña dio cero. Los siete mutantes y su veredicto:

| # | Fichero:línea | Mutación | Veredicto |
|---|---|---|---|
| 1 | `registro_pipeline.py:289` | `if not sin_partida(a):` → `if sin_partida(a):` | muerto |
| 2 | `registro_pipeline.py:460` | `c.motivo == "pisado"` → `!=` | muerto |
| 3 | `registro_pipeline.py:466` | `c.motivo == "sobrecarga"` → `!=` | muerto |
| 4 | `reglas_porcentajes.py:302` | `and` → `or` | muerto |
| 5 | `reglas_porcentajes.py:302` | `paride == 0` → `paride != 0` | muerto |
| 6 | `reglas_porcentajes.py:302` | `accion == "escribir"` → `!=` | muerto |
| 7 | `reglas_porcentajes.py:302` | `paride == 0` → `paride == 1` | muerto |

**Por qué solo 7 mutantes para 174 líneas en alcance:** el mutador ataca
comparaciones, operadores lógicos, negaciones y literales enteros, y el grueso
del diff es docstrings, comentarios y la construcción del `Conflicto` (paso de
argumentos, sin decisiones). La conducta nueva se concentra en **dos
decisiones** —el predicado y el reparto de motivos en `ejecutar`—, y las dos
están mutadas y muertas. La única línea con decisión que el mutador no genera
es la deduplicación de `omitidas` (`if r in omitidas_ya`), cubierta
directamente por `test_f013_la_omision_no_se_duplica_con_los_dos_avisos`.

### 9.2 Sobre los dos avisos de `ruff` nuevos

Los dos son `C408 Unnecessary dict() call` en las dos fábricas de fixtures
del fichero de tests nuevo (`linea_que_no_casa` y `accion`). Es **el mismo
idioma** que usan `tests/conftest.py` (líneas 259 y 268) y
`tests/test_f002_capacidad.py` (línea 51), que disparan exactamente el mismo
aviso: `dict(...)` seguido de `.update(kw)`. Se mantuvo por coherencia con
los ficheros hermanos; `ruff` es informativo en este repositorio y la
alternativa era escribir el fichero nuevo con un estilo distinto al de sus
vecinos. Los otros tres avisos que aparecieron en la primera pasada (`RUF015`,
slice `[0]` en vez de `next()`) sí se corrigieron (commit `3285fd9`).

## 10. Aviso al líder

Nada bloqueado, nada ambiguo, ninguna desviación respecto de los criterios
`acceptance`. Los dos puntos que merecen decisión del humano —y que **no**
son requisito de F-013— están en §8: el texto de la casilla del front, que
ahora es pobre para dos motivos de tres, y el casado automático de partidas
del caso real de julio.
