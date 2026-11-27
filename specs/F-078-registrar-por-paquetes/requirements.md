# F-078 · Registrar en Sigrid solo los seleccionados o los visibles (paquetes)

Rigor **`critico`** (decide qué líneas se escriben en Sigrid y cuáles se ponen
a 0; design, cabecera). Petición de negocio del 2026-11-22, punto 8: «poder
registrar solo por seleccionados o visibles (por paquetes)». Toca **api y
front**; el transfer, nada (design §1). Decisiones D1-D9 **abiertas** para el
humano (design §10); los requisitos van escritos con la opción recomendada y
llevan su `[Dn]`.

## 0. Glosario

- **Modo** del registro, hoy: **mes** (botón «Registrar en Sigrid», sin
  `trabajador_ide`), **trabajador** («⇪ Sigrid» de la fila o del editor,
  `trabajador_ide`) y **obra** (`obra_ide`, solo el repreflight del modal al
  cambiar una partida, F-050; no es una entrada del usuario).
- **Paquete**: un conjunto de trabajadores que el usuario elige en el
  cuadrante; modo nuevo, `trabajador_ides`. Es el modo trabajador para N.
- **Seleccionados**: la selección múltiple de F-029 (Ctrl/Shift+clic) que
  queda **visible** con los filtros (la «selección efectiva» de F-029 D6).
- **Visibles**: los trabajadores que enseña la tabla con los filtros activos
  (buscador, filtros de columna, chips, «Solo pendientes», incidencia).
- **Trabajador entero**: todas sus asignaciones con % > 0 del periodo (obra,
  `Postv-` y VAR), sus subfilas de vinculados y sus incidencias.

## 1. Contrato de la api (`registro/preflight` y `registro/ejecutar`)

- **R1.** `[D1, D2, D8]` CUANDO el cuerpo trae `trabajador_ides`, el sistema
  debe analizar (preflight) o escribir (ejecutar) **solo** a esos
  trabajadores y a cada uno **entero**, con la visibilidad por empresa y la
  vigencia por mes de hoy (F-034, F-026). (capa: unit)
- **R2.** `[D8]` Cada elemento de `trabajador_ides` debe validarse como el
  `trabajador_ide` de F-056 (entero; también `"11"` y `11.0`); los repetidos
  se quitan conservando el primer orden. (capa: unit)
- **R3.** SI `trabajador_ides` no es una lista, está **vacía** o algún
  elemento no es entero (`null`, `""`, `true`/`false`, texto, decimal, lista,
  objeto), ENTONCES las dos rutas deben responder **422** sin llamar al
  registro: un paquete mal formado **nunca** registra el mes entero.
  (capa: unit)
- **R4.** SI el cuerpo trae a la vez `trabajador_ides` y un `trabajador_ide`
  no nulo, ENTONCES 422 sin llamar al registro. (capa: unit)
- **R5.** Sin `trabajador_ides` (ausente o `null`), las dos rutas deben
  comportarse como hoy en los modos mes, trabajador y obra, con la misma
  sentencia (el filtro `asignacion.trabajador_ide == X` de F-056): ningún
  test anterior cambia. (capa: unit)
- **R6.** Para cada obra, la petición del paquete al transfer debe ser la
  del mes entero **sin** las líneas, incidencias, `quitadas` e
  `incidencias_mes` de los trabajadores de fuera; los `cierres_recursos`,
  designados sobre las peticiones del paquete (F-062 R24); una obra sin
  nada del paquete no se pide. Con todos los trabajadores en el paquete, las
  peticiones son exactamente las del mes. (capa: unit)
- **R7.** `[D1]` CUANDO el preflight de un paquete no trae `obra_ide`, el
  sistema debe pedir el lote **completo** (sobrantes de F-054,
  `#regla-obra-cero`) y devolver `sobrantes` como el de un trabajador; con
  `obra_ide`, solo esa obra del paquete y sin sobrantes (F-054 R31).
  (capa: unit)
- **R8.** CUANDO `ejecutar` recibe un paquete, el sistema debe poner a 0
  primero las `sobrantes_a_cero` confirmadas y después escribir por obra y en
  serie las peticiones del paquete, con la traza de hoy (F-054 R35).
  (capa: unit)
- **R9.** `no_vigentes` e `incidencias_quitadas` del paquete deben traer
  solo las de sus trabajadores. (capa: unit)
- **R10.** CUANDO ningún trabajador del paquete tiene nada que registrar
  (sin asignaciones, otra empresa, `ide` que no existe), el sistema debe
  responder como el modo trabajador en ese caso: `ok: true`, `obras: []`,
  sin llamar al transfer. (capa: unit)
