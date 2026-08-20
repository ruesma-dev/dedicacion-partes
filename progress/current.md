<!-- progress/current.md -->
# Trabajo en curso

**F-002 · Fijar las reglas P4 y P5: postventa y conflicto tienen dos versiones**
Rama `feature/F-002-reglas-postventa-conflicto` · `sdd: true` · rigor `critico`
Estado: **Fases 1 y 2 implementadas y APROBADAS** (2026-08-19). Falta la
**Fase 3**, que es toda del humano: T6, T13 y T14. Sin ellas F-002 no pasa a
`done`.

## Qué se ha hecho en esta sesión (2026-08-19)

**Sí se ha tocado código.** 8 commits en la rama, de `04fbd9b` a `2987fc0`
más el de bookkeeping de esta corrección. Informe completo:
`progress/impl_F-002.md`. Campaña de mutación: `progress/mutacion_F-002.md`.
Review de la fase: `progress/review_F-002_fase1.md`.

| Tarea | Estado | Commit |
|---|---|---|
| T1 · fixtures offline parametrizables del transfer | [x] | `04fbd9b` |
| T2 · tests de las reglas no disputadas (R6–R9, R12) | [x] | `60d5319` |
| T3 · un solo punto de decisión para el conflicto | [x] | `22328fb` |
| T4 · R14, R10, R11 y el defecto R13 | [x] | `20280c7` |
| T5 · fuente única de las reglas (lo que no depende de D1/D2) | [x] | `beba73b` |
| T7 · punto 5 de ARCHITECTURE definitivo (D1), con procedencia | [x] | `d0f03d9` |
| T8 · fuente única de P4 y P5, y la Regla B escrita | [x] | `25b4cc1` |
| T9 · la partida de postventa solo puede ser hoja activa | [x] | `eb3e80e` |
| T10 · **Regla A**: la partida entra en la identidad | [x] | `05ceef7` |
| T11 · **Regla B** (capacidad): detección | [x] | `01468b6` |
| T12 · **Regla B**: escritura y guarda contra pérdida de datos | [x] | `a8313f1` |
| T15 · campaña de mutación (8 supervivientes → 1 equivalente) | [x] | `caed865` |
| T16/T17 · informe, evidencias y portero en verde | [x] | `eaf77a0` |
| — · demostración exacta del equivalente + lint | [x] | `ab192b7` |
| **T6 · avisos y procedencia** | **[ ]** | **del humano** |
| **T13 · casado real contra Sigrid, sin escribir** | **[ ]** | **del humano** |
| **T14 · escritura real en la obra de pruebas `0404`** | **[ ]** | **del humano** |

### Verificado con salida real

- `bash harness/init.sh` → ENTORNO LISTO. Suite del transfer: **187 passed,
  0 xfail** (eran 90 y 5 al abrir la sesión); raíz 11 passed; api 21 passed.
- **Puerta de cobertura: 99,1 % (107/108 líneas cambiadas)**, umbral 80 %.
- **Campaña de mutación: 34 mutantes, 33 muertos, 1 superviviente**, y ese
  superviviente es **demostrablemente equivalente** (`>` vs `>=` en la
  tolerancia: los dos solo diferirían si el exceso valiese exactamente
  0,00005, que no es representable como resultado de esa resta). La
  demostración es un test con `Fraction`, y el reviewer la ejecutó.
  La **primera** pasada dejó **8 supervivientes** y se atacaron los ocho: uno
  destapó un fallo real (el `contexto` de un conflicto colaba líneas de
  **otro trabajador**), dos se resolvieron **quitando** guardas inalcanzables
  y tres con tests del cuarto decimal.
- ruff: **178** avisos (bajó desde 180; los ficheros de producción de la
  feature pasan de 83 a 82, medido por el reviewer con `ruff --isolated`).
