<!-- specs/F-051-pisar-lineas-cero/requirements.md -->
# F-051 · Al registrar, pisar editando: nunca se borra una línea del parte

Rigor **`critico`**. Toca **los tres servicios**: sobre todo el transfer; la
api manda y guarda el `hmores.ide` (columna que ya existe) y el front cambia un
texto del modal (design §1). Pedida el 2026-10-08 («que también pise las
líneas de parte a 0 % que ya existan»). **Decisiones del humano del
2026-10-20** (design §9): editar en su sitio y nunca borrar (D1, D12),
cualquier línea al 0 % (D5), se editan todos los campos (D10), localizar lo
editado por `hmores.ide` sin cambiar la `synckey` de otro sistema (D11) y
guardar en el log lo que tenía la línea (D13); el resto, las recomendadas.
**D14-D15 ABIERTAS**: los R marcados están escritos con la recomendación.
Fuera: recursos vinculados (F-044), obras donde el recurso ya no tiene línea
(D8), el deshacer en sí (F-033) y `partes`.

## 0. Lo que hay en Sigrid (exploración, solo lectura)

Detalle en `progress/spec_F-051.md`. **Octubre de 2026, 0707, parte
PT26/00370 (En registro):** líneas `M*` a 0 de cuatro personas (`hmores`
410600, 410931, 410935, 410937) y de sus vinculados, copiadas por
Administración de septiembre con hora, partida, cuenta y `pre`, sin `synckey`.
`criterio_choque` solo las ve con la misma hora y partida, y entonces pide
confirmar un pisado que hoy **borra e inserta**. `partes` nunca ha escrito
una línea `M*`. Hay identidades repetidas: en 2026, 63 grupos de varias
líneas `M*` con el mismo recurso, hora y partida en un parte (PT26/00109,
`MDEL` día a día, hasta 9).

Glosario: **línea al 0 %** = hora `M*` y `can` 0 o nulo; **pisable** = R1;
**choque** = línea con la misma identidad (`#regla-conflicto`); **editar** =
`UPDATE` de la línea en su sitio con lo que habríamos insertado (R12).

## 1. Ninguna línea se borra

- **R1.** Una línea es **pisable** para una acción `escribir` si es del mismo
  recurso, al 0 %, en un parte **En registro** del periodo de la obra
  destino, su `synckey` no es de esta ejecución y, en postventa, tiene su
  partida (D3, D4, D5, D7). Lo deciden funciones puras de
  `reglas_porcentajes.py`.
- **R2.** Cada acción sin choque edita **como mucho una** pisable libre de su
  recurso (misma partida, después misma hora, después menor `ide`; acciones
  por `registro_id`). Sin pisable libre, se inserta como hoy.
- **R3.** `[D2]` La edición de una pisable no pide confirmación: el preflight
  publica `linea_cero` en la acción y un `aviso` que nombra la línea y su
  partida, y cuántas pisables del recurso **se quedan a 0**. Una pisable no
  es choque, no sale en ningún `contexto` y no suma a la capacidad.
- **R4.** `[D12]` Un choque sigue siendo un conflicto de pisado **a
  confirmar**, como hoy. Confirmado, la acción **edita** el choque de menor
  `ide` en vez de borrarlo e insertar; el conflicto publica qué `ide` edita.
- **R5.** `[D14]` Si el pisado tiene **varios** choques, la acción edita uno
  (R4) y los demás **se ponen a 0** (`can` y `tot` a 0, nada más); el
  conflicto lo publica y el modal lo dice.
- **R6.** El registro **no emite ningún `DELETE`** en ningún caso. El texto
  del modal para el pisado dice qué línea se edita y cuáles quedan a 0.
- **R7.** Nunca se toca una línea de otro recurso, de un parte cerrado (R8 de
  hoy: si choca con un cerrado, `parte_cerrado`), con hora no `M*` ni, en
  modo pruebas, fuera de la obra de pruebas.

## 2. Qué se escribe en la línea editada

- **R8.** `[D10 = B]` Se editan `can`, `pre`, `tot`, hora, partida, cuenta
  analítica y `fec`, con los mismos valores y redondeos que una inserción.
  No cambian `ide`, `pos`, parte, obra, centro ni periodo.
- **R9.** `[D11]` La `synckey` de **otro sistema** (no vacía y sin el prefijo
  `porcentajes:`) **no se cambia nunca**. Una vacía (Administración) o
  nuestra de otra asignación pasa a ser la de esta asignación (design §6.3).
