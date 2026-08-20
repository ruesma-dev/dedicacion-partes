# infra/00_capps_vars_dedicacion.ps1
# Valores DERIVADOS de la fase 1 (los recursos ya tienen que existir) y
# ayudantes que comparten todos los scripts de alta de Container Apps.
#
# Dot-source DESPUES de 00_vars_dedicacion.ps1:
#
#     . .\00_vars_dedicacion.ps1
#     . .\00_capps_vars_dedicacion.ps1
#
# Aqui tampoco entra ningun valor secreto: lo unico que se lee de Azure son
# identificadores de RECURSO (el id de la managed identity), no credenciales.

$ErrorActionPreference = "Stop"
if (-not $RG) { throw "Falta `$RG. Haz primero:  . .\00_vars_dedicacion.ps1" }

# --- Derivados de la fase 1 -------------------------------------------------
$Global:MI_ID     = az identity show -n $MI -g $RG --query "id" -o tsv
if (-not $MI_ID) { throw "No encuentro la managed identity '$MI' en '$RG'. Corre antes .\fase1_infra_dedicacion.ps1" }

# --- FQDN compuestos a partir del NOMBRE del recurso ------------------------
# Se componen aqui en vez de escribirse literales: el nombre del recurso es
# publico dentro de la casa (R2 obliga a declararlo), pero un FQDN escrito a
# mano es media cadena de conexion y acaba copiandose donde no debe.
$Global:ACR_LOGIN   = "$ACR.azurecr.io"
$Global:KV_URI      = "https://$KV.vault.azure.net"
$Global:PG_HOST     = "$PG.postgres.database.azure.com"
$Global:SIGRID_URL  = "https://$SIGRID_FUNC.azurewebsites.net"

# --- Ayudantes compartidos --------------------------------------------------

function KvRef($nombreEnKeyVault) {
    <#
        Secret de Container App -> REFERENCIA a Key Vault, leida con la
        identidad gestionada. El valor no viaja nunca por la definicion del
        recurso, ni por el historial de la consola, ni por esta carpeta (R19).
    #>
    "keyvaultref:$KV_URI/secrets/$nombreEnKeyVault,identityref:$MI_ID"
}

function Run-Az($argList) {
    <# az con codigo de salida comprobado: az escribe a stderr y con
       ErrorActionPreference=Stop PowerShell 5.1 confunde un warning benigno
       con un error terminante. #>
    az @argList | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "az fallo (exit $LASTEXITCODE) en: $($argList -join ' ')" }
}

function App-Existe($nombreApp) {
    <# `containerapp show` de una app inexistente escribe en stderr y, con
       -Stop, PS 5.1 lo convierte en error terminante aunque haya 2>$null:
       el alta moria justo en el caso "no existe". `list --query` devuelve
       vacio sin tocar stderr. #>
    [bool](az containerapp list -g $RG --query "[?name=='$nombreApp'].name" -o tsv)
}

function Tag-Publicado($servicio) {
    <#
        Tag fechado que consta como publicado para ese servicio en
        infra/imagenes.json. Es la fuente de verdad de "que codigo esta
        corriendo" (R24): si esta a null, ese servicio no se ha construido
        nunca y no hay nada que desplegar.
    #>
    $ruta = Join-Path $PSScriptRoot "imagenes.json"
    if (-not (Test-Path $ruta)) { throw "No encuentro $ruta." }
    $inventario = Get-Content $ruta -Raw -Encoding UTF8 | ConvertFrom-Json
    $entrada = $inventario.servicios.$($IMG[$servicio])
    if (-not $entrada) { throw "imagenes.json no tiene entrada para '$($IMG[$servicio])'." }
    if (-not $entrada.tag) {
        throw "El servicio '$servicio' no se ha publicado nunca. Corre antes: .\build_images_dedicacion.ps1 -Solo $servicio"
    }
    $entrada.tag
}

function Imagen($servicio) {
    <# Referencia completa de imagen, con TAG FECHADO. Nunca 'latest'. #>
    "$ACR_LOGIN/$($IMG[$servicio]):$(Tag-Publicado $servicio)"
}

function Fqdn-Interno($servicio) {
    <# FQDN del ingress de un Container App ya creado, para cablear a quien lo
       consume (R27: el orden de alta es transfer -> api -> front). #>
    $app = $APPS[$servicio]
    $fqdn = az containerapp show -n $app -g $RG --query "properties.configuration.ingress.fqdn" -o tsv
    if (-not $fqdn) { throw "No pude leer el FQDN de '$app'. Existe ya?" }
    $fqdn
}

Write-Host "[capps-vars-dedicacion] MI_ID resuelto. ACR=$ACR_LOGIN  KV=$KV_URI" -ForegroundColor Cyan
Write-Host "[capps-vars-dedicacion] PG_HOST y SIGRID_URL compuestos desde el nombre del recurso." -ForegroundColor Cyan
