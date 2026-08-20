<!-- progress/impl_F-008.md -->
# F-008 · Infraestructura y despliegue en Azure — implementación (fases 1-6 y 8)

**Fecha:** 2026-08-20 · **Rama:** `feature/F-008-infra-azure` ·
**Autor:** subagente `implementer` · **Rigor:** `critico`.

**Alcance ejecutado: T1–T23 (fases 1 a 6) y T32–T33 (cierre).**
**La fase 7 (T24–T31) NO se ha ejecutado**: crea recursos en Azure, gasta
dinero y toca la suscripción. Los scripts están escritos y revisables; los
comandos exactos para el humano están en la §7 de este informe.

**No se ha ejecutado ni un `az`, ni un `docker`, ni un `psql` contra ningún
servidor.** Ni una escritura en Sigrid. Ni un `git push`.

---

## 1 · Resumen en una página

| | |
|---|---|
| Commits | 21, uno por tarea (con una excepción justificada en §8) |
| Ficheros nuevos | 20 |
| Ficheros modificados | 7 |
| Tests nuevos | **119** (16 + 12 en la api, 11 en el front, 27 + 53 en la raíz) |
| Suite completa | **401 tests en verde** (91 raíz + 112 api + 11 front + 187 transfer) |
| Cobertura de líneas cambiadas | **93,3 %** (28/30), umbral 80 % |
| Mutación | **5 mutantes, 5 muertos, 0 supervivientes** |
| `bash harness/init.sh` | **ENTORNO LISTO** (exit 0) |
| Avisos de `ruff` | 176, los mismos que antes de empezar: F-008 no añade ni uno |

Lo que de verdad cambia en el sistema, más allá de la carpeta `infra/`:

1. **`dedicacion-api` ya no crea bases ni roles al arrancar.** Y con el
   conmutador apagado ni siquiera abre la conexión de administración, así que
   la contraseña del administrador de un servidor compartido por cinco
   proyectos deja de necesitarse y deja de viajar.
2. **El front tiene suite por primera vez**, y lo que fija no es decorativo:
   que la identidad de Easy Auth llega al backend y que el `X-Usuario` que
   llegue de fuera se descarta.
3. **El transfer se puede empaquetar.** Era el único sin `Dockerfile`.
4. **Hay un guardián permanente de secretos** sobre `infra/`, `specs/`,
   `docs/` y `progress/`, y ya ha cazado algo real (§4.2 y §10).

---

## 2 · Qué se creó y qué se modificó

### 2.1 Código de producción (lo único que la mutación puede medir)

| Fichero | Qué cambia |
|---|---|
| `services/dedicacion-api/config/settings.py` | `+ auto_create_database: bool = False` (R14) |
| `services/dedicacion-api/infrastructure/db/database.py` | cortocircuito de `asegurar_base_datos`, `BaseDatosNoExiste`, `es_base_inexistente`, `comprobar_base_datos` (R13, R15, R16) |
| `services/dedicacion-api/main.py` | llama a `comprobar_base_datos` entre `crear_engine` y `sincronizar_esquema` |

### 2.2 Empaquetado

| Fichero | Qué |
|---|---|
| `services/dedicacion-transfer/Dockerfile` | **nuevo** (R26). `python:3.12-slim`, `EXPOSE 8006`, `CMD ["python", "main.py"]` |
| `services/dedicacion-transfer/.dockerignore` | **nuevo** (R25) |
| `services/dedicacion-{api,front,transfer}/.env.example` | completados, con el porqué de cada valor de Azure |

### 2.3 Tests

| Fichero | Requisitos | Tests |
|---|---|---|
| `services/dedicacion-api/tests/test_f008_bootstrap_bbdd.py` | R13-R16 | 16 |
| `services/dedicacion-api/tests/test_f008_despliegue.py` | R8 | 12 |
| `services/dedicacion-front/tests/{__init__,conftest}.py` | — | (la suite no existía) |
| `services/dedicacion-front/tests/test_f008_identidad.py` | R11, R12 | 11 |
| `tests/test_f008_imagenes.py` | R23-R26 | 27 |
| `tests/test_f008_infra_sin_secretos.py` | R21, R22 | 53 (39 + 14 de la ampliación §10) |

### 2.4 `infra/` (nueva)

