# infra/00_vars_dedicacion.ps1
# Variables compartidas de la infraestructura de DEDICACION (proyecto
# `porcentajes`). Dot-source este fichero en cada consola nueva ANTES de
# cualquier otro script:
#
#     . .\00_vars_dedicacion.ps1
#
# NINGUN VALOR SECRETO ENTRA AQUI (F-008, R21). La suscripcion y el tenant
# llevan el marcador REDACTADO-VER-COPIA-LOCAL: crea tu propia copia
# 00_vars_dedicacion.local.ps1 (ignorada por infra/.gitignore) con los valores
# reales y dot-sourceala DESPUES de esta:
#
#     . .\00_vars_dedicacion.ps1 ; . .\00_vars_dedicacion.local.ps1
#
# Esto es un repositorio git: lo que entra, se queda en el historial aunque
# luego se borre.

# --- Identidad de la suscripcion -------------------------------------------
$Global:SUBSCRIPTION = "REDACTADO-VER-COPIA-LOCAL"
$Global:TENANT       = "REDACTADO-VER-COPIA-LOCAL"
$Global:LOCATION     = "spaincentral"

# --- Sufijo unico global ----------------------------------------------------
# El nombre del Key Vault comparte espacio de nombres MUNDIAL: puede estar
# pillado por otro cliente de Azure. Si la creacion falla por "already taken",
# cambia este sufijo por otro corto (minusculas/digitos) y relanza fase1, que
# es idempotente. Tope del nombre del KV: 24 caracteres.
$Global:SUFFIX = "dd7k2"

# --- Recursos PROPIOS (se crean en rg-dedicacion-dev) -----------------------
$Global:RG   = "rg-dedicacion-dev"
$Global:MI   = "id-dedicacion-dev"          # managed identity (la crea fase1)
$Global:LAW  = "log-dedicacion-dev"         # Log Analytics
$Global:CAE  = "cae-dedicacion-dev"         # Container Apps Environment
$Global:KV   = "kv-dedicacion-$SUFFIX"      # 3-24 caracteres, unico global

# NO se crea Storage Account, ni colas, ni contenedores de blobs (R3): aqui
# no hay canal asincrono. La cadena front -> api -> transfer es HTTP sincrono
# y el volumen es un cuadrante mensual por obra. Un Storage sin usar es
# superficie de ataque y factura sin contrapartida.

# --- REUTILIZADOS (cross-RG; NO se crean ni se modifican aqui) --------------
# Registro de contenedores compartido. Usuario admin DESHABILITADO en la
# suscripcion: se accede por identidad gestionada (AcrPull + --registry-identity).
$Global:ACR    = "acralbaranesdev"
$Global:ACR_RG = "rg-albaranes-dev"

# Servidor PostgreSQL COMPARTIDO con albaranes, partes, datamart y postventa.
# Somos el QUINTO inquilino (decision D1 del humano, 2026-08-20). Nada a nivel
# de servidor: ni ALTER SYSTEM, ni CREATE EXTENSION, ni parametros, ni
# autenticacion, ni almacenamiento. Su disco son 32 GB compartidos que solo
# crecen, y el punto de restauracion es del servidor entero.
$Global:PG          = "psql-albaranes-rs9k2"
$Global:PG_RG       = "rg-albaranes-dev"
$Global:PG_DB       = "dedicacion"          # base PROPIA en ese servidor
$Global:PG_SCHEMA   = "public"              # decision D1b: public, como albaranes y partes
$Global:PG_APP_USER = "dedicacion_app"      # rol de aplicacion PROPIO, NUNCA el admin
$Global:PG_ADMIN    = "ruesmaadmin"         # admin del servidor: solo lo usa una persona, una vez

# Pasarela al SQL Server on-premise de Sigrid. UNICO acceso a esa base: nadie
# se conecta por SQL directo. La api lee maestros; el transfer escribe.
$Global:SIGRID_FUNC = "func-sigridapi-dev-huyke"
$Global:SIGRID_RG   = "rg-sigrid-dev-data-api"
$Global:SIGRID_DB   = "ruesma"              # base REAL; la replica ruesma_rep no admite escritura

