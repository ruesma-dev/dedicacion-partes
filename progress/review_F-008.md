<!-- progress/review_F-008.md -->
# F-008 · Infraestructura y despliegue en Azure — review

Rama `feature/F-008-infra-azure` · revisado el 2026-08-20 contra `dev`
(`git merge-base` = `f594ff1e`).

**Alcance de esta review:** fases 1 a 6 y el cierre — **T1–T23, T32, T33**.
La fase 7 (**T24–T31**) es MANUAL del humano (crear recursos, secretos, Easy
Auth, ejecutar `az`) y **no cuenta como trabajo faltante**; sí se ha
comprobado que está listada con su comando exacto y su resultado esperado. El
commit en el repositorio `azure-apps` es igualmente manual del humano.

---

## Veredicto

# APPROVED

Con **ocho recomendaciones** y **una acción para el líder**, ninguna
bloqueante, recogidas en §7 y §8. Ninguna es un checkbox vacío de C1–C5.

Trabajo de calidad alta y, sobre todo, **verificable**: todas las cifras que
declara el implementer se han recalculado o reejecutado de forma
independiente y **todas coinciden**. Las tres cosas que más podían salir mal
en esta feature —un secreto en el repositorio, un script que actúe por su
cuenta contra el servidor compartido, o el transfer saliendo del modo
pruebas— están cerradas, y verificadas por ejecución, no por lectura.

Las ocho recomendaciones son de documentación y de convención; **la más
valiosa es §7.2**: el guardián de secretos no barre `progress/`, que es
precisamente el directorio donde la fase 7 manda pegar la salida real de los
comandos `az`.

---

## 1 · Nivel de rigor y qué exige

`harness/features.json` declara **`rigor: "critico"`** para F-008. No hay
omisión que suplir. Ese nivel exige, sobre `estandar`:

| Puerta | Exigida | Resultado |
|---|---|---|
| `bash harness/init.sh` en verde | sí | **[x]** exit 0 |
| Tests trazables por requisito (C4) | sí | **[x]** 13 requisitos con test |
| **Fase RED** en los requisitos centrales | sí | **[x]** traza real, dos veces |
| **Cobertura** de las líneas cambiadas ≥ 80 % | sí | **[x]** 93,3 % (28/30) |
| **Campaña de mutación** | sí | **[x]** reejecutada por el reviewer |
| **Cero supervivientes** | sí (`critico`) | **[x]** 0 |
| Verificaciones `MANUAL (humano)` con comando exacto | sí (`critico`) | **[x]** `tasks.md` fase 7 + `infra/README_dedicacion.md` + §7 del informe |

---

## 2 · Verificación independiente (no me he creído el informe)

### 2.1 `bash harness/init.sh`

Ejecutado tal cual. **Exit code 0.** Puerta de cobertura:

```
[OK] PUERTA COBERTURA: 93.3% de 30 líneas cambiadas cubiertas (28/30, umbral 80%, nivel critico)
```

Avisos no bloqueantes y preexistentes: `ruff: 176 avisos (deuda previa)` y
`Hay features en estado blocked` (F-002).

### 2.2 Las cuatro suites, ejecutadas A MANO

`init.sh` dio las tres líneas de servicio **por caché** («árbol sin cambios
desde el último verde»), así que se relanzaron una por una con el intérprete
de cada servicio:

| Suite | Declarado por el implementer | **Medido por el reviewer** |
|---|---|---|
| raíz (`tests/`) | 77 | **77 passed** |
| `services/dedicacion-api` | 112 | **112 passed in 1.34s** |
| `services/dedicacion-front` | 11 | **11 passed, 19 warnings in 0.58s** |
| `services/dedicacion-transfer` | 187 | **187 passed, 1 warning in 0.33s** |
| **Total** | 387 | **387, 0 fallos** |

Coincide. Los avisos son previos a F-008 (`on_event is deprecated` de FastAPI
y un `PytestReturnNotNoneWarning` en `test_pipeline_offline.py`).

### 2.3 Mutación — recálculo puro Y reejecución completa

El informe declara **«Tiempo total: 4.6 s»**, por debajo de los 5 minutos,
así que C4 bis obliga a **reejecutar la campaña entera**. Se ha hecho.

**Paso 1 — alcance recalculado** con `harness.alcance.alcance_de_feature`:

```
F-008: 3 fichero(s), 108 línea(s) de producción
(origen rama, f594ff1e6e81cfea13f82b4b96a11e35d2b27ea4..feature/F-008-infra-azure)
```

Coincide con el informe línea por línea (`settings.py` 8, `database.py` 85,
`main.py` 15) y el commit base coincide con `git merge-base dev HEAD`.

**Paso 2 — mutantes recalculados** con `harness.mutacion.generar_mutantes`
(cálculo puro, sin ejecutar la suite ni escribir en disco). **5 mutantes**,
con el mismo operador y el mismo texto original→mutado:

| Fichero:línea | Operador | Original → mutado |
|---|---|---|
| `config/settings.py:57` | `booleano` | `auto_create_database: bool = False` → `True` |
| `infrastructure/db/database.py:71` | `booleano` | `return True` → `return False` |
| `infrastructure/db/database.py:73` | `booleano` | `return True` → `return False` |
| `infrastructure/db/database.py:75` | `booleano` | `return False` → `return True` |
| `infrastructure/db/database.py:104` | `not` | `if not settings.auto_create_database:` → `if settings.auto_create_database:` |
| `main.py` | — | **0 mutantes** (15 líneas: imports, docstring y una llamada) |

**Paso 3 — campaña reejecutada**, con la salida fuera de `progress/`
(scratchpad de sesión, para no pisar el informe del implementer):

```
5 mutantes evaluados, 5 muertos, 0 supervivientes, 0 timeouts en 4.5 s
```

Coincide con el informe en las cuatro cifras. `git status` **limpio** después.

**Los 5 mutantes caen exactamente donde tiene que haber vigilancia.** No en
periferia: en el valor por defecto de `AUTO_CREATE_DATABASE` y en las cuatro
decisiones del bootstrap de la BBDD (detección de `InvalidCatalogName`,
detección por texto, salida del bucle y el guardián del cortocircuito). Es la
lógica peligrosa de toda la feature, y está toda cazada.