`README_dedicacion.md`, `.gitignore`, `imagenes.json`,
`00_vars_dedicacion.ps1`, `00_capps_vars_dedicacion.ps1`,
`fase1_infra_dedicacion.ps1`, `crear_base_dedicacion.ps1`,
`add_secrets_dedicacion.ps1`, `build_images_dedicacion.ps1`,
`create_transfer_dedicacion.ps1`, `create_api_dedicacion.ps1`,
`create_front_dedicacion.ps1`, `setup_front_easyauth.ps1`,
`redeploy_dedicacion.ps1`.

Los once `.ps1` están en **UTF-8 con BOM** y su `eol=crlf` lo garantiza
`.gitattributes`. **Los once parsean sin errores** con el analizador de
PowerShell (`[System.Management.Automation.Language.Parser]::ParseFile`), que
comprueba la sintaxis **sin ejecutar nada**. Es lo máximo que un agente puede
verificar de un script cuyo efecto es crear recursos en Azure; el resto es
revisión y ejecución manual, y así lo dice `design.md` §8.2.

### 2.5 Documentación

| Fichero | Qué |
|---|---|
| `docs/INTEGRACION.md` | **nuevo**: fuente de verdad de qué exponemos y consumimos (R29, R31, R35) |
| `docs/ARCHITECTURE.md` | §«Qué hace este proyecto», §«Acceso a datos» y §«Infra y despliegue» reescritas (R32). **La sección de semántica de dominio no se toca**: desplegar no cambia una regla |
| `azure-apps/dedicacion.md` | **nuevo, en OTRO repositorio**: copia con la cabecera obligatoria de origen y fecha (R30) |
| `azure-apps/README.md` | fila nueva en la tabla de documentos |

---

## 3 · Fase RED (obligatoria, nivel `critico`)

### 3.1 T1 · El bootstrap de la base de datos

Los tests se escribieron **antes** que el código, contra un API que no
existía. Comando y salida reales:

```
$ cd services/dedicacion-api && .venv/Scripts/python -m pytest tests/test_f008_bootstrap_bbdd.py -q

=================================== ERRORS ====================================
_____________ ERROR collecting tests/test_f008_bootstrap_bbdd.py ______________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\porcentajes\services\dedicacion-api\tests\test_f008_bootstrap_bbdd.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f008_bootstrap_bbdd.py:39: in <module>
    from infrastructure.db.database import (
E   ImportError: cannot import name 'BaseDatosNoExiste' from 'infrastructure.db.database' (C:\Users\pgris\PycharmProjects\porcentajes\services\dedicacion-api\infrastructure\db\database.py)
=========================== short test summary info ===========================
ERROR tests/test_f008_bootstrap_bbdd.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 3.53s
```

Tras T2, T3 y T4, los 16 tests del fichero pasan (§5).

### 3.2 T10 · El guardián de secretos, y lo que destapó

El entregable de T10 **es el propio test**, así que su fase RED consiste en
romperlo a propósito. Se creó un fichero temporal `infra/_prueba_red_f008.ps1`
con **un GUID y una contraseña inventados** (no existían, no apuntaban a
nada):

```powershell
$Global:SUBSCRIPTION = "<GUID-INVENTADO>"
$Global:PG_PASSWORD  = "<CONTRASENA-INVENTADA>"
```

> Los dos valores iban aquí literales hasta que el guardián empezó a barrer
> también `progress/` (§10): **se acusó a sí mismo, y con razón**. Aunque
> fueran inventados, tenían exactamente la forma de un secreto, y un guardián
> que distinga «inventado» de «real» no existe. Sustituidos por marcadores,
> que es la salida que este informe recomienda para el mismo caso.

**Primera ejecución — el guardián solo cazó la mitad:**

```
E       AssertionError: Posibles secretos en el repositorio:
E         infra/_prueba_red_f008.ps1:4 [guid]
E       assert ['infra/_prue...ps1:4 [guid]'] == []
1 failed, 33 deselected in 0.11s
```

**La línea 5 no saltó, y eso es un agujero real.** El patrón de credenciales
excluía todo valor que empezara por comilla —lo hacía para no acusar a
`"PG_PASSWORD=secretref:pg-password"`, que es una referencia legítima— y con
ello se le colaba `PG_PASSWORD = "<un valor entre comillas>"`, que es **la
forma más habitual de escribir una contraseña en un `.ps1`**. Un guardián así
habría dado verde para siempre sobre el caso que más importa.

