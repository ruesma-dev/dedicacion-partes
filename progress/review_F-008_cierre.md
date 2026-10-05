<!-- progress/review_F-008_cierre.md -->
# F-008 · Infraestructura y despliegue en Azure — REVIEW DE CIERRE

Fecha: 2026-08-21 · Rama revisada: `dev` (todo integrado) · Reviewer: subagente
`reviewer`.

**Alcance de esta review.** NO se revisan de nuevo las fases 1–6: tienen
review aprobada en `progress/review_F-008.md`. Aquí se comprueba que la
feature está **terminada de verdad** ahora que el despliegue se ha ejecutado,
y que el rastro documental **dice la verdad**.

> **Nota de concurrencia.** Se ejecutó con otro reviewer trabajando en el
> mismo árbol (cierre de F-015). No se ha tocado ningún fichero suyo. Los
> únicos ficheros creados fueron dos controles temporales del guardián de
> secretos, borrados en el acto; `git status` quedó limpio (verificado).

---

> **Este informe tiene TRES pasadas.** La primera (§1-§13) es del 2026-08-21 y
> pidió cinco cambios; la segunda (§14) verificó los remates y bloqueó por un
> punto más. **El veredicto definitivo está en §15, al final: APPROVED.** Lo
> anterior se conserva sin retocar: es el estado en que se encontró la feature,
> y borrarlo sería reescribir la historia.

---

## Veredicto de la PRIMERA pasada (histórico — ver §14 para el vigente)

> ## CHANGES_REQUESTED

**No por lo que está desplegado —que está bien y lo he verificado yo contra
Azure—, sino por lo que el rastro afirma sin respaldo.** El sistema real pasa
todas las comprobaciones que he podido hacer: exposición, réplicas, modo
pruebas, secretos por Key Vault, digests, Easy Auth, FQDN y Key Vault
coinciden exactamente con lo documentado. Lo que no se sostiene es el papel:

1. **T29 está marcada `[x] EJECUTADA` y no existe evidencia de ella en ningún
   sitio del repositorio.** Es la prueba funcional de extremo a extremo: la
   única que demuestra que el sistema desplegado *hace algo*, y la que no
   puedo verificar yo desde fuera.
2. **La fase 7 entera incumple la instrucción que su propio `tasks.md` le
   impone**: «El humano pega el resultado real en `progress/impl_F-008.md`».
   La §7 de ese informe sigue escrita **en futuro**, como lista de comandos
   pendientes. En nivel `critico`, `CHECKPOINTS.md` exige las verificaciones
   `MANUAL (humano)` «con su comando exacto **y su resultado real**».
3. **T31 está marcada `[x] EJECUTADA` y su mitad no está hecha**: el commit
   en `azure-apps` no existe (`dedicacion.md` sigue **sin versionar** allí), y
   su verificación declarada («las dos cabeceras llevan fecha y **commit de
   origen**») no se cumple en ninguna de las dos cabeceras. R30 pide una
   *copia en `azure-apps/`*: un fichero sin trackear en el árbol de trabajo de
   otro repositorio no es eso — se lo lleva un `git clean`.

Ninguno de los tres es un defecto del sistema desplegado. Los tres son
exactamente el fallo que una review de cierre existe para impedir: **cerrar
sobre un rastro que afirma más de lo que puede demostrar.**

---

## Nivel de rigor

`harness/features.json` declara **`rigor: "critico"`** para F-008. Es el nivel
correcto: infraestructura compartida (quinto inquilino de
`psql-albaranes-rs9k2`), producción y seguridad.

Puertas que exige (`harness/rigor.json`, tabla de `CHECKPOINTS.md`): C1–C3,
C3 bis, C4, **fase RED**, **cobertura de las líneas cambiadas ≥ 80 %**,
**campaña de mutación con cero supervivientes**, C5, y además —propio de
`critico`— **verificaciones `MANUAL (humano)` listadas con su comando exacto y
su resultado real**. Esta última es la que falla.

---

## 1 · Lo que he verificado yo contra Azure (lecturas, ninguna escritura)

No me he creído el informe: he consultado el estado real con `az` en modo
lectura. **Todo lo que se puede comprobar desde fuera, cuadra.**

### 1.1 T27 — la verificación que de verdad importa · **CUADRA ENTERA**

```
App                     Externo    Min    Max    Img
ca-dedicacion-transfer  False      1      1      acralbaranesdev.azurecr.io/dedicacion-transfer:r20260820-1625
ca-dedicacion-api       False      1      1      acralbaranesdev.azurecr.io/dedicacion-api:r20260820-1625
ca-dedicacion-front     True       1      1      acralbaranesdev.azurecr.io/dedicacion-front:r20260820-1625
```

- **R7 · exposición**: `externo = True` **solo** en el front. Api y transfer
  internos. ✔
- **R4, R5 · réplicas**: `min = max = 1` en los tres. ✔
- **R9 · modo pruebas**: `OBRA_PRUEBAS_FORZAR` del transfer devuelve `true`. ✔
- **R19 · secretos**: los dos secretos de la api (`pg-password`,
  `sigrid-key`) tienen `keyVaultUrl` no nulo. Ninguno como valor. ✔

### 1.2 T24 — provisión base · **CUADRA**

Recursos en `rg-dedicacion-dev`: `id-dedicacion-dev` (MI),
`log-dedicacion-dev`, `kv-dedicacion-dd7k2`, `cae-dedicacion-dev`, y los tres
`ca-dedicacion-*`. **Ninguna Storage Account** (R3). ✔

### 1.3 T25 e `infra/imagenes.json` — los digests · **CUADRAN AL BYTE**

Comparé los tres digests del inventario con los del ACR (`az acr repository
show-tags --detail`). Coinciden **exactamente**, y las tres imágenes
desplegadas corren ese mismo tag:

| Servicio | Digest en `imagenes.json` | En el ACR | Creado |
|---|---|---|---|
| `dedicacion-transfer` | `sha256:cf872c89…413e3f` | **idéntico** | 2026-08-20T14:25:44Z |
| `dedicacion-api` | `sha256:d5b4a18a…edb84e` | **idéntico** | 2026-08-20T14:26:32Z |
| `dedicacion-front` | `sha256:abd1b6f4…cec8f3` | **idéntico** | 2026-08-20T14:27:15Z |

Esto importa más de lo normal: `imagenes.json` **se rellenó a mano** porque el
script falló al escribirlo (bug 5). Un inventario escrito a mano es
exactamente el que hay que contrastar contra la fuente. Está bien.

### 1.4 T26 y T28 — Easy Auth y salud · **CUADRAN, con un matiz**

- `az containerapp auth show` del front: `platform.enabled = true`,
  proveedor `azureActiveDirectory`, `unauthenticatedClientAction =
  RedirectToLoginPage`. ✔ (R36, login obligatorio)
- `GET https://<fqdn-front>/health` **anónimo → HTTP 401**. Es justo lo que
  `docs/INTEGRACION.md` documenta como esperado (R35): el `/health` del front
  **no** es alcanzable sin sesión. ✔
- Las tres revisiones activas: `Healthy` / `RunningAtMaxScale`, 1 réplica. ✔

**Matiz:** `Healthy` es el veredicto de la sonda de Azure, no el cuerpo de la
respuesta. **R33** («responden a `/health`») y sobre todo **R34** (la salud
del transfer debe declarar `modo_pruebas: true` y `database: "ruesma"`) piden
el contenido, y el contenido no consta en ninguna parte. R34 solo se puede
comprobar desde dentro del entorno, tal y como avisa la propia T28 — pero
entonces hay que pegar el resultado, y no se pegó.

### 1.5 FQDN y Key Vault frente a la documentación · **CUADRAN**

| Dato | Azure real | `docs/INTEGRACION.md` |
|---|---|---|
| Front | `ca-dedicacion-front.ashypebble-3c89c6d6.spaincentral.azurecontainerapps.io` | idéntico |
| Api | `ca-dedicacion-api.internal.ashypebble-3c89c6d6.…` | idéntico |
| Transfer | `ca-dedicacion-transfer.internal.ashypebble-3c89c6d6.…` | idéntico |
| Key Vault | `kv-dedicacion-dd7k2` | `kv-dedicacion-dd7k2` (§ tabla, línea 281) |
| Acceso | asignación requerida + grupo | «solo miembros de `dedicacion-portal-users`» |

