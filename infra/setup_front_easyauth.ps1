# infra/setup_front_easyauth.ps1
# Protege el front (`ca-dedicacion-front`) con Easy Auth (Entra ID) y
# restringe el acceso a los miembros de un grupo de seguridad propio.
#
#     . .\00_vars_dedicacion.ps1 ; . .\00_capps_vars_dedicacion.ps1
#     .\setup_front_easyauth.ps1
#     .\setup_front_easyauth.ps1 -Miembros "ana@ruesma.es","luis@ruesma.es"
#
# Corre INMEDIATAMENTE despues de create_front_dedicacion.ps1: entre uno y
# otro, el front esta abierto a Internet sin login.
#
# MECANISMO (el mismo que albaranes-portal y partes)
# --------------------------------------------------
#   1) Grupo de seguridad `dedicacion-portal-users`.
#   2) App Registration propia, con redirect /.auth/login/aad/callback.
#   3) Client secret -> Key Vault -> secret del Container App por keyvaultref.
#      El valor NO pasa por disco ni por la definicion del recurso (R19).
#   4) Enterprise App con ASIGNACION REQUERIDA y el grupo asignado a ella:
#      Entra solo emite token a los miembros del grupo (R36).
#   5) Login obligatorio: quien no esta autenticado va al login, no al front.
#   6) Admin-consent en mejor esfuerzo, para SSO silencioso desde el Portal.
#
# ES IDEMPOTENTE: relanzarlo reutiliza grupo, App Registration, secret y
# service principal. No genera un client secret nuevo si ya hay uno en el
# Key Vault.
#
# QUIEN ENTRA EN EL GRUPO ES DECISION DEL HUMANO (D3, sin cerrar el
# 2026-08-20). Este script anade siempre a quien lo ejecuta -para poder
# probar- y admite el resto por el parametro -Miembros. La lista no se
# escribe en el repositorio: son datos de personas y el GUID del grupo no
# puede entrar aqui (R21).

param(
    # UPN o objectId de las personas que entran en el grupo, ademas de ti.
    [string[]] $Miembros = @()
)

$ErrorActionPreference = "Stop"
$env:AZURE_CORE_ONLY_SHOW_ERRORS = "true"

foreach ($v in @('RG', 'KV', 'KV_URI', 'TENANT', 'MI_ID', 'SUBSCRIPTION', 'APPS', 'GRUPO_ACCESO')) {
    if (-not (Get-Variable -Name $v -ValueOnly -ErrorAction SilentlyContinue)) {
        throw "Falta `$$v. Haz:  . .\00_vars_dedicacion.ps1 ; . .\00_capps_vars_dedicacion.ps1"
    }
}
if ($TENANT -like "REDACTADO*") {
    throw "TENANT sigue redactado. Crea 00_vars_dedicacion.local.ps1 con el valor real y dot-sourceala."
}
az account set --subscription $SUBSCRIPTION | Out-Null

$APP_NAME       = $APPS["front"]
$APP_REG_NAME   = "dedicacion (front EasyAuth)"
$SECRET_KV_NAME = "EASYAUTH-CLIENT-SECRET"
$CA_SECRET_NAME = "easyauth-client-secret"

# --- 0) FQDN del front (dinamico) -------------------------------------------
$FQDN = Fqdn-Interno "front"
$REDIRECT = "https://$FQDN/.auth/login/aad/callback"
Write-Host "[easyauth] front  : $FQDN" -ForegroundColor Cyan
Write-Host "[easyauth] redirect: $REDIRECT" -ForegroundColor Cyan