**«Solo 5 mutantes sobre 30 líneas» — verificado, y la justificación es
cierta.** `harness.alcance.es_produccion` solo admite `.py` fuera de
`tests/`, `specs/`, `progress/` y `docs/`. El diff son 5.755 inserciones, de
las cuales **solo tres ficheros son código de producción Python**; los once
`.ps1`, los cuatro documentos y los cinco ficheros de test no son mutables ni
medibles por construcción. Se comprobó que el filtro no descarta en silencio
ningún `.py` de producción: los tres del diff están los tres en alcance.

**Prueba de control de «cero mutantes»: no aplica** — la campaña genera 5, no
0, así que no hay ambigüedad entre «no había nada que mutar» y «el generador
está roto».

### 2.4 Fase RED — traza real, y no es papeleo

Dos fases RED con **salida pegada**, no con la frase «se siguió TDD»:

- **T1** (`progress/impl_F-008.md` §3.1): `ImportError: cannot import name
  'BaseDatosNoExiste' from 'infrastructure.db.database'`, con la traza
  completa de `pytest`, antes de existir el código.
- **T10** (§3.2): el entregable **es** el propio test, así que la fase RED se
  hizo rompiéndolo en un fichero temporal con un GUID y una contraseña
  **inventados**. Y destapó un agujero real: el patrón de credenciales
  excluía todo valor que empezara por comilla, y con ello se le colaba
  `PG_PASSWORD = "<un valor entre comillas>"`, **la forma más habitual de
  escribir una contraseña en un `.ps1`**. Dos ejecuciones pegadas: la primera caza solo el
  GUID, la segunda —con el patrón corregido consumiendo la comilla de
  apertura— caza las dos líneas.

Verificado además que **el fichero temporal nunca entró en git**:
`git log --diff-filter=D --name-only dev..HEAD` no lista ningún fichero
añadido y borrado en la rama.

### 2.5 El bootstrap de la BBDD — comprobado EJECUTANDO, no leyendo

Sonda independiente del reviewer (fuera del árbol del proyecto), con
`psycopg.connect` sustituido por una bomba que registra la llamada:

```
R14 auto_create_database por defecto = False
R13/R15 asegurar_base_datos retorno sin abrir conexion. llamadas = 0
R16 mensaje: La base de datos 'dedicacion' no existe en el servidor '...'.
    Este servicio NO crea bases ni roles (AUTO_CREATE_DATABASE está desactivado,
    y en un servidor compartido debe seguir así): créala una sola vez
    ejecutando infra/crear_base_dedicacion.ps1.
R16 base ajena detectada como nuestra? False
Control: con AUTO_CREATE_DATABASE=true SI abre la conexion -> SE ABRIO LA CONEXION DE ADMINISTRACION
```

La última línea es el **control de no vacuidad**: si el cortocircuito no
existiera, la sonda daría verde igual. Con el conmutador encendido la
conexión sí se abre, luego la sonda mide algo.

Confirmado por ejecución: R13, R14, R15 y R16. El cortocircuito **evita
incluso abrir la conexión**, no solo ejecutar el DDL — que era el punto.

Detalle bien resuelto: `es_base_inexistente` exige que el error nombre
**nuestra** base. En un servidor compartido, que falte la base de otro
proyecto no puede traducirse a «crea la tuya».

### 2.6 Cobertura — las dos líneas sin cubrir

93,3 % (28/30). Las dos descubiertas son de `main.py`: el `import` de
`comprobar_base_datos` y su llamada. Ninguna suite importa `main.py` porque
ejecutarlo levantaría uvicorn y abriría PostgreSQL, que es justo lo que
`docs/CONVENTIONS.md` prohíbe. **No queda como hueco**: hay un test que lo
cubre por otra vía leyendo el fuente
(`test_f008_r16_el_arranque_comprueba_la_base_antes_de_sincronizar`), y que
además fija el **orden** —entre `crear_engine` y `sincronizar_esquema`—, que
es lo que importa: después del DDL la comprobación no serviría de nada.

---

## 3 · SECRETOS — lo más importante de esta review

**Resultado: LIMPIO.** Ni en el árbol final ni en el historial de la rama.

### 3.1 Barrido propio del reviewer, fichero por fichero del diff

No me he fiado del guardián de T10. Barrido independiente sobre **los 41
ficheros del diff**, con patrones propios: GUID, IP privada RFC 1918,
`AccountKey=` / `DefaultEndpointsProtocol=`, URI con usuario y contraseña,
`Server=tcp:`, `User ID=...Password=`, credencial con valor, y base64 largo.

Los **únicos** aciertos son estos, y ninguno es un secreto:

| Dónde | Qué | Por qué no lo es |
|---|---|---|
| `infra/setup_front_easyauth.ps1:153` | `appRoleId = "00000000-0000-0000-0000-000000000000"` | GUID de «acceso por defecto» de Entra: constante documentada de la plataforma, igual para todo el mundo |
| `tests/test_f008_infra_sin_secretos.py:217-239` | GUID, IP, `AccountKey=`, cadenas de conexión | **Controles positivos inventados** del propio guardián. Sin ellos el test no probaría nada |
| `infra/create_api_dedicacion.ps1:76` | `PG_PASSWORD=secretref:pg-password` | Referencia a un secret del Container App, que a su vez es `keyvaultref`. Nombrar dónde vive un secreto es lo que R22 **exige** |
| `progress/impl_F-008.md:139` | `$Global:SUBSCRIPTION = "3f7c1d2e-..."` | GUID **inventado**, pegado como evidencia de la fase RED de T10 |

### 3.2 El historial de la rama, no solo el árbol final

Un secreto commiteado y borrado después seguiría vivo en git. Se barrió
`git log -p dev..HEAD` entero sobre `infra/`, `docs/`, `specs/`, `services/`
y `tests/`. **Cero hallazgos** más allá de los controles positivos del test y
de la prosa que describe el barrido. Y **ningún fichero añadido y borrado**
en la rama.