- **R11.** `[D7]` El paquete no debe tener tope de tamaño: uno con todos los
  trabajadores del mes se acepta. (capa: unit)

## 2. Front (`app.js`, `index.html`)

- **R12.** `[D4]` La barra de herramientas debe tener el botón
  `#btn-registro-paquete` junto a «Completar al 100 %», cuyo rótulo dice a
  quién registra: con selección múltiple, «⇪ Registrar seleccionados (M)»
  (M = seleccionados visibles); sin ella, «⇪ Registrar visibles (N)»; se
  recalcula en cada pintado de la tabla. «Registrar en Sigrid» sigue siendo
  el mes entero. (capa: unit)
- **R13.** `[D3]` MIENTRAS el periodo no está ABIERTO, M (o N) es 0 o el
  registro está bloqueado tras un corte (hotfix del 2026-11-11), el botón
  debe estar desactivado; con selección y todos sus seleccionados ocultos,
  su `title` debe decir que están ocultos por el filtro, y nunca pasa a
  registrar los visibles. (capa: unit)
- **R14.** CUANDO se pulsa, el front debe pedir el preflight con
  `trabajador_ides` = los `ide` de los seleccionados visibles (o de los
  visibles), en el orden de la tabla, y `trabajador_ide: null`. (capa: unit)
- **R15.** `[D9]` CUANDO se pulsa con el editor de un trabajador abierto, el
  front debe guardarlo (`guardarAhora`) antes de pedir el preflight.
  (capa: unit)
- **R16.** La lista debe congelarse al pedir el preflight: el repreflight
  de una obra (F-050) y `ejecutar` mandan la misma, aunque cambien la
  selección o los filtros; «Registrar en Sigrid» y «⇪ Sigrid» no mandan
  `trabajador_ides` (el cuerpo de hoy). (capa: unit)
- **R17.** `[D5]` CUANDO el preflight es de un paquete, el modal debe llevar
  en el título «· paquete de N trabajadores (seleccionados | visibles)», una
  lista plegable con sus nombres (escapados) y, si quedan seleccionados
  ocultos, «K seleccionados ocultos por el filtro no se registran»; obras,
  avisos, casillas y sobrantes, como hoy. Sin paquete, el modal de hoy.
  (capa: unit)
- **R18.** `[D5]` CUANDO termina `ejecutar` de un paquete, el aviso final
  debe empezar por «Paquete de N · » y seguir con el de hoy; ante un corte
  del proxy (502, 504, red), el comportamiento del hotfix del 2026-11-11.
  (capa: unit)
- **R19.** El front no debe decidir qué líneas se registran: solo manda los
  `ide` de los trabajadores elegidos; el cuerpo del paquete lleva las claves
  de hoy más `trabajador_ides`, ninguna otra. (capa: unit)

## 3. Regla del 100 % y obras compartidas

- **R20.** `[D6]` El sistema no debe bloquear ni avisar de nuevo por la
  regla del 100 % en el paquete: cada trabajador va entero (R1), así que su
  total es el del cuadrante, que no bloquea (regla 4 de ARCHITECTURE).
  (capa: unit)
- **R21.** CUANDO una obra tiene en su parte trabajadores de dentro y de
  fuera del paquete, el sistema no debe tocar ninguna línea de los de fuera
  (ni pisarla, ni ponerla a 0, ni contarla como sobrante); el parte que
  falte lo crea el primer registro y los siguientes lo reutilizan (paso 5
  del transfer). (capa: unit)

## 4. Documentación y verificación manual

- **R22.** `docs/ARCHITECTURE.md` (endpoints y `#regla-obra-cero`: «del
  periodo, de un trabajador o de un paquete»), `docs/INTEGRACION.md` y
  `azure-apps/dedicacion.md` deben describir `trabajador_ides` con su
  validación. (capa: unit)
- **R23.** En local y en **modo pruebas** (`OBRA_PRUEBAS_FORZAR=true`), el
  registro de un paquete de dos trabajadores debe escribir solo sus líneas
  en la 0404 y dejar igual las de un tercero del mismo parte (MANUAL del
  humano, tasks). (capa: integración)

## 5. Fuera de alcance

- Registrar en segundo plano o con progreso (F-073); el informe Excel
  (F-073); un atajo de teclado para el paquete; pasar el modo trabajador a
  `trabajador_ides` (D8 b); un aviso del 100 % en cualquier modo (D6 b/c).

## 6. Tests anteriores que cambian

**Ninguno** (lista cerrada). El filtro de un trabajador sigue siendo `==`
(R5; `test_f056_trabajador_ide.py` lo inspecciona) y el front solo añade
`trabajador_ides` cuando hay paquete (`JSON.stringify` omite `undefined`).
Otro test en rojo ⇒ PARA y `blocked`.
