<!-- specs/F-008-infra-azure/tasks.md -->
# F-008 · Tareas

Rama: `feature/F-008-infra-azure`. Un commit por tarea:
`F-008 Tn: descripción`.

> **Rigor `critico`.** T1 es la fase RED y va **antes** que el código: la
> traza real del fallo se pega en `progress/impl_F-008.md`. Las tareas de
> código llevan cobertura ≥ 80 % de las líneas cambiadas y campaña de
> mutación con **cero supervivientes** (`CHECKPOINTS.md` C4 bis).
>
> **Ningún agente ejecuta `az`, ni `docker`, ni `psql` contra un servidor
> remoto, ni despliega nada.** Todo lo marcado **MANUAL (humano)** lo hace
> una persona; el agente deja el comando exacto escrito y espera.
>
> **Prohibido tocar** `harness/features.json` y `progress/current.md` durante
> las tareas: los lleva el líder. El informe del implementer va a
> `progress/impl_F-008.md`.
>
> **Orden deliberado:** las fases 1–4 **no dependen de ninguna decisión del
> humano** y pueden hacerse ya. La fase 5 en adelante sí depende: no se
> arranca sin las decisiones D1–D5 cerradas (`progress/spec_F-008.md`).

---

## Fase 1 — RED

- [x] **T1**: Crear `services/dedicacion-api/tests/test_f008_bootstrap_bbdd.py`
  con los tests de R13, R14, R15 y R16 escritos contra un API que todavía no
  existe: `Settings.auto_create_database`, el cortocircuito de
  `asegurar_base_datos` y el error `BaseDatosNoExiste`. Nombres
  `test_f008_rN_*`. Sin red ni BBDD: `psycopg.connect` sustituido por un doble
  que **falla si lo llaman**.
  **Verificación:** `cd services/dedicacion-api && .venv/Scripts/python -m
  pytest tests/test_f008_bootstrap_bbdd.py -q` falla con `AttributeError` /
  `ImportError`. **Pegar la salida real en `progress/impl_F-008.md`.**

---

## Fase 2 — El arranque deja de crear bases y roles

- [x] **T2**: Añadir `auto_create_database: bool = False` a
  `services/dedicacion-api/config/settings.py` (R14). Nada más en ese fichero.
  **Verificación:** `pytest tests/test_f008_bootstrap_bbdd.py -q -k r14` en
  verde; el resto sigue rojo.

- [x] **T3**: Cortocircuitar `asegurar_base_datos` en
  `services/dedicacion-api/infrastructure/db/database.py`: si
  `not settings.auto_create_database`, dejar un registro en el log y
  **retornar sin abrir la conexión** (R13, R15).
  **Verificación:** `pytest tests/test_f008_bootstrap_bbdd.py -q -k "r13 or
  r15"` en verde, con el doble de `psycopg.connect` sin invocar.

- [x] **T4**: Añadir el error tipado `BaseDatosNoExiste` y la traducción del
  fallo de conexión en el arranque (`main.py` + `database.py`): el mensaje
  nombra la base que falta y `infra/crear_base_dedicacion.ps1` (R16).
  **Verificación:** `pytest tests/test_f008_bootstrap_bbdd.py -q` **entero**
  en verde.

- [x] **T5**: Crear `services/dedicacion-api/tests/test_f008_despliegue.py`
  con el test de R8: `obtener_usuario` devuelve tal cual lo que venga en
  `X-Usuario` y no valida nada. El docstring del test dice por qué existe (es
  la razón escrita de que la api no pueda tener ingress externo).
  **Verificación:** `pytest tests/test_f008_despliegue.py -q` en verde.

- [x] **T6**: Crear la suite del front, que hoy no tiene ninguna
  (`harness/init.sh` lo avisa en cada ejecución): `tests/__init__.py`,
  `tests/conftest.py` y `tests/test_f008_identidad.py` con el test de R11 —
  `X-MS-CLIENT-PRINCIPAL-NAME` se propaga como `X-Usuario` y, sin ella, se usa
  `DEFAULT_USER`. Sin red: el backend se sustituye por un transporte de prueba
  de `httpx`.
  **Verificación:** `cd services/dedicacion-front && .venv/Scripts/python -m
  pytest tests -q` en verde, y `bash harness/init.sh` deja de avisar de que
  el servicio front no tiene tests.

