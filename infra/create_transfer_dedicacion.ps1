# infra/create_transfer_dedicacion.ps1
# Alta del Container App `ca-dedicacion-transfer`: el registro en Sigrid.
#
#     . .\00_vars_dedicacion.ps1 ; . .\00_capps_vars_dedicacion.ps1
#     .\create_transfer_dedicacion.ps1
#
# ES EL PRIMERO DE LOS TRES. La api necesita su FQDN interno para hablarle,
# y el front necesita el de la api (R27).
#
# ESTE ES EL UNICO SERVICIO CON CREDENCIAL DE ESCRITURA SOBRE EL ERP.
# Todo lo que sigue sale de ahi:
#
#   - Ingress INTERNO (R7). Su unico cliente es la api. Nadie desde Internet
#     puede disparar una escritura en Sigrid. Es una decision de seguridad,
#     no de comodidad.
#   - --allow-insecure: la api lo llama por http:// y httpx no sigue el 307
#     hacia https que devolveria el ingress. El trafico no sale del entorno.
#   - max-replicas 1, y esto NO es una palanca de coste (R4): la linea se
#     inserta con MAX(ide)+1 bajo UPDLOCK/HOLDLOCK (docs/ARCHITECTURE.md §9).
#     Dos replicas escribiendo a la vez se pisan los ide.
#   - min-replicas 1 (decision D4): el arranque en frio del transfer caeria
#     dentro del preflight, que es justo donde el usuario esta mirando.
#   - MODO PRUEBAS por defecto: OBRA_PRUEBAS_FORZAR=true. Todo va a la obra
#     0404 con la marca PRUEBA-PORC en `tex` (R9), asi que se puede limpiar.
#
# SALIR DEL MODO PRUEBAS (R10)
# ----------------------------
# Exige DOS senales explicitas: -ModoProduccion y -Confirmar. El valor por
# defecto de este script es, y sigue siendo, modo pruebas. Que el script lo
# permita NO autoriza el cambio: es una decision del humano, posterior a esta
# feature y para una accion concreta (CLAUDE.md, reglas duras).

param(
    # Desvia el servicio a PRODUCCION: cada linea a su obra real en Sigrid.
    [switch] $ModoProduccion,

    # Segunda senal. Sin ella, -ModoProduccion no basta.
    [switch] $Confirmar
)

$ErrorActionPreference = "Stop"
$env:AZURE_CORE_ONLY_SHOW_ERRORS = "true"

foreach ($v in @('MI_ID', 'IMG', 'APPS', 'KV_URI', 'SIGRID_URL')) {
    if (-not (Get-Variable -Name $v -ValueOnly -ErrorAction SilentlyContinue)) {
        throw "Falta `$$v. Haz:  . .\00_vars_dedicacion.ps1 ; . .\00_capps_vars_dedicacion.ps1"
    }
}
az account set --subscription $SUBSCRIPTION | Out-Null

$APP = $APPS["transfer"]

# --- Modo pruebas / produccion: la doble confirmacion de R10 ----------------
$OBRA_PRUEBAS = "true"
if ($ModoProduccion) {
    Write-Host "`n############################################################" -ForegroundColor Red
    Write-Host "# MODO PRODUCCION: cada linea se escribira en SU OBRA REAL  #" -ForegroundColor Red
    Write-Host "# de Sigrid, en la base 'ruesma'. Eso NO se puede deshacer   #" -ForegroundColor Red
    Write-Host "# con el script de limpieza, que solo borra lo marcado       #" -ForegroundColor Red
    Write-Host "# PRUEBA-PORC.                                              #" -ForegroundColor Red
    Write-Host "############################################################" -ForegroundColor Red
    if (-not $Confirmar) {
        Write-Host "`nABORTADO: falta la segunda senal. Si de verdad es lo que quieres:" -ForegroundColor Red
        Write-Host "  .\create_transfer_dedicacion.ps1 -ModoProduccion -Confirmar" -ForegroundColor Yellow
        Write-Host "`nY antes de eso, que conste: salir del modo pruebas es una decision" -ForegroundColor Yellow
        Write-Host "del humano para una accion concreta, no un paso del despliegue." -ForegroundColor Yellow
        exit 1
    }
    $OBRA_PRUEBAS = "false"
} else {
    Write-Host "`n=== transfer (registro en Sigrid, ingress INTERNO) ===" -ForegroundColor Green
    Write-Host "  MODO PRUEBAS: todo se desviara a la obra 0404 con la marca PRUEBA-PORC." -ForegroundColor Cyan
    Write-Host "  Es lo correcto: F-008 termina con el transfer en modo pruebas (R9)." -ForegroundColor Cyan
}

