<!-- specs/F-069-importe-caja-km/design.md -->
# F-069 · Diseño: caja por obra, km y viajes por %, con comentario

D1-D10 **cerradas**; D11-D16 **abiertas** (§9), con mi recomendación.

## 1. Servicios y límite

- **api** (dueña del dato: la cantidad y el comentario se teclean como el
  %): tipos, unidad, reparto y `precio_km` (config versionada), tabla
  `importe_vinculado`, columnas nuevas, `PUT …/importes`, evento `IMPORTES`,
  copia del mes, cuadrante, contrato y, tras F-054, el comentario traído.
  Guarda km y € tal cual: **no multiplica**.
- **transfer** (única pluma): calcula el importe (km × `precio_km`, que le
  llega en el contrato) y la línea (por % o por obra), escribe el
  comentario en `tex` y, tras F-054, publica el `tex` al traer. Partida,
  cuenta, pisado y capacidad, los de F-044/F-068.
- **front**: editor, columna «Comentario», subfila y modal; no calcula.
  Ningún servicio nuevo; la cuenta solo en el transfer.

## 2. Encaje

Editor → `PUT …/importes` / `…/asignaciones` → `_sumar_vinculados` →
`decidir_vinculados` (`can`, `pre`, `tot` por reparto) → `PasoVinculados` →
`tex`. Las peticiones van por obra: la caja de cada obra viaja en su línea.

## 3. Ficheros a crear

- `services/dedicacion-api/domain/importes.py` (§6.1) y, en el transfer,
  `application/services/texto_linea.py` (§4). Tests sin red ni BBDD: api
  `test_f069_importes_dominio.py`, `_importes_api.py`, `_traer_comentarios.py`;
  transfer `test_f069_reglas_importe.py`, `_pipeline_importe.py`,
  `_existentes_tex.py`; front `test_f069_importes_front.py`.

## 4. Ficheros a modificar

**api**
- `config/config.yaml` — `sync.vinculados.importes: {CAJA: {unidad: eur,
  reparto: obra}, VIAJE: {eur, pct}, VP: {km, pct}}` y `precio_km: 0.20`.
- `application/sync_pipeline.py` — `ConfigVinculados.importes` y
  `.precio_km` (validados al arrancar, R1).
- `infrastructure/db/orm_models.py` — `ImporteVinculadoORM` (§7.2);
  `AsignacionVinculadoORM.cantidad`, `.copiado`, `.comentario`;
  `AsignacionORM.comentario` (columnas nuevas: el `ALTER … ADD COLUMN IF
  NOT EXISTS` lo deriva `esquema.py`).
- `domain/models.py` — `TipoEvento.IMPORTES`; `SubfilaVinculado` y `Linea`
  con sus campos nuevos; `CuadranteTrabajador.importes`.
- `domain/ports.py` y `infrastructure/db/repositories.py` —
  `ImporteRepository`/`PgImporteRepository` (`de_trabajador`,
  `del_periodo`, `reemplazar`, `copiar_vacias`), `UnitOfWork.importes`;
  `_valores_subfila` y `_a_subfila` con cantidad, copiado y comentario (así
  `reemplazar` los conserva, como la partida elegida, F-044 R8);
  `reemplazar` de asignaciones con `comentario`.
- `application/use_cases.py` — `GuardarImportes` (R4-R7); `GuardarAsignaciones`
  con `comentario` (R9); `DeshacerUltimaModificacion` con `IMPORTES`; las dos
  copias del mes con `_copiar_importes` y el comentario (R8, R9); cuadrante
  con `importes` y comentarios (R10).
- `application/registro_sigrid.py` — `_sumar_vinculados` (una lectura,
  R16), `_vinculado(...)` con las claves de R15 y la línea con `comentario`.
- `application/traer_sigrid.py` (de F-054) — R32 (§6.4). **Solo tras F-054.**
- `interface_adapters/api/schemas.py`, `routes.py`, `deps.py` — `ImporteIn`,
  `ImportesIn`, `ImporteOut`, campos nuevos de `SubfilaOut`, `LineaOut`,
  `LineaIn` y `TrabajadorOut`; la ruta `PUT`.

