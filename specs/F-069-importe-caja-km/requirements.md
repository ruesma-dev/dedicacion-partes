<!-- specs/F-069-importe-caja-km/requirements.md -->
# F-069 · Importe del mes de caja y viajes, y km de vehículo propio, por %

Rigor **`critico`** (cambia lo que el transfer escribe en Sigrid). Toca **los
tres servicios** (design §1). Enmienda F-044 R14: algunos tipos de vinculado
ya no toman el precio de `reshor.pre`, sino una **cantidad del mes** que se
teclea. **Decisiones** en design §9: D1-D9 **cerradas por el humano el
2026-11-11** («d2, caja en euros, km en km y viaje en wuros. d7, copia
importes. A a lo demas»); **D10 (de dónde sale el precio por km) y D11
(copiado sin revisar) ABIERTAS**: con ellas abiertas la spec no se puede
aprobar entera. `[Dn]` remite a cada una. Fuera: mensajería (F-052), el
ajuste del % por alta o baja (F-071, design §10), el informe Excel (F-073),
deshacer en Sigrid (F-033) y `partes`.

## 0. Contexto

- F-044 R14 omite «sin importe mensual» el vinculado sin `pre`: todos los
  `CAJA` y `VIAJE` y casi todos los `VP` (`KM`). Octubre de 2026: 300 de las
  521 líneas no escritas (caja 177, viaje 74, VP 49).
- Glosario: **vinculado de cantidad** = vinculado vigente de un tipo de la
  lista de R1; **cantidad del mes** = lo que se teclea para él en el periodo:
  euros (caja, viaje) o kilómetros (VP); **importe del mes** = los euros
  (la cantidad, o km × precio por km).

## 1. Qué vinculados llevan cantidad (api)

- **R1.** `[D1, D2]` El sistema debe leer de `config.yaml`
  (`sync.vinculados.tipos_importe`) los tipos (`auxrestip.cod`) que van por
  cantidad del mes y su unidad: hoy `{CAJA: eur, VIAJE: eur, VP: km}`. Mal
  escrito (unidad que no sea `eur` o `km`), la api no arranca.
- **R2.** El sistema debe decidir si un vinculado es de cantidad, y su
  unidad, con **una** función pura de `dedicacion-api/domain/importes.py`
  (tipo sin espacios y en mayúsculas). Un tipo fuera de la lista, como hoy.

## 2. Guardar la cantidad (api)

- **R3.** `[D7]` La cantidad se guarda en la tabla nueva `importe_vinculado`
  (periodo × vinculado, único), declarada en `orm_models.py`, con su
  `cantidad`, la marca `copiado` y usuario y fecha del último cambio.
- **R4.** CUANDO llega `PUT /api/v1/periodos/{a}/{m}/trabajadores/{ide}/
  importes` con `{importes: [{vinculado_ide, cantidad}]}`, el sistema debe
  sustituir las de esos vinculados: un número la guarda con `copiado =
  false`; `null` la borra (vuelve a «falta»); el que no viene no se toca.
- **R5.** `[D2]` La cantidad es ≥ 0 y con dos decimales como mucho; en `eur`
  ≤ 999.999,99 y en `km` ≤ 99.999,99. SI no cumple, ENTONCES 422 y no se
  guarda ninguna.
- **R6.** SI el vinculado no es del trabajador, no está activo, no es
  vigente en el mes, no es de cantidad (R2) o viene repetido, ENTONCES 422 y
  no se guarda ninguna. SI el periodo no existe, 404; SI está cerrado, 409.
- **R7.** CUANDO cambia alguna cantidad (o su `copiado`), el sistema debe
  dejar un evento `IMPORTES` con la foto de antes y de después, deshacible
  como cualquier otro (`#regla-deshacer`). Sin cambios, ni escribe ni evento.
- **R8.** `[D7]` CUANDO se copia el mes anterior (el periodo o un
  trabajador), el sistema debe copiar también las cantidades del periodo de
  origen de los vinculados que en el destino sean de cantidad, vigentes y
  **sin** cantidad, con `copiado = true`; nunca pisa una ya puesta. Si copia
  alguna, deja su propio evento `IMPORTES` tras el de la copia.

## 3. Cuadrante (api y front)

- **R9.** El cuadrante debe devolver en cada trabajador `importes`: uno por
  vinculado de cantidad vigente en el mes, en el orden de
  `recurso_vinculado.ide`, con `vinculado_ide`, tipo, descripción del tipo,
  código, `unidad`, `cantidad` (nula = falta) y `copiado`. Sin ellos, `[]`.
- **R10.** Cada subfila de un vinculado de cantidad debe llevar
  `con_importe: true`, `unidad`, `cantidad` y `copiado`; el resto,
  `con_importe: false`.
- **R11.** `[D3]` MIENTRAS el periodo está abierto, el editor del trabajador
  debe enseñar, aparte y detrás de las incidencias, una casilla por entrada
  de `importes` con su tipo, código y unidad («€» o «km»), la cantidad
  guardada (vacía si falta) y, si `copiado`, la marca «copiado del mes
  anterior, sin revisar» con un botón «Revisado».
