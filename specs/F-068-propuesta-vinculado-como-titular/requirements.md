<!-- specs/F-068-propuesta-vinculado-como-titular/requirements.md -->
# F-068 · La partida del vinculado se propone como la del trabajador

Rigor **`critico`**: decide la partida que se escribe en Sigrid. **Enmienda de
F-044 R15-R16 (D4b)** (`specs/F-044-recursos-vinculados/`). Petición del
humano del 2026-10-28 sobre un caso de la 0678: cada vinculado tiene allí DOS
hojas con su cuenta (`CI.0.xx` y `CI.4.x`, mismo nombre) y F-044 deja la
subfila «automática», aunque su historial en la obra es claro. Decisión
literal: «el criterio debe ser como el principal…»; «ok, preferir CI.4 en
empate. antes de f54». Toca **transfer** (regla, una lectura más), **api**
(guarda los métodos nuevos y manda la descripción del vinculado) y **front**
(un rótulo); design §1. Evidencia de Sigrid: `progress/explore_F-068.md`.
Decisiones abiertas `[Dn]`: design §9. Fuera: el «último parte en otra obra»
del trabajador (paso b de `#regla-partida`), F-054, la regla del titular y
todo lo que no es la partida del vinculado (hora, importe, cuenta, parte,
identidad, capacidad: F-044 tal cual).

Glosario (el de F-044): **vinculado**, **titular**. **Hoja activa**: hoja del
presupuesto de la obra de alta (`build_arbol_partidas`). **Su cuenta**: la
subcuenta de la cuenta de la hora del vinculado (F-044 R15). **Casador**: el
del trabajador, `partida_matcher.match_partida` (copia cerrada de `partes`).

## 1. El orden (transfer, regla pura)

- **R1.** CUANDO un vinculado no tiene elegida válida (F-044 R15, sin cambio)
  y su titular no va a postventa, VAR ni partida no `CI*` (F-044 R17, sin
  cambio), el sistema debe proponerle la partida del **primer** paso que dé
  una, en este orden: historial en la obra (R2), su cuenta (R4), nombre (R5,
  R6), capítulo CI.4 en empate (R7); si ninguno, sin partida (R9).
- **R2.** `[D2, D3]` Historial: entre las líneas de ESE recurso en ESA obra de
  la ventana del trabajador `[D3]`, con partida `CI*` (código, como F-044
  R17) `[D2]`, las del **último mes**; gana la partida con más `can` sumado si es la única con ese máximo y
  es hoja activa. Método `parte_anterior`, con el `origen` del trabajador
  («parte P · MM/AAAA · obra O»). Empate o ganadora que no es hoja activa:
  este paso no propone.
- **R3.** El paso de R2 usa la **misma** función que el «parte anterior» del
  trabajador (`propuesta_partida.previa_en_obra`), no una copia.
- **R4.** Su cuenta: si **una** sola hoja activa de la obra tiene su cuenta,
  esa, método `ci_tipo` (lo de F-044 R15, ahora tras el historial).
- **R5.** `[D5]` Si **varias** hojas activas tienen su cuenta, se puntúa cada
  una con el casador (categoría = descripción del tipo, `tipo_res`; nombre =
  descripción del recurso); la que no casa puntúa 0. Gana la de puntuación
  máxima si es la única; método el del casador (`auto_nombre` o
  `auto_categoria`).
- **R6.** Si **ninguna** hoja activa tiene su cuenta, se casa igual entre las
  hojas activas `CI*` de la obra (código que empieza por `CI`, la misma
  prueba que F-044 R17), **solo** las que casan; gana la única de puntuación
  máxima.
- **R7.** `[D1, D5]` Empate en R5 (también todas a 0) o en R6 (entre las que
  casan): gana la **única** empatada del capítulo CI.4; método
  `capitulo_ci4`.
- **R8.** `[D1]` Una hoja es del capítulo CI.4 si su código normalizado
  (mayúsculas, sin espacios ni guiones), partido por puntos, tiene `CI` como
  primer trozo y como segundo un número igual a 4: `CI.4.13`, `CI.04.13`,
  `CI.4.19_1` sí; `CI0.04.05`, `CI_F1.04.10`, `CI.0.17`, `CI.03P.9` no.