---

## Fase 3 — Empaquetado de los tres servicios

- [x] **T7**: Crear `services/dedicacion-transfer/Dockerfile` y
  `services/dedicacion-transfer/.dockerignore` (R25, R26), calcados de los de
  la api: `python:3.12-slim`, `requirements.txt` primero, `EXPOSE 8006`,
  `CMD ["python", "main.py"]`. El `.dockerignore` excluye `.env`, `logs/`,
  `tests/`, `__pycache__/`, `.venv/`.
  **Verificación:** T8.

- [x] **T8**: Crear `tests/test_f008_imagenes.py` (raíz) con R24, R25 y R26:
  los tres servicios tienen `Dockerfile` y `.dockerignore`, los tres
  `.dockerignore` excluyen `.env`, y `infra/imagenes.json` —cuando exista—
  parsea, cubre los tres servicios y sus tags cumplen `rAAAAMMDD-HHmm`.
  **Verificación:** `.venv/Scripts/python -m pytest tests/test_f008_imagenes.py -q`
  en verde.

- [x] **T9**: Completar los `.env.example` de los tres servicios: en la api
  `AUTO_CREATE_DATABASE=true`, `TRANSFER_BASE_URL` y `TRANSFER_TIMEOUT_S`
  (hoy el código los lee y el ejemplo no los declara); en el front, comentario
  de los valores de Azure (`DEFAULT_USER=desconocido`, `API_TIMEOUT_S=200`);
  en el transfer, `LOG_DIR`. **Ningún valor real, ningún secreto.**
  **Verificación:** `bash harness/init.sh` sigue dando «Los tres servicios
  tienen .env.example», y `git diff` no introduce ni una credencial.

---

## Fase 4 — Esqueleto de `infra/` y guardianes

> El guardián de secretos va **primero**: vigila los scripts desde el commit
> en que nacen, no después.

- [x] **T10**: Crear `tests/test_f008_infra_sin_secretos.py` (raíz) con R21 y
  R22: barrido de `infra/`, `specs/` y `docs/` buscando GUID, `AccountKey=`,
  `password=`/`pwd=` con valor, function keys, IP privada y claves largas en
  base64. Falla nombrando fichero y línea. Excluye deliberadamente los
  marcadores tipo `REDACTADO-VER-COPIA-LOCAL` y `<...>`.
  **Ojo con el propio guardián:** los patrones tienen que exigir un **valor**
  detrás. Estas specs nombran `AccountKey=` y `password=` en prosa al describir
  el barrido, y un regex ingenuo se acusaría a sí mismo. Un test del guardián
  comprueba las dos caras: que una cadena con valor real (inventada, en un
  fichero temporal) **sí** dispara, y que la mención en prosa **no**.
  **Verificación:** en verde sobre el árbol actual. **Fase RED de este test**
  (C4 bis, entregable = el propio test): romperlo a propósito en una **copia
  aislada** (un fichero temporal con un GUID) y pegar la traza en
  `progress/impl_F-008.md`. El árbol real queda limpio (`git status`).

- [x] **T11**: Crear `infra/.gitignore` (ignora `*.local.ps1`),
  `infra/00_vars_dedicacion.ps1` y `infra/00_capps_vars_dedicacion.ps1` según
  `design.md` §7.1: nombres de recurso, `$TAGS` acens, mapa `$IMG`, y
  **marcadores redactados** para suscripción y tenant.
  **Verificación:** `pytest tests/test_f008_infra_sin_secretos.py -q` en
  verde.

- [x] **T12**: Crear `infra/build_images_dedicacion.ps1` (tag fechado
  `rAAAAMMDD-HHmm`, `az acr build`, escribe `infra/imagenes.json`) y el
  `infra/imagenes.json` inicial (R23, R24).
  **Verificación:** `pytest tests/test_f008_imagenes.py -q` en verde ·
  ejecución real: MANUAL (humano), T24.