---

## 2 · ¿Dice la verdad `tasks.md`? (encargo 1)

| Tarea | Marca | ¿Es cierto? | Evidencia |
|---|---|---|---|
| T24 | `[x] EJECUTADA` | **Sí** | Verificado por mí: RG con MI, Log Analytics, KV y CAE; sin Storage Account |
| T25 | `[x] EJECUTADA` | **Sí** | Verificado por mí: tres tags `r20260820-1625` en el ACR, digests idénticos a `imagenes.json` |
| T26 | `[x] EJECUTADA` | **Sí** | Verificado por mí: Easy Auth activo, login obligatorio, 401 anónimo |
| T27 | `[x] EJECUTADA` | **Sí** | Verificado por mí, las cuatro comprobaciones (§1.1) |
| T28 | `[x] EJECUTADA` | **Parcial** | Las tres revisiones `Healthy`; **el resultado nunca se pegó** y **R34 no consta** |
| T29 | `[x] EJECUTADA` | **NO DEMOSTRADO** | **Cero evidencia en todo el repositorio** (ver §2.1) |
| T30 | `[~] MOVIDA A F-015` | **Sí** | Correcto: commit `96cf169`, y F-015 la recoge íntegra en su descripción |
| T31 | `[x] EJECUTADA` | **Parcial** | Los docs sí se refrescaron; **el commit en `azure-apps` NO existe** y las cabeceras no llevan commit de origen (ver §2.2) |

### 2.1 T29: marcada hecha, sin una sola línea de respaldo

Busqué la evidencia en los cuatro sitios donde podría estar:

1. **`progress/impl_F-008.md` §7** — que es donde `tasks.md` manda pegarla
   («El humano pega el resultado real en `progress/impl_F-008.md`»). Sigue
   diciendo, literalmente, `## 7 · Lo que queda: fase 7, MANUAL (humano)`, y
   sus subsecciones T24–T31 son **comandos a ejecutar**, en futuro. No se
   actualizó ni una.
2. **`progress/current.md`** — el único sitio donde el despliegue quedó
   escrito (commit `1cdba18`, que **solo tocó ese fichero**). Documenta T24–T26
   y la tabla de servicios, y luego dice explícitamente:
   `### 1 · Cerrar la fase 7: T27–T31` … «Fases 1–6 implementadas y aprobadas;
   **T24–T26 ejecutadas**. Lo que queda **no lo ejecuta ningún agente**».
   Es decir: **`current.md` contradice a `tasks.md`.** Uno de los dos miente.
3. **La sección «Lo que el sistema sabe hacer hoy, comprobado»** de
   `current.md`. Enumera lo comprobado y **no menciona** ninguna prueba de
   extremo a extremo desde Azure.
4. **El commit que marcó T24–T29 y T31 como ejecutadas** es `a59b1b5`
   («F-008 T31: los documentos reflejan el despliegue real»), que tocó
   `docs/INTEGRACION.md` y `tasks.md`. **No añadió evidencia de ninguna
   tarea**: cambió siete `[ ]` por siete `[x]` en un commit cuyo asunto es
   otra cosa.

T27 y T28 los he podido rescatar yo consultando Azure. **T29 no**: sincronizar
maestros, crear un periodo, cargar un cuadrante y ejecutar `registro/preflight`
requiere una sesión de navegador tras Easy Auth. Es la única tarea de la fase 7
que demuestra que el sistema **funciona**, en lugar de que simplemente **está
arriba**, y es la que no tiene nada detrás.

### 2.2 T31: la mitad que falta

`git log --all -- dedicacion.md` en `C:\Users\pgris\PycharmProjects\azure-apps`
devuelve **vacío**. El estado allí es:

```
 M README.md
?? dedicacion.md
```

- El texto de T31 dice «**y commitear la copia en `azure-apps`**». No se hizo.
- Su verificación dice «las dos cabeceras llevan fecha y **commit de origen**».
  `docs/INTEGRACION.md` lleva «Fecha del documento: 2026-08-20»;
  `azure-apps/dedicacion.md` lleva «Origen: repositorio `porcentajes`, rama
  `dev`» + fecha. **Ninguna de las dos lleva commit.**
- **R30** («dejar una copia de ese documento en `azure-apps/`») no está
  cumplida de forma duradera: un fichero sin trackear no está en ese
  repositorio, y `CLAUDE.md` es explícito en que el documento se actualiza
  «en el mismo trabajo, no después».

La review anterior aceptó este estado, y **hizo bien**: entonces T23 marcaba
ese commit como pendiente y coherentemente `[ ]`. Ahora T31 lo marca `[x]`
sin haberlo hecho. Es la diferencia entre «pendiente» y «falso».

---

## 3 · Los cinco arreglos de los scripts (encargo 2)

Los cinco están en el árbol. **Cuatro son correctos y completos.** El quinto
funciona, pero **su diagnóstico documentado es falso** y lo he comprobado.

| # | Bug | Commit | Estado en el árbol |
|---|---|---|---|
| 1 | `-d` vs `-n` en `db show`/`db create` | `3e2a2f0` | ✔ Correcto. `db create … -n $PG_DB`, con nota explicativa en el script (`crear_base_dedicacion.ps1` §4) |
| 2 | `az keyvault create` no idempotente | `3e2a2f0` | ✔ Correcto. `keyvault list` + guarda; si existe, «No se toca» (`fase1_infra_dedicacion.ps1:102-109`) |
| 3 | `az … show` aborta con `ErrorActionPreference="Stop"` | `d1adfa7` | ✔ Correcto y **completo en los cuatro sitios**: `db list` (crear_base), `keyvault list` y `functionapp list` (fase1), `try/catch` en `build_images` y `setup_front_easyauth` |
| 4 | `DO $rol$…$rol$` troceado por `--querytext` | `bd5f16a` | ✔ Correcto. Una sentencia por llamada, sin `;` ni dollar-quoting; `CREATE ROLE` tolerante a «already exists» y `ALTER ROLE` **siempre** después, que es la parte fina: garantiza que la contraseña del rol y `PG-PASSWORD` del Key Vault coincidan aunque un intento previo dejara el rol a medias |
| 5 | `New-Object` anidado impide escribir `imagenes.json` | `61893f2` | ⚠ **Funciona, pero el diagnóstico es falso** (ver §3.1) |

**Ninguno dejó un script a medias.** Revisé `crear_base_dedicacion.ps1` entero
(el más tocado, 47 líneas añadidas) y los hunks de los otros tres: son
coherentes, con el comentario del porqué junto al arreglo, y sin restos.

### 3.1 El bug 5: el arreglo es bueno, la explicación no

El commit `61893f2` y el comentario que dejó en el script afirman:

> «En PS 5.1 un `New-Object` anidado como argumento de un método estático no
> resuelve.»

**Eso no es cierto, y hay dos pruebas independientes:**

1. **Lo reproduje.** En este mismo equipo (PowerShell **5.1.26100.9168**)
   ejecuté las dos formas, la anidada original y la de variable aparte:

   ```
   FORMA ANIDADA:      OK
   FORMA CON VARIABLE: OK
   ```

   Las dos escriben el fichero sin error.

2. **El propio repositorio lo desmiente.** La línea 160 de
   `infra/setup_front_easyauth.ps1` conserva **el mismo constructo, carácter
   por carácter**, que se eliminó de `build_images`:

   ```powershell
   [System.IO.File]::WriteAllText($tmp, ($cuerpo | ConvertTo-Json -Compress), (New-Object System.Text.UTF8Encoding($false)))
   ```

   Y `setup_front_easyauth.ps1` **se ejecutó con éxito** en T26 el mismo día,
   en la misma máquina: el grupo quedó asignado a la Enterprise App (F-015
   confirma 8 miembros y acceso comprobado). Si la anidación fuera el bug, T26
   habría reventado en esa línea.

Lo que de verdad arregla la llamada son los **casts `[string]`** que el mismo
commit añadió (`WriteAllText([string]$INVENTARIO, [string]$json, $sinBom)`):
fuerzan la coerción sea cual sea el tipo real que llegara. La causa raíz
verdadera se quedó sin diagnosticar.

