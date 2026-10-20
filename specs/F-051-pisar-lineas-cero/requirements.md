<!-- specs/F-051-pisar-lineas-cero/requirements.md -->
# F-051 · Al registrar, pisar las líneas del parte al 0 % del recurso

Rigor **`critico`**; toca **solo `dedicacion-transfer`** y la documentación
(design §1). Pedida por el humano el 2026-10-08 («que también pise las líneas
de parte a 0 % que ya existan, ahora no lo hace»). **Decidido el 2026-10-20:**
D1 = C («nunca borramos lineas, editamos el valor»: la línea al 0 % se
**edita en su sitio**), D5 («cualquier linea a 0% se puede pisar») y el resto
de D2-D9 como se recomendó (design §9). **D10-D13 ABIERTAS** (design §9): los
R que dependen de ellas llevan su `[Dn]` y están escritos con la
**recomendación**. Fuera: recursos vinculados (F-044), obras donde el recurso
ya no tiene línea (D8), el pisado confirmado de hoy (D12), `partes`, api y
front.

## 0. Lo que hay en Sigrid (exploración, solo lectura, 2026-10-20)

Detalle en `progress/spec_F-051.md`. En corto:

- **Octubre de 2026, obra 0707, parte PT26/00370 (En registro):** líneas
  `M*` con `can = 0` de cuatro personas (`hmores` 410600 `MADM` CI.1.5,
  410931 `MENC` CI.1.3, 410935 y 410937 `MCAP` CI.1.8) y de sus recursos
  vinculados (`OTEL`, `OGAS`, `KM`, `MESVE`). Son **copia** de las de
  septiembre (PT26/00332, Cerrado): mismo recurso, hora, partida, cuenta y
  `pre`; `fec` = 31/10; sin `synckey` ni `tex`; sin enlaces de Sigrid; las
  mismas columnas que una línea nuestra. Las puso Administración.
- **Antes**: 18 líneas `M*` a 0 en 2024-2025, en partes hoy cerrados, cada
  una sola en su parte; ninguna de junio de 2025 a septiembre de 2026.
- **`partes` nunca ha escrito una línea `M*`** (sus 358 líneas son `H*` y
  `C*`, 9 de ellas a 0): con D3 ninguna línea suya es pisable hoy.
- **Por qué hoy no se pisa siempre.** `criterio_choque` solo ve la línea al
  0 % si coinciden recurso, hora **y partida**, y entonces pide confirmar
  un pisado (borrar e insertar). Con otra partida u otro código `M*` la línea
  a 0 se queda y la nuestra se añade al lado.

Glosario: **línea al 0 %** = hora `M*` (`es_linea_mensual`) y `can` 0 o nulo
(D4); **pisable** = la que cumple R1; **pisar** = **editar** la pisable para
que quede como la línea que habríamos insertado (R10, D1 = C, `[D10]`).

## 1. Qué línea al 0 % se pisa (transfer, preflight)

- **R1.** `[D11]` Una línea existente es **pisable** para una acción
  `escribir` si, y solo si: es del **mismo recurso**; es una línea al 0 %;
  vive en un parte **En registro** del periodo de la obra destino; su
  `synckey` no es de esta ejecución (`mias`) ni de `partes`; y, si la acción
  es de **postventa**, tiene su misma partida (D7). Hora `M*` y partida, en
  la obra normal, dan igual (D3); vacía o nuestra, la `synckey` también (D5).
- **R2.** Cada acción `escribir` pisa **como mucho una** línea, elegida de
  forma determinista entre las pisables aún libres de su recurso: primero la
  de su misma partida, después la de su misma hora, después la de menor
  `ide`. Las acciones del recurso se recorren por `registro_id`. Una acción
  sin pisable libre se **inserta** como hoy.
- **R3.** R1 y R2 viven en funciones puras de `reglas_porcentajes.py`, sin
  I/O; ninguna otra parte del código decide qué se pisa.
- **R4.** `[D2]` CUANDO una acción pisa, el preflight publica en ella
  `linea_cero` (`ide`, parte, hora, partida y `synckey` que tiene) y suma a
  su `aviso` que se **edita** esa línea al 0 % del parte. Si al recurso le
  quedan pisables sin acción, el aviso dice cuántas **se quedan a 0**. No
  es un conflicto: no sale en `conflictos` ni pide confirmación.
