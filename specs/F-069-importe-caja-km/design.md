<!-- specs/F-069-importe-caja-km/design.md -->
# F-069 · Diseño: caja por obra, km y viajes por %, con comentario

D1-D21 **cerradas por el humano** (§9); ninguna abierta. Enmienda del
2026-11-19 (D17-D21, review 1): §1, §4, §6.1, §6.3-§6.5, §7, §8, §9.2, §10.

## 1. Servicios y límite

- **api** (dueña del dato: cantidad y comentario se teclean como el %):
  tipos, unidad, reparto y `precio_km` (config versionada), `importe_vinculado`
  y columnas nuevas, `PUT …/importes`, evento `IMPORTES`, copia del mes,
  cuadrante, contrato y comentario traído. **No multiplica** ni conoce la
  marca de pruebas (D17).
- **transfer** (única pluma): importe (km × `precio_km`, del contrato), línea
  (por % o por obra), comentario en `tex` (también en una ya registrada,
  D20) y, al traer, el `tex` sin su marca. Partida, cuenta, pisado y
  capacidad, F-044/F-068. **front**: editor, columna «Comentario», subfila y
  modal; no calcula. Ningún servicio nuevo.

## 2. Encaje

Editor → `PUT …/importes`/`…/asignaciones` → `_sumar_vinculados` →
`decidir_vinculados` → `PasoVinculados` → `tex`; la caja de cada obra, en su línea.

## 3. Ficheros a crear

`services/dedicacion-api/domain/importes.py` (§6.1) y, en el transfer,
`application/services/texto_linea.py` (§4). Tests sin red ni BBDD: api
`test_f069_importes_dominio.py`, `_importes_api.py`, `_traer_comentarios.py`;
transfer `test_f069_reglas_importe.py`, `_pipeline_importe.py`, `_existentes_tex.py`,
`_tex_registrada.py` (D20); front `test_f069_importes_front.py`.

## 4. Ficheros a modificar

**api**
- `config/config.yaml` — `sync.vinculados.importes` (`CAJA {eur, obra}`,
  `VIAJE {eur, pct}`, `VP {km, pct}`) y `precio_km: 0.20`, validados al
  arrancar en `sync_pipeline.py` (`ConfigVinculados`, R1).
- `infrastructure/db/orm_models.py` — `ImporteVinculadoORM` (§7.2); `cantidad`,
  `copiado`, `comentario` en `AsignacionVinculadoORM`; `AsignacionORM.comentario`.
- `domain/models.py` — `TipoEvento.IMPORTES`; `SubfilaVinculado` y `Linea`
  con sus campos; `CuadranteTrabajador.importes`; `ImporteMes` con
  `cantidad` opcional (D19).
- `domain/ports.py` y `infrastructure/db/repositories.py` — `ImporteRepository`
  /`PgImporteRepository` (`de_trabajador`, `del_periodo`, `guardar`,
  `borrar`), `UnitOfWork.importes`; en `AsignacionRepository`,
  `guardar_subfila_importe` (cantidad, copiado y/o comentario de una subfila,
  sin tocar la línea), `poner_comentario` y `registradas` (R32); la función
  `importes_del_mes_de` (una lectura, R16); `_valores_subfila`/`_a_subfila`
  con lo nuevo (la traza no lo pisa, R30).
- `application/use_cases.py` — `GuardarImportes` (R4-R7, §6.3),
  `GuardarAsignaciones` con `comentario` (R9), deshacer `IMPORTES`, copias
  del mes con `_copiar_importes` (R8, R9) y cuadrante (R10).
- `registro_sigrid.py` — `_sumar_vinculados` (R16), claves de R15 y
  `comentario` de la línea; `traer_sigrid.py` — R32 (§6.4), sin marca (D17).
- `interface_adapters/api/` (`schemas.py`, `routes.py`, `deps.py`) —
  `ImporteIn` (con `revisado`, D18), `ImportesIn`, `ImporteOut`, campos de
  `SubfilaOut`, `LineaOut`, `LineaIn`, `TrabajadorOut`; la ruta `PUT`.

**transfer**
- `domain/models/registro_models.py` — `VinculadoEntrada` (`importe_mensual`,
  `unidad`, `reparto`, `cantidad`, `copiado`, `comentario`, `precio_km`),
  `LineaEntrada.comentario`, `AccionVinculado.km`/`.precio_km`/`.reparto`, y
  sus `In` de `app.py`; D20: `tex_nuevo` en `AccionLinea`/`AccionVinculado`,
  `LineaSigrid.obride` y `ResultadoRegistro.tex_actualizadas` (a `ejecutar`).
- `application/services/reglas_vinculados.py` — `precio_del_vinculado` y
  motivos; `decidir_vinculados` con `can`/`pre`/`tot` por reparto (§6.2).
