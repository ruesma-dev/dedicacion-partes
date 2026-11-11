<!-- specs/F-069-importe-caja-km/design.md -->
# F-069 · Diseño: cantidad del mes de caja, viajes y km

D1-D9 **cerradas** (2026-11-11); **D10 y D11 abiertas** (§9). El diseño de la
lectura del precio por km (§7.1) queda a expensas de D10.

## 1. Servicios y límite

- **api** (dueña del dato, la cantidad se teclea como el %): tipos y unidad
  (config), tabla `importe_vinculado`, `PUT …/importes`, evento `IMPORTES`,
  la copia del mes, el cuadrante y el contrato (`importe_mensual`, `unidad`,
  `cantidad`, `copiado`). Guarda **km** para los `VP` y **€** para caja y
  viaje; no multiplica km por precio (el precio está en Sigrid, y Sigrid lo
  lee el transfer, como `reshor.pre`).
- **transfer** (única pluma): lee el precio por km (D10), calcula el importe
  y lo pone en `pre` en vez de `reshor.pre`, u omite con motivo. Partida,
  cuenta, pisado y capacidad, los de F-044/F-068.
- **front**: casillas en el editor, marcas en la subfila, km/precio/`pre`/
  `tot` en el modal; no reparte ni multiplica. Ningún servicio nuevo;
  `round(...)` solo en el transfer (la subfila no enseña la parte de obra).

## 2. Encaje

Editor (front) → `PUT …/importes` (api) → registro: `_sumar_vinculados`
añade las cuatro claves → `PasoVinculados` lee los precios por km (si hace
falta) → `decidir_vinculados` pone el importe en `pre` → lo de siempre. Las
peticiones van **por obra**: cada una calcula su `tot` sin ver las demás.

## 3. Ficheros a crear

- `services/dedicacion-api/domain/importes.py` — puro (§6.1).
- Tests, sin red ni BBDD: api `tests/test_f069_importes_dominio.py` (R1, R2,
  R5) y `test_f069_importes_api.py` (R3-R10, R14, R15; `TestClient` y dobles
  de UoW); transfer `tests/test_f069_reglas_importe.py` (R16-R22) y
  `test_f069_pipeline_importe.py` (R17, R22-R26; dobles de `conftest.py`);
  front `tests/test_f069_importes_front.py` (R11-R13, R27; arnés de F-044).

## 4. Ficheros a modificar

**api**
- `config/config.yaml` — `sync.vinculados.tipos_importe: {CAJA: eur,
  VIAJE: eur, VP: km}` con su comentario (D1, D2).
- `application/sync_pipeline.py` — `ConfigVinculados.tipos_importe:
  dict[str, str]` (validado al arrancar, R1).
- `infrastructure/db/orm_models.py` — `ImporteVinculadoORM` (§7.2).
- `domain/models.py` — `TipoEvento.IMPORTES`; `SubfilaVinculado.con_importe`,
  `.unidad`, `.cantidad`, `.copiado`; `CuadranteTrabajador.importes`.
- `domain/ports.py` — `ImporteRepository` (`de_trabajador`, `del_periodo`,
  `reemplazar`, `copiar_vacias`) y `UnitOfWork.importes`.
- `infrastructure/db/repositories.py` — `PgImporteRepository`; `subfilas_de`
  rellena los campos de cantidad (una lectura más solo si hay vinculados de
  cantidad); `SqlAlchemyUnitOfWork.importes`.
- `application/use_cases.py` — `GuardarImportes` (R4-R7);
  `DeshacerUltimaModificacion` con `IMPORTES`; `CopiarPeriodoAnterior` y
  `CopiarTrabajadorAnterior` llaman a `_copiar_importes` (R8);
  `ObtenerCuadrante` / `ObtenerFilaTrabajador` con `importes` (R9).
- `application/registro_sigrid.py` — `_sumar_vinculados` lee las cantidades
  del periodo (R15); `_vinculado(v, es_var, cantidades, tipos)` añade las
  cuatro claves solo a los de cantidad (R14).
- `interface_adapters/api/schemas.py` — `ImporteIn`, `ImportesIn`,
  `ImporteOut`; campos nuevos de `SubfilaOut`; `TrabajadorOut.importes = []`.
- `interface_adapters/api/routes.py` y `deps.py` — la ruta `PUT` y su caso.

