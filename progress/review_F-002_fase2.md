<!-- progress/review_F-002_fase2.md -->
# F-002 · Review de la Fase 2 (T7–T12, T15–T17)

> Rama `feature/F-002-reglas-postventa-conflicto` · HEAD `eaf77a0`.
> Alcance: **solo la Fase 2**. La Fase 1 (T1–T5) está aprobada en
> `progress/review_F-002_fase1.md` y no se revuelve; se comprueba únicamente
> que la Fase 2 no la ha roto (no la ha roto: §4.3 y §6).
> T6 (humano), T13 y T14 (MANUAL contra Sigrid real) **no cuentan como
> trabajo faltante**; se verifica que están listadas con su comando.

## Veredicto

**APPROVED**

Es el trabajo mejor verificado que ha pasado por esta review. Las tres
afirmaciones centrales del implementer —el superviviente es equivalente, las
guardas retiradas eran inalcanzables y la Fase 2 no toca `dedicacion-api` ni
`dedicacion-front`— **se han comprobado ejecutándolas, no leyéndolas**, y las
tres se sostienen. Quedan cinco observaciones no bloqueantes (§9) y tres
acciones de rastro que son del líder (§10).

## Nivel de rigor

`harness/features.json` declara **`rigor: "critico"`** para F-002. Exige:
C1–C5, tests trazables, **fase RED**, **cobertura ≥ 80 %** de las líneas
cambiadas, **campaña de mutación** con **cero supervivientes o justificación
escrita**, y las verificaciones `MANUAL (humano)` listadas con su comando.
Todas se han evaluado contra ese nivel; ninguna se ha rebajado.

---

## 1. Portero (`bash harness/init.sh`)

Ejecutado tal cual por el reviewer. **Exit code 0 · ENTORNO LISTO.**

```
[OK] features.json válido        11 features, 10 abiertas, en curso: ['F-002']
[AVISO] ruff: 180 avisos (deuda previa, no bloquea)
[OK] pytest en verde (con medición de cobertura)          11 passed (raíz)
[OK] servicio api (services/dedicacion-api): pytest       21 passed
[AVISO] servicio front: sin directorio de tests
[OK] servicio transfer: pytest en verde                  187 passed, 1 warning
[OK] PUERTA COBERTURA: 99.1% de 108 líneas cambiadas cubiertas
     (107/108, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-002-reglas-postventa-conflicto
```

**Ninguna línea de servicio vino de caché**: las tres suites imprimieron sus
puntos de progreso en esta ejecución (11, 21 y 187 tests). No ha hecho falta
relanzar ninguna a mano.

El único aviso de pytest (`test_preflight` devuelve el `Preflight` en vez de
aserciones) es heredado de antes de F-002, está declarado en el informe del
implementer §8 y no se ha tocado. Correcto: mezclarlo aquí habría ensuciado
el diff.

---

## 2. C4 bis · verificación independiente de la mutación

El informe `progress/mutacion_F-002.md` declara **«Tiempo total 35,3 s»**,
por debajo de los 5 minutos, así que **la campaña se ha reejecutado entera**,
como manda CHECKPOINTS C4 bis:

```
python -m harness.mutacion --feature F-002 --workers 1 \
  --salida <scratchpad>/mutacion_F-002_review.md
```

La salida fue **fuera de `progress/`** (scratchpad de sesión), así que el
informe del implementer no se ha pisado. `git status` antes y después es
idéntico: los cinco artefactos de cobertura modificados (`.coverage`,
`coverage.json` ×3) ya estaban sucios al empezar y son el problema conocido
de **F-009**; la campaña no ha añadido ni un fichero.

| Métrica | Informe del implementer | Reejecución del reviewer | ¿Coincide? |
|---|---|---|---|
| Alcance (ficheros) | 5 | 5, los mismos | sí |
| Alcance (líneas) | 439 | 439 | sí |
| Mutantes generados | 34 | 34 | sí |
| Evaluados | 34 | 34 | sí |
| Muertos | 33 | 33 | sí |
| Supervivientes | 1 | 1 | sí |
| Timeouts | 0 | 0 | sí |
| Tiempo | 35,3 s | 37,8 s | — |

El superviviente es **el mismo, con el mismo operador y el mismo texto**:

```
[33/34] superviviente reglas_porcentajes.py:233 [comparacion]
        sobrecarga=exceso > EPSILON_CAPACIDAD  ->  >=
```

No hay campaña de cero mutantes, así que no procede la prueba de control de
la exclusión de alcance.

### 2.1 · El superviviente, verificado a mano (no leído)

El argumento del implementer se ha **ejecutado**, no aceptado:

```
EPS exacto (Fraction)      : 7378697629483821 / 147573952589676412928
EPS / 2^-52                : 7378697629483821/32768   -> NO es entero
(1.0 + EPS) - 1.0          : 5.0000000000105516e-05   != 0.00005
vecinos double de 1+EPS    : 4.999999999988347e-05 / 5.0000000000105516e-05
                             / 5.000000000032756e-05  -> ninguno == EPS
barrido de 200.000 total∈[1,2): ningún caso con (total - 1.0) == EPS
```

El razonamiento es **correcto y completo**:

- para `total ∈ [1, 2)` la resta `total - 1.0` es exacta (Sterbenz), luego el
  `exceso` solo puede ser múltiplo de `2⁻⁵²`;
- `EPSILON_CAPACIDAD` **no** es múltiplo de `2⁻⁵²` (el cociente sale
  `…/32768`, no entero), así que ningún `exceso` de esa franja puede
  igualarlo;
- para `total ≥ 2` el `exceso` es ≥ 1, y `>` y `>=` responden lo mismo;
- para `total < 1` el exceso es negativo.

**Mutante EQUIVALENTE: justificación aceptada.** El requisito de `critico`
(«cero supervivientes salvo justificación escrita aceptada») queda cumplido
por esta vía, y queda constancia aquí de que el reviewer lo verificó por su
cuenta.

La conducta del borde sí está probada por los dos lados
(`test_f002_r26_la_tolerancia_decide_el_borde[…]`: media épsilon no avisa, el
doble sí) y por el control positivo `test_f002_r26_justo_uno_no_es_sobrecarga`.

**Pero el test que «lo demuestra» demuestra menos de lo que dice** (§9.1).

---

## 3. Checkpoints

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina con exit code 0.
- [x] Existen los siete ficheros obligatorios.

### C2 — El estado es coherente

- [x] Una sola feature `in_progress` (`F-002`); lo valida `init.sh`.
- [x] Rama actual `feature/F-002-reglas-postventa-conflicto`.
- [x] `progress/current.md` describe la sesión activa de F-002 (sin restos de
      sesiones anteriores) — **con la salvedad de §10.1**: su tabla de tareas
      y su bloque «Verificado con salida real» siguen contando la Fase 1
      (90 tests, 5 xfailed, 96,8 %, 9 mutantes). Es rastro del líder, no del
      implementer, y hay que refrescarlo antes de cerrar.
- [x] `F-001` (única `done`) tiene su resumen en `progress/history.md`.

### C3 — El código respeta arquitectura y convenciones

- [x] **Hexagonal.** `domain/models/registro_models.py` no importa nada de
      `application` ni de `infrastructure`; `reglas_porcentajes.py` importa
      solo modelos de dominio; el pipeline recibe cliente y settings
      inyectados. Ningún adaptador fuera de `infrastructure/`.
- [x] **Primera línea con la ruta** en los 13 ficheros `.py` del diff
      (comprobado uno a uno).
- [x] Sin `print()`, sin TODOs sin contexto, sin secretos, sin dependencias
      nuevas. El único `POSTV2` del servicio sigue en
      `config/settings.py:38` como defecto del ajuste, que es exactamente
      donde R5 lo permite.
- [x] **Las tres trampas del proyecto:**
  - *Escala del porcentaje.* No hay conversión nueva. La Regla B trabaja
    entera en escala 0–1 y su tolerancia es `0.005 / 100`, la conversión
    correcta de la épsilon del cuadrante; hay test que lee el fichero de la
    API y falla si allí cambia (`test_f002_r26_la_tolerancia_es_la_del_cuadrante`).
  - *Postventa no se escribe en su obra.* Sin cambios de destino; lo que
    cambia es que el `paride` ahora solo puede ser **hoja activa**, que es
    más restrictivo, no menos.
  - *Solo escribe el transfer.* Ninguna escritura nueva, ningún `.env`
    tocado, `OBRA_PRUEBAS_FORZAR` intacto, `MAX(ide)+1` sin tocar. La
    novedad de T12 va en la dirección segura: **se borra menos**, nunca más.

### C3 bis — Documentos que entran de fuera

**N/A justificado:** el diff no añade ni modifica ningún fichero de
`docs/referencia/` (comprobado con `git diff dev..HEAD --name-only`). No hay
originales PDF ni ofimáticos en el árbol ni en el historial de la rama.

### C4 — La verificación es real

- [x] **Los 33 requisitos R1–R33 tienen ≥ 1 test trazable y todos pasan.**
      Recolectado de la propia suite, no del informe (tabla en §5).
      187 tests, 0 fallos, **0 `xfail`**.
