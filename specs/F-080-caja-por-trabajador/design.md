# F-080 · Diseño: la caja, una por trabajador y repartida por %

**Rigor: `critico`.** Disparadores 1 y 2 de «Niveles de rigor»
(`CHECKPOINTS.md`): cambia el **importe** de caja que se contabiliza en el
parte (`hmores.can`/`pre`/`tot`) y que el transfer **escribe en Sigrid de
producción** (`reglas_vinculados.precio_del_vinculado`); y la api reescribe
datos guardados de la base `dedicacion` al arrancar (§7).

## 1. Servicios y límite

| Servicio | Qué cambia | Por qué ahí |
|---|---|---|
| api | config (R1), pasada de restos al arrancar (R11-R18), guarda en la copia del mes (R19), docs | dueña del dato y de la config de tipos |
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
- **Lo que no basta.** (1) Las cajas ya tecleadas por obra en
  `asignacion_vinculado.cantidad/copiado/comentario` quedarían **invisibles**
  (el cuadrante no las pinta en un por %) y sin registrar: hay que decidir
  qué se hace (D2, §7). (2) `_sin_propuesta` (copiar el mes) copia la
  `cantidad` de **toda** subfila con `copiado = true`: los restos de un mes
  cerrado se propagarían al nuevo (R19, §6.2).

## 3. Ficheros a crear

Tests, sin red ni BBDD. api `tests/test_f080_caja_api.py` (R1, R2, R4, R5,
R19, R20) y `tests/test_f080_restos.py` (R11-R18, UoW falsa como en
`test_f069_importes_api.py`, `caplog`); transfer
`tests/test_f080_reglas_caja.py` (R6-R8); front `tests/test_f080_caja_front.py`
(R3, R9). Todos bajo `services/dedicacion-<servicio>/`.

## 4. Ficheros a modificar (solo api)

- `services/dedicacion-api/config/config.yaml` — `CAJA: {unidad: eur,
  reparto: pct}` y el comentario de `importes` (fuera «la caja se asigna a la
  obra»; dice que `obra` queda sin tipo y cita F-080).
- `services/dedicacion-api/application/use_cases.py` —
  `PasarRestosAlMes` (§6.1), junto a `GuardarImportes`, reutilizando
  `_foto_importes`, `_aplicar_foto` y `_snapshot_importes`; `_sin_propuesta`
  con `tipos` (§6.2); `CopiarPeriodoAnterior` y `CopiarTrabajadorAnterior`
  ganan `__init__(self, tipos=None)` y se lo pasan.
- `services/dedicacion-api/interface_adapters/api/routes.py` —
  `CopiarPeriodoAnterior(_tipos(contenedor))` (l. ~267) y
  `CopiarTrabajadorAnterior(_tipos(contenedor))` (l. ~514).
- `services/dedicacion-api/main.py` — paso 3 bis tras `sincronizar_esquema`:
  `pasar_restos_al_mes(engine, tipos)` (§6.1), con los tipos de
  `ConfigVinculados.desde_config(cargar_config()["sync"]["vinculados"])`.
  Docstring del módulo con el paso nuevo.
- Los dos tests de requirements §6.
- `docs/ARCHITECTURE.md` — `#regla-vinculado`, «Cantidad y comentario»:
  «Hoy `CAJA` (€, `pct`), `VIAJE` (€, `pct`) y `VP` (km, `pct`)»; la viñeta
  «Por obra» dice que hoy ningún tipo lo usa; «Se omite» sin «falta la caja del
  mes»; viñeta nueva «Restos por obra (F-080)» con R11-R19; cita de la
  decisión del humano (2026-11-25 y la de D1-D7).

## 5. Ficheros que NO se tocan

- El transfer entero (`CAN_CAJA`, `MOTIVO_FALTA_CAJA`, `MOTIVO_CAJA_CERO`,
  `REPARTO_OBRA`: mecanismo dormido, D1) y `static/js/app.js` con su CSS.
- api: `domain/importes.py` (`REPARTOS` sigue con `obra`), `registro_sigrid.py`,
  `traer_sigrid.py`, `schemas.py`, `orm_models.py`, `esquema.py`.
- Los tests de F-069 con `CAJA` por obra como fixture (prueban el mecanismo
  `obra`, que sigue) y `docs/INTEGRACION.md` (el contrato no cambia).

