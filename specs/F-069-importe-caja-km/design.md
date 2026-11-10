<!-- specs/F-069-importe-caja-km/design.md -->
# F-069 · Diseño: importe del mes de caja, km y viajes

**D1-D9 ABIERTAS** (§9); el diseño va con mi recomendación de cada una.

## 1. Servicios y límite

- **api** (dueña del dato, el importe se teclea como el %): tipos de importe
  (config), tabla `importe_vinculado`, `PUT …/importes`, evento `IMPORTES`,
  cuadrante y contrato (`importe_mensual`, `importe`).
- **transfer** (única pluma): con `importe_mensual`, `pre` = importe en vez
  de `reshor.pre`, u omitir con motivo; partida, cuenta, pisado y capacidad,
  los de F-044/F-068.
- **front**: casillas en el editor, marca en la subfila, `pre`/`tot` en el
  modal; no reparte ni calcula. Ningún servicio nuevo; `round(can × pre, 2)`
  sigue solo en el transfer (por eso la subfila no enseña la parte de obra).

## 2. Encaje

Editor (front) → `PUT …/importes` (api) → registro: `_sumar_vinculados`
añade `importe_mensual`/`importe` → `decidir_vinculados` usa el importe como
`pre` → el `PasoVinculados` de siempre. Las peticiones van **por obra**: cada
una calcula su `tot` sin ver las demás (por eso D5-B exigiría calcular en la
api).

## 3. Ficheros a crear

- `services/dedicacion-api/domain/importes.py` — puro (§6.1).
- Tests, sin red ni BBDD: api `tests/test_f069_importes_dominio.py` (R1, R2,
  R5) y `test_f069_importes_api.py` (R3-R10, R14, R15; `TestClient` y dobles
  de UoW); transfer `tests/test_f069_reglas_importe.py` (R16-R20) y
  `test_f069_pipeline_importe.py` (R16, R20-R24; dobles de `conftest.py`);
  front `tests/test_f069_importes_front.py` (R11-R13, R25; arnés de F-044).

## 4. Ficheros a modificar

**api**
- `config/config.yaml` — `sync.vinculados.tipos_importe: [CAJA, VP, VIAJE]`
  con su comentario (D1).
- `application/sync_pipeline.py` — `ConfigVinculados.tipos_importe:
  frozenset[str]` (lista de textos o falla al arrancar, R1).
- `infrastructure/db/orm_models.py` — `ImporteVinculadoORM` (§7.2).
- `domain/models.py` — `TipoEvento.IMPORTES`; `SubfilaVinculado.con_importe`
  e `.importe`; `CuadranteTrabajador.importes` (tupla de `ImporteVinculado`).
- `domain/ports.py` — `ImporteRepository` (`de_trabajador`, `del_periodo`,
  `reemplazar`) y `UnitOfWork.importes`.
- `infrastructure/db/repositories.py` — `PgImporteRepository`;
  `subfilas_de` rellena `con_importe`/`importe` (con los tipos y los importes
  del periodo, una lectura más solo si hay vinculados de importe);
  `SqlAlchemyUnitOfWork.importes`.
- `application/use_cases.py` — `GuardarImportes` (R4-R7);
  `DeshacerUltimaModificacion` con `IMPORTES`; `ObtenerCuadrante` /
  `ObtenerFilaTrabajador` con `importes` e `importe_anterior` (R9). Las dos
  copias del mes no se tocan: no copian importes (R8), y un test lo fija.
- `application/registro_sigrid.py` — `_sumar_vinculados` lee los importes
  del periodo (R15) y `_vinculado(v, es_var, importes)` añade las dos claves
  solo a los de importe (R14).
- `interface_adapters/api/schemas.py` — `ImporteIn`, `ImportesIn`,
  `ImporteOut`; `SubfilaOut.con_importe`/`.importe`;
  `TrabajadorOut.importes = []`.
- `interface_adapters/api/routes.py` — `PUT …/trabajadores/{ide}/importes`.
- `interface_adapters/api/deps.py` — el caso de uso con `tipos_importe`.

**transfer**
- `domain/models/registro_models.py` — `VinculadoEntrada.importe_mensual:
  bool = False`, `.importe: float | None = None`.