Corregido consumiendo la comilla de apertura **antes** de aplicar la
exclusión. Segunda ejecución, con el patrón arreglado:

```
E       AssertionError: Posibles secretos en el repositorio:
E         infra/_prueba_red_f008.ps1:4 [guid]
E         infra/_prueba_red_f008.ps1:5 [credencial]
E       assert ['infra/_prue...[credencial]'] == []
E         Left contains 2 more items, first extra item: 'infra/_prueba_red_f008.ps1:4 [guid]'
1 failed, 32 passed, 3 deselected in 0.11s
```

El fichero temporal se borró acto seguido; `git status` quedó limpio y el
caso está fijado como control positivo permanente del test.

**Este es el argumento de por qué la fase RED no es papeleo.** Sin ella, el
guardián se habría commiteado en verde y roto.

### 3.3 Segundo hallazgo del guardián, ya en marcha

Al escribir `crear_base_dedicacion.ps1`, el barrido señaló dos líneas:

```
infra/crear_base_dedicacion.ps1:104 [credencial]
infra/crear_base_dedicacion.ps1:110 [credencial]
```

Eran **falsos positivos**: `$PGADMIN_PWD = [System.Net.NetworkCredential]...`,
es decir, justo la línea que **evita** escribir la contraseña en el script
(la lee de un `SecureString` pedido por consola). Se afinó el patrón para
excluir los valores que empiezan por `[` —aceleradores de tipo .NET, nunca
literales— y se añadieron las dos líneas como controles negativos, para que
el motivo quede escrito y nadie lo vuelva a «arreglar» al revés.

No se relajó ninguna otra familia de patrones, y ningún valor salió de ningún
fichero: no había ninguno.

---

## 4 · Evidencias

Números **medidos**, no estimados.

### 4.1 Tests ejecutados

Salida real de `bash harness/init.sh` (una línea por suite):

| Suite | Resultado |
|---|---|
| raíz (`tests/`) | `77 passed in 1.24s` |
| `services/dedicacion-api` | `112 passed in 1.37s` |
| `services/dedicacion-front` | `11 passed, 19 warnings in 1.29s` |
| `services/dedicacion-transfer` | `187 passed, 1 warning in 0.91s` |
| **Total** | **387 tests, 0 fallos** |

Los avisos son **previos a F-008**: `on_event is deprecated` de FastAPI en el
front y un `PytestReturnNotNoneWarning` en un test del transfer. Ninguno lo
introduce esta feature y ninguno entra en su alcance.

**Tiempo de ejecución de la suite: 4,81 s en total** (1,24 + 1,37 + 1,29 +
0,91), medido por las propias suites.

### 4.2 Cobertura de las líneas cambiadas

Línea literal de `PUERTA COBERTURA` de `bash harness/init.sh`:

```
[OK] PUERTA COBERTURA: 93.3% de 30 líneas cambiadas cubiertas (28/30, umbral 80%, nivel critico)
```

Desglose, medido sobre `services/dedicacion-api/coverage.json`:

| Fichero | Líneas medibles | Cubiertas |
|---|---|---|
| `config/settings.py` | 1 | 1 |
| `infrastructure/db/database.py` | 27 | 27 |
| `main.py` | 2 | **0** |

**Las dos sin cubrir son de `main.py`**, y son el `import` de
`comprobar_base_datos` y su llamada. `main.py` no lo importa ninguna suite:
su función es arrancar `uvicorn`, y ejecutarlo en un test levantaría un
servidor y abriría una conexión a PostgreSQL, que es justo lo que
`docs/CONVENTIONS.md` prohíbe.

No se deja como hueco: hay un test que lo cubre **por otra vía**,
`test_f008_r16_el_arranque_comprueba_la_base_antes_de_sincronizar`, que lee el
fuente de `main.py` y comprueba que la llamada existe **y está entre
`crear_engine` y `sincronizar_esquema`**. El orden importa: después del DDL no
serviría de nada, porque el esquema reventaría antes con el error crudo del
driver. Es el mismo recurso que ya usaba `test_f003_esquema.py` en este
servicio.

### 4.3 Mutación

`python -m harness.mutacion --feature F-008` → `progress/mutacion_F-008.md`.

| Métrica | Valor |
|---|---|
| Alcance | 3 ficheros, 108 líneas de producción |
| Mutantes generados | **5** |
| Muertos | **5** |
| **Supervivientes** | **0** |
| Timeouts | 0 |
| Tiempo | 4,6 s |
| Muestreo | no: campaña completa |

