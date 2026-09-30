<!-- progress/explore_grafico_parte.md -->
# Exploración: «el gráfico del parte»

> Encargado por el humano el 2026-09-02 al pedir que el registro de porcentajes
> guarde también «el gráfico del parte», avisando de que «la BBDD de gráficos es
> `ruesma_rep`, no `ruesma`».
>
> **Nota de procedencia:** lo exploró un subagente de solo lectura que no tenía
> herramientas de escritura, así que devolvió el informe por chat y lo persistió
> el líder. Error de encargo del líder, no del explorador.
>
> **NO es una spec ni una propuesta aprobada.** Son hechos con cita para decidir.

## 1 · Qué es el gráfico del parte

**Confianza ALTA sobre el mecanismo, MEDIA sobre que aplique a un parte `tip=35`.**

En Sigrid, «gráfico» **no** es una gráfica: es como el ERP llama a un **documento
adjunto** (PDF, imagen, escaneo). Son dos tablas y un enlace:

| Tabla | Papel | Referencia |
|---|---|---|
| `gra` — «Gráficos» | El documento. `ide` (PK), `cod` (128), `emp`, `res` (48, descripción), `nom`/`nomori` (255, nombre de fichero), `fec`, `usu`, **`ima` (binario ilimitado = EL BLOB)**, `gratipide` → `auxgra`, `vin` (modo de almacenamiento), `guid`, `tex` («Camino») | `azure-apps/sigrid_tablas.md:14408-14439` |
| `rcg` — «Gráficos en conceptos» | N:N que ata el gráfico al concepto: `ide`, **`con`** (→`con.ide`), **`gra`** (→`gra.ide`), `pos`, `cla` | `azure-apps/sigrid_tablas.md:19529-19534` |
| `auxgra` — «Documental: tipo de gráfico» | Catálogo de clases (`cod`, `res`, `tammax`, `tipaso`) | `azure-apps/sigrid_tablas.md:2026-2040` |

**Relación con lo que el transfer ya escribe.** El parte de trabajo es un `con`
con `tip=35`, y `hmo.ide == con.ide`
(`services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py:4-11`).
Como `rcg.con` apunta a `con.ide`, el gráfico se colgaría del `ide` del parte que
el pipeline ya maneja. Las líneas `hmores` no tienen enganche documental: **el
gráfico va a la cabecera, no a la línea**.

Detalle útil: `rcg.pos` va en múltiplos de 64, la misma convención que
`hmores.pos` (`settings.paso_pos = 64`, `config/settings.py:44`).

**Candidatos descartados o dudosos**

- `dog` («Documento», con `graima` binario) + `condog`
  (`sigrid_tablas.md:9379-9412` y `:6029-6034`): segundo canal documental de
  Sigrid, más rico. **Confianza BAJA** de que sea lo que el humano llama
  «gráfico»: el término está reservado a `gra`/`rcg` en todo el ecosistema.
- El literal `grafico` de `sigrid_tablas.md:12545` es basura de paginación del
  autodocumentador, no una tabla.
- **No existe ninguna tabla `hmogra` ni `hmodog`.** Las `hmo*` del diccionario
  son `hmo`, `hmores`, `hmomed`, `hmorespro`, `hmoval`, `hmorec`, `hmoobr`,
  `hmomix`, `hmofacdef`, `hmoacc`. Ninguna documental.

**Hueco:** no se ha verificado que la pantalla del parte de trabajo (`tip=35`)
tenga pestaña de gráficos ni qué `auxgra.gratipide` le tocaría. El único caso
medido con datos reales es el de reclamaciones de posventa (`con.tip=708`).

## 2 · `ruesma` vs `ruesma_rep`: los hechos

**La documentación contradice a la vez al `CLAUDE.md` y, en parte, al humano. El
humano tiene razón en lo esencial.**

**Hecho 1 — `ruesma_rep` NO es una réplica.** La documentación autoritativa de la
pasarela lo dice explícitamente:

- «no son una base y su réplica: son dos bases con **propósitos distintos**»
  — `azure-apps/sigrid_api.md:125-126`
- `ruesma` = base de NEGOCIO; `ruesma_rep` = «**base de datos DOCUMENTAL.**
  Almacena los ficheros adjuntos (BLOBs)» — `azure-apps/sigrid_api.md:130-131`