- **R13 era un defecto real**, reproducido por el reviewer: dos líneas
  pendientes del mismo recurso y mes con partidas distintas chocaban contra
  la misma línea previa y emitían **dos `DELETE` del mismo `hmores.ide`**,
  con `res.borradas` contando 2. Arreglado deduplicando por `ide`.

## Consultas de lectura contra Sigrid

- **C2 · EJECUTADA** el 2026-08-19, autorizada por el humano. Volcado íntegro
  en `progress/sigrid_F-002.md`. Cerró D1: la obra de postventa es `POSTV2`,
  se imputa a **partida hoja** y el emparejamiento por **código exacto**
  (`cod = '0610'`, `res = 'COLEGIO ALEGRA'`, campos separados) es el correcto.
  De paso encontró cuatro partidas duplicadas sin el cero inicial (`656`,
  `664`, `680`, `693`) colgando de la raíz del presupuesto en vez de `CD`.
- **C6 · EJECUTADA** el 2026-08-19. Buscaba cualquier fila de `hmores` con
  `synckey LIKE 'porcentajes:%'` o la marca `PRUEBA-PORC`. **Resultado: 0
  filas ⇒ este sistema NUNCA ha escrito en Sigrid.** Cierra la ventana ciega
  del 25/07/2026 que detectó `progress/explore_transfer_original.md`: lo que
  hubo en julio fueron cinco **preflights** en modo pruebas, no escrituras. No
  hay restos que limpiar y **T14 sigue entera por hacer**.
- **C1, C3, C4 y C5 · NO ejecutadas.** Siguen escritas en
  `specs/F-002-reglas-postventa-conflicto/requirements.md` §2. C4 perdió casi
  todo su interés cuando el humano contestó D2 directamente.

## Decisiones del humano en esta sesión

1. **D1 · cerrada.** Obra de postventa `POSTV2`, siempre viva. Se imputa
   siempre a la partida de la obra original dentro de POSTV2 (`0610 COLEGIO
   ALEGRA`), **nunca** a una partida normal de ejecución. Confirmado además
   con la lectura C2.
2. **D2 · contestada con una tercera opción.** Pueden convivir varias líneas
   `M*` del mismo trabajador en el mismo parte y mes con **partidas
   distintas**, pero **la suma de sus cantidades no puede pasar de 1**
   (el 100 % del trabajador).

## Fase 2 · qué se está implementando (T7–T12)

El rediseño de P4 **ya está hecho y aprobado por el humano** (PARADA 1 del
2026-08-19). La vieja P4 se parte en dos reglas:

- **Regla A · identidad.** `campos_identidad(destino)` pasa a devolver
  `CAMPOS_CLAVE` completos **siempre**, también en obra normal: una línea
  nuestra solo pisa una existente si coinciden recurso + mes + código de hora
  + **partida**.
- **Regla B · capacidad (nueva).** Por trabajador y parte,
  `Σ can de las líneas M* existentes que NO se pisan + Σ can de las nuestras`
  no puede pasar de 1. Tolerancia `0.00005`, el equivalente exacto en escala
  0-1 del `_EPSILON = 0.005` que ya usa el cuadrante en
  `services/dedicacion-api/domain/estados.py`, para que front y Sigrid no
  discrepen en el último decimal.
- **Qué hace al pasarse (decisión del humano): avisar y esperar
  confirmación**, no bloquear ni escribir a ciegas.
- **Cómo viaja (decisión del humano): como un `Conflicto` más**, con motivo
  propio, para que F-002 **no toque `dedicacion-api` ni `dedicacion-front`**.

**T6 es del humano y no bloquea el código** (ver abajo).

## Verificaciones `MANUAL (humano)` pendientes

Ninguna de la Fase 1 lo era. Todas las que quedan están bajo la PARADA:

