<!-- specs/F-069-importe-caja-km/requirements.md -->
# F-069 · Importe mensual de caja de obra, km y viajes, repartido por %

Rigor **`critico`** (cambia lo que el transfer escribe en Sigrid). Toca **los
tres servicios** (design §1). Es una enmienda de F-044 R14: algunos tipos de
vinculado ya no toman el precio de `reshor.pre`, sino un **importe del mes**
que se teclea. **Decisiones abiertas D1-D9** en design §9; cada `[Dn]` remite
a una de ellas y **los requisitos están escritos con mi recomendación**: si el
humano elige otra opción, se reescribe el requisito antes de implementar.
Fuera: mensajería (F-052), el ajuste del % por alta o baja (F-071, ver design
§10), el informe Excel (F-073), deshacer en Sigrid (F-033) y `partes`.

## 0. Lo que hay hoy (contexto)

- F-044 R14: un vinculado sin `pre` en su hora por defecto se omite «sin
  importe mensual». Les pasa a todos los `CAJA` y `VIAJE` y a 44 de los 45
  `VP` (`KM`) (`progress/explore_F-044_sigrid.md` §1).
- Registro de octubre de 2026 (10/11): de 521 líneas no escritas, 300 son
  «sin importe mensual» (caja 177, viaje 74, VP 49). Hay además 29 vinculados
  caja/VP con una línea hecha a mano en el parte con el gasto real.
- Las líneas `KM` hechas a mano en 2026 llevan `can` = % del titular,
  `pre` = importe del mes (cambia cada mes) y `tot = can × pre`
  (explore F-044 §3: `tot = can × pre` en 489 de 489).
- Glosario: **vinculado de importe** = un vinculado vigente cuyo tipo está en
  la lista de tipos de importe (R1); **importe del mes** = la cantidad en €
  que se teclea para ese vinculado y ese periodo.

## 1. Qué vinculados llevan importe (api)

- **R1.** `[D1]` El sistema debe leer de `config.yaml`
  (`sync.vinculados.tipos_importe`) la lista de tipos de recurso
  (`auxrestip.cod`) que van por importe del mes, hoy `[CAJA, VP, VIAJE]`.
  Mal escrita (no es una lista de textos), la api no arranca.
- **R2.** El sistema debe decidir si un vinculado es de importe con **una**
  función pura de `dedicacion-api/domain/importes.py`, comparando su tipo sin
  espacios y en mayúsculas. Un tipo fuera de la lista se registra como hoy.

## 2. Guardar el importe (api)

- **R3.** `[D7]` El importe del mes se guarda en la tabla nueva
  `importe_vinculado` (periodo × vinculado, único), declarada en
  `orm_models.py`, con usuario y fecha del último cambio.
- **R4.** CUANDO llega `PUT /api/v1/periodos/{a}/{m}/trabajadores/{ide}/
  importes` con `{importes: [{vinculado_ide, importe}]}`, el sistema debe
  sustituir los importes de los vinculados de ese trabajador en el periodo:
  un número los guarda; `null` lo borra (vuelve a «falta»); un vinculado que
  no viene no se toca.
- **R5.** `[D2]` El importe es en **euros**, con dos decimales como mucho,
  ≥ 0 y ≤ 999.999,99. SI no cumple, ENTONCES 422 y no se guarda ninguno.
- **R6.** SI el vinculado no es del trabajador, no está activo, no es
  vigente en el mes o no es de importe (R2), ENTONCES 422 y no se guarda
  ninguno. SI el periodo no existe, 404; SI está cerrado, 409.
- **R7.** CUANDO cambia algún importe, el sistema debe dejar un evento
  `IMPORTES` con la foto de antes y de después, que se deshace como cualquier
  otro (`#regla-deshacer`). Si no cambia nada, ni escribe ni deja evento.
- **R8.** `[D7]` Copiar el mes anterior (el periodo o un trabajador) **no**
  copia importes.

## 3. Cuadrante (api y front)

- **R9.** El cuadrante debe devolver en cada trabajador `importes`: uno por
  vinculado de importe vigente en el mes, en el orden de
  `recurso_vinculado.ide`, con `vinculado_ide`, tipo, descripción del tipo,
  código, `importe` (nulo = falta) e `importe_anterior` `[D7]` (el del
  periodo anterior, nulo si no hay). Sin vinculados de importe, lista vacía.
- **R10.** Cada subfila de un vinculado de importe debe llevar `con_importe:
  true` y su `importe` del mes; la del resto, `con_importe: false`.