- [x] Los unit tests no tocan red ni BBDD: todo va por `ClienteFalso` y
      `SettingsFalso` de `tests/conftest.py`. No hay un solo import de
      `requests`, `httpx`, `psycopg`, `socket` ni `sqlalchemy` en `tests/`.
- [x] Las verificaciones `MANUAL (humano)` están en `progress/current.md`
      (T6.1, T6.2, T6 opcional C3/C5, T13 y T14) **con su comando exacto** y
      con el aviso de que T14 exige autorización expresa para esa acción
      concreta. También están en `tasks.md` §Fase 3 y en el informe §7.

### C4 bis — El rigor declarado se cumple

- [x] `rigor: "critico"` declarado en `harness/features.json`.
- [x] **Fase RED.** El informe trae **seis trazas reales** (§3.1–3.6), todas
      contra el árbol y no simuladas, y cada una es la RED del requisito
      central de su tarea. Las dos que valen doble:
      `assert True is False` en `criterio_choque` (T10: la línea previa con
      otra partida se daba por la misma y **se borraba**) y
      `AssertionError: [5001] == []` en R32 (T12: **se borraba el apunte de
      Administración sin escribir el sustituto**). Son averías reales
      enseñadas fallando, no ceremonia.
- [x] **Cobertura.** `PUERTA COBERTURA [OK] 99,1 % (107/108)`, umbral 80 %.
      La única línea sin cubrir es el `import` de `clave_conflicto` en
      `interface_adapters/api/app.py`, heredada de la Fase 1 y explicada en
      el informe §6.1. **Ninguna línea de producción de la Fase 2 queda sin
      cubrir.**
- [x] **Mutación.** `progress/mutacion_F-002.md` existe, lo generó la
      herramienta y sus totales se han **verificado reejecutando la campaña
      completa** (§2), no solo recalculando alcance y número de mutantes.
- [x] **Los muertos están comprobados**, no contados: campaña reejecutada
      (35,3 s declarados < 5 min), 33/33 muertos coincidentes.
- [x] El único superviviente tiene su análisis **completado** (nada en
      `PENDIENTE`) y es equivalente, verificado a mano (§2.1).
- [x] El informe trae la sección **«Evidencias»** (§6) con los cuatro
      números: 187 tests, 99,1 %, 34/1 mutantes, 0,52 s de suite.
- [x] Ningún punto marcado N/A sin justificación escrita.

### C4 ter — Rutas sensibles

**N/A justificado:** el repositorio no declara `harness/rutas_sensibles.json`
(solo existe `rutas_sensibles.ejemplo.json`). Sin declaración, este bloque es
el caso mayoritario y no hay nada que exigir.

### C5 — La sesión se cerró bien

- [x] `tasks.md`: **T7–T12 y T15–T17 marcadas `[x]`**, cada una con su commit
      `F-002 Tn: …` (`d0f03d9`, `25b4cc1`, `eb3e80e`, `05ceef7`, `01468b6`,
      `a8313f1`, `caed865`, `eaf77a0`), más dos de aseo (`0b5c921`, `cf26362`).
- [x] **T6, T13 y T14 siguen `[ ]`: N/A justificado y correcto.** T6 es del
      humano (aviso a Administración y firma de la procedencia); T13 y T14
      son verificación MANUAL contra Sigrid real y T14 exige además
      autorización expresa para esa acción concreta (`CLAUDE.md`, reglas
      duras). Las tres están listadas con su comando exacto en `tasks.md`
      §Fase 3, en `progress/current.md` y en el informe §7. **Que un agente
      las hubiera ejecutado sería el defecto, no dejarlas pendientes.**
- [x] Sin ficheros temporales ni artefactos sin trackear. Los cinco
      artefactos de cobertura **trackeados** que quedan modificados son el
      problema conocido de F-009 y ya estaban así antes de esta review.
- [x] `features.json` refleja el estado real: `F-002` sigue `in_progress`,
      que es lo correcto mientras la Fase 3 manual esté pendiente.

---

## 4. Los puntos que el líder pidió mirar con lupa

### 4.1 · El superviviente que queda

Verificado ejecutando el razonamiento (§2.1). **Equivalente de verdad.**
El test que lo documenta es más flojo de lo que anuncia: §9.1.

### 4.2 · Las soluciones a los 8 supervivientes de la primera pasada

Se ha comprobado que son **honestas**, no cosméticas:

| # | Superviviente | Solución declarada | Comprobación del reviewer |
|---|---|---|---|
| 1 | `and es_linea_mensual(ls)` → `or` | test nuevo | **Real.** `test_f002_r13_el_contexto_es_solo_del_mismo_recurso` (negativo, `contexto == []`) y `..._si_recoge_otro_codigo_del_mismo_recurso` (positivo, `[5002]`). Con `or` el aviso acusaría al empleado equivocado. |
| 2, 3 | `int(a.recurso_ide or 0)` ×2 | quitar la guarda | **Segura.** `grupo` sale de `pendientes = [a for a in acciones if a.accion == "escribir"]`, y `ReglasPorcentajes.decidir` (línea 297-298) devuelve `omitir(MOTIVO_SIN_RECURSO)` **antes** de poder producir un `escribir` si `linea.recurso_ide` es falsy. El `recurso_ide` de la acción se copia de esa misma línea. **Garantizado por quien lo construye, no por casualidad.** |
| 4 | `int(ls.reside or 0)` | quitar la guarda | **Segura.** `existentes` viene de `SigridWriteClient.lineas_del_parte`, que construye cada `LineaSigrid` con `reside=int(f["reside"] or 0)` (línea 236) **y** filtra en SQL por `hmores.reside IN (…)`. `reside` es siempre `int`; `int(ls.reside)` no puede reventar. |
| 5, 6, 7 | `round(cap.…, 4)` → `round(…, 5)` | tests nuevos del 4.º decimal | **Real.** `test_f002_r25_las_cifras_se_redondean_a_cuatro_decimales` usa un `can` previo de seis decimales (0,123456) y clava `0.1235 / 1.0235 / 0.0235`. Con `round(…,5)` falla. |
| 8 | `exceso > EPSILON` → `>=` | equivalente | Verificado en §2.1. |

Quitar dos guardas defensivas en vez de justificar sus mutantes es la
decisión correcta y, además, la más difícil: deja el código más pequeño y
elimina una rama que nadie podía mantener. El comentario que la sustituye
(«sin `or 0` a propósito…», `registro_pipeline.py:313-316`) explica el
porqué en el sitio donde se leerá.

### 4.3 · Regla A y Regla B contra la spec v2

| Exigencia de la spec v2 | Implementación | ¿Cumple? |
|---|---|---|
| Identidad con `paride` **siempre** (R20) | `campos_identidad()` devuelve `CAMPOS_CLAVE = ("recurso","periodo","hora","paride")` sin parámetro `destino`; `criterio_choque` los recorre | sí |
| Otra partida no es conflicto ni se borra (R21) | el criterio falla en `paride` → no hay choque; test de control sobre el pipeline | sí |
| Tolerancia **0,00005** equivalente exacto del `_EPSILON = Decimal("0.005")` de `dedicacion-api/domain/estados.py` | `EPSILON_CAPACIDAD = 0.00005` con `assert EPSILON_CAPACIDAD == 0.005 / 100` y test que **lee el fichero de la API** y falla si cambia | sí |
| Al pasarse **avisa y espera confirmación**; no bloquea a ciegas ni escribe a ciegas | `ejecutar`: sin confirmar → `bloqueadas` + `omitidas` con motivo (R28); confirmada → escribe y `borradas == 0` (R29) | sí |
| Viaja **como un `Conflicto` más**, con motivo propio | campo `motivo: str = "pisado"` \| `"sobrecarga"`, clave con prefijo propio `sobrecarga:`, cuatro campos numéricos **todos con defecto** (R33) | sí |
| Sobrecarga **nunca** borra | `lineas=[]` por construcción, no por comprobación | sí |
| Los dos conflictos a la vez, pisado primero (R30) | el paso 7 bis va después del 7 dentro del mismo bucle de parte | sí |

### 4.4 · F-002 no toca `dedicacion-api` ni `dedicacion-front`

**Confirmado en el diff.** `git diff dev..HEAD --name-only | grep -E
"dedicacion-(api|front)"` no devuelve **nada**. Los 29 ficheros del diff son:
`docs/ARCHITECTURE.md`, el README y 11 ficheros de `dedicacion-transfer`, la
spec, `progress/`, `BACKLOG.md`, `harness/features.json` y `coverage.json`.
Era la razón de reutilizar el `Conflicto` y se ha respetado.

El único punto de contacto es de **lectura**: un test del transfer abre
`services/dedicacion-api/domain/estados.py` como texto para comprobar que la
épsilon no se ha separado. No importa código de la API, no duplica lógica y
es la única forma de que las dos tolerancias no diverjan en silencio. Se
acepta; el matiz está en §9.4.

### 4.5 · La guarda de T12 «que evita perder datos»

**Qué pérdida evita**, con nombres: el humano confirma un pisado (la línea
5001 de Administración se va a sustituir) y **no** confirma la sobrecarga del
mismo trabajador. Antes de la guarda, el borrado se emitía *por conflicto
confirmado* mientras la escritura se bloqueaba *por registro*: se borraba la
5001 y **no se escribía su sustituta**. Pérdida neta de un apunte, y
silenciosa. La RED del informe §3.6 lo enseña fallando (`[5001] == []`).

