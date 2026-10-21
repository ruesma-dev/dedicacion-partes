<!-- specs/F-030-dias-bajas-incidencias/requirements.md -->
# F-030 · Incidencias en el cuadrante: texto en la celda del % con desplegable

Rigor **`critico`**; front, api y transfer (design §1). Petición del humano
del 2026-10-20. **D1-D10 DECIDIDAS**; **anexo R30** (review 1, opción C del
humano, 2026-10-21) en §8, con **D11-D15 ABIERTAS** (§7). **Incidencia** = V,
B, AT, FJ, F, H o M (su `CI*` de `auxhor`); **línea de %** = la de hoy. Fuera
(D10): % por días, calendario, bandeja de `partes`, Excel y copias.

## 1. Lo de hoy no cambia
- **R1.** CUANDO en la celda del % se teclea algo **sin ninguna letra**
  (cifras, coma, punto, `%`, espacios o vacío) o se acepta el sugerido, el
  front hace lo de hoy: mismo %, total en vivo, guardado diferido, Enter al
  buscador de obra y, al salir en blanco, lo que falta hasta el 100 %.
- **R2.** El PUT de asignaciones, `domain/estados.py`, F7, F8, Copiar mes,
  Completar, Deshacer de los demás eventos y la decisión sobre cada línea de %
  en preflight y `ejecutar` no cambian, haya o no incidencias.

## 2. El catálogo, de una sola fuente: Sigrid
- **R3.** `[D1]` El sync de maestros y su preview leen de `auxhor` los `CI*`
  salvo `CIZ` (consulta en `config.yaml`) y los guardan en `tipo_incidencia`
  (`ide` de `auxhor`, código, nombre, letra, `activa`). Nada viene de `partes`.
- **R4.** `[D1]` Letra = el texto entre paréntesis al final de `auxhor.res`;
  nombre = lo de delante (`Vacaciones(V)` → `V`, `Vacaciones`); sin
  paréntesis, el código sin `CI` y `res` entero. Una función pura de la api.
- **R5.** Un código que deja de leerse o tiene fecha de baja queda
  `activa = false`; no se borra. **R6.** `GET /api/v1/incidencias` devuelve las
  activas por orden de letra (código, letra, nombre). **R7.** SI la lectura de
  `auxhor` falla o viene `truncated`, ENTONCES el sync falla sin persistir.

## 3. El desplegable en la celda del % (front; UX exacta en design §5)
- **R8.** CUANDO la celda del % tiene **al menos una letra**, se abre el panel
  de F-042 con las incidencias cuyo texto normalizado (letra y nombre, sin
  tildes ni mayúsculas) contiene lo tecleado, antes las de letra idéntica.
  **R9.** Abierto, % de la línea, total y guardado siguen como antes.
- **R10.** ↓/↑ mueven la activa (al abrir, la primera; siempre a la vista);
  Enter o Tab la eligen; el ratón, como en F-042. Sin coincidencias, «Ninguna
  incidencia con «…»» y Enter no hace nada. **R11.** Escape cierra y repone el
  valor de antes de la primera letra, sin guardar. **R12.** Sin letras, el
  panel se cierra y la celda sigue por R1.
- **R13.** `[D9]` Elegida en una línea **recién añadida** (la acaba de crear el
  buscador y el foco no ha salido de su %), esa línea de % se quita y queda la
  incidencia en su obra; en una que ya existía, el % no cambia.
- **R14.** `[D2]` Sale en el editor como chip «obra · letra nombre · del [ ]
  al [ ] · ✕» con el foco en «del»; Enter pasa a «al» y luego al buscador;
  Escape en un día, al buscador. **R15.** Sin PV ni suma en el total; ✕ la
  quita; días y quitar guardan con el mismo diferido.
- **R16.** En la tabla, una subfila más del trabajador tras sus líneas de %:
  en Obra, la obra y «letra del d al h»; Partida y % vacías. No cuenta en
  Total ni en el estado; el filtro de Obra la encuentra.

