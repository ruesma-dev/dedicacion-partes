<!-- specs/F-051-pisar-lineas-cero/requirements.md -->
# F-051 · Al registrar, pisar las líneas del parte al 0 % del recurso

Rigor **`critico`**; toca **solo `dedicacion-transfer`** y la documentación
(design §1). Pedida por el humano el 2026-10-08 («que también pise las líneas
de parte a 0 % que ya existan, ahora no lo hace»). **D1-D9 ABIERTAS** (design
§9): cada R que depende de una lleva su `[Dn]` y está escrito con la
**recomendación**; si el humano decide otra cosa, se reescribe antes de
implementar. Fuera: recursos vinculados (F-044), obras donde el recurso no
tiene línea este mes (D8), `partes`, api y front.

## 0. Lo que hay en Sigrid (exploración, solo lectura, 2026-10-20)

Detalle, consultas y cifras en `progress/spec_F-051.md`. En corto:

- **Octubre de 2026, obra 0707, parte PT26/00370 (En registro):** líneas
  `M*` con `can = 0` de cuatro personas (`hmores` 410600 `MADM` CI.1.5,
  410931 `MENC` CI.1.3, 410935 y 410937 `MCAP` CI.1.8) y de sus recursos
  vinculados (`OTEL`, `OGAS`, `KM`, y `MESVE` de un vehículo). Son **copia**
  de las del parte de septiembre PT26/00332 (Cerrado): mismo recurso, hora,
  partida y cuenta (`caaide`), `fec` = 31/10, **sin `synckey`** ni `tex`, sin
  enlaces de Sigrid. Las escribió Administración a mano o con una función de
  copia de Sigrid (no se distingue en la base: D9).
- **Antes**, 2024-2025: 18 líneas `M*` a 0 en partes hoy cerrados (GG y
  obras), cada una **sola** (su recurso sin otra línea `M*` en ese parte);
  ninguna de junio de 2025 a septiembre de 2026.