La guarda es `registro_pipeline.py:468` —`if not (set(c.registros) &
escribibles): continue`— y **está cubierta por tres tests**:

- `test_f002_r32_premisa_hay_pisado_y_sobrecarga_del_mismo_recurso` (premisa:
  si dejara de haber los dos conflictos, el de abajo pasaría por el motivo
  equivocado);
- `test_f002_r32_no_se_borra_si_no_se_escribe` (no borra, **y** lo que no
  estaba bloqueado sí se escribe: la guarda es por conflicto, no un «ante la
  duda, no hagas nada»);
- `test_f002_r32_confirmando_las_dos_si_se_borra` (control positivo: no es
  «no borres nunca», es «no borres sin escribir»).

El segundo trabajador que el implementer añadió al `conftest` no es adorno:
sin él el pipeline salía por el atajo `if not a_escribir: return` y el test
habría pasado por la razón equivocada. Está bien visto y bien explicado.

### 4.6 · El arreglo de D1 en `resolver_postventa`

`hojas = [n for n in nodos.values() if n.activa]` → `candidatos =
partidas_hoja(nodos)`. Verificado contra `partida_catalog.partidas_hoja`:
filtra `es_hoja`, filtra `activa` (`solo_activas=True` por defecto) y
**ordena por `cod`**. Es literalmente el mismo universo que el preflight
publica en `partidas_postventa` (`_cat()`: `n.es_hoja and n.activa`), con lo
que R16, R17 y R19 se cierran de un solo cambio.

**Coherente con la evidencia real** de `progress/sigrid_F-002.md`: el
presupuesto de la obra de postventa tiene 23 capítulos, y entre ellos hay
códigos numéricos (`3`, `4`, …, `11`) que la cascada «empieza por» podía
devolver. Que hoy no se materialice no lo hacía menos real. Los cuatro
duplicados sin cero inicial (`656`/`0656`…) no rompen nada porque
`normalize_code` no quita ceros a la izquierda, y eso lo fija R18 con test
propio.

### 4.7 · Los cinco `xfail(strict=True)` de la Fase 1

**Retirados los cinco, y no queda ni uno vivo.** Comprobado por dos vías: la
suite imprime `187 passed` sin la columna `xfailed` (la Fase 1 cerraba con
`90 passed, 5 xfailed`), y `grep -rn xfail services/dedicacion-transfer/tests`
solo encuentra una mención en un comentario de cabecera que dice justamente
que ya no queda ninguno. Concuerda con el informe.

### 4.8 · El lint sube de 174 a 180

**Juicio: aceptable.** No bloquea, y estas son las razones, medidas:

1. **Los seis avisos nuevos están todos en ficheros de test.** Se ha
   comparado el lint de los **cinco ficheros de producción** entre `dev` y
   `HEAD` extrayéndolos con `git show` a un directorio aparte y pasando
   `ruff --isolated` con el mismo conjunto de reglas: **83 avisos en `dev`,
   82 en `HEAD`**. El código de producción de esta feature no empeora: mejora
   en uno.
2. **Son el patrón que ya usaba el servicio, no deuda nueva de estilo.**
   `I001` viene del bloque `from tests.conftest import …` colocado tras los
   imports de la aplicación, que ya tenían los cuatro ficheros de test de la
   Fase 1 **y** el `test_pipeline_offline.py` anterior a F-002; `C408` es el
   `dict(...)` del ayudante `accion()`, copiado del que ya existía; los
   `B009` son `getattr(pf, "…")` sobre atributos que el preflight adjunta con
   `setattr` —acceder a ellos por punto sería peor, no mejor, porque el
   atributo no existe en la clase—.
3. El implementer **sí limpió** lo que era deuda evitable (`RUF059`,
   `RUF015`) en su commit `0b5c921`, y lo declara sin maquillarlo.

La norma de F-001/F-003 («los ficheros nuevos salen limpios») se cumple
**donde importa** —producción— y se incumple en tests por consistencia con
los cinco ficheros de test que ya estaban. Aun así, el `I001` de los dos
ficheros nuevos es un `ruff check --fix` de un segundo: recomendación §9.2.

### 4.9 · La procedencia (R4)

**Correcto y deliberado; no se marca como defecto**, tal y como el líder
instruyó y por el motivo que lo justifica: no consta ninguna conversación con
Administración, y escribir «Confirmado por Administración» para poner un test
en verde habría sido **fabricar una procedencia**, que es exactamente lo
contrario de lo que R4 persigue.