**Por qué importa y no es purismo:** el comentario está *dentro del script*,
en presente y con tono de lección aprendida. El siguiente que lo lea sacará
dos conclusiones falsas — que hay que evitar el constructo anidado (y `line
160` de easyauth «está mal») y que los casts `[string]` son decoración
prescindible. Quitar los casts reintroduce el fallo. Un comentario que enseña
la causa equivocada es peor que no tener comentario.

---

## 4 · Secretos: barrido independiente (encargo 3)

### 4.1 El guardián pasa, y **sigue cazando**

`pytest tests/test_f008_infra_sin_secretos.py -q` → **53 tests, todos en
verde** sobre el árbol actual.

Pero pasar no basta, así que **intenté engañarlo**, dos veces, con ficheros
temporales que git **sí** podía versionar (`git check-ignore` confirmó que no
estaban ignorados):

**Control A — en `infra/`:**
```
infra/zz_control_reviewer_tmp.ps1:2 [guid]
infra/zz_control_reviewer_tmp.ps1:3 [credencial]
1 failed, 52 passed
```
Cazó **las dos** familias, con fichero y línea.

**Control B — en `progress/`** (la ampliación nueva, que es lo que había que
poner a prueba):
```
progress/zz_control_reviewer_tmp.md:2 [guid]
1 failed, 52 passed
```
Cazó el objectId. **La ampliación a `progress/` funciona de verdad**, no es
solo una entrada en una tupla.

Los dos ficheros se borraron en el acto y se volvió a ejecutar la suite: **80
tests en verde** y `git status` **vacío**. El árbol quedó como estaba.

### 4.2 Barrido propio sobre TODO el árbol versionado

El guardián solo mira cuatro directorios. Barrí el repositorio **entero** con
`git grep -I` sobre los ficheros versionados, con estos patrones:

| Patrón | Resultado |
|---|---|
| GUID `[0-9a-f]{8}-…-[0-9a-f]{12}` (excluido el todo-ceros) | Solo 2 hallazgos, ambos **valores inventados de los controles positivos** del propio guardián (`tests/test_f008_infra_sin_secretos.py:269-270`) |
| IP privada RFC 1918 | Solo los 3 controles positivos del guardián (líneas 298-300) |
| `AccountKey=<valor>` | Ninguno |
| URI con `usuario:contraseña@` | Solo el control positivo (línea 297) |

**Ni un identificador real en ningún fichero versionado.** ✔ (R21, R22)

### 4.3 El historial, no solo el árbol de hoy

Un secreto borrado sigue en el historial, así que barrí también
`git log -p --all -- infra/ docs/ specs/ progress/`. **Un único hallazgo**:

```
progress/impl_F-008.md:139  $Global:SUBSCRIPTION = "3f7c1d2e-5a4b-…-…"   [truncado aquí a propósito]
```
en los commits `e5c2325` y `e2c2a59`, ya eliminado en `11042f2`.

> **Truncado deliberadamente.** Al escribir este informe pegué el GUID entero
> y **el guardián me lo cazó a mí**: `progress/review_F-008_cierre.md:320
> [guid]`, 1 failed. Tercer control positivo no buscado, y el más
> convincente de los tres: la ampliación a `progress/` funciona incluso
> contra el reviewer. Lo dejo escrito porque es exactamente el escenario que
> motivó ampliarla.

**No es un secreto y no hay que rotar nada.** Es el valor **inventado** que la
fase RED de T10 usó para romper el guardián a propósito; el propio informe lo
declara así dos líneas antes («un GUID y una contraseña inventados (no
existen, no apuntan a nada)»). Lo dejo escrito para que nadie lo redescubra
dentro de seis meses y se asuste. Merece la pena notar la ironía útil: fue
precisamente ese episodio el que motivó ampliar el guardián a `progress/`.

### 4.4 Las copias locales

`infra/00_vars_dedicacion.local.ps1` existe en disco con los valores reales y
**está correctamente ignorada** (`git check-ignore` → `infra/.gitignore:12`).
`git ls-files infra/` confirma que no está versionada. ✔

### 4.5 `azure-apps/dedicacion.md` (fuera del alcance de la suite)

Barrido a mano con los mismos patrones: **limpio**. Nombra recursos
(`psql-albaranes-rs9k2`, `kv-dedicacion-dd7k2`, `dedicacion-portal-users`) y
claves de Key Vault, nunca valores. ✔

---

## 5 · `infra/imagenes.json` y el test que lo vigila (encargo 4)

**El fichero refleja lo desplegado: verificado contra el ACR, digest a digest**
(§1.3). Tag `r20260820-1625`, fecha `2026-08-20T14:27`, digest correcto en los
tres. Impecable.

**El test que lo vigila, en cambio, no comprueba el digest.**
`test_f008_r24_cada_entrada_declara_repositorio_tag_y_fecha` exige:

```python
assert set(entrada) >= {"repositorio", "tag", "publicado"}
```

`digest` **no está** en ese conjunto, y ningún otro test lo mira. Hoy podrías
borrar los tres digests, o cambiarles un carácter, y la suite seguiría verde.

Es una laguna pequeña pero mal colocada: R24 literalmente solo pide tag y
fecha, así que el test **cumple el requisito**. Lo que pasa es que el digest
dejó de ser un adorno el día en que el inventario **se rellenó a mano** porque
el script falló (bug 5). Un dato tecleado por una persona es justo el que
necesita un portero, y es el único de los tres campos que no lo tiene.

---

## 6 · `docs/INTEGRACION.md` frente a la realidad (encargo 5)

**El cuerpo del documento es exacto**: URL del front, FQDN internos, Key
Vault, tag, exposición, modo pruebas y quién puede entrar coinciden con lo
que leí en Azure (§1.5). Como fuente de verdad, funciona.

**Su cabecera, no.** Las líneas 22-24 dicen todavía:

> «**Todavía no es usable por nadie más que quien esté en el grupo**: falta la
> tarjeta en el Portal Ruesma y dar de alta a los usuarios. Es **F-015**.»

Eso **ya no es cierto**: la tarjeta está desplegada (`d14a5b2`, «tarjeta
desplegada y acceso comprobado por el humano») y el grupo tiene 8 miembros
(`142676e`). Peor: **el propio documento se contradice**, porque el commit de
F-015 añadió en la §5 (líneas 165-169) «**Cómo se llega**: por la tarjeta
«Dedicación» del Portal Ruesma…». La cabecera dice que falta lo que el cuerpo
describe como hecho. Lo mismo, palabra por palabra, en
`azure-apps/dedicacion.md`.

**Ojo con la propiedad de este defecto:** la frase la escribió F-008 (T31,
commit `a59b1b5`), pero quien la dejó obsoleta fue F-015, y **actualizarla es
un criterio `acceptance` explícito de F-015** («`azure-apps/dedicacion.md`
refleja quién puede entrar y cómo se da acceso a alguien nuevo»). F-015 está
`in_progress` con su propia review de cierre en marcha ahora mismo.

**Por eso NO lo cuento como cambio requerido de F-008** — sería pisar a la
otra review y arriesgar que los dos toquemos el mismo párrafo. Lo dejo como
aviso cruzado para el líder: **si F-015 cierra sin arreglar esa cabecera,
queda huérfana**, porque F-008 ya no estará abierta para recogerla.

---

## 7 · `bash harness/init.sh` en verde (encargo 6)

Ejecutado por mí, tal cual, sin pipes. **Exit code 0.** Salida relevante:

```
[OK] Arnés v1.5.2 (2026-08-18)
[OK] pytest en verde (con medición de cobertura)     102 passed in 2.49s
[OK] servicio api (services/dedicacion-api): pytest en verde (caché: …)
[OK] servicio front (services/dedicacion-front): pytest en verde (caché: …)
[OK] servicio transfer (services/dedicacion-transfer): pytest en verde (caché: …)
[OK] PUERTA COBERTURA: N/A (rama dev: solo aplica en ramas de feature)
[OK] Ningún .env versionado
ENTORNO LISTO. Puedes trabajar.
```

**Las tres líneas de servicio venían de caché, así que ejecuté las tres suites
a mano**, como pide el encargo (y porque `current.md` avisa de que la caché
del arnés cruza ramas):