### 3.3 `azure-apps/` — barrido a mano, porque la suite no lo alcanza

`azure-apps/dedicacion.md` (320 líneas) y `azure-apps/README.md` (67 líneas)
viven en otro repositorio y el guardián no llega. Barridos con la **misma
función `hallazgos()`** del guardián: **los dos, LIMPIOS**.

### 3.4 Se intentó ENGAÑAR al guardián

No basta con que pase: hay que saber si fallaría mañana. Se llamó a
`hallazgos()` con 16 entradas adversarias (sin tocar el árbol):

**Caza correctamente** las cinco familias que R21 declara: contraseña en
`.ps1` con comillas simples, dobles y sin comillas; GUID en mayúsculas;
function key en base64 con relleno; cadena de conexión PostgreSQL completa
con credencial; IP privada.

**Se le escapan** (heurísticas, no incumplimientos de R21):

> **Actualización del implementer (2026-08-20).** Las **dos primeras filas
> están CERRADAS** por la recomendación §7.3; los valores de ejemplo se
> sustituyen aquí por marcadores porque el guardián, que desde §7.2 barre
> también `progress/`, los cazaba —correctamente— en esta misma tabla. Las
> cuatro restantes siguen abiertas y a propósito.

| Entrada que escapa | Comentario |
|---|---|
| ~~`secret_value=<valor>`~~ | **CERRADO**: el patrón admite ya el sufijo `_value` / `-value` / `Value` |
| ~~`"clientSecret": "<valor>"`~~ | **CERRADO**: el patrón admite ya el separador `:`, que es como sale de `az` |
| here-string de PowerShell (`@"…"@`) | el valor va en la línea siguiente y el barrido es línea a línea |
| GUID sin guiones (32 hex) | el patrón exige el formato con guiones |
| base64 largo **sin** relleno `=` | exigir el `=` es deliberado: sin él, cualquier identificador largo saltaría |
| `password = "Mi Clave Con Espacios"` | el patrón corta en el espacio |

Son límites conocidos de un barrido por regex, no fallos: el guardián cubre
lo que su requisito declara y los tests de las dos caras están bien
planteados. Ver §7 para las recomendaciones.

### 3.5 Los valores reales, fuera de git

`infra/.gitignore` ignora `*.local.ps1` y `*.local.json`, y también `*.log` y
`*.tmp.json` («salidas de `az` que a veces se guardan al depurar»). Los
ficheros versionados llevan `REDACTADO-VER-COPIA-LOCAL` en suscripción y
tenant, y `fase1_infra_dedicacion.ps1` y `setup_front_easyauth.ps1`
**abortan** si el marcador sigue puesto.

En `setup_front_easyauth.ps1` el client secret se genera y va **directo al
Key Vault**, se anula la variable acto seguido, y el único fichero temporal
que se escribe (`$env:TEMP`, fuera del repositorio) lleva solo
`principalId` / `resourceId` / `appRoleId` y se borra.

---

## 4 · Que los scripts no ejecuten nada por sí solos

**Cumple, con tres cerrojos encadenados.**

1. **Los dos ficheros de variables no hacen nada.** `00_vars_dedicacion.ps1`
   solo asigna variables y escribe en consola. `00_capps_vars_dedicacion.ps1`
   hace una única llamada a Azure, y es de **lectura** (`az identity show`).
2. **Ningún script muta Azure sin la copia local del humano.** Los valores de
   suscripción y tenant están redactados en el repositorio;
   `fase1_infra_dedicacion.ps1` lanza `throw` si `$SUBSCRIPTION` sigue
   redactada y `setup_front_easyauth.ps1` lo mismo con `$TENANT`. Los
   `create_*` dependen de `$MI_ID`, que solo se resuelve si la fase 1 ya
   existe de verdad.
3. **Lo destructivo lleva confirmación explícita.**
   `crear_base_dedicacion.ps1` **imprime el plan y retorna** sin `-Confirmar`;
   es lo único que escribe en el servidor compartido y por eso el plan va
   primero. Los `create_*` **abortan** si el Container App ya existe, y
   `redeploy_dedicacion.ps1` aborta si **no** existe («eso sería una primera
   publicación, no una republicación»).

### `OBRA_PRUEBAS_FORZAR` — verificado en todo el diff

Se buscó la cadena en **los 41 ficheros del diff**. `false` **no aparece como
valor por defecto en ningún sitio**. La única vía para ponerlo a `false` es
`create_transfer_dedicacion.ps1` con **dos señales**, `-ModoProduccion` **y**
`-Confirmar`, precedidas de un aviso en rojo; con solo la primera el script
sale con `exit 1` y escribe que «salir del modo pruebas es una decisión del
humano para una acción concreta, no un paso del despliegue». Es exactamente
R10 y exactamente la regla dura de `CLAUDE.md`.

El valor desplegado por defecto es `OBRA_PRUEBAS_FORZAR=true`,
`OBRA_PRUEBAS_COD=0404`, `MARCA_PRUEBAS=PRUEBA-PORC`. **La feature termina
con el transfer en modo pruebas** (R9).

---

## 5 · Las cuatro decisiones del humano, una por una

### D1 · Base propia dentro de `psql-albaranes-rs9k2` — las cuatro salvaguardas

| Salvaguarda | Dónde se implementa | Estado |
|---|---|---|
| Creación **una sola vez por una persona** | `crear_base_dedicacion.ps1`: sin `-Confirmar` solo imprime el plan. `AUTO_CREATE_DATABASE=false` en el Container App | **[x]** |
| **Rol de aplicación propio, nunca el admin** | `PG_USER=dedicacion_app`, creado `NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS`. Y un `throw` si la contraseña del rol coincide con la del admin | **[x]** |
| **Nada a nivel de servidor** | Ni `ALTER SYSTEM`, ni `CREATE EXTENSION`, ni `GRANT` de servidor: verificado por `grep` sobre todo `infra/`. Los `GRANT` están acotados a `$PG_DB` y `$PG_SCHEMA` | **[x]** con matiz, ver §7.1 |
| `PG_SSLMODE=require` | `create_api_dedicacion.ps1:77` | **[x]** |

