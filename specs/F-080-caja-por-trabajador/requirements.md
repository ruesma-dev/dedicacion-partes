# F-080 · Caja de obra: una por trabajador y repartida con su %, como los km

Rigor **`critico`** (cambia el importe que el transfer escribe en Sigrid;
design, cabecera). Petición del humano del 2026-11-25: «la caja de obra se
comporte como los km, una por trabajador y se reparte siguiendo los % de
reparto». **Sustituye F-069 D12** (caja por obra) y, para la caja, F-069 R11
(casilla «Caja · obra»), R18 y la parte de caja de R20. Absorbe el punto (b) de
F-077 (D7). Toca **solo la api**; transfer y front ya admiten `pct` en `eur`
desde F-069 (design §2). Decisiones **cerradas por el humano el 2026-11-25**
(design §13): D1, D3, D4, D5 y D7 la (a); D2 sin pasada de restos (no hay
cajas por obra con importe, `progress/manual_F-080.md`); D6 retirada.

## 0. Glosario

- **Por %** / **por obra**: los dos repartos de F-069 (`reparto: pct | obra`
  en `sync.vinculados.importes`). Tras F-080, ningún tipo es por obra.
- **Resto por obra**: lo que una subfila (`asignacion_vinculado`) guarda en
  `cantidad`, `copiado` o `comentario` de un vinculado cuyo tipo es **por %**.
  Medido en producción el 2026-11-25: ninguna caja por obra con importe y un
  solo comentario suelto; invisible y sin efecto (el transfer usa el del mes).
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

## 3. Copiar el mes (api)

- **R11.** CUANDO se copia el mes anterior (periodo o trabajador), las
  subfilas de un tipo **por %** deben llegar sin `cantidad`, `copiado` ni
  `comentario` (un resto por obra no se propaga al mes nuevo); las de un tipo
  por obra y las de vinculados que no son de cantidad, como hoy. Sin tipos
  configurados, como hoy. (capa: unit)

## 4. Documentación, despliegue y verificación

- **R12.** `#regla-vinculado` («Cantidad y comentario») debe decir caja `€`,
  `pct`; el reparto `obra`, sin tipo hoy; que los restos por obra no se pasan
  al mes (D2) ni se copian (R11); y la cita de la decisión. El comentario de
  `config.yaml`, igual. (capa: unit)
- **R13.** Despliegue: **solo la api**. Sin «Sincronizar Sigrid» (el reparto
  sale de la config, no del sync). Tras desplegar, recargar la página en el
  navegador. (MANUAL)
- **R14.** MANUAL M1, M3 y M4 (design §10; tasks). **R15.**
  `azure-apps/dedicacion.md` al día (design §12).

## 5. Tests anteriores que cambian (lista CERRADA)

Solo dos, porque leen la config versionada; los demás de F-069 usan sus
propios tipos (`CAJA` por obra) y siguen igual:

- `services/dedicacion-api/tests/test_f069_importes_dominio.py::
  test_f069_r1_config_versionada` — `CAJA` pasa a `TipoCantidad("eur", "pct")`.
- `services/dedicacion-api/tests/test_f069_importes_api.py::
  test_f069_r15_el_contenedor_pasa_tipos_y_precio` — compara con `TIPOS`
  (caja por obra): compara con los tipos de la config nueva.

Si al cambiar la config falla **otro** test: **PARA** y `blocked`.