- `interface_adapters/api/app.py` — `VinculadoIn` con los mismos dos campos.
- `application/services/reglas_vinculados.py` — `precio_del_vinculado`,
  `MOTIVO_FALTA_IMPORTE`, `MOTIVO_IMPORTE_CERO`, `MOTIVO_SIN_HORA` y
  `decidir_vinculados` usándolos (§6.2).

**front**
- `static/js/app.js` — `chipImporte` en `pintarEditor` (tras las
  incidencias), `state.importesEdicion`/`importesGuardados`, `cuerpoImportes`
  y su `PUT` en `guardarAhora` (patrón de las incidencias, R12);
  `construirCeldaVinculado` (`tipo`) con el importe o «falta importe» (R13);
  `filaVinculado` del modal con `tot`/`pre` (R25).
- `static/css/` — estilo de la casilla y de la marca, sin dependencias.

**docs** — `docs/ARCHITECTURE.md` (`#regla-vinculado`: punto «Importe del
mes» con las decisiones citadas, «Qué se escribe» remite a él; tabla
`importe_vinculado` en la lista de tablas) y `docs/INTEGRACION.md` §5
(contrato, endpoint) y §7 (orden de despliegue, `tipos_importe`) (R27, R28).

## 5. Ficheros que NO se tocan

- Transfer: `registro_pipeline.py` y `registro_vinculados.py` (partida,
  idempotencia, pisado y capacidad no cambian, R21, R22; solo cambia el
  `pre`/`tot` que sale de `decidir_vinculados`); `sigrid_write_client.py`
  (ninguna SQL nueva; `stmt_insert_linea` ya escribe `can`, `pre`, `tot`);
  `reglas_porcentajes.py` y las copias de `partes` (lista cerrada).
- Api: `domain/vinculados.py` y el sync de vinculados (`tipos_excluidos`
  sigue vacío); el export Excel (fuera, F-073 / F-038).
- Front: `main.py` (el proxy `/api/*` ya cubre la ruta).

## 6. Clases y funciones

### 6.1 api · `domain/importes.py` (domain, sin dependencias)

- `es_de_importe(tipo: str | None, tipos: frozenset[str]) -> bool` — R2:
  `tipo.strip().upper() in tipos` (los de la config, ya normalizados).
- `validar_importe(valor: object) -> Decimal | None` — R5: `None` pasa;
  número finito, ≥ 0, ≤ 999.999,99 y sin más de dos decimales (comparando el
  `Decimal(str(valor))` con su cuantizado), si no `ImporteInvalido` (422).
  Booleanos y textos, inválidos.
- `@dataclass(frozen=True) ImporteVinculado` — `vinculado_ide`, `tipo`,
  `tipo_res`, `cod`, `importe: Decimal | None`,
  `importe_anterior: Decimal | None`.

### 6.2 transfer · `reglas_vinculados.py` (application, puro)

- `precio_del_vinculado(v: VinculadoEntrada, horas: list[HoraRecurso]) ->
  tuple[HoraRecurso | None, float | None, str | None]` — la hora, el `pre` y
  el motivo de omitir. Sin `importe_mensual`: `hora_del_vinculado` como hoy
  (R20; mismo motivo `MOTIVO_SIN_IMPORTE`). Con él: hora por defecto
  (`defecto`), sin ella `MOTIVO_SIN_HORA` (R19); `importe is None` ⇒
  `MOTIVO_FALTA_IMPORTE` (R17); `importe == 0` ⇒ `MOTIVO_IMPORTE_CERO`
  (R18); si no, `(hora, float(importe), None)` (R16).
- `decidir_vinculados` — usa `precio_del_vinculado` en vez de
  `hora_del_vinculado`; `tot = round(can × pre, 2)` sin cambios. Motivos
  (≤ 300 caracteres, con `{tipo} {cod}`): «falta el importe del mes del
  recurso vinculado …: no se registra; escríbelo en la fila del
  trabajador», «importe 0 este mes del recurso vinculado …: no se registra»
  y «el recurso vinculado … no tiene hora por defecto en Sigrid: no se
  registra».

### 6.3 api · `GuardarImportes` (application)

