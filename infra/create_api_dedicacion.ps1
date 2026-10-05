# infra/create_api_dedicacion.ps1
# Alta del Container App `ca-dedicacion-api`: cuadrante, maestros y export.
#
#     . .\00_vars_dedicacion.ps1 ; . .\00_capps_vars_dedicacion.ps1
#     .\create_api_dedicacion.ps1
#
# VA DESPUES DEL TRANSFER: este script lee su FQDN interno y lo cablea en
# TRANSFER_BASE_URL (R27). Si el transfer no existe todavia, aborta.
#
# POR QUE LA API VA INTERNA, Y NO ES NEGOCIABLE (R7, R8)
# ------------------------------------------------------
# La api NO tiene autenticacion propia. Su unico control de identidad es
# `interface_adapters/api/deps.py::obtener_usuario`, que lee la cabecera
# X-Usuario y se la cree. Con ingress externo, cualquiera en Internet podria
# llamar a POST /api/v1/registro/ejecutar poniendo la cabecera que quisiera;
# la api llamaria al transfer, y el transfer es la unica pluma del sistema
# sobre el ERP.
#
# El ingress interno ES el control de acceso de la api. Lo que hay que
# aceptar a cambio: la api solo se alcanza a traves del proxy del front
# autenticado (https://<fqdn-front>/api/v1/...). No se abre un atajo
# "temporal" para probar; los atajos temporales se quedan.
#
# LA BASE DE DATOS (R13, R17)
# ---------------------------
# AUTO_CREATE_DATABASE=false: este servicio NO crea bases ni roles. La base
# vive en un servidor COMPARTIDO con otros cuatro proyectos y la creo una
# persona con crear_base_dedicacion.ps1. Con el conmutador apagado el
# servicio ni siquiera abre la conexion de administracion, y por eso aqui no
# se despliega ninguna variable PG_ADMIN_*: no las necesita, y lo que no
# viaja no se filtra.
# PG_SSLMODE=require: Azure Flexible Server exige TLS, y el defecto del
# codigo ('prefer') acepta sin protestar una conexion sin cifrar.

$ErrorActionPreference = "Stop"
$env:AZURE_CORE_ONLY_SHOW_ERRORS = "true"

foreach ($v in @('MI_ID', 'IMG', 'APPS', 'KV_URI', 'PG_HOST', 'SIGRID_URL')) {
    if (-not (Get-Variable -Name $v -ValueOnly -ErrorAction SilentlyContinue)) {
        throw "Falta `$$v. Haz:  . .\00_vars_dedicacion.ps1 ; . .\00_capps_vars_dedicacion.ps1"
    }
}
az account set --subscription $SUBSCRIPTION | Out-Null

$APP = $APPS["api"]

if (App-Existe $APP) {
    throw "El Container App '$APP' ya existe. Para republicar: .\redeploy_dedicacion.ps1 -Solo api"
}
if (-not (App-Existe $APPS["transfer"])) {
    throw "No existe '$($APPS['transfer'])'. El orden es transfer -> api -> front (R27): corre antes .\create_transfer_dedicacion.ps1"
}

Write-Host "`n=== api (cuadrante y maestros, ingress INTERNO) ===" -ForegroundColor Green

# FQDN interno del transfer, para cablear el registro en Sigrid.
$TRANSFER_URL = "http://$(Fqdn-Interno 'transfer')"
Write-Host "  Cableando TRANSFER_BASE_URL=$TRANSFER_URL" -ForegroundColor Cyan

# --- Secretos: SOLO referencias a Key Vault (R19) ---------------------------
$secretos = @(
    "pg-password=$(KvRef 'PG-PASSWORD')",
    "sigrid-key=$(KvRef 'SIGRID-API-FUNCTION-KEY')"
)