## 6. Clases y funciones (api)

### 6.1 `PasarRestosAlMes` (application) y su llamada (main)

`PasarRestosAlMes(tipos).ejecutar(uow) -> ResumenRestos(pasados: int,
periodos: int, saltados: int)`. Para cada periodo de `uow.periodos.listar()`
con estado `ABIERTO` y cada trabajador de
`uow.asignaciones.lineas_del_periodo(pid)`:

1. **Restos** de cada vinculado `vid` de tipo por % (`tipo_de`): sus
   subfilas con `cantidad` no nula, `comentario` o `copiado`, en el orden de
   las líneas (código de obra, postventa). Sin restos, nada.
2. Alguna subfila de `vid` con `sigrid_estado == "registrado"` ⇒ saltado,
   `logger.warning` (R14). Suma > `TOPES["eur"]` (o el de su unidad) ⇒
   saltado y aviso (R15).
3. `mes = uow.importes.de_trabajador(pid, t)`; foto `antes =
   _foto_importes(lineas, mes)`; `despues` = `antes` sin las claves
   `(vid, obra, pv)` de los restos y, **si `vid` no está en `mes`**, con
   `(vid, None, False) = (suma, suma is not None, comentario)` (R11, R13).
4. Si `despues != antes`: `_aplicar_foto(uow, pid, t, despues, USUARIO)` y
   `uow.eventos.registrar(pid, t, TipoEvento.IMPORTES, USUARIO,
   _snapshot_importes(antes), _snapshot_importes(despues))` (R12), con
   `USUARIO = "arranque F-080"`.

Un único `uow.commit()` al final (todo o nada). Comentario:
`_unir_comentarios(textos) -> str | None`, función pura (distintos, sin
vacíos, « · », `[:200]`). Una segunda pasada no encuentra restos (R16).

`pasar_restos_al_mes(engine, tipos)` (en `application/use_cases.py` o un
`application/restos_por_obra.py` si el implementer lo prefiere, sin lógica
nueva): abre `SqlAlchemyUnitOfWork(sessionmaker(engine))`, llama a
`ejecutar`, `logger.info` con la línea de R18; ante **cualquier** excepción,
`rollback`, `logger.exception` y vuelve sin relanzar (R17). Sin tipos por %,
no lee nada.

### 6.2 Guarda de la copia (R19)

`_sin_propuesta(lineas, tipos=None)`: si `tipo_de(v.tipo, tipos)` es por %,
la subfila llega con `cantidad=None, copiado=None, comentario=None`; si no,
como hoy (`copiado=None if v.cantidad is None else True`). Sin `tipos` (los
dobles de los tests de antes), como hoy.

## 7. Datos: lo tecleado y lo registrado (D2, D3)

**Dónde vive hoy.** La caja por obra, en `asignacion_vinculado` (`cantidad`
`Numeric(12, 2)`, `copiado` boolean, `comentario` `String(200)`, nulables;
única por `asignacion_id` × `vinculado_ide`); la caja del mes irá a
`importe_vinculado` (`periodo_id` × `vinculado_ide`, `cantidad`, `copiado`,
`comentario`, `actualizado_en`, `actualizado_por`). Ambas de F-069 (§7.2).
**Sin DDL**: solo filas, por los repositorios de siempre
(`guardar_subfila_importe`, `importes.guardar`, `eventos.registrar`).

**Abiertos (D2).** Recomendado (a): sumar en la caja del mes, **sin revisar**.
Quien tecleó 100 € en la obra A y 50 € en la B ve «CAJA … 150,00 € · copiado
del mes anterior, sin revisar» (D6: el mismo rótulo de F-069; el texto no es
exacto, el efecto sí: no se registra hasta que alguien la mira). Al
registrar, se reparte por %, no 100/50: por eso pide revisión.

**Cerrados y ya registrados (D3).** No se tocan (R14, R16): sus restos
quedan en la base, invisibles en el cuadrante, y lo escrito en Sigrid se
queda. Volver a registrar un mes con cajas por obra ya registradas:

- Sin caja del mes (lo normal tras R14): cada caja se omite «falta el
  importe» **antes** de la idempotencia del transfer (paso 6); nada se escribe
  en Sigrid y la traza de la subfila pasa a `omitido` (la `sigrid_hmores_ide`
  se conserva), igual que hoy un km ya registrado al que se le borra la
  cantidad.
