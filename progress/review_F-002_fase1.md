<!-- progress/review_F-002_fase1.md -->
# F-002 · Review de la Fase 1 (T1–T5)

- **Veredicto:** **APPROVED** (2ª pasada, sobre `f469de8`).
  La 1ª pasada, sobre `2987fc0`, fue CHANGES_REQUESTED por el rastro
  documental; el código nunca estuvo en cuestión. Ver §11.
- **Rama:** `feature/F-002-reglas-postventa-conflicto`
- **Alcance revisado:** **solo T1–T5**. T6 en adelante están bajo la ⛔ PARADA
  de `tasks.md` y **no se cuentan como trabajo faltante**.
- **Nivel de rigor:** `critico` (declarado en `harness/features.json`).
  Exige: fase RED en los requisitos centrales + cobertura de líneas cambiadas
  ≥ 80 % + campaña de mutación con **cero supervivientes**, y verificaciones
  `MANUAL (humano)` listadas con su comando y su resultado.
- **Fecha:** 2026-08-19.

---

> **Nota de lectura.** Las secciones §1–§10 son la **1ª pasada** y se
> conservan tal cual: son la evidencia de lo que se verificó y por qué se
> rechazó. Los checkboxes que quedaron en `[ ]` se cierran en la **§11**, que
> es la que manda sobre el veredicto final.

---

## 0. Resumen del veredicto (1ª pasada)

**La ingeniería de T1–T5 está bien hecha y la he verificado de forma
independiente, punto por punto: pasa todo lo que el humano pidió mirar con
lupa.** El refactor de T3 preserva la conducta, el defecto R13 era real y lo
he reproducido, la campaña de mutación reejecutada da los mismos totales y la
cobertura recalculada coincide al dígito.

El rechazo **no es por el código**. Es por el rastro documental del arnés, que
está sin actualizar y en un punto **activamente falso**:

1. `tasks.md` tiene T1–T5 en `[ ]` aunque están hechas y commiteadas.
2. `progress/current.md` afirma «**No se ha tocado ni una línea de código**» y
   «Sin commits todavía de esta sesión» cuando hay 8 commits y 5 tareas
   cerradas; y declara las consultas contra Sigrid «NO ejecutadas» cuando
   `progress/sigrid_F-002.md` documenta la C2 ejecutada.
3. `harness/features.json` deja F-002 en `spec_ready` con la Fase 1 dentro.

Los tres son checkboxes vacíos de C2, C4 y C5, y `CHECKPOINTS.md` es
inequívoco: «un checkbox vacío en C1–C5 es CHANGES_REQUESTED». No es una
formalidad: `progress/current.md` es la memoria externa del arnés y es lo
primero que lee el líder de la sesión siguiente. Tal como está, le dice que
esta feature no ha empezado.

Es trabajo de minutos, no rework. Ver §7.

---

## 1. C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina con exit code 0. Ejecutado tal cual, sin
      pipes ni `tail`. Cierre: `ENTORNO LISTO. Puedes trabajar.`
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`,
      `progress/current.md`, `progress/history.md`, `docs/ARCHITECTURE.md`,
      `docs/CONVENTIONS.md`.

Líneas relevantes de la salida real:

```
[OK] pytest en verde (con medición de cobertura)          11 passed in 0.34s
[OK] servicio api (services/dedicacion-api): pytest en verde (caché: árbol sin cambios…)
[AVISO] servicio front (services/dedicacion-front): sin directorio de tests
[OK] servicio transfer (services/dedicacion-transfer)     90 passed, 5 xfailed in 2.34s
[OK] PUERTA COBERTURA: 96.8% de 31 líneas cambiadas cubiertas (30/31, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-002-reglas-postventa-conflicto
[AVISO] ruff: 174 avisos (deuda previa, no bloquea)
```

**La línea del servicio `api` venía de caché, así que la he ejecutado yo a
mano** (un `[OK]` cacheado no es una verificación mía):

```
$ cd services/dedicacion-api && python -m pytest -q
21 passed in 0.09s
```

La del `transfer` **no** salió de caché: se ejecutó de verdad en esa misma
corrida (90 passed, 5 xfailed).

Los dos `[AVISO]` son deuda previa del repositorio, no de esta feature.

## 2. C2 — El estado es coherente

- [x] Como mucho UNA feature `in_progress`: hay **cero** (init.sh: «en curso:
      ninguna»). El límite se respeta.
- [x] La rama actual es `feature/F-002-reglas-postventa-conflicto`, nunca
      `main`.
- [ ] **`progress/current.md` NO describe la sesión activa.** Describe la
      sesión anterior (la del `spec-author`) y contradice los hechos:
      - línea 9: «Estado: spec escrita… **No se ha tocado ni una línea de
        código.**» — falso: T1–T5 están implementadas y commiteadas.
      - línea 109: «Sin commits todavía de esta sesión.» — falso: hay 8
        commits en la rama por encima de la spec.
      - línea 85: «### 3. Consultas de lectura contra Sigrid — NO
        ejecutadas» — falso: `progress/sigrid_F-002.md` documenta la **C2**
        ejecutada el 2026-08-19 con 248 filas y `truncated: false`.

      El protocolo del implementer (`.claude/agents/implementer.md:28`) obliga
      a mantenerlo actualizado. Es el fallo más serio de los tres: la memoria
      externa del arnés miente sobre lo que hay hecho.
- [x] Toda feature `done` tiene su resumen en `progress/history.md` (F-001
      cerrada; F-002 no es `done`, así que no aplica todavía).

## 3. C3 — El código respeta arquitectura y convenciones

- [x] **Arquitectura hexagonal respetada.** El movimiento de fondo va en la
      dirección correcta: `clave_conflicto` **sale** de `domain/` y **entra**
      en `application/services/`, de modo que la dependencia es
      application → domain. Verificado que `domain/` no importa de
      `application`, `infrastructure` ni `interface_adapters`:
      búsqueda sin resultados. `interface_adapters/api/app.py` importa de
      `application`: correcto.
- [x] **Primera línea de cada fichero con su ruta relativa.** Comprobado en
      los 10 ficheros de código tocados o creados; todos la llevan
      (`# tests/conftest.py`, `# application/services/reglas_porcentajes.py`,
      …).
