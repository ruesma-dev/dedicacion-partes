# infra/redeploy_dedicacion.ps1
# Republica uno o varios servicios de DEDICACION tras cambiar su codigo:
#   1) reconstruye su imagen con TAG FECHADO NUEVO y la sube al ACR,
#   2) crea una revision nueva del Container App apuntando a esa imagen.
#
# El codigo va HORNEADO en la imagen: reiniciar NO basta, hay que reconstruir.
# Con tag fechado no hace falta --revision-suffix para forzar el pull (la
# imagen es OTRA), pero se pone igual para que la revision lleve el sello en
# el nombre y se lea de un vistazo cual esta activa.
#
# ORDEN FIJO, sin importar como se pidan (R27):
#     transfer -> api -> front
# Cada servicio ANTES que quien lo consume: cuando el front levanta con codigo
# nuevo, la api ya esta sana; y cuando la api levanta, el transfer tambien.
# Al reves, la primera peticion de un usuario cae en un backend en arranque.
#
# Este script SOLO REPUBLICA. Si el Container App no existe, aborta: la
# primera publicacion se hace con create_<servicio>_dedicacion.ps1, que es
# quien decide ingress, replicas, secretos y variables de entorno.
#
# Uso:
#     . .\00_vars_dedicacion.ps1 ; . .\00_capps_vars_dedicacion.ps1
#     .\redeploy_dedicacion.ps1 -Solo api,front
#     .\redeploy_dedicacion.ps1                    # los tres

param(
    [ValidateSet("transfer", "api", "front")]
    [string[]] $Solo = @("transfer", "api", "front"),

    # Salta el `az acr build` y solo crea la revision nueva con el tag que ya
    # conste en infra/imagenes.json (util si acabas de construir a mano).
    [switch] $SinBuild
)

$ErrorActionPreference = "Stop"
# La extension containerapp escribe un warning benigno en stderr y, con -Stop,
# PowerShell 5.1 lo trata como error terminante (NativeCommandError).
$env:AZURE_CORE_ONLY_SHOW_ERRORS = "true"

foreach ($v in @('RG', 'ACR', 'IMG', 'APPS', 'ORDEN')) {
    if (-not (Get-Variable -Name $v -ValueOnly -ErrorAction SilentlyContinue)) {
        throw "Falta `$$v. Haz:  . .\00_vars_dedicacion.ps1 ; . .\00_capps_vars_dedicacion.ps1"
    }
}

# --- Se REORDENA lo que pidan al orden seguro -------------------------------
$pedidos = $Solo | Select-Object -Unique
$plan = $ORDEN | Where-Object { $pedidos -contains $_ }
if (-not $plan) { throw "No hay servicios validos que desplegar en -Solo." }

$suf = "r" + (Get-Date -Format "yyyyMMddHHmmss")   # unico, [a-z0-9-]

az account set --subscription $SUBSCRIPTION | Out-Null

Write-Host "`n=== Redeploy DEDICACION ===" -ForegroundColor Cyan
Write-Host "  Pedidos : $($pedidos -join ', ')"
Write-Host "  Orden   : $($plan -join ' -> ')   (cada servicio antes que quien lo consume)"
Write-Host "  Build   : $(if ($SinBuild) { 'NO (-SinBuild)' } else { 'si' })"

# --- 0) Precheck: republicar no es dar de alta ------------------------------
foreach ($svc in $plan) {
    $app = $APPS[$svc]
    if (-not (App-Existe $app)) {
        Write-Host "`nEl Container App '$app' ($svc) no existe en '$RG'." -ForegroundColor Red
        Write-Host "Eso seria una PRIMERA publicacion, no una republicacion." -ForegroundColor Red
        Write-Host "Usa:  .\create_${svc}_dedicacion.ps1" -ForegroundColor Yellow
        throw "Abortado: '$app' no existe."
    }
    if (-not $IMG[$svc]) { throw "No hay entrada '$svc' en `$IMG (00_vars_dedicacion.ps1)." }
}

$build = Join-Path $PSScriptRoot "build_images_dedicacion.ps1"
if (-not $SinBuild -and -not (Test-Path $build)) {
    throw "No encuentro build_images_dedicacion.ps1 junto a este script."
}

# --- Despliegue, en el orden seguro -----------------------------------------
foreach ($svc in $plan) {
    $app = $APPS[$svc]

    Write-Host "`n============================================================" -ForegroundColor DarkGray
    Write-Host "=== $svc -> $app" -ForegroundColor Green

    if (-not $SinBuild) {
        Write-Host "--- 1) Build ($svc) ---" -ForegroundColor Green
        & $build -Solo $svc
        if ($LASTEXITCODE -ne 0) { throw "Build de '$svc' fallo (exit $LASTEXITCODE)." }
    }

    # Tag recien escrito en infra/imagenes.json por el build.
    $imagen = Imagen $svc
    Write-Host "--- 2) Revision nueva de $app ---" -ForegroundColor Green
    Write-Host "    imagen: $imagen"
    Run-Az @("containerapp", "update", "-n", $app, "-g", $RG,
             "--image", $imagen, "--revision-suffix", $suf)
}

# --- Verificacion final -----------------------------------------------------
Write-Host "`n=== Estado tras el redeploy ===" -ForegroundColor Green
foreach ($svc in $plan) {
    $app = $APPS[$svc]
    $img = az containerapp show -n $app -g $RG --query "properties.template.containers[0].image" -o tsv
    $rev = az containerapp show -n $app -g $RG --query "properties.latestRevisionName" -o tsv
    Write-Host ("  {0,-24} imagen={1}  revision={2}" -f $app, $img, $rev)
}

if ($plan -contains "front") {
    Write-Host "`nFront: https://$(Fqdn-Interno 'front')   (Ctrl+F5 para refrescar app.js)" -ForegroundColor Yellow
    Write-Host "Con Easy Auth activo, pedirlo sin sesion redirige al login: es lo esperado." -ForegroundColor Yellow
}
if ($plan -contains "transfer") {
    Write-Host "`nEl transfer es INTERNO (sin URL publica). Comprueba su arranque:" -ForegroundColor Yellow
    Write-Host "  az containerapp logs show -n $($APPS['transfer']) -g $RG --tail 60" -ForegroundColor Yellow
    Write-Host "Y que SIGUE en modo pruebas (R9):" -ForegroundColor Yellow
    Write-Host "  az containerapp show -n $($APPS['transfer']) -g $RG --query `"properties.template.containers[0].env[?name=='OBRA_PRUEBAS_FORZAR'].value`" -o tsv" -ForegroundColor Yellow
}

Write-Host "`nNo olvides commitear infra/imagenes.json: es el registro de que hay desplegado." -ForegroundColor Yellow
