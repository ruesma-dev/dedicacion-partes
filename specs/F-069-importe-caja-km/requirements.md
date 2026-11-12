<!-- specs/F-069-importe-caja-km/requirements.md -->
# F-069 · Caja por obra, km y viajes por %, con comentario

Rigor **`critico`** (cambia lo que el transfer escribe en Sigrid). Toca **los
tres servicios** (design §1). Enmienda F-044 R14: caja, km y viajes ya no
toman el precio de `reshor.pre`, sino una **cantidad** que se teclea.
Decisiones en design §9: D1-D10 **cerradas** (2026-11-11 y 2026-11-12); D11
y D12-D16 **abiertas** (cada una con su recomendación, con la que están
escritos los R). **Depende de F-054** para traer los comentarios (§7, D16).
Fuera: F-052, F-071, F-073, F-033 y `partes`.

## 0. Contexto y glosario

- Octubre de 2026: 300 de 521 líneas no escritas, «sin importe mensual».
- **Vinculado de cantidad**: el de un tipo de R1. **Por %** (`VP`, `VIAJE`):
  una cantidad del mes que se reparte con el % del titular. **Por obra**
  (`CAJA`): una cantidad por cada línea del titular, entera a esa obra.
  **Importe**: los euros (la cantidad, o km × precio por km).

## 1. Tipos (api)

- **R1.** `[D1, D2, D10, D12]` El sistema debe leer de `config.yaml`
  (`sync.vinculados.importes`) los tipos de cantidad con su unidad y su
  reparto — hoy `CAJA: {eur, obra}`, `VIAJE: {eur, pct}` (puede no usarse de
  momento), `VP: {km, pct}` — y el `precio_km` (hoy 0,20 €/km). Mal escrito,
  la api no arranca.
- **R2.** Tipo, unidad y reparto de un vinculado los decide **una** función
  pura de `dedicacion-api/domain/importes.py` (tipo sin espacios, en
  mayúsculas). Un tipo fuera de la lista, como hoy.

## 2. Guardar cantidades y comentarios (api)

- **R3.** `[D7]` La cantidad **del mes** (por %) va a la tabla nueva
  `importe_vinculado` (periodo × vinculado, único) y la **por obra**, a
  `asignacion_vinculado` (columnas nuevas), las dos con `cantidad`,
  `copiado` y `comentario`; declaradas en `orm_models.py`.
- **R4.** CUANDO llega `PUT /api/v1/periodos/{a}/{m}/trabajadores/{ide}/
  importes` con `{importes: [{vinculado_ide, obra_ide?, es_postventa?,
  cantidad, comentario}]}` (obra y modo solo en los por obra), el sistema
  debe sustituir lo de esos vinculados (y líneas): número ⇒ se guarda con
  `copiado = false`; `null` ⇒ se borra; lo que no viene no se toca.
- **R5.** `[D2]` Cantidad ≥ 0, dos decimales como mucho, ≤ 999.999,99 en
  `eur` y ≤ 99.999,99 en `km`; comentario de 200 caracteres como mucho. SI
  no, ENTONCES 422 y no se guarda nada.
- **R6.** SI el vinculado no es del trabajador, activo, vigente en el mes y
  de cantidad; si es por obra y no hay línea suya en esa obra y modo; o si
  viene repetido, ENTONCES 422. Periodo inexistente 404; cerrado 409.
- **R7.** CUANDO cambia algo, el sistema debe dejar un evento `IMPORTES`
  (foto de antes y de después), deshacible como cualquier otro. Sin cambios,
  ni escribe ni deja evento.
- **R8.** `[D7]` CUANDO se copia el mes anterior (periodo o trabajador), el
  sistema debe copiar también las cantidades y comentarios de origen que en
  el destino estén vacíos (las del mes, por vinculado; las por obra, con su
  línea copiada), con `copiado = true`; nunca pisa. Si copia alguna, deja su
  evento `IMPORTES` tras el de la copia.
- **R9.** `[D14]` Cada línea del titular (`asignacion`) gana un `comentario`
  (≤ 200), que se guarda con el `PUT …/asignaciones` de siempre (campo
  opcional por línea: sin él, se conserva), se copia al copiar el mes y entra
  en el evento `GUARDAR`.

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
- **R12.** CUANDO cambia una casilla, un comentario o se pulsa «Revisado»,
  el front debe mandar el `PUT` en el diferido del editor (`guardarAhora`),
  solo si algo cambió. Coma o punto decimal; vacía ⇒ `null`; lo rechazado,
  al aviso de siempre y pendiente.
