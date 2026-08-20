# infra/crear_base_dedicacion.ps1
# Crea la base `dedicacion` y su rol de aplicacion en el servidor PostgreSQL
# COMPARTIDO `psql-albaranes-rs9k2`. UNA SOLA VEZ Y EJECUTADO POR UNA PERSONA.
#
#     . .\00_vars_dedicacion.ps1
#     .\crear_base_dedicacion.ps1                # muestra el PLAN, no toca nada
#     .\crear_base_dedicacion.ps1 -Confirmar     # ejecuta
#
# El plan primero no es ceremonia: este script es lo unico de todo el
# despliegue que escribe en un servidor de PRODUCCION que usan otros cuatro
# proyectos (albaranes, partes, datamart y postventa). Verlo antes de hacerlo
# cuesta diez segundos.
#
# POR QUE ESTO NO LO HACE LA APLICACION
# -------------------------------------
# Hasta F-008, `dedicacion-api` ejecutaba CREATE ROLE y CREATE DATABASE en
# CADA arranque, conectandose como administrador del servidor. Contra
# localhost es una comodidad; contra un servidor compartido es justo lo que el
# ecosistema prohibe por escrito. Ahora el servicio arranca con
# AUTO_CREATE_DATABASE=false y ni siquiera abre esa conexion (R13-R15): la
# contrasena del administrador no viaja a ningun contenedor, no se guarda en
# el Key Vault y no aparece en ningun fichero. La usas tu, aqui, una vez.
#
# LO QUE ESTE SCRIPT NO HACE, Y ES DELIBERADO (R18)
# ------------------------------------------------
#   - NINGUN `ALTER SYSTEM`: los parametros del servidor son de todos.
#   - NINGUN `CREATE EXTENSION`: se instalan a nivel de servidor.
#   - NINGUN `GRANT` a nivel de servidor ni rol con privilegios globales.
#     Los unicos GRANT que se ejecutan son DENTRO de nuestra base y sobre
#     nuestro esquema.
#   - NO toca el esquema `public` de ninguna otra base.
#   - NO cambia almacenamiento, autenticacion ni copias de seguridad.
#
# Es el mismo criterio que `postventa-incidencias` dejo escrito al ser el
# cuarto inquilino de este servidor. Nosotros somos el quinto.

param(
    # Sin este conmutador el script solo IMPRIME lo que haria.
    [switch] $Confirmar
)

$ErrorActionPreference = "Stop"
if (-not $PG) { throw "Falta `$PG. Haz primero:  . .\00_vars_dedicacion.ps1" }

function Section($t) { Write-Host "`n=== $t ===" -ForegroundColor Green }

# --- 0) El plan, siempre ----------------------------------------------------
Write-Host "`n============================================================" -ForegroundColor Yellow
Write-Host " SERVIDOR COMPARTIDO: $PG ($PG_RG)" -ForegroundColor Yellow
Write-Host " Lo usan tambien albaranes, partes, datamart-seg-anual y postventa." -ForegroundColor Yellow
Write-Host " Su disco son 32 GB que SOLO CRECEN, y el punto de restauracion es" -ForegroundColor Yellow
Write-Host " del servidor ENTERO: no se puede volver atras nuestra base sin" -ForegroundColor Yellow
Write-Host " arrastrar las ajenas." -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "`nPLAN:"
Write-Host "  1. Comprobar que el servidor existe (NO se crea)."
Write-Host "  2. Regla de firewall 'AllowAzureServices' SI NO EXISTE ya."
Write-Host "  3. Crear la base '$PG_DB' si no existe."
Write-Host "  4. Crear el rol de aplicacion '$PG_APP_USER' si no existe (LOGIN, sin privilegios globales)."
Write-Host "  5. Darle permisos DENTRO de '$PG_DB', esquema '$PG_SCHEMA', y nada mas."
Write-Host "`nNO se ejecutara: ALTER SYSTEM, CREATE EXTENSION, GRANT de servidor," -ForegroundColor Cyan
Write-Host "ni nada sobre las bases de los otros cuatro proyectos." -ForegroundColor Cyan