`CLAUDE.md:143-144`, `services/dedicacion-transfer/config/settings.py:21`,
`azure-apps/dedicacion.md:54` y `azure-apps/partes.md:546-547` usan todos la
palabra «réplica». Es un **error de vocabulario propagado por copia** entre
proyectos. La conclusión operativa («no se escribe ahí») coincide; la razón que
dan es falsa.

**Hecho 2 — los gráficos viven (también) en `ruesma_rep`, con medición real.**

- «Son DOS tablas `gra`, en dos bases distintas»
  — `postventa-incidencias/docs/referencia/03_modelo_posventa_sigrid.md:246`
- `ruesma.gra` = metadatos (282.599 filas, `ima` vacío para posventa);
  `ruesma_rep.gra` = el binario en `ima` (357.901 filas, ninguna vacía)
  — ibíd. `:251-262`
- «Los `ide` de las dos tablas son espacios independientes… **la pareja se
  localiza por `gra.cod`**, no por `ide`» — ibíd. `:263-268`
- `gra.vin = 3` («incrustado externo») en los 13.450 gráficos de posventa; con
  `vin=3`, `ruesma.gra.ima` y `ruesma.gra.tex` están vacíos — ibíd. `:270-274`
- **`rcg` está en `ruesma`** (base de negocio) — ibíd. `:252-253`

Confirmado desde código independiente:
`albaranes-persistencia/domain/models/contrato_models.py:55` y
`infrastructure/database/orm_contrato_models.py:23` sitúan el PDF en
`ruesma_rep.gra`, mientras el `SELECT rcg JOIN gra` de metadatos va contra
`ruesma` (`sigrid_api_contrato_client.py:102-113`, `:1047`).

**Hecho 3 — `ruesma_rep` NO admite escritura hoy, y es deliberado.**

- `ALLOWED_DATABASES = ruesma,ruesma_rep` /
  `ALLOWED_WRITE_DATABASES = ruesma  # escritura SOLO en negocio`
  — `azure-apps/sigrid_api.md:307-309`
- «Nunca uses `ruesma_rep` para escrituras. Está fuera de
  `ALLOWED_WRITE_DATABASES` precisamente para impedirlo»
  — `azure-apps/sigrid_api.md:142-143`

Y `sigrid-api` **no tiene ningún endpoint de escritura documental**: solo
`read_document_use_case.py`, y `function_app.py:254` expone únicamente
`documents/read`. La tabla de endpoints (`sigrid_api.md:566-573`) no lista
ninguna escritura documental.

**Síntesis del choque.** El `CLAUDE.md` acierta en la regla operativa por un
motivo equivocado. El humano acierta en dónde viven los gráficos. Ambos son
compatibles: **metadatos + enlace (`gra` + `rcg`) SÍ se pueden escribir en
`ruesma`; el binario (`ruesma_rep.gra.ima`) NO tiene por dónde hacerse hoy.**

## 3 · Cómo escribe hoy el transfer

Ruta del dato, toda en `services/dedicacion-transfer/`:

1. `interface_adapters/api/app.py` → `application/pipelines/registro_pipeline.py`
   (`preflight` pasos 1-8, `ejecutar` 1-10; orden en `registro_pipeline.py:7-31`).
2. **Paso 1a, destino:** `registro_pipeline.py:81-103` (`_obra_destino`). Con
   `obra_pruebas_forzar` se ignora la obra real y todo va a `OBRA_PRUEBAS_COD`.
3. **Paso 9, crear parte:** `registro_pipeline.py:497-517` llama a
   `stmts_crear_parte` (`sigrid_write_client.py:277-295`):
   `INSERT INTO con (ide, emp, tip=35, est=1, cod='PT<aa>/<nnnnn>', res, fec)`
   + `INSERT INTO hmo (...)`. **`hmo.ide` hereda de `con.ide`**: ese es el `ide`
   al que se colgaría un `rcg`.
4. **Paso 10, líneas:** `registro_pipeline.py:519-568` → `stmt_insert_linea`
   (`sigrid_write_client.py:297-317`) inserta en `hmores` con `MAX(ide)+1` bajo
   `UPDLOCK, HOLDLOCK`; `stmt_borrar_linea` (`:319-322`) para las pisadas. Todo
   por `escribir()` (`:79-101`) en lotes de `SIGRID_MAX_STATEMENTS` (15).