- **R9.** SI ningún paso propone (R6 sin ninguna que case, o el empate sigue
  con 0 o 2+ del CI.4), ENTONCES el vinculado queda **sin partida** como en
  F-044 R16 (`#regla-sin-partida`, su clave, su aviso), nunca la primera, con
  motivo `sin_ci` (ninguna con su cuenta), `varias_ci` (varias con su cuenta)
  o `empate_nombre` (sin su cuenta, empate por nombre) y su texto.
- **R10.** Toda propuesta de R2-R7 es hoja activa del presupuesto de la obra
  de origen; la regla no lee nada (las lecturas llegan como funciones).

## 2. Lecturas (transfer)

- **R11.** El historial de los vinculados es **una** lectura más por
  petición, solo si alguno llega a R2: líneas de partes de trabajo de los
  recursos de los vinculados de la petición, **en la obra de origen**, en la
  ventana, con partida del presupuesto de esa obra, de cualquier hora.
- **R12.** Las cuentas del presupuesto (F-044 R27) se leen solo si alguno
  llega a R4; el presupuesto, el del pipeline o una lectura, como hoy.
- **R13.** SI la lectura del historial falla o vuelve `truncated`, ENTONCES el
  preflight y la propuesta fallan sin proponer ni escribir (F-044 R27).
- **R14.** Sin vinculados, o con todos resueltos antes de R2 (elegida,
  titular o propuesta guardada válida), las lecturas son **las mismas** que
  hoy (F-044 R11, R27): ni historial de vinculados ni cuentas.
- **R15.** Suelto, por lote y en `partidas/propuesta(-lote)`, el resultado de
  cada subfila es el mismo (F-044 R29); en un lote, el historial de
  vinculados se lee como mucho una vez por obra.

## 3. Propuesta guardada, contrato y api

- **R16.** CUANDO un vinculado trae propuesta guardada con un método de
  propuesta propio (`parte_anterior`, `ci_tipo`, `auto_nombre`,
  `auto_categoria`, `capitulo_ci4`) que es hoja activa y su titular no va con
  él (F-044 R17), el transfer debe escribirla tal cual, con su método y su
  origen, sin leer historial ni cuentas (F-055 R8; hoy solo `ci_tipo`). La de
  método `titular` se recalcula, como hoy.
- **R17.** La api debe guardar como propuesta de subfila (preflight y cola
  del mes) la de cualquiera de los métodos de R16 y `titular`
  (`METODOS_PROPUESTA_VINCULADO`); `manual` no se guarda.
- **R18.** La api debe mandar en cada vinculado su `descripcion`
  (`recurso_vinculado.descripcion`) al registrar y al proponer, y su
  `tipo_res` también al proponer. El transfer los acepta opcionales: sin
  ellos, R5-R6 casan con lo que llegue (sin texto, nada casa).
- **R19.** `[D4]` Las propuestas de subfila guardadas antes de F-068 se
  tratan según D4 (recomendado: se quedan; R16 las escribe).

## 4. Front, documentación y verificación

- **R20.** El front debe rotular `capitulo_ci4` («capítulo CI.4 en empate»)
  en la subfila y el modal con `rotuloOrigen`; `parte_anterior`, `ci_tipo` y
  `auto_*` usan los rótulos que ya tiene. No calcula nada.
- **R21.** `docs/ARCHITECTURE.md#regla-vinculado` (Partida y Lecturas) dice
  el orden nuevo; `docs/INTEGRACION.md` §5 los campos y métodos nuevos; la
  enmienda queda anotada en F-044 bajo R15-R16.
- **R22.** Los tests de F-044 que fijan el orden viejo (CI del tipo sin
  historial; varias ⇒ sin partida) se ajustan a la enmienda; los demás
  siguen intactos.
- **R23.** MANUAL del humano, solo lectura: el selector y el preflight de la
  0678 del caso dan a sus subfilas `CI.4.13`, `CI.4.1` y `CI.4.15` con método
  «parte anterior» (tasks, T13).