- `texto_linea.py` (nuevo, puro): `tex_de(comentario, marca)` (R23; la marca
  solo en pruebas), `comentario_de_tex(tex, marca)` (R31) y
  `tex_a_actualizar(...)` (R26, §6.5).
- `application/pipelines/registro_pipeline.py` y `registro_vinculados.py` —
  `tex_de(...)` donde iba `tex = marca o None`; pasos 6 y 10 con D20.
- `infrastructure/sigrid/sigrid_write_client.py` — `lineas_registradas` con
  `tex`, `obride` y `con.est`; `stmt_editar_tex` (§7.1).
- `prueba_escritura_porcentajes.py` — `estado`/`limpiar`, marca como **prefijo**.
- `application/services/porcentajes_existentes.py` y su lectura — `tex` por
  línea con `comentario_de_tex` y las `porcentajes:vin:` del periodo (R31).

**front** — `static/js/app.js`: `chipImporte` (comentario, marca, «Revisado»)
y el comentario del titular (`chipEditable`); `cuerpoImportes` **solo con las
casillas cuya foto cambió** (review 1, cambio 1), `revisado: true` desde
«Revisado» (D18), comentario sin cantidad (D19); `PUT` en `guardarAhora`
(R12); columna `comentario`, subfila (R14) y modal con km, precio y «se
actualiza el comentario» (R29). `static/css/`, sin dependencias.

**docs** — `ARCHITECTURE.md` (`#regla-vinculado`, D17-D21; `#regla-traer-sigrid`,
§10) e `INTEGRACION.md` §5 (`revisado`, `tex_nuevo`, `tex_actualizadas`, `tex`
sin marca) y §7 (fuera la fila de la marca en la api) (R33).

## 5. Ficheros que NO se tocan

Transfer: `reglas_porcentajes.py`, `stmt_insert_linea`, `stmt_editar_linea`,
`_guarda` y las copias de `partes`. Api: `domain/vinculados.py`, el sync de
vinculados y el export Excel («Observaciones», vacía). Front: `main.py`.

## 6. Clases y funciones

### 6.1 api · `domain/importes.py` (domain, sin dependencias)
- `TipoCantidad(unidad: "eur" | "km", reparto: "pct" | "obra")` y
  `tipo_de(tipo, importes) -> TipoCantidad | None` (R2).
- `validar_cantidad(valor, unidad) -> Decimal | None` (R5: `Decimal(str(v))`
  contra su cuantizado; booleanos y textos, inválidos);
  `validar_comentario(texto) -> str | None` (sin espacios a los lados, vacío
  ⇒ `None`, > 200 ⇒ `ImporteInvalido`; nada más, D19); `a_copiar` (R8).
- `comentario_de_sigrid(tex) -> str | None` (R32): sin espacios, vacío ⇒
  `None`. **Sin marca** (D17): ni `MARCA_PRUEBAS` ni parámetro.

### 6.2 transfer · `reglas_vinculados.py` (application, puro)
`precio_del_vinculado(v, horas) -> (hora, can, pre, tot, km, precio_km,
motivo)`. Sin `importe_mensual`, F-044 (R24). Con él, en orden: sin hora por
defecto (`hora_del_vinculado`: `CO`, `KM`, `VI`) ⇒ «sin hora» (R22);
`copiado` ⇒ «sin revisar» (R21); nula ⇒ «falta el importe»; 0 ⇒ «importe 0»
(R20); por obra ⇒ `can` 1, `pre = tot = cantidad` (R18); por % ⇒ importe =
cantidad o `round(km × precio_km, 2)` (sin `precio_km` > 0, «sin precio por
km»), `can` del titular, `tot = round(can × pre, 2)` (R17). Motivos ≤ 300.

### 6.3 api · `GuardarImportes` y la copia (application)
`GuardarImportes.ejecutar(uow, anio, mes, trabajador_ide, entrada, usuario,
*, filtro)`: periodo abierto o 404/409; trabajador o 404; cada elemento
validado (R5, R6): por % ⇒ `importe_vinculado`; por obra ⇒ su subfila
(`guardar_subfila_importe`). `copiado`: el guardado si la cantidad no cambia
y no llega `revisado: true`; si no, `false` (D18). Cantidad `null` ⇒ sin
cantidad, con su comentario; por %, sin los dos ⇒ `borrar` (D19). Foto de
**todo** lo del trabajador; si cambia, se guarda y evento `IMPORTES`;
deshacer vuelve a la foto. `_copiar_importes`: tras la copia de líneas (con
sus subfilas, partida, cantidad y comentario), `copiado = true` en las
copiadas **con cantidad** y copia las del mes vacías; evento `IMPORTES`
propio (deshacer dos veces deshace la copia entera; `#regla-deshacer`).

