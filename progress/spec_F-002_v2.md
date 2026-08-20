<!-- progress/spec_F-002_v2.md -->
# F-002 · Actualización de la spec a la versión 2

- **Fecha:** 2026-08-19 · **Autor:** subagente `spec-author`.
- **Rama:** `feature/F-002-reglas-postventa-conflicto` (no la he cambiado; no
  he hecho commit: lo hace el líder).
- **Alcance:** solo `specs/F-002-reglas-postventa-conflicto/` (los tres
  ficheros). **Ni una línea de código, ni de tests, ni de `docs/`.**

## 0. Por qué

La v1 se escribió con D1 y D2 abiertas. Desde entonces:

1. El humano **cerró D1** y la lectura real C2 contra Sigrid la corroboró
   (`progress/sigrid_F-002.md`).
2. El humano **cerró D2 con una tercera opción** que la propia v1 había
   anticipado como «la que invalida el diseño».
3. La **Fase 1 (T1–T5) está implementada y APROBADA**
   (`progress/impl_F-002.md`, `progress/review_F-002_fase1.md`).

La spec se había quedado desfasada justo en su parte más importante: la que
decide qué se borra y qué se escribe en un parte de Sigrid.

## 1. `requirements.md`

| Antes (v1) | Ahora (v2) |
|---|---|
| §2 «Decisiones abiertas que solo puede cerrar Administración»: dos preguntas cerradas con sus dos versiones enfrentadas y cinco consultas SQL. | §2 «Decisiones tomadas»: D1 y D2 **cerradas**, con fecha (2026-08-19), quién decide (el humano; D1 además corroborada con la lectura C2) y la evidencia. |
| R15–R19 «BLOQUEADOS hasta la respuesta de Administración», redactados en condicional («del tipo que Administración confirme»). | R15–R19 son requisitos EARS normales y concretos sobre la postventa: obra no encontrada, **partida hoja activa**, mismo universo que el desplegable, **casado por código exacto** y **determinismo**. |
| R18/R19 de la v1 hablaban del conflicto «según el criterio que Administración confirme». | Se renumeran y se parten: **R20–R22 (Regla A · identidad)** y **R23–R31 (Regla B · capacidad)**, que **no existían**. |
| — | **R32** (nuevo, seguridad): un conflicto confirmado no emite su borrado si ninguno de sus registros llega a escribirse. |
| — | **R33** (nuevo, compatibilidad): el contrato sigue siendo consumible por un cliente que ignore los campos nuevos. |
| R13 enunciado sobre «dos líneas pendientes que chocan con la misma». | R13 reenunciado sobre «dos conflictos confirmados que contienen la misma línea», con la nota de que su escenario original **deja de ser alcanzable** con la Regla A. |
| §2 traía el SQL de C1–C5. | §3 nueva: **estado** de cada consulta. **C1 y C4 han perdido su motivo** (C4 lo perdió cuando el humano contestó D2); **C3 y C5 siguen teniendo valor** como diagnóstico de cuánta sobrecarga real va a aflorar. El SQL literal no se duplica: está en el historial de git. |
| Tabla de trazabilidad con «bloqueado» en R15–R19. | Tabla al día: qué test cubre cada requisito, en qué fichero y en qué tarea llega. Se marcan los que ya pasan (Fase 1) y los cinco `xfail(strict=True)` con la tarea que los cierra. |

Los requisitos R1–R14 se conservan; solo se retocan R1 (añade el ancla
`#regla-capacidad`), R4 (exige además la referencia al volcado) y R13.

## 2. `design.md`

- **§1 Límite de servicio**: se añade la justificación de por qué la Regla B
  **no** va a `dedicacion-api` aunque sea quien ve el cuadrante completo (la
  API no ve las líneas que Administración mete a mano en el parte, y el
  transfer se invoca por obra). Con tabla comparativa de las dos reglas.
- **§1.1 nuevo**: el único efecto que cruza la frontera sin tocar código
  ajeno. Al meter en `omitidas` las líneas bloqueadas por sobrecarga, la API
  las persistirá como `sigrid_estado='omitido'` en PostgreSQL. Está
  documentado, con sus dos consecuencias aceptadas (el motivo cabe en los 300
  caracteres a los que la API trunca; el *toast* del front cuenta esa línea
  dos veces).
- **§3.4**: el arreglo del filtro de hojas de `resolver_postventa`
  (`partidas_hoja(nodos)`), con el efecto secundario de que la elección pasa
  a ser **determinista** por orden de código — cambio de conducta observable,
  deliberado y con test (R19).
- **§4** reescrita: `campos_identidad()` **sin parámetro**, y las piezas
  nuevas de la Regla B (`Capacidad`, `es_linea_mensual`,
  `evaluar_capacidad`, `clave_sobrecarga`, las constantes y el motivo).
- **§4.3**: la tolerancia `0,00005` con su justificación escrita para que
  nadie la cambie por un número redondo, y el argumento de por qué `float` y
  no `Decimal` (el porcentaje es `Numeric(6,2)` sobre 0–100, así que /100 es
  exacto a cuatro decimales).
- **§5 nueva**: cómo interactúan las dos reglas. Es la sección que el humano
  pidió razonar: la línea pisada no se cuenta dos veces, las `synckey`
  propias tampoco, la suma se calcula **suponiendo todos los pisados
  confirmados**, y qué se enseña cuando un recurso tiene pisado y sobrecarga
  a la vez.