**transfer**
- `domain/models/registro_models.py` — `VinculadoEntrada` (`importe_mensual`,
  `unidad`, `reparto`, `cantidad`, `copiado`, `comentario`, `precio_km`),
  `LineaEntrada.comentario`, `AccionVinculado.km`/`.precio_km`/`.reparto`.
- `interface_adapters/api/app.py` — `VinculadoIn` y `LineaIn` iguales.
- `application/services/reglas_vinculados.py` — `precio_del_vinculado` y sus
  motivos; `decidir_vinculados` con `can`/`pre`/`tot` por reparto (§6.2).
- `texto_linea.py` (nuevo, puro): `tex_de(comentario, marca, tex_previo,
  editando) -> str | None` (R23).
- `application/pipelines/registro_pipeline.py` y `registro_vinculados.py` —
  donde hoy pasan `tex = marca o None`, pasan `tex_de(...)` de cada línea.
- `prueba_escritura_porcentajes.py` — `estado` y `limpiar` buscan la marca
  como **prefijo** (`tex LIKE marca + '%'`, con el prefijo de `synckey` de
  siempre): con comentario, el `tex` ya no es la marca sola.
- Tras F-054: `application/services/porcentajes_existentes.py` y su lectura
  en `sigrid_write_client.py` — `tex` en cada línea y la lectura de las
  `porcentajes:vin:` del periodo (R31).

**front** — `static/js/app.js`: `chipImporte` (por % y por obra, con
comentario, marca y «Revisado») en `pintarEditor` tras las incidencias;
comentario del titular en `chipEditable`; `cuerpoImportes`/`cuerpoLineas`
con comentario y el `PUT` en `guardarAhora` (patrón incidencias, R12);
columna `comentario` en `state.columnas` y en `construirCeldaVinculado`;
subfila con cantidad/«falta importe»/«copiado» (R14); `filaVinculado` del
modal (R29). `static/css/`, sin dependencias.

**docs** — `ARCHITECTURE.md` y `INTEGRACION.md` §5 y §7 (R33).

## 5. Ficheros que NO se tocan

Transfer: `reglas_porcentajes.py`, la SQL de escritura (ya acepta `can`,
`pre`, `tot`, `tex`) y las copias de `partes`. Api: `domain/vinculados.py`,
el sync de vinculados y el export Excel («Observaciones» sigue vacía). Front:
`main.py`.

## 6. Clases y funciones

### 6.1 api · `domain/importes.py` (domain, sin dependencias)

- `TipoCantidad(unidad: "eur" | "km", reparto: "pct" | "obra")` y
  `tipo_de(tipo, importes) -> TipoCantidad | None` (R2).
- `validar_cantidad(valor, unidad) -> Decimal | None` y
  `validar_comentario(texto) -> str | None` (R5: `Decimal(str(v))` contra
  su cuantizado; booleanos y textos inválidos; comentario sin espacios a
  los lados, vacío ⇒ `None`, > 200 ⇒ `ImporteInvalido`).
- `a_copiar(origen, destino) -> dict` — R8: las claves del origen que no
  están en el destino.
- `comentario_de_sigrid(tex, marca) -> str | None` — R32: quita la marca de
  pruebas del principio y los espacios; vacío ⇒ `None`.

### 6.2 transfer · `reglas_vinculados.py` (application, puro)

`precio_del_vinculado(v, horas) -> (hora, can, pre, tot, km, precio_km,
motivo)` dado el `can` del titular. Sin `importe_mensual`: F-044 tal cual
(R24). Con él, en orden: sin hora por defecto ⇒ «sin hora» (R22; la hora
es la de `hora_del_vinculado`, que ya elige el `defecto` de `reshor`, es
decir `res.horide`: `CO` en los 120 `CAJA` activos, `KM` en los 57 `VP`,
`VI` en los 22 `VIAJE`, leído el 2026-11-12); `copiado` ⇒ «sin revisar»
(R21); `cantidad` nula ⇒ «falta el importe» (R20); 0 ⇒ «importe 0»; por
obra ⇒ `can` 1, `pre = tot = cantidad` (R18); por % ⇒ importe = cantidad
(`eur`) o `round(km × precio_km, 2)` (`km`, sin `precio_km` > 0 ⇒ «sin
precio por km»), `can` del titular, `tot = round(can × pre, 2)` (R17).
Motivos ≤ 300 caracteres con `{tipo} {cod}` y, en caja, la obra.