- Si alguien teclea la caja del mes en ese mes: las ya registradas siguen
  `ya_registrado` (mismo `synckey` `porcentajes:vin:{registro_id}:{recurso}`
  y `hmores_ide`; ni `can` ni `tot` cambian, F-069 D9) y su `tex` solo cambia
  por D20; **pero** las obras sin caja registrada recibirían su parte por %:
  ese mes contaría caja dos veces. Por eso la regla (D3 a): un mes con cajas
  por obra ya registradas no lleva caja del mes. M1 (antes de desplegar)
  dice si existe alguno; si existe y se quiere volver a registrar, **PARA**
  y se vuelve a proponer D3 (b).

## 8. Postventa y céntimos (D4, D5)

- **Postventa.** `registro_vinculados.py` (l. ~119) da al vinculado el
  destino del titular: los km ya van a postventa y VAR con su %, con la
  partida del titular (F-044 D4). La caja, igual (R6); hoy también tenía
  casilla en cada postventa.
- **Céntimos.** Km y viajes no ajustan: `tot = round(can × pre, 2)` por
  línea, `can` = `porcentaje / 100` a 4 decimales (`registro_sigrid`, l.
  ~276). El descuadre es como mucho medio céntimo por línea; y un trabajador
  por debajo del 100 % reparte menos (F-044 D8, «sin normalizar»). Ajustar
  exigiría que alguien viera todas las líneas del trabajador a la vez: la api
  no multiplica (F-069) y el transfer recibe una petición por obra.

## 9. Despliegue (R21)

- **Solo la api** (imagen nueva). Transfer (`r20261121-1743`, F-069) y front
  ya tratan `pct` en `eur`: no se redespliegan.
- **Sin «Sincronizar Sigrid»**: el reparto se lee de `config.yaml` al
  arrancar; los vínculos de las cajas ya están en `recurso_vinculado`.
- **Paso a comprobar (explícito).** Tras desplegar, buscar en Log Analytics
  la línea `F-080:` de R18 de la revisión nueva (lección de F-074: un paso que
  no se mira se salta). Sin esa línea, la pasada no corrió: se para.
- Quien tenga el cuadrante abierto **recarga la página**: hasta entonces su
  editor enseña las casillas «Caja · obra» de antes; un `PUT` desde ahí de una
  sola obra se guarda como caja del mes (R4) y dos, 422.

## 10. Verificación MANUAL (humano)

- **M1, antes de desplegar (solo lectura, base `dedicacion` que usa la api
  desplegada).** `SELECT p.anio, p.mes, p.estado, count(*) AS restos,
  count(*) FILTER (WHERE av.sigrid_estado = 'registrado') AS registradas FROM
  asignacion_vinculado av JOIN asignacion a ON a.id = av.asignacion_id JOIN
  periodo p ON p.id = a.periodo_id JOIN recurso_vinculado rv ON rv.ide =
  av.vinculado_ide WHERE upper(replace(rv.tipo, ' ', '')) = 'CAJA' AND
  (av.cantidad IS NOT NULL OR av.comentario IS NOT NULL) GROUP BY 1, 2, 3
  ORDER BY 1, 2;` Anotar el resultado; `registradas > 0` ⇒ aplicar D3.
- **M2, local.** En `dev`, teclear dos cajas por obra (100 y 50) a un
  trabajador de un periodo abierto de la base **local**; arrancar la api de
  la rama: log `F-080: 1 vinculados…`, el cuadrante con una casilla «CAJA …
  150,00 €» copiada sin revisar; rearrancar: `F-080: 0 …` (idempotente).
- **M3, local en modo pruebas** (`OBRA_PRUEBAS_FORZAR=true`): «Revisado» o
  teclear 300; «⇪ Sigrid» de ese trabajador (dos obras al 60/40 o una
  postventa): el modal dice «180,00 € de 300,00 €» y «120,00 € de 300,00 €»;
  **Cancelar** (solo preflight).
- **M4, producción tras desplegar**: la línea `F-080:` (§9); Ctrl+F5; en el
  mes abierto, una casilla de caja por trabajador y ninguna «Caja · obra»; si
  se abre el modal, solo preflight y **Cancelar**.

