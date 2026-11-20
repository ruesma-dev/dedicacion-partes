<!-- specs/F-069-importe-caja-km/requirements.md -->
# F-069 · Caja por obra, km y viajes por %, con comentario

Rigor **`critico`** (cambia lo que el transfer escribe en Sigrid); toca **los
tres servicios** (design §1). Enmienda F-044 R14: caja, km y viajes llevan una
**cantidad** tecleada, no el `reshor.pre`. D1-D21 **cerradas por el humano**
(2026-11-11, -12 y -19; design §9). Fuera: F-052, F-071, F-073, F-033, `partes`.

## 0. Contexto y glosario

- Octubre de 2026: 300 de 521 líneas no escritas, «sin importe mensual».
- **Vinculado de cantidad**: el de un tipo de R1. **Por %** (`VP`, `VIAJE`):
  una cantidad del mes que se reparte con el % del titular. **Por obra**
  (`CAJA`): una cantidad por cada línea del titular, entera a esa obra.
  **Importe**: los euros (la cantidad, o km × precio por km).

## 1. Tipos (api)

- **R1.** `[D1, D2, D10, D12]` El sistema debe leer de `config.yaml`
  (`sync.vinculados.importes`) los tipos de cantidad con unidad y reparto —
  `CAJA: {eur, obra}`, `VIAJE: {eur, pct}` (quizá sin uso aún), `VP: {km,
  pct}`— y el `precio_km` (0,20 €/km). Mal escrito, la api no arranca.
- **R2.** Tipo, unidad y reparto los decide **una** función pura de
  `domain/importes.py` (tipo sin espacios, en mayúsculas); fuera, como hoy.

## 2. Guardar cantidades y comentarios (api)

- **R3.** `[D7, D19]` La cantidad **del mes** (por %) va a la tabla nueva
  `importe_vinculado` (periodo × vinculado, único) y la **por obra**, a
  `asignacion_vinculado` (columnas nuevas), las dos con `cantidad` (nulable),
  `copiado` y `comentario`; declaradas en `orm_models.py`.
- **R4.** `[D18, D19]` CUANDO llega `PUT /api/v1/periodos/{a}/{m}/trabajadores/
  {ide}/importes` con `{importes: [{vinculado_ide, obra_ide?, es_postventa?,
  cantidad, comentario, revisado?}]}` (obra y modo, solo por obra), el sistema
  debe sustituir cantidad y comentario de esos; lo demás no se toca. `copiado`
  pasa a `false` solo si la cantidad difiere de la guardada o llega
  `revisado: true` (solo el comentario lo conserva). Cantidad `null` ⇒ sin
  cantidad y el comentario se guarda igual, también por %; sin los dos, nada.
- **R5.** `[D2, D19]` Cantidad ≥ 0, dos decimales como mucho, ≤ 999.999,99
  en `eur` y ≤ 99.999,99 en `km`; comentario ≤ 200 caracteres, sin más
  chequeo; `revisado`, booleano. SI no, ENTONCES 422 y nada se guarda.
- **R6.** SI el vinculado no es del trabajador, activo, vigente en el mes y
  de cantidad; si es por obra y no hay línea suya en esa obra y modo; o si
  viene repetido, ENTONCES 422. Periodo inexistente 404; cerrado 409.
- **R7.** CUANDO cambia algo, el sistema debe dejar un evento `IMPORTES`
  (antes y después), deshacible; sin cambios, ni escribe ni deja evento.
- **R8.** `[D7]` CUANDO se copia el mes anterior (periodo o trabajador), el
  sistema debe copiar también las cantidades y comentarios de origen que en
  el destino estén vacíos (las del mes, por vinculado; las por obra, con su
  línea copiada), con `copiado = true` si se copia una cantidad; nunca pisa.
  Si copia alguna, deja su evento `IMPORTES` tras el de la copia.
- **R9.** `[D14]` Cada línea del titular (`asignacion`) gana un `comentario`
  (≤ 200), por el `PUT …/asignaciones` de siempre (opcional por línea: sin
  él, se conserva); se copia con el mes y entra en el evento `GUARDAR`.

## 3. Cuadrante y front

- **R10.** El cuadrante debe devolver por trabajador `importes` (uno por
  vinculado por % vigente: tipo, código, unidad, cantidad, copiado,
  comentario) y, en cada subfila, `reparto`, `unidad` y, si es por obra, su
  `cantidad`, `copiado` y `comentario`; en cada línea, su `comentario`.
- **R11.** `[D3, D12]` MIENTRAS el periodo está abierto, el editor debe
  enseñar, tras las incidencias, una casilla por vinculado por % («€» o
  «km») y, por cada línea con un vinculado por obra, una casilla «Caja ·
  obra» en €; cada una con su comentario al lado y, si `copiado`, la marca
  «copiado del mes anterior, sin revisar» y un botón «Revisado».
- **R12.** `[D18]` CUANDO cambia una casilla, un comentario o se pulsa
  «Revisado», el front debe mandar en `guardarAhora` el `PUT` **solo con las
  casillas que cambiaron** (actuar sobre una no toca otra), con `revisado:
  true` en «Revisado». Coma o punto; vacía ⇒ `null`; rechazo ⇒ aviso, pendiente.
- **R13.** `[D14]` Columna **«Comentario»**: en la línea, el del titular
  (editable en el editor); en la subfila, el del vinculado. Solo pinta.
- **R14.** La subfila de un vinculado de cantidad debe enseñar su cantidad
  con unidad (del mes o de su obra), «falta importe» o la marca de copiado.