- [x] **Sin `print()` de debug, sin TODOs sin contexto, sin secretos
      hardcodeados, sin dependencias nuevas.** Barrido sobre el diff:
      - `print(` añadido: ninguno.
      - `TODO|FIXME|XXX`: el único acierto es la palabra castellana «TODO»
        dentro de un docstring («En pruebas TODO se escribe en la obra de
        pruebas»), no un marcador.
      - patrones `password|secret|api[_-]?key|function[_-]?key|token|
        connectionstring|Bearer|AccountKey`: ninguno.
      - `requirements.txt` no se toca: cero dependencias nuevas.
- [x] **Las tres trampas del proyecto, vigiladas:**
      - **Escala del porcentaje.** La feature no añade ninguna conversión.
        Además la fija con test y con mutante: `test_f002_r8_el_porcentaje_no_
        viaja_sobre_100` y la fase RED 3.5 (romper `can` a `porcentaje * 100`
        tumba 3 tests).
      - **Postventa no se escribe en su obra.** Nada la trata como línea
        normal; `campos_identidad("postventa")` conserva `paride` justo para
        eso, y `test_f002_r14_en_postventa_la_partida_si_distingue` lo fija.
      - **Solo escribe el transfer, en `ruesma`, con `synckey` y modo
        pruebas.** No se añade ninguna escritura, no se toca
        `sigrid_write_client.py`, no se toca ningún `.env` y
        `OBRA_PRUEBAS_FORZAR` sigue a `true`. El único cambio en la emisión de
        sentencias es la **deduplicación de `DELETE`** de R13, que emite
        estrictamente **menos** borrados que antes, nunca más.

## 4. C3 bis — Documentos que entran de fuera

**N/A justificado:** la feature **no añade ni modifica ningún fichero en
`docs/referencia/`**. Comprobado con `git diff dev..HEAD --stat --
docs/referencia/`: salida vacía. No hay original en PDF ni ofimática en el
diff ni en el árbol. Al no haber documento nuevo, no hay barrido de datos
sensibles que ejecutar (el barrido general de secretos sobre todo el diff sí
está hecho, en C3, y salió limpio).

## 5. C4 — La verificación es real

- [x] **Cada requisito EARS de la Fase 1 tiene ≥ 1 test trazable y pasa.**
      Tabla en §8. 86 tests `test_f002_*` + 5 `xfail(strict=True)`.
- [x] **Los unit tests no tocan red ni BBDD.** Búsqueda de
      `httpx|requests|socket|psycopg|sqlalchemy|urllib|pyodbc|connect(` en
      `conftest.py` y los cuatro `test_f002_*.py`: el único acierto es la
      frase «No abre ningún socket» del docstring del `ClienteFalso`. El
      `test_f002_fuente_unica.py` solo hace I/O de ficheros locales.
- [ ] **Las verificaciones `MANUAL (humano)` NO están listadas en
      `progress/current.md` con su comando exacto y su estado real.** Están
      bien listadas, pero en el sitio equivocado: `progress/impl_F-002.md` §6
      (T7, T13, T14, con comando). `CHECKPOINTS.md` C4 pide expresamente
      `progress/current.md`, y lo que ese fichero dice hoy sobre ellas es
      falso (declara C1–C5 «NO ejecutadas» con la C2 ya ejecutada).

## 6. C4 bis — El rigor declarado se cumple

- [x] **`rigor` declarado y válido:** `"rigor": "critico"` en la entrada
      F-002 de `harness/features.json`.

- [x] **Fase RED.** El informe trae **salida real pegada**, no la frase «se
      hizo TDD», y con los dos métodos legítimos:
      - **RED real contra producción** donde el entregable era código que no
        existía: R13 (§3.1) y R1–R5 (§3.2, «25 failed, 4 passed, 4 xfailed»).
      - **RED por rotura en copia aislada** donde el entregable era el test
        sobre código ya escrito: R6, R7, R8, R9, R12, R14, R11, R10
        (§3.3–3.10), cada uno declarando qué línea se rompió.
      **He reproducido la de R13 yo mismo** (ver §6.1): coincide carácter por
      carácter con la pegada en el informe.

- [x] **Cobertura.** `[OK] PUERTA COBERTURA: 96.8% de 31 líneas cambiadas
      cubiertas (30/31, umbral 80%, nivel critico)`. **Recalculada por mí de
      forma independiente** con `harness.cobertura` + `harness.alcance`:

      registro_pipeline.py    8 relevantes, 0 sin cubrir
      partida_resolver.py     0 relevantes
      reglas_porcentajes.py  22 relevantes, 0 sin cubrir
      registro_models.py      0 relevantes
      app.py            NO MEDIDO, 1 línea ejecutable cambiada: la 19
      TOTAL 30 / 31

      Coincide exactamente con la puerta y con el informe.

- [x] **Mutación: totales verificados de forma independiente.** Recálculo
      puro con `harness.alcance` + `harness.mutacion.generar_mutantes` (sin
      ejecutar la suite ni escribir en disco):

      | Fichero | Líneas (informe) | Líneas (recalculado) | Mutantes |
      |---|---|---|---|
      | `registro_pipeline.py` | 18 | **18** | 0 |
      | `partida_resolver.py` | 6 | **6** | 0 |
      | `reglas_porcentajes.py` | 97 | **97** | **9** |
      | `registro_models.py` | 4 | **4** | 0 |
      | `app.py` | 2 | **2** | 0 |
      | **Total** | **127** | **127** | **9** |

      Además he comprobado los **9 mutantes uno a uno** contra la tabla §4.2
      del informe: coinciden línea, operador y texto original→mutado en los
      nueve (72 `logico`, 72 `entero`, 100 `comparacion`, 102 `comparacion`,
      125 `logico`, 126 `booleano`, 130 `comparacion`, 131 `booleano`, 132
      `booleano`). El `ref_diff` recalculado es el mismo que declara el
      informe (`c43a12fd…` .. `feature/F-002-reglas-postventa-conflicto`).

      **No aplica la prueba de control del cero:** la campaña no declara cero
      mutantes, declara nueve.