- **R13.** `[D14]` El cuadrante debe tener la columna **«Comentario»**:
  en la fila de la línea, el del titular (editable en el editor); en la
  subfila, el del vinculado. El front no decide nada: pinta lo que llega.
- **R14.** La subfila de un vinculado de cantidad debe enseñar su cantidad
  con unidad (la del mes en los por %; la de esa obra en caja), «falta
  importe» o la marca de copiado. El front no reparte ni multiplica.

## 4. Contrato api → transfer

- **R15.** Cada vinculado de cantidad en `vinculados` (F-044 R10) debe
  llevar `importe_mensual: true`, `unidad`, `reparto`, `cantidad` (la del
  mes o la de esa línea; `null` si falta), `copiado`, `comentario` y, si es
  `km`, `precio_km`. Cada línea lleva su `comentario`. Lo demás, como hoy.
- **R16.** La api lee las cantidades del periodo en **una** lectura más y
  solo si alguna línea mandada lleva vinculados de cantidad.

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
  «falta el importe» (tipo y código); SI es 0, «importe 0». Caja: nula o 0
  en una obra ⇒ nada en esa obra; SI ninguna línea del vinculado trae caja,
  ENTONCES se omite «falta la caja del mes» (en la línea de menor
  `registro_id`). El titular y los demás, como siempre.
- **R21.** `[D11]` SI llega `copiado: true`, ENTONCES se omite «copiado del
  mes anterior sin revisar».
- **R22.** SI no tiene hora por defecto en `reshor`, se omite «sin hora».
  **R23.** `[D14]` El `tex` de una línea escrita (titular o vinculado) es su
  comentario; en modo pruebas, la marca seguida del comentario. Sin
  comentario, como hoy (vacía al insertar; la de antes al editar).
- **R24.** Sin `importe_mensual` ni `comentario`, todo como en F-044:
  mismas acciones, valores y lecturas.
- **R25.** `[D6]` Lo ya escrito en el parte, como F-044 (R20-R23) y F-064.
  Una caja a mano de esa obra con su hora suma en la capacidad del vinculado
  (`can` 1 + 1 ⇒ sobrecarga a confirmar). Nunca `DELETE`.
- **R26.** `[D9]` Ya registrado ⇒ `ya_registrado` aunque cambie la cantidad
  o el comentario. **R27.** Suelto y por lote, lo mismo.
- **R28.** Las entradas de `vinculados` de preflight y `ejecutar` ganan
  `km`, `precio_km` y `reparto` (nulos si no aplican).

## 6. Modal y traza

- **R29.** El modal debe enseñar en cada vinculado que se escribe su `tot` y
  su `pre` («27,36 € de 45,60 €»), en `km` los km y el precio («724,5 km ×
  0,20 €/km») y, en caja, «caja de esta obra»; el omitido, su motivo.
  La traza del vinculado, como F-044 R30 (**R30**).

## 7. Traer los comentarios al sincronizar (tras F-054)

- **R31.** `[D15, D16]` CUANDO «Sincronizar Sigrid» trae los % (F-054,
  `POST /api/porcentajes/existentes`, `traer-sigrid`), el transfer debe
  publicar el `tex` de cada línea y, en **una** lectura más, las líneas del
  periodo con `synckey` `porcentajes:vin:` con su `tex`.
- **R32.** `[D15]` La api debe poner como comentario de cada línea **nuestra
  ya registrada** (titular por `sigrid_hmores_ide` o su `synckey`; vinculado
  por la suya) el `tex` de Sigrid sin la marca de pruebas, si difiere; con
  un evento `SIGRID` por trabajador. Una aceptada de F-054 trae el `tex` de
  su línea de menor `ide`.

## 8. Documentación, despliegue y verificación

- **R33.** `#regla-vinculado` gana «Cantidad y comentario» (fuente única,
  decisiones citadas; F-044 R14 remite a él), las tablas y columnas nuevas y
  `#regla-traer-sigrid` el comentario; `INTEGRACION.md` §5 y §7.
- **R34.** Despliegue **transfer → api → front**; transfer viejo + api
  nueva: los de cantidad se siguen omitiendo y el comentario no viaja.
- **R35.** MANUAL en local, modo pruebas, 0404. **R36.** `azure-apps` al día.