**Ningún script toca el servidor compartido a nivel de servidor** salvo el
matiz de la regla de firewall, que se detalla en §7.1 y que el propio script
declara en voz alta. `fase1_infra_dedicacion.ps1` sobre PostgreSQL no hace
nada; `crear_base_dedicacion.ps1` solo lee el servidor
(`az postgres flexible-server show`) para comprobar que existe, y aborta si
no lo encuentra con un «**NO lo crees**».

La salvaguarda mejor implementada, y no estaba pedida explícitamente: la
contraseña del administrador **no se guarda en el Key Vault**.
`add_secrets_dedicacion.ps1` lo deja escrito y dice por qué, citando el
precedente de `partes`, que desplegó con `PG_USER=<admin del servidor>` y
metió esa credencial en tres contenedores.

### D1b · Esquema `public`

`$Global:PG_SCHEMA = "public"` en `00_vars_dedicacion.ps1:56`, usado en los
`GRANT` y en `ALTER DEFAULT PRIVILEGES`. Con el `GRANT USAGE, CREATE ON
SCHEMA` que PostgreSQL 15+ exige. **[x]**

### D2 · Solo el front externo

| Servicio | `--ingress` | Fichero |
|---|---|---|
| transfer | `internal` | `create_transfer_dedicacion.ps1:117` |
| api | `internal` | `create_api_dedicacion.ps1:108` |
| front | **`external`** | `create_front_dedicacion.ps1:78` |

**[x]** Y está argumentado donde hace falta que se lea: la cabecera de
`create_api_dedicacion.ps1` explica que la api no tiene autenticación propia,
que el ingress interno **es** su control de acceso, y que «no se abre un
atajo temporal para probar; los atajos temporales se quedan». R8 tiene además
cinco tests que fijan que `obtener_usuario` se cree la cabecera sin
validarla — es decir, la razón escrita y ejecutable de por qué la api no
puede exponerse.

### D4 · `min-replicas 1`

`$Global:MIN_REPLICAS = 1` y `$Global:MAX_REPLICAS = 1`, aplicados en los
tres `create_*`. **[x]** El comentario distingue bien lo que es palanca de
coste (el `min`) de lo que es restricción dura (el `max` en transfer y api,
por `MAX(ide)+1` bajo `UPDLOCK/HOLDLOCK` y por la sincronización de maestros).

---

## 6 · Los demás requisitos

### 6.1 Trazabilidad requisito → test

La spec prometía nueve requisitos con test. Hay **trece**:

| Requisito | Tests | Fichero |
|---|---|---|
| R8 (la api no puede exponerse) | 5 | `services/dedicacion-api/tests/test_f008_despliegue.py` |
| R11 (Easy Auth → `X-Usuario`) | 9 | `services/dedicacion-front/tests/test_f008_identidad.py` |
| R12 (`DEFAULT_USER`) | 2 | ídem |
| R13 (no `CREATE DATABASE` al arrancar) | 2 | `services/dedicacion-api/tests/test_f008_bootstrap_bbdd.py` |
| R14 (`AUTO_CREATE_DATABASE` por defecto `false`) | 3 | ídem |
| R15 (ni abrir la conexión) | 2 | ídem |
| R16 (error que nombra base y script) | 9 | ídem |
| R21 (ningún secreto en el repositorio) | 5 | `tests/test_f008_infra_sin_secretos.py` |
| R22 (secretos por su clave en Key Vault) | 1 | ídem |
| R23 (tag fechado, nunca `latest`) | 2 | `tests/test_f008_imagenes.py` |
| R24 (inventario versionado) | 3 | ídem |
| R25 (`.env` fuera de la imagen) | 2 | ídem |
| R26 (`Dockerfile` del transfer) | 4 | ídem |

Los requisitos marcados `revisión` se han comprobado leyendo el fichero, uno
a uno: R2, R3, R4, R5, R6, R7, R9, R10, R17, R18, R19, R20, R27, R28. Los
marcados `MANUAL (humano)` (R1, R30, R33–R36) están listados con su comando
exacto en `tasks.md` fase 7 y en §7 del informe del implementer.

**Los tests no tocan red ni BBDD.** Verificado: `psycopg.connect` sustituido
por un doble que falla si lo llaman; el backend del front sustituido por
`httpx.MockTransport`, que responde en memoria; el resto son barridos de
ficheros del propio árbol.

### 6.2 R3 · Ninguna Storage Account

`grep -rniE 'az +storage|az +queue|blob|storageaccount' infra/` solo devuelve
**comentarios** que explican por qué no se crea. Ningún comando. **[x]**

### 6.3 R6 · Tags acens

`$TAGS` con los cuatro valores obligatorios, aplicado en el resource group,
la managed identity, Log Analytics, el Key Vault, el CAE **y los tres
Container Apps**. **[x]**

### 6.4 R19 y R20 · Secretos e identidad gestionada

Los tres `create_*` llevan `--registry-identity $MI_ID`; **ningún**
`--registry-username`, `--registry-password` ni `admin-enabled` en todo
`infra/`. Los secretos se declaran con `KvRef`, que produce
`keyvaultref:$KV_URI/secrets/<clave>,identityref:$MI_ID`. Ningún valor viaja
en la definición del recurso. **[x]**

### 6.5 R28 · Los timeouts encadenados — el fallo que la feature venía a corregir

El problema era real: el front tenía 120 s y la api 180 s, de modo que el
front se rendía **antes** que la api y el usuario veía un error de un
registro que sí se estaba haciendo. Ahora:

| Salto | Valor desplegado | Fuente |
|---|---|---|
| front → api | **200 s** | `$TIMEOUT_FRONT_API`, `create_front_dedicacion.ps1:65` |
| api → transfer | **180 s** | `$TIMEOUT_API_TRANSFER`, `create_api_dedicacion.ps1:95` |
| transfer → `sigrid-api` | **60 s** | `$TIMEOUT_TRANSFER_SIGRID` |
| corte del balanceador | 230 s | no configurable |