- **R12.** CUANDO el usuario cambia una casilla o pulsa «Revisado», el front
  debe mandar su `PUT` con el mismo diferido del editor (`guardarAhora`),
  solo si algo cambió («Revisado» manda la cantidad tal cual). Acepta coma o
  punto decimal; vacía manda `null`; lo rechazado sale en el aviso de
  siempre y queda pendiente.
- **R13.** La subfila de un vinculado de cantidad debe enseñar la cantidad
  del mes con su unidad (la del mes entero), «falta importe» o, si
  `copiado`, la marca de copiado. El front no reparte ni multiplica.

## 4. Contrato api → transfer

- **R14.** Cada vinculado de cantidad que viaja en `vinculados` (F-044 R10)
  debe llevar `importe_mensual: true`, `unidad` (`eur` | `km`), `cantidad`
  (número o `null`) y `copiado`. El resto viaja exactamente como hoy.
- **R15.** La api debe leer las cantidades del periodo en **una** lectura más
  y solo si alguna línea mandada lleva vinculados de cantidad.

## 5. Qué escribe el transfer

- **R16.** `[D5]` CUANDO un vinculado llega con `importe_mensual` y
  `cantidad > 0`, el transfer debe escribir su línea con su hora por
  defecto, `can` = el del titular (sin normalizar, `[D8]`), `pre` = el
  importe del mes y `tot = round(can × pre, 2)`, ignorando `reshor.pre`.
  En `eur`, importe = cantidad. Partida, cuenta, parte, pisado, capacidad,
  modo pruebas y `synckey`: los de F-044, sin cambios.
- **R17.** `[D2, D10]` En `km`, importe = `round(km × precio por km, 2)`,
  con el precio por km del recurso que el transfer lee de Sigrid (fuente:
  D10), en **una** lectura por petición y solo si algún `VP` llega con
  km > 0. SI no hay precio (> 0) para ese recurso, ENTONCES se omite «sin
  precio por km en Sigrid» con tipo y código. Un fallo o `truncated` de la
  lectura: falla sin escribir.
- **R18.** `[D4]` SI llega con `cantidad` nula, ENTONCES se omite «falta el
  importe del mes» (tipo y código); el titular y los demás, como siempre.
- **R19.** `[D4]` SI llega con `cantidad` 0, ENTONCES se omite «importe 0
  este mes»: no se escribe ninguna línea.
- **R20.** `[D11]` SI llega con `copiado: true`, ENTONCES se omite «importe
  copiado del mes anterior sin revisar» (recomendación de D11, abierta).
- **R21.** SI no tiene hora por defecto en `reshor`, ENTONCES se omite «sin
  hora por defecto».
- **R22.** Un vinculado sin `importe_mensual` se decide como en F-044 (R14
  incluido): mismas acciones, valores y lecturas que antes de F-069.
- **R23.** `[D6]` Lo que ya está en el parte, como en F-044 (R20-R23) y
  F-064: misma hora y partida ⇒ pisado a confirmar del vinculado; otra
  partida ⇒ cuenta en su capacidad. Nunca `DELETE`.
- **R24.** `[D9]` Ya registrado (`synckey` o `hmores_ide`) ⇒ `ya_registrado`
  aunque su cantidad haya cambiado, como el % de hoy.
- **R25.** Suelto y por lote (`RegistroLote`) el resultado es el mismo.
- **R26.** La entrada de `vinculados` de preflight y `ejecutar` gana `km` y
  `precio_km` (nulos si no es `km`); `pre` y `tot` siguen siendo el importe
  del mes y su parte en esa obra.

## 6. Modal y traza

- **R27.** El modal de registro debe enseñar, en la fila de cualquier
  vinculado que se escribe, su `tot` y su `pre` como los manda el transfer
  («27,36 € de 45,60 €») y, en un `km`, además los km y el precio
  («724,5 km × 0,20 €/km»); el omitido, su motivo.
- **R28.** La traza del vinculado se guarda en `asignacion_vinculado` como en
  F-044 R30, sin cambios.

## 7. Documentación, despliegue y verificación

- **R29.** `docs/ARCHITECTURE.md#regla-vinculado` gana el punto «Cantidad del
  mes» (fuente única, decisiones citadas; F-044 R14 remite a él) y la tabla
  `importe_vinculado`; `docs/INTEGRACION.md` §1 (la lectura del precio por
  km), §5 y §7.
- **R30.** Despliegue **transfer → api → front**. Transfer viejo con api
  nueva: los de cantidad se siguen omitiendo «sin importe mensual».
- **R31.** MANUAL en local, en modo pruebas sobre la 0404 (tasks T13).
- **R32.** Al desplegar, `azure-apps/dedicacion.md` al día en el mismo
  trabajo (tabla, endpoint, contrato, lectura nueva del transfer).