| Tarea | Qué es | Comando |
|---|---|---|
| T6.1 | trasladar a Administración el aviso de las **cuatro partidas duplicadas** de POSTV2 (`656`, `664`, `680`, `693`, colgando de la raíz en vez de `CD`) | ninguno: es un aviso, no una acción técnica |
| T6.2 | confirmar **quién firma** la línea de procedencia de R4 | ver «Procedencia» abajo |
| T6 opc. | calibrar cuánta sobrecarga real va a aflorar con **C3** y **C5** (solo lectura) | `requirements.md` §3. **C1 y C4 ya no tienen motivo** |
| T13 | casado real contra Sigrid **sin escribir** | `python prueba_escritura_porcentajes.py capitulos` / `estado` / `preflight` |
| T14 | escritura real en la obra de pruebas `0404` | `ejecutar --confirmar` → `verificar` → `limpiar --confirmar`. **Exige autorización expresa del humano para esa acción concreta**; ningún agente la lanza |

`OBRA_PRUEBAS_FORZAR` sigue en `true` y esta fase no ha tocado ningún `.env`.

### Procedencia de las decisiones (R4) — pendiente de confirmar por el humano

La spec pide la línea `Confirmado por Administración el AAAA-MM-DD ·
<interlocutor>`. **No consta que se haya hablado con Administración**: D1 y D2
las decidió el humano directamente el 2026-08-19, y se respaldaron con las
lecturas reales C2 y C6 contra Sigrid. Escribir «Administración» sería una
procedencia falsa, que es justo lo que esta feature viene a eliminar. Se
implementa con la procedencia real:

> `Confirmado por Pablo Gris (responsable del proyecto) el 2026-08-19 ·
> verificado contra Sigrid, ver progress/sigrid_F-002.md`

Si el humano prefiere otro interlocutor o quiere llevarlo a Administración
antes de cerrar, **es una línea de `docs/ARCHITECTURE.md`**.

## Otras features vivas

> **Nota de estado entre ramas.** `harness/features.json` de ESTA rama tiene
> F-003 en `pending`, porque su `in_progress` vive en la rama de F-003 y
> `harness/init.sh` solo admite **una** feature en curso a la vez. No es un
> descuadre que haya que arreglar aquí: se resuelve solo al mergear.

- **F-003** (`in_progress` en su rama): implementada y **APROBADA** por el reviewer en su
  rama `feature/F-003-orm-columnas-sigrid` (HEAD `e6aeefb`). 84 tests en el
  api, cobertura 94,4 %, 14 mutantes y 0 supervivientes. **No pasa a `done`
  hasta que el humano ejecute la verificación MANUAL T8** contra su base real
  y anote el resultado en el `current.md` de esa rama, donde están los
  comandos. Lo que consiguió: `_ALTERS` desaparece, el ORM es la única fuente
  de verdad y **construir la app ya no abre conexión a PostgreSQL** — que era
  el motivo de que el servicio no pudiera tener tests de API.
- **F-011** (`pending`, prioridad 11): abierta hoy por decisión del humano.
  Si un recurso tiene varios códigos `M*`, hoy se elige el primero por orden
  alfabético y de ahí sale el importe mensual que se escribe en Sigrid. Se
  deja así de momento; la feature es avisarlo en el preflight (hoy solo va al
  log) y pedir a Administración un único código de hora mes por trabajador.
- **F-009** (higiene de artefactos de cobertura) ha estorbado ya **tres
  veces**: `init.sh` deja el árbol sucio y eso impide usar la campaña de
  mutación paralela, que exige árbol limpio. Ver `review_F-002_fase1.md` §10.

## Nota de proceso

Los cuatro puntos que el reviewer pidió corregir (checkboxes de `tasks.md`,
este fichero y el estado en `features.json`) los ha hecho **el líder**, no el
implementer: `current.md` y `features.json` son suyos por protocolo y al
implementer se le había prohibido tocarlos para que no chocara con el
subagente que escribía la spec de F-003 en el mismo árbol. El rastro quedó
sin actualizar por ese motivo.
