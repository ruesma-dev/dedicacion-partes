# infra/vaciar_datos_prueba_dedicacion.ps1
# Vacia los DATOS DE PRUEBA de la base `dedicacion` (F-026, decision D1).
# LO EJECUTA UNA PERSONA, con autorizacion expresa, en el despliegue de F-026
# y ANTES del primer sync (infra/README_dedicacion.md, paso F-026).
#
#     $env:Path = "C:\Program Files\PostgreSQL\16\bin;$env:Path"   # si psql no esta
#     . .\00_vars_dedicacion.ps1 ; . .\00_vars_dedicacion.local.ps1
#     .\vaciar_datos_prueba_dedicacion.ps1                       # PLAN, no conecta
#     .\vaciar_datos_prueba_dedicacion.ps1 -SoloRecuento         # cuenta en Azure, no escribe
#     .\vaciar_datos_prueba_dedicacion.ps1 -Confirmar            # ejecuta en Azure
#     .\vaciar_datos_prueba_dedicacion.ps1 -Local                # PLAN en local
#     .\vaciar_datos_prueba_dedicacion.ps1 -Local -SoloRecuento  # cuenta en local, no escribe
#     .\vaciar_datos_prueba_dedicacion.ps1 -Local -Confirmar     # ejecuta en local
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
# CON psql TAMBIEN EN AZURE (F-035)
# ---------------------------------
# Hasta F-035 la rama de Azure usaba `az postgres flexible-server` con la
# contrasena como ARGUMENTO. En Windows `az` es un .cmd: su linea de comandos
# la interpreta cmd.exe, que se come o reinterpreta " & | < > ^ % y la
# contrasena le llegaba corrompida a PostgreSQL ("password authentication
# failed" con la contrasena buena). psql es un .exe y la contrasena le llega
# por el entorno (PGPASSWORD), nunca por la linea de comandos. Por eso psql
# hace falta en los dos modos, y en Azure ademas que el servidor admita
# conexiones desde TU IP.
#
# QUE NO HACE, Y ES DELIBERADO (R10)
# ---------------------------------
#   - No toca los maestros de obras ni de empresas: no cuelgan del trabajador.
#   - No borra tablas, no reinicia secuencias, no cambia el esquema.
#   - Nada a nivel de servidor: `psql-albaranes-rs9k2` es COMPARTIDO con
#     albaranes, partes, datamart-seg-anual y postventa. Tampoco abre el
#     acceso de tu IP: si falta, lo dice y para.
#   - No pide la contrasena del administrador del servidor: basta la del rol
#     de aplicacion ($PG_APP_USER), que tiene GRANT ALL sobre nuestras tablas.
#   - La contrasena se pide con Read-Host -AsSecureString, no se escribe en
#     ningun fichero y solo esta en el entorno (PGPASSWORD) durante cada
#     llamada a psql.

param(
    # Sin este conmutador (ni -SoloRecuento) el script solo IMPRIME el plan.
    [switch] $Confirmar,
    # Contra la base local (localhost/dedicacion) en vez de Azure.
    [switch] $Local,
    # Solo lectura: pide la contrasena, cuenta las filas y sale sin vaciar.
    [switch] $SoloRecuento
)

$ErrorActionPreference = "Stop"

# Uno escribe y el otro solo lee: juntos no se sabe que se queria. Se para
# antes de conectar a nada.
if ($Confirmar -and $SoloRecuento) {
    throw "-Confirmar y -SoloRecuento se excluyen: -SoloRecuento solo cuenta y -Confirmar vacia. Lanza uno de los dos."
}

# La UNICA sentencia de escritura. Se imprime en el plan y se ejecuta tal cual.
$SENTENCIA = "TRUNCATE TABLE asignacion, evento, periodo, trabajador CONTINUE IDENTITY"
# Recuento de solo lectura, antes y despues. Una sola sentencia, sin `;`.
$RECUENTO = "SELECT (SELECT COUNT(*) FROM asignacion) AS asignacion, (SELECT COUNT(*) FROM evento) AS evento, (SELECT COUNT(*) FROM periodo) AS periodo, (SELECT COUNT(*) FROM trabajador) AS trabajador"