- [x] **Los muertos están comprobados, no solo contados.** El informe declara
      «Tiempo total 11.9 s» (< 5 min), así que **he reejecutado la campaña
      entera**, con la salida fuera de `progress/`:

      ```
      $ python -m harness.mutacion --feature F-002 --workers 1 \
          --salida <scratchpad>/mutacion_review.md
      9 mutantes evaluados, 9 muertos, 0 supervivientes, 0 timeouts en 9.4 s
      ```

      | Métrica | Informe | Mi reejecución |
      |---|---|---|
      | Mutantes | 9 | **9** |
      | Muertos | 9 | **9** |
      | Supervivientes | 0 | **0** |
      | Timeouts | 0 | **0** |

      Los 9 salieron `muerto` uno a uno en la traza. **Árbol limpio después**
      (`git status`: los mismos tres artefactos de cobertura que ya estaban
      antes de lanzarla, ninguno nuevo; sin stashes).

      **Sobre `--workers 1`.** El humano pidió probar antes la campaña
      paralela porque los ficheros sin versionar de F-003 ya no están. Lo he
      hecho y **sigue abortando**, pero por un motivo distinto del que decía
      el implementer:

      ```
      $ git status --porcelain
       M coverage.json
       M services/dedicacion-transfer/.coverage
       M services/dedicacion-transfer/coverage.json
      $ python -m harness.mutacion --feature F-002 --salida <scratchpad>/…
      El árbol principal tiene cambios sin commitear y la campaña paralela crea
      sus worktrees desde HEAD: evaluaría un código distinto del que ves en
      disco. Commitea los cambios o lanza la campaña con --workers 1.
      ```

      No son ficheros de F-003: son los **tres artefactos de cobertura
      versionados que `bash harness/init.sh` reescribe en cada ejecución**
      (F-009 del backlog). Como el reviewer está obligado a ejecutar
      `init.sh` antes que nada, **el árbol nunca puede estar limpio cuando le
      toca lanzar la campaña**, y `--workers 1` es de facto obligatorio para
      todo reviewer de este repositorio. Propuesta de mejora en §9.

- [x] **Cero supervivientes**, así que no hay ninguna sección de análisis en
      `PENDIENTE` ni justificación que aceptar. Cumple la exigencia extra del
      nivel `critico`.

- [x] **Sección «Evidencias» con los cuatro números.** `progress/impl_F-002.md`
      §4: tests (90 passed / 5 xfailed en transfer, 11 en raíz, 21 en api),
      cobertura de lo cambiado (96,8 %, 30/31), mutantes y supervivientes
      (9/9, 0), y tiempo de la suite (transfer 1,41 s; raíz 0,45 s; api
      0,39 s).

- [x] Ningún punto de este bloque marcado N/A.

### 6.1 · Reproducción independiente del defecto R13

El humano pidió confirmar que R13 era un defecto real. **Lo es.** Lo he
reproducido sin tocar el árbol: copia del servicio al scratchpad (sin `.venv`)
y reversión **solo** de `registro_pipeline.py` a su versión previa a T4
(`22328fb`), que se diferencia de la actual exactamente en las 8 líneas de la
deduplicación y en nada más (verificado con `diff`).

```
$ cd <scratchpad>/r13 && python -m pytest tests/test_f002_pipeline.py -q
.......F..                                                          [100%]
>       assert cli2.borrados() == [5001], cli2.borrados()
E       AssertionError: [5001, 5001]
E       assert [5001, 5001] == [5001]
E         Left contains one more item: 5001
1 failed, 9 passed in 0.65s
```

Idéntico a la traza RED del informe. **Dos `DELETE` del mismo `hmores.ide`, y
`res.borradas` contando 2**, contra código de producción real.

**El arreglo es correcto.** Dedupica por `ls.ide` con un `set` acumulado sobre
**todos** los conflictos confirmados —no dentro de cada conflicto—, que es el
ámbito correcto: el duplicado nace precisamente de que la misma `LineaSigrid`
aparece en dos `Conflicto` con claves distintas. `res.borradas` se incrementa
dentro del mismo `if`, así que el recuento y las sentencias no pueden
divergir.

**Y está bien cubierto**, con controles en los dos sentidos (4 tests):
`..._las_dos_lineas_chocan_con_la_misma` fija la premisa (si dejara de
haber dos choques, el test principal pasaría por el motivo equivocado);
`..._borrado_unico_por_ide` es el caso; `..._dos_lineas_distintas_se_borran_
las_dos` es el control negativo que impide que la dedup degenere en un tope de
uno; `..._sin_confirmar_no_se_borra_nada` cierra el flanco de la confirmación.

### 6.2 · T3 no cambia la conducta (la comprobación que pedía el humano)

- **`tests/test_pipeline_offline.py` NO aparece en el diff.** Verificado con
  `git diff dev..HEAD --stat -- …/test_pipeline_offline.py`: **salida vacía**.
  El fichero está intacto y pasa, incluida la aserción
  `c.clave == "200|202607|5|80001"`. **Criterio de T3 cumplido.**
- **Equivalencia leída línea a línea.** El filtro viejo y `criterio_choque`
  comparan lo mismo: `synckey ∈ mias` → no choca; recurso; `horide`
  normalizado con `int(x or 0)`; y `paride` **solo** si
  `destino == "postventa"` — que es exactamente lo que hace
  `campos_identidad`, devolviendo `CAMPOS_CLAVE` en postventa y
  `CAMPOS_CLAVE` sin `paride` en obra.
- **Una diferencia real, pero inalcanzable.** El filtro viejo comparaba el
  recurso en crudo (`ls.reside == a.recurso_ide`); el nuevo lo normaliza
  (`int(x or 0)` en las dos partes). Diverge solo si un lado es `None` y el
  otro `0`, o si los tipos no casan. **No es alcanzable:** `grupo` solo
  contiene acciones con `accion == "escribir"`, que siempre traen
  `recurso_ide` resuelto (sin recurso se omite, y lo fija
  `test_f002_r6_sin_recurso_resuelto_se_omite`), y `existentes` sale de
  `lineas_del_parte(...)` con `LineaSigrid.reside: int`. En la ruta real el
  `_entero()` es un no-op. Es endurecimiento, no cambio de conducta.