- [x] **T13**: Crear `infra/redeploy_dedicacion.ps1`: reordena siempre a
  **transfer → api → front** y aborta si el Container App no existe (R27).
  **Verificación:** revisión del reviewer contra R27 · ejecución real: MANUAL
  (humano).

- [x] **T14**: Crear `infra/README_dedicacion.md`: orden de ejecución, qué
  hace cada script, y **qué pasos son MANUAL (humano)** con su comando.
  **Verificación:** revisión.

---

## ⛔ PARADA — decisiones del humano

**Nada de la fase 5 en adelante se ejecuta hasta que estén cerradas las
decisiones D1–D5 de `progress/spec_F-008.md`.** Resumen:

| | Decisión | Bloquea |
|---|---|---|
| **D1** | Dónde vive la BBDD `dedicacion` (servidor compartido / servidor propio) | T15, T18 |
| **D1b** | Esquema `public` o esquema nominado | T15, y el ORM si es nominado |
| **D2** | Confirmar que solo el front se expone (api y transfer internos) | T17, T18, T19 |
| **D3** | Quién entra en el grupo `dedicacion-portal-users` | T20, T27 |
| **D4** | `min-replicas 1` en los tres (coste) frente a escalado a cero (arranque en frío) | T17–T19 |
| **D5** | Si `sigrid-api` puede dar a la api una clave que no escriba | T16 (informativo) |

---

## Fase 5 — Scripts que dependen de las decisiones

- [x] **T15**: Crear `infra/fase1_infra_dedicacion.ps1` (RG, MI, AcrPull sobre
  `acralbaranesdev`, Log Analytics, Key Vault RBAC, CAE) y
  `infra/crear_base_dedicacion.ps1` (base + rol de aplicación + firewall,
  **una sola vez, ejecutado por una persona**), según D1 y D1b. Sin
  `ALTER SYSTEM`, sin `CREATE EXTENSION`, sin `GRANT` de servidor (R18).
  **Verificación:** revisión contra R2, R3, R6, R18, R19, R20 ·
  `pytest tests/test_f008_infra_sin_secretos.py -q` en verde.

- [x] **T16**: Crear `infra/add_secrets_dedicacion.ps1`: pide `PG-PASSWORD`,
  `SIGRID-API-FUNCTION-KEY` y `EASYAUTH-CLIENT-SECRET` con
  `Read-Host -AsSecureString`, sin escribirlos en disco ni imprimirlos (R19,
  R22). Deja escrito en el propio script que **no** se carga la contraseña de
  administrador de PostgreSQL, y por qué.
  **Verificación:** revisión + `pytest tests/test_f008_infra_sin_secretos.py -q`.

- [x] **T17**: Crear `infra/create_transfer_dedicacion.ps1`: ingress
  **interno**, `--allow-insecure`, min 1 / **max 1**, `OBRA_PRUEBAS_FORZAR=true`
  por defecto, doble confirmación para salir de modo pruebas (R4, R7, R9,
  R10), secret `sigrid-key` por `keyvaultref`, `LOG_DIR=/tmp/logs`.
  **Verificación:** revisión contra R4, R7, R9, R10, R19, R20.

- [x] **T18**: Crear `infra/create_api_dedicacion.ps1`: ingress **interno**,
  `--allow-insecure`, min 1 / max 1, `AUTO_CREATE_DATABASE=false`,
  `PG_SSLMODE=require`, `PG_USER` = rol de aplicación (no admin),
  `TRANSFER_TIMEOUT_S=180`, y cableado de `TRANSFER_BASE_URL` leyendo el FQDN
  interno del transfer (R5, R7, R13, R17, R19, R28).
  **Verificación:** revisión contra esos requisitos.

- [x] **T19**: Crear `infra/create_front_dedicacion.ps1`: ingress
  **externo**, `DEFAULT_USER=desconocido`, `API_TIMEOUT_S=200`, cableado de
  `API_BASE_URL` con el FQDN interno de la api (R7, R12, R28). Imprime el FQDN
  público y avisa de que **hasta T20 no hay autenticación**.
  **Verificación:** revisión contra R7, R12, R28.