**200 ≥ 180 ≥ 60, y todos por debajo de 230.** Orden coherente, decreciente
hacia dentro. **[x]** Los tres valores salen de una única definición en
`00_vars_dedicacion.ps1`, no de literales repartidos, y los `.env.example`
del front y de la api explican la diferencia entre el valor local y el
desplegado. Ver §7.5 para una observación sobre el presupuesto acumulado.

### 6.6 R25 y R26 · Empaquetado

`services/dedicacion-transfer/Dockerfile` es **coherente con los otros dos**:
mismo `python:3.12-slim`, mismo `WORKDIR /app`, `requirements.txt` antes de
copiar el código (para que la capa de dependencias se cachee), `EXPOSE 8006`
—que casa con `$PUERTOS['transfer']`— y `CMD ["python", "main.py"]`. Añade un
comentario que los otros no tienen y que hace falta: `LOG_DIR=/tmp/logs`
porque `/app` no tiene por qué ser escribible.

El `.dockerignore` del transfer excluye **`.env` y `.venv`**, y además
`logs/`, `tests/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`,
`coverage.json` y `.coverage`. Es el más completo de los tres. Ver §7.4.

`infra/imagenes.json` parsea, cubre los tres servicios y trae los tags a
`null` con la nota de que el build real es MANUAL. Correcto: el inventario
existe versionado desde ya y lo rellena `build_images_dedicacion.ps1`.

### 6.7 Convenciones

- **Primera línea con la ruta**: los 30 ficheros nuevos la llevan. Los `.ps1`
  con `# infra/<nombre>.ps1`, los `.md` con `<!-- ruta -->`, los `.py` con
  la ruta relativa a su servicio, que es la convención ya vigente en este
  monorepo. **[x]**
- **`ruff`**: 2 avisos `I001` en `database.py` y `main.py`. **Los dos son
  deuda previa**: se comprobó ejecutando `ruff` sobre la versión de esos
  ficheros en `dev` y ya estaban. F-008 **no introduce deuda nueva**. **[x]**
- **Sin `print()` de debug, sin TODO/FIXME/HACK, sin dependencias nuevas**:
  verificado con `grep` sobre todo el diff y sobre los `requirements.txt`
  (que no cambian). **[x]**
- **Los once `.ps1` parsean.** Se verificó la afirmación del informe con
  `[System.Management.Automation.Language.Parser]::ParseFile`, sin
  ejecutarlos: **11 de 11 OK, 0 errores de sintaxis**. **[x]**

### 6.8 Documentación (R29–R32) — verificada contra el código, no leída por encima

**`docs/INTEGRACION.md` (R29, R31) · cumple.** Trae los cinco mínimos que R31
exige, y los números **están verificados contra el código**, no estimados:
declara un techo real de 10 conexiones, que es exactamente lo que fija
`services/dedicacion-api/infrastructure/db/database.py:158-164`
(`pool_size=5, max_overflow=5`); y los timeouts de su tabla casan con
`infra/00_vars_dedicacion.ps1:107-109`.

| Mínimo de R31 | Dónde |
|---|---|
| Qué consumimos (PostgreSQL, `sigrid-api`, ACR, Entra ID) | §1, con las cuatro filas, más «lo que NO consumimos» |
| Qué exponemos | §5: «hacia otros proyectos: **nada**. Consumidor puro» |
| Qué le hacemos al servidor compartido, **en números** | 32 GB al 93,4 %, 156 trabajadores, ~10.000 filas/año, techo de 10 conexiones |
| Qué se rompe si alguien toca algo | separado en «algo nuestro» / «algo de otros» |
| Dónde está cada cosa | tabla de documentos y tabla de recursos de Azure |

Cubre además los tres puntos que T21 pedía explícitamente: por qué la api va
interna y que nadie lo «arregle» («los atajos temporales se quedan»), que el
transfer está en modo pruebas con su comando de comprobación, y que
`/health` del front **no** responde a un `curl` anónimo (R35). **Ni un valor
de conexión**: los huecos quedan sin resolver a propósito
(`kv-dedicacion-<sufijo>`, `<fqdn-front>`) y el Object ID del grupo se declara
fuera del repositorio.

**`docs/ARCHITECTURE.md` (R32) · cumple.** Deja de decir «No hay nada
desplegado ni carpeta `infra/`»; añade dónde vive PostgreSQL (base propia en
`psql-albaranes-rs9k2`, esquema `public`, rol propio, `PG_SSLMODE=require`,
con la decisión fechada), la tabla de timeouts con columnas Local/Desplegado,
y el recordatorio de `OBRA_PRUEBAS_FORZAR=true` **enlazando** `#regla-pruebas`.
Y lo que importaba: **la sección de semántica de dominio NO se ha tocado**;
los tres hunks del diff caen fuera de ese rango.

**`azure-apps/dedicacion.md` (R30) · cumple.** Existe (320 líneas), con la
cabecera obligatoria en el formato exacto de `azure-apps/README.md`
(`Origen: repositorio porcentajes, commit 1e719db` / `Fecha del documento:
2026-08-20`). El diff normalizado contra `docs/INTEGRACION.md` es **idéntico
salvo la cabecera**: cero divergencia, que es justo la avería que la regla de
no duplicar persigue. Su fila está añadida a `azure-apps/README.md`. Barrido
de secretos: **limpio** (§3.3).

Los dos ficheros están **sin commitear** en `azure-apps` (`M README.md`,
`?? dedicacion.md`). Es lo previsto: `tasks.md` T23 marca ese commit como
MANUAL del humano, por ser otro repositorio. Conviene decirlo claro de todos
modos: hoy esa entrega vive solo en el árbol de trabajo del otro repositorio.

**`infra/README_dedicacion.md` (T14) · cumple con un hueco.** Trae el orden de
ejecución (tabla numerada 1→8 con columna «¿Se repite?» y bloque ejecutable
copiable), qué hace cada script, por qué el orden 5→6→7 no es cosmético, y el
aviso del hueco sin login entre el paso 7 y el 8. Y encabeza con «Los scripts
**los ejecuta una persona**. **Ningún agente ejecuta nada de aquí**». El hueco
está en §7.7.

