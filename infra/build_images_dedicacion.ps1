# infra/build_images_dedicacion.ps1
# Construye las imagenes de DEDICACION con `az acr build` (sin Docker local)
# y las publica en el ACR compartido `acralbaranesdev` con TAG FECHADO.
#
# Uso:
#     . .\00_vars_dedicacion.ps1
#     .\build_images_dedicacion.ps1                     # los tres servicios
#     .\build_images_dedicacion.ps1 -Solo api,front     # solo esos
#
# Requisito: az login con AcrPush sobre 'acralbaranesdev'. El usuario admin
# del registro esta DESHABILITADO en la suscripcion: se entra con tu identidad.
#
# POR QUE TAG FECHADO Y NO 'latest' (R23)
# ---------------------------------------
# docs/CONVENTIONS.md es explicito: imagenes con tag rAAAAMMDD-HHmm, nunca
# reescribir un tag ya publicado. Aqui nos separamos a proposito del patron de
# `partes`, que usa 'latest' y por eso necesita --revision-suffix para forzar
# el pull y no puede responder "que codigo esta corriendo" sin abrir Azure.
#
# El tag publicado se escribe en infra/imagenes.json, que SI se versiona: es
# un fichero de tags, no de secretos, y es lo que hace que esa pregunta se
# responda desde git (R24). Metelo en el commit del despliegue.

param(
    # Servicios a construir. Sin este parametro, los tres.
    [ValidateSet("transfer", "api", "front")]
    [string[]] $Solo = @("transfer", "api", "front"),

    # Construye el contexto y para antes de llamar a `az acr build`. Sirve
    # para ver QUE se subiria sin subir nada ni gastar un minuto de ACR.
    [switch] $Simular
)

$ErrorActionPreference = "Stop"
if (-not $ACR) { throw "Falta `$ACR. Haz primero:  . .\00_vars_dedicacion.ps1" }
if (-not $IMG) { throw "Falta `$IMG (mapa de imagenes). Haz primero:  . .\00_vars_dedicacion.ps1" }
if (-not $SRC) { throw "Falta `$SRC (carpetas de codigo). Haz primero:  . .\00_vars_dedicacion.ps1" }

$INVENTARIO = Join-Path $PSScriptRoot "imagenes.json"
if (-not (Test-Path $INVENTARIO)) { throw "No encuentro $INVENTARIO (deberia estar versionado)." }

# UN solo tag por ejecucion: los servicios que se construyan a la vez quedan
# con el mismo sello temporal y se sabe de un vistazo que van juntos.
$TAG = "r" + (Get-Date -Format "yyyyMMdd-HHmm")
$AHORA = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"

if (-not $Simular) { az account set --subscription $SUBSCRIPTION }

Write-Host "`n=== Build de DEDICACION ===" -ForegroundColor Cyan
Write-Host "  Registro : $ACR"
Write-Host "  Tag      : $TAG   (fechado; NUNCA se reescribe un tag publicado)"
Write-Host "  Servicios: $($Solo -join ', ')"
if ($Simular) { Write-Host "  MODO SIMULACION: se prepara el contexto y NO se sube nada" -ForegroundColor Yellow }

$construidos = @{}

