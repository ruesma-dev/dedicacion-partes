# infra/vaciar_datos_prueba_dedicacion.ps1
# Vacia los DATOS DE PRUEBA de la base `dedicacion` (F-026, decision D1).
# LO EJECUTA UNA PERSONA, con autorizacion expresa, en el despliegue de F-026
# y ANTES del primer sync (infra/README_dedicacion.md, paso F-026).
#
#     . .\00_vars_dedicacion.ps1 ; . .\00_vars_dedicacion.local.ps1
#     .\vaciar_datos_prueba_dedicacion.ps1                   # PLAN, no conecta
#     .\vaciar_datos_prueba_dedicacion.ps1 -Confirmar        # ejecuta en Azure
#     .\vaciar_datos_prueba_dedicacion.ps1 -Local            # PLAN en local
#     .\vaciar_datos_prueba_dedicacion.ps1 -Local -Confirmar # ejecuta en local
#
# POR QUE
# -------
# Desde F-026 la clave del trabajador es el `res.ide` del RECURSO de Sigrid,
# no el `emp.ide` de su ficha de empleado. Lo que hay hoy en la base son
# pruebas ("no hace falta migrarlo", decision del humano del 2026-10-02): se
# vacian las cuatro tablas que cuelgan del trabajador y el primer sync lo
# vuelve a llenar con la clave nueva.
#
# QUE HACE: UNA sentencia, la de $SENTENCIA, en la base `dedicacion` y nada
# mas. Antes y despues cuenta las filas (solo lectura).
#   - CONTINUE IDENTITY, a proposito: las secuencias siguen donde estaban. Si
#     volvieran a empezar, un `asignacion.id` nuevo reutilizaria la synckey
#     `porcentajes:{id}` de una linea de prueba YA escrita en Sigrid (obra de
#     pruebas 0404) y el transfer la daria por ya registrada (R11).
#   - Las cuatro tablas van en la MISMA sentencia: asi las claves ajenas entre
#     ellas no obligan a vaciar en cascada ninguna otra.
#
# QUE NO HACE, Y ES DELIBERADO (R10)
# ---------------------------------
#   - No toca los maestros de obras ni de empresas: no cuelgan del trabajador.
#   - No borra tablas, no reinicia secuencias, no cambia el esquema.
#   - Nada a nivel de servidor: `psql-albaranes-rs9k2` es COMPARTIDO con
#     albaranes, partes, datamart-seg-anual y postventa.
#   - No pide la contrasena del administrador del servidor: basta la del rol
#     de aplicacion ($PG_APP_USER), que tiene GRANT ALL sobre nuestras tablas.
#   - La contrasena se pide con Read-Host -AsSecureString y no se escribe en
#     ningun fichero.

param(
    # Sin este conmutador el script solo IMPRIME el plan, sin conectar.
    [switch] $Confirmar,
    # Contra la base local (localhost/dedicacion, con psql) en vez de Azure.
    [switch] $Local
)

$ErrorActionPreference = "Stop"

# La UNICA sentencia de escritura. Se imprime en el plan y se ejecuta tal cual.
$SENTENCIA = "TRUNCATE TABLE asignacion, evento, periodo, trabajador CONTINUE IDENTITY"
# Recuento de solo lectura, antes y despues. Una sola sentencia, sin `;`.
$RECUENTO = "SELECT (SELECT COUNT(*) FROM asignacion) AS asignacion, (SELECT COUNT(*) FROM evento) AS evento, (SELECT COUNT(*) FROM periodo) AS periodo, (SELECT COUNT(*) FROM trabajador) AS trabajador"

if ($Local) {
    $DESTINO = "localhost/dedicacion (base LOCAL)"
} else {
    if (-not $PG) { throw "Falta `$PG. Haz primero:  . .\00_vars_dedicacion.ps1" }
    $DESTINO = "$PG/$PG_DB (Azure, servidor COMPARTIDO)"
}

function Section($t) { Write-Host "`n=== $t ===" -ForegroundColor Green }