## 4. Guardar las incidencias (api)
- **R17.** `PUT /api/v1/periodos/{a}/{m}/trabajadores/{ide}/incidencias`
  sustituye las del trabajador en el periodo (`obra_ide`, `codigo`,
  `dia_desde`, `dia_hasta`, `id` de R36), deja un evento `INCIDENCIAS` con su
  `X-Usuario` y devuelve fila y resumen. `[D2]` `desde` vacío = 1, `hasta`
  vacío = último día. **R18.** 404 o periodo `CERRADO` (409): nada cambia.
- **R19.** SI un código no está activo, la obra no se ofrece como obra normal
  (`[D7]`: ni `Postv-` ni VAR), un día cae fuera del mes, `desde > hasta` o
  dos del trabajador comparten algún día, ENTONCES 422 sin tocar nada.
- **R20.** Deshacer un `INCIDENCIAS` las devuelve a su `snapshot_antes` (R47)
  con [`#regla-deshacer`] (solo el autor y el último evento, de cualquier tipo).
- **R21.** Cuadrante y fila llevan `incidencias` (id, obra, código, letra,
  nombre, desde, hasta, `quitada` y estado de registro). F7, F8, Copiar mes y
  Completar no las copian ni tocan. **R22.** `[D4]` **No cuentan para el
  100 %**: total, estado, desviación, resumen y Completar, como sin ellas.

## 5. Registro en Sigrid (api → transfer)
- **R23.** Al registrar (preflight, lote y ejecutar), la petición de cada obra
  lleva `incidencias` (id, recurso, empresa, código, desde, hasta, año, mes,
  `paride` `[D6]`, R39), aunque la obra solo tenga esas. Trabajador no vigente
  o no visible: como sus líneas ([`#regla-recurso`], [`#regla-empresa`]).
- **R24.** `[D5]` Cada una son **dos** líneas `hmores` en el parte del periodo
  de su obra ([`#regla-analitica`]): **inicio**, su `CI*` y `fec` = desde;
  **fin**, `CIZ` y `fec` = hasta; `can = tot = 0`, `pre` de `reshor`, `synckey`
  `porcentajes:inc:{id}:ini|fin` y cuenta analítica. `[D3]` Un `CIZ` por mes.
- **R25.** `[D6]` `paride` = la elegida o la propuesta guardada de la línea de
  % del trabajador en esa obra, si vale por `ide` (F-055); si no, 0.
- **R26.** SI el recurso no tiene en `reshor` el código o `CIZ`, ENTONCES se
  omiten **las dos** con un motivo que nombra el código.
- **R27.** `[D7]` SI en un parte del mes de **cualquier** obra (en pruebas,
  solo de la de pruebas) hay una línea del recurso con el mismo código y
  `fec`, ENTONCES esa no se escribe: «ya registrada» si es la nuestra (R40);
  si no, omitida «ya está en el parte X». La otra del par se decide sola.
- **R28.** Una línea de incidencia no es pisado, ni sobrecarga, ni «sin
  partida»: no avisa, no se confirma y no suma en [`#regla-capacidad`].
- **R29.** Modo pruebas, marca, empresa, parte En registro y alta protegida:
  como cualquier línea. **R30.** Cambiar los días de una ya registrada
  **edita** sus líneas (§8); nunca escribe otro par.
- **R31.** Preflight y ejecutar devuelven `incidencias`: por línea, id, rol
  (`ini`/`fin`), acción, `fec`, código, parte y motivo; la api guarda la traza
  en la incidencia (R39). **R32.** El modal de registro tiene la sección
  «Incidencias» (trabajador, obra, letra, días y qué se hará), sin confirmar.
- **R33.** R27 es **una** lectura por petición o lote, solo si hay
  incidencias; SI falla o viene `truncated`, ENTONCES no se escribe nada. El
  parte que «se creará» cuenta solo las que se escriben tras R27 (obs. 7).

## 6. Documentación y verificación
- **R34.** [`#regla-incidencia`] (`ARCHITECTURE.md`), fuente única de §5 y §8,
  vigilada por `test_f002`; P2-P4 remiten a ella. `INTEGRACION.md` y
  `azure-apps/dedicacion.md`: leemos `auxhor`, escribimos y editamos `CI*`/`CIZ`.
