<!-- specs/F-030-dias-bajas-incidencias/requirements.md -->
# F-030 · Incidencias en el cuadrante: texto en la celda del % con desplegable

Rigor **`critico`**; front, api y transfer (design §1). Petición del humano
del 2026-10-20 en `features.json`. **D1-D10 PENDIENTES** (§7): las R con
`[Dn]` llevan la recomendación. Evidencia de Sigrid: design §10.

Glosario: **incidencia** = V, B, AT, FJ, F, H o M, con su `CI*` de `auxhor`;
**línea de %** = la asignación de hoy. **Fuera** (D10): % por días, calendario
de convenio, bandeja de `partes` (su F-019), Excel y copias de incidencias.

## 1. Lo de hoy no cambia

- **R1.** CUANDO en la celda del % se teclea un valor **sin ninguna letra**
  (cifras, coma, punto, `%`, espacios o vacío), el front debe hacer
  exactamente lo de hoy: el mismo % en la línea, el mismo total en vivo, el
  mismo guardado diferido, Enter al buscador de obra y, al salir en blanco, lo
  que falta hasta el 100 %. También al aceptar el % sugerido.
- **R2.** El PUT de asignaciones, `domain/estados.py`, F7, F8, Copiar mes,
  Completar, Deshacer de los demás eventos y la decisión sobre cada línea de %
  en preflight y `ejecutar` no cambian, haya o no incidencias.

## 2. El catálogo, de una sola fuente: Sigrid

- **R3.** `[D1]` El sync de maestros y su preview leen de `auxhor` los `CI*`
  salvo `CIZ` (consulta en `config.yaml`) y los guardan en `tipo_incidencia`
  (`ide` de `auxhor`, código, nombre, letra, `activa`). Nada viene de `partes`.
- **R4.** `[D1]` La letra es el texto entre paréntesis al final de
  `auxhor.res` y el nombre, lo que va delante (`Vacaciones(V)` → `V`,
  `Vacaciones`); sin paréntesis, la letra es el código sin `CI` y el nombre,
  `res` entero. Una sola función pura de la api.
- **R5.** Un código que deja de leerse o tiene fecha de baja queda
  `activa = false`; no se borra. **R6.** `GET /api/v1/incidencias` devuelve las
  activas por orden de letra (código, letra, nombre).
- **R7.** SI la lectura de `auxhor` falla o viene `truncated`, ENTONCES el sync
  falla como con cualquier maestro, sin persistir nada.

## 3. El desplegable en la celda del % (front)

- **R8.** CUANDO el valor de la celda del % contiene **al menos una letra**, el
  front debe abrir junto a ella el panel de sugerencias de F-042 con las
  incidencias del catálogo cuyo texto normalizado (letra y nombre, sin tildes
  ni mayúsculas) contiene lo tecleado: antes las de letra idéntica.
- **R9.** MIENTRAS el panel de incidencias está abierto, el % de la línea, el
  total en vivo y el guardado siguen como antes de la primera letra.
- **R10.** ↓ y ↑ mueven la activa (al abrir, la primera; siempre a la vista);
  Enter o Tab eligen la activa; el ratón elige como en F-042. Sin
  coincidencias, una fila «Ninguna incidencia con «…»» y Enter no hace nada.
- **R11.** Escape cierra el panel y devuelve la celda al valor de antes de la
  primera letra, sin guardar. **R12.** Si se borran todas las letras, el panel
  se cierra y la celda sigue por R1 con lo que quede.
- **R13.** `[D9]` CUANDO se elige una incidencia en una línea **recién añadida**
  (la acaba de crear el buscador de obra y el foco no ha salido de su %), esa
  línea de % se quita y queda la incidencia en su obra; en una línea que ya
  existía, su % no cambia y la incidencia se añade aparte en esa obra.
- **R14.** `[D2]` La incidencia elegida sale en el editor como un chip «obra ·
  letra nombre · del [ ] al [ ] · ✕» con el foco en «del»; Enter pasa a «al» y
  Enter vuelve al buscador de obra. Escape en un día vuelve al buscador.
- **R15.** El chip no tiene PV ni suma en el total en vivo; ✕ la quita; días
  y quitar guardan con el mismo diferido.
- **R16.** En la tabla, cada incidencia es una subfila más del trabajador,
  detrás de sus líneas de %: en Obra, la obra y «letra del d al h»; Partida y %
  vacías. No cuenta en Total ni en el estado; el filtro de Obra la encuentra.

## 4. Guardar las incidencias (api)

- **R17.** `PUT /api/v1/periodos/{a}/{m}/trabajadores/{ide}/incidencias`
  sustituye las incidencias del trabajador en el periodo (`obra_ide`, `codigo`,
  `dia_desde`, `dia_hasta`), deja un evento `INCIDENCIAS` con su `X-Usuario` y
  devuelve la fila y el resumen como el PUT de asignaciones. `[D2]` Día
  `desde` vacío = 1; `hasta` vacío = último día del mes.
- **R18.** SI el periodo o el trabajador no existen (404) o el periodo está
  `CERRADO` (409), ENTONCES no se toca nada, como en asignaciones.
- **R19.** SI un código no está activo en `tipo_incidencia`, la obra no se
  ofrece como obra normal (`[D7]`: ni `Postv-` ni entrada VAR), un día cae
  fuera del mes, `desde > hasta` o dos incidencias del trabajador comparten
  algún día, ENTONCES 422 con el motivo y no se toca nada.