Los cinco, y quién los mata:

| Mutante | Lo caza |
|---|---|
| `auto_create_database: bool = False` → `True` | `test_f008_r14_auto_create_database_por_defecto_es_false` |
| `if not settings.auto_create_database:` → `if settings...` | `test_f008_r15_apagado_no_abre_la_conexion_de_administracion` |
| `return True` → `False` (rama `InvalidCatalogName`) | `test_f008_r16_reconoce_el_error_del_driver_por_tipo` |
| `return True` → `False` (rama del texto) | `test_f008_r16_reconoce_el_error_por_el_texto_del_driver` |
| `return False` → `True` (salida del bucle) | `test_f008_r16_no_confunde_la_base_de_otro_proyecto` |

**Ningún superviviente que justificar.** La campaña paralela (16 worktrees)
funcionó a la primera: la avería que la tumbaba se cerró en F-009, al dejar
de versionar los artefactos de cobertura. No hizo falta `--workers 1`.

Que solo salgan 5 mutantes de 108 líneas no es un fallo de la herramienta: el
mutador toca comparaciones, aritmética, booleanos, `not` y enteros, y el grueso
del diff son docstrings, imports y llamadas. Lo mutable es exactamente donde
está la decisión peligrosa, y está todo cazado.

### 4.4 Lo que no tiene test, y qué se hizo en su lugar

Once ficheros `.ps1` y cuatro documentos. No se han inventado tests de adorno.

| Qué | Verificación aplicada |
|---|---|
| Los once `.ps1` | **Parseo sin ejecución** con el analizador de PowerShell: los once OK. Más revisión del reviewer contra los criterios escritos de R4, R7, R9, R10, R12, R17, R18, R20, R23, R27 |
| `infra/` y los documentos | **Barrido automático de secretos** (39 tests), que sí es permanente |
| `azure-apps/dedicacion.md` y `azure-apps/README.md` | Barridos **a mano con la misma función `hallazgos()`** del guardián, porque viven en otro repositorio y la suite no los alcanza: **los dos, LIMPIOS** |
| Que los recursos existan y estén bien configurados | **MANUAL (humano)**, §7 |

---

## 5 · Decisiones que tuve que tomar

Ninguna contradice la spec; todas rellenan huecos que la spec dejaba abiertos.

1. **`infra/crear_base_dedicacion.ps1` no actúa sin `-Confirmar`.** Por
   defecto imprime el plan y no toca nada. Es el único script de todo el
   despliegue que escribe en un servidor de **producción compartido por cinco
   proyectos**; ver el plan antes cuesta diez segundos. **Consecuencia para el
   humano**: el comando de T24 de `tasks.md` necesita el conmutador; está en
   la §7.

2. **Los permisos del rol de aplicación se conceden con `GRANT` dentro de
   nuestra base**, no haciéndolo `OWNER` de la base. Hacerlo owner exigía que
   el administrador fuese miembro del rol, que es un enredo de privilegios en
   un servidor ajeno. Los `GRANT` emitidos están acotados a la base
   `dedicacion` y al esquema `public` **de esa base**; ninguno sale de ahí, y
   R18 sigue cumpliéndose al pie de la letra.

3. **El rol se crea `NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION
   NOBYPASSRLS`**, explícito aunque sean los defectos. Es lo que va dentro del
   contenedor y por tanto lo único que podría filtrarse: que se lea en el
   script vale más que ahorrar una línea. Y el script **aborta** si se le da
   al rol la contraseña del administrador, que es exactamente el error que
   `partes` cometió al desplegar con `PG_USER=<admin>`.

4. **Los FQDN se componen desde el nombre del recurso** (`"$PG.postgres...`),
   no se escriben literales. El nombre es público dentro de la casa y R2
   obliga a declararlo; un FQDN escrito a mano ya es media cadena de conexión.
   Es el mismo patrón de `00_capps_vars_partes.ps1`.

5. **El guardián no persigue nombres de host.** R21 pide GUID, `AccountKey=`,
   credenciales con valor, IP privada y clave larga en base64: eso es lo que
   busca, más cadenas de conexión con usuario y contraseña. Perseguir además
   los FQDN habría chocado con la composición del punto anterior y con R2. La
   decisión está escrita en el docstring del test.