### 6.4 api · comentario traído (sobre F-054; D16, D17, D21)
En `TraerDeSigrid`, con `existentes` (`tex` ya sin marca): por asignación y
subfila con traza (`sigrid_hmores_ide`) o `synckey` nuestra, si
`comentario_de_sigrid(tex)` difiere, se pone. Titular y caja, en el evento
`SIGRID` del trabajador (F-054 R25); las del mes, en `importe_vinculado` (de
su primera línea por `ide`), con un evento `IMPORTES` propio: deshacer
`SIGRID` no repone esa tabla (D21). Ni % ni cantidades.

### 6.5 transfer · comentario de una ya registrada (D20)
- **Paso 6** (titulares y `PasoVinculados.idempotencia`): el `hit` de
  `lineas_registradas` trae `tex`, `obride` y el `con.est` de su parte;
  `tex_a_actualizar(comentario, marca, hit, en_registro, obra_pruebas)`, pura,
  da `(tex_nuevo, motivo)`: sin comentario ⇒ nada (R23); `tex_de(...)` igual al
  leído (sin espacios a los lados) ⇒ nada; `synckey` sin `porcentajes:` ⇒ «no
  es nuestra»; parte no En registro ⇒ «parte cerrado»; en pruebas, otra
  `obride` ⇒ «fuera de la obra de pruebas». Sigue `ya_registrado` (la traza
  de la api no cambia); el motivo añade «se actualiza el comentario» o por qué no.
- **Paso 10** (`_actualizar_tex`; decisión 8, aceptada en la review 2 del
  2026-11-19): lo último de `ejecutar`, tras titulares y vinculados o sin nada
  más que escribir, y solo si alguna trae `tex_nuevo`. Relectura propia
  `lineas_para_editar`; las que siguen valiendo (nuestra, recurso y hora, sin
  enlaces, En registro), `stmt_editar_tex` en un lote propio; lectura de
  comprobación (`lineas_registradas(con_tex=True)`): `tex_actualizadas`, las
  que quedan; las demás, al log. Solo el `tex`; nunca `DELETE`.

## 7. SQL

### 7.1 Sigrid
Escritura: la de F-044 con otro `can`/`pre`/`tot` y `tex`, y `stmt_editar_tex`:
`UPDATE hmores SET tex = ?` con `_guarda` (`ide`, recurso, `can` y `synckey`
leídos, sin enlaces, parte En registro, `M*` o la hora del vinculado) y, en
pruebas, `AND obride = ?`. Lecturas parametrizadas, `truncated` es error:
`lineas_registradas`, si algo trae comentario (si no, la de hoy, R24), gana en
la misma lectura `CAST(tex AS NVARCHAR(400))`, `obride` y `con.est` (`LEFT
JOIN con`), también en la comprobación tras `stmt_editar_tex` (§6.5); y (R31)
las del periodo con `synckey LIKE 'porcentajes:vin:%'`.

### 7.2 PostgreSQL `dedicacion` (ORM, única verdad)
- `importe_vinculado` (nueva, `create_all`): `id` PK · `periodo_id` y
  `vinculado_ide` FK NOT NULL, únicos juntos · `cantidad` `Numeric(12, 2)`
  **nulable** (D19) · `copiado` boolean NOT NULL default false · `comentario`
  `String(200)` · `actualizado_en`, `actualizado_por`. Sin desplegar; en una
  BBDD local de la pasada 1, `cantidad` a nulable a mano (T16).
- `asignacion_vinculado`: `cantidad` `Numeric(12, 2)`, `copiado` boolean y
  `comentario` `String(200)`, nulables y sin default; `asignacion.comentario`
  `String(200)`. `ADD COLUMN` lo deriva `esquema.py`. Nada de servidor.

## 8. Contrato y frontera

`lineas[]` gana `comentario`; cada vinculado de cantidad, las claves de R15
(no en `partidas/propuesta(-lote)`). Respuesta: `km`, `precio_km`, `reparto`
y `tex_nuevo` (R28); `ejecutar`, `tex_actualizadas`. `existentes`: `tex` sin
marca y `vinculados_registrados` (R31). Front → api: `revisado`. Transfer
viejo + api nueva: ignora las claves (sin `extra="forbid"`), omite «sin
importe mensual» y no actualiza `tex`; api vieja + transfer nuevo: F-044 tal
cual. Orden **transfer → api → front**. **¿Cruza la frontera?** Sí: contrato,
`dedicacion` y `tex` en Sigrid ⇒ `azure-apps/dedicacion.md` (T17), `partes` (§10).

## 9. Decisiones (técnicas, mías: nombres, topes, `PUT` aparte, `limpiar` por prefijo)

