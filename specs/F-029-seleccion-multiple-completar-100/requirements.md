<!-- specs/F-029-seleccion-multiple-completar-100/requirements.md -->
# F-029 · Selección múltiple con Ctrl/Shift y completar hasta el 100 % en la obra filtrada

Rigor **`estandar`**. Servicios: **`dedicacion-api`** (regla y lote) y
**`dedicacion-front`** (selección, diálogo, botón, atajo); el **transfer no se
toca** y **nada se escribe en Sigrid** (design §1). Decidido por el humano:
completa hasta el 100 % con el cálculo en la API, por lote (2026-09-29); va
antes que F-021 con el filtro «Filtrar obra…» de hoy, y Sesame queda para
F-021, que alimentará la misma selección (2026-10-05, R7).

Glosario. **Cursor**: `state.seleccionIde`, como hoy. **Selección múltiple**:
`ide` marcados con Ctrl/Shift. **Selección efectiva**: la múltiple ∩ visibles;
sin múltiple, el cursor (D6). **Destino**: obra + modo (normal o `Postv-`).
**Lo que falta**: 100 − total del mes sobre **todas** sus líneas. **E**: F-024.

## 1. Selección múltiple (front)

- **R1.** CUANDO el usuario hace Ctrl+clic (Cmd+clic en Mac) en una fila, el
  sistema debe añadirla a la selección múltiple si no estaba y quitarla si
  estaba, sin abrir el editor. Si la selección estaba vacía, el cursor entra
  antes en ella. El cursor y el ancla pasan a la fila clicada.
- **R2.** CUANDO el usuario hace Shift+clic, la selección múltiple debe pasar a
  ser el rango de filas **visibles**, en el orden en que se ven, entre el ancla
  y la fila clicada, ambas incluidas, sin abrir el editor ni seleccionar texto.
- **R3.** Las filas de la selección múltiple deben verse marcadas con una clase
  propia, distinta de la del cursor, y el contador debe añadir «· N
  seleccionados» cuando N > 0.
- **R4.** CUANDO el usuario hace clic simple en una fila, el sistema debe vaciar
  la selección múltiple y hacer lo de hoy (cursor y, si ABIERTO, editor).
- **R5.** Con o sin selección múltiple, ↑ ↓, Enter, R, F7, F8, Ctrl+Z, «/» y la
  secuencia «% Enter obra Enter» del editor deben actuar **exactamente como
  hoy**, sobre el cursor o el editor. Esc con el editor cerrado y fuera de un
  campo vacía la selección múltiple.
- **R6.** CUANDO cambia el mes o la empresa, o un lote termina sin error, la
  selección múltiple debe quedar vacía.
- **R7.** La selección múltiple debe ser un conjunto de `ide` independiente de
  los filtros, y solo la deben modificar dos funciones: `marcarSeleccion` (los
  clics) y `fijarSeleccion(ides)` (la puerta por la que F-021 la llenará).

## 2. Lanzar la acción (front)

- **R8.** DONDE el periodo esté ABIERTO y la selección efectiva no esté vacía,
  el botón «Completar al 100 %» y el atajo (D4) deben abrir el diálogo de la
  acción. Con el periodo CERRADO el botón está desactivado y el atajo no hace
  nada; con el editor abierto, el atajo tampoco.
- **R9.** El lote debe mandarse con la selección efectiva (D6), y el diálogo
  decir cuántos seleccionados quedan fuera por estar ocultos.
- **R10.** El destino se elige en el diálogo entre las entradas del catálogo del
  cuadrante (`state.catalogoObras`, el del autocompletado: solo ofrecibles,
  normal y `Postv-` como entradas distintas, D2) que casan con el texto de
  «Filtrar obra…», con la misma comparación que el autocompletado (D1). Una
  sola: elegida. Varias: la de código exacto primero, y ↑ ↓ Enter. Ninguna o
  sin filtro: se escribe en el campo.
- **R11.** El diálogo debe enseñar el destino (código, `Postv-` si aplica,
  descripción) y los nombres a los que se mandará, y llamar a la API solo al
  confirmar (Enter o botón). Esc cancela sin llamar. Las teclas del diálogo no
  llegan al manejador global (`teclas`).
- **R12.** El front no debe calcular cifras: manda `trabajadores`, `obra_ide` y
  `es_postventa`; ni porcentajes ni «lo que falta».
- **R13.** CUANDO la API responde 200, el front debe enseñar el resultado de cada
  trabajador con su nombre (completado y cuánto; sin cambios por estar al
  100 % o por encima; no vigente; no visible) y recargar el cuadrante. SI hay
  error, enseña su motivo y conserva la selección.

## 3. La operación por lote (API)

- **R14.** `POST /api/v1/periodos/{anio}/{mes}/completar` debe aceptar
  `{trabajadores: [ide], obra_ide, es_postventa}` (por defecto `false`) y la
  empresa por query como el resto de rutas del periodo (422 si no es un
  entero > 0, sin abrir UoW). `trabajadores`: de 1 a 500; un `ide` repetido se
  procesa una vez, en el orden de llegada. Campos extra: 422.
- **R15.** Para cada trabajador en `FALTA` o `SIN_CARGA` (según
  `calcular_estado`, con la épsilon compartida de la regla del 100 %), el
  sistema debe poner en el destino lo que falta: si ya tiene línea con la
  misma clave (obra, `es_postventa`), sumándolo a ella; si no, con una línea
  nueva. Sus demás líneas no cambian (obra, modo y porcentaje).