- **R35.** MANUAL en la `0404`, modo pruebas (T20, con R49).

## 7. Preguntas al humano
D1-D10 **decididas** (2026-10-20, todas la recomendada; `progress/
spec_F-030.md`). **Abiertas**, con alternativas y razones en design §11 (§8
va con la rec.): **D11** quitar una registrada (B: `quitada`); **D12** cambiar
su tipo y **D13** su obra (A: quitar + nueva); **D14** nuestra cambiada a mano
en Sigrid (A: no tocar); **D15** día nuevo con otra igual (A: no editar esa).

## 8. Anexo R30: cambiar una incidencia ya registrada (2026-10-21)
- **R36.** El PUT admite `id`: con él, la api conserva fila, `id` y traza
  aunque cambien los días; sin él, es nueva. SI el `id` no es del trabajador
  en el periodo, o una **registrada** (con algún `ide` en su traza) llega con
  otra obra o código (D12, D13), ENTONCES 422. **R37.** El front manda el `id`
  de las guardadas y, tras el PUT, toma de la respuesta el de las nuevas.
- **R38.** `[D11]` Una registrada que el PUT deja fuera no se borra: queda
  `quitada` con `id` y traza; no cuenta en solapes ni va al transfer; la
  tabla la pinta «quitada · sigue en Sigrid» y el modal la lista para
  retirarla a mano (parte e `ide`s). Una no registrada se borra como hoy.
- **R39.** La traza guarda por rol el `ide` y el día escritos, editados o ya
  registrados, y la api los manda con la incidencia (o nulos). Un `omitir` de
  una registrada solo guarda el motivo: ni la pasa a `omitido` ni los borra.
- **R40.** El transfer busca cada línea **nuestra** (su `ide` o su `synckey`,
  del recurso y con nuestra `synckey`) en la lectura de R33, con el estado de
  su parte; con la `fec` pedida, `ya_registrado`.
- **R41.** CUANDO se pide otra `fec` y la nuestra sigue en la registrada (o
  no consta), la acción es **`editar`**: `UPDATE` de **solo** su `fec`, con
  guarda (mismo `ide` y recurso, su código, `can` 0, la `synckey` leída, sin
  enlaces, parte En registro). Cada línea del par se decide sola.
- **R42.** `[D14]` SI la nuestra está fuera de la `fec` registrada, con otro
  código o `can` ≠ 0, ENTONCES no se toca: `omitir` «cambiada en Sigrid». La
  que ya no está (ni por `ide` ni por `synckey`) se escribe (F-051 R17).
- **R43.** SI su parte no está En registro, ENTONCES `omitir` «el parte X está
  cerrado: sigue del d al h»; nada va a otro parte. **R44.** `[D15]` SI otra
  línea del recurso con su código ya está en la `fec` nueva (sin contar las
  que la petición mueve), ENTONCES no se edita: `omitir` como en R27.
- **R45.** `ejecutar` relee lo que edita en la lectura de F-051 R12; SI una
  del par ya no cumple R41, ENTONCES no edita ninguna. Una editada sin su
  `fec` en la relectura va a `omitir`; nunca se inserta en su lugar.
- **R46.** El log de cada edición lleva `ide`, parte, incidencia, rol, todo lo
  leído en R45 y la `fec` nueva; preflight y `ejecutar` publican `editar` con
  `fec_antes` y el modal dice «se cambia del d al d».
- **R47.** El evento guarda `id` y `quitada`; deshacer repone cada una con su
  `id` y traza (el registro siguiente edita de vuelta su `fec`) y lo que
  quitaría una registrada la deja `quitada`. **R48.** `[D3]` Una incidencia
  no cambia de mes (R19): alargar el tramo es una nueva en el otro mes;
  vaciar un mes es quitarla (R38). Cada mes edita su par.
- **R49.** MANUAL (T20): en la `0404`, del 5 al 9, registrar, pasar al 6-12 y
  registrar: los mismos dos `ide`, `fec` 6 y 12 y ninguna línea nueva.