### 9.1 Cerradas por el humano el 2026-11-11 y el 2026-11-12
2026-11-11 («d2, caja en euros, km en km y viaje en wuros. d7, copia
importes. A a lo demas»): **D1 = A** (`CAJA`, `VP`, `VIAJE`; el 2026-11-12
«viaje dejalo dentro, como euros tambien. aunque es posible que de momento
no se use») · **D2** caja y viaje en €, `VP` en km · **D3 = A** casillas en
el editor · **D4 = A** sin cantidad se omite, 0 no escribe · **D5 = A** por
% con `can` = %, `pre` = importe, `tot = can × pre` (`VP`, `VIAJE`) · **D6
= A** líneas a mano como F-044/F-064 · **D7 = B** copiar el mes copia las
cantidades, `copiado` · **D8 = A** sin normalizar · **D9 = A** ya
registrado no se edita (salvo su `tex`, D20).

**D10 = precio único 0,20 €/km en `config.yaml`** (Juan Romero, Dir. Admón.
y Control de Costes, correo «RE: parte km» del 2026-11-12: «que permita
meter los kilómetros totales y que el sistema multiplique por 0,20€. He
comprobado que se cumple la regla en todos los pdf analizados»). Leído el
2026-11-11: sin precio por km por recurso (`reshor`, `auxhor`, `tarmob`,
`rescen`, `conext`); `auxgas` 8 0,1923 global; 8 `KM` de 2026 a mano, `pre`
0,20. **Hora de caja**, la por defecto (Juan: «lleve al parte el tipo de
hora por defecto (CO)»). **Caja por obra** (humano, 2026-11-12: «la caja se
asigna a la obra, cada obra con la suya»). **Comentarios** (humano: «hay que
añadir una columna de comentarios, y esots deben traerse al sincronizar»;
Juan: «con el campo de observaciones podemos reflejar cualquier cosa que se
salga de la rutina»).

2026-11-12 («elijo opcion A en d11. a en las demas»): **D11 = A** la copiada sin
revisar se omite hasta teclearla o «Revisado» (R21; descartada B, registrarla) ·
**D12 = A** caja por línea, `can` 1, `pre = tot` = cantidad, «una caja por obra
y mes» (descartadas casilla en la subfila, B, y `pre = cantidad / %`, C) · **D13
= A** **cada** obra sin caja avisa y se omite; 0 ⇒ nada (R20; yo recomendaba B,
vacía = sin gasto) · **D14 = A** comentario en cada línea y vinculado de
cantidad (por %, uno al mes; caja, uno por obra), a `tex` · **D15 = A** al
traer, en nuestras ya registradas manda el `tex` de Sigrid; las a mano ajenas no
· **D16 = A** antes, F-054 en `dev` (hecho el 2026-11-18).

### 9.2 Cerradas por el humano el 2026-11-19, tras la review 1
- **D17 = A** («A: el transfer la quita»): `PRUEBA-PORC` no se copia en la
  api; el transfer publica el `tex` sin su marca (R31, R32). Descartada B:
  excepción en la lista cerrada de `CLAUDE.md`.
- **D18** («No cuenta»): cambiar solo el comentario de una copiada no la
  revisa; solo teclear la cantidad o «Revisado» (`revisado`, R4, R12). Con
  el cambio 1 de la review, el `PUT` lleva solo las casillas que cambiaron.
- **D19** («Guardarlo igual»; antes: «el comentario es un campo de texto que
  deberia llevarse sin chequeo del contenido»): el de km o viaje sin
  cantidad se guarda; sin cantidad no se registra nada (R3-R5, R20).
- **D20** («Que el cambio llegue a Sigrid»): en una ya registrada, si cambia
  el comentario, se cambia su `tex` sin tocar cantidades (R26, §6.5). Mías,
  por reglas vigentes: sin comentario, el `tex` se queda (R23); parte
  cerrado, línea ajena o, en pruebas, fuera de su obra ⇒ no se toca.
- **D21** («Sí, se acepta»): decisión 6 del implementer; el comentario traído
  de una cantidad del mes va en un evento `IMPORTES` (R32, §6.4).

## 10. Riesgos y avisos

- **F-071**: no debe tocar la caja (`can` 1); en `VP`/`VIAJE` repartiría
  sobre el `can` ajustado (anotarlo en su spec). **Octubre**: titulares ya
  registrados ⇒ cada vinculado se decide solo (F-044 R18). Aviso a `partes`
  (lo da el humano): escribiremos `KM`, `CO`, `VI` variables y `tex`, y
  cambiaremos el `tex` de nuestras ya registradas (D20).
- Horas mal codificadas a mano (`CO` en vez de `KM`): el gasto puede salir
  doble; se ve en la MANUAL. D15 + D20: sincronizar **antes** de registrar
  pisa el comentario tecleado con el de Sigrid (`#regla-traer-sigrid`).