# --- 1) Grupo de seguridad (idempotente) ------------------------------------
$GROUP_ID = az ad group list --display-name $GRUPO_ACCESO --query "[0].id" -o tsv
if (-not $GROUP_ID) {
    $GROUP_ID = az ad group create --display-name $GRUPO_ACCESO `
                    --mail-nickname $GRUPO_ACCESO --query id -o tsv
    Write-Host "[easyauth] grupo '$GRUPO_ACCESO' creado" -ForegroundColor Green
} else {
    Write-Host "[easyauth] grupo '$GRUPO_ACCESO' ya existe" -ForegroundColor Yellow
}
if (-not $GROUP_ID) { throw "No pude crear ni localizar el grupo '$GRUPO_ACCESO'." }

# --- 2) Miembros: tu y quien digas (decision D3) ----------------------------
function Anadir-Miembro($identificador) {
    $oid = $identificador
    if ($identificador -notmatch '^[0-9a-fA-F-]{36}$') {
        $oid = az ad user show --id $identificador --query id -o tsv 2>$null
        if (-not $oid) { Write-Warning "No encuentro al usuario '$identificador'. Lo salto."; return }
    }
    $esMiembro = az ad group member check --group $GROUP_ID --member-id $oid --query value -o tsv
    if ($esMiembro -ne "true") {
        az ad group member add --group $GROUP_ID --member-id $oid | Out-Null
        Write-Host "[easyauth] anadido al grupo: $identificador" -ForegroundColor Green
    } else {
        Write-Host "[easyauth] ya era miembro: $identificador" -ForegroundColor DarkGray
    }
}

$ME = az ad signed-in-user show --query id -o tsv
if ($ME) { Anadir-Miembro $ME } else { Write-Warning "No pude resolver tu objectId: anadete a mano o no podras entrar." }
foreach ($m in $Miembros) { Anadir-Miembro $m }

# --- 3) App Registration (idempotente por displayName) ----------------------
$APP_ID = az ad app list --display-name $APP_REG_NAME --query "[0].appId" -o tsv
if (-not $APP_ID) {
    $APP_ID = az ad app create --display-name $APP_REG_NAME `
                --sign-in-audience AzureADMyOrg `
                --web-redirect-uris $REDIRECT `
                --enable-id-token-issuance true `
                --query appId -o tsv
    Write-Host "[easyauth] App Registration creada" -ForegroundColor Green
} else {
    az ad app update --id $APP_ID `
        --web-redirect-uris $REDIRECT --enable-id-token-issuance true | Out-Null
    Write-Host "[easyauth] App Registration ya existia (redirect actualizado)" -ForegroundColor Yellow
}
if (-not $APP_ID) { throw "No pude crear ni localizar la App Registration '$APP_REG_NAME'." }

# --- 4) Client secret -> Key Vault (solo si NO hay uno ya) ------------------
# Generarlo de nuevo en cada ejecucion dejaria credenciales huerfanas en Entra
# y romperia el login hasta la siguiente revision del Container App.
$yaEnKv = az keyvault secret list --vault-name $KV `
            --query "[?name=='$SECRET_KV_NAME'] | [0].name" -o tsv
if (-not $yaEnKv) {
    $CLIENT_SECRET = az ad app credential reset --id $APP_ID --append `
                        --display-name "easyauth" --years 2 --query password -o tsv
    if (-not $CLIENT_SECRET) { throw "No pude generar el client secret." }
    az keyvault secret set --vault-name $KV --name $SECRET_KV_NAME `
        --value $CLIENT_SECRET --only-show-errors | Out-Null
    $CLIENT_SECRET = $null
    Remove-Variable CLIENT_SECRET -ErrorAction SilentlyContinue
    Write-Host "[easyauth] client secret generado y guardado en el Key Vault" -ForegroundColor Green
} else {
    Write-Host "[easyauth] client secret ya estaba en el Key Vault: se reutiliza" -ForegroundColor Yellow
}

# --- 5) Enterprise App: asignacion requerida + grupo asignado (R36) ---------
$SP_OID = az ad sp list --filter "appId eq '$APP_ID'" --query "[0].id" -o tsv
if (-not $SP_OID) {
    # La App recien creada tarda en propagarse por Entra: reintentos.
    for ($i = 1; $i -le 6 -and -not $SP_OID; $i++) {
        try { $SP_OID = az ad sp create --id $APP_ID --query id -o tsv } catch { }
        if (-not $SP_OID) { Start-Sleep -Seconds 10 }
    }
    if (-not $SP_OID) { throw "No pude crear el Service Principal de la App (propagacion de Entra)." }
    Write-Host "[easyauth] Enterprise App creada" -ForegroundColor Green
} else {
    Write-Host "[easyauth] Enterprise App ya existia" -ForegroundColor Yellow
}

az ad sp update --id $APP_ID --set appRoleAssignmentRequired=true | Out-Null
Write-Host "[easyauth] asignacion requerida = ON" -ForegroundColor Green

# appRoleId todo ceros = "acceso por defecto". Es una constante documentada de
# la plataforma, igual para todo el mundo, no un identificador nuestro.
$yaAsignado = az rest --method GET `
    --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$SP_OID/appRoleAssignedTo" `
    --query "value[?principalId=='$GROUP_ID'] | [0].id" -o tsv