- **R14 se cumple en el sentido que importa.** El implementer pide en su §T3
  que lo mire con lupa, y aguanta: `CAMPOS_CLAVE` es la única declaración, y
  `campos_identidad()` **se deriva de ella** filtrando. La asimetría
  clave-más-fina-que-criterio no es un descuido: es la conducta de hoy, que T3
  tenía prohibido cambiar, y su consecuencia —R13— está arreglada, no tapada.
  `test_f002_r14_cambiar_la_tupla_cambia_la_clave_y_el_criterio` demuestra que
  tocar la tupla mueve las dos cosas a la vez, y
  `..._un_campo_nuevo_sin_lector_falla_en_alto` garantiza que un campo sin
  lector **revienta con `KeyError`** en vez de dejar de compararse en
  silencio, que era justo la avería original. Doy R14 por satisfecho.

### 6.3 · La línea cambiada sin cubrir (`app.py:19`)

**La justificación es aceptable, y la he cerrado yo a mano.**

La línea es el `import` de `clave_conflicto`. `app.py` no lo importa ningún
test porque construye la app de FastAPI, así que la puerta lo cuenta como no
medido, que es la verdad. El otro cambio del fichero (la línea 104,
`{"clave": clave_conflicto(a)}`) no computa como sentencia ejecutable
independiente porque continúa una expresión que empieza en una línea no
tocada — de modo que el hueco real no es el `import`, es **el punto de uso**.

Lo he verificado a mano en lugar de darlo por bueno:

```
$ cd services/dedicacion-transfer && python -c "import interface_adapters.api.app as m; …"
modulo importado OK; clave_conflicto = <function clave_conflicto at 0x…>
clave en el punto de uso: 200|202607|5|80001
```

El módulo importa limpio (el `import` resuelve) y la llamada del punto de uso
produce **la misma clave que asevera `test_pipeline_offline.py`**. No hay
hueco: es una sustitución mecánica de una línea, ya comprobada. Añadir un test
de arranque de FastAPI habría sido infraestructura fuera del alcance de la
Fase 1, y la puerta pasa con holgura (96,8 % contra un umbral de 80 %).

### 6.4 · Los 5 `xfail(strict=True)`

Ninguno enmascara trabajo que se pudiera hacer ya. Los cinco son
exactamente lo que espera a Administración, y `strict=True` garantiza que si
alguno empieza a pasar la suite lo dice en vez de callarse:

| Test | Cuántos | Qué espera | ¿Se podía hacer ya? |
|---|---|---|---|
| `test_f002_r2_los_docstrings_remiten_p4_p5` | 1 | que los docstrings de P4/P5 remitan a `#regla-p4` / `#regla-p5` | **No.** Remitir es *retirar* el enunciado, y los puntos 5 y 6 de `ARCHITECTURE.md` siguen `PENDIENTE`: se remitiría a un ancla sin regla, y el servicio se quedaría sin ninguna descripción mientras se espera. `tasks.md` lo asigna a T12. |
| `test_f002_r3_frases_prohibidas_p4_p5` | 3 | retirar «choca aunque tenga otra partida», «la misma partida en ese parte», «imputando al CAPÍTULO» | **No,** mismo motivo: son los enunciados heredados de P4/P5. T12. |
| `test_f002_r4_procedencia_fechada` | 1 | ≥ 2 líneas `Confirmado por Administración el AAAA-MM-DD · <interlocutor>` | **No.** Administración no ha contestado por escrito. La lectura de Sigrid corrobora D1, pero no *es* la confirmación de Administración. T8/T9. |

Suman 5, que es lo que reporta la suite. Y el propio informe (§3.2) cuenta que
un `xfail` en `XPASS` destapó un fallo del test —una frase prohibida partida
en dos líneas por el rewrap—, que es precisamente para lo que sirve `strict`.

## 7. C4 ter — Rutas sensibles

**N/A y no hay nada que justificar:** el repositorio no declara
`harness/rutas_sensibles.json` (solo existe
`harness/rutas_sensibles.ejemplo.json`). Es el caso mayoritario que
`CHECKPOINTS.md` describe.

## 8. C5 — La sesión se cerró bien

- [ ] **`tasks.md` NO tiene marcadas las tareas hechas.** T1, T2, T3, T4 y T5
      siguen en `- [ ]` en
      `specs/F-002-reglas-postventa-conflicto/tasks.md` (líneas 18, 25, 34,
      44, 55) aunque las cinco están hechas y commiteadas. El protocolo del
      implementer (`.claude/agents/implementer.md:23-24`) manda marcarlas
      `[x]` al completarlas.

      **Los commits, en cambio, están perfectos** — uno por tarea y con el
      formato exigido (8 en total sobre la spec, de `04fbd9b` a `2987fc0`):

      ```
      beba73b F-002 T5: fuente unica de las reglas, la parte que no depende de D1/D2
      20280c7 F-002 T4: R14 (clave y criterio no divergen) y R10/R11/R13 del pipeline
      22328fb F-002 T3: un solo punto de decision para el conflicto
      60d5319 F-002 T2: tests de las reglas no disputadas (R6-R9, R12)
      04fbd9b F-002 T1: fixtures offline parametrizables del transfer
      ```

      Los tres commits `F-002: …` restantes (informe, campaña y el `noqa`
      inútil) usan el formato de ajuste, que también es correcto.

- [x] **Sin ficheros temporales ni artefactos sin trackear sospechosos.**
      `git status` solo muestra `coverage.json`,
      `services/dedicacion-transfer/coverage.json` y
      `services/dedicacion-transfer/.coverage`: ficheros **ya versionados**
      que `init.sh` reescribe en cada ejecución. La decisión de no
      commitearlos es correcta (F-009). No hay nada sin trackear.

- [ ] **`features.json` NO refleja el estado real.** F-002 sigue en
      `"status": "spec_ready"`, que significa «spec lista, sin empezar», con
      cinco tareas implementadas y commiteadas dentro. Lo coherente con lo
      hecho es `in_progress` (el límite de una sola lo permite: hoy hay cero).

### Trazabilidad requisito → test (Fase 1)

Todos verificados por recolección real de la suite, no leyendo la spec.