- **Por qué hoy no se pisa siempre.** Una línea al 0 % es para
  `criterio_choque` una línea más ([`#regla-conflicto`](../../docs/ARCHITECTURE.md#regla-conflicto)):
  solo choca si coinciden recurso, hora **y partida**; entonces es un pisado
  **a confirmar**. Con otra partida (elegida, o propuesta distinta, como
  pasaba antes de F-050) o con otro código `M*` no choca: la línea a 0 se
  queda y la nuestra se añade al lado. La capacidad no avisa (suma 0).

Glosario: **línea al 0 %** = línea de parte con hora `M*`
(`es_linea_mensual`) y `can` 0 o nulo; **pisable** = la que cumple R1;
**pisar** = borrar la pisable y escribir la nuestra (R5, `[D1]`).

## 1. Qué línea al 0 % se pisa (transfer, preflight)

- **R1.** `[D3, D5, D7]` Una línea existente es **pisable** para una acción
  `escribir` si, y solo si: es del **mismo recurso**; es una línea al 0 %;
  su `synckey` está vacía; vive en un parte **En registro** del periodo de
  la obra destino de la acción; y, si la acción es de **postventa**, tiene su
  misma partida. Hora `M*` y partida, en la obra normal, dan igual.
- **R2.** Las pisables se deciden en **una** función pura de
  `reglas_porcentajes.py`, sin I/O, que el pipeline usa en el preflight;
  ninguna otra parte del código decide qué es pisable.
- **R3.** `[D2]` CUANDO una acción `escribir` tiene pisables, el preflight
  publica en ella `lineas_cero` (los `ide`, ordenados) y suma a su `aviso`
  un texto que dice cuántas líneas al 0 % sustituye y en qué parte(s). **No**
  es un conflicto: no sale en `conflictos` ni pide confirmación.
- **R4.** Una pisable que además coincide por identidad (los cuatro campos)
  **no** genera conflicto de pisado ni aparece en el `contexto` de ningún
  conflicto; para la capacidad cuenta como pisada (no suma).
- **R5.** Varias acciones del mismo recurso en la misma obra y periodo
  (varias partidas) publican las **mismas** pisables, que se borran una vez.

## 2. Qué no se toca nunca

- **R6.** Una línea de **otro recurso** no es pisable, aunque esté al 0 % y
  en el mismo parte (el teléfono, gasoil o vehículo vinculados: F-044).
- **R7.** No es pisable una línea con `can` distinto de 0, con `synckey`
  (nuestra o de `partes`), con hora que no empiece por `M`, ni sin recurso.
- **R8.** `[D6]` En un parte **cerrado** (todo lo que no es En registro) no
  se pisa nada. Una línea al 0 % de un cerrado se trata **como hoy**: si
  coincide por identidad, la acción se omite con `parte_cerrado`; si no, no
  hace nada.
- **R9.** MIENTRAS el transfer está en **modo pruebas**, solo se miran los
  partes de la obra de pruebas (son los de la obra destino): nunca se pisa
  una línea de la obra real.

## 3. El borrado (transfer, ejecutar)

- **R10.** `[D1]` CUANDO `ejecutar` escribe al menos una acción del recurso
  en esa obra y periodo, borra antes de insertar las pisables de esas
  acciones, cada una **una sola vez**, en el mismo envío que las inserciones
  (las sentencias de borrado van delante, como las de los pisados).
- **R11.** SI ninguna acción del recurso en esa obra y periodo se escribe
  (omitida, ya registrada o retenida por un aviso sin confirmar), ENTONCES
  no se borra ninguna de sus pisables.
- **R12.** El borrado lleva **guarda**: solo borra si la línea sigue siendo
  del mismo recurso, al 0 %, sin `synckey`, sin enlaces de Sigrid (albarán,
  factura, dedicación, nómina) y en un parte En registro. Si algo cambió, no
  borra nada y la inserción sigue.
- **R13.** El resultado de `ejecutar` cuenta las pisadas en `borradas` y las
  lista en `pisadas_cero` (`ide`); cada una deja un log con `ide`, parte y
  recurso, sin nombres ni importes.
- **R14.** Idempotencia: reejecutar lo mismo no borra ni escribe nada más
  (la línea nuestra ya está por `synckey`, P4; las pisadas ya no existen).
  Si el envío falla tras borrar, reejecutar escribe la nuestra sin borrar
  nada.

## 4. Lo que no cambia

- **R15.** Capacidad, sin partida, pisado por identidad, idempotencia por
  `synckey`, cuenta analítica, elección del parte, propuesta de partida,
  postventa, VAR y empresa: como hoy, con las pisables fuera de los choques
  (R4). Las lecturas de Sigrid son las mismas (ninguna nueva).
- **R16.** api y front sin cambios: el aviso de R3 lo pinta el modal de hoy
  (`a.aviso`) y la api reenvía las acciones tal cual.

## 5. Documentación

- **R17.** `docs/ARCHITECTURE.md` gana la regla con ancla `#regla-cero`
  (fuente única: qué es pisable, sin confirmación, guarda, fuera los
  cerrados), `#regla-conflicto` remite a ella y `test_f002_fuente_unica`
  la vigila (`ANCLAS`).
- **R18.** `docs/INTEGRACION.md` (§1 y §7) dice que el transfer **borra sin
  confirmar** las líneas `M*` al 0 % de Administración del recurso que
  registra; al desplegar se refresca `azure-apps/dedicacion.md` y se avisa
  a `partes` (mismo parte; ellos no escriben `M*`).

## 6. Verificación con el humano (MANUAL, modo pruebas)

- **R19.** `[D9]` En local, transfer con `OBRA_PRUEBAS_FORZAR=true`: con una
  línea al 0 % del recurso de prueba y otra al 0 % de un segundo recurso en
  el parte En registro de la 0404 del mes de prueba, registrar al recurso de
  prueba: el modal enseña el aviso de R3; tras **Registrar**, la suya ya no
  está, la nuestra sí (`PRUEBA-PORC`), y la del segundo recurso sigue.
  Repetir: nada cambia. Comandos en tasks.md (T10).