- **R20.** Deshacer un evento `INCIDENCIAS` devuelve las incidencias del
  trabajador a su `snapshot_antes`, con [`#regla-deshacer`] (solo el autor y
  solo el último evento pendiente, sea del tipo que sea).
- **R21.** El cuadrante y la fila llevan por trabajador `incidencias` (id,
  obra, código, letra, nombre, desde, hasta y estado de registro). F7, F8,
  Copiar mes y Completar no las copian ni las tocan.
- **R22.** `[D4]` Las incidencias **no cuentan para el 100 %**: total, estado,
  desviación, resumen y Completar salen como si no existieran.

## 5. Registro en Sigrid (api → transfer)

- **R23.** Al registrar (preflight, también en lote, y ejecutar), la api manda
  en la petición de la obra de cada incidencia una lista `incidencias` (id,
  recurso, empresa, código, desde, hasta, año, mes, `paride` `[D6]`). Una obra
  solo con incidencias también va. Las de un trabajador no vigente o no
  visible, como sus líneas ([`#regla-recurso`], [`#regla-empresa`]).
- **R24.** `[D5]` Cada incidencia son **dos** líneas `hmores` en el parte del
  periodo de su obra ([`#regla-analitica`]): el **inicio** con su `CI*` y `fec`
  = desde; el **fin** con `CIZ` y `fec` = hasta (el mismo día si dura uno);
  `can = 0`, `tot = 0`, `pre` = el de `reshor` del recurso para ese código,
  `synckey` `porcentajes:inc:{id}:ini` / `:fin` y la cuenta analítica como
  cualquier línea. `[D3]` Cada mes cierra su tramo con su `CIZ`.
- **R25.** `[D6]` `paride` = la elegida o la propuesta guardada de la línea de
  % del trabajador en esa obra, si la hay y vale por `ide` (F-055); si no, 0,
  sin aviso ni confirmación.
- **R26.** SI el recurso no tiene en `reshor` el código de la incidencia o
  `CIZ`, ENTONCES se omiten **las dos** líneas con un motivo que nombra el
  código: nunca un inicio sin su fin.
- **R27.** `[D7]` SI en algún parte del mes de **cualquier** obra (en modo
  pruebas, solo de la obra de pruebas) ya hay una línea del recurso con el
  mismo código y la misma `fec`, ENTONCES esa línea no se escribe: «ya
  registrada» si la `synckey` es la suya; si no, omitida «ya está en el parte
  X», sea de Administración o de `partes`. La otra del par se decide sola.
- **R28.** Una línea de incidencia no es pisado, ni sobrecarga, ni «sin
  partida»: no avisa, no se confirma y no suma en [`#regla-capacidad`].
- **R29.** Modo pruebas, obra de pruebas, marca `PRUEBA-PORC`, empresa, parte
  En registro y alta protegida: como cualquier línea. **R30.** Una incidencia
  ya registrada no se reescribe aunque cambien sus días (eso es F-033).
- **R31.** Preflight y ejecutar devuelven `incidencias`: por línea, id, rol
  (`ini`/`fin`), acción, `fec`, código, parte y motivo. La api guarda en la
  incidencia su traza (estado, parte, `ide` de las dos líneas y motivo).
- **R32.** El modal de registro enseña una sección «Incidencias» (trabajador,
  obra, letra, días y qué se hará), sin confirmaciones.
- **R33.** La comprobación de R27 es **una** lectura por petición o lote, y
  solo si hay incidencias. SI falla o viene `truncated`, ENTONCES la petición
  falla sin escribir nada.

## 6. Documentación y verificación

- **R34.** `docs/ARCHITECTURE.md` gana [`#regla-incidencia`], única fuente de
  §5, y `test_f002_fuente_unica.py` la vigila; P2, P3 y P4 remiten a ella como
  excepción. `docs/INTEGRACION.md` y `azure-apps/dedicacion.md`: leemos
  `auxhor` y escribimos `CI*`/`CIZ` con `synckey porcentajes:inc:`.
- **R35.** MANUAL: preflight, ejecutar, verificar y limpiar una incidencia en
  modo pruebas en la `0404` (tasks T20).

## 7. Preguntas al humano (alternativas y evidencia: design §11)

- **D1. Fuente de la lista.** Rec. **A**: `auxhor` de Sigrid (7 códigos con
  la letra en `res`, los de `partes`). B: copiar su `incidencias.yaml`.
- **D2. Fechas.** Rec. **A**: tramo del mes obligatorio, Enter en vacío = mes
  entero. B: sin fechas y sin registrar. C: solo el día de inicio.
- **D3. Tramo que cruza meses.** Rec. **A**: cada mes con su `CIZ`. B: sin
  `CIZ` si llega a fin de mes (como Administración en bajas largas).
- **D4. 100 %.** Rec. **A**: no cuenta. B: resta días del % (va con D10).
- **D5. Qué se escribe.** Rec. **A**: par `CI*`/`CIZ`, `can = 0`. B: inicio.
- **D6. Partida.** Rec. **A**: la de la línea de % de esa obra o 0. B: 0.
- **D7. Duplicados y obras.** Rec. **A**: R27 en todas las obras del mes y
  solo obra normal. B: comparar solo en la obra destino.
- **D8. Alcance.** Rec. **A**: captura y registro aquí. B: partir en dos.
- **D9. Línea recién añadida.** Rec. **A**: R13. B: el % siempre se queda.
- **D10. % por días, calendario de convenio y bandeja de `partes`.** Rec.:
  **fuera**, en features nuevas que propone el líder.