if ($Local) {
    $DESTINO = "localhost/dedicacion (base LOCAL)"
    $MODO = "-Local "
} else {
    if (-not $PG) { throw "Falta `$PG. Haz primero:  . .\00_vars_dedicacion.ps1" }
    $DESTINO = "$PG/$PG_DB (Azure, servidor COMPARTIDO)"
    $MODO = ""
}

function Section($t) { Write-Host "`n=== $t ===" -ForegroundColor Green }

# --- 0) El plan, siempre ----------------------------------------------------
Write-Host "`n============================================================" -ForegroundColor Yellow
Write-Host " VACIADO DE DATOS DE PRUEBA (F-026, D1)" -ForegroundColor Yellow
Write-Host " DESTINO: $DESTINO" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "`nPLAN:"
if ($SoloRecuento) {
    Write-Host "  -SoloRecuento: SOLO LECTURA."
    Write-Host "  1. Contar las filas de asignacion, evento, periodo y trabajador."
    Write-Host "  2. Salir. NO se ejecuta la sentencia de vaciado:"
    Write-Host "       $SENTENCIA"
} else {
    Write-Host "  1. Contar las filas de asignacion, evento, periodo y trabajador."
    Write-Host "  2. Ejecutar UNA sentencia, y ninguna mas:"
    Write-Host "       $SENTENCIA"
    Write-Host "  3. Volver a contar (esperado: 0 en las cuatro)."
}
Write-Host "`nNO se toca: las tablas obra y empresa, ninguna otra base, ni nada" -ForegroundColor Cyan
Write-Host "del servidor. Las secuencias se conservan (CONTINUE IDENTITY)." -ForegroundColor Cyan
Write-Host "Se conecta con psql (tambien en Azure): la contrasena va por el entorno," -ForegroundColor Cyan
Write-Host "nunca por la linea de comandos (F-035)." -ForegroundColor Cyan

# Sin -Confirmar ni -SoloRecuento, aqui se acaba: no se ha conectado a nada.
if (-not $Confirmar -and -not $SoloRecuento) {
    Write-Host "`nEsto ha sido el PLAN: no se ha conectado a nada." -ForegroundColor Yellow
    Write-Host "  Para solo contar las filas, sin escribir nada:" -ForegroundColor Yellow
    Write-Host "    .\vaciar_datos_prueba_dedicacion.ps1 $($MODO)-SoloRecuento" -ForegroundColor Yellow
    Write-Host "  Para ejecutarlo:" -ForegroundColor Yellow
    Write-Host "    .\vaciar_datos_prueba_dedicacion.ps1 $($MODO)-Confirmar" -ForegroundColor Yellow
    return
}

# --- 1) Conexion: psql y, en Azure, el FQDN del servidor --------------------
Section "1) Conexion"
# psql hace falta en los DOS modos (ver la cabecera: en Azure tambien).
if (-not (Get-Command psql -ErrorAction SilentlyContinue)) {
    throw "No encuentro psql en el PATH: instala el cliente de PostgreSQL o anade su carpeta bin al PATH (por ejemplo:  `$env:Path = `"C:\Program Files\PostgreSQL\16\bin;`$env:Path`") y vuelve a lanzarlo."
}
if (-not $Local) {
    az account set --subscription $SUBSCRIPTION | Out-Null
    # Solo lectura: pregunta el nombre DNS del servidor, no lo modifica.
    $PG_FQDN = az postgres flexible-server show -n $PG -g $PG_RG --query fullyQualifiedDomainName -o tsv
    if ([string]::IsNullOrWhiteSpace($PG_FQDN)) {
        throw "No encuentro el servidor '$PG' en '$PG_RG': revisa 00_vars_dedicacion.ps1 y que hayas hecho az login."
    }
    $PG_FQDN = $PG_FQDN.Trim()
    Write-Host "  Servidor: $PG_FQDN (psql con PGSSLMODE=require)"
}