**transfer**
- `domain/models/registro_models.py` — `VinculadoEntrada.importe_mensual:
  bool = False`, `.unidad`, `.cantidad`, `.copiado = False`;
  `AccionVinculado.km`, `.precio_km` (`None` por defecto).
- `interface_adapters/api/app.py` — `VinculadoIn` con los cuatro campos.
- `application/services/reglas_vinculados.py` — `precio_del_vinculado` y sus
  motivos; `decidir_vinculados(titular, linea, horas, precios_km=None)`.
- `application/pipelines/registro_vinculados.py` — `PasoVinculados.decidir`
  pide los precios por km una vez (perezoso, `_UnaVez`) y se los pasa.
- `infrastructure/sigrid/sigrid_write_client.py` — `precios_km(recursos)`
  (SELECT según D10, parametrizado, `truncated` es error) y su doble en
  `tests/conftest.py`.
- `prueba_escritura_porcentajes.py` — nada (ya lista y limpia `porcentajes:vin:`).

**front**
- `static/js/app.js` — `chipImporte` en `pintarEditor` (tras las
  incidencias), `state.importesEdicion`/`importesGuardados`,
  `cuerpoImportes` y su `PUT` en `guardarAhora` (patrón incidencias, R12);
  `construirCeldaVinculado` (`tipo`) con cantidad, «falta importe» o
  «copiado» (R13); `filaVinculado` del modal con km/precio/`tot`/`pre` (R27).
- `static/css/` — estilo de la casilla y de las marcas, sin dependencias.

**docs** — `docs/ARCHITECTURE.md` (`#regla-vinculado`: punto «Cantidad del
mes» con las decisiones citadas, «Qué se escribe» remite a él; tabla
`importe_vinculado`) y `docs/INTEGRACION.md` §1 (lectura del precio por km),
§5 (contrato, endpoint) y §7 (orden de despliegue, `tipos_importe`).

## 5. Ficheros que NO se tocan

- Transfer: `registro_pipeline.py` (solo cambia lo que `PasoVinculados`
  decide), `reglas_porcentajes.py`, la escritura (`stmt_insert_linea` ya
  escribe `can`, `pre`, `tot`) y las copias de `partes` (lista cerrada).
- Api: `domain/vinculados.py` y el sync de vinculados (`tipos_excluidos`
  sigue vacío); el export Excel (fuera, F-073 / F-038).
- Front: `main.py` (el proxy `/api/*` ya cubre la ruta).

## 6. Clases y funciones

### 6.1 api · `domain/importes.py` (domain, sin dependencias)

- `unidad_de(tipo: str | None, tipos: dict[str, str]) -> str | None` — R2:
  `eur`, `km` o `None` (no es de cantidad).
- `validar_cantidad(valor: object, unidad: str) -> Decimal | None` — R5:
  `None` pasa; número finito, ≥ 0, dos decimales como mucho (comparando
  `Decimal(str(valor))` con su cuantizado) y bajo el tope de su unidad; si
  no, `ImporteInvalido` (422). Booleanos y textos, inválidos.
- `a_copiar(origen: dict[int, Decimal], destino: dict[int, Decimal],
  vinculados: set[int]) -> dict[int, Decimal]` — R8: las del origen de
  `vinculados` que no están en el destino.
- `@dataclass(frozen=True) ImporteVinculado` — `vinculado_ide`, `tipo`,
  `tipo_res`, `cod`, `unidad`, `cantidad: Decimal | None`, `copiado: bool`.

### 6.2 transfer · `reglas_vinculados.py` (application, puro)

- `precio_del_vinculado(v, horas, precios_km) -> (hora, pre, km, precio_km,
  motivo)`. Sin `importe_mensual`: `hora_del_vinculado` como hoy (R22). Con
  él, en orden: sin hora por defecto ⇒ «sin hora» (R21); `copiado` ⇒
  «copiado sin revisar» (R20, si D11-A); `cantidad` nula ⇒ «falta el
  importe del mes» (R18); 0 ⇒ «importe 0 este mes» (R19); `eur` ⇒ `pre =
  cantidad`; `km` ⇒ `precio = precios_km.get(recurso)`, sin él o ≤ 0 «sin
  precio por km en Sigrid» (R17), si no `pre = round(km × precio, 2)`.