5. **Idempotencia:** `synckey_de(registro_id)` = `"porcentajes:{id}"`
   (`sigrid_write_client.py:31-35`), escrito en `hmores.synckey` y releído en
   `lineas_por_synckey` (`:245-273`). **`gra` y `rcg` no tienen `synckey`.**

**Dónde se fija la base — punto crítico.** Es **una sola, fija en el
constructor**, no un parámetro por llamada: `sigrid_write_client.py:43`
(`database: str`) → `:54` (`self._db = database`), usada en `_read` (`:67`) y en
`escribir` (`:92`). Valor: `SIGRID_API_DATABASE`, por defecto `"ruesma"`
(`config/settings.py:22`, con el comentario erróneo de la «réplica» en `:21`).

→ **El cliente actual no puede apuntar a otra base por llamada.** Precedente de
cómo se hace bien: `albaranes-persistencia/.../sigrid_api_contrato_client.py:193-209`
inyecta `database` **y** `database_rep="ruesma_rep"`, y elige por método (`:594`).

**Reglas P1-P5** (`application/services/reglas_porcentajes.py:7-14`): ninguna
toca documentos. El gráfico es ortogonal: cabecera del parte, una vez por parte.

## 4 · Qué habría que tocar (sin escribir código)

| Fichero | Por qué |
|---|---|
| `infrastructure/sigrid/sigrid_write_client.py` | `stmts_crear_grafico` (INSERT en `gra` + INSERT en `rcg`, `MAX(ide)+1` con `UPDLOCK, HOLDLOCK`, `rcg.pos` múltiplo de 64) y lectura `grafico_de_parte(conide)`. **Si entra el binario, se rompe la premisa de una sola base**: `_db` pasa a ser dos. |
| `config/settings.py` | `SIGRID_API_DATABASE_REP`, el `gratipide`/código `auxgra`, plantilla de `gra.cod` y `gra.res`. |
| `application/pipelines/registro_pipeline.py` | Paso nuevo **entre el 9 y el 10** (parte ya creado con su `ide`, líneas aún no). El paso 9 hace su propio `escribir()` (`:507`); el gráfico entra ahí natural. Exige decidir idempotencia. |
| `docs/ARCHITECTURE.md` | Regla de dominio nueva: qué gráfico, de dónde sale el binario, quién lo genera. Hoy `grep -i grafic` en todo `porcentajes` da **cero resultados**. |
| `CLAUDE.md:143-144` | «la réplica `ruesma_rep`» es fácticamente falso y es justo lo que hace parecer imposible esta petición. Corregirlo es prerrequisito para razonar. |
| `prueba_escritura_porcentajes.py` | `inspeccionar`/`verificar`/`limpiar` (`:183-188`) no saben de `gra`/`rcg`. |
| **`sigrid-api` (OTRO REPO, otro dueño)** | Solo si hace falta el binario: endpoint de escritura documental + `ALLOWED_WRITE_DATABASES`. **No es decisión de este proyecto.** |

**El corte natural.** Si «el gráfico» se resuelve como **metadatos + enlace en
`ruesma`** (`gra` con `ima` vacío y el fichero referenciado por `gra.tex`/`nom`/
URL), cabe entero en el `POST /api/sql/write` ya desplegado, **sin tocar
`sigrid-api` y sin violar el `CLAUDE.md`**. Si exige el BLOB, está bloqueado por
una decisión ajena.

## 5 · Modo pruebas y limpieza — RIESGO DE PRIMER ORDEN

Hoy: `_obra_destino` desvía a la obra `0404` (`registro_pipeline.py:83-92`), la
marca `PRUEBA-PORC` va en `hmores.tex` (`:545`) y en `con.res` (`:503-505`), y
`limpiar` borra por `tex = marca AND synckey LIKE 'porcentajes:%'`
(`prueba_escritura_porcentajes.py:183-188`).

- **El desvío a 0404 SÍ vale para el gráfico**: `rcg.con` sería el `ide` del
  parte, que ya está desviado. Nada extra que hacer.
- **La marca SÍ tiene dónde ir**: `gra.res` (48) o `gra.cod` (128). `rcg` no
  tiene campo de texto, pero se localiza por `rcg.gra`: basta marcar `gra`.