**Idioma · cumple.** Barrido de los 44 ficheros del diff —comentarios de los
`.ps1`, docstrings de los tests nuevos, los tres `.env.example`, `Dockerfile`,
`.dockerignore`, `infra/.gitignore`, el campo `$doc` de `imagenes.json` y los
títulos de los `.md`—: **cero prosa en inglés**. Lo único en inglés es
inevitable y correcto: SQL, nombres de rol de Azure («Key Vault Secrets
Officer»), verbos de cmdlet de PowerShell, identificadores de Python y las
salidas de `pytest` citadas literalmente. La frase en inglés con la que el
agente cerró su informe **no se ha colado en ningún fichero entregado**.

(Los `.ps1` van en español **sin tildes**, por la codificación de PowerShell
5.1. No incumple la regla de idioma; los `.md` sí las llevan.)

### 6.9 Arquitectura hexagonal

El diff **no toca `domain/`** en ningún servicio. Los tres ficheros de
producción son `config/settings.py` (configuración), `infrastructure/db/
database.py` (adaptador, donde le toca) y `main.py` (composición). Ninguna
regla de dominio movida. Las tres trampas que C3 obliga a vigilar siempre
—escala del porcentaje, postventa en su obra, y que solo escriba el transfer—
**no las toca esta feature**, y la tercera queda además reforzada: el transfer
sale interno y en modo pruebas.

---

## 7 · Recomendaciones (no bloquean)

### 7.1 La regla de firewall es, técnicamente, una acción a nivel de servidor

R18 dice literalmente que `crear_base_dedicacion.ps1` «**no** debe contener
`ALTER SYSTEM`, `CREATE EXTENSION` ni ningún cambio a nivel de servidor». El
script crea, si no existe, la regla `AllowAzureServices`
(`0.0.0.0`–`0.0.0.0`), y una firewall rule de Flexible Server **es** un
recurso a nivel de servidor.

No lo trato como bloqueante, y por cuatro razones:

1. **Está declarado en voz alta**, no escondido: «AVISO: es la unica accion a
   nivel de servidor de este script» (`crear_base_dedicacion.ps1:92`).
2. **Se comprueba antes**: si ya existe la regla —y con cuatro inquilinos
   conectando desde Azure es lo más probable— **no se toca**.
3. Es aditiva y no cambia configuración que afecte a los demás.
4. Sin ella el Container App no puede conectar en absoluto.

**Recomendación:** ajustar la redacción de R18 para que diga lo que de verdad
se quiere prohibir —parámetros, extensiones, autenticación, almacenamiento y
`GRANT` de servidor— y exceptúe explícitamente la regla de firewall
idempotente. Hoy el script hace lo correcto y el requisito dice otra cosa;
esa distancia es la que dentro de seis meses se resuelve mal.

### 7.2 El guardián no barre `progress/`, y la fase 7 manda pegar salida real de `az` ahí

Es el hallazgo más útil de esta review. `DIRECTORIOS = ("infra", "specs",
"docs")`. Pero `tasks.md` fase 7 dice literalmente «el humano pega el
resultado real en `progress/impl_F-008.md`», y los comandos que va a pegar
son `az resource list`, `az containerapp show` y `az ad group show`, cuya
salida contiene identificadores de suscripción y objectId de grupo. El propio
`progress/impl_F-008.md` ya contiene hoy un GUID (inventado, y por buen
motivo), lo que demuestra que ese directorio recibe esa clase de texto.

**Recomendación:** añadir `"progress"` a `DIRECTORIOS`. Antes de hacerlo hay
que comprobar si dispara con los informes ya existentes, y si lo hace,
resolverlo con marcadores en vez de relajando el patrón. Vale también para
`arnes-base`, por la regla de propagación.

### 7.3 Cuatro rendijas del guardián que conviene cerrar

De las de §3.4, dos son baratas y valen la pena:

1. Aceptar `_value`, `-value` y variantes entre el nombre y el `=`
   (`secret_value=...` escapa hoy).
2. Aceptar el separador `":"` además de `=`, para pillar
   `"clientSecret": "..."` en JSON.

Las otras dos —here-strings y valores con espacios— exigen barrer por bloques
en vez de por líneas y probablemente no compensen. Lo importante es que
consten por escrito, que es para lo que sirve esta sección.

### 7.4 Los `.dockerignore` de api y front son peores que el nuevo del transfer

`services/dedicacion-api/.dockerignore` y el del front **no excluyen
`.venv/`** (ni `tests/`, ni `.pytest_cache/`). El del transfer, nuevo en esta
feature, sí. **No es un incumplimiento de R25**, que solo exige excluir
`.env`, y los tres lo hacen; y el riesgo real está mitigado porque
`build_images_dedicacion.ps1` excluye `.venv`, `.git`, `tests` y las cachés
del contexto con `robocopy /XD`. Pero son ficheros **preexistentes a F-008**
que ahora se quedan por detrás del que la feature acaba de escribir.

**Recomendación:** alinear los tres, en una feature de higiene aparte.

### 7.5 El presupuesto de 180 s de la api hacia el transfer es por salto, no acumulado

R28 pide que los timeouts encadenados sean crecientes hacia fuera, y lo son.
Pero el transfer puede encadenar **varias** llamadas a `sigrid-api` de hasta
60 s dentro de un mismo `registro/ejecutar`, de modo que un `ejecutar` lento
podría superar los 180 s que la api le concede sin que ninguna llamada
individual se pase.

La spec deja explícitamente fuera de alcance «un test que cruce los timeouts
de dos servicios», y con razón (ataría la suite de un servicio al monorepo,
que es la avería abierta en F-012). **No es un cambio requerido**: es algo que
conviene mirar con el primer registro real de un mes completo (T29), y que
debería quedar anotado cuando se abra esa observación.

---

### 7.6 `INTEGRACION.md` §8 afirma en presente un despliegue que no existe