| Req | Test que lo cubre | Fichero | Estado |
|---|---|---|---|
| R1 | `test_f002_r1_fuente_unica_tiene_ancla_por_regla` (×7), `..._el_ancla_no_esta_repetida` (×7), `..._los_puntos_sin_cerrar_estan_marcados` (×2), `..._los_puntos_cerrados_no_estan_marcados` (×5), `..._el_arbol_es_el_que_creemos` | `test_f002_fuente_unica.py` | pasa |
| R2 | `test_f002_r2_el_readme_remite_a_las_anclas` (×3: p1, p2, p3) | `test_f002_fuente_unica.py` | pasa |
| R2 (P4/P5) | `test_f002_r2_los_docstrings_remiten_p4_p5` | `test_f002_fuente_unica.py` | `xfail(strict)` → T12 |
| R3 | `test_f002_r3_frases_prohibidas_fase1` (×4), `..._la_fuente_si_puede_enunciarla` | `test_f002_fuente_unica.py` | pasa |
| R3 (P4/P5) | `test_f002_r3_frases_prohibidas_p4_p5` (×3) | `test_f002_fuente_unica.py` | `xfail(strict)` → T12 |
| R4 | `test_f002_r4_procedencia_fechada` | `test_f002_fuente_unica.py` | `xfail(strict)` → T8/T9 |
| R5 | `test_f002_r5_sin_literal_de_la_obra_de_postventa` (×3), `..._el_valor_sigue_estando_donde_debe` | `test_f002_fuente_unica.py` | pasa |
| R6 | `test_f002_r6_sin_mensual_se_omite`, `..._con_mensual_se_escribe`, `..._sin_recurso_resuelto_se_omite` | `test_f002_reglas.py` | pasa |
| R7 | `test_f002_r7_fecha_ultimo_dia_mes` (×6 periodos), `..._la_fecha_no_depende_del_dia_de_captura` | `test_f002_reglas.py` | pasa |
| R8 | `test_f002_r8_can_pre_tot`, `..._el_porcentaje_no_viaja_sobre_100`, `..._tot_se_redondea_a_dos_decimales` | `test_f002_reglas.py` | pasa |
| R9 | `test_f002_r9_porcentaje_fuera_de_rango` (×4), `..._los_bordes_validos_se_escriben` | `test_f002_reglas.py` | pasa |
| R10 | `test_f002_r10_idempotencia_synckey`, `..._la_reejecucion_no_inserta_nada`, `..._sin_synckey_previa_si_se_escribe` | `test_f002_pipeline.py` | pasa |
| R11 | `test_f002_r11_modo_pruebas_destino_y_partida`, `..._marca_las_lineas`, `..._sin_modo_pruebas_va_a_la_obra_real` | `test_f002_pipeline.py` | pasa |
| R12 | `test_f002_r12_postventa_desactivada`, `..._postventa_activada_va_a_la_obra_de_postventa`, `..._la_linea_normal_no_se_ve_afectada` | `test_f002_reglas.py` | pasa |
| R13 | `test_f002_r13_borrado_unico_por_ide` + 3 controles | `test_f002_pipeline.py` | pasa |
| R14 | 17 tests `test_f002_r14_*` | `test_f002_conflicto.py` | pasa |
| R15–R19 | — | — | **Fase 2/3, bajo la PARADA. Fuera de alcance.** |

**Mérito que conviene dejar escrito:** cada regla lleva su **control
positivo**. Sin ellos, una implementación que omitiera siempre pasaría todos
los tests de omisión. Es la diferencia entre tests que pasan y tests que
verifican, y aquí está hecho a conciencia (R6, R9, R10, R11, R12, R13 y R3 lo
tienen).

### Coherencia con la evidencia real de Sigrid

Revisado el punto 6 que pedía el humano. **Nada de lo implementado en T5
contradice `progress/sigrid_F-002.md`:**

- **`'postventa-2'` era efectivamente falso.** La C2 devuelve 248 nodos del
  presupuesto de `POSTV2` con HTTP 200 y `truncated: false`: la obra existe
  con ese código. Retirarlo del docstring de `reglas_porcentajes.py:15` es
  correcto, y el test `test_f002_r3_frases_prohibidas_fase1[ruta3-postventa-2]`
  impide que vuelva.
- **Partida hoja:** las 86 líneas de obra tienen `n_hijos = 0`. Lo que T5
  escribió en `ARCHITECTURE.md` punto 5 («imputando a la partida que
  corresponde a la obra original, `0707` → partida `0707 · …`») **va en la
  misma dirección** que la evidencia. Y no cierra la decisión: la marca
  `PENDIENTE · decisión D1/D2 de F-002` sigue puesta, que es lo correcto
  mientras Administración no conteste por escrito.
- **Casado por código exacto:** la C2 confirma que `cod` y `res` son campos
  separados (`cod='0610'`, `res='COLEGIO ALEGRA'`), así que el emparejamiento
  exacto de `resolver_postventa` es el bueno. El docstring que T5 dejó en
  `partida_resolver.py` («la partida cuyo código ES el código de la obra
  original») es coherente con eso.
- **Lo que sigue diciendo «CAPÍTULO»** en el docstring de
  `reglas_porcentajes.py` está **explícitamente marcado como enunciado
  heredado y PENDIENTE**, con puntero a `#regla-p4` / `#regla-p5`; su retirada
  es T12. Correcto: T5 no tenía permiso para decidirlo.
- **`partida_resolver.py:54` sigue sin filtrar `es_hoja`** (la variable `hojas`
  que no son hojas). Es un defecto real, pero su corrección es **T10**, bajo la
  PARADA. El implementer lo escaló al líder en su §7 en vez de arreglarlo por
  su cuenta: es la conducta correcta.

## 9. Cambios requeridos

Concretos y de bookkeeping. **Ninguno toca código de producción ni tests.**

1. **`specs/F-002-reglas-postventa-conflicto/tasks.md`, líneas 18, 25, 34, 44
   y 55** — marcar `- [x]` las tareas **T1, T2, T3, T4 y T5**. Dejar **T6 y
   todo lo que hay bajo la ⛔ PARADA en `- [ ]`**, que es su estado correcto.