- **R5.** Una pisable no genera conflicto de pisado ni sale en el
  `contexto` de ningún conflicto; para la capacidad no suma (es 0).

## 2. Qué no se toca nunca

- **R6.** Ninguna línea de **otro recurso**, aunque esté al 0 % y en el mismo
  parte (teléfono, gasoil o vehículo vinculados: F-044).
- **R7.** Ninguna línea con `can` distinto de 0, con hora que no empiece por
  `M` (las incidencias `C*` de `partes` van a 0 por diseño) ni sin recurso.
- **R8.** En un parte **cerrado** no se edita nada; una línea al 0 % de un
  cerrado sigue la regla de hoy (si coincide por identidad, la acción se
  omite con `parte_cerrado`) (D6).
- **R9.** MIENTRAS el transfer está en **modo pruebas**, solo se miran los
  partes de la obra de pruebas: nunca se edita una línea de la obra real.

## 3. La edición (transfer, ejecutar)

- **R10.** `[D10]` CUANDO `ejecutar` escribe una acción con `linea_cero`, en
  vez de insertar **actualiza** esa línea en su sitio (mismo `ide`, `pos` y
  parte) con lo que habría insertado: `can`, `pre`, `tot`, hora, partida,
  cuenta analítica, `fec` y `synckey` nuestra. No se borra ninguna línea.
- **R11.** `[D11]` En modo pruebas la línea editada lleva `tex` = la marca de
  pruebas; en modo real conserva el `tex` que tenía.
- **R12.** La actualización lleva **guarda**: solo cambia la fila si sigue
  siendo del mismo recurso, `M*`, al 0 %, con la misma `synckey` que se leyó,
  sin enlaces de Sigrid (albarán, factura, dedicación, nómina) y en un parte
  En registro. Va en el mismo envío que las inserciones.
- **R13.** SI tras escribir la línea no aparece por su `synckey` (la guarda
  no la cambió), ENTONCES la acción sale de `escritas` y va a `omitidas` con
  un motivo que pide volver a registrar; no se inserta nada en su lugar.
- **R14.** Una acción retenida (omitida, ya registrada o con un aviso sin
  confirmar) no edita nada.
- **R15.** `[D13]` El resultado de `ejecutar` lista las editadas en
  `pisadas_cero` (`ide`, `registro_id`, parte y lo que tenía: hora, partida,
  `fec` y `synckey`); cada una deja un log con eso, sin nombres ni importes.
- **R16.** Idempotencia: reejecutar no edita ni inserta nada más (la línea
  editada ya lleva nuestra `synckey`: «ya registrada», P4). Si el envío falla
  a medias, reejecutar completa lo que faltó.

## 4. Lo que no cambia

- **R17.** Capacidad, sin partida, pisado por identidad (borrar e insertar,
  D12), idempotencia, cuenta analítica, elección del parte, propuesta de
  partida, postventa, VAR y empresa: como hoy, con las pisables fuera de los
  choques (R5). Ninguna lectura nueva de Sigrid.
- **R18.** api y front sin cambios: el aviso de R4 lo pinta el modal de hoy y
  la api reenvía las acciones y lee `escritas` y `omitidas` como siempre.

## 5. Documentación

- **R19.** `docs/ARCHITECTURE.md` gana la regla `#regla-cero` (fuente única:
  qué es pisable, emparejado, edición sin confirmar, guarda, cerrados),
  `#regla-conflicto` remite a ella y `test_f002_fuente_unica` la vigila.
- **R20.** `docs/INTEGRACION.md` (§1 y §7) dice que el transfer **edita** sin
  confirmar líneas `M*` al 0 % ajenas (su primer `UPDATE` en Sigrid); al
  desplegar se refresca `azure-apps/dedicacion.md` y se avisa a `partes`.

## 6. Verificación con el humano (MANUAL, modo pruebas)

- **R21.** En local con `OBRA_PRUEBAS_FORZAR=true`, con una línea al 0 % del
  recurso de prueba y otra de un segundo recurso en el parte En registro de
  la 0404 (creadas a mano en Sigrid, D9): registrar al recurso de prueba
  enseña el aviso de R4; tras **Registrar**, su línea conserva `ide` y `pos`
  y lleva el %, la partida, `PRUEBA-PORC` y nuestra `synckey`; no hay línea
  nueva; la del segundo recurso sigue a 0. Repetir: nada cambia (T11).
