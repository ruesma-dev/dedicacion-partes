# F-080 · Diseño: la caja, una por trabajador y repartida por %

**Rigor: `critico`.** Disparador 1 de «Niveles de rigor» (`CHECKPOINTS.md`):
cambia el **importe** de caja que se contabiliza en el parte
(`hmores.can`/`pre`/`tot`, `reglas_vinculados.precio_del_vinculado`) y que el
transfer escribe en Sigrid. El disparador 2 ya no aplica como motivo propio:
F-080 no escribe datos guardados ni añade escrituras nuevas (sin pasada de
restos, D2).

Decisiones **cerradas por el humano el 2026-11-25** (§13): D1, D3, D4, D5 y
D7 la (a); D2 sin pasada (medido en producción, `progress/manual_F-080.md`:
ninguna caja por obra con importe en ningún periodo ni empresa, y un solo
comentario suelto); D6 retirada.

## 1. Servicios y límite

| Servicio | Qué cambia | Por qué ahí |
|---|---|---|
| api | config (R1), guarda en la copia del mes (R11), docs (R12) | dueña del dato y de la config de tipos |
| transfer | **nada** (solo tests de regresión, R6-R8) | ya reparte cualquier tipo `pct` |
| front | **nada** (solo tests, R3, R9) | pinta lo que dice `reparto` |

Ningún servicio nuevo; el reparto sigue solo en el transfer.

## 2. Diagnóstico: por qué basta casi con la config (D1)

Leído en el código el 2026-11-25:

- **api.** El tipo y su reparto los decide `domain/importes.tipo_de` con la
  config; no se guardan (`SubfilaVinculado.reparto`, «de la config»).
  `importes_del_mes` saca una casilla por vinculado **por %**;
  `GuardarImportes._validar` ignora `obra_ide` en los por % (clave `(vid,
  None, False)`); `registro_sigrid._cantidad_al_transfer` toma la cantidad
  del mes si el reparto no es `obra`; `traer_sigrid` lleva el comentario de un
  por % a la caja del mes; `schemas` solo pone `cantidad` en la subfila si es
  por obra. Con `CAJA: pct`, todo eso sale ya como km.
- **transfer.** `precio_del_vinculado`: `por_obra = v.reparto == "obra"`;
  si no, `can` del titular, `pre` = cantidad (en `eur`, sin multiplicar),
  `tot = round(can × pre, 2)`. `MOTIVO_FALTA_CAJA`/`MOTIVO_CAJA_CERO` solo
  salen por obra. Sin código nuevo.
- **front.** `importesDeFila` y `cantidadVinculado` deciden por
  `v.reparto`; «Caja · obra» y «caja de esta obra» solo con `obra`.
- **Lo que no basta.** `_sin_propuesta` (copiar el mes) copia `cantidad` y
  `comentario` de **toda** subfila, con `copiado = true` si hay cantidad: un
  resto por obra de un mes anterior (hoy, el comentario suelto de 2026/11) se
  propagaría al nuevo, invisible. La guarda de R11 lo corta (§6).

## 3. Ficheros a crear

Tests, sin red ni BBDD. api `tests/test_f080_caja_api.py` (R1, R2, R4, R5,
R11, R12); transfer `tests/test_f080_reglas_caja.py` (R6-R8); front
`tests/test_f080_caja_front.py` (R3, R9, como `test_f069_importes_front.py`).
Todos bajo `services/dedicacion-<servicio>/`.

## 4. Ficheros a modificar (solo api)

- `services/dedicacion-api/config/config.yaml` — `CAJA: {unidad: eur,
  reparto: pct}` y el comentario de `importes` (fuera «la caja se asigna a la
  obra»; dice que `obra` queda sin tipo y cita F-080).
- `services/dedicacion-api/application/use_cases.py` — `_sin_propuesta` con
  `tipos` (§6); `CopiarPeriodoAnterior` y `CopiarTrabajadorAnterior` ganan
  `__init__(self, tipos=None)` y se lo pasan.
- `services/dedicacion-api/interface_adapters/api/routes.py` —
  `CopiarPeriodoAnterior(_tipos(contenedor))` (l. ~267) y
  `CopiarTrabajadorAnterior(_tipos(contenedor))` (l. ~514).
- Los dos tests de requirements §5.
- `docs/ARCHITECTURE.md` — `#regla-vinculado`, «Cantidad y comentario»:
  «Hoy `CAJA` (€, `pct`), `VIAJE` (€, `pct`) y `VP` (km, `pct`)»; la viñeta
  «Por obra» dice que hoy ningún tipo lo usa; «Se omite» sin «falta la caja del
  mes»; en «Copiar el mes», que los restos por obra de un tipo por % no se
  copian (R11) ni se pasan al mes (D2); cita de la decisión del humano del
  2026-11-25 (petición y D1-D7).

## 5. Ficheros que NO se tocan