Verificado:

- La línea está **donde R4 la exige**: en los tres bloques de regla que F-002
  decide — `#regla-p5` (punto 5), `#regla-p4`/`#regla-conflicto` (punto 6) y
  `#regla-capacidad` (punto 7) —, con el texto
  `Confirmado por Pablo Gris (responsable del proyecto) el 2026-08-19 · …`.
- El punto 5 **referencia además el volcado** `progress/sigrid_F-002.md`,
  como R4 pide, y resume la lectura que lo respalda.
- El test es **más fuerte** que el original: comprueba **bloque a bloque**
  (`_bloque(ancla)`), no contando apariciones en el documento entero, con lo
  que dos procedencias en la misma regla ya no pueden hacer pasar por
  confirmada a la de al lado; y `test_f002_r4_la_procedencia_no_es_anonima`
  controla que «Confirmado el 2026-08-19» a secas **no** vale.
- **Barrido de atribuciones falsas: limpio.** Se ha recorrido todo el
  repositorio buscando `Administración` en `docs/`, `services/` y `specs/`.
  Ningún fichero de código ni de documentación atribuye a Administración una
  confirmación que no consta. El viejo `"""Definidas por Administración
  (hilo de porcentajes, 25/07/2026)"""` del docstring de
  `reglas_porcentajes.py` **desapareció** en T8, que es justo lo que había
  que hacer. Las menciones que quedan son de tres tipos legítimos: el aviso
  que hay que trasladarle (T6), las «líneas que metió Administración a mano»
  en el parte (descripción de un hecho del dominio, correcta) y el texto
  prescriptivo de la propia spec (§9.3).

---

## 5. Cobertura requisito → test

Recolectado de la suite (`pytest --collect-only`), no del informe. Todos los
ficheros son de `services/dedicacion-transfer/tests/`. **187 passed, 0 xfail.**

| Req | Tests | Fichero |
|---|---|---|
| R1 | 28 | `test_f002_fuente_unica.py` |
| R2 | 9 | `test_f002_fuente_unica.py` |
| R3 | 14 | `test_f002_fuente_unica.py` |
| R4 | 4 | `test_f002_fuente_unica.py` |
| R5 | 4 | `test_f002_fuente_unica.py` |
| R6 | 3 | `test_f002_reglas.py` |
| R7 | 7 | `test_f002_reglas.py` |
| R8 | 3 | `test_f002_reglas.py` |
| R9 | 9 | `test_f002_reglas.py` |
| R10 | 3 | `test_f002_pipeline.py` |
| R11 | 3 | `test_f002_pipeline.py` |
| R12 | 3 | `test_f002_reglas.py` |
| R13 | 5 | `test_f002_pipeline.py` |
| R14 | 12 | `test_f002_conflicto.py` |
| R15 | 3 | `test_f002_postventa.py` |
| R16 | 9 | `test_f002_postventa.py` |
| R17 | 3 | `test_f002_postventa.py` |
| R18 | 6 | `test_f002_postventa.py` |
| R19 | 2 | `test_f002_postventa.py` |
| R20 | 4 | `test_f002_conflicto.py` |
| R21 | 4 | `test_f002_conflicto.py`, `test_f002_pipeline.py` |
| R22 | 3 | `test_f002_conflicto.py` |
| R23 | 6 | `test_f002_capacidad.py` |
| R24 | 9 | `test_f002_capacidad.py` |
| R25 | 4 | `test_f002_capacidad.py` |
| R26 | 6 | `test_f002_capacidad.py` |
| R27 | 4 | `test_f002_capacidad.py` |
| R28 | 3 | `test_f002_pipeline.py` |
| R29 | 1 | `test_f002_pipeline.py` |
| R30 | 2 | `test_f002_capacidad.py` |
| R31 | 2 | `test_f002_capacidad.py` |
| R32 | 3 | `test_f002_pipeline.py` |
| R33 | 2 | `test_f002_capacidad.py` |
| Sigrid real | MANUAL (humano) | T13, T14 · `tasks.md` §Fase 3 |

**Ningún requisito sin test. Ningún hueco.**

Calidad, no solo cantidad: los tests traen **premisas** y **controles
positivos** (`test_f002_r32_premisa_…`, `..._confirmando_las_dos_si_se_borra`,
`test_f002_r28_un_pisado_sin_confirmar_no_va_a_omitidas`). Es la diferencia
entre un test que pasa y un test que prueba, y aquí está hecha.

---

## 6. Que la Fase 2 no ha roto la Fase 1