`ejecutar(uow, anio, mes, trabajador_ide, entrada, usuario, *, filtro)`:
periodo abierto o 404/409; trabajador o 404; cada elemento con
`validar_importe`; cada `vinculado_ide` entre los vinculados activos del
trabajador vigentes en el mes y de importe, si no 422 (`ImporteInvalido`);
repetido, 422. Compara la foto de antes con la prevista (sólo los que
vienen); si cambia, `uow.importes.reemplazar(...)` y evento `IMPORTES`
(`snapshot_antes`/`_despues`: `[{vinculado_ide, importe}]` de **todos** los
del trabajador en el periodo). Devuelve la fila del trabajador.
`DeshacerUltimaModificacion`: un `IMPORTES` devuelve la foto de antes
(borra los que no estaban), como `INCIDENCIAS`.

### 6.4 front · `app.js`

`chipImporte(entrada, idx, editor)`: `tipo_res cod`, `<input
inputmode="decimal">` con el importe en formato español y «mes anterior: X €»
si lo hay; al teclear, `parsearImporte` (coma o punto, vacío ⇒ `null`, lo
demás tal cual: la api lo rechaza) y `programarGuardado()`.

## 7. SQL

### 7.1 Sigrid

**Ninguna** lectura ni escritura nueva. La escritura es el `INSERT`/`UPDATE`
de F-044 con otro `pre`.

### 7.2 PostgreSQL `dedicacion` (ORM, única verdad)

`ImporteVinculadoORM` → `importe_vinculado`, tabla **nueva** (`create_all`,
sin `ALTER`): `id` PK · `periodo_id` FK `periodo.id` y `vinculado_ide` FK
`recurso_vinculado.ide`, NOT NULL, `UniqueConstraint` de los dos ·
`importe` `Numeric(12, 2)` NOT NULL · `actualizado_en` timestamptz
(`now()`, `onupdate`) · `actualizado_por` text NOT NULL. No cuelga de
`asignacion` (D7-C). Un `null` del PUT borra la fila. Una tabla más en la
base `dedicacion`; nada a nivel de servidor.

## 8. Contrato (api ↔ transfer)

`lineas[].vinculados` de `registro/preflight` y `registro/ejecutar` gana,
**solo en los de importe**, `importe_mensual: true` e `importe: number |
null` (en `partidas/propuesta(-lote)` no viajan). Respuesta sin cambios de
forma (R24). Transfer viejo + api nueva: ignora las claves (`VinculadoIn` no
prohíbe extras) y omite «sin importe mensual», como hoy; api vieja +
transfer nuevo: F-044 tal cual. Orden **transfer → api → front** (R28).

## 9. Decisiones ABIERTAS (las pregunta el líder al humano)

- **D1 · Qué tipos van por importe** (R1). (A) `CAJA`, `VP` y `VIAJE`, en
  una lista de `config.yaml`: los tres tienen `pre` 0 y un gasto que cambia
  cada mes (octubre: 177 + 49 + 74 líneas omitidas). (B) Solo `CAJA` y `VP`,
  como dice la petición; `VIAJE` seguiría «sin importe mensual». (C) Todo
  vinculado con `pre` 0 en su hora: la api no conoce `reshor.pre` (lo lee el
  transfer), habría que sincronizarlo, y un `pre` mal dado de alta en Sigrid
  cambiaría solo la forma de captura. **Recomiendo A** (B se consigue
  quitando `VIAJE` de la lista sin tocar código). Con A, el único `VP` con
  `pre` ≠ 0 también va por importe: lo tecleado manda.
- **D2 · Unidad** (R5). (A) Euros en todos: es lo que lleva hoy el `pre` de
  las `KM` a mano (199,36 / 292,88…), sin fuente de precio por km. (B) Km en
  los `VP` × un precio por km (¿`config.yaml`? ¿el `pre` del único `VP` que
  lo tiene?): una regla nueva y un dato que hoy no está en ningún sitio. Sin
  negativos (un abono se corrige a mano). **Recomiendo A.**
- **D3 · Dónde se pide** (R11-R13). (A) En el **editor del trabajador**, tras
  las incidencias, una casilla por caja/km/viaje con autoguardado: «al
  escribir en la línea del recurso te pregunte cantidad», sin interrumpir.
  (B) Ventana emergente al guardar si falta alguno: corta el tecleo. (C) En
  cada subfila: hay una **por obra** y el importe es del mes. (D) En el modal
  de registro: se descubre tarde. **Recomiendo A** + «falta importe» en la
  subfila.