# --- 0) El plan, siempre ----------------------------------------------------
Write-Host "`n============================================================" -ForegroundColor Yellow
Write-Host " VACIADO DE DATOS DE PRUEBA (F-026, D1)" -ForegroundColor Yellow
Write-Host " DESTINO: $DESTINO" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "`nPLAN:"
Write-Host "  1. Contar las filas de asignacion, evento, periodo y trabajador."
Write-Host "  2. Ejecutar UNA sentencia, y ninguna mas:"
Write-Host "       $SENTENCIA"
Write-Host "  3. Volver a contar (esperado: 0 en las cuatro)."
Write-Host "`nNO se toca: las tablas obra y empresa, ninguna otra base, ni nada" -ForegroundColor Cyan
Write-Host "del servidor. Las secuencias se conservan (CONTINUE IDENTITY)." -ForegroundColor Cyan

if (-not $Confirmar) {
    Write-Host "`nEsto ha sido el PLAN: no se ha conectado a nada. Para ejecutarlo:" -ForegroundColor Yellow
    if ($Local) {
        Write-Host "  .\vaciar_datos_prueba_dedicacion.ps1 -Local -Confirmar" -ForegroundColor Yellow
    } else {
        Write-Host "  .\vaciar_datos_prueba_dedicacion.ps1 -Confirmar" -ForegroundColor Yellow
    }
    return
}

# --- 1) Credenciales, en memoria y solo durante esta sesion -----------------
Section "1) Credenciales"
if ($Local) {
    if (-not (Get-Command psql -ErrorAction SilentlyContinue)) {
        throw "No encuentro psql en el PATH: instala el cliente de PostgreSQL (o anade su carpeta bin al PATH) y vuelve a lanzarlo."
    }
    $USUARIO = if ($env:PGUSER) { $env:PGUSER } else { "postgres" }
    $sec = Read-Host "  Contrasena del usuario '$USUARIO' en localhost" -AsSecureString
} else {
    $USUARIO = $PG_APP_USER
    $sec = Read-Host "  Contrasena del rol de aplicacion '$PG_APP_USER' (la de PG-PASSWORD)" -AsSecureString
}
$CLAVE = [System.Net.NetworkCredential]::new("", $sec).Password
if ([string]::IsNullOrWhiteSpace($CLAVE)) { throw "Sin contrasena no se conecta." }

function Ejecutar-Sql($sql) {
    # UNA sentencia por llamada y sin `;`: `az ... --querytext` trocea por `;`.
    # El ErrorActionPreference se relaja solo aqui, como en
    # crear_base_dedicacion.ps1: en PS 5.1 el stderr de un ejecutable nativo
    # con "Stop" seria un error terminante sin mensaje que inspeccionar.
    $anterior = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        if ($Local) {
            $env:PGPASSWORD = $CLAVE
            $salida = psql -h localhost -d dedicacion -U $USUARIO -v ON_ERROR_STOP=1 -c $sql 2>&1 | Out-String
        } else {
            $salida = az postgres flexible-server execute -n $PG -u $PG_APP_USER -p $CLAVE -d $PG_DB --querytext $sql --only-show-errors 2>&1 | Out-String
        }
        $codigo = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $anterior
        Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
    }
    if ($codigo -ne 0) { throw "Fallo ejecutando SQL en ${DESTINO}:`n$salida" }
    return $salida
}

if (-not $Local) {
    az account set --subscription $SUBSCRIPTION | Out-Null
    az extension add --name rdbms-connect --upgrade --only-show-errors | Out-Null
}

# --- 2) Antes ---------------------------------------------------------------
Section "2) Filas antes del vaciado"
Write-Host (Ejecutar-Sql $RECUENTO)

# --- 3) La sentencia --------------------------------------------------------
Section "3) Vaciado"
Ejecutar-Sql $SENTENCIA | Out-Null
Write-Host "  Ejecutada: $SENTENCIA" -ForegroundColor Green

# --- 4) Despues -------------------------------------------------------------
Section "4) Filas despues (esperado: 0 en las cuatro)"
Write-Host (Ejecutar-Sql $RECUENTO)

Section "HECHO"
Write-Host "Destino: $DESTINO"
Write-Host "`nSIGUIENTE (infra/README_dedicacion.md, paso F-026):" -ForegroundColor Yellow
Write-Host "  GET  /api/v1/sync/preview   y revisar empleados.ventana_baja" -ForegroundColor Yellow
Write-Host "  POST /api/v1/sync           antes de registrar nada" -ForegroundColor Yellow