2. **`progress/current.md`** — reescribirlo para que describa la sesión
   activa. Como mínimo hay que corregir tres afirmaciones falsas:
   - línea 9: «No se ha tocado ni una línea de código» → Fase 1 (T1–T5)
     implementada, con la referencia a `progress/impl_F-002.md`.
   - línea 109: «Sin commits todavía de esta sesión» → los 7 commits de la
     rama, de `04fbd9b` a `2987fc0`.
   - sección «### 3. Consultas de lectura contra Sigrid — NO ejecutadas»
     (línea 85) → la **C2 ya está ejecutada**; el volcado está en
     `progress/sigrid_F-002.md`. Quedan pendientes C1, C3, C4 y C5.
   Añadir además que el trabajo está **parado en la PARADA de `tasks.md`**
   esperando la respuesta de Administración a D1/D2, y el aviso del
   implementer de que **D2 se ha contestado con la opción (c)**, que invalida
   el diseño y obliga a volver a proponer (`design.md` §7, Riesgo 2).

3. **`progress/current.md`, verificaciones `MANUAL (humano)`** — listar T7,
   T13 y T14 con su **comando exacto** y su estado, como pide `CHECKPOINTS.md`
   C4. Están bien redactadas en `progress/impl_F-002.md` §6: basta traerlas.

4. **`harness/features.json`** — F-002 pasa de `"status": "spec_ready"` a
   `"in_progress"`, que es lo que refleja la realidad (C5). Hoy hay cero
   features `in_progress`, así que no rompe el límite que valida `init.sh`.

Nada más. **Al cerrar estos cuatro puntos, la Fase 1 queda aprobada**: no
tengo ninguna objeción pendiente sobre el código, los tests, la cobertura ni
la campaña de mutación.

## 10. Automejora (propuestas, NO aplicadas)

1. **`CHECKPOINTS.md` / `.claude/agents/reviewer.md` — no existe la review de
   una fase.** C5 asume que se revisa la feature entera («`tasks.md` con
   **todas** las tareas `[x]`»). Esta review es de una fase deliberadamente
   parcial, con una PARADA por diseño, y he tenido que interpretar C5 a mano.
   Propongo añadir a `CHECKPOINTS.md` una nota de cabecera equivalente a la de
   `sdd=false`: *«Review de fase. Si el líder acota la review a un subconjunto
   declarado de `tasks.md`, C5 se evalúa contra ese subconjunto: las tareas de
   la fase revisada en `[x]`, las de fases posteriores en `[ ]` sin que
   cuenten como incumplimiento. El informe de review declara qué fase
   cubre.»* Sin eso, una feature bien partida en fases no puede aprobarse
   nunca.

2. **La campaña de mutación paralela es inalcanzable para el reviewer.**
   `harness/mutacion_paralela.py` aborta si el árbol tiene cambios sin
   commitear, pero `bash harness/init.sh` —que el reviewer está **obligado** a
   ejecutar como paso 1— reescribe tres artefactos de cobertura versionados
   (`coverage.json`, `services/dedicacion-transfer/coverage.json`,
   `.coverage`). El resultado es que el árbol **nunca** está limpio cuando
   toca lanzar la campaña y `--workers 1` es obligatorio de facto, con la
   consiguiente pérdida de tiempo en features grandes. Dos arreglos posibles,
   por orden de preferencia:
   - **cerrar F-009** (dejar de versionar los artefactos de cobertura), que
     mata el problema de raíz; o
   - que la comprobación de árbol limpio de `mutacion_paralela.py` **ignore
     los artefactos que el propio arnés genera**, leyéndolos de una lista
     declarada (los mismos que reescribe `init.sh`).

   Mientras no se arregle, convendría que `.claude/agents/reviewer.md` avisara
   de que `--workers 1` es lo normal en este repositorio, para que ningún
   reviewer lo interprete como una anomalía del implementer. Yo lo he
   interpretado así al principio, siguiendo el aviso de
   `progress/impl_F-002.md` §4.3, y he perdido una ejecución en comprobarlo.

3. **Observación menor, sin acción requerida.** En `registro_pipeline.py`, la
   construcción de `contexto` sigue comparando el recurso en crudo
   (`ls.reside == a.recurso_ide`) mientras el criterio de choque ya lo
   normaliza. No es un defecto alcanzable hoy (mismo razonamiento de §6.2),
   pero es la clase de asimetría que originó esta feature. Vale la pena
   unificarlo cuando T11 vuelva a tocar ese bloque.

---

# 11. Segunda pasada — verificación de las correcciones (`f469de8`)

Commit `f469de8 · F-002: corrige el rastro documental de la Fase 1 (tasks,
current.md, estado)`. Toca **4 ficheros y ni una línea de código**:
`BACKLOG.md`, `harness/features.json`, `progress/current.md` y
`specs/F-002-reglas-postventa-conflicto/tasks.md`. Verificado con
`git show f469de8 --stat`: no aparece ningún `.py` ni nada bajo `services/`.
Eso es exactamente lo que pedía §9 —bookkeeping, no rework— y significa que
**todo lo verificado en la 1ª pasada sigue vigente sin repetirlo**. Aun así he
reejecutado las dos puertas (abajo), porque el `ref_diff` de la campaña va por
nombre de rama y HEAD se ha movido.

## 11.1 · Los cuatro cambios requeridos

| # | Cambio pedido en §9 | Estado |
|---|---|---|
| 1 | `tasks.md`: T1–T5 en `[x]`, el resto en `[ ]` | **hecho** |
| 2 | `progress/current.md`: retirar las tres afirmaciones falsas | **hecho** |
| 3 | `current.md`: `MANUAL (humano)` con comando exacto | **hecho** |
| 4 | `features.json`: F-002 a `in_progress` | **hecho** |

**1 · `tasks.md`.** Comprobado leyendo los 17 checkboxes, no el resumen:

```
18:- [x] **T1**   25:- [x] **T2**   34:- [x] **T3**
44:- [x] **T4**   55:- [x] **T5**
71:- [ ] **T6**  … 187:- [ ] **T17**
```

Las cinco de la Fase 1 marcadas; **T6 y las once de debajo de la ⛔ PARADA
intactas en `[ ]`**, que es su estado correcto. T6 sigue sin marcar aunque
esté por encima de la barrera: es `MANUAL (humano)` y no se ha hecho. Correcto.