6. **`infra/imagenes.json` arranca con `tag: null` en los tres servicios**, no
   con un tag de ejemplo. Nunca se ha publicado nada y eso es lo honesto; el
   test acepta `null` como estado legítimo, pero exige que si hay tag haya
   fecha, y viceversa.

7. **`$SUFFIX` del Key Vault vale `dd7k2`.** Es un valor de arranque; su
   espacio de nombres es mundial y puede estar pillado. `fase1` es idempotente
   y el script dice qué hacer si falla.

8. **El GUID todo ceros está en la lista de admitidos del guardián.** Es el
   `appRoleId` de «acceso por defecto» de Entra, una constante documentada de
   la plataforma igual para todo el mundo, no un identificador nuestro.
   `setup_front_easyauth.ps1` lo necesita.

---

## 6 · Desviaciones respecto a `tasks.md`

Cuatro, todas menores, ninguna silenciosa.

1. **T3 y T4 van en un solo commit.** Los dos tocan regiones solapadas de
   `database.py` (el cortocircuito y el error tipado quedan a pocas líneas), y
   separarlos exigía inventar un estado intermedio que no aporta nada al
   historial. El mensaje del commit lo dice.

2. **La verificación de T2 y T3 no pudo ser `pytest -k r14`.** El fichero de
   T1 importa `BaseDatosNoExiste` a nivel de módulo, así que hasta T4 la
   colección entera falla y `-k` no selecciona nada. Es coherente con lo que
   la propia T1 predice («falla con `AttributeError` / `ImportError`»), pero
   hace imposible el verde parcial. R14 se verificó ejecutando el `Settings`
   directamente:

   ```
   auto_create_database por defecto: False
   con AUTO_CREATE_DATABASE=true: True
   ```

3. **`infra/imagenes.json` se crea en T8, no en T12.** El test de T8 lo
   necesita para que su verificación pueda darse en verde tal como la pide
   `tasks.md`. T12 aporta el script que lo escribe.

4. **T14 (el README de `infra/`) se escribió al final de la fase 5, no en la
   fase 4.** Un manual que describe scripts que todavía no existen no se puede
   revisar.

**T23 no tiene commit en este repositorio**: sus dos ficheros viven en
`azure-apps`, que es otro repositorio y donde **el commit lo hace el humano**.

---

## 7 · Lo que queda: fase 7, MANUAL (humano)

**Ningún agente ejecuta nada de esto.** Antes de empezar hay que resolver dos
cosas:

> ### ⚠ Precondición 1 — la fila de prueba viva en Sigrid
> `hmores.ide = 403039`, parte `PT26/00296`, obra `0404`, marca
> `PRUEBA-PORC` (`progress/current.md`). El humano quería **verla en la
> pantalla de partes del ERP antes de borrarla**. Probar desde el entorno
> desplegado escribirá **más** líneas `PRUEBA-PORC` en la misma obra y el
> mismo mes, y ya no se distinguirán de esa. **Cierra esa comprobación
> primero.**

> ### ⚠ Precondición 2 — la copia local con los valores reales
> Los ficheros versionados llevan `REDACTADO-VER-COPIA-LOCAL`. Sin la copia
> local, `fase1` aborta con un mensaje explícito.
>
> ```powershell
> # infra\00_vars_dedicacion.local.ps1   (lo ignora infra/.gitignore)
> $Global:SUBSCRIPTION = "<el id real>"
> $Global:TENANT       = "<el id real>"
> ```

### T24 · Provisión base

```powershell
cd C:\Users\pgris\PycharmProjects\porcentajes\infra
. .\00_vars_dedicacion.ps1 ; . .\00_vars_dedicacion.local.ps1
.\fase1_infra_dedicacion.ps1
.\crear_base_dedicacion.ps1              # imprime el PLAN y NO toca nada
.\crear_base_dedicacion.ps1 -Confirmar   # lo ejecuta (pide las dos contrasenas)
.\add_secrets_dedicacion.ps1
```

El `-Confirmar` es la decisión 1 de la §5. `crear_base` pide la contraseña del
administrador del servidor **y** una nueva para el rol de aplicación; la
segunda es la que hay que guardar como `PG-PASSWORD` en el paso siguiente.

*Comprobación:* `az resource list -g rg-dedicacion-dev -o table` lista RG,
managed identity, Log Analytics, Key Vault y el entorno de Container Apps, **y
ninguna Storage Account**.