## 11. Riesgos y alternativas descartadas

- **Deshacer** un `IMPORTES` anterior al despliegue repone restos por obra:
  invisibles, no se registran; el arranque siguiente los trata (R11, R13).
- **F-071** (mes parcial): ya no hay caja con `can` 1; si ajusta el `can`,
  la caja se reparte sobre el ajustado, como los km. Anotarlo en su spec.
- Descartado **retirar el reparto `obra`** (D1 b): obliga a rehacer unos 18
  tests de F-069 con «caja» u «obra» en el nombre, más los del front, y no
  cambia nada de lo que se escribe; se puede limpiar después (`estandar`).
- Descartado **un comando a mano** para los restos: un paso manual contra la
  base desplegada, lo que falló en F-074; al arrancar es idempotente y deja log.
- Descartado **corte por periodo** (`pct_desde` en la config, D3 b) como
  primera opción: `tipo_de` pasaría a depender del mes en una decena de
  llamadas (cuadrante, copia entre dos meses, registro, traer). Queda como
  plan B si M1 encuentra cajas registradas que haya que volver a registrar.

## 12. Frontera

**¿Cruza la frontera del proyecto? Sí, en lo que se escribe en Sigrid; no en
contratos.** Ni endpoint, ni clave, ni columna, ni variable de entorno nuevos;
el contrato api → transfer es el de F-069 (cambia el valor de `reparto` de la
caja, no su forma). Cambia **qué se escribe**: la caja pasa de una línea `CO`
con `can` 1 y `tot` = la caja de esa obra a una por línea del titular con
`can` = su % y `tot` = su parte (también en postventa). La base `dedicacion`
(compartida al desplegar) recibe filas, sin DDL ni tocar el servidor.
`azure-apps/dedicacion.md`: nota del redespliegue de la api y, en «Desde
F-069», que la caja se reparte por % (F-080) y la pasada de restos al
arrancar. Lo actualiza el líder en un commit aparte (protocolo de
`CLAUDE.md`). Aviso a `partes` (lo da el humano): las `CO` de caja ya no
llevan `can` 1.

## 13. Decisiones

| Decisión | Opciones | Recomendado | Decidido |
|---|---|---|---|
| D1 Alcance del código | (a) config + pasada de restos + guarda de la copia; el reparto `obra` se queda en el código sin tipo; (b) además retirar `obra` (motivos de caja, «Caja · obra», «caja de esta obra») | (a): urgente, dos tests cambian en vez de ~18 y los del front, y lo que se escribe es lo mismo | |
| D2 Cajas por obra ya tecleadas en periodos ABIERTOS | (a) sumarlas en la caja del mes al arrancar, sin revisar, con los comentarios unidos; (b) descartarlas (vaciar y teclear de nuevo); (c) dejarlas (invisibles, no se registran) | (a): no se pierde lo tecleado y nada se registra sin que alguien lo mire | |
| D3 Periodos CERRADOS y cajas por obra ya registradas | (a) no se tocan; no se pone caja del mes en un mes con cajas por obra registradas (M1 antes de desplegar); (b) corte por periodo: los meses anteriores siguen por obra | (a) si M1 no encuentra registradas que se vayan a volver a registrar; si las hay, volver a proponer (b) | |
| D4 Postventa (y VAR) en el reparto | (a) como los km: la caja se reparte también a postventa y VAR con su %; (b) solo a obras normales | (a): es lo que hacen los km y ya no hay que tocar el transfer | |
| D5 Céntimos | (a) como los km: cada línea redondeada, sin ajuste; (b) ajustar la diferencia en una línea | (a): ±½ céntimo por línea; (b) exige ver todas las líneas a la vez (§8) | |
| D6 Rótulo de la caja pasada al mes | (a) el de F-069, «copiado del mes anterior, sin revisar»; (b) marca y texto nuevos («sumada de las cajas por obra») | (a): cero cambios en front y base; solo afecta al primer mes | |
| D7 Solape con F-077 (b) | (a) F-080 se queda con la caja por %; el líder recorta F-077 a los km en euros; (b) mover también los km en euros a F-080 | (a): F-080 es urgente y (a) de F-077 cambia otra unidad | |
