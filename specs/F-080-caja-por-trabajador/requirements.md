# F-080 · Caja de obra: una por trabajador y repartida con su %, como los km

Rigor **`critico`** (cambia el importe que el transfer escribe en Sigrid;
design, cabecera). Petición del humano del 2026-11-25: «la caja de obra se
comporte como los km, una por trabajador y se reparte siguiendo los % de
reparto». **Sustituye F-069 D12** (caja por obra) y, para la caja, F-069 R11
(casilla «Caja · obra»), R18 y la parte de caja de R20. Absorbe el punto (b) de
F-077 (D7). Toca **solo la api**; transfer y front ya admiten `pct` en `eur`
desde F-069 (design §2). Decisiones D1-D7 abiertas (design §13).

## 0. Glosario

- **Por %** / **por obra**: los dos repartos de F-069 (`reparto: pct | obra`
  en `sync.vinculados.importes`). Tras F-080, ningún tipo es por obra.
- **Resto por obra**: lo que una subfila (`asignacion_vinculado`) guarda en
  `cantidad`, `copiado` o `comentario` de un vinculado cuyo tipo es **por %**
  (hoy, solo las cajas tecleadas por obra antes de F-080).
- **Caja del mes**: la fila de `importe_vinculado` (periodo × vinculado).

## 1. Configuración y lo que se ve (api)

- **R1.** `[D1]` `config.yaml` debe declarar `CAJA: {unidad: eur, reparto:
  pct}`; `VIAJE` y `VP`, como hoy. El reparto `obra` sigue siendo un valor
  válido de la config (mecanismo de F-069 sin tipo que lo use). (capa: unit)
- **R2.** El cuadrante debe devolver la caja **una vez por trabajador** en
  `importes` (tipo, código, unidad `eur`, cantidad del mes, copiado,
  comentario) y en cada subfila de caja `reparto: pct`, sin `cantidad` de
  subfila. (capa: unit)
- **R3.** El editor debe enseñar **una** casilla de caja en € por trabajador
  («CAJA <código>») y ninguna «Caja · <obra>»; la subfila, la caja del mes o
  «falta importe». Sin cambio en `app.js`: se prueba con la fila de R2.
  (capa: unit)
- **R4.** CUANDO llega `PUT …/importes` con la caja de un trabajador, el
  sistema debe guardarla como caja del mes (`importe_vinculado`), aunque
  traiga `obra_ide`; dos elementos de la misma caja ⇒ 422 «repetido».
  (capa: unit)

## 2. Qué se manda y qué escribe el transfer

- **R5.** Al registrar, cada línea del titular debe llevar su caja con
  `reparto: pct` y la **cantidad del mes** (`null` si falta), su `copiado` y
  el comentario del mes, en la misma lectura de F-069 R16. (capa: unit)
- **R6.** `[D4]` Con caja del mes `> 0`, el transfer debe escribir en **cada**
  línea del titular (obra normal, postventa y VAR) una línea de caja con su
  hora por defecto (`CO`), `can` = el del titular (sin normalizar), `pre` =
  la caja del mes y `tot = round(can × pre, 2)`. Ejemplo: 300 € al 60 % y al
  40 % (postventa) ⇒ `tot` 180 y 120. (capa: unit)
- **R7.** `[D5]` El sistema **no** debe ajustar céntimos: cada `tot` se
  redondea por su cuenta, como km y viajes. 100 € al 33,33 % × 3 ⇒ 33,33 × 3
  = 99,99. Un total < 100 % reparte menos que lo tecleado. (capa: unit)
- **R8.** Caja del mes nula ⇒ cada línea se omite «falta el importe del mes»
  (sin obra); 0 ⇒ «importe 0»; copiada sin revisar ⇒ «sin revisar», sin «en la
  obra». Los motivos `MOTIVO_FALTA_CAJA`/`MOTIVO_CAJA_CERO` no salen.
  (capa: unit)
- **R9.** El modal debe enseñar la caja como km y viajes («180,00 € de 300,00
  €»), nunca «caja de esta obra». Sin cambio en `app.js`. (capa: unit)
