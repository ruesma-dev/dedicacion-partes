# infra/create_front_dedicacion.ps1
# Alta del Container App `ca-dedicacion-front`: la SPA de captura y el proxy.
#
#     . .\00_vars_dedicacion.ps1 ; . .\00_capps_vars_dedicacion.ps1
#     .\create_front_dedicacion.ps1
#
# VA EL ULTIMO: lee el FQDN interno de la api y lo cablea en API_BASE_URL (R27).
#
# ES EL UNICO SERVICIO CON INGRESS EXTERNO (R7)
# ---------------------------------------------
# Y por tanto el unico sitio donde la identidad existe de verdad. El proxy
# traduce la cabecera X-MS-CLIENT-PRINCIPAL-NAME que pone Easy Auth a la
# cabecera X-Usuario que la api usa para auditar (R11). Ese es el unico
# camino por el que la identidad llega al backend.
#
# OJO: AL TERMINAR ESTE SCRIPT, EL FRONT ESTA ABIERTO A INTERNET SIN
# AUTENTICACION. La Easy Auth la pone setup_front_easyauth.ps1, que es el
# paso siguiente e inmediato. No lo dejes a medias.
#
# DEFAULT_USER=desconocido (R12)
# ------------------------------
# En local vale 'local', que es comodo. Desplegado NO: si por cualquier
# motivo llegara una peticion sin cabecera de Easy Auth, la auditoria tiene
# que registrar que el usuario no se identifico, y no un nombre con aspecto
# legitimo que nadie sabria interpretar seis meses despues.

$ErrorActionPreference = "Stop"
$env:AZURE_CORE_ONLY_SHOW_ERRORS = "true"

foreach ($v in @('MI_ID', 'IMG', 'APPS')) {
    if (-not (Get-Variable -Name $v -ValueOnly -ErrorAction SilentlyContinue)) {
        throw "Falta `$$v. Haz:  . .\00_vars_dedicacion.ps1 ; . .\00_capps_vars_dedicacion.ps1"
    }
}
az account set --subscription $SUBSCRIPTION | Out-Null

$APP = $APPS["front"]

if (App-Existe $APP) {
    throw "El Container App '$APP' ya existe. Para republicar: .\redeploy_dedicacion.ps1 -Solo front"
}
if (-not (App-Existe $APPS["api"])) {
    throw "No existe '$($APPS['api'])'. El orden es transfer -> api -> front (R27): corre antes .\create_api_dedicacion.ps1"
}

Write-Host "`n=== front (captura y proxy, ingress EXTERNO) ===" -ForegroundColor Green

$API_URL = "http://$(Fqdn-Interno 'api')"
Write-Host "  Cableando API_BASE_URL=$API_URL" -ForegroundColor Cyan

# El front no consume ningun secreto propio: no habla con PostgreSQL ni con
# Sigrid. El unico secreto que acabara teniendo es el client secret de Easy
# Auth, y lo anade setup_front_easyauth.ps1 por referencia al Key Vault.
$entorno = @(
    # uvicorn tiene que escuchar en 0.0.0.0 DENTRO del contenedor.
    "FRONT_HOST=0.0.0.0", "FRONT_PORT=$($PUERTOS['front'])",
    "LOG_LEVEL=INFO",

    # --- Backend (ingress interno, http plano) -----------------------------
    "API_BASE_URL=$API_URL",
    # Espera MAS que la api al transfer (180 s) y menos que el corte del
    # balanceador de Azure (230 s, no configurable). Al reves, el front se
    # rendiria mientras la api sigue registrando y el usuario veria un error
    # de una escritura que si se hizo (R28).
    "API_TIMEOUT_S=$TIMEOUT_FRONT_API",

    # --- Identidad (R12) ----------------------------------------------------
    "DEFAULT_USER=desconocido"
)

$argumentos = @(
    "containerapp", "create", "-n", $APP, "-g", $RG, "--environment", $CAE,
    "--image", (Imagen "front"),
    "--registry-server", $ACR_LOGIN, "--registry-identity", $MI_ID,
    "--user-assigned", $MI_ID,
    "--min-replicas", "$MIN_REPLICAS", "--max-replicas", "$MAX_REPLICAS",
    "--cpu", "0.25", "--memory", "0.5Gi",
    "--ingress", "external", "--target-port", "$($PUERTOS['front'])",
    "--transport", "auto",
    "--env-vars") + $entorno + @("--tags") + $TAGS
Run-Az $argumentos

$FQDN = Fqdn-Interno "front"

Write-Host "`n=== $APP creado ===" -ForegroundColor Green
az containerapp show -n $APP -g $RG `
    --query "{Estado:properties.provisioningState, Min:properties.template.scale.minReplicas, Max:properties.template.scale.maxReplicas, Externo:properties.configuration.ingress.external, FQDN:properties.configuration.ingress.fqdn}" `
    -o table

Write-Host "`nURL publica:  https://$FQDN" -ForegroundColor Cyan
Write-Host "GUARDA ese FQDN: lo necesitas para el redirect de Easy Auth y para la" -ForegroundColor Cyan
Write-Host "tarjeta del Portal Ruesma, que la anade el proyecto front-portal." -ForegroundColor Cyan

Write-Host "`n############################################################" -ForegroundColor Red
Write-Host "# AHORA MISMO ESTE FRONT ESTA ABIERTO A INTERNET SIN LOGIN. #" -ForegroundColor Red
Write-Host "# Y su proxy llega hasta la api, que se cree la cabecera     #" -ForegroundColor Red
Write-Host "# X-Usuario y sabe llamar al transfer.                       #" -ForegroundColor Red
Write-Host "#                                                            #" -ForegroundColor Red
Write-Host "# SIGUIENTE PASO, SIN DEJARLO PARA MANANA:                   #" -ForegroundColor Red
Write-Host "#   .\setup_front_easyauth.ps1                               #" -ForegroundColor Red
Write-Host "############################################################" -ForegroundColor Red

Write-Host "`nDespues de Easy Auth, /health del front NO respondera a un curl anonimo:" -ForegroundColor Yellow
Write-Host "devolvera una redireccion al login. Es lo esperado (R35), no una caida." -ForegroundColor Yellow