- Motivos ≤ 300 caracteres con `{tipo} {cod}` (cabe en `sigrid_motivo`).
- `necesita_precios_km(lineas) -> list[int]` — los `recurso_ide` `km` con
  cantidad > 0 y sin `copiado`: si está vacía, no se lee nada (R17).

### 6.3 api · `GuardarImportes` y la copia (application)

`GuardarImportes.ejecutar(uow, anio, mes, trabajador_ide, entrada, usuario,
*, filtro)`: periodo abierto o 404/409; trabajador o 404; cada elemento con
`validar_cantidad` en la unidad de su vinculado, que tiene que ser activo,
vigente, de cantidad y del trabajador (si no, 422); repetido, 422. Si la foto
cambia, `reemplazar` y evento `IMPORTES` (`[{vinculado_ide, cantidad,
copiado}]` de **todos** los del trabajador). Deshacer: vuelve a la foto de
antes, como `INCIDENCIAS`. `_copiar_importes(uow, origen_id, periodo_id,
trabajador_ide, usuario)`: tras la copia de líneas de ese trabajador (en el
periodo, solo los copiados), `a_copiar` y `copiar_vacias` con `copiado =
true`, y su evento `IMPORTES` si copió alguna (deshacer dos veces deshace la
copia entera; consta en `#regla-deshacer`).

### 6.4 front · `app.js`

`chipImporte(entrada, idx, editor)`: `tipo_res cod`, `<input
inputmode="decimal">` con la cantidad en formato español y su unidad; con
`copiado`, la marca y el botón «Revisado» (manda la misma cantidad). Al
teclear, `parsearCantidad` (coma o punto, vacío ⇒ `null`, lo demás tal cual:
la api lo rechaza) y `programarGuardado()`. El front no decide qué es
«revisado»: pinta `copiado` tal como llega.

## 7. SQL

### 7.1 Sigrid (solo lectura; la escritura es la de F-044 con otro `pre`)

`precios_km`: **pendiente de D10**. Lo leído el 2026-11-11 (§9, D10) no da
un precio por km por recurso. Cuando D10 diga la tabla y el campo: un
`SELECT` parametrizado por los `recurso_ide` (lotes como las demás
lecturas), alias `reside` y `precio`, `truncated` es error.

### 7.2 PostgreSQL `dedicacion` (ORM, única verdad)

`ImporteVinculadoORM` → `importe_vinculado`, tabla **nueva** (`create_all`,
sin `ALTER`): `id` PK · `periodo_id` FK `periodo.id` y `vinculado_ide` FK
`recurso_vinculado.ide`, NOT NULL, `UniqueConstraint` de los dos ·
`cantidad` `Numeric(12, 2)` NOT NULL (€ o km según el tipo, no se guarda la
unidad: es de la config) · `copiado` boolean NOT NULL default false ·
`actualizado_en` timestamptz (`now()`, `onupdate`) · `actualizado_por` text
NOT NULL. No cuelga de `asignacion` (`reemplazar` borra las líneas). Un
`null` del PUT borra la fila. Nada a nivel de servidor.

## 8. Contrato (api ↔ transfer)

`lineas[].vinculados` de `registro/preflight` y `registro/ejecutar` gana,
**solo en los de cantidad**, `importe_mensual: true`, `unidad`, `cantidad`
y `copiado` (en `partidas/propuesta(-lote)` no viajan). La respuesta gana
`km` y `precio_km` en cada entrada de `vinculados` (nulos fuera de `km`,
R26). Transfer viejo + api nueva: ignora las claves (`VinculadoIn` no
prohíbe extras) y omite «sin importe mensual», como hoy; api vieja +
transfer nuevo: F-044 tal cual. Orden **transfer → api → front** (R30).

## 9. Decisiones

### 9.1 Cerradas por el humano (2026-11-11: «d2, caja en euros, km en km y viaje en wuros. d7, copia importes. A a lo demas»)

- **D1 = A** · `CAJA`, `VP` y `VIAJE`, en una lista de `config.yaml`.
- **D2 = caja y viaje en €, `VP` en km** · importe del `VP` = km × precio
  unitario; a «¿de dónde sale el precio?»: «esta en sigrid como unitario de
  ese recurso» (→ D10). Sin negativos.
- **D3 = A** · casillas en el editor del trabajador, tras las incidencias.
- **D4 = A** · sin cantidad ⇒ ese vinculado se omite y lo demás se
  registra; 0 ⇒ no se escribe nada.