- **R11.** `[D3]` MIENTRAS el periodo está abierto, el editor del trabajador
  debe enseñar, aparte y detrás de las incidencias, una casilla por cada
  entrada de `importes`, con su tipo y código, el importe guardado (vacía si
  falta) y, si lo hay, «mes anterior: X €» como referencia, sin rellenarla.
- **R12.** CUANDO el usuario cambia una casilla, el front debe guardarla con
  el mismo diferido del editor (`guardarAhora`), con su propio `PUT`, solo si
  los importes cambiaron. Acepta coma o punto decimal; vacía manda `null`; lo
  que la api rechace sale en el aviso de siempre y queda pendiente.
- **R13.** La subfila de un vinculado de importe debe enseñar su importe del
  mes (el del mes entero, no la parte de la obra) o una marca «falta
  importe». El front no reparte ni calcula nada.

## 4. Contrato api → transfer

- **R14.** Cada vinculado de importe que viaja en `vinculados` (F-044 R10)
  debe llevar `importe_mensual: true` y `importe` (número o `null` si falta).
  El resto de vinculados viajan exactamente como hoy, sin esas claves.
- **R15.** La api debe leer los importes del periodo en **una** lectura más
  y solo si alguna línea mandada lleva vinculados de importe.

## 5. Qué escribe el transfer

- **R16.** `[D5]` CUANDO un vinculado llega con `importe_mensual` e
  `importe > 0`, el transfer debe escribir su línea con la hora por defecto
  del vinculado, `can` = el del titular (sin normalizar, `[D8]`),
  `pre` = el importe del mes y `tot = round(can × pre, 2)`, ignorando
  `reshor.pre`. Partida, cuenta, parte, pisado, capacidad, modo pruebas y
  `synckey`: los de F-044, sin cambios.
- **R17.** `[D4]` SI llega con `importe_mensual` e `importe` nulo, ENTONCES
  el vinculado se omite con el motivo «falta el importe del mes» (con tipo y
  código); el titular y los demás vinculados se registran igual.
- **R18.** `[D4]` SI llega con `importe_mensual` e `importe` 0, ENTONCES se
  omite con el motivo «importe 0 este mes»: no se escribe ninguna línea.
- **R19.** SI un vinculado de importe no tiene hora por defecto en `reshor`,
  ENTONCES se omite «sin hora por defecto», como hoy.
- **R20.** Un vinculado sin `importe_mensual` se decide exactamente como en
  F-044 (R14 incluido), y una petición sin vinculados de importe da el mismo
  `asdict(Preflight)` y las mismas lecturas que antes de F-069.
- **R21.** `[D6]` Lo que ya está en el parte se trata como en F-044 (R20-R23)
  y F-064: la línea a mano con su hora y partida es un pisado a confirmar del
  vinculado; con otra partida, cuenta en su capacidad (sobrecarga a confirmar
  si pasa de 1). Nunca `DELETE`.
- **R22.** `[D9]` Un vinculado ya registrado (`synckey` o `hmores_ide`) sale
  `ya_registrado` aunque su importe haya cambiado, como el % de hoy.
- **R23.** Suelto y por lote (`RegistroLote`) el resultado es el mismo.
- **R24.** La forma de la respuesta de preflight y `ejecutar` no cambia: la
  entrada de `vinculados` ya lleva `pre` y `tot` (F-044 R25), que en un
  vinculado de importe son el importe del mes y su parte en esa obra.

## 6. Modal y traza

- **R25.** El modal de registro debe enseñar, en la fila de **cualquier**
  vinculado que se escribe, su `tot` y su `pre` tal como los manda el
  transfer («27,36 € de 45,60 €»); el omitido, su motivo, como hoy.
- **R26.** La traza del vinculado (estado, motivo, parte, `hmores.ide`) se
  guarda en `asignacion_vinculado` como en F-044 R30, sin cambios.

## 7. Documentación, despliegue y verificación

- **R27.** `docs/ARCHITECTURE.md#regla-vinculado` debe ganar el punto
  «Importe del mes» (fuente única; R14 de F-044 remitido a él) y la tabla
  `importe_vinculado` en la lista de tablas; `docs/INTEGRACION.md` §5 y §7,
  el contrato nuevo y el orden de despliegue.
- **R28.** Orden de despliegue **transfer → api → front**. Con el transfer
  viejo y la api nueva, los vinculados de importe se siguen omitiendo «sin
  importe mensual» (nunca se escribe un importe inventado).
- **R29.** MANUAL en local, en modo pruebas sobre la 0404 (tasks T13).
- **R30.** Al desplegar, `azure-apps/dedicacion.md` al día (tabla, endpoint,
  campos del contrato) en el mismo trabajo.