- `test_pipeline_offline.py`, la red de seguridad de T3, **conserva todas sus
  aserciones**, incluida `c.clave == "200|202607|5|80001"`. Lo único que
  cambia es un **dato de entrada** (el `paride` de la línea previa del
  `ClienteFalso`, de 0 a 80001) y el motivo está escrito en el propio
  fichero: sin ese dato el fichero dejaría de ejercitar el camino del pisado
  y pasaría a probar dos veces el caso «no hay conflicto». La aserción sigue
  siendo cierta **por el motivo bueno**, que es lo que había que comprobar.
- Los tests de R14 que fijaban la conducta contraria se **invierten** o se
  **reubican**, uno a uno y con su razón escrita (informe §4.1). Ninguno se
  borra para hacer sitio.
- R13 conserva la deduplicación por `ide` y su control positivo; su test se
  reexpresa inyectando dos `Conflicto` que comparten `hmores.ide` porque la
  Regla A elimina la ruta que lo disparaba. **La salvaguarda se queda**, que
  es lo correcto: el defecto desaparece por diseño, no por confianza.
- La cobertura sube (96,8 % → 99,1 %) y los tests de 90 a 187.

---

## 7. Cambios requeridos

**Ninguno bloqueante.** No hay lista numerada de correcciones: nada de lo
encontrado impide aprobar.

---

## 8. Lo que esta review NO cubre

Que quede dicho, porque el veredicto no debe leerse por encima de su alcance:

- **Nadie ha visto estas reglas funcionar contra Sigrid.** T13 y T14 siguen
  pendientes. La feature está aprobada como **código**, no como **conducta
  verificada en el sistema real**, y `OBRA_PRUEBAS_FORZAR` sigue en `true`.
- **El front no lee los campos nuevos.** El informe §8 lo mide sin adornos:
  una sobrecarga se pinta con el texto de un pisado, la casilla dice «Pisar»
  cuando confirmar no pisa nada, y las cuatro cifras viajan pero no se
  enseñan. **La seguridad no se pierde**, pero el modelo mental que induce es
  el equivocado. Declararlo así, en vez de esconderlo, es lo correcto; que
  vaya al backlog, también.
- **La Regla B no detecta sobrecargas preexistentes** en las que no
  participamos. Consciente y documentado en `ARCHITECTURE.md`.

---

## 9. Observaciones (no bloquean)

### 9.1 · El test que «demuestra» el mutante equivalente demuestra menos

`test_f002_r26_el_borde_exacto_de_la_tolerancia_no_existe` afirma en su
docstring que en coma flotante **no existe** un caso con
`exceso == EPSILON_CAPACIDAD`. Su primera aserción es:

```python
alcanzables = {(1.0 + k * 2.0 ** -52) - 1.0 for k in range(1, 2000)}
assert EPSILON_CAPACIDAD not in alcanzables
```

Ese conjunto llega como mucho a `2000 · 2⁻⁵² ≈ 4,4e-13`, cinco millones de
veces por debajo de la épsilon (`5e-5`, que cae en `k ≈ 2,25e11`). La
aserción **no puede fallar aunque la épsilon fuera alcanzable**: es
exactamente el vicio que el propio implementer denuncia en su §4.1 («un test
que pasa por la razón que no es, no prueba nada»). La segunda aserción,
`(1.0 + EPS) - 1.0 != EPS`, sí es un hecho observable, pero tampoco es la
demostración general.

La demostración de verdad cabe en una línea y no depende de ningún barrido:

```python
from fractions import Fraction
# El double más cercano a 0,00005 no es múltiplo del ULP de la franja [1,2).
assert Fraction(EPSILON_CAPACIDAD) % Fraction(1, 2**52) != 0
```

**No cambia el veredicto**: el mutante *es* equivalente y el reviewer lo ha
verificado por su cuenta (§2.1). Lo que se pide es que el test que se ofrece
como prueba lo sea.

### 9.2 · El `I001` de los dos ficheros de test nuevos

`test_f002_capacidad.py:16` y `test_f002_postventa.py:18`. Es `ruff check
--fix` sobre esos dos ficheros y baja el contador a 178. Los `B009` y el
`C408` **no** se tocan: están justificados y cambiarlos empeoraría el código.

### 9.3 · La spec quedó desalineada con la procedencia real

`requirements.md` R4 (línea 53) y `tasks.md` T7 (líneas 85 y 97) siguen
pidiendo el literal `Confirmado por Administración el AAAA-MM-DD ·
<interlocutor>`. La decisión de no escribir eso es correcta (§4.9), pero deja
la spec diciendo una cosa y el código otra, y el próximo que lea R4 sin el
informe delante creerá que el requisito está incumplido. **Es trabajo del
spec-author, no del implementer**: relajar el enunciado de R4 a «quién ·
cuándo · respaldo», que es lo que el test comprueba y lo que el requisito
siempre quiso decir.