foreach ($svc in $Solo) {
    $repo = $IMG[$svc]
    $dir  = Join-Path $PSScriptRoot $SRC[$svc]
    if (-not $repo) { throw "No hay entrada '$svc' en `$IMG (00_vars_dedicacion.ps1)." }
    if (-not (Test-Path $dir)) { throw "No existe la carpeta de codigo de '$svc': $dir" }
    if (-not (Test-Path (Join-Path $dir "Dockerfile"))) {
        throw "El servicio '$svc' no tiene Dockerfile. Sin el no hay imagen que desplegar."
    }

    # --- Un tag publicado no se reescribe JAMAS (R23) ----------------------
    if (-not $Simular) {
        # La PRIMERA vez el repositorio no existe en el registro y `show-tags`
        # falla; con ErrorActionPreference="Stop" eso abortaria el build.
        # No poder listar tags equivale a que el tag no esta publicado.
        $yaEsta = $null
        try   { $yaEsta = az acr repository show-tags -n $ACR --repository $repo --query "[?@=='$TAG']" -o tsv }
        catch { $yaEsta = $null }
        if ($yaEsta) {
            throw "El tag '$TAG' ya existe en '$repo'. Un tag publicado no se reescribe: espera al minuto siguiente y relanza."
        }
    }

    Write-Host "`n--- $svc  ($repo`:$TAG) ---" -ForegroundColor Green
    $rand = [guid]::NewGuid().ToString("N").Substring(0, 8)
    $ctx  = Join-Path $env:TEMP "acrbuild_dedicacion_${svc}_$rand"
    New-Item -ItemType Directory -Path $ctx | Out-Null
    try {
        # 1) Codigo del servicio -> contexto temporal, sin pesados ni basura.
        #    El .env queda fuera por partida doble: aqui y en el .dockerignore
        #    del propio servicio (R25). Lleva la function key de sigrid-api,
        #    que es la credencial de ESCRITURA sobre el ERP.
        robocopy $dir $ctx /E `
            /XD .venv .git .idea __pycache__ .pytest_cache .ruff_cache logs tests `
            /XF *.log *.pyc .env *.env *.zip coverage.json .coverage /NFL /NDL /NJH /NJS /NP | Out-Null
        if ($LASTEXITCODE -ge 8) { throw "robocopy fallo copiando $dir (code $LASTEXITCODE)" }
        $global:LASTEXITCODE = 0   # robocopy: 0-7 son exito

        if (Test-Path (Join-Path $ctx ".env")) {
            throw "ABORTADO: el .env de '$svc' se ha colado en el contexto de build."
        }

        # 2) Build en el ACR (sin Docker local). El Dockerfile y el
        #    .dockerignore son los del propio servicio: es donde deben estar,
        #    y por eso aqui no hace falta la carpeta manifests/ de `partes`.
        if ($Simular) {
            Write-Host "  (simulacion) contexto listo en $ctx" -ForegroundColor Yellow
            Get-ChildItem $ctx | Select-Object -ExpandProperty Name | ForEach-Object { Write-Host "    $_" }
        } else {
            Push-Location $ctx
            az acr build --registry $ACR --image "${repo}:${TAG}" .
            $code = $LASTEXITCODE
            Pop-Location
            if ($code -ne 0) { throw "Build de '$svc' FALLO (exit $code). Revisa el log de ACR." }
            Write-Host "OK $svc -> $ACR.azurecr.io/${repo}:${TAG}" -ForegroundColor Green
            $construidos[$repo] = $TAG
        }
    }
    finally {
        if (Test-Path $ctx) { Remove-Item -Recurse -Force $ctx -ErrorAction SilentlyContinue }
    }
}

# --- Inventario versionado: que tag se publico y cuando (R24) --------------
if ($construidos.Count -gt 0) {
    $inventario = Get-Content $INVENTARIO -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($repo in $construidos.Keys) {
        $entrada = $inventario.servicios.$repo
        if (-not $entrada) { throw "imagenes.json no tiene entrada para '$repo'." }
        $entrada.tag = $construidos[$repo]
        $entrada.publicado = $AHORA
        if ($entrada.PSObject.Properties.Name -contains "nota") {
            $entrada.nota = "Publicado por build_images_dedicacion.ps1."
        }
    }
    # Sin BOM y con LF: .gitattributes declara *.json eol=lf.
    $json = ($inventario | ConvertTo-Json -Depth 6).Replace("`r`n", "`n") + "`n"
    # El encoding se construye ANTES: en PS 5.1, un `New-Object` anidado como
    # argumento de un metodo estatico no resuelve, y la llamada falla con
    # "No se encuentra ninguna sobrecarga para WriteAllText y el numero de
    # argumentos 3". Con la variable aparte, la sobrecarga (String, String,
    # Encoding) se resuelve sin problema.
    $sinBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText([string]$INVENTARIO, [string]$json, $sinBom)

    Write-Host "`n=== infra/imagenes.json actualizado ===" -ForegroundColor Green
    foreach ($repo in $construidos.Keys) { Write-Host ("  {0,-22} {1}" -f $repo, $construidos[$repo]) }
    Write-Host "`nMETELO EN EL COMMIT: es lo que responde 'que codigo esta corriendo' sin abrir Azure." -ForegroundColor Yellow
}

Write-Host "`nSiguiente (primera vez, y en este orden):" -ForegroundColor Yellow
Write-Host "  .\create_transfer_dedicacion.ps1 ; .\create_api_dedicacion.ps1 ; .\create_front_dedicacion.ps1" -ForegroundColor Yellow
Write-Host "Para republicar algo ya dado de alta:  .\redeploy_dedicacion.ps1 -Solo api" -ForegroundColor Yellow