### T25 · Imágenes y alta de los tres servicios, en orden

```powershell
. .\00_capps_vars_dedicacion.ps1
.\build_images_dedicacion.ps1
.\create_transfer_dedicacion.ps1
.\create_api_dedicacion.ps1
.\create_front_dedicacion.ps1
```

*Comprobación:*
`az acr repository show-tags -n acralbaranesdev --repository dedicacion-api -o table`
muestra el tag fechado, y `git diff infra/imagenes.json` recoge los tres tags
publicados. **Ese fichero hay que commitearlo**: es lo que responde «qué
código está corriendo» sin abrir Azure.

> Al terminar `create_front_dedicacion.ps1`, **el front está abierto a
> Internet sin login** y su proxy llega hasta la api. El paso siguiente es
> inmediato.

### T26 · Easy Auth

```powershell
.\setup_front_easyauth.ps1
.\setup_front_easyauth.ps1 -Miembros "persona@ruesma.es","otra@ruesma.es"
```

Aquí se cierra la **decisión D3** (quién entra en el grupo). El script te añade
siempre a ti; el resto van por `-Miembros`, y la lista **no se escribe en el
repositorio**.

Si la asignación del grupo falla por falta de licencia Entra ID P1, el script
lo dice **en rojo**: mientras tanto, Easy Auth deja pasar a cualquiera del
tenant.

*Comprobación:* ventana de incógnito. `https://<fqdn-front>` pide login, y un
usuario **fuera** del grupo no entra (R36).

### T27 · Exposición y modo pruebas — la verificación que importa

```powershell
az containerapp list -g rg-dedicacion-dev `
  --query "[].{app:name, externo:properties.configuration.ingress.external}" -o table
az containerapp show -n ca-dedicacion-transfer -g rg-dedicacion-dev `
  --query "properties.template.containers[0].env[?name=='OBRA_PRUEBAS_FORZAR'].value" -o tsv
az containerapp show -n ca-dedicacion-transfer -g rg-dedicacion-dev --query "properties.template.scale"
az containerapp show -n ca-dedicacion-api      -g rg-dedicacion-dev --query "properties.template.scale"
az containerapp show -n ca-dedicacion-api -g rg-dedicacion-dev `
  --query "properties.configuration.secrets[].{n:name, kv:keyVaultUrl}" -o table
```

Esperado: `externo` = `true` **solo** en el front; `OBRA_PRUEBAS_FORZAR` =
`true`; `maxReplicas` = 1 en transfer y api; `keyVaultUrl` en **todos** los
secretos.

### T28 · Salud de los tres

- **front**: `https://<fqdn-front>/health` **con sesión iniciada**. Anónimo
  redirige al login: **es lo esperado**, no una caída.
- **api**: `https://<fqdn-front>/api/v1/health` en el navegador. Debe dar
  `ok: true` y `sigrid_configurado: true`. (Ojo: la salud de la api está en
  `/api/v1/health`, no en `/health`.)
- **transfer**: es interno.
  `az containerapp logs show -n ca-dedicacion-transfer -g rg-dedicacion-dev --tail 60`.

### T29 · Prueba funcional, **sin escribir en Sigrid**

Entrar al front, sincronizar maestros, crear un periodo, cargar un cuadrante
y ejecutar **solo `registro/preflight`**. **No ejecutar `registro/ejecutar`**
hasta que el humano lo decida expresamente.

### T30 · Petición al Portal Ruesma y a `sigrid-api`

Pasar a `front-portal` la URL del front, el nombre y el Object ID del grupo,
la categoría («Obra») y el icono. **El GUID no entra en este repositorio**;
sácalo con:

```powershell
az ad group show --group "dedicacion-portal-users" --query id -o tsv
```

Y aprovechar para cerrar la **decisión D5**: pedirle al dueño de `sigrid-api`
una function key de **solo lectura** para la api. Hoy la api y el transfer
comparten la misma, y lo único que impide que la api escriba en el ERP es que
su código no tiene rutas de escritura, **no la credencial**.

### T31 · Refrescar la documentación con el estado real

`docs/INTEGRACION.md` y `azure-apps/dedicacion.md` dicen hoy, en su cabecera,
«en Azure no hay nada creado todavía». Tras el despliegue hay que actualizar
esa frase, la fecha, el commit de origen y el FQDN del front.

### Y el commit en `azure-apps`, que es MANUAL