- El transfer entero (`CAN_CAJA`, `MOTIVO_FALTA_CAJA`, `MOTIVO_CAJA_CERO`,
  `REPARTO_OBRA`: mecanismo dormido, D1) y `static/js/app.js` con su CSS.
- api: `main.py`, `domain/importes.py` (`REPARTOS` sigue con `obra`),
  `registro_sigrid.py`, `traer_sigrid.py`, `schemas.py`, `orm_models.py`,
  `esquema.py`.
- Los tests de F-069 con `CAJA` por obra como fixture (prueban el mecanismo
  `obra`, que sigue) y `docs/INTEGRACION.md` (el contrato no cambia).

## 6. Clases y funciones (api): la guarda de la copia (R11)

`_sin_propuesta(lineas, tipos=None)` (application): si `tipo_de(v.tipo,
tipos)` es por %, la subfila llega con `cantidad=None, copiado=None,
comentario=None`; si no, como hoy (`copiado=None if v.cantidad is None else
True`). Sin `tipos` (los dobles de los tests de antes), como hoy. Las demás
columnas de la subfila (partida elegida), como hoy (F-050 R16, F-044 R8).

## 7. Datos: lo tecleado y lo registrado (D2, D3)

**Dónde vive.** La caja por obra, en `asignacion_vinculado` (`cantidad`
`Numeric(12, 2)`, `copiado` boolean, `comentario` `String(200)`, nulables;
única por `asignacion_id` × `vinculado_ide`); la caja del mes, en
`importe_vinculado` (`periodo_id` × `vinculado_ide`, `cantidad`, `copiado`,
`comentario`, `actualizado_en`, `actualizado_por`). Ambas de F-069 (§7.2).
**Sin DDL ni escritura de datos** en F-080.

**Abiertos (D2).** No hay cajas por obra con importe: nada que pasar al mes.
El comentario suelto («26-11», 2026/11, obra 0678) queda en su subfila:
invisible en el cuadrante (un por % no pinta el de la subfila), no viaja al
transfer (manda el del mes) y R11 no lo copia.

**Cerrados y ya registrados (D3).** No se tocan; lo escrito en Sigrid se
queda. Hoy no hay cajas con importe, luego tampoco registradas. Si volviera
a registrarse un mes con cajas por obra ya registradas:

- Sin caja del mes: cada caja se omite «falta el importe» **antes** de la
  idempotencia del transfer (paso 6); nada se escribe en Sigrid y la traza de
  la subfila pasa a `omitido` (la `sigrid_hmores_ide` se conserva), igual que
  hoy un km ya registrado al que se le borra la cantidad.
- Con caja del mes: las ya registradas siguen `ya_registrado` (mismo
  `synckey` `porcentajes:vin:{registro_id}:{recurso}` y `hmores_ide`; ni `can`
  ni `tot` cambian, F-069 D9) y su `tex` solo cambia por D20; **pero** las
  obras sin caja registrada recibirían su parte por %: ese mes contaría caja
  dos veces. Regla (D3 a): un mes con cajas por obra registradas no lleva
  caja del mes. M1 repite la lectura justo antes de desplegar.

## 8. Postventa y céntimos (D4, D5)

- **Postventa.** `registro_vinculados.py` (l. ~119) da al vinculado el
  destino del titular: los km ya van a postventa y VAR con su %, con la
  partida del titular (F-044 D4). La caja, igual (R6).
- **Céntimos.** Km y viajes no ajustan: `tot = round(can × pre, 2)` por
  línea, `can` = `porcentaje / 100` a 4 decimales (`registro_sigrid`, l.
  ~276). El descuadre es como mucho medio céntimo por línea; y un trabajador
  por debajo del 100 % reparte menos (F-044 D8, «sin normalizar»). Ajustar
  exigiría que alguien viera todas las líneas del trabajador a la vez: la api
  no multiplica (F-069) y el transfer recibe una petición por obra.

## 9. Despliegue (R13)

- **Solo la api** (imagen nueva). Transfer (`r20261121-1743`, F-069) y front
  ya tratan `pct` en `eur`: no se redespliegan.
- **Sin «Sincronizar Sigrid» ni otro paso manual**: el reparto se lee de
  `config.yaml` al arrancar; los vínculos de las cajas ya están en
  `recurso_vinculado`.
- Antes de desplegar, M1 (§10). Después, quien tenga el cuadrante abierto
  **recarga la página**: hasta entonces su editor enseña las casillas «Caja ·
  obra» de antes; un `PUT` desde ahí de una sola obra se guarda como caja del
  mes (R4) y dos, 422.

## 10. Verificación MANUAL (humano)

- **M1, justo antes de desplegar (solo lectura, producción).** Repetir la
  lectura del líder de `progress/manual_F-080.md`: `GET /api/v1/periodos` y
  `GET /api/v1/periodos/{anio}/{mes}/cuadrante?empresa={1,18,25,31}` desde la
  sesión del navegador; contar las subfilas de caja por obra con `cantidad`.
  Esperado: **0**. Si aparece alguna, **PARA** y vuelve al humano (D2, D3).