La §8 abre con «`dedicacion-transfer` **está desplegado** con
`OBRA_PRUEBAS_FORZAR=true`», y las tablas de §5 y §6 hablan en presente de
recursos que todavía no se han creado. Quien lea solo esa sección concluirá
que hay algo corriendo en Azure.

**No lo trato como bloqueante** porque la cabecera del propio documento lo
desmiente en negrita y en el primer bloque: «**Estado al escribirlo:** los
scripts de despliegue existen y están revisados; **en Azure no hay nada creado
todavía**», con la instrucción de volver a actualizarla tras desplegar —que es
exactamente T31. El lector queda advertido antes de llegar a la §8.

**Recomendación:** cambiar a «queda desplegado con» / «los scripts lo dan de
alta con» en §8, §5 y §6, y propagarlo a `azure-apps/dedicacion.md`. Es
barato, y evita que la única frase que alguien cite fuera de contexto sea la
que afirma un despliegue inexistente.

### 7.7 El manual de `infra/` no recoge los pasos manuales que no son scripts

T14 pide «**qué pasos son MANUAL (humano)** con su comando».
`infra/README_dedicacion.md` cubre bien los pasos que **son** un script, pero
**no recoge T29, T30 ni T31**: la prueba funcional de extremo a extremo, la
petición de la tarjeta al proyecto `front-portal` con el Object ID del grupo,
y el refresco de `docs/INTEGRACION.md` y `azure-apps/dedicacion.md` con el
FQDN real.

Los tres están escritos con su comando exacto en `tasks.md` fase 7 y en §7 del
informe del implementer, así que **la exigencia de C4 se cumple**; el problema
es de ergonomía: quien despliegue tendrá abierto el manual de operación, no la
spec. El propio `docs/INTEGRACION.md` **promete** ese refresco en su cabecera,
pero no lo pide donde se va a leer.

**Recomendación:** añadir al README un paso 9 con T29–T31 y marcar fila a fila
cuál es MANUAL, en vez de apoyarse solo en el aviso global de cabecera.

### 7.8 `INTEGRACION.md` reenuncia la regla de modo pruebas en vez de enlazarla

`docs/ARCHITECTURE.md` §«Semántica de dominio imprescindible» establece, en
negrita, que esa sección es **la única fuente normativa** de las reglas P1-P5
y que el resto de documentos «**remiten** a las anclas … no vuelven a enunciar
la regla con palabras propias». `docs/INTEGRACION.md` §8 la reenuncia con
palabras propias —obra `0404`, marca `PRUEBA-PORC`, campo `tex`— y **no**
enlaza `#regla-pruebas`. `infra/README_dedicacion.md` hace lo mismo. La
sección nueva de `ARCHITECTURE.md` sí lo enlaza bien.

El guardián que vigila esto,
`services/dedicacion-transfer/tests/test_f002_fuente_unica.py`, mira una
**lista fija de seis ficheros** heredada de F-002, así que los dos nuevos no
le disparan.

No es bloqueante —el texto reenunciado es hoy correcto y consistente con el
ancla—, pero es exactamente la clase de duplicado que la convención existe
para impedir, y ahora vive además en `azure-apps/dedicacion.md`, en otro
repositorio.

**Recomendación:** sustituir la reenunciación por un enlace al ancla en los
dos ficheros, y **añadirlos a la lista que vigila
`test_f002_fuente_unica.py`** para que el guardián cubra los documentos
nuevos. Sin lo segundo, el mismo desvío volverá en la próxima feature.

---

## 8 · Acción para el líder (no para el implementer)

**C4 pide que las verificaciones `MANUAL (humano)` estén listadas en
`progress/current.md` con su comando exacto.** Hoy `current.md` describe la
sesión de F-008 y las decisiones D1–D5, pero **no** trae el listado de la
fase 7.

No es un fallo del implementer: `tasks.md` le prohíbe expresamente tocar
`progress/current.md` y `harness/features.json` («los lleva el líder»), y esta
review tiene la misma prohibición. Y la sustancia del checkpoint **sí está
cubierta**, en tres sitios y con el comando exacto:

- `specs/F-008-infra-azure/tasks.md` fase 7 (T24–T31), con bloques
  `powershell` completos y el resultado esperado de cada uno;
- `progress/impl_F-008.md` §7, con las dos precondiciones;
- `infra/README_dedicacion.md`, con el orden de ejecución.

Por eso marco el checkbox `[x]`. **Acción para el líder:** al cerrar la
sesión, llevar a `progress/current.md` el listado de la fase 7 con sus
comandos y las dos precondiciones, para que quien abra el repositorio dentro
de un mes lo encuentre donde el arnés dice que va a estar.

---

## 9 · CHECKPOINTS.md

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina con exit code 0. Verificado.
- [x] Existen los siete ficheros obligatorios. Verificado por `init.sh`.

### C2 — El estado es coherente

- [x] Una sola feature `in_progress` (F-008). `init.sh` lo valida.
- [x] Rama actual `feature/F-008-infra-azure`, nunca `main`.
- [x] `progress/current.md` describe la sesión activa de F-008.
- [x] F-001, F-003 y F-009 (`done`) tienen su resumen en
      `progress/history.md`. F-008 no está `done` todavía, así que no le toca
      entrada.

### C3 — El código respeta arquitectura y convenciones

- [x] Hexagonal respetada: el diff no toca `domain/`; el adaptador nuevo está
      en `infrastructure/db/`.
- [x] Primera línea con la ruta en los 30 ficheros nuevos.
- [x] Sin `print()` de debug, sin TODOs, **sin secretos hardcodeados** (§3),
      sin dependencias nuevas.
- [x] Reglas de dominio respetadas. Las tres trampas permanentes no las toca
      esta feature; la tercera (solo escribe el transfer, en `ruesma`, con
      `synckey` y modo pruebas) queda **reforzada**: transfer interno,
      `OBRA_PRUEBAS_FORZAR=true` y doble confirmación para salir. La regla en
      sí se enuncia correctamente en todas partes; lo que se desvía es la
      convención de **remitir al ancla en vez de reenunciarla** (§7.8), que
      es un problema de forma, no de contenido.