if (App-Existe $APP) {
    throw "El Container App '$APP' ya existe. Para republicar: .\redeploy_dedicacion.ps1 -Solo transfer"
}

# --- Secretos: SOLO referencias a Key Vault (R19) ---------------------------
$secretos = @(
    "sigrid-key=$(KvRef 'SIGRID-API-FUNCTION-KEY')"
)

$entorno = @(
    # uvicorn tiene que escuchar en 0.0.0.0 DENTRO del contenedor.
    "API_HOST=0.0.0.0", "API_PORT=$($PUERTOS['transfer'])",
    # /app no tiene por que ser escribible; el arranque escribe log de fichero.
    "LOG_DIR=/tmp/logs", "LOG_LEVEL=INFO",

    # --- Sigrid CON ESCRITURA: solo la base real 'ruesma' -------------------
    # La replica ruesma_rep no admite escritura. El valor de la clave no
    # aparece aqui: viaja por referencia al Key Vault.
    "SIGRID_API_BASE_URL=$SIGRID_URL",
    "SIGRID_API_FUNCTION_KEY=secretref:sigrid-key",
    "SIGRID_API_DATABASE=$SIGRID_DB",
    "SIGRID_EMPRESA=1",
    "SIGRID_API_TIMEOUT_S=$TIMEOUT_TRANSFER_SIGRID",

    # --- Modo pruebas (R9) --------------------------------------------------
    "OBRA_PRUEBAS_FORZAR=$OBRA_PRUEBAS",
    "OBRA_PRUEBAS_COD=0404",
    "MARCA_PRUEBAS=PRUEBA-PORC",

    # --- Postventa: la dedicacion de postventa va a su obra ----------------
    "POSTVENTA_REGISTRAR=true",
    "POSTVENTA_OBRA_COD=POSTV2"
)

$argumentos = @(
    "containerapp", "create", "-n", $APP, "-g", $RG, "--environment", $CAE,
    "--image", (Imagen "transfer"),
    "--registry-server", $ACR_LOGIN, "--registry-identity", $MI_ID,
    "--user-assigned", $MI_ID,
    "--min-replicas", "$MIN_REPLICAS", "--max-replicas", "$MAX_REPLICAS",
    "--cpu", "0.5", "--memory", "1.0Gi",
    "--ingress", "internal", "--target-port", "$($PUERTOS['transfer'])",
    "--transport", "auto",
    "--secrets") + $secretos + @("--env-vars") + $entorno + @("--tags") + $TAGS
Run-Az $argumentos

# HTTP plano dentro del entorno: la api lo llama por http://.
Run-Az @("containerapp", "ingress", "update", "-n", $APP, "-g", $RG, "--allow-insecure", "true")

$FQDN = Fqdn-Interno "transfer"

Write-Host "`n=== $APP creado ===" -ForegroundColor Green
az containerapp show -n $APP -g $RG `
    --query "{Estado:properties.provisioningState, Min:properties.template.scale.minReplicas, Max:properties.template.scale.maxReplicas, Externo:properties.configuration.ingress.external, FQDN:properties.configuration.ingress.fqdn}" `
    -o table

Write-Host "`nURL interna (la consume la api):  http://$FQDN" -ForegroundColor Cyan
Write-Host "No hay URL publica, y es deliberado: este servicio es la unica pluma sobre el ERP." -ForegroundColor Cyan

Write-Host "`nComprueba el modo pruebas (R9):" -ForegroundColor Yellow
Write-Host "  az containerapp show -n $APP -g $RG --query `"properties.template.containers[0].env[?name=='OBRA_PRUEBAS_FORZAR'].value`" -o tsv" -ForegroundColor Yellow
Write-Host "Logs del arranque:" -ForegroundColor Yellow
Write-Host "  az containerapp logs show -n $APP -g $RG --tail 60" -ForegroundColor Yellow

if ($OBRA_PRUEBAS -ne "true") {
    Write-Host "`nAVISO: este servicio escribe EN PRODUCCION en Sigrid (base 'ruesma')." -ForegroundColor Red
} else {
    Write-Host "`nSIGUIENTE:  .\create_api_dedicacion.ps1" -ForegroundColor Yellow
}