### 6.3 api · `GuardarImportes` y la copia (application)

`GuardarImportes.ejecutar(uow, anio, mes, trabajador_ide, entrada, usuario,
*, filtro)`: periodo abierto o 404/409; trabajador o 404; cada elemento
validado (R5, R6): por % ⇒ `importe_vinculado`; por obra ⇒ la fila de
`asignacion_vinculado` de esa línea (se crea si no hay). Foto de **todo**
lo del trabajador (del mes y por obra); si cambia, se guarda y evento
`IMPORTES`; deshacer vuelve a la foto. `_copiar_importes`: tras la copia de
líneas (que ya copia las subfilas con su partida, y ahora con cantidad y
comentario), marca `copiado = true` en las copiadas y copia las del mes
vacías; evento `IMPORTES` propio (deshacer dos veces deshace la copia
entera; consta en `#regla-deshacer`).

### 6.4 api · comentario traído (tras F-054)

En `TraerDeSigrid`, con las líneas de `existentes`: por cada asignación y
cada subfila con traza (`sigrid_hmores_ide`) o `synckey` nuestra, si
`comentario_de_sigrid(tex)` difiere del guardado, se pone; las del mes, en
`importe_vinculado` (el de su primera línea por `ide`). Un evento `SIGRID`
por trabajador, como F-054 R25. No toca % ni cantidades.

## 7. SQL

### 7.1 Sigrid

Escritura: la de F-044 con otro `can`/`pre`/`tot` y `tex`. Lectura nueva
**solo tras F-054** (R31): las líneas del periodo con `synckey LIKE
'porcentajes:vin:%'` en obras de la empresa (`hmores` + `hmo` + `con`),
con `CAST(tex AS NVARCHAR(400))`, parametrizada; `truncated` es error.

### 7.2 PostgreSQL `dedicacion` (ORM, única verdad)

- `importe_vinculado` (nueva, `create_all`): `id` PK · `periodo_id` FK y
  `vinculado_ide` FK, NOT NULL, únicos juntos · `cantidad` `Numeric(12, 2)`
  NOT NULL · `copiado` boolean NOT NULL default false · `comentario`
  `String(200)` · `actualizado_en`, `actualizado_por`.
- `asignacion_vinculado`: `cantidad` `Numeric(12, 2)`, `copiado` boolean,
  `comentario` `String(200)`, nulables y sin default (como sus demás
  columnas). `asignacion`: `comentario` `String(200)` nulable.
- Unidad y reparto, de la config. Nada a nivel de servidor.

## 8. Contrato (api ↔ transfer)

`lineas[]` gana `comentario`; cada vinculado de cantidad, las claves de R15
(en `partidas/propuesta(-lote)` no viajan). Respuesta: `km`, `precio_km`,
`reparto` en `vinculados` (R28). Tras F-054, `existentes` gana `tex` por
línea y `vinculados_registrados` (R31). Transfer viejo + api nueva: ignora
las claves (sin `extra="forbid"`) y omite «sin importe mensual», como hoy;
api vieja + transfer nuevo: F-044 tal cual. Orden **transfer → api → front**.

## 9. Decisiones

### 9.1 Cerradas por el humano

2026-11-11 («d2, caja en euros, km en km y viaje en wuros. d7, copia
importes. A a lo demas»): **D1 = A** (`CAJA`, `VP`, `VIAJE`; el 2026-11-12
«viaje dejalo dentro, como euros tambien. aunque es posible que de momento
no se use») · **D2** caja y viaje en €, `VP` en km · **D3 = A** casillas en
el editor · **D4 = A** sin cantidad se omite, 0 no escribe · **D5 = A** por
% con `can` = %, `pre` = importe, `tot = can × pre` (ahora solo `VP` y
`VIAJE`) · **D6 = A** líneas a mano como F-044/F-064 · **D7 = B** copiar el
mes copia las cantidades marcadas `copiado` · **D8 = A** sin normalizar ·
**D9 = A** ya registrado no se edita.