- **D4 · Sin importe y con 0** (R17, R18). (A) Sin importe ⇒ ese vinculado se
  omite («falta el importe del mes») y lo demás se registra; 0 ⇒ nada
  («importe 0 este mes»); se registra otra vez al rellenarlo, sin duplicar.
  (B) El trabajador no se registra hasta tener todos. (C) Aviso a confirmar
  en el modal. (D) 0 ⇒ línea con `pre` y `tot` 0 (rastro que no imputa).
  **Recomiendo A** (un ticket que falta no frena el % de las personas).
- **D5 · Reparto y forma de la línea** (R16). (A) `can` = % del titular,
  `pre` = importe del mes, `tot = round(can × pre, 2)` en cada obra, como las
  `KM` a mano y como TF/CO/VE hoy; la suma de `tot` puede diferir del
  importe en algún céntimo (p. ej. 10,01 € al 50/50 da 5,005 por obra, que
  redondea a 5,00 o 5,01: la suma, 10,00 o 10,02). (B) Cuadrar
  céntimos dando el resto a la línea de mayor %: lo tendría que calcular la
  api (las peticiones van por obra), mandar `tot` y entonces `tot ≠ can ×
  pre` en Sigrid. (C) `can` = 1, `pre` = `tot` = importe × %: rompe la
  capacidad del vinculado (suma de `can` ≤ 1). **Recomiendo A.**
- **D6 · Líneas hechas a mano ya en el parte** (R21; 29 casos en octubre).
  (A) Como F-044/F-064: misma hora y partida ⇒ pisado a confirmar, marcado
  por defecto (lo tecleado sustituye a lo de a mano); otra partida ⇒ cuenta
  en la capacidad (sobrecarga si pasa de 1). (B) Como A, con ese pisado
  **desmarcado**. (C) Respetar: cualquier línea de ese recurso y hora en el
  mes ⇒ omitir «ya tiene gasto a mano». **Recomiendo A**; riesgo: una línea a
  mano en otra partida con `can` pequeño no llega a sobrecarga y el gasto
  saldría doble (se ve en el modal y en la MANUAL T13).
- **D7 · Persistencia y mes anterior** (R3, R8, R9). (A) Tabla
  `importe_vinculado` por periodo y vinculado; copiar el mes **no** copia
  importes (cambian cada mes: copiarlos registraría el gasto del mes
  pasado); el editor enseña el del mes anterior solo como referencia. (B)
  Copiar el mes los copia como sugerencia. (C) Guardarlo en
  `asignacion_vinculado` (por línea): sería por obra y se borra al
  sustituir las líneas. **Recomiendo A.**
- **D8 · Trabajador que no suma 100 %** (R16). (A) Sin normalizar, como F-044
  (al 80 % se imputa el 80 % del importe; el modal enseña el `tot`). (B)
  Normalizar el reparto al 100 % solo para los de importe. **Recomiendo A**
  (una sola regla para todos los vinculados; el 100 % ya se avisa).
- **D9 · Importe cambiado tras registrar** (R22). (A) Como el % hoy:
  `ya_registrado`, no se edita; se corrige a mano en Sigrid (o F-033). (B)
  Editar en su sitio nuestra línea si su `pre` difiere (UPDATE con guarda):
  cambia la idempotencia de F-044 y merece feature propia. **Recomiendo A.**

Decididas por mí (técnicas): nombres `importe_vinculado`, `importe_mensual`,
`importe`, `IMPORTES`; tope 999.999,99; el `PUT` aparte (patrón incidencias).

## 10. Riesgos, relaciones y avisos

- **F-071** (`can` ajustado por alta/baja): con D5-A el importe se
  repartiría sobre el `can` ajustado y una parte quedaría sin imputar; su
  spec debe decidirlo (anotarlo allí al aprobar esta). F-058 y F-054: sin
  cruce directo (F-054 no trae importes).
- **Octubre de 2026**: titulares ya registrados ⇒ cada vinculado se decide
  solo (F-044 R18): tecleados los importes, registrar otra vez escribe solo
  los vinculados de importe. Aviso a `partes` (lo transmite el humano):
  dedicación escribirá `KM`, caja (`CO`/`CA`/`CD`/`CG`) y `VI` variables.
- La forma de las líneas de **caja** a mano no está medida (la de `KM` sí);
  si el humano lo pide antes de aprobar D5, una lectura vía `sigrid-api`.