### C3 bis — Documentos que entran de fuera

**N/A justificado:** la feature **no añade ni modifica ningún fichero en
`docs/referencia/`** (verificado sobre `git diff --name-only dev..HEAD`).
No hay original en PDF ni ofimática en el diff ni en el historial de la rama.

Aun así, el **barrido de datos sensibles se ha ejecutado igualmente** sobre
todo el diff y sobre el historial de la rama, y consta en §3 con los patrones
usados: GUID, IP privada RFC 1918, `AccountKey=`,
`DefaultEndpointsProtocol=`, URI con credencial incrustada, `Server=tcp:`,
`User ID=...Password=`, credencial con valor y base64 largo.

### C4 — La verificación es real

- [x] 13 requisitos EARS con ≥ 1 test trazable `test_f008_rN_*`, y todos
      pasan (§6.1). La spec prometía nueve.
- [x] Los unit tests no tocan red ni BBDD: `psycopg.connect` sustituido por
      un doble que falla si lo llaman, `httpx.MockTransport` en el front.
- [x] Verificaciones `MANUAL (humano)` listadas con su comando exacto, en
      `tasks.md` fase 7, `infra/README_dedicacion.md` e
      `progress/impl_F-008.md` §7. **Matiz y acción para el líder en §8.**

### C4 bis — El rigor declarado se cumple

- [x] `rigor: "critico"` declarado en `harness/features.json`.
- [x] **Fase RED** con salida real, dos veces (§2.4). La de T10 destapó un
      agujero real en el propio guardián.
- [x] **Cobertura**: `[OK] PUERTA COBERTURA: 93.3% ... (28/30, umbral 80%,
      nivel critico)`.
- [x] **Mutación**: `progress/mutacion_F-008.md` existe, generado por la
      herramienta. **Alcance y nº de mutantes recalculados de forma
      independiente** con `harness.alcance` y
      `harness.mutacion.generar_mutantes` (cálculo puro): coinciden, y los
      cinco mutantes coinciden además en operador y en el texto
      original→mutado (§2.3).
- [x] **Los muertos están comprobados, no solo contados.** El informe declara
      4,6 s (< 5 min), así que **la campaña se reejecutó entera** con
      `--salida` a un directorio del scratchpad, fuera de `progress/`:
      **5 mutantes, 5 muertos, 0 supervivientes, 0 timeouts**, idénticos al
      informe. `git status` limpio después.
- [x] Cero supervivientes, luego no hay ninguna sección de análisis en
      `PENDIENTE`. Nivel `critico` satisfecho sin necesidad de justificación
      escrita.
- [x] Sección **«Evidencias»** (§4 del informe del implementer) con los
      cuatro números: 387 tests / 0 fallos, 93,3 % de cobertura de lo
      cambiado, 5 mutantes y 0 supervivientes, y 4,81 s de suite. Los cuatro
      verificados por el reviewer.
- [x] Ningún punto de este bloque marcado N/A.

### C4 ter — Rutas sensibles

**N/A por configuración, y no hay nada que justificar**: este repositorio no
declara `harness/rutas_sensibles.json`, que es el caso mayoritario previsto
por el propio checkpoint.

### C5 — La sesión se cerró bien

- [x] `tasks.md` con **T1–T23, T32 y T33 todas `[x]`**. Las únicas sin marcar
      son **T24–T31**, todas `MANUAL (humano)`, que es exactamente la fase 7
      fuera del alcance de esta review.
- [x] Un commit `F-008 Tn: ...` por tarea, con **cuatro desviaciones
      declaradas** en §6 del informe (T3+T4 en un commit, la verificación de
      T2/T3 imposible con `-k`, `imagenes.json` adelantado a T8 y el README de
      `infra/` escrito al final de la fase 5). T23 no tiene commit aquí porque
      sus dos ficheros viven en `azure-apps`, otro repositorio, y ese commit
      es del humano. Todas razonables y ninguna silenciosa.
- [x] Sin ficheros temporales ni artefactos sin trackear: `git status`
      limpio, antes y después de la campaña de mutación del reviewer.
- [x] `features.json` refleja el estado real: `in_progress`, que es lo
      correcto — la feature no puede pasar a `done` hasta que el humano
      ejecute la fase 7.

---

## 10 · Automejora del arnés (propuesta, no aplicada)

Dos, ambas genéricas y por tanto candidatas a `arnes-base`:

1. **`CHECKPOINTS.md` C4, tercer punto.** Pide las verificaciones `MANUAL
   (humano)` en `progress/current.md`, pero las plantillas de `tasks.md`
   prohíben al implementer tocar ese fichero. El checkpoint queda sin dueño
   claro y el reviewer tiene que resolverlo a mano cada vez (§8). Propuesta:
   redactarlo como «listadas con su comando exacto en `progress/current.md`
   **o en el `tasks.md` de la spec**, y el líder las consolida en
   `current.md` al cerrar la sesión».

2. **El guardián de secretos debería barrer `progress/`.** Es donde el arnés
   manda pegar la salida real de los comandos, y es el único de los cuatro
   directorios versionados que hoy nadie vigila (§7.2). Si `arnes-base`
   incorpora un guardián de secretos genérico, que nazca ya con
   `progress/` dentro.

3. **Un guardián con lista fija de ficheros envejece mal.**
   `test_f002_fuente_unica.py` vigila que las reglas P1-P5 no se reenuncien,
   pero contra una lista de seis ficheros escrita en F-002. F-008 añadió dos
   documentos que la incumplen y el test no se enteró (§7.8). El patrón
   correcto es el del guardián de secretos de esta misma feature: **barrer un
   directorio**, no enumerar ficheros. Vale para cualquier proyecto con
   documentación normativa.

Ninguna de las tres se ha aplicado: las decide el humano. Y ninguna se ha
tocado en el código, la spec ni el `features.json` del implementer: el trabajo
del reviewer es decir qué falla, no arreglarlo.