### 9.4 · El test que lee el fichero de `dedicacion-api`

`test_f002_r26_la_tolerancia_es_la_del_cuadrante` navega
`Path(__file__).resolve().parents[3]` hasta `services/dedicacion-api/domain/
estados.py`. Es la decisión correcta —sin él, las dos épsilon se separan sin
que nadie se entere— y no viola el límite de servicio: no importa código ni
duplica lógica. Pero **ata la suite del transfer a la disposición del
monorepo**: si algún día el servicio se extrae a su propio repositorio, este
test se cae con un error de ruta y no con el mensaje de negocio que lleva
escrito. Merece una línea en el backlog, no un cambio hoy.

### 9.5 · Un número que no cuadra en la evidencia de Sigrid

`progress/sigrid_F-002.md` dice «las **86** líneas de obra del presupuesto
tienen `n_hijos = 0`» en la tabla de respuestas y «las **84** partidas de
obra cuelgan de `CD`, salvo cuatro» dos párrafos después; `requirements.md`
§2 usa 84. Las cifras que sostienen la decisión (todas son hojas; `cod` y
`res` son campos separados; hay capítulos de código numérico) no cambian, y
el volcado íntegro está en el mismo fichero, así que **la decisión sigue
siendo trazable**. Es un desajuste de redacción heredado de la Fase 1;
conviene cuadrarlo cuando alguien vuelva a ese documento.

---

## 10. Rastro pendiente, que es del líder (no del implementer)

### 10.1 · `progress/current.md` se quedó en la Fase 1

Su tabla de tareas termina en «T6 en adelante · `[ ]` · bajo la PARADA» y el
bloque «Verificado con salida real» sigue contando **90 tests, 5 xfailed,
96,8 % de cobertura y 9 mutantes**, que son los números de la Fase 1. Los de
hoy son **187 tests, 0 xfail, 99,1 % y 34 mutantes con 1 superviviente
equivalente**. El fichero es del líder por protocolo y el implementer tenía
prohibido tocarlo, así que esto no cuenta contra la Fase 2 — pero **hay que
refrescarlo antes de mover F-002 a `done`**, o el rastro dirá que la feature
está a medias cuando no lo está.

### 10.2 · Las tres verificaciones manuales

Antes de `done`: T6 (aviso a Administración de `656`/`664`/`680`/`693`, y la
firma definitiva de la procedencia si Administración acaba confirmando
D1/D2 — el patrón del test no clava el interlocutor, así que actualizar la
línea **no rompe nada**), T13 y T14. T14 exige autorización expresa del
humano para esa acción concreta.

### 10.3 · Un desajuste de estado ajeno a F-002

`progress/current.md` describe **F-003** como `in_progress` y aprobada en su
rama, mientras `harness/features.json` la tiene en `pending`. No afecta a
esta review ni al portero (que solo cuenta una `in_progress`), pero conviene
cuadrarlo.

---

## 11. Automejora del protocolo

Dos propuestas, **no aplicadas**, para que las valore el humano:

1. **`CHECKPOINTS.md` C4 bis — un superviviente declarado «equivalente» debe
   traer su demostración *ejecutable*, y el reviewer debe ejecutarla.** El
   protocolo obliga hoy a que el análisis no quede en `PENDIENTE`, pero no
   dice nada de la *calidad* del argumento. Esta review ha encontrado
   justamente eso: una justificación correcta acompañada de un test que no
   demuestra lo que dice (§9.1). Redacción propuesta para el punto de los
   supervivientes: «Si el análisis concluye *mutante equivalente*, el
   reviewer **reproduce el argumento por su cuenta** (ejecutándolo cuando sea
   aritmético) y deja constancia en su informe de que lo hizo. Un argumento
   plausible sin reproducir no es una justificación aceptada».
2. **`.claude/agents/reviewer.md` §Protocolo — comprobar que las guardas
   retiradas para matar un mutante eran realmente inalcanzables.** Quitar
   código es la forma más limpia de eliminar un superviviente y también la
   más fácil de hacer mal: basta con que el invariante que la hacía
   inalcanzable no exista. Propuesta: añadir al paso 5 «Cuando un
   superviviente se resuelva **quitando código defensivo**, el reviewer
   verifica el invariante que lo justifica **en quien construye el dato**, no
   en el punto donde se quitó la guarda». Es lo que se ha hecho en §4.2 y es
   donde estaba el riesgo real de esta feature.

Ambas valen para cualquier proyecto: si el humano las acepta, van a
`arnes-base` en el mismo trabajo (regla de propagación de `CLAUDE.md`).