$entorno = @(
    # uvicorn tiene que escuchar en 0.0.0.0 DENTRO del contenedor.
    "API_HOST=0.0.0.0", "API_PORT=$($PUERTOS['api'])",
    "LOG_LEVEL=INFO",

    # --- PostgreSQL: base propia en el servidor COMPARTIDO -----------------
    "PG_HOST=$PG_HOST", "PG_PORT=5432", "PG_DB=$PG_DB",
    # Rol de aplicacion PROPIO, nunca el admin del servidor. Es lo unico que
    # va dentro del contenedor y por tanto lo unico que podria filtrarse.
    "PG_USER=$PG_APP_USER",
    "PG_PASSWORD=secretref:pg-password",
    "PG_SSLMODE=require",
    # El servicio no crea bases ni roles. NO se despliega ninguna PG_ADMIN_*.
    "AUTO_CREATE_DATABASE=false",

    # --- Sigrid: SOLO LECTURA de maestros ----------------------------------
    # La api no tiene rutas de escritura. La unica escritura del sistema la
    # hace el transfer. (Decision D5, abierta: si sigrid-api puede dar una
    # clave de solo lectura, esta deberia serlo.)
    "SIGRID_API_BASE_URL=$SIGRID_URL",
    "SIGRID_API_FUNCTION_KEY=secretref:sigrid-key",
    "SIGRID_API_DATABASE=$SIGRID_DB",
    "SIGRID_API_TIMEOUT_S=60",
    "SIGRID_MAX_ROWS=5000",

    # --- Registro en Sigrid, a traves del transfer -------------------------
    # El timeout tiene que ser MENOR que el del front hacia aqui (200 s) y
    # los dos por debajo del corte del balanceador de Azure, 230 s (R28).
    "TRANSFER_BASE_URL=$TRANSFER_URL",
    "TRANSFER_TIMEOUT_S=$TIMEOUT_API_TRANSFER"
)

$argumentos = @(
    "containerapp", "create", "-n", $APP, "-g", $RG, "--environment", $CAE,
    "--image", (Imagen "api"),
    "--registry-server", $ACR_LOGIN, "--registry-identity", $MI_ID,
    "--user-assigned", $MI_ID,
    # max 1 (R5): la sincronizacion de maestros y la sustitucion atomica de
    # asignaciones no estan disenadas para varias replicas concurrentes, y no
    # hay ningun test que demuestre lo contrario.
    "--min-replicas", "$MIN_REPLICAS", "--max-replicas", "$MAX_REPLICAS",
    "--cpu", "0.5", "--memory", "1.0Gi",
    "--ingress", "internal", "--target-port", "$($PUERTOS['api'])",
    "--transport", "auto",
    "--secrets") + $secretos + @("--env-vars") + $entorno + @("--tags") + $TAGS
Run-Az $argumentos

# HTTP plano dentro del entorno: el front la llama por http://.
Run-Az @("containerapp", "ingress", "update", "-n", $APP, "-g", $RG, "--allow-insecure", "true")

$FQDN = Fqdn-Interno "api"

Write-Host "`n=== $APP creado ===" -ForegroundColor Green
az containerapp show -n $APP -g $RG `
    --query "{Estado:properties.provisioningState, Min:properties.template.scale.minReplicas, Max:properties.template.scale.maxReplicas, Externo:properties.configuration.ingress.external, FQDN:properties.configuration.ingress.fqdn}" `
    -o table

Write-Host "`nURL interna (la consume el front):  http://$FQDN" -ForegroundColor Cyan
Write-Host "No hay URL publica, y es deliberado (R8): esta api se cree la cabecera X-Usuario." -ForegroundColor Cyan

Write-Host "`nSi el arranque falla con 'La base de datos ... no existe', es que falta" -ForegroundColor Yellow
Write-Host "correr crear_base_dedicacion.ps1. El servicio NO la crea solo, a proposito." -ForegroundColor Yellow
Write-Host "Logs:  az containerapp logs show -n $APP -g $RG --tail 60" -ForegroundColor Yellow
Write-Host "`nSIGUIENTE:  .\create_front_dedicacion.ps1" -ForegroundColor Yellow