# --- 2) Credenciales, en memoria y solo durante esta sesion -----------------
Section "2) Credenciales"
if ($Local) {
    $USUARIO = if ($env:PGUSER) { $env:PGUSER } else { "postgres" }
    $sec = Read-Host "  Contrasena del usuario '$USUARIO' en localhost" -AsSecureString
} else {
    $USUARIO = $PG_APP_USER
    $sec = Read-Host "  Contrasena del rol de aplicacion '$PG_APP_USER' (la de PG-PASSWORD)" -AsSecureString
}
$CLAVE = [System.Net.NetworkCredential]::new("", $sec).Password
if ([string]::IsNullOrWhiteSpace($CLAVE)) { throw "Sin contrasena no se conecta." }

function Ejecutar-Sql($sql) {
    # UNA sentencia por llamada. La contrasena va en PGPASSWORD (y en Azure el
    # cifrado obligatorio en PGSSLMODE) SOLO mientras dura la llamada: el
    # finally las borra pase lo que pase.
    # El ErrorActionPreference se relaja solo aqui, como en
    # crear_base_dedicacion.ps1: en PS 5.1 el stderr de un ejecutable nativo
    # con "Stop" seria un error terminante sin mensaje que inspeccionar.
    $anterior = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $env:PGPASSWORD = $CLAVE
        if ($Local) {
            $salida = psql -h localhost -d dedicacion -U $USUARIO -v ON_ERROR_STOP=1 -c $sql 2>&1 | Out-String
        } else {
            $env:PGSSLMODE = "require"
            $salida = psql -h $PG_FQDN -d $PG_DB -U $PG_APP_USER -v ON_ERROR_STOP=1 -c $sql 2>&1 | Out-String
        }
        $codigo = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $anterior
        Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
        Remove-Item Env:PGSSLMODE -ErrorAction SilentlyContinue
    }
    if ($codigo -ne 0) {
        if ($Local) { throw "Fallo ejecutando SQL en ${DESTINO}:`n$salida" }
        throw "Fallo ejecutando SQL en ${DESTINO}:`n$salida`nSi psql no llega a conectar (tiempo agotado o 'no pg_hba.conf entry'), lo mas probable es que tu IP no tenga acceso al servidor: revisa en el Portal de Azure (servidor $PG, Redes) la regla de firewall de tu IP. Este script NO la crea ni la toca: el servidor es COMPARTIDO."
    }
    return $salida
}

# --- 3) Antes ---------------------------------------------------------------
Section "3) Filas antes del vaciado"
Write-Host (Ejecutar-Sql $RECUENTO)

# -SoloRecuento: aqui se acaba, sin escribir nada.
if ($SoloRecuento) {
    Section "SOLO RECUENTO: hecho, no se ha escrito nada"
    Write-Host "Destino: $DESTINO"
    Write-Host "Para vaciar:  .\vaciar_datos_prueba_dedicacion.ps1 $($MODO)-Confirmar" -ForegroundColor Yellow
    return
}

# --- 4) La sentencia --------------------------------------------------------
Section "4) Vaciado"
Ejecutar-Sql $SENTENCIA | Out-Null
Write-Host "  Ejecutada: $SENTENCIA" -ForegroundColor Green

# --- 5) Despues -------------------------------------------------------------
Section "5) Filas despues (esperado: 0 en las cuatro)"
Write-Host (Ejecutar-Sql $RECUENTO)

Section "HECHO"
Write-Host "Destino: $DESTINO"
Write-Host "`nSIGUIENTE (infra/README_dedicacion.md, paso F-026):" -ForegroundColor Yellow
Write-Host "  GET  /api/v1/sync/preview   y revisar empleados.ventana_baja" -ForegroundColor Yellow
Write-Host "  POST /api/v1/sync           antes de registrar nada" -ForegroundColor Yellow