- **R16.** Tras completar, el total del trabajador debe ser exactamente 100,00 y
  su estado `OK` (D5).
- **R17.** SI el trabajador está en `OK` o en `EXCESO`, ENTONCES no se toca ni se
  registra evento, y su resultado es `YA_AL_100` o `EXCESO`.
- **R18.** Completar en `Postv-X` no debe sumar a la línea normal de X, ni al
  revés: `es_postventa` es parte de la clave (`#regla-p5`).
- **R19.** Cada trabajador cambiado debe dejar **un** evento, tipo `COMPLETAR`,
  con el usuario de `X-Usuario` y los snapshots en el formato de guardar.
  Deshacerlo (`#regla-deshacer`) devuelve su fila a lo de antes del lote, y
  `puede_deshacer` es verdadero para quien lanzó el lote y falso para otro.
- **R20.** El lote debe ser una sola transacción: SI falla una validación
  global (R21, R22), ENTONCES no se escribe nada ni se registra ningún evento.
- **R21.** SI el periodo no existe, 404; SI está CERRADO, 409.
- **R22.** SI la obra no existe, no es de la empresa de las obras
  (`#regla-empresa`) o no se ofrece en ese modo (`Linea.ofrecible`: normal si
  `activa`, `Postv-` si `admite_postventa`), ENTONCES 422 con el motivo y no se
  toca a nadie (D3).
- **R23.** SI un `ide` no existe o no es visible en E, ENTONCES su resultado es
  `NO_VISIBLE` y el lote sigue con los demás.
- **R24.** SI un trabajador no está vigente en el mes (`activo` falso en el
  cuadrante, `#regla-recurso`), ENTONCES su resultado es `NO_VIGENTE`, no se
  toca y el lote sigue (D3).
- **R25.** La respuesta debe traer `resultados` (uno por `ide` distinto, en el
  orden de llegada: `trabajador_ide`, `resultado` y `anadido` en escala 0-100,
  0 si no se tocó) y el `resumen` de E después del lote.
- **R26.** El lote no debe llamar al transfer ni a `sigrid-api`.
- **R27.** (Documentación) `ARCHITECTURE.md` debe tener `#regla-completar`
  (punto 15) y la ruta; `INTEGRACION.md` §5 y el README de la api, la ruta.

## 4. Tests anteriores que cambian: lista CERRADA

**Ninguno.** Comprobado ejecutando el 2026-10-05 un prototipo desechable de
este diseño (worktree aparte, ya borrado; api, `TipoEvento`, punto 15 de
ARCHITECTURE, `app.js`, `index.html`, `styles.css`): api 535, front 28,
transfer 379 y raíz 418 (+1 omitido) pasados, cero fallos. Los dobles de F-024
no se editan (design §6). Si al implementar cambia alguno, se para.

## 5. Verificación MANUAL (humano)

`tasks.md` T9, con pasos exactos: local, sin Sigrid; clics, diálogo y teclado.

## 6. Decisiones abiertas (las valida el humano antes de implementar)

- **D1 · Cómo se elige el destino.** A) Diálogo con las entradas del catálogo
  que casan con el filtro: una, elegida; varias, se elige; ninguna, se escribe
  (R10). B) Solo si casa una entrada exacta; si no, no se lanza y se pide
  afinar el filtro. C) Tomar en cada fila el chip que casa: cada trabajador
  podría ir a una obra distinta. **Recomendada A**: parte del filtro y, si casa
  varias (`0656` casa `0656` y `Postv-0656`) o ninguna, hay salida.
- **D2 · Normal o `Postv-`.** A) Lo dice la entrada elegida del catálogo, como
  en el editor. B) Solo normal. C) Normal con conmutador PV en el diálogo.
  **Recomendada A**: un solo mecanismo, con los modos que marca la API.
- **D3 · No vigente y obra no ofrecible.** No vigente: A) no se toca y se dice
  (R24); B) se completa, como permite guardar. Obra no ofrecible: A) 422
  entera (R22); B) sumar solo a quien ya tiene la línea (D5 de F-025).
  **Recomendadas A y A**: copia y registro ya dejan fuera al no vigente, y el
  front nunca ofrece una obra no ofrecible.
- **D4 · Botón y atajo** (ocupadas: ↑ ↓ Enter Esc / R F7 F8 Ctrl+Z). A) Botón
  «Completar al 100 %» y tecla **C** sin modificadores, editor cerrado y fuera
  de campo, como R. B) Botón y F9. C) Solo botón. **Recomendada A**: C está
  libre, no pisa Ctrl+C y solo abre el diálogo.
- **D5 · Precisión.** A) Lo que falta = 100 − total a 0,01 (`Numeric(6,2)`:
  resta exacta, total 100,00); si se toca lo decide `calcular_estado` (épsilon
  0,005), así que falta 0,01 se completa. B) Umbral propio (no completar si
  falta < 0,5). C) Redondear a entero. **Recomendada A**: B es un tercer
  criterio de «al 100 %» frente a API y transfer (`#regla-capacidad`), y C deja
  `FALTA` o `EXCESO` residual.
- **D6 · Seleccionados ocultos por los filtros.** A) Solo la selección efectiva
  (visibles); el diálogo cuenta los ocultos (R9). B) Todos, ocultos incluidos,
  listados en el diálogo. C) Vaciar la selección al cambiar un filtro.
  **Recomendada A**: se toca lo que se ve (para F-021: lo que Sesame
  preseleccione tendrá que estar visible).