- **R10.** `tex`: en modo pruebas, la marca de pruebas; en real, el que tenía.
- **R11.** Cada edición lleva **guarda**: solo cambia la fila si sigue siendo
  del recurso, `M*`, con el `can` y la `synckey` leídos justo antes de
  escribir, sin enlaces de Sigrid y en un parte En registro. Poner a 0 (R5),
  igual.
- **R12.** `ejecutar` lee **una vez**, justo antes de escribir, las líneas que
  va a editar o poner a 0. Una que ya no cumple su condición (pisable al 0 %,
  o choque con la misma identidad) no se envía: su acción va a `omitidas` con
  un motivo que pide volver a registrar.
- **R13.** SI tras escribir una línea editada no tiene lo escrito (la guarda
  no la cambió), ENTONCES su acción sale de `escritas` y va a `omitidas` con
  ese motivo; nunca se inserta en su lugar.

## 3. Localizar lo nuestro por `hmores.ide` (idempotencia)

- **R14.** La api manda en cada línea el `hmores_ide` que tenga la asignación
  (`asignacion.sigrid_hmores_ide`, columna existente); sin él, la línea viaja
  como hoy.
- **R15.** La línea es **ya registrada** si existe en Sigrid una fila con ese
  `ide`, del mismo recurso y cuya `synckey` no es nuestra de otra
  asignación; si no, si hay una fila con su `synckey` (como hoy). Las dos, en
  la **misma** lectura de hoy (por `synckey` **o** `ide`).
- **R16.** El resultado de `ejecutar` da el `hmores_ide` de cada escrita
  (editada o insertada) y, en `ya_registradas_ide`, el de cada ya
  registrada; la api lo guarda en `sigrid_hmores_ide` (así se completan las
  registradas antes de F-051).
- **R17.** Una línea editada o insertada que Administración borra deja de
  estar: el siguiente registro la vuelve a escribir (como hoy).

## 4. Traza y deshacer (D13)

- **R18.** Cada línea editada o puesta a 0 deja un log con su `ide`, parte,
  `registro_id` y **todo lo que tenía** (`can`, `pre`, `tot`, hora, partida,
  cuenta, `fec`, `synckey`, `tex`) y lo que queda; el resultado lo publica en
  `editadas` y `a_cero`. El deshacer lo hará F-033 con un `UPDATE` a ese
  estado; F-051 no deshace.

## 5. Lo que no cambia

- **R19.** Capacidad, sin partida, idempotencia de lo ya registrado, cuenta
  analítica, elección y alta del parte, propuesta de partida, postventa, VAR,
  empresa y modo pruebas: como hoy. El preflight hace las mismas lecturas;
  `ejecutar`, una más (R12). `borradas` sigue en la respuesta, siempre 0.
- **R20.** `limpiar` (script, solo obra de pruebas y lo marcado
  `PRUEBA-PORC`) sigue borrando `[D15]`; nada del registro lo usa.

## 6. Documentación y despliegue

- **R21.** `docs/ARCHITECTURE.md`: regla nueva `#regla-cero`, y
  `#regla-conflicto`, `#regla-analitica` y la descripción del transfer dicen
  «editar», no «borrar»; `test_f002_fuente_unica` vigila la nueva ancla.
- **R22.** `docs/INTEGRACION.md` §1, §5 y §7: el transfer **edita** líneas
  ajenas (su primer `UPDATE`), el contrato api↔transfer gana `hmores_ide` y
  el orden de despliegue es **transfer → api → front**. Al desplegar, se
  refresca `azure-apps/dedicacion.md` y se avisa a `partes`.

## 7. Verificación con el humano (MANUAL, modo pruebas, D9)

- **R23.** En local con `OBRA_PRUEBAS_FORZAR=true`, con líneas al 0 % del
  recurso de prueba y de otro recurso en el parte En registro de la 0404
  (creadas a mano en Sigrid): registrar edita la del recurso de prueba (mismo
  `ide` y `pos`, con el %, partida, `PRUEBA-PORC` y nuestra `synckey`), sin
  línea nueva, y la otra sigue a 0; cambiar el % en el cuadrante y registrar
  da un pisado a confirmar que, confirmado, edita **la misma** línea; repetir
  no cambia nada; ningún `DELETE` en el log (T15).