- **D5 = A** · `can` = % del titular, `pre` = importe del mes, `tot =
  round(can × pre, 2)`; descuadre de céntimos aceptado.
- **D6 = A** · líneas a mano: como F-044/F-064 (pisado marcado; otra partida
  ⇒ capacidad).
- **D7 = B** · copiar el mes copia las cantidades, como valor puesto y
  editable, con la marca `copiado` hasta que se teclea o se pulsa
  «Revisado» (R8, R11). Riesgo: registrar el gasto del mes pasado sin
  revisarlo (→ D11).
- **D8 = A** · sin normalizar. **D9 = A** · ya registrado no se edita.

### 9.2 Abiertas (las pregunta el líder al humano)

- **D10 · Dónde está en Sigrid «el unitario» de cada `VP`.** Leído el
  2026-11-11 vía `sigrid-api` (solo `SELECT`): `reshor` de la hora `KM`
  (46) tiene `pre`, `prenom`, `preven` a 0 en los `VP` salvo 3 con un
  **importe mensual** (VP0016 160, VP0046 600, VP0115 175; `candef` 1 en 43);
  `auxhor` 46 (`KM`, unidad 19 «ud») sin precio; `tarmob` sin filas de la
  hora 46; `rescen` y `tarres` sin filas de los `VP` mirados; `conext` solo
  el «Recurso Asociado»; `reshor.proide` 0. Lo único con precio por km es
  `auxgas` 8 «Kilometros» `pre` 0,1923 (tipo de gasto **global**, de las
  hojas de gastos; `hgvres` sin líneas suyas desde 2025). Las líneas `KM`
  de 2026 (602): 563 con `can` ≤ 1 y `pre` en € (6 a 1.069,20), 31 a 0 y 8
  con `can` = km y `pre` **0,20** (VP0111 724,5 km, VP0117, VP0137 2.018
  km; también en 2024-2025: VP0050, VP0078…), un 0,20 que no está en ninguna
  ficha leída. Opciones: (A) el humano dice la pantalla y el campo exactos
  de Sigrid (con un `VP` de ejemplo) y se lee de ahí; (B) un precio por km
  único en `config.yaml` (hoy 0,20, el de las líneas a mano); (C) `auxgas`
  «Kilometros» (0,1923; no coincide con el 0,20 de las líneas); (D) que
  Administración lo dé de alta en `reshor.pre` de la hora `KM` de cada `VP`
  (hoy ese campo lleva importes mensuales en 3 de ellos). **Recomiendo A**
  y, si no existe por recurso, B. **Sin D10 cerrada no se implementa
  `precios_km` (T3) ni se aprueba la spec.**
- **D11 · Cantidad copiada sin revisar al registrar** (R20). (A) Se omite
  «importe copiado del mes anterior sin revisar» hasta que se teclea o se
  pulsa «Revisado»: nunca se registra el gasto del mes pasado por descuido.
  (B) Se registra tal cual (la copia vale como dato) y el modal solo lo
  avisa. **Recomiendo A.**

Decididas por mí (técnicas): nombres `importe_vinculado`, `importe_mensual`,
`unidad`, `cantidad`, `copiado`, `IMPORTES`; topes; `PUT` aparte (patrón de
las incidencias); evento `IMPORTES` propio en la copia.

## 10. Riesgos, relaciones y avisos

- **F-071** (`can` ajustado por alta/baja): con D5 el importe se repartiría
  sobre el `can` ajustado y una parte quedaría sin imputar; su spec debe
  decidirlo (anotarlo allí). F-058 y F-054: sin cruce (F-054 no trae
  cantidades).
- **Octubre de 2026**: titulares ya registrados ⇒ cada vinculado se decide
  solo (F-044 R18): tecleadas las cantidades, registrar otra vez escribe solo
  los de cantidad. Aviso a `partes` (lo transmite el humano): dedicación
  escribirá `KM`, caja (`CO`/`CA`/`CD`/`CG`) y `VI` variables.
- Con D5-A la línea `KM` sale `can` = %, `pre` = km × precio: no como las 8
  líneas a mano con `can` = km y `pre` 0,20 (romperían la capacidad del
  vinculado, suma de `can` ≤ 1). El modal enseña los km y el precio (R27).