**2 · `progress/current.md`.** Reescrito entero (224 líneas cambiadas). Las
tres afirmaciones falsas han desaparecido, y lo he comprobado buscándolas por
patrón, no leyendo por encima:

- «No se ha tocado ni una línea de código» → **ya no está.** Ahora, línea 11:
  «**Sí se ha tocado código.** 8 commits en la rama, de `04fbd9b` a
  `2987fc0`…», con **tabla de T1–T5 y su commit**. Contado con
  `git rev-list --count`: 9 commits sobre la evidencia C2, que son los 8 del
  implementer más el de bookkeeping. **El número es correcto** — de hecho
  corrige un error mío: mi §0 de la 1ª pasada decía «7 commits». Ya está
  arreglado arriba.
- «Sin commits todavía de esta sesión» → **ya no está.**
- «Consultas de lectura contra Sigrid — NO ejecutadas» → **ya no está en esa
  forma.** El único «NO ejecutadas» que queda (línea 47) dice «**C1, C3, C4 y
  C5** · NO ejecutadas», que es **verdad**, y la línea 41 abre con «**C2 ·
  EJECUTADA** el 2026-08-19… Volcado íntegro en `progress/sigrid_F-002.md`»
  con lo que cerró (obra `POSTV2`, **partida hoja**, **código exacto**) y
  hasta el hallazgo de las cuatro partidas duplicadas sin cero inicial.
  Coincide con `progress/sigrid_F-002.md`. **C2 correcto.**

  El fichero va además más allá de lo que pedí, y para bien: registra las dos
  decisiones del humano (D1 cerrada; **D2 contestada con la opción (c)**),
  y una sección «⚠ Lo que bloquea la Fase 2» que dice sin rodeos que
  `design.md` §7 queda invalidado y que **P4 hay que diseñarla de cero**,
  volviendo a la PARADA 1 antes de que nadie toque T11. Eso es exactamente lo
  que `CLAUDE.md` manda hacer cuando el trabajo revela que la propuesta
  aprobada era incompleta.

**3 · Verificaciones `MANUAL (humano)`.** Tabla en `current.md`
§«Verificaciones MANUAL (humano) pendientes» (líneas 71-82) con las cuatro
—T6, T7, T13, T14— y su comando. T14 conserva el aviso que importa: «**Exige
autorización expresa del humano para esa acción concreta**; ningún agente la
lanza». Cierra el hueco de **C4**. Bien traído de `impl_F-002.md` §6, y T7
está actualizado a «ejecutar C1, C3, C4, C5» en vez de C1–C5, coherente con
que la C2 ya está hecha.

**4 · `harness/features.json`.** `F-002 -> in_progress`. Y el propio `init.sh`
lo valida en la corrida de abajo: «en curso: **['F-002']**», exactamente una.
La nota del líder sobre **F-003 en `pending` en esta rama a propósito** es
correcta y no la discuto: su `spec_ready` vive en su rama, y en esta el
fichero no debe afirmar un estado cuya spec no existe aquí.
`BACKLOG.md` se regeneró en el mismo commit y `init.sh` lo da «al día».

## 11.2 · Puertas reejecutadas sobre el nuevo HEAD

`bash harness/init.sh`, ejecutado **por mí**, tal cual, sin pipes ni `tail`:

```
    10 features, 9 abiertas, en curso: ['F-002'], bloqueadas: ninguna
[OK] features.json válido
[OK] BACKLOG.md al día
[OK] compileall: sin errores de sintaxis
[OK] servicio transfer (services/dedicacion-transfer): pytest en verde
     90 passed, 5 xfailed, 1 warning in 2.80s
[OK] PUERTA COBERTURA: 96.8% de 31 líneas cambiadas cubiertas (30/31, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-002-reglas-postventa-conflicto
ENTORNO LISTO. Puedes trabajar.
EXIT=0
```

La suite del transfer **no salió de caché**: se ejecutó de verdad (2,80 s).
La del servicio `api` **sí salió de caché**, así que la he vuelto a ejecutar a
mano: `21 passed in 0.12s`. (Y el commit no toca nada bajo
`services/dedicacion-api`, así que la caché era legítima.)

**Campaña de mutación reejecutada sobre `f469de8`**, por si el movimiento de
HEAD alteraba el alcance:

```
$ python -m harness.mutacion --feature F-002 --workers 1 --salida <scratchpad>/mut_review2.md
9 mutantes evaluados, 9 muertos, 0 supervivientes, 0 timeouts en 13.4 s
```

Mismos totales que el informe y que mi primera reejecución. **Cero
supervivientes**, que es lo que exige `critico`. Cobertura, idéntica: 96,8 %
(30/31).

## 11.3 · La campaña paralela: dato definitivo para §10.2

El líder señala que los ficheros sin versionar de F-003 ya no están y me
invita a reintentarla. **Lo he hecho, y vuelve a abortar** — lo que confirma
mi diagnóstico y descarta del todo la explicación de F-003:

```
$ git status --porcelain
 M .coverage
 M coverage.json
 M services/dedicacion-transfer/.coverage
 M services/dedicacion-transfer/coverage.json
$ python -m harness.mutacion --feature F-002 --salida <scratchpad>/mut_paralela2.md
El árbol principal tiene cambios sin commitear y la campaña paralela crea sus
worktrees desde HEAD: … Commitea los cambios o lanza la campaña con --workers 1.
```

Sin un solo fichero de F-003 en el árbol, el bloqueo persiste, y ahora son
**cuatro** artefactos en vez de tres: la última corrida de `init.sh` ha
sumado el `.coverage` de la raíz. Queda probado que la causa es
**exclusivamente** que `init.sh` reescribe artefactos de cobertura
versionados (**F-009**), y que como el reviewer está obligado a ejecutar
`init.sh` como paso 1, **la campaña paralela es inalcanzable para cualquier
reviewer de este repositorio**. La propuesta de §10.2 se mantiene y sube de
prioridad: el síntoma empeora solo, sumando ficheros.

## 11.4 · Sobre quién debía actualizar el rastro