- **M3, local en modo pruebas** (`OBRA_PRUEBAS_FORZAR=true`): teclear 300 en
  la casilla «CAJA …» de un trabajador con dos obras al 60/40 (o una
  postventa); «⇪ Sigrid» de ese trabajador: el modal dice «180,00 € de 300,00
  €» y «120,00 € de 300,00 €»; **Cancelar** (solo preflight).
- **M4, producción tras desplegar**: Ctrl+F5; en el mes abierto, una casilla
  de caja por trabajador y ninguna «Caja · obra»; si se abre el modal, solo
  preflight y **Cancelar**.

(M2 retirada con la pasada de restos.)

## 11. Riesgos y alternativas descartadas

- **Deshacer** un `IMPORTES` anterior al despliegue podría reponer una caja
  por obra: invisible y sin registrar (el transfer usa la del mes); hoy no hay
  ninguna con importe.
- **F-071** (mes parcial): ya no hay caja con `can` 1; si ajusta el `can`,
  la caja se reparte sobre el ajustado, como los km. Anotarlo en su spec.
- Descartado **retirar el reparto `obra`** (D1 b): obliga a rehacer unos 18
  tests de F-069 con «caja» u «obra» en el nombre, más los del front, y no
  cambia nada de lo que se escribe; se puede limpiar después (`estandar`).
- Descartada **la pasada de restos al arrancar** (D2): no hay nada que pasar.
- Descartado **corte por periodo** (`pct_desde`, D3 b): `tipo_de` pasaría a
  depender del mes en una decena de llamadas; sin cajas registradas, sobra.

## 12. Frontera

**¿Cruza la frontera del proyecto? Sí, en lo que se escribe en Sigrid; no en
contratos.** Ni endpoint, ni clave, ni columna, ni variable de entorno nuevos;
el contrato api → transfer es el de F-069 (cambia el valor de `reparto` de la
caja, no su forma). Cambia **qué se escribe**: la caja pasa de una línea `CO`
con `can` 1 y `tot` = la caja de esa obra a una por línea del titular con
`can` = su % y `tot` = su parte (también en postventa). La base `dedicacion`
no cambia. `azure-apps/dedicacion.md`: nota del redespliegue de la api y, en
«Desde F-069», que la caja se reparte por % (F-080). Lo actualiza el líder en
un commit aparte (protocolo de `CLAUDE.md`). Aviso a `partes` (lo da el
humano): las `CO` de caja ya no llevan `can` 1.

## 13. Decisiones

| Decisión | Opciones | Recomendado | Decidido |
|---|---|---|---|
| D1 Alcance del código | (a) config + guarda de la copia; el reparto `obra` se queda en el código sin tipo; (b) además retirar `obra` (motivos de caja, «Caja · obra», «caja de esta obra») | (a): urgente, dos tests cambian en vez de ~18 y los del front, y lo que se escribe es lo mismo | (a), humano 2026-11-25 |
| D2 Cajas por obra ya tecleadas en periodos ABIERTOS | (a) sumarlas en la caja del mes al arrancar, sin revisar, con los comentarios unidos; (b) descartarlas (vaciar y teclear de nuevo); (c) dejarlas (invisibles, no se registran) | (a): no se pierde lo tecleado y nada se registra sin que alguien lo mire | sin pasada: no hay cajas por obra con importe (humano 2026-11-25: «d1 y d2 ignoralo, no hay nada que tocar ahi») |
| D3 Periodos CERRADOS y cajas por obra ya registradas | (a) no se tocan; no se pone caja del mes en un mes con cajas por obra registradas (M1 antes de desplegar); (b) corte por periodo: los meses anteriores siguen por obra | (a) si M1 no encuentra registradas que se vayan a volver a registrar; si las hay, volver a proponer (b) | (a), humano 2026-11-25 |
| D4 Postventa (y VAR) en el reparto | (a) como los km: la caja se reparte también a postventa y VAR con su %; (b) solo a obras normales | (a): es lo que hacen los km y ya no hay que tocar el transfer | (a), humano 2026-11-25 |
| D5 Céntimos | (a) como los km: cada línea redondeada, sin ajuste; (b) ajustar la diferencia en una línea | (a): ±½ céntimo por línea; (b) exige ver todas las líneas a la vez (§8) | (a), humano 2026-11-25 |
| D6 Rótulo de la caja pasada al mes | (a) el de F-069, «copiado del mes anterior, sin revisar»; (b) marca y texto nuevos («sumada de las cajas por obra») | (a): cero cambios en front y base; solo afecta al primer mes | retirada (sin pasada) |
| D7 Solape con F-077 (b) | (a) F-080 se queda con la caja por %; el líder recorta F-077 a los km en euros; (b) mover también los km en euros a F-080 | (a): F-080 es urgente y (a) de F-077 cambia otra unidad | (a), humano 2026-11-25 |