```powershell
cd C:\Users\pgris\PycharmProjects\azure-apps
git add dedicacion.md README.md
git commit -m "dedicacion: documento de integracion (F-008)"
```

> **Aviso.** Ese repositorio tenía **trabajo ajeno sin commitear** de otra
> sesión cuando escribí en él: `postventa_incidencias.md` sin seguir y
> `README.md` modificado (la fila de postventa). **No lo he tocado**: mi
> cambio en `README.md` es una fila añadida encima del suyo. Revisa el `git
> diff` antes de commitear, porque el commit arrastraría también lo de la
> otra sesión si lo haces con `git add -A`.

---

## 8 · Verificación final

```
$ bash harness/init.sh

[OK] Arnés v1.5.2 (2026-08-18)
[OK] features.json válido
[OK] BACKLOG.md al día
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 176 avisos (deuda previa, no bloquea)
[OK] pytest en verde (con medición de cobertura)          77 passed
[OK] servicio api (services/dedicacion-api): pytest en verde
[OK] servicio front (services/dedicacion-front): pytest en verde
[OK] servicio transfer (services/dedicacion-transfer): pytest en verde
[OK] PUERTA COBERTURA: 93.3% de 30 líneas cambiadas cubiertas (28/30, umbral 80%, nivel critico)
[OK] Ningún .env versionado
[OK] config.yaml de dedicacion-api: válido
[OK] Los tres servicios tienen .env.example
[OK] Rama actual: feature/F-008-infra-azure
----------------------------------------
ENTORNO LISTO. Puedes trabajar.
```

**La línea `servicio front` en verde es nueva**: hasta esta feature el portero
avisaba en cada ejecución de que nadie estaba comprobando los tests del front.

`ruff` estaba en 176 avisos antes de empezar y sigue en 176: el único que
introdujo F-008 (`PYI034` en un doble de prueba) se corrigió en el momento.

---

## 9 · Lo que este informe NO puede decir

Con honestidad, y para que el reviewer no lo dé por hecho:

- **Que el despliegue funcione.** No se ha ejecutado. Lo que está verificado
  es que los scripts parsean, que no llevan secretos, que dicen lo que la spec
  exige y que el código que cambian está cubierto y probado.
- **Que las imágenes construyan.** `az acr build` no se ha llamado. Lo
  comprobado es que los tres servicios tienen `Dockerfile` y `.dockerignore`,
  que los tres excluyen `.env`, que el `EXPOSE` casa con el puerto que usa
  cada script y que arrancan por `python main.py` y no por `uvicorn` a pelo.
- **Que Easy Auth deje pasar a los del grupo y no a los demás.** Requiere
  Entra y dos usuarios: es T26, y es de una persona.
- **Que el transfer siga en modo pruebas una vez desplegado.** El script lo
  fija a `true` y exige dos señales para cambiarlo; comprobarlo sobre el
  recurso vivo es T27.

---

## 10 · Ampliación posterior a la review: el guardián barre `progress/` (§7.2 y §7.3)

**Fecha:** 2026-08-20, tras el APROBADO de las fases 1-6
(`progress/review_F-008.md`). Se atiende **solo** lo que pedía el coordinador;
el resto del trabajo aprobado no se toca.

### 10.1 Qué cambió

| Cambio | Recomendación |
|---|---|
| `DIRECTORIOS` pasa de `("infra", "specs", "docs")` a incluir **`"progress"`** | §7.2 |
| El patrón de credenciales admite el sufijo `_value` / `-value` / `Value` | §7.3.1 |
| El patrón admite el separador **`:`** además de `=` | §7.3.2 |

El motivo de §7.2, con nombre y apellidos: **la fase 7 manda pegar en este
mismo fichero la salida real de `az resource list`, `az containerapp show` y
`az ad group show`**, que escupe identificadores de suscripción y objectId de
grupo. El directorio con más probabilidad de recibir esa clase de texto era
justo el único de los cuatro versionados que nadie vigilaba.

Sobre el separador `:` hay una asimetría deliberada: con `:` se admite la
comilla de **cierre** del nombre (una clave JSON siempre va entrecomillada),
y con `=` no. Sin esa distinción, una tabla de descripciones de PowerShell
—`"PG-PASSWORD" = "contrasena del rol de aplicacion..."`, que es prosa, no un
valor— empezaría a saltar. Las dos formas están fijadas como controles.

