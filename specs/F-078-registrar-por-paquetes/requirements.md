# F-078 · Registrar en Sigrid solo los seleccionados o los visibles (paquetes)

Rigor **`critico`** (decide qué líneas se escriben en Sigrid y cuáles se ponen
a 0; design, cabecera). Petición de negocio del 2026-11-22, punto 8: «poder
registrar solo por seleccionados o visibles (por paquetes)». Toca **api y
front**; el transfer, nada (design §1). D3 y D4 **decididas** por el humano el
2026-11-27 («quiero que el registrar actual sea el boton registrar
seleccionados… si solo hay 1 seleccionado… registra todos los que estan
visibles, sin ocultos»); D1, D2 y D5-D11 decididas en la (a) por el humano el mismo día, «ok a todo»
(design §10); los requisitos llevan su `[Dn]`.

## 0. Glosario

- **Modos** de hoy: **mes** («Registrar en Sigrid»; tras F-078 el front no lo
  pide), **trabajador** («⇪ Sigrid», `trabajador_ide`) y **obra** (`obra_ide`,
  solo el repreflight del modal, F-050). **Paquete** (nuevo,
  `trabajador_ides`): el modo trabajador para N.
- **Seleccionados**: la selección múltiple de F-029 (Ctrl/Shift+clic) que
  queda **visible** con los filtros. Puede tener 0, 1 o más; sin ella, el
  cursor (`state.seleccionIde`, siempre en una fila visible) cuenta como 1.
- **Visibles**: los que enseña la tabla con los filtros activos.
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
- **R11.** `[D7]` El paquete no debe tener tope: uno con todos los del mes
  (el botón sin filtros) se acepta. (capa: unit)

## 2. Front (`app.js`, `index.html`)

- **R12.** `[D4, D10]` El botón actual `#btn-registro` debe registrar el
  **paquete** (no hay botón nuevo) y su rótulo decir a quién: «Registrar
  seleccionados (M)» o «Registrar visibles (N)»; se recalcula en cada
  pintado de la tabla. El front ya no pide el registro del mes entero.
  (capa: unit)
- **R13.** `[D3, D4, D11]` El alcance debe ser: con **2 o más**
  seleccionados (F-029) **visibles**, esos (M = cuántos); con 0 o 1
  seleccionados (el cursor cuenta como 1), **todos los visibles** con los
  filtros (sin filtros, todos los de la tabla). **Nunca** va un oculto por el
  filtro. (capa: unit)
- **R14.** `[D11]` SI hay 2 o más seleccionados pero menos de 2 visibles,
  ENTONCES el botón debe estar desactivado con un `title` que diga que la
  selección está oculta por el filtro (no pasa a los visibles). (capa: unit)
- **R15.** MIENTRAS el periodo no está ABIERTO, no hay ningún visible o el
  registro está bloqueado tras un corte (hotfix del 2026-11-11), el botón
  debe estar desactivado; al pulsarlo con la lista vacía, no se pide nada.
  (capa: unit)
- **R16.** CUANDO se pulsa, el front debe pedir el preflight con
  `trabajador_ides` = esos `ide` en el orden de la tabla y `trabajador_ide:
  null`. (capa: unit)
- **R17.** `[D9]` CUANDO se pulsa con el editor de un trabajador abierto, el
  front debe guardarlo (`guardarAhora`) antes de pedir el preflight.
  (capa: unit)
- **R18.** La lista debe congelarse al pedir el preflight: el repreflight
  de una obra (F-050) y `ejecutar` mandan la misma aunque cambien la
  selección o los filtros. «⇪ Sigrid» de la fila y del editor sigue igual
  (un trabajador, sin `trabajador_ides`). (capa: unit)
- **R19.** `[D10]` Al acabar el preflight y al desbloquearse tras un corte,
  el botón debe volver al rótulo de su alcance, no a uno fijo. (capa: unit)
- **R20.** `[D5]` CUANDO el preflight es de un paquete, el modal debe llevar
  en el título «· N trabajadores (seleccionados | visibles)», una lista
  plegable con sus nombres (escapados) y, si quedan seleccionados ocultos,
  «K seleccionados ocultos por el filtro no se registran»; obras, avisos,
  casillas y sobrantes, como hoy. (capa: unit)
- **R21.** `[D5]` CUANDO termina `ejecutar` de un paquete, el aviso final
  debe empezar por «N trabajadores · » y seguir con el de hoy; ante un corte
  del proxy (502, 504, red), el comportamiento del hotfix. (capa: unit)
- **R22.** El front no debe decidir qué líneas se registran: solo manda los
  `ide` de los trabajadores; el cuerpo lleva las claves de hoy más
  `trabajador_ides`, ninguna otra. (capa: unit)

## 3. Regla del 100 % y obras compartidas

- **R23.** `[D6]` El sistema no debe bloquear ni avisar de nuevo por la
  regla del 100 % en el paquete: cada trabajador va entero (R1), así que su
  total es el del cuadrante, que no bloquea (regla 4 de ARCHITECTURE).
  (capa: unit)
- **R24.** CUANDO una obra tiene en su parte trabajadores de dentro y de
  fuera del paquete, el sistema no debe tocar ninguna línea de los de fuera
  (ni pisarla, ni ponerla a 0, ni contarla como sobrante); el parte que
  falte lo crea el primer registro y los siguientes lo reutilizan (paso 5
  del transfer). (capa: unit)

## 4. Documentación y verificación manual

- **R25.** `docs/ARCHITECTURE.md` (endpoints, `#regla-obra-cero`: «del
  periodo, de un trabajador o de un paquete», y que el front ya no pide el
  mes entero), `docs/INTEGRACION.md` y `azure-apps/dedicacion.md` deben
  describir `trabajador_ides` con su validación. (capa: unit)
- **R26.** En local y en **modo pruebas** (`OBRA_PRUEBAS_FORZAR=true`), el
  registro de un paquete de dos trabajadores debe escribir solo sus líneas
  en la 0404 y dejar igual las de un tercero del mismo parte (MANUAL del
  humano, tasks). (capa: integración)

## 5. Fuera de alcance

- La «otra forma» de registrar el mes entero desde la interfaz (la dejó el
  humano para más adelante; la ruta de la api sigue, design §5); registrar en
  segundo plano o el informe Excel (F-073); un atajo de teclado; pasar el
  modo trabajador a `trabajador_ides` (D8 b); un aviso del 100 % (D6 b/c).

## 6. Tests anteriores que cambian

**Ninguno** (lista cerrada). El filtro de un trabajador sigue siendo `==`
(R5; `test_f056_trabajador_ide.py` lo inspecciona); el front solo añade
`trabajador_ides` con paquete (`JSON.stringify` omite `undefined`), y el
rótulo se restaura desde `dataset.rotulo` con «Registrar en Sigrid» si falta
(design §6), que es lo que esperan `test_hotfix_registro_corte_proxy.py` y
`test_f049_ampliacion_registro.py` con sus dobles. Otro test en rojo ⇒ PARA
y `blocked`.