Acepto la explicación del líder y **no la cuento contra el implementer**. Está
escrita en `current.md` §«Nota de proceso» y la he verificado contra los
protocolos: `.claude/agents/leader.md:48` y `:82` sí ponen `features.json` y
`progress/current.md` del lado del líder («Deja siempre `progress/current.md`
reflejando el estado real»). Con el implementer trabajando en el mismo árbol
que el subagente de la spec de F-003, prohibirle tocarlos fue una decisión
razonable de coordinación, no un descuido.

Dicho eso, **el reparto está mal escrito en el arnés y conviene arreglarlo**,
porque es lo que produjo el agujero: `.claude/agents/implementer.md:28` le
manda al implementer *«Mantén `progress/current.md` actualizado»*, y
`leader.md:82` se lo manda al líder. Dos dueños para un fichero es cómo se
queda sin dueño. Va como propuesta 4 de §12.

Lo que **sí** era inequívocamente del implementer es marcar `[x]` en
`tasks.md` (`implementer.md:23-24`, «Marca cada una `[x]` al completarla»), y
eso quedó sin hacer. Es el único punto de los cuatro que no cubre la
explicación del líder. No bloquea nada: está corregido y es una anotación para
la próxima, no un reproche.

## 11.5 · Checkboxes que quedaban abiertos

| Checkpoint | 1ª pasada | 2ª pasada | Por qué |
|---|---|---|---|
| **C2** · `current.md` describe solo la sesión activa | `[ ]` | **`[x]`** | Reescrito; las tres afirmaciones falsas verificadas como ausentes |
| **C4** · `MANUAL (humano)` en `current.md` con su comando | `[ ]` | **`[x]`** | T6, T7, T13 y T14 listadas con comando y con el aviso de autorización de T14 |
| **C5** · `tasks.md` con las tareas hechas en `[x]` | `[ ]` | **`[x]`** | T1–T5 en `[x]`, T6–T17 en `[ ]` |
| **C5** · `features.json` refleja el estado real | `[ ]` | **`[x]`** | `in_progress`, y `init.sh` confirma «en curso: ['F-002']» |

**C1, C3, C4 bis y C5 (artefactos)** ya estaban en `[x]` en la 1ª pasada y no
los ha alterado un commit que no toca código. **C3 bis** y **C4 ter** siguen
N/A con el motivo escrito en §4 y §7.

**No queda ningún checkbox vacío en C1–C5.**

---

# 12. Veredicto final

## **APPROVED** — Fase 1 (T1–T5) de F-002.

Lo que se aprueba, y con qué evidencia propia:

- **T3 no cambia la conducta.** `tests/test_pipeline_offline.py` **no aparece
  en el diff** y pasa intacto, con su aserción
  `c.clave == "200|202607|5|80001"`. La única diferencia real entre el filtro
  viejo y `criterio_choque` —normalizar el recurso— es inalcanzable en la ruta
  de ejecución (§6.2).
- **R13 era un defecto real.** Reproducido por mí en copia aislada:
  `AssertionError: [5001, 5001]`, dos `DELETE` del mismo `hmores.ide` contra
  código de producción. El arreglo dedupica en el ámbito correcto y lleva
  cuatro tests con controles en los dos sentidos (§6.1).
- **Las dos puertas miden de verdad, por primera vez en el repositorio.**
  Cobertura recalculada a mano: **30/31**, y la única línea sin cubrir es
  `app.py:19`, cuyo hueco he cerrado ejecutando el punto de uso yo mismo
  (§6.3). Mutación: alcance, nº de mutantes y los nueve operadores
  recalculados uno a uno, y **campaña reejecutada dos veces** (9/9 muertos,
  0 supervivientes, 0 timeouts).
- **Los 5 `xfail(strict=True)` no tapan nada** que se pudiera hacer ya (§6.4).
- **Nada contradice la evidencia de Sigrid**, y el `'postventa-2'` retirado
  era efectivamente falso (§8).
- **El rastro documental ya es fiel** (§11).

**Trabajo de calidad alta**, y no solo porque pase: los controles positivos de
cada regla, el `KeyError` deliberado para que un campo sin lector reviente en
alto en vez de callarse, y el haber **encontrado y arreglado un defecto real**
en vez de limitarse a documentar la contradicción, son lo que separa unos
tests que pasan de unos tests que verifican.

## Antes de tocar la Fase 2 — para el líder, no para el reviewer

No condiciona esta aprobación, pero no debe perderse:

**D2 se ha contestado con la opción (c)**, que `requirements.md` §2 ya
anticipaba como la respuesta que invalida el diseño: no es ninguna de las dos
versiones enfrentadas, es una regla nueva (validar que la suma del mes no pase
de 1) que hoy no existe en el transfer y que podría corresponder a la API, que
es quien ve el cuadrante completo del trabajador. `design.md` §7 (Riesgo 2)
manda **parar y volver a proponer**. Correctamente, el implementer **no la
anticipó**: T3 replica la conducta de hoy, como mandaba la spec.

Por tanto **T11 no se abre** hasta que el humano apruebe un diseño nuevo de
P4 en la PARADA 1. `OBRA_PRUEBAS_FORZAR` sigue a `true` y así debe seguir.

## Propuestas de automejora (NO aplicadas)

Las tres de §10 siguen vivas — la 2 (campaña paralela) **reforzada** por
§11.3 — y añado una cuarta:

4. **`progress/current.md` tiene dos dueños en el arnés.**
   `.claude/agents/implementer.md:28` manda al implementer mantenerlo, y
   `.claude/agents/leader.md:82` manda lo mismo al líder. Esta feature enseña
   cómo acaba eso: cada uno supone que lo lleva el otro y el fichero se queda
   mintiendo. Propongo fijar la propiedad en un solo rol —el **líder**, que es
   quien ya posee `features.json` y quien lo lee al arrancar sesión— y cambiar
   `implementer.md:28` por *«Registra tu avance en `progress/impl_F-XXX.md`;
   `progress/current.md` y `harness/features.json` son del líder y no los
   tocas»*. `tasks.md` se queda donde está, con el implementer. Si se acepta,
   **hay que portarlo a `arnes-base`**: el conflicto es del arnés genérico, no
   de este repositorio (regla de propagación de `CLAUDE.md`).