if (-not $Confirmar) {
    Write-Host "`nEsto ha sido el PLAN. Para ejecutarlo de verdad:" -ForegroundColor Yellow
    Write-Host "  .\crear_base_dedicacion.ps1 -Confirmar" -ForegroundColor Yellow
    return
}

az account set --subscription $SUBSCRIPTION | Out-Null
az extension add --name rdbms-connect --upgrade --only-show-errors | Out-Null

# --- 1) El servidor tiene que existir. No se crea. --------------------------
Section "1) Servidor $PG"
$PG_FQDN = az postgres flexible-server show -n $PG -g $PG_RG --query "fullyQualifiedDomainName" -o tsv
if ([string]::IsNullOrWhiteSpace($PG_FQDN)) {
    throw "No encuentro el servidor '$PG' en '$PG_RG'. NO lo crees: revisa el nombre en 00_vars_dedicacion.ps1."
}
Write-Host "  Localizado. No se modifica ningun parametro suyo."

# --- 2) Firewall: solo si falta ---------------------------------------------
Section "2) Regla de firewall para los servicios de Azure"
# Los Container Apps de Consumo tienen IP saliente dinamica. La regla
# 0.0.0.0-0.0.0.0 es la forma documentada de decir "permitir servicios de
# Azure"; NO es una IP ni abre el servidor a Internet.
# Es lo unico de este script a nivel de servidor, asi que primero se mira si
# ya esta puesta por otro proyecto: si esta, no se toca.
$reglas = az postgres flexible-server firewall-rule list -g $PG_RG -s $PG `
            --query "[?startIpAddress=='0.0.0.0' && endIpAddress=='0.0.0.0'].name" -o tsv
if ([string]::IsNullOrWhiteSpace($reglas)) {
    Write-Host "  No existe: se crea 'AllowAzureServices'." -ForegroundColor Yellow
    Write-Host "  AVISO: es la unica accion a nivel de servidor de este script." -ForegroundColor Yellow
    az postgres flexible-server firewall-rule create -g $PG_RG -s $PG `
        --rule-name AllowAzureServices `
        --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0 --only-show-errors | Out-Null
} else {
    Write-Host "  Ya existe ('$reglas'), puesta por otro proyecto. No se toca."
}

# --- 3) Credenciales, en memoria y solo durante esta sesion -----------------
Section "3) Credenciales"
Write-Host "  Ninguna de las dos se escribe en disco ni se imprime."
$secAdmin = Read-Host "  Contrasena del admin '$PG_ADMIN' del servidor '$PG'" -AsSecureString
$PGADMIN_PWD = [System.Net.NetworkCredential]::new("", $secAdmin).Password
if ([string]::IsNullOrWhiteSpace($PGADMIN_PWD)) { throw "Sin la contrasena del admin no se puede crear nada." }

Write-Host "`n  Ahora la del ROL DE APLICACION '$PG_APP_USER' (la eliges tu, es nueva)."
Write-Host "  Guarda la MISMA en el Key Vault como PG-PASSWORD con add_secrets_dedicacion.ps1."
$secApp = Read-Host "  Contrasena para '$PG_APP_USER'" -AsSecureString
$APP_PWD = [System.Net.NetworkCredential]::new("", $secApp).Password
if ([string]::IsNullOrWhiteSpace($APP_PWD)) { throw "El rol de aplicacion necesita contrasena." }
if ($APP_PWD -eq $PGADMIN_PWD) {
    throw "ABORTADO: el rol de aplicacion NO puede llevar la contrasena del administrador del servidor. Ese es justo el error que `partes` cometio al desplegar con PG_USER=admin."
}
# Escapado para SQL: en PostgreSQL una comilla simple se duplica.
$APP_PWD_SQL = $APP_PWD.Replace("'", "''")

function Ejecutar-Sql($base, $sql) {
    az postgres flexible-server execute `
        -n $PG -u $PG_ADMIN -p $PGADMIN_PWD -d $base `
        --querytext $sql --only-show-errors | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Fallo ejecutando SQL en la base '$base'." }
}

