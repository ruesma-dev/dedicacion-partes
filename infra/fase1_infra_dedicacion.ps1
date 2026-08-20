# infra/fase1_infra_dedicacion.ps1
# Provision de la infraestructura PROPIA de DEDICACION con az CLI.
# NO crea los Container Apps (eso es la fase 2) y NO crea nada que ya exista
# en el ecosistema: el registro de contenedores, el servidor PostgreSQL y la
# pasarela sigrid-api se REUTILIZAN tal cual (R2).
#
# Uso:
#     . .\00_vars_dedicacion.ps1
#     .\fase1_infra_dedicacion.ps1
#
# ES IDEMPOTENTE: si el nombre del Key Vault esta pillado (su espacio de
# nombres es MUNDIAL), cambia $SUFFIX en 00_vars_dedicacion.ps1 y relanza.
#
# LO QUE ESTE SCRIPT NO CREA, Y POR QUE
# -------------------------------------
#   - Storage Account, colas y contenedores de blobs (R3): aqui no hay canal
#     asincrono. La cadena front -> api -> transfer es HTTP sincrono y el
#     volumen es un cuadrante mensual por obra. `partes` los necesita porque
#     su pipeline encadena cinco servicios por cola; copiarlos aqui seria
#     superficie de ataque y factura sin contrapartida.
#   - La base de datos: la crea crear_base_dedicacion.ps1, aparte y a mano,
#     porque vive en un servidor COMPARTIDO con otros cuatro proyectos (R18).
#   - Ningun secreto: los carga add_secrets_dedicacion.ps1 pidiendolos de
#     forma segura. Aqui solo se conceden los PERMISOS para leerlos.

$ErrorActionPreference = "Stop"

function Section($t) { Write-Host "`n=== $t ===" -ForegroundColor Green }
function Require($val, $msg) {
    if ([string]::IsNullOrWhiteSpace($val)) {
        Write-Host "`nABORTADO: $msg" -ForegroundColor Red
        exit 1
    }
}

if (-not $RG) { throw "Falta `$RG. Haz primero:  . .\00_vars_dedicacion.ps1" }
if ($SUBSCRIPTION -like "REDACTADO*") {
    throw "SUBSCRIPTION sigue redactada. Crea 00_vars_dedicacion.local.ps1 con el valor real y dot-sourceala."
}

# --- 0) Precondiciones ------------------------------------------------------
Section "0) Suscripcion, proveedores y extension containerapp"
az account set --subscription $SUBSCRIPTION
foreach ($p in @(
        "Microsoft.App", "Microsoft.OperationalInsights",
        "Microsoft.KeyVault", "Microsoft.ManagedIdentity")) {
    az provider register --namespace $p --only-show-errors | Out-Null
}
az extension add --name containerapp --upgrade --only-show-errors | Out-Null

# objectId de quien ejecuta, para poder escribir secretos en el Key Vault.
$ME = az ad signed-in-user show --query "id" -o tsv 2>$null
if ([string]::IsNullOrWhiteSpace($ME)) {
    Write-Host "  (aviso) no pude resolver tu objectId: me salto el rol 'Key Vault Secrets Officer' para ti." -ForegroundColor Yellow
    Write-Host "  (aviso) sin el, add_secrets_dedicacion.ps1 fallara al guardar." -ForegroundColor Yellow
}

# --- 1) Resource group ------------------------------------------------------
Section "1) Resource group $RG"
az group create -n $RG -l $LOCATION --tags $TAGS | Out-Null

# --- 2) Managed identity (la comparten los tres Container Apps) -------------
Section "2) Managed identity $MI"
az identity create -n $MI -g $RG -l $LOCATION --tags $TAGS | Out-Null
$MI_PRINCIPAL = az identity show -n $MI -g $RG --query "principalId" -o tsv
$MI_ID_LOCAL  = az identity show -n $MI -g $RG --query "id"          -o tsv
Require $MI_PRINCIPAL "No pude crear/leer la managed identity '$MI'."

function Assign-Role($role, $scope) {
    # Idempotente: si ya esta asignado, az avisa y no se rompe nada.
    az role assignment create --assignee-object-id $MI_PRINCIPAL `
        --assignee-principal-type ServicePrincipal `
        --role $role --scope $scope --only-show-errors 2>$null | Out-Null
}