**Las otras dos rendijas de §7.3 —here-strings de PowerShell y valores con
espacios— NO se han tocado**, por indicación expresa: exigen barrer por
bloques en vez de línea a línea y el reviewer concluye que no compensan.
Siguen escritas en §3.4 de la review.

### 10.2 Sí, disparó con los informes existentes

Al añadir `progress/` (8.521 líneas en 24 informes), el barrido señaló
**cuatro líneas**, y después de cerrar las dos rendijas, **dos más**:

| Fichero | Qué era |
|---|---|
| `impl_F-008.md:139-140` | el GUID y la contraseña **inventados** de la fase RED de T10, pegados literales |
| `impl_F-008.md:155` y `review_F-008.md:149` | `PG_PASSWORD = "…"` citado en prosa al explicar el agujero que destapó esa fase RED |
| `review_F-008.md:246-247` | la tabla de la review que **documentaba estas dos rendijas**, con sus valores de ejemplo |

Ninguno era un secreto real. Pero **todos tenían exactamente la forma de
uno**, y un guardián capaz de distinguir «inventado» de «real» no existe: esa
es precisamente la razón por la que sirve.

**Resuelto con marcadores en el texto, sin relajar ni un patrón**
(`<GUID-INVENTADO>`, `<CONTRASENA-INVENTADA>`, `<valor>`). Encajan solos,
porque el carácter `<` ya estaba en la lista de exclusiones del patrón desde
el principio: los marcadores eran ya la salida prevista. Cada sitio editado
dice por qué se editó.

Las dos filas de la tabla de la review quedan marcadas **CERRADO**, porque
después de este cambio ya no describen la realidad. Las otras cuatro siguen
abiertas, tal cual.

> Merece la pena dejarlo dicho: el guardián **se acusó a sí mismo dos veces**
> —una en su propia fase RED, otra al ampliarse— y las dos veces tenía razón.

### 10.3 Comprobación de que la ampliación sirve de algo

Un guardián que solo se ve pasar no demuestra nada. Se creó un fichero
temporal en `progress/` con la salida de `az` **con la forma exacta que va a
tener en la fase 7** (valores inventados):

```
progress/_prueba_red_progress.md:8  [guid]         "subscriptionId": "…"
progress/_prueba_red_progress.md:9  [credencial]   "clientSecret": "…"
progress/_prueba_red_progress.md:10 [credencial]   "secret_value": "…"
```

Las tres cazadas, nombrando fichero y línea: el identificador de suscripción
por el patrón de GUID, y las otras dos **por las dos rendijas recién
cerradas** —el separador `:` y el sufijo `_value`—, que antes de este cambio
se habrían colado. Fichero borrado; `git status` limpio.

### 10.4 Estado

El guardián pasa de **39 a 53 tests**: seis controles positivos nuevos (las
dos rendijas, en sus tres variantes cada una) y ocho negativos nuevos (las
tablas de descripciones de PowerShell, los marcadores y las referencias
`secretref:` / `keyvaultref:` / `kv:keyVaultUrl`, que llevan `:` y **no** son
valores).

```
$ bash harness/init.sh

[OK] pytest en verde (con medición de cobertura)          91 passed
[OK] servicio api (services/dedicacion-api): pytest en verde
[OK] servicio front (services/dedicacion-front): pytest en verde
[OK] servicio transfer (services/dedicacion-transfer): pytest en verde
[OK] PUERTA COBERTURA: 93.3% de 30 líneas cambiadas cubiertas (28/30, umbral 80%, nivel critico)
[OK] Ningún .env versionado
[OK] Rama actual: feature/F-008-infra-azure
----------------------------------------
ENTORNO LISTO. Puedes trabajar.
```

La cobertura y la mutación no se mueven: este cambio es solo de tests y de
texto, y `harness/alcance.py` no considera producción ni `tests/` ni
`progress/`. **La campaña de mutación sigue siendo válida** (5 mutantes, 5
muertos, 0 supervivientes): no se ha tocado una sola línea de código de
producción.

### 10.5 Para el líder

La recomendación §7.2 dice que esto **vale también para `arnes-base`**, por la
regla de propagación de `CLAUDE.md`: si el arnés genérico incorpora un
guardián de secretos, que nazca ya con `progress/` dentro, porque `progress/`
es justo donde el arnés manda pegar salidas reales. **No lo he hecho**: está
fuera de este encargo y `arnes-base` es otro repositorio.