# --- 4) La base --------------------------------------------------------------
# OJO con los flags: en `db show` y `db create` el nombre de la base va con
# -n/--name. El -d/--database-name SOLO existe en `flexible-server execute`
# (lo usa Ejecutar-Sql mas arriba). Mezclarlos da:
#   ERROR: unrecognized arguments: -d dedicacion
Section "4) Base '$PG_DB'"
# `db show` DEVUELVE ERROR si la base no existe, y con $ErrorActionPreference
# = "Stop" eso aborta el script: en PS 5.1 el `2>$null` sobre un ejecutable
# nativo no silencia nada, lo convierte en NativeCommandError. Se pregunta
# con `db list`, que devuelve vacio sin fallar.
$existe = az postgres flexible-server db list -g $PG_RG -s $PG --query "[?name=='$PG_DB'] | [0].name" -o tsv
if ([string]::IsNullOrWhiteSpace($existe)) {
    az postgres flexible-server db create -g $PG_RG -s $PG -n $PG_DB --only-show-errors | Out-Null
    Write-Host "  Base '$PG_DB' creada." -ForegroundColor Green
} else {
    Write-Host "  Base '$PG_DB' ya existe. No se toca."
}

# --- 5) El rol de aplicacion -------------------------------------------------
Section "5) Rol de aplicacion '$PG_APP_USER'"
# Rol PROPIO, con LOGIN y nada mas: ni SUPERUSER, ni CREATEDB, ni CREATEROLE,
# ni REPLICATION. Es lo que va dentro del Container App, y por tanto lo unico
# que podria filtrarse.
$sqlRol = @"
DO `$rol`$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '$PG_APP_USER') THEN
    CREATE ROLE $PG_APP_USER LOGIN PASSWORD '$APP_PWD_SQL'
      NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
  END IF;
END
`$rol`$;
"@
Ejecutar-Sql "postgres" $sqlRol
Write-Host "  Rol '$PG_APP_USER' listo (LOGIN, sin privilegios globales)." -ForegroundColor Green

# --- 6) Permisos DENTRO de nuestra base, y solo ahi -------------------------
Section "6) Permisos dentro de '$PG_DB' (esquema '$PG_SCHEMA')"
# Desde PostgreSQL 15 el esquema public no deja crear tablas a cualquiera:
# hace falta este GRANT explicito. Todo lo de abajo esta acotado a NUESTRA
# base y a NUESTRO esquema; ninguna sentencia sale de ahi.
$sqlPermisos = @"
GRANT CONNECT ON DATABASE $PG_DB TO $PG_APP_USER;
GRANT USAGE, CREATE ON SCHEMA $PG_SCHEMA TO $PG_APP_USER;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA $PG_SCHEMA TO $PG_APP_USER;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA $PG_SCHEMA TO $PG_APP_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA $PG_SCHEMA GRANT ALL ON TABLES TO $PG_APP_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA $PG_SCHEMA GRANT ALL ON SEQUENCES TO $PG_APP_USER;
"@
Ejecutar-Sql $PG_DB $sqlPermisos
Write-Host "  Permisos concedidos, acotados a '$PG_DB'." -ForegroundColor Green

# --- 7) Resumen -------------------------------------------------------------
Section "7) HECHO"
Write-Host "Servidor : $PG   (compartido; sin cambios a nivel de servidor)"
Write-Host "Base     : $PG_DB"
Write-Host "Esquema  : $PG_SCHEMA"
Write-Host "Rol app  : $PG_APP_USER   (LOGIN, sin privilegios globales)"
Write-Host "`nLas tablas las crea el propio servicio al arrancar, derivadas del ORM"
Write-Host "(infrastructure/db/esquema.py). Este script no escribe DDL de tablas."
Write-Host "`nSIGUIENTE:" -ForegroundColor Yellow
Write-Host "  .\add_secrets_dedicacion.ps1   # guarda esa misma contrasena como PG-PASSWORD" -ForegroundColor Yellow
Write-Host "`nY olvida la contrasena del administrador: no vuelve a hacer falta." -ForegroundColor Yellow