if (-not $yaAsignado) {
    $cuerpo = @{
        principalId = $GROUP_ID
        resourceId  = $SP_OID
        appRoleId   = "00000000-0000-0000-0000-000000000000"
    }
    $tmp = Join-Path $env:TEMP "appRoleAssign_dedicacion.json"
    [System.IO.File]::WriteAllText($tmp, ($cuerpo | ConvertTo-Json -Compress), (New-Object System.Text.UTF8Encoding($false)))
    try {
        az rest --method POST `
            --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$SP_OID/appRoleAssignedTo" `
            --headers "Content-Type=application/json" --body "@$tmp" | Out-Null
        Write-Host "[easyauth] grupo '$GRUPO_ACCESO' asignado a la Enterprise App" -ForegroundColor Green
    } catch {
        # Asignar GRUPOS a una Enterprise App exige Entra ID P1. Sin licencia,
        # Easy Auth dejaria pasar a CUALQUIERA del tenant: no es un detalle.
        Write-Host "`n[easyauth] NO se pudo asignar el grupo a la Enterprise App." -ForegroundColor Red
        Write-Host "[easyauth] Suele ser falta de licencia Entra ID P1." -ForegroundColor Red
        Write-Host "[easyauth] MIENTRAS TANTO, cualquiera del tenant con sesion puede entrar." -ForegroundColor Red
        Write-Host "[easyauth] Salidas: conseguir la licencia, o filtrar por el claim 'groups'" -ForegroundColor Yellow
        Write-Host "[easyauth] (esta documentado en el repositorio de partes)." -ForegroundColor Yellow
    }
    Remove-Item $tmp -ErrorAction SilentlyContinue
} else {
    Write-Host "[easyauth] el grupo ya estaba asignado a la Enterprise App" -ForegroundColor Yellow
}

# --- 6) Secret del Container App + Easy Auth --------------------------------
Run-Az @("containerapp", "secret", "set", "-n", $APP_NAME, "-g", $RG,
         "--secrets", "$CA_SECRET_NAME=$(KvRef $SECRET_KV_NAME)")
Write-Host "[easyauth] secret '$CA_SECRET_NAME' anadido por referencia al Key Vault" -ForegroundColor Green

Run-Az @("containerapp", "auth", "microsoft", "update", "-n", $APP_NAME, "-g", $RG,
         "--client-id", $APP_ID,
         "--client-secret-name", $CA_SECRET_NAME,
         "--issuer", "https://login.microsoftonline.com/$TENANT/v2.0",
         "--yes")

Run-Az @("containerapp", "auth", "update", "-n", $APP_NAME, "-g", $RG,
         "--enabled", "true",
         "--redirect-provider", "azureactivedirectory",
         "--unauthenticated-client-action", "RedirectToLoginPage",
         "--yes")
Write-Host "[easyauth] login OBLIGATORIO activado" -ForegroundColor Green

# --- 7) Admin-consent, en mejor esfuerzo ------------------------------------
# Con el consent hecho, no se le pide permiso a cada usuario al entrar.
try {
    az ad app permission admin-consent --id $APP_ID 2>$null | Out-Null
    Write-Host "[easyauth] admin-consent OK" -ForegroundColor Green
} catch {
    Write-Host "[easyauth] admin-consent no aplicado (lo hara el primer usuario o un admin)" -ForegroundColor DarkYellow
}

# --- Resumen ----------------------------------------------------------------
Write-Host "`n=== Easy Auth LISTA ===" -ForegroundColor Green
Write-Host "Front  : https://$FQDN" -ForegroundColor Cyan
Write-Host "Acceso : solo miembros del grupo '$GRUPO_ACCESO'" -ForegroundColor Cyan
Write-Host "`nCOMPRUEBALO EN UNA VENTANA DE INCOGNITO (R36):" -ForegroundColor Yellow
Write-Host "  - debe pedir login de Entra;" -ForegroundColor Yellow
Write-Host "  - un usuario FUERA del grupo no debe entrar." -ForegroundColor Yellow
Write-Host "`nDar acceso a alguien mas:" -ForegroundColor Yellow
Write-Host "  .\setup_front_easyauth.ps1 -Miembros `"persona@ruesma.es`"" -ForegroundColor Yellow
Write-Host "`nY que conste: a partir de ahora /health del front NO responde a un curl" -ForegroundColor Yellow
Write-Host "anonimo, devuelve una redireccion al login. Es lo esperado (R35)." -ForegroundColor Yellow
Write-Host "`nPara la tarjeta del Portal Ruesma hacen falta la URL de arriba y el" -ForegroundColor Yellow
Write-Host "objectId del grupo. El objectId NO se escribe en el repositorio: sacalo con" -ForegroundColor Yellow
Write-Host "  az ad group show --group '$GRUPO_ACCESO' --query id -o tsv" -ForegroundColor Yellow
Write-Host "y pasalo al proyecto front-portal por el canal que uses." -ForegroundColor Yellow