# --- 3) ACR REUTILIZADO: AcrPull para nuestra identidad (cross-RG) ----------
Section "3) AcrPull sobre el registro compartido $ACR ($ACR_RG)"
# El usuario admin del registro esta DESHABILITADO en la suscripcion: la unica
# via de acceso es la identidad gestionada, tanto aqui como con
# --registry-identity en cada Container App (R20).
$ACR_ID = az acr show -n $ACR -g $ACR_RG --query "id" -o tsv
Require $ACR_ID "No encuentro el registro '$ACR' en '$ACR_RG'. Revisa 00_vars_dedicacion.ps1. NO lo crees: es compartido."
Assign-Role "AcrPull" $ACR_ID
Write-Host "  AcrPull concedido a '$MI' sobre $ACR (no se modifica el registro)."

# --- 4) Log Analytics -------------------------------------------------------
Section "4) Log Analytics $LAW"
az monitor log-analytics workspace create -g $RG -n $LAW -l $LOCATION --tags $TAGS | Out-Null
$LAW_CUSTOMERID = az monitor log-analytics workspace show -g $RG -n $LAW --query "customerId" -o tsv
$LAW_KEY = az monitor log-analytics workspace get-shared-keys -g $RG -n $LAW --query "primarySharedKey" -o tsv
Require $LAW_CUSTOMERID "No pude obtener el customerId de Log Analytics '$LAW'."

# --- 5) Key Vault (RBAC, no access policies) -------------------------------
Section "5) Key Vault $KV (RBAC)"
az keyvault create -n $KV -g $RG -l $LOCATION `
    --enable-rbac-authorization true --tags $TAGS | Out-Null
$KV_ID = az keyvault show -n $KV -g $RG --query "id" -o tsv
Require $KV_ID "El Key Vault '$KV' no se creo (su nombre es unico MUNDIAL y puede estar pillado). Cambia `$SUFFIX en 00_vars_dedicacion.ps1 y relanza."

# La identidad gestionada solo LEE secretos, en tiempo de ejecucion.
Assign-Role "Key Vault Secrets User" $KV_ID
# Quien despliega los ESCRIBE (add_secrets_dedicacion.ps1).
if (-not [string]::IsNullOrWhiteSpace($ME)) {
    az role assignment create --assignee-object-id $ME --assignee-principal-type User `
        --role "Key Vault Secrets Officer" --scope $KV_ID --only-show-errors 2>$null | Out-Null
}

# --- 6) Container Apps Environment -----------------------------------------
Section "6) Container Apps Environment $CAE"
# Es la red interna donde se ven los tres servicios. El ingress interno de la
# api y del transfer solo significa algo dentro de este entorno (R7).
az containerapp env create -n $CAE -g $RG -l $LOCATION `
    --logs-destination log-analytics `
    --logs-workspace-id $LAW_CUSTOMERID --logs-workspace-key $LAW_KEY `
    --tags $TAGS | Out-Null

# --- 7) Comprobacion: la pasarela de Sigrid existe y NO se toca -------------
Section "7) sigrid-api (reutilizada, solo se comprueba)"
$SIGRID_ID = az functionapp show -n $SIGRID_FUNC -g $SIGRID_RG --query "id" -o tsv 2>$null
if ([string]::IsNullOrWhiteSpace($SIGRID_ID)) {
    Write-Host "  (aviso) no encuentro '$SIGRID_FUNC' en '$SIGRID_RG'. Revisa el nombre." -ForegroundColor Yellow
    Write-Host "  (aviso) NO la crees: es de otro proyecto y es el UNICO acceso al SQL Server de Sigrid." -ForegroundColor Yellow
} else {
    Write-Host "  $SIGRID_FUNC localizada. No se modifica."
}

# --- 8) Resumen -------------------------------------------------------------
Section "8) RESUMEN"
Write-Host "RG                 : $RG"
Write-Host "Managed identity   : $MI"
Write-Host "Registro (reutil.) : $ACR.azurecr.io   (AcrPull concedido; admin deshabilitado)"
Write-Host "Log Analytics      : $LAW"
Write-Host "Key Vault          : $KV   (RBAC; VACIO todavia)"
Write-Host "CA Environment     : $CAE"
Write-Host "PostgreSQL         : $PG ($PG_RG) - COMPARTIDO, no se ha tocado"
Write-Host "Storage Account    : NINGUNA, a proposito (R3)"

Write-Host "`nSIGUIENTE:" -ForegroundColor Yellow
Write-Host "  1) .\crear_base_dedicacion.ps1            # base y rol en el servidor compartido (una sola vez)"
Write-Host "  2) .\add_secrets_dedicacion.ps1           # las tres claves del Key Vault"
Write-Host "  3) .\build_images_dedicacion.ps1          # imagenes con tag fechado"
Write-Host "  4) create_transfer -> create_api -> create_front   # en ese orden"