- [x] **T20**: Crear `infra/setup_front_easyauth.ps1`: grupo
  `dedicacion-portal-users`, App Registration, client secret al Key Vault,
  Enterprise App con asignación requerida, grupo asignado, Easy Auth con
  login obligatorio. **Idempotente** (R36).
  **Verificación:** revisión contra R36 · ejecución real: MANUAL (humano), T26.

---

## Fase 6 — Documentación

- [x] **T21**: Escribir `docs/INTEGRACION.md` con las nueve secciones de
  `design.md` §10 (R29, R31). Sin un solo valor de conexión. Incluye
  explícitamente: por qué la api va interna (para que nadie lo «arregle»), que
  el transfer está en modo pruebas, y que `/health` del front **no** es
  alcanzable anónimamente por Easy Auth (R35).
  **Verificación:** `pytest tests/test_f008_infra_sin_secretos.py -q` en verde
  + revisión.

- [x] **T22**: Actualizar `docs/ARCHITECTURE.md` (R32): §«Qué hace este
  proyecto» y §«Infra y despliegue» dejan de decir que no hay nada desplegado;
  se añaden dónde vive PostgreSQL (D1), la tabla de timeouts de `design.md`
  §2.5 y el recordatorio de que `OBRA_PRUEBAS_FORZAR` sigue a `true`. **No se
  toca** la sección de semántica de dominio.
  **Verificación:** revisión + `bash harness/init.sh` en verde.

- [x] **T23**: Escribir `azure-apps/dedicacion.md` (copia de
  `docs/INTEGRACION.md` con la cabecera obligatoria de origen y fecha) y
  añadir su fila a `azure-apps/README.md` (R30).
  **Verificación:** revisión — el barrido de secretos del reviewer se ejecuta
  **también** sobre ese fichero, que vive en otro repositorio y no lo alcanza
  la suite. **El commit en `azure-apps` es MANUAL (humano)**: es otro
  repositorio.

---

## Fase 7 — MANUAL (humano) · ejecución en Azure

> **Precondición de toda esta fase**: cerrar la comprobación pendiente de
> F-002 en Sigrid (fila `hmores.ide=403039`, parte `PT26/00296`, obra `0404`,
> `progress/current.md`). Probar desde el entorno desplegado escribirá **más**
> líneas `PRUEBA-PORC` en la misma obra y mes, y ya no se distinguirán de la
> que el humano quiere ver en la pantalla del ERP.

> Ninguna de estas tareas la ejecuta un agente. El humano pega el resultado
> real en `progress/impl_F-008.md`.

- [ ] **T24 · MANUAL (humano)**: provisión base.
  ```powershell
  cd C:\Users\pgris\PycharmProjects\porcentajes\infra
  . .\00_vars_dedicacion.ps1
  .\fase1_infra_dedicacion.ps1
  .\crear_base_dedicacion.ps1        # solo si D1 = servidor compartido
  .\add_secrets_dedicacion.ps1
  ```
  **Verificación:** `az resource list -g rg-dedicacion-dev -o table` lista RG,
  MI, Log Analytics, Key Vault y CAE, **y ninguna Storage Account** (R1, R3,
  R6).

- [ ] **T25 · MANUAL (humano)**: imágenes y alta de los tres servicios, en
  orden.
  ```powershell
  . .\00_vars_dedicacion.ps1 ; . .\00_capps_vars_dedicacion.ps1
  .\build_images_dedicacion.ps1
  .\create_transfer_dedicacion.ps1
  .\create_api_dedicacion.ps1
  .\create_front_dedicacion.ps1
  ```
  **Verificación:** `az acr repository show-tags -n acralbaranesdev
  --repository dedicacion-api -o table` muestra el tag fechado (R23), y
  `git diff infra/imagenes.json` recoge los tres tags publicados (R24).

- [ ] **T26 · MANUAL (humano)**: Easy Auth.
  ```powershell
  .\setup_front_easyauth.ps1
  ```
  **Verificación:** en ventana de incógnito, `https://<fqdn-front>` pide login
  Entra; un usuario **fuera** del grupo `dedicacion-portal-users` no entra
  (R36).

