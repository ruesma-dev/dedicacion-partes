# infra/add_secrets_dedicacion.ps1
# Carga en el Key Vault de DEDICACION los tres secretos de la aplicacion,
# pedidos de forma SEGURA: no se escriben en disco, no se imprimen y no
# quedan en el historial de la consola.
#
# Uso:
#     . .\00_vars_dedicacion.ps1
#     .\add_secrets_dedicacion.ps1                 # los pide todos
#     .\add_secrets_dedicacion.ps1 -Solo PG-PASSWORD
#
# Correlo DESPUES de fase1_infra_dedicacion.ps1 (que crea el Key Vault y te
# da el rol para escribir en el) y de crear_base_dedicacion.ps1 (que es donde
# eliges la contrasena del rol de aplicacion).
#
# COMO LOS CONSUME LA APLICACION (R19)
# ------------------------------------
# Ninguno de estos valores viaja como valor en la definicion del Container
# App, ni en un .env, ni dentro de la imagen. Cada Container App declara un
# secret que es una REFERENCIA a este Key Vault (keyvaultref) leida con la
# identidad gestionada, y la variable de entorno apunta a ese secret
# (secretref). Cambiar un secreto aqui y crear una revision nueva basta: no
# hay que reconstruir ninguna imagen.
#
# LO QUE NO SE GUARDA AQUI, Y ES DELIBERADO
# -----------------------------------------
# La contrasena del ADMINISTRADOR de PostgreSQL. No entra en este Key Vault
# ni en ningun otro sitio nuestro. Con AUTO_CREATE_DATABASE=false el servicio
# no la necesita (R13-R15): la base y el rol ya existen, creados una vez por
# una persona. La usa esa persona, en su sesion, al correr
# crear_base_dedicacion.ps1, y ahi se acaba. Lo que no se guarda, no se filtra.
#
# `partes` desplego con PG_USER=<admin del servidor>, y eso puso la contrasena
# del administrador de un servidor COMPARTIDO dentro de tres contenedores.
# Aqui no se repite.

param(
    [ValidateSet("PG-PASSWORD", "SIGRID-API-FUNCTION-KEY", "EASYAUTH-CLIENT-SECRET")]
    [string[]] $Solo = @("PG-PASSWORD", "SIGRID-API-FUNCTION-KEY", "EASYAUTH-CLIENT-SECRET")
)

$ErrorActionPreference = "Stop"
if (-not $KV) { throw "Falta `$KV. Haz primero:  . .\00_vars_dedicacion.ps1" }

# Nombre en Key Vault -> que es y quien lo consume.
$secretos = [ordered]@{
    "PG-PASSWORD" = "contrasena del rol de aplicacion '$PG_APP_USER' en '$PG' (la que elegiste en crear_base_dedicacion.ps1). La consume: api. NO es la del administrador del servidor."
    "SIGRID-API-FUNCTION-KEY" = "function key de sigrid-api. La consumen: api (lectura de maestros) y transfer (ESCRITURA en la base 'ruesma')."
    "EASYAUTH-CLIENT-SECRET" = "client secret de la App Registration del front. Lo genera y lo guarda solo setup_front_easyauth.ps1: aqui solo hace falta si lo estas rotando a mano."
}

Write-Host "`n=== Secretos de DEDICACION -> Key Vault $KV ===" -ForegroundColor Cyan
Write-Host "Ninguno se escribe en disco ni se imprime. Vacio = saltar." -ForegroundColor DarkGray

# Aviso util sobre D5, que sigue sin cerrar: hoy api y transfer referencian la
# MISMA function key. Lo unico que impide que la api escriba en el ERP es que
# su codigo no tiene rutas de escritura, no la credencial. Si sigrid-api
# admite claves distintas por consumidor, la api deberia llevar una de solo
# lectura. Es una pregunta para el dueno de ese proyecto.
Write-Host "`nAVISO (decision D5, abierta): la api y el transfer comparten la misma" -ForegroundColor Yellow
Write-Host "function key de sigrid-api. Lo que impide hoy que la api escriba en el ERP" -ForegroundColor Yellow
Write-Host "es que su codigo no tiene rutas de escritura, NO la credencial. Si sigrid-api" -ForegroundColor Yellow
Write-Host "puede dar una clave de solo lectura, pidesela y usala para la api." -ForegroundColor Yellow

$guardados = @()
foreach ($nombre in $Solo) {
    Write-Host "`n$nombre" -ForegroundColor Cyan
    Write-Host "  $($secretos[$nombre])" -ForegroundColor DarkGray

    $yaEsta = az keyvault secret list --vault-name $KV --query "[?name=='$nombre'] | [0].name" -o tsv 2>$null
    if ($yaEsta) {
        Write-Host "  Ya existe en el Key Vault. Dejalo vacio para conservarlo; escribe un valor solo si lo estas ROTANDO." -ForegroundColor Yellow
    }

    $sec = Read-Host "  Pega el valor (vacio = saltar)" -AsSecureString
    $val = [System.Net.NetworkCredential]::new("", $sec).Password
    if ([string]::IsNullOrWhiteSpace($val)) {
        Write-Host "  (saltado)" -ForegroundColor DarkGray
        continue
    }

    az keyvault secret set --vault-name $KV --name $nombre --value $val --only-show-errors | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "No pude guardar '$nombre' en '$KV'. Tienes el rol 'Key Vault Secrets Officer'?" }
    Write-Host "  OK guardado en $KV" -ForegroundColor Green
    $guardados += $nombre

    # Que no se quede en memoria mas de lo necesario.
    $val = $null
    Remove-Variable val -ErrorAction SilentlyContinue
}

Write-Host "`n=== Secretos presentes en $KV ===" -ForegroundColor Green
az keyvault secret list --vault-name $KV --query "[].name" -o tsv

if ($guardados.Count -gt 0) {
    Write-Host "`nSi has ROTADO un secreto de un servicio ya desplegado, hace falta una" -ForegroundColor Yellow
    Write-Host "revision nueva para que lo relea:  .\redeploy_dedicacion.ps1 -Solo <servicio> -SinBuild" -ForegroundColor Yellow
}