- **R10.** `[D3]` Una caja ya registrada en Sigrid sigue `ya_registrado` (F-069
  R26, D9): ni su `can` ni su `tot` cambian al volver a registrar; solo su `tex`
  si el comentario del mes difiere y se dan las condiciones de D20. Lo
  prueban los tests de F-069 R26, que no cambian. (capa: unit)

## 3. Lo ya tecleado por obra (api, al arrancar)

- **R11.** `[D2]` CUANDO arranca la api (tras poner al día el esquema), el
  sistema debe recorrer los periodos **ABIERTOS** y, por trabajador y
  vinculado de tipo por % con **restos por obra** en sus subfilas, pasarlos a
  la caja del mes: cantidad = suma de las no nulas (nula si no hay ninguna),
  `copiado = true` si hay cantidad (`[D6]`, «sin revisar»: no se registra
  hasta teclearla o pulsar «Revisado»), comentario = los distintos no vacíos
  en el orden de las líneas, unidos por « · » y cortados a 200; y dejar los
  restos vacíos. (capa: unit)
- **R12.** Cada trabajador cambiado debe dejar **un** evento `IMPORTES` (antes
  y después, usuario `arranque F-080`), deshacible. (capa: unit)
- **R13.** SI ese vinculado ya tiene caja del mes (fila en
  `importe_vinculado`), ENTONCES esa fila no se toca y solo se vacían los
  restos. (capa: unit)
- **R14.** `[D3]` SI alguna subfila de ese vinculado en ese periodo está
  `registrado`, ENTONCES no se cambia nada de ese vinculado en ese periodo y
  se avisa en el log (periodo, trabajador, vinculado). (capa: unit)
- **R15.** SI la suma pasa del tope de `eur` (999.999,99, F-069 R5), ENTONCES
  no se cambia nada de ese vinculado y se avisa en el log. (capa: unit)
- **R16.** Los periodos **CERRADOS** no se tocan. Una segunda pasada no cambia
  nada ni deja eventos (idempotente). (capa: unit)
- **R17.** SI la pasada falla, ENTONCES se deshace entera, se registra en el
  log como error y la api **arranca igual** (los restos no se registran: el
  transfer usa la caja del mes). (capa: unit)
- **R18.** Al terminar, el sistema debe dejar en el log **una** línea `INFO`
  con el resumen: `F-080: N vinculados pasados al mes en P periodos; S
  saltados` (aunque N sea 0), para comprobarla en Log Analytics. (capa: unit)

## 4. Copiar el mes (api)

- **R19.** CUANDO se copia el mes anterior (periodo o trabajador), las
  subfilas de un tipo **por %** deben llegar sin `cantidad`, `copiado` ni
  `comentario` (los restos de un mes cerrado no se propagan); las de un tipo
  por obra y las de vinculados que no son de cantidad, como hoy. Sin tipos
  configurados, como hoy. (capa: unit)

## 5. Documentación, despliegue y verificación

- **R20.** `#regla-vinculado` («Cantidad y comentario») debe decir caja `€`,
  `pct`; el reparto `obra`, sin tipo hoy; la pasada de R11-R18; y la cita de
  la decisión. El comentario de `config.yaml`, igual. (capa: unit)
- **R21.** Despliegue: **solo la api**. Sin «Sincronizar Sigrid» (el reparto
  sale de la config, no del sync). Tras desplegar, la línea de R18 en Log
  Analytics y recargar la página en el navegador. (MANUAL)
- **R22.** MANUAL M1-M4 (design §10; tasks). **R23.** `azure-apps/dedicacion.md`
  al día (design §12).

## 6. Tests anteriores que cambian (lista CERRADA)

Solo dos, porque leen la config versionada; los demás de F-069 usan sus
propios tipos (`CAJA` por obra) y siguen igual:

- `services/dedicacion-api/tests/test_f069_importes_dominio.py::
  test_f069_r1_config_versionada` — `CAJA` pasa a `TipoCantidad("eur", "pct")`.
- `services/dedicacion-api/tests/test_f069_importes_api.py::
  test_f069_r15_el_contenedor_pasa_tipos_y_precio` — compara con `TIPOS`
  (caja por obra): compara con los tipos de la config nueva.

Si al cambiar la config falla **otro** test: **PARA** y `blocked`.