- **§5.5**: la vía por la que la Regla B podía reabrir R13 **por otro lado**
  (confirmar el pisado y denegar la sobrecarga ⇒ se borra la línea de
  Administración y no se escribe el sustituto). Cerrada con R32.
- **§8 nueva**: **qué se pierde** por reutilizar el mecanismo de conflicto en
  lugar de darle un tipo propio, sin adornos: el texto del front dice
  «Pisar … se borran ⟨vacío⟩», las cifras que justifican el aviso no se
  pintan, el resumen mezcla los dos tipos y el modelo mental que induce es el
  equivocado. Con la propuesta de feature de front que lo arregla, **fuera**
  de F-002.
- **§7 Riesgo 2 corregido**: la v1 decía que la opción (c) invalidaba el
  diseño. Ya no es un riesgo: **es el diseño**. Su hueco lo ocupa el riesgo
  real que queda —el efecto de la Regla A el primer día: menos pisados y más
  líneas conviviendo—, que es justamente lo que la Regla B tiene que cazar.
- **§9**: alternativas descartadas nuevas (el tipo propio en el contrato;
  omitir en silencio; dejar el parámetro `destino`).

## 3. `tasks.md`

- **T1–T5 intactas y en `[x]`.** No he tocado ni su texto.
- **Se retira la barrera ⛔ PARADA**: D1 y D2 están cerradas, no bloquea nada.
- **T6** deja de ser «llevar las preguntas a Administración» y pasa a ser el
  cierre de los dos cabos que solo puede atar el humano: el aviso de las
  **cuatro partidas duplicadas** (`656`, `664`, `680`, `693`) y el
  interlocutor/fecha de la línea de procedencia de R4. Con C3 y C5 ofrecidas
  como opcionales y no bloqueantes.
- **T7 y T8**: la fuente única definitiva (punto 5, punto 6, punto nuevo
  `#regla-capacidad`, la frase cruzada en el punto 4, la retirada de los
  enunciados de P4/P5 y los cinco `xfail`).
- **T9**: código de D1 (el filtro de hojas, el motivo nuevo, el renombrado) y
  `test_f002_postventa.py` con R15–R19.
- **T10**: Regla A, con la reescritura explícita de los dos tests de T4 que
  hoy fijan la conducta contraria y la revisión de
  `tests/test_pipeline_offline.py`, justificando por escrito cada aserción.
- **T11**: Regla B — detección (funciones puras, campos del `Conflicto`,
  paso 7 bis del preflight) y `test_f002_capacidad.py`.
- **T12**: Regla B — escritura y salvaguardas (bloqueo, `omitidas`, cero
  borrados al confirmar una sobrecarga, R32, y la reexpresión del test de
  R13).
- **T13–T17 conservan su numeración y su significado**, que es lo que pedía
  el líder: **T13 y T14 siguen marcadas `MANUAL (humano)`**, y T14 —la
  escritura real contra la obra de pruebas `0404`— lleva escrito que **exige
  autorización expresa del humano para esa acción concreta** y que **ningún
  agente la lanza por su cuenta**.
- T13 gana dos comprobaciones nuevas: que la partida resuelta sea una **hoja**
  y que el conflicto de sobrecarga aparezca con sus cifras.

## 4. Lo que NO he hecho

- No he tocado código, tests, `docs/`, `harness/features.json` ni
  `progress/current.md` (es del líder).
- No he ejecutado ninguna consulta contra Sigrid ni ningún comando de
  escritura. `OBRA_PRUEBAS_FORZAR` sigue como estaba.
- No he cambiado de rama ni he commiteado nada.

## 5. Decisiones abiertas que necesita validar el humano

Ninguna bloquea la implementación. Son tres, y las tres son de forma, no de
fondo:

1. **El interlocutor de la línea de procedencia (R4).** El formato que exige
   el test es `Confirmado por Administración el AAAA-MM-DD · <interlocutor>`.
   La fecha es **2026-08-19**; el nombre no me lo puedo inventar. Es la T6.
   Si Administración no tiene un interlocutor nominal para esto, decir con
   qué texto se rellena.

2. **El atributo `capitulo_postventa` del preflight se queda con ese nombre**
   aunque D1.2 haya dicho «partida». Renombrarlo rompería el contrato HTTP
   que lee el front, y F-002 no toca el front. Lo he dejado así y documentado
   en `design.md` §3.5, con el renombrado coordinado propuesto como feature
   aparte. Si el humano prefiere hacerlo ya, hay que ampliar el alcance a los
   tres servicios y volver a proponer.

3. **La feature de front que arregla los cuatro costes de `design.md` §8.**
   Con la decisión de reutilizar el mecanismo de conflicto, el humano ve una
   casilla que dice «Pisar» para algo que no pisa, y sin las cifras que
   justifican el aviso. Es pequeña (una rama en `pintarModalPreflight`) y no
   entra en F-002. Propongo darla de alta en `BACKLOG.md` **antes** de T14,
   para que no se pierda al cerrar la feature.

Y un aviso operativo que no es una decisión: **T14 sigue necesitando
autorización expresa** aunque la feature esté aprobada. Que la spec la
describa no la autoriza.
</content>
</invoke>