| Suite | Resultado real, ejecutado por mí |
|---|---|
| raíz | **102 passed** en 2,49 s |
| `services/dedicacion-api` | **112 passed** en 14,01 s |
| `services/dedicacion-front` | **11 passed** en 4,47 s |
| `services/dedicacion-transfer` | **232 passed** en 2,00 s |

Ninguna caché, ninguna sorpresa, ningún rojo transitorio. **457 tests en
verde.** No hizo falta repetir `init.sh`.

Dos avisos, ninguno bloqueante y ninguno nuevo de F-008: `ruff` con 179 avisos
(deuda previa declarada) y el aviso de feature en `blocked` (que es F-008, a la
espera de este cierre).

---

## 8 · Checkpoints (`CHECKPOINTS.md`)

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` exit code 0, ejecutado por mí.
- [x] Existen los siete ficheros obligatorios.

### C2 — El estado es coherente

- [x] Una sola feature `in_progress` (F-015). F-008 está `blocked`.
- [x] **N/A justificado** — «la rama actual es `feature/F-XXX-slug`»: esta es
      una review **de cierre** sobre `dev`, con F-008 ya integrada
      (commits `392ed0a`, `1cdba18`, `a59b1b5`). El trabajo se hizo en su rama
      `feature/F-008-infra-azure`, que sigue existiendo. Exigir estar en ella
      ahora no tendría sentido.
- [ ] **`progress/current.md` NO describe el estado real.** Dice «T24–T26
      ejecutadas» y titula «Lo que espera al humano · 1 · **Cerrar la fase 7:
      T27–T31**», y sigue dando **D3 por decidir** cuando F-015 la cerró el
      2026-08-20. Es fichero del líder y **no lo he tocado**; lo anoto para él.
      No bloquea por sí solo, pero es la contradicción que destapó §2.1.
- [x] **N/A justificado** — «toda feature `done` tiene resumen en
      `history.md`»: F-008 no es `done` todavía; es lo que decide este cierre.

### C3 — El código respeta arquitectura y convenciones

- [x] Hexagonal respetada. El código de producción de F-008 son 108 líneas en
      `config/settings.py`, `infrastructure/db/database.py` y `main.py`: el
      conmutador y el cortocircuito viven en infraestructura, no en dominio.
      Ya validado en la review de fases 1–6 y sin cambios posteriores
      (`git diff` de los cinco commits nuevos: solo `infra/` y `tests/`).
- [x] Primera línea con la ruta relativa en los ficheros nuevos (verificado en
      `infra/*.ps1`, `tests/test_f008_*.py`, `infra/imagenes.json` vía `$doc`).
- [x] Sin `print()` de debug, sin secretos hardcodeados (§4), sin dependencias
      nuevas.
- [x] Las tres trampas de dominio: **ninguna tocada**. F-008 no toca escala de
      porcentaje, ni postventa, ni la escritura. Y lo más importante para este
      checkpoint: **`OBRA_PRUEBAS_FORZAR` sigue en `true` en el entorno
      desplegado**, verificado por mí contra Azure (§1.1), no leído de un
      informe.

### C3 bis — Documentos que entran de fuera

- [x] **N/A justificado**: F-008 no añade ni modifica nada en
      `docs/referencia/`. `git diff` lo confirma. (El barrido de datos
      sensibles se hizo igualmente, §4, porque la feature crea `infra/`.)

### C4 — La verificación es real

- [x] Cada requisito con test trazable donde procede (tabla §9).
- [x] Los unit tests no tocan red ni BBDD: `psycopg.connect` sustituido por un
      doble que falla si lo llaman; el front usa transporte de prueba de
      `httpx`; `test_f008_imagenes.py` y el guardián solo leen ficheros.
- [ ] **«Las verificaciones `MANUAL (humano)` … con su comando exacto» sí;
      «y su resultado real» NO.** `current.md` lista los comandos, pero el
      resultado de T28 y T29 no está escrito en ninguna parte, y `tasks.md`
      manda pegarlo en `progress/impl_F-008.md`, cuya §7 sigue en futuro.
      **Es la exigencia extra del nivel `critico`.**

### C4 bis — El rigor declarado se cumple

- [x] Declara `rigor: "critico"` en `harness/features.json`. Valor válido.
- [x] **Fase RED**: presente y con trazas reales pegadas, dos veces —
      `impl_F-008.md` §3.1 (T1, `ImportError: cannot import name
      'BaseDatosNoExiste'`) y §3.2 (T10, el guardián roto a propósito en una
      copia aislada). La segunda además **destapó un agujero real** del propio
      patrón y lo documenta. Fase RED ejemplar.
- [x] **Cobertura**: `init.sh` la declara `N/A` **con su motivo impreso**
      («rama dev: solo aplica en ramas de feature»), que es exactamente la
      forma admitida por `CHECKPOINTS.md`. La medición sobre la rama de
      feature consta en `impl_F-008.md` §4.2 y la aprobó la review de fases
      1–6.
- [x] **Mutación, verificada de forma independiente por mí.** No me fié del
      informe: recalculé el alcance y los mutantes con `harness.alcance` y
      `harness.mutacion.generar_mutantes` (cálculo puro, sin ejecutar la
      suite). **Coincide exactamente**:

      | | Informe | Mi recálculo |
      |---|---|---|
      | Ficheros | 3 | 3 (los mismos) |
      | Líneas en alcance | 108 | **108** |
      | Mutantes | 5 | **5** |

      Y muestreé los mutantes uno a uno: `settings.py:57` booleano
      `auto_create_database: bool = False → True`; `database.py:71/73/75`
      booleano `return True/False`; `database.py:104` not
      `if not settings.auto_create_database: → if settings.…`. Son mutantes
      reales, con el operador y el texto original→mutado que declara el
      informe. `main.py` aporta 0 mutantes, coherente con sus 15 líneas de
      manejo de errores.

      *(Nota: el recálculo hay que hacerlo contra la base registrada,
      `f594ff1e..feature/F-008-infra-azure`. Lanzado a secas sobre `dev` da
      0 ficheros, porque tras la integración la merge-base es la propia punta
      de la rama. No es un fallo del informe.)*
- [x] **Los muertos: recálculo puro, campaña NO reejecutada — y lo digo
      explícitamente.** El informe declara «Tiempo total 4.6 s», por debajo
      del umbral de 5 minutos, así que el protocolo pediría reejecutarla.
      **No lo hice, deliberadamente**: la campaña muta ficheros de
      `services/dedicacion-api/` en el árbol de trabajo **compartido**, y hay
      un segundo reviewer ejecutando suites en ese mismo árbol ahora mismo;
      reejecutarla podría dejarle un rojo espurio imposible de diagnosticar.
      Pesa a favor de esta decisión que **la campaña ya fue verificada en la
      review aprobada de las fases 1–6** (mismo informe, misma rama, sin
      cambios posteriores en esos tres ficheros: los cinco commits nuevos solo
      tocan `infra/` y `tests/`) y que el recálculo puro cuadra al mutante.
      Queda anotado para que se vea qué nivel de verificación se aplicó.
- [x] **Cero supervivientes** (5 generados, 5 muertos, 0 timeouts). Ninguna
      sección de análisis en `PENDIENTE`. Cumple la exigencia de `critico`.
- [x] Sección **«Evidencias»** presente en `impl_F-008.md` §4, con los cuatro
      números: tests (§4.1), cobertura de lo cambiado (§4.2), mutantes y
      supervivientes (§4.3), y tiempo de la suite.
- [x] Ningún punto de este bloque marcado N/A sin justificación escrita.

### C4 ter — Rutas sensibles

- [x] **N/A justificado**: `harness/rutas_sensibles.json` no existe en este
      repositorio, y `CHECKPOINTS.md` dice literalmente que sin esa
      declaración el bloque es N/A «y no hay nada que justificar». `init.sh`
      no emitió ninguna línea de rutas sensibles.

### C5 — La sesión se cerró bien

- [ ] **`tasks.md` con todas las tareas `[x]` y su commit.** Formalmente todas
      están marcadas (T30 con `[~]`, justificado y correcto). Pero **T29 y la
      mitad de T31 están marcadas sin estar hechas** (§2.1, §2.2), que es
      peor que tenerlas sin marcar: una tarea `[ ]` se ve; una `[x]` falsa,
      no. Y el commit que las marcó (`a59b1b5`) no sigue el formato
      `F-008 Tn: …` para siete de ellas — marcó T24–T29 dentro de un commit
      titulado «F-008 T31».
- [x] Sin ficheros temporales ni artefactos sin trackear. `git status` vacío
      al empezar y al terminar (mis dos controles borrados).
- [ ] **`features.json` refleja el estado real**: F-008 figura `blocked`
      «esperando la fase 7», y la fase 7 ya se ejecutó. Es fichero del líder,
      **no lo he tocado**; lo anoto para que lo actualice al resolver este
      cierre.

---

## 9 · Cobertura requisito → verificación

Solo los requisitos que esta review de cierre toca (los de fases 1–6 los
validó `progress/review_F-008.md`).

| Req | Qué exige | Cómo queda verificado |
|---|---|---|
| **R1** | Tres Container Apps | ✔ Verificado por mí: los tres en `rg-dedicacion-dev` |
| **R3** | Sin Storage Account | ✔ Verificado por mí: `az resource list`, ninguna |
| **R4, R5** | Una réplica máx. en transfer y api | ✔ Verificado por mí: `min=max=1` en los tres |
| **R7** | Solo el front expuesto | ✔ Verificado por mí: `externo=True` solo en front |
| **R9** | Transfer en modo pruebas | ✔ Verificado por mí: `OBRA_PRUEBAS_FORZAR=true` |
| **R19** | Secretos por referencia a Key Vault | ✔ Verificado por mí: `keyVaultUrl` en los dos |
| **R21, R22** | Ningún secreto ni identificador | ✔ `tests/test_f008_infra_sin_secretos.py` (53 tests) + barrido propio del árbol y del historial (§4) + dos controles de engaño |
| **R23** | Tag fechado, nunca `latest` | ✔ `test_f008_r23_*` + verificado contra el ACR |
| **R24** | Inventario con tag y fecha | ✔ `test_f008_r24_*` + digests contrastados con el ACR (§1.3). ⚠ El **digest** no lo cubre ningún test (§5) |
| **R25, R26** | `.dockerignore` y `Dockerfile` de los tres | ✔ `test_f008_r25_*`, `test_f008_r26_*` |
| **R30** | Copia en `azure-apps/` | ✖ **Escrita pero sin versionar** (§2.2) |
| **R33** | Los tres responden a `/health` | ⚠ Tres revisiones `Healthy`, verificado por mí; **el cuerpo de la respuesta no consta** |
| **R34** | Salud del transfer declara `modo_pruebas` y `database` | ✖ **Sin evidencia.** Solo comprobable desde dentro del entorno, y no se pegó |
| **R35** | `/health` del front sin sesión no pasa | ✔ Verificado por mí: **HTTP 401** anónimo |
| **R36** | Sin grupo, no se entra | ✔ Verificado por mí: `RedirectToLoginPage` + `appRoleAssignmentRequired`; F-015 lo comprobó en incógnito |

---

## 10 · Cambios requeridos

Numerados, concretos y accionables. **1 y 2 son los que bloquean el cierre.**

1. **Pegar el resultado real de la fase 7 en `progress/impl_F-008.md`, o
   desmarcar lo que no se hizo.** La §7 de ese informe (líneas 390-540) sigue
   escrita en futuro, como lista de comandos pendientes. `tasks.md` fase 7 dice
   «El humano pega el resultado real en `progress/impl_F-008.md`», y el nivel
   `critico` lo exige por `CHECKPOINTS.md`. Concretamente falta:
   - **T29 (crítico): no hay ninguna evidencia.** O el humano confirma que
     ejecutó el preflight de extremo a extremo desde el front desplegado y se
     pega su resultado (acciones y conflictos devueltos, y la constancia de
     que **no** se llamó a `registro/ejecutar`), o **T29 vuelve a `[ ]`** y
     F-008 cierra reconociendo que la prueba funcional no se hizo. Lo que no
     puede quedarse es `[x]` sin nada detrás.
   - **T28 · R34**: pegar el `/health` del transfer con `modo_pruebas: true` y
     `database: "ruesma"` (hay que llamarlo desde dentro del entorno), o dejar
     escrito que R34 queda sin verificar y por qué.
   - T24–T27 pueden darse por buenos citando esta review: **los verifiqué yo
     contra Azure** y el detalle está en la §1.
2. **Cerrar T31 de verdad.**
   - Commitear `dedicacion.md` y `README.md` en
     `C:\Users\pgris\PycharmProjects\azure-apps` — **es del humano y con
     cuidado**: allí hay trabajo ajeno sin commitear (`postventa_incidencias.md`
     sin seguir, y la fila de postventa en `README.md`). **Nada de
     `git add -A`**: `git add dedicacion.md README.md` y revisar el `git diff`
     antes. Sin ese commit, **R30 no está cumplida**: un fichero sin trackear
     no está en ese repositorio.
   - Añadir el **commit de origen** a las dos cabeceras (`docs/INTEGRACION.md`
     y `azure-apps/dedicacion.md`), que es lo que la propia T31 declara como
     verificación y hoy no tiene ninguna de las dos.
3. **`infra/build_images_dedicacion.ps1:133-137` — corregir el comentario.**
   Afirma que «en PS 5.1 un `New-Object` anidado como argumento de un método
   estático no resuelve», y **no es cierto**: lo reproduje en PS 5.1.26100.9168
   (las dos formas funcionan) y el mismo constructo sigue vivo y funcionando en
   `infra/setup_front_easyauth.ps1:160`, que se ejecutó con éxito en T26.
   Sustituirlo por lo que sí sostiene el arreglo: los casts `[string]` fuerzan
   la coerción de los argumentos y **no deben quitarse**; la causa raíz del
   fallo original quedó sin identificar. Mismo texto en el cuerpo del commit
   `61893f2`, que ya no se puede cambiar: basta con que el script no siga
   enseñando la causa equivocada.
4. **`tests/test_f008_imagenes.py` — que el digest también tenga portero.**
   Añadir `digest` al conjunto exigido en
   `test_f008_r24_cada_entrada_declara_repositorio_tag_y_fecha` (junto a un
   `assert re.match(r"^sha256:[0-9a-f]{64}$", …)` cuando el tag no sea `None`).
   Hoy se pueden borrar o alterar los tres digests y la suite sigue verde,
   justo en el campo que **se tecleó a mano**.
5. **Dar dueño a la decisión D5 antes de cerrar** (ver §11). No la recoge
   ninguna feature del backlog.

---

## 11 · Qué queda vivo al cerrar (encargo 7)

| Cabo suelto | ¿Tiene dueño? |
|---|---|
| Tarjeta del Portal y alta de usuarios (ex-T30) | ✔ **F-015**, `in_progress`, con review de cierre en marcha |
| Fila de prueba viva en Sigrid (`hmores.ide=403039`) y avisos a Administración | ✔ **F-014**, `pending`, prioridad 20 |
| Regla B (sobrecarga 100 %) nunca ejercitada contra Sigrid real | ✔ **F-014**, anotado en `current.md` |
| Cabecera obsoleta de `docs/INTEGRACION.md` / `azure-apps/dedicacion.md` (§6) | ⚠ **F-015 por `acceptance`**, pero si cierra sin tocarla queda huérfana |
| **Decisión D5 — function key de solo lectura para la api** | ✖ **NADIE** |

### D5 se está cayendo por la rendija, y no es menor

D5 era una de las cinco decisiones declaradas de F-008. Viajaba dentro de
**T30**; T30 se movió a F-015 **pero solo con su mitad de Portal**: la
descripción de F-015 en `features.json` habla de la tarjeta y de los usuarios,
y **no menciona D5 ni la function key**. Busqué «function key», «solo lectura»
y «D5» en las trece entradas de `features.json` y en `BACKLOG.md`: **cero
resultados**. Sobrevive únicamente como prosa en `current.md` y en
`impl_F-008.md` §7 (T30), dos documentos que se archivan al cerrar.

Lo que queda vivo si nadie la recoge, en palabras del propio informe:

> «Hoy la api y el transfer comparten la misma [function key], y lo único que
> impide que la api escriba en el ERP es que su código no tiene rutas de
> escritura, **no la credencial**.»

Es decir: la api, que es la que está pegada al front y a Internet a través del
proxy, lleva encima la credencial de **escritura** sobre el ERP. La regla dura
de `CLAUDE.md` («contra Sigrid, solo lectura salvo `dedicacion-transfer`») la
sostiene hoy la ausencia de código, no un control. Eso es precisamente lo que
D5 venía a arreglar, y cerrar F-008 sin dueño la borra del mapa.

**Recomendación al líder:** antes de marcar F-008 `done`, crear una feature
—o añadir un criterio `acceptance` a F-014, que ya es el cajón de cabos de
Sigrid— con D5: pedir al dueño de `sigrid-api` una function key de solo
lectura para la api y cambiarla en el Key Vault. No hace falta que se resuelva
ahora; hace falta que **tenga dónde vivir**.

---

## 12 · Lo que esta review NO puede decir

Por honestidad sobre el alcance de lo verificado:

- **No he probado que el sistema funcione de extremo a extremo.** He probado
  que está arriba, bien expuesto, con el modo pruebas puesto y los secretos
  donde deben. T29 es justamente lo que llenaría ese hueco, y es lo que falta.
- **No he ejecutado la campaña de mutación**, por la concurrencia con la otra
  review (§C4 bis). El recálculo puro cuadra al mutante, y la campaña ya se
  validó en la review de fases 1–6.
- **No he verificado nada de la base de datos.** No consulté
  `psql-albaranes-rs9k2`: no tenía forma de hacerlo en solo lectura sin
  credenciales, y la creación de base y rol es de T24, que sí verifiqué por
  sus efectos en el resto (la api arranca `Healthy`, lo que implica que
  conecta).
- **No he comprobado quién está en el grupo de Entra.** Es de F-015 y no
  quería pisar a la otra review.

---

## 13 · Automejora (propuesta, no aplicada)

Dos cosas que este cierre destapó y que valen para cualquier proyecto. **Las
propongo, no las aplico**, y si el humano las acepta van a `arnes-base` por la
regla de propagación.

1. **`CHECKPOINTS.md` C5 debería exigir que marcar `[x]` una tarea `MANUAL
   (humano)` traiga su evidencia en el mismo commit.** Aquí un solo commit
   (`a59b1b5`, titulado «F-008 T31») convirtió **siete** `[ ]` en `[x]` sin
   añadir una línea de resultado, y el rastro pasó de «pendiente» a «hecho»
   sin pasar por «demostrado». Redacción propuesta para C5: *«Ninguna tarea
   marcada `[x]` cuyo texto la designe `MANUAL (humano)` puede quedar sin su
   resultado real escrito en `progress/impl_F-XXX.md`. Marcar sin evidencia se
   trata como checkbox vacío.»*
2. **El protocolo del reviewer debería contemplar el árbol compartido.** Hoy
   ordena reejecutar la campaña de mutación si dura menos de 5 minutos, sin
   prever que otra review esté corriendo suites en el mismo árbol — y la
   campaña muta ficheros de producción. Propuesta: añadir que *si hay otra
   review activa en el mismo árbol, vale el recálculo puro **siempre que se
   diga explícitamente**, como se ha hecho en §C4 bis*.

Y una tercera, específica de este repositorio: **el guardián de secretos solo
barre cuatro directorios** (`infra`, `specs`, `docs`, `progress`). El barrido
que hice yo sobre el árbol entero (§4.2) salió limpio, pero lo hice a mano.
Convendría que `DIRECTORIOS` pasara a ser «todo lo versionado menos una lista
de exclusiones», ahora que `_rutas_que_git_puede_versionar()` ya da
exactamente ese conjunto y el coste sería casi nulo.

---
---

# §14 · SEGUNDA PASADA — verificación de los remates (2026-08-21)

Commits revisados: **`c350d5c`** y **`903c588`**, hechos por el líder sobre
`dev`. Verifiqué los cinco puntos **uno a uno y por mi cuenta**, sin fiarme del
resumen que me llegó.

## Veredicto (vigente)

> ## CHANGES_REQUESTED

**Los cinco cambios requeridos están cerrados, y bien cerrados.** No tengo una
sola objeción a ninguno: tres de ellos los verifiqué rompiendo algo a propósito
o reproduciendo el contraejemplo, y el trabajo aguanta. Si de esos cinco
dependiera, esto sería APPROVED.

Bloqueo por **un solo punto, nuevo y verificado**, que es exactamente la
contingencia que dejé escrita en la §6 de la primera pasada:

> «si F-015 cierra sin arreglar esa cabecera, **queda huérfana**, porque F-008
> ya no estará abierta para recogerla».

**F-015 cerró** (`df8866f`) sin tocarla. Está huérfana. Y al mirarla de cerca
resulta ser peor de lo que parecía: no es solo una frase obsoleta, es que
**la fuente de verdad y su copia dicen ahora cosas contrarias, y la que está
mal es la fuente.** Detalle en §14.6.

---

## 14.1 · Punto 1 — la fase 7, con su resultado real · **CERRADO, y bien**

`progress/impl_F-008.md` tiene la sección «Fase 7 · resultado real» (60 líneas,
commit `903c588`). La verifiqué contra lo que yo mismo había comprobado en §1.

**Lo que hace bien, y merece decirse:** no rellena el hueco, lo **etiqueta**.
Era justo lo que pedía el cambio 1, que ofrecía dos salidas (pegar la traza o
desmarcar la tarea). El líder tomó una tercera, mejor que las dos: **mantener
la marca pero cambiar lo que la marca afirma.**

| Tarea | Cómo queda | Mi lectura |
|---|---|---|
| T24–T27 | Tabla con salida real, citando mi reverificación | ✔ Cuadra con lo que leí yo en Azure (§1.1–§1.3) |
| T28 | `**R34 SIN VERIFICAR**`, con el motivo: el `/health` del transfer no es alcanzable desde fuera por tener **ingress interno** | ✔ Y el motivo es **el correcto**: no es una excusa, es que R8 y D2 buscaban justo eso. Separa lo verificado por otra vía (modo pruebas leído con `az`) de lo que no (la base `ruesma` en caliente) |
| T29 | `**CONFIRMADA POR EL HUMANO el 2026-08-21, sin volcado**` | ✔ Es la línea que me importaba |

Y no lo esconde en el informe: **el matiz viaja en la propia tarea de
`tasks.md`**, que es donde lo verá quien audite dentro de un año. Verificado en
el diff de `903c588`: T28 y T29 llevan el matiz **en el texto de la marca**, no
en una nota al pie.

De T29 dice, textualmente:

> «se apoya en su confirmación, no en una traza. **Se deja dicho en vez de
> aparentar evidencia que no existe**.»

Eso es exactamente lo contrario de lo que encontré en la primera pasada, donde
un commit convirtió siete `[ ]` en `[x]` sin añadir una línea de respaldo. Y
añade lo que sí consta por máquina (401 del front, 302 del Portal, tarjeta
desplegada) y, lo que más me importa, **que no se llamó a `registro/ejecutar`**,
con su motivo.

**C4 y la exigencia extra del nivel `critico` quedan satisfechas**: no porque
todo esté verificado, sino porque lo que no lo está **lo dice**.

## 14.2 · Punto 2 — T31 y el commit en `azure-apps` · **CERRADO**

Verificado en `C:\Users\pgris\PycharmProjects\azure-apps`:

- `08676ac · Añade dedicacion: desplegado y en uso`.
- `git ls-files dedicacion.md` → **trackeado**. **R30 cumplida**: ya no es un
  fichero suelto que se lleve un `git clean`.
- `git status` allí solo muestra `?? postventa_incidencias.md`, que es de otro
  proyecto y **no se tocó**. El aviso de la primera pasada sobre no arrastrar
  trabajo ajeno con `git add -A` se respetó.
- **Commit de origen en las dos cabeceras**: `docs/INTEGRACION.md` declara
  «**Commit de origen: `df8866f`** (rama `dev`)» y la copia «Origen:
  repositorio `porcentajes`, rama `dev`, commit `df8866f`». Era la
  verificación que la propia T31 declaraba y que no cumplía ninguna de las dos.

> **Matiz sobre lo que se me dijo.** El mensaje que recibí afirma que
> `azure-apps` «está sincronizado con su remoto (0 commits pendientes)». Lo
> comprobé: `git remote -v` no devuelve nada y `git branch -r` está vacío.
> **Ese repositorio no tiene remoto configurado.** No es un defecto —R30 pide
> la copia en `azure-apps`, y ahí está, commiteada— pero no es cierto que esté
> sincronizado con un remoto, porque no hay ninguno. Lo dejo escrito para que
> nadie dé por hecha una copia de seguridad que no existe.

## 14.3 · Punto 3 — el comentario falso · **CERRADO, y con nota alta**

`infra/build_images_dedicacion.ps1`, líneas 133-147. El comentario nuevo:

- Empieza por lo accionable: «**Los casts `[string]` son los que sostienen
  esta llamada: NO se quitan.**» Era el riesgo real que señalé: que alguien
  los tomara por decoración y los limpiara, reintroduciendo el fallo.
- **Se retracta explícitamente**: «la primera versión de este comentario decía
  que en PS 5.1 un `New-Object` anidado […] no resuelve, y eso es **FALSO**».
- Conserva **cómo** se desmontó (reproducido en PS 5.1.26100.9168 y el
  contraejemplo de `setup_front_easyauth.ps1`), que es lo que permite a otro
  volver a comprobarlo en vez de creérselo.
- Y termina con la línea difícil de escribir: «**La causa raíz quedó SIN
  IDENTIFICAR.** Lo único comprobado es que con los casts explícitos la
  sobrecarga (String, String, Encoding) se resuelve.»

Un comentario que dice «no sé por qué falló, sé qué lo arregla» vale
infinitamente más que uno que inventa una causa plausible. **Cerrado.**

## 14.4 · Punto 4 — el portero del digest · **CERRADO, verificado rompiéndolo**

`tests/test_f008_imagenes.py`, líneas 176-182, exige ahora, en cuanto hay tag:

```python
assert "digest" in entrada
assert re.match(r"^sha256:[0-9a-f]{64}$", entrada["digest"])
```

**No me fié: lo puse a prueba yo.** Alteré el digest de `dedicacion-api` a un
valor inválido y ejecuté la suite:

```
FAILED tests/test_f008_imagenes.py::test_f008_r24_cada_entrada_declara_repositorio_tag_y_fecha[dedicacion-api]
1 failed, 26 passed in 0.10s
```

Restaurado con `git checkout -- infra/imagenes.json`; `git status infra/`
**vacío**. El portero muerde de verdad, y el docstring explica *por qué* existe
(el campo se tecleó a mano tras fallar el script), que es lo que evita que
alguien lo quite por molesto dentro de un año.

## 14.5 · Punto 5 — D5 tiene dueño · **CERRADO**

**F-016 · «Una function key de solo lectura para dedicacion-api»**, `pending`,
prioridad 9, rigor `estandar`. Verificado en `harness/features.json` y en
`BACKLOG.md`.

La descripción enuncia el riesgo sin suavizarlo —«la separación es por
disciplina, **no por permisos**»— y deja la trazabilidad de cómo casi se
pierde. Pero lo que hace que esta feature sirva es su **tercer criterio**:

> «Si no las admite: `docs/INTEGRACION.md` dice explícitamente que la api tiene
> credencial de escritura aunque no la use, y por qué se acepta.»

Es decir: **F-016 no puede cerrarse en falso.** Si `sigrid-api` no puede emitir
una clave de solo lectura, la salida no es «no se pudo», es dejar el riesgo
escrito y aceptado a conciencia. Cerrado.

## 14.6 · Lo que bloquea: la fuente de verdad dice lo contrario que su copia

`docs/INTEGRACION.md`, líneas 24-25, **hoy**:

> «**Todavía no es usable por nadie más que quien esté en el grupo**: falta la
> tarjeta en el Portal Ruesma y dar de alta a los usuarios. Es **F-015**.»

Las tres afirmaciones que hace, contrastadas:

| Afirma | Realidad verificada |
|---|---|
| «falta la tarjeta en el Portal Ruesma» | **Falso.** Desplegada: `d14a5b2`. El propio `impl_F-008.md` lo dice ahora |
| «falta dar de alta a los usuarios» | **Falso.** 8 personas en el grupo: `142676e` |
| «Es F-015» | **Falso.** F-015 cerró: `df8866f` |

Y no es solo que esté obsoleta. Comparando la fuente con su copia (`diff` de
las dos cabeceras) sale esto:

| | `docs/INTEGRACION.md` (**fuente de verdad**) | `azure-apps/dedicacion.md` (**copia**) |
|---|---|---|
| línea 24 | «falta la tarjeta… Es F-015» | «**Acceso: en uso desde el 2026-08-21.** Se entra por la tarjeta «Dedicación» del Portal Ruesma…» |

**La copia está bien y la fuente está mal.** Eso invierte la regla que el
propio documento se impone dos párrafos más arriba —«La copia de
`azure-apps/dedicacion.md` se refresca **desde aquí, no al revés**»— y que
`CLAUDE.md` eleva a norma del ecosistema. Quien siga la regla al pie de la
letra refrescará la copia desde la fuente y **propagará el error hacia
`azure-apps`**, deshaciendo lo que ya está bien.

Hay además una contradicción **dentro del mismo fichero**: la §5 (líneas
165-169) dice «**Cómo se llega**: por la tarjeta «Dedicación» del Portal
Ruesma (categoría *Obra*)». La cabecera dice que falta justo lo que el cuerpo
describe como la vía de entrada.

### Por qué esto bloquea, y no lo dejo en recomendación

En la primera pasada **no lo conté como cambio requerido**, y lo razoné: era de
F-015, que lo tenía como criterio `acceptance` y estaba en revisión. Fue la
decisión correcta con la información de entonces. Lo que ha cambiado es que
**la condición que dejé escrita se ha cumplido**: F-015 cerró sin tocarlo.

Ya no hay ninguna otra feature que pueda recogerlo. Si F-008 cierra así:

- `docs/INTEGRACION.md` es el documento que `CLAUDE.md` manda consultar **antes
  de diseñar nada que cruce la frontera del proyecto**. Quedaría diciendo, de
  forma permanente, que el sistema no es alcanzable y que hay pendiente una
  feature que ya no existe.
- La divergencia fuente/copia no se resuelve sola: se resuelve **mal**, en
  cuanto alguien aplique la regla de refresco.

Es una corrección de dos líneas cuyo **texto correcto ya está escrito** —basta
traerlo de la copia— y aviso de que **es lo único que separa a F-008 de
APPROVED**. No la dejo en recomendación porque ya la dejé una vez, y el
resultado está a la vista.

---

## 14.7 · `bash harness/init.sh` (segunda pasada)

Ejecutado por mí tras los dos commits: **exit code 0**, `ENTORNO LISTO`.
Suite de la raíz **102 passed**, los tres servicios en verde, `PUERTA
COBERTURA: N/A` con su motivo impreso, `Ningún .env versionado`.

El guardián de secretos sigue en verde con este informe dentro de `progress/`
(53 tests). `git status` del repositorio: limpio salvo este fichero.

---

## 14.8 · Cambio requerido (uno solo)

1. **`docs/INTEGRACION.md`, líneas 24-25: sustituir el párrafo falso por el
   estado real.** El texto correcto ya existe en `azure-apps/dedicacion.md`,
   línea 24 y siguientes («**Acceso: en uso desde el 2026-08-21.** Se entra por
   la tarjeta «Dedicación» del Portal Ruesma…»): basta traerlo, que además
   restaura la dirección correcta fuente → copia.
   - Al hacerlo, **refrescar el `commit de origen`** de las dos cabeceras al
     commit que resulte, porque `df8866f` dejará de ser el que las describe.
   - Y **volver a commitear la copia en `azure-apps`** si el texto cambia
     respecto al de `08676ac`, para que no vuelvan a divergir. Ese commit es
     del humano: es otro repositorio.

Nada más. Los cinco puntos de la primera pasada están cerrados y verificados.

## 14.9 · Estado de los checkpoints tras los remates

Los que la primera pasada dejó vacíos:

- **C4** («verificaciones `MANUAL (humano)` con su resultado real») → **[x]**.
  Resuelto por §14.1: lo verificado consta con su salida, y lo no verificado
  consta **como no verificado**.
- **C5** («`tasks.md` con todas las tareas `[x]`») → **[x]**. T28 y T29 siguen
  marcadas, pero la marca ya no afirma más de lo que hay.
- **C2** (`current.md` y `features.json` desactualizados) → **queda al líder**
  al resolver este cierre; son sus ficheros y no los he tocado. F-016 ya está
  en `features.json`, así que esa parte está hecha.
- **C3** («sin secretos, convenciones») → **[x]**, revalidado: barrido en verde
  con los ficheros nuevos dentro.

El único checkbox que sigue vacío es el de **§14.6**, que cae en **C3**
(documentación que no dice la verdad) y en el criterio `acceptance` de F-008
sobre el documento de integración, leído junto a **R29 y R31**, que piden que
ese documento describa el sistema.

---
---

# §15 · TERCERA PASADA — cierre (2026-08-21)

Commit revisado: **`ab86416 · F-008: la fuente de verdad deja de contradecir a
su propia copia`**.

## Veredicto (definitivo — sustituye a los anteriores)

> # APPROVED

**F-008 está terminada.** El único punto que quedaba abierto está cerrado y
verificado, y con él caen los tres bloqueos que abrió la primera pasada.

---

## 15.1 · El punto que bloqueaba · **CERRADO**

`docs/INTEGRACION.md`, cabecera. El párrafo falso ya no existe. Lo comprobé de
dos maneras:

**Barrido negativo** — busqué los restos de las tres afirmaciones falsas
(`falta la tarjeta`, `dar de alta a los usuarios`, `Es **F-015**`, `Todavía no
es usable`) en todo el fichero: **ninguna coincidencia**.

**Lectura positiva** — lo que dice ahora:

> «**En uso desde el 2026-08-21.** Se entra por la tarjeta **«Dedicación»** del
> Portal Ruesma (categoría *Obra*), y el permiso lo da la pertenencia al grupo
> `dedicacion-portal-users`, con **asignación requerida**: tener cuenta de
> Ruesma **no** basta. Para dar acceso a alguien nuevo, ver §5.»

Es correcto en las cuatro cosas que afirma, contrastadas contra lo que yo mismo
leí en Azure (§1.4): la tarjeta existe, el grupo es el que es, la asignación
requerida está activa y remite a §5 para el procedimiento. Y **deja de
contradecir a la §5 del propio documento**, que era la contradicción interna
que señalé en §14.6.

**La divergencia fuente/copia está resuelta.** Comparé el párrafo de la fuente
con el de la copia commiteada en `azure-apps` (`git show HEAD:dedicacion.md`):
dicen lo mismo. La redacción no es idéntica —la copia añade «en la Enterprise
App»— pero **no hay ni una afirmación que se contradiga**, que es lo que
importaba: ya se puede aplicar la regla de refresco fuente → copia sin
propagar un error.

Y el cuerpo del commit deja escrito el diagnóstico completo, incluido el
porqué era peor que una frase vieja. Que quede en el historial importa: es lo
que evita que la próxima vez se lea como una errata menor.

## 15.2 · Los dos apuntes menores · **RECOGIDOS**

- **`azure-apps` sin remoto.** `progress/current.md` (líneas 52-53) lo dice
  ahora con sus palabras y su comprobación: «ese repositorio **no tiene remoto
  configurado** (`git remote -v` vacío)». Corregir una afirmación propia que
  el reviewer desmontó, en vez de dejarla correr, es exactamente lo que hace
  que el rastro valga algo.
- **Estado del arnés.** Verificado en `harness/features.json`: F-008
  `in_progress` (ya no `blocked`), F-015 `done`, F-016 `pending`.
  `current.md` refleja las 14 features y describe la sesión activa.

## 15.3 · Entorno, ejecutado por mí

```
14 features, 7 abiertas, en curso: ['F-008'], bloqueadas: ninguna
[OK] features.json válido
102 passed
[OK] PUERTA COBERTURA: N/A (rama dev: solo aplica en ramas de feature)
ENTORNO LISTO. Puedes trabajar.        exit 0
```

Suite de la raíz relanzada aparte: **102 passed**. Guardián de secretos y
portero del inventario: **80 passed**. `git status`: **limpio**.

## 15.4 · Los checkpoints, al cerrar

| | Estado |
|---|---|
| **C1** — arnés en verde | **[x]** `init.sh` exit 0, ejecutado por mí tres veces a lo largo de esta review |
| **C2** — estado coherente | **[x]** Una sola feature en curso, ninguna bloqueada, `current.md` y `features.json` al día |
| **C3** — arquitectura y convenciones | **[x]** Revalidado, incluida la documentación que ahora sí dice la verdad |
| **C3 bis** — documentos de fuera | **[x] N/A justificado**: F-008 no toca `docs/referencia/` |
| **C4** — verificación real | **[x]** Resuelto en la segunda pasada: lo verificado consta con su salida, lo no verificado consta **como no verificado** |
| **C4 bis** — rigor `critico` | **[x]** Fase RED con trazas reales, cobertura N/A con motivo impreso, mutación recalculada por mí (108 líneas, 5 mutantes, cero supervivientes), «Evidencias» completa |
| **C4 ter** — rutas sensibles | **[x] N/A justificado**: no existe `harness/rutas_sensibles.json` |
| **C5** — sesión cerrada | **[x]** `tasks.md` sin marcas que afirmen de más, árbol limpio, `features.json` real |

**Ningún checkbox vacío. Ningún N/A sin justificar.**

## 15.5 · Una observación que NO bloquea

La cabecera declara «Commit de origen: `df8866f`», y el documento cambió
después, en `ab86416`. Está, por tanto, un commit por detrás.

**No lo cuento como defecto y no quiero que se "arregle" a la carrera**,
porque es un límite lógico, no un descuido: **un fichero no puede contener el
hash del commit que lo introduce**. Cualquier documento que se autoestampe
está siempre uno por detrás por construcción. Lo que ese sello tiene que
garantizar —y garantiza— es que se pueda saber de qué versión salió la copia
de `azure-apps`. Lo natural es **restamparlo la próxima vez que se refresque
la copia**, no ahora.

Lo dejo escrito para que nadie lo lea dentro de seis meses como un cabo suelto
que se nos pasó.

## 15.6 · Qué queda vivo, con dueño

| Cabo | Dueño |
|---|---|
| Function key de solo lectura para la api (**D5**) | **F-016**, `pending` |
| Fila de prueba en Sigrid, avisos a Administración, Regla B sin ejercitar | **F-014**, `pending` |
| Tarjeta y usuarios del Portal | **F-015**, `done` |
| **R34** (`/health` del transfer en caliente) | **Sin dueño, y es correcto**: consta como no verificado en `impl_F-008.md` y en `tasks.md`, con el motivo —ingress interno, que es lo que D2 buscaba—. No es deuda oculta: es una limitación declarada del diseño |
| **T29** sin volcado | **Sin dueño, y es correcto**: consta como confirmación del humano, no como traza |

Nada se cierra en falso y nada se cae por una rendija.

---

## 15.7 · Nota final sobre las tres pasadas

Las tres bajadas de esta review encontraron cosas distintas, y merece la pena
dejar dicho por qué, porque no fue casualidad:

1. **La primera** no encontró nada mirando el sistema desplegado —estaba
   bien— y lo encontró todo **contrastando el rastro contra la realidad**: no
   fiándose de `tasks.md`, sino comprobando las mismas cosas con `az` y
   preguntándose de dónde salía cada `[x]`.
2. **La segunda** no encontró nada en los cinco remates, que estaban bien, y
   encontró el bloqueo **en una condición que la primera había dejado escrita
   como riesgo futuro** y que entretanto se había cumplido. Ese aviso, escrito
   y fechado, es lo que hizo que se pudiera reclamar.
3. **La tercera** no encontró nada, y eso también es un resultado.

Y en las tres, lo que más aguantó fue lo que se puso a prueba en vez de
leerse: el guardián de secretos (que acabó cazándome a mí), el portero del
digest (roto a propósito y restaurado), el comentario falso de PowerShell
(reproducido hasta desmontarlo) y los totales de mutación (recalculados,
mutante a mutante). Leer un informe verde y verificarlo son dos actividades
distintas, y solo una de ellas es una review.

**F-008 · Infraestructura y despliegue en Azure: APROBADA.**