## 4. Contrato api → transfer

- **R15.** Cada vinculado de cantidad en `vinculados` (F-044 R10) debe
  llevar `importe_mensual: true`, `unidad`, `reparto`, `cantidad` (la del
  mes o la de esa línea; `null` si falta), `copiado`, `comentario` y, si es
  `km`, `precio_km`. Cada línea lleva su `comentario`. Lo demás, como hoy.
  **R16.** Las cantidades del periodo, en **una** lectura más y solo si
  alguna línea mandada lleva vinculados de cantidad.

## 5. Qué escribe el transfer

- **R17.** `[D5]` Por % con `cantidad > 0`: su hora por defecto, `can` = el
  del titular (sin normalizar, `[D8]`), `pre` = importe del mes y `tot =
  round(can × pre, 2)`, ignorando `reshor.pre`. `[D10]` En `km`, importe =
  `round(km × precio_km, 2)`.
- **R18.** `[D12]` Por obra con `cantidad > 0`: su hora por defecto, `can` =
  1, `pre` = `tot` = la cantidad de esa línea, en el parte de esa obra.
- **R19.** En los dos, partida, cuenta, parte, pisado, capacidad, modo
  pruebas y `synckey` son los de F-044. La hora es **siempre** la hora por
  defecto del recurso (`hora_del_vinculado`; en caja, `CO`): no se elige.
- **R20.** `[D4, D13]` Por %: SI `cantidad` es nula, ENTONCES se omite
  «falta el importe» (tipo y código); SI es 0, «importe 0». Caja, igual
  **en cada obra**: nula ⇒ esa línea se omite «falta la caja del mes» (con
  la obra); 0 ⇒ nada en esa obra. El titular y los demás, como siempre.
- **R21.** `[D11]` SI llega `copiado: true`, ENTONCES se omite «copiado del
  mes anterior sin revisar». **R22.** Sin hora por defecto, «sin hora».
- **R23.** `[D14]` El `tex` de una línea escrita (titular o vinculado) es su
  comentario; en modo pruebas, la marca seguida del comentario. Sin
  comentario, como hoy (vacía al insertar; la de antes al editar).
- **R24.** Sin `importe_mensual` ni `comentario`, todo como en F-044.
- **R25.** `[D6]` Lo ya escrito en el parte, como F-044 (R20-R23) y F-064.
  Una caja a mano de esa obra con su hora suma en la capacidad del vinculado
  (`can` 1 + 1 ⇒ sobrecarga a confirmar). Nunca `DELETE`.
- **R26.** `[D9]` Ya registrado ⇒ `ya_registrado` aunque cambie la cantidad.
  `[D20]` SI tiene comentario, su `tex` (R23) difiere del de la línea, esta
  es nuestra (`synckey` `porcentajes:`), su parte está En registro y, en
  modo pruebas, es de la obra de pruebas, ENTONCES `ejecutar` debe cambiar
  **solo** su `tex` (`UPDATE` con la guarda de F-051, nunca `DELETE`); si
  no, nada, y el motivo dice por qué. **R27.** Suelto y por lote, igual.
- **R28.** Las entradas de `vinculados` de preflight y `ejecutar` ganan
  `km`, `precio_km` y `reparto`, y las de líneas y vinculados, `tex_nuevo`
  (nulos si no aplican); `ejecutar` devuelve `tex_actualizadas`.

## 6. Modal y traza

- **R29.** El modal debe enseñar en cada vinculado que se escribe su `tot` y
  su `pre` («27,36 € de 45,60 €»), en `km` los km y el precio («724,5 km ×
  0,20 €/km») y, en caja, «caja de esta obra»; el omitido, su motivo; en una
  ya registrada con `tex_nuevo`, «se actualiza el comentario» (D20).
- **R30.** La traza que la api escribe en la subfila de un vinculado (F-044
  R30) debe conservar su cantidad, `copiado` y comentario.

## 7. Traer los comentarios al sincronizar (tras F-054)

- **R31.** `[D15, D16, D17]` CUANDO «Sincronizar Sigrid» trae los % (F-054,
  `POST /api/porcentajes/existentes`, `traer-sigrid`), el transfer debe
  publicar el `tex` de cada línea **sin su marca** (`st.marca_pruebas`) ni
  espacios (vacío ⇒ `null`) y, en **una** lectura más, las del periodo con
  `synckey` `porcentajes:vin:`, igual.
- **R32.** `[D15, D21]` La api debe poner como comentario de cada línea
  **nuestra ya registrada** (titular por `sigrid_hmores_ide` o su `synckey`;
  vinculado por la suya) el `tex` publicado tal cual (D17), si difiere:
  titular y caja, con un evento `SIGRID` por trabajador; las del mes, con uno
  `IMPORTES` (D21). Una aceptada de F-054 trae el de su línea de menor `ide`.

## 8. Documentación, despliegue y verificación

- **R33.** `#regla-vinculado` gana «Cantidad y comentario» (fuente única,
  decisiones citadas; F-044 R14 remite a él), las tablas y columnas nuevas y
  `#regla-traer-sigrid` el comentario (sincronizar antes de registrar pisa
  el tecleado con el de Sigrid, D15); `INTEGRACION.md` §5 y §7.
- **R34.** Despliegue **transfer → api → front**; transfer viejo + api
  nueva: los de cantidad se siguen omitiendo y el comentario no viaja.
- **R35.** MANUAL en local, modo pruebas, 0404. **R36.** `azure-apps` al día.