**D10 = precio único 0,20 €/km en `config.yaml`**, no por recurso (Juan
Romero, Dir. Admón. y Control de Costes, correo «RE: parte km» del
2026-11-12: «que permita meter los kilómetros totales y que el sistema
multiplique por 0,20€. He comprobado que se cumple la regla en todos los
pdf analizados»). Queda lo leído el 2026-11-11: ningún precio por km por
recurso en `reshor`, `auxhor`, `tarmob`, `rescen` ni `conext`; `auxgas` 8
«Kilometros» 0,1923 (global); 8 líneas `KM` de 2026 a mano con `can` = km
y `pre` 0,20. **Hora de caja**: la por defecto del recurso, sin categorizar
(Juan, mismo correo: «lleve al parte el tipo de hora por defecto (CO)»); es
lo que ya hace `hora_del_vinculado` (§6.2). **Caja por obra** (humano,
2026-11-12: «la caja se asigna a la obra, cada obra con la suya»); el
riesgo que veía Juan (un gasto de una obra repartido entre todas las del
trabajador) desaparece. **Comentarios** (humano: «hay que añadir una
columna de comentarios, y esots deben traerse al sincronizar»; Juan: «con
el campo de observaciones podemos reflejar cualquier cosa que se salga de
la rutina»).

### 9.2 Abiertas (las pregunta el líder al humano)

- **D11 · Copiada sin revisar al registrar** (R21). (A) Se omite hasta
  teclearla o pulsar «Revisado». (B) Se registra tal cual. **Recomiendo A.**
- **D12 · Caja: dónde y qué línea** (R11, R18). (A) Casilla «Caja · obra»
  por línea en el editor (como D3) y línea `can` 1, `pre = tot` = cantidad,
  como las de caja a mano; la capacidad de F-044 queda en «una caja por obra
  y mes» (una a mano en esa obra ⇒ sobrecarga a confirmar). (B) Casilla en
  la subfila (hay una por obra, encaja, pero rompe «se teclea en el
  editor»). (C) `can` = % del titular y `pre = cantidad / %`: `tot` igual,
  pero `pre` raro y redondeos. **Recomiendo A.**
- **D13 · Caja vacía en una obra** (R20). (A) Como D4: «falta el importe»
  en esa obra (omisión que avisa; con 5 obras y gasto en 1, hay que poner 0
  en 4 o ver 4 avisos). (B) Vacía = sin gasto en esa obra, sin aviso; solo
  avisa si **ninguna** obra tiene caja. **Recomiendo B** (es la forma
  normal de la caja) — contradice D4 en caja: lo decide el humano.
- **D14 · Alcance del comentario** (R9, R13, R23). (A) En cada línea del
  titular y en cada vinculado de cantidad (por % uno al mes, que va a todas
  sus líneas; caja, uno por obra), todos a `tex`. (B) Solo vinculados de
  cantidad. **Recomiendo A** («una columna de comentarios»).
- **D15 · Comentario traído** (R31, R32). (A) De nuestras líneas ya
  registradas, el `tex` de Sigrid manda (Administración corrige allí; D9:
  lo de la app tras registrar no llega a Sigrid). (B) Solo si el de la app
  está vacío. (C) Como entradas a aceptar en la tabla de F-054. Las líneas a
  mano no nuestras no se traen. **Recomiendo A.**
- **D16 · Orden con F-054** (§7 de requirements). F-054 (rama
  `feature/F-054-sync-trae-porcentajes`, copia `porcentajes-f054`) no está
  en `dev`. (A) Cerrar y unir F-054, rebasar esta rama sobre `dev` y
  entonces implementar F-069 entera. (B) Implementar T1-T13 ya y dejar
  T14-T15 (traer) condicionadas a F-054 en `dev`. **Recomiendo A**: F-054
  está casi cerrada y las dos tocan el registro y el cuadrante.

Técnicas (mías): nombres, topes, `PUT` aparte, `limpiar` por prefijo.

## 10. Riesgos y avisos

- **F-071**: no debe tocar la caja (`can` 1); en `VP`/`VIAJE` repartiría
  sobre el `can` ajustado (anotarlo en su spec). **Octubre**: titulares ya
  registrados ⇒ cada vinculado se decide solo (F-044 R18). Aviso a `partes`
  (lo da el humano): escribiremos `KM`, `CO`, `VI` variables y `tex`.
- Horas mal codificadas a mano (`CO` en vez de `KM`, Juan): otra hora no
  choca y el gasto puede salir doble; se ve en la MANUAL.