- **NO hay `synckey` ni en `gra` ni en `rcg`.** Toda la idempotencia del transfer
  se apoya en esa columna. Haría falta otra convención (`gra.cod` determinista
  tipo `porcentajes:{parte_ide}`, o `gra.guid`). Sin eso, **un reintento crea
  gráficos duplicados** colgando del mismo parte. Diseñarlo ANTES de escribir.
- **Riesgo grave:** un binario escrito en `ruesma_rep` **quedaría fuera del
  alcance de `limpiar`**, porque el borrado también pasa por
  `ALLOWED_WRITE_DATABASES`. Escribiríamos algo que no podemos borrar. Y como la
  pareja se empareja por `gra.cod` y no por `ide`, un borrado parcial deja
  huérfanos silenciosos. La parte en `ruesma` sí es limpiable.

## 6 · Precedentes en el ecosistema

- **`postventa-incidencias`: el precedente directo, mismo problema, ya
  analizado.** `docs/ARCHITECTURE.md:321-341`: «cerrar una incidencia a mano son
  tres escrituras, y en este orden: `INSERT` en `gra` con el PDF → `INSERT` en
  `rcg` → `UPDATE con.est`». Su feature **F-012** es literalmente «subir el parte
  a Sigrid como gráfico» y está **bloqueada**: `BACKLOG.md:60` y
  `docs/INTEGRACION.md:242` («HALLAZGO DEL 2026-08-26… subir el PDF a Sigrid hoy
  NO TIENE POR DÓNDE HACERSE, y habilitar la escritura en esa base es decisión
  del dueño de `sigrid-api`»). Leer esto antes de diseñar nada.
- **`albaranes-persistencia`: el precedente de cliente bicéfalo.** Metadatos
  `rcg JOIN gra` contra `ruesma` (`:102-113`); BLOB con `documents/read` contra
  `ruesma_rep` (`:578-605`). Es el patrón a copiar si hiciera falta hablar con
  dos bases. **Solo lee, nunca escribe documentos.**
- **`partes` / `partes-transfer` / `partes-persistencia`:** escriben las mismas
  tablas de partes (`azure-apps/partes.md:540-547`) pero **no tocan gráficos**.
  `partes-transfer/config/settings.py:18` repite el comentario erróneo.
- **Nadie en todo el ecosistema escribe un gráfico hoy.** Ni siquiera en `ruesma`.

## 7 · Huecos: lo que NO se ha podido averiguar

1. **Qué quiere decir el humano exactamente.** «El gráfico del parte» puede ser
   (a) adjuntar un PDF del parte firmado al `con`, como en posventa; (b) adjuntar
   el cuadrante de porcentajes; (c) algo que ya existe en la pantalla de Sigrid
   del parte. **Hay que preguntárselo**: todo lo demás depende de la respuesta.
2. **Si la pantalla del parte (`con.tip=35`) admite gráficos.** El modelo
   `rcg`→`con` lo permite estructuralmente, pero el único caso medido es `tip=708`.
3. **Qué `gratipide`/`auxgra` correspondería a un parte.** El de posventa es `35`
   → `PV002` «POSTVENTA:Fotos Reparaciones». No se sabe si existe uno de partes.
4. **De dónde saldría el binario.** El transfer no genera ni recibe ficheros:
   `front → api → transfer` es HTTP síncrono con JSON, sin blobs ni colas, y
   **deliberadamente** (`azure-apps/dedicacion.md:47-54`). Meter un PDF cambia
   esa premisa arquitectónica.
5. **Si `vin=0` (binario dentro de `ruesma.gra.ima`) es viable.** Existen 38
   filas así, pero `sql/write` «no está pensado para BLOBs»
   (`postventa-incidencias/docs/ARCHITECTURE.md:339`). Sin verificar; sería la
   vía que desbloquearía todo sin depender de `sigrid-api`.
6. **Si `gra.tex` («Camino») permite referenciar un fichero externo.**
   `postventa-incidencias/BACKLOG.md:168` lo deja como pregunta abierta.
7. **La configuración desplegada real de `sigrid-api`.** Todo lo de
   `ALLOWED_WRITE_DATABASES` viene de documentación, no de Azure.