- [ ] **T27 · MANUAL (humano)**: comprobación de exposición y modo pruebas —
  **la verificación que de verdad importa**.
  ```powershell
  # Solo el front es externo (R7)
  az containerapp list -g rg-dedicacion-dev `
    --query "[].{app:name, externo:properties.configuration.ingress.external}" -o table
  # El transfer sigue en modo pruebas (R9)
  az containerapp show -n ca-dedicacion-transfer -g rg-dedicacion-dev `
    --query "properties.template.containers[0].env[?name=='OBRA_PRUEBAS_FORZAR'].value" -o tsv
  # Una sola réplica como máximo en transfer y api (R4, R5)
  az containerapp show -n ca-dedicacion-transfer -g rg-dedicacion-dev --query "properties.template.scale"
  az containerapp show -n ca-dedicacion-api -g rg-dedicacion-dev --query "properties.template.scale"
  # Todos los secretos por referencia a Key Vault (R19)
  az containerapp show -n ca-dedicacion-api -g rg-dedicacion-dev `
    --query "properties.configuration.secrets[].{n:name, kv:keyVaultUrl}" -o table
  ```
  **Verificación:** `externo` solo `true` en el front; `OBRA_PRUEBAS_FORZAR`
  devuelve `true`; `maxReplicas` = 1 en transfer y api; todos los secretos con
  `keyVaultUrl`.

- [ ] **T28 · MANUAL (humano)**: salud de los tres servicios (R33, R34, R35).
  - **front**: navegar a `https://<fqdn-front>/health` **con sesión iniciada**
    (anónimo redirige al login: es lo esperado, R35).
  - **api**: `https://<fqdn-front>/api/v1/health` en el navegador; debe
    responder `ok: true` y `sigrid_configurado: true`.
  - **transfer**: es interno.
    `az containerapp logs show -n ca-dedicacion-transfer -g rg-dedicacion-dev --tail 60`
    debe mostrar el arranque limpio; y la vía directa es T27
    (`OBRA_PRUEBAS_FORZAR=true`). Si se quiere ver el `/health` completo
    —`modo_pruebas: true`, `database: "ruesma"` (R34)—, hay que llamarlo desde
    dentro del entorno.

- [ ] **T29 · MANUAL (humano)**: prueba funcional de extremo a extremo, **sin
  escribir en Sigrid**: entrar al front, sincronizar maestros, crear un
  periodo, cargar un cuadrante y ejecutar **solo `registro/preflight`**.
  **Verificación:** el preflight devuelve acciones y conflictos; **no se
  ejecuta `registro/ejecutar`** hasta que el humano lo decida expresamente
  (precondición de la fase 7).

- [~] **T30 · MOVIDA A F-015** por decisión del humano del 2026-08-20, para
  que F-008 pueda cerrarse. Contenido íntegro en la descripción de F-015:
  pasar a `front-portal` la URL y el objectId del grupo para la tarjeta, y
  dar de alta en `dedicacion-portal-users` a quien deba entrar (la decisión
  **D3**, que quedó abierta). El original decía:
  de la tarjeta: URL del front, nombre y Object ID del grupo, categoría
  («Obra») e icono. **El GUID no entra en este repositorio** (R21).
  **Verificación:** petición enviada; la tarjeta la añade ese proyecto.

- [ ] **T31 · MANUAL (humano)**: refrescar `docs/INTEGRACION.md` y
  `azure-apps/dedicacion.md` con el estado real tras el despliegue (FQDN del
  front, fecha, «estado al escribirlo»), y commitear la copia en `azure-apps`.
  **Verificación:** las dos cabeceras llevan fecha y commit de origen.

---

## Fase 8 — Cierre

- [x] **T32**: Ejecutar la campaña de mutación sobre el alcance de la feature
  y dejar `progress/mutacion_F-008.md` con **cero supervivientes** o cada
  superviviente analizado y justificado por escrito (`CHECKPOINTS.md` C4 bis,
  nivel `critico`).
  **Verificación:** `python -m harness.mutacion --feature F-008`.

- [x] **T33**: Ejecutar `bash harness/init.sh` en verde.
  **Verificación:** exit code 0, con las líneas `servicio api`, `servicio
  front` y `servicio transfer` en verde y la puerta de cobertura en `[OK]` (o
  en `N/A` **con su motivo impreso**, si el diff no deja líneas `.py`
  medibles).