# --- Mapa de imagenes: servicio -> repositorio en el ACR --------------------
# El TAG no esta aqui: es fechado (rAAAAMMDD-HHmm) y vive en infra/imagenes.json,
# que escribe build_images_dedicacion.ps1 y se versiona. Asi "que codigo esta
# corriendo" se responde desde git, sin abrir Azure (R23, R24).
$Global:IMG = [ordered]@{
  "transfer" = "dedicacion-transfer"   # 8006, UNICA pluma sobre el ERP
  "api"      = "dedicacion-api"        # 8090, cuadrante + maestros + export
  "front"    = "dedicacion-front"      # 8080, captura y proxy
}

# --- Mapa de Container Apps: servicio -> nombre del recurso -----------------
$Global:APPS = [ordered]@{
  "transfer" = "ca-dedicacion-transfer"
  "api"      = "ca-dedicacion-api"
  "front"    = "ca-dedicacion-front"
}

# --- Puertos de escucha (tienen que casar con el EXPOSE de cada Dockerfile) -
$Global:PUERTOS = @{
  "transfer" = 8006
  "api"      = 8090
  "front"    = 8080
}

# --- Carpeta de codigo de cada servicio (relativa a infra/) ----------------
$Global:SRC = @{
  "transfer" = "..\services\dedicacion-transfer"
  "api"      = "..\services\dedicacion-api"
  "front"    = "..\services\dedicacion-front"
}

# --- Orden de despliegue: cada servicio ANTES que quien lo consume ---------
# No es una preferencia: la api necesita el FQDN interno del transfer y el
# front el de la api (R27).
$Global:ORDEN = @("transfer", "api", "front")

# --- Timeouts encadenados (R28) --------------------------------------------
# Cada salto espera MAS que el siguiente, y todos por debajo del corte del
# balanceador de Azure, que son 230 s y no se configura. Al reves, el de
# fuera se rinde antes y el usuario ve un error de una escritura que si se
# estaba haciendo.
$Global:TIMEOUT_FRONT_API      = 200   # front -> api
$Global:TIMEOUT_API_TRANSFER   = 180   # api   -> transfer
$Global:TIMEOUT_TRANSFER_SIGRID = 60   # transfer -> sigrid-api

# --- Escalado (decision D4 del humano, 2026-08-20) -------------------------
# min 1 en los tres: comportamiento predecible mientras se valida, sin
# arranque en frio. La palanca de coste, si molesta, es bajar api y transfer
# a min 0 (el max sigue siendo 1 en los dos).
# max 1 en transfer y api NO es una palanca: es restriccion dura. La linea se
# inserta en Sigrid con MAX(ide)+1 bajo UPDLOCK/HOLDLOCK y dos replicas se
# pisarian los ide; y la sincronizacion de maestros de la api no esta
# disenada para varias replicas concurrentes (R4, R5).
$Global:MIN_REPLICAS = 1
$Global:MAX_REPLICAS = 1

# --- Grupo de seguridad de Entra para Easy Auth ----------------------------
# Quien entra en el grupo lo decide el humano (decision D3, sin cerrar). El
# script setup_front_easyauth.ps1 lo crea y anade al usuario que lo ejecuta;
# el resto se anaden con:
#   az ad group member add --group <objectId> --member-id <objectIdUsuario>
$Global:GRUPO_ACCESO = "dedicacion-portal-users"

# --- Tags acens (OBLIGATORIOS por Azure Policy) ----------------------------
$Global:TAGS = @(
  "acens-customer=Construcciones-Ruesma",
  "acens-environment=dev",
  "acens-project=dedicacion",
  "acens-responsable-so-app=pgris"
)

# --- IP para la regla de firewall de PostgreSQL ----------------------------
# "AUTO" = la resuelve el propio script. Si prefieres fijarla, ponla en tu
# copia LOCAL, nunca aqui: una IP interna es justo lo que R21 prohibe.
$Global:MY_IP = "AUTO"

Write-Host "[vars-dedicacion] cargadas. RG=$RG  KV=$KV  CAE=$CAE" -ForegroundColor Cyan
Write-Host "[vars-dedicacion] REUTILIZA ACR=$ACR ($ACR_RG)  PG=$PG/$PG_DB ($PG_RG)  SIGRID=$SIGRID_FUNC" -ForegroundColor Cyan
if ($SUBSCRIPTION -like "REDACTADO*") {
    Write-Host "[vars-dedicacion] AVISO: SUBSCRIPTION y TENANT estan redactados." -ForegroundColor Yellow
    Write-Host "[vars-dedicacion] Crea 00_vars_dedicacion.local.ps1 con los valores reales y dot-sourceala DESPUES de esta." -ForegroundColor Yellow
}
