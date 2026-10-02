# scripts/verif_f034_f026.ps1
# Verificacion MANUAL conjunta de F-034 (T9) y F-026 (T14 sync, T15 preflight).
#
# Solo contra lo LOCAL: lee Sigrid por sigrid-api (solo lectura), escribe en el
# PostgreSQL LOCAL (sync, un periodo y dos asignaciones de prueba) y lanza dos
# PREFLIGHT, que no escriben. Nunca llama a registro/ejecutar.
#
# Antes de lanzarlo (lo hace el humano, ver progress/current.md):
#   1. Vaciado local con autorizacion: infra/vaciar_datos_prueba_dedicacion.ps1 -Local (plan)
#      y despues el mismo con -Confirmar.
#   2. Transfer local con OBRA_PRUEBAS_FORZAR=true en su .env, y api local, los dos
#      desde la rama con F-034 y F-026 (python main.py en cada servicio).
#
# Uso, desde la raiz del repo:
#   powershell -ExecutionPolicy Bypass -File scripts/verif_f034_f026.ps1 [-Anio 2026 -Mes 10]

param([int]$Anio = (Get-Date).Year, [int]$Mes = (Get-Date).Month)
$ErrorActionPreference = "Stop"
$api = "http://127.0.0.1:8090/api/v1"
$apiDir = Join-Path $PSScriptRoot "..\services\dedicacion-api"
$fallos = 0
function Ok($cond, $txt) {
    if ($cond) { Write-Host "  OK    $txt" -ForegroundColor Green }
    else { Write-Host "  FALLA $txt" -ForegroundColor Red; $script:fallos++ }
}
function Put-Json($url, $obj) {
    Invoke-RestMethod -Method Put -Uri $url -ContentType "application/json" `
        -Headers @{ "X-Usuario" = "verif-f034-f026" } -Body ($obj | ConvertTo-Json -Depth 5)
}

# --- 0. Servicios -----------------------------------------------------------
$t = Invoke-RestMethod "http://127.0.0.1:8006/health"
if (-not $t.modo_pruebas) { throw "El transfer local NO esta en modo pruebas. Para aqui." }
Invoke-RestMethod "$api/health" | Out-Null
Write-Host "Transfer local en modo pruebas (obra $($t.obra_pruebas)); api ok."

# --- 1. T14: preview y sync -------------------------------------------------
Write-Host "`n== T14 · preview (no escribe) =="
$pv = Invoke-RestMethod "$api/sync/preview"
$e = $pv.empleados
Write-Host ("  empleados={0}  ventana_baja={1}  incluidos_con_baja={2}" -f $e.total, $e.ventana_baja, $e.incluidos_con_baja)
Write-Host ("  por empresa: {0}" -f ($e.por_empresa | ConvertTo-Json -Compress))
Write-Host ("  posible_misma_persona: {0}" -f ($e.posible_misma_persona | ConvertTo-Json -Compress -Depth 4))
Ok ($e.ventana_baja -gt 20000000) "el preview publica la ventana de bajas"

Write-Host "`n== T14 · sync (solo BBDD local) =="
(Invoke-RestMethod -Method Post "$api/sync") | ConvertTo-Json -Depth 5 -Compress | Write-Host

Write-Host "`n== T14 · trabajadores en la BBDD local =="
$py = @"
from sqlalchemy import create_engine, text
from config.settings import get_settings
e = create_engine(get_settings().database_url)
cods = ('MO/0772','MO/0759','MO/0760','MO/0762','MO/0774','MO/0775','MO/0776','MO/0777','MO/0779','MO/0496')
with e.connect() as c:
    filas = c.execute(text("SELECT ide, cod, empresa, activo, fecha_baja FROM trabajador WHERE cod = ANY(:c) AND empresa = 1 ORDER BY cod"), {"c": list(cods)}).all()
    for f in filas:
        print("FILA", f.ide, f.cod, f.empresa, f.activo, f.fecha_baja)
    print("ACTIVOS", sum(1 for f in filas if f.activo))
    print("EUSEBIO", next((f.ide for f in filas if f.cod == 'MO/0772'), 0))
    print("DE18", c.execute(text("SELECT ide FROM trabajador WHERE empresa = 18 AND activo ORDER BY ide LIMIT 1")).scalar() or 0)
    print("BAJA_ANTIGUA", c.execute(text("SELECT COUNT(*) FROM trabajador WHERE fecha_baja IS NOT NULL AND fecha_baja < :v"), {"v": $($e.ventana_baja)}).scalar())
"@
Push-Location $apiDir
try { $salida = $py | & .\.venv\Scripts\python.exe - } finally { Pop-Location }
$salida | Where-Object { $_ -like "FILA*" } | ForEach-Object { Write-Host "  $_" }
$activos = [int](($salida | Where-Object { $_ -like "ACTIVOS*" }) -split " ")[1]
$eusebio = [int](($salida | Where-Object { $_ -like "EUSEBIO*" }) -split " ")[1]
$de18 = [int](($salida | Where-Object { $_ -like "DE18*" }) -split " ")[1]
$antigua = [int](($salida | Where-Object { $_ -like "BAJA_ANTIGUA*" }) -split " ")[1]
Ok ($activos -eq 10) "los diez recursos del diagnostico (Eusebio y nueve mas) estan activos en la empresa 1 ($activos)"
Ok ($eusebio -gt 0) "Eusebio (MO/0772) esta en el maestro, ide = su res.ide ($eusebio)"
Ok ($antigua -eq 0) "ningun trabajador con baja anterior a la ventana"

# --- 2. Periodo de prueba y dos asignaciones (solo BBDD local) --------------
Write-Host "`n== Periodo $Anio-$('{0:D2}' -f $Mes) y asignaciones de prueba (BBDD local) =="
Invoke-RestMethod -Method Post "$api/periodos" -ContentType "application/json" -Body (@{ anio = $Anio; mes = $Mes } | ConvertTo-Json) | Out-Null
$c1 = Invoke-RestMethod "$api/periodos/$Anio/$Mes/cuadrante?empresa=1"
$c18 = Invoke-RestMethod "$api/periodos/$Anio/$Mes/cuadrante?empresa=18"
$obra = @($c1.obras | Where-Object { $_.activa })[0]
Write-Host "  obra de prueba: $($obra.cod) ($($obra.ide))"
$ides1 = @($c1.obras | ForEach-Object { $_.ide }) -join ","
$ides18 = @($c18.obras | ForEach-Object { $_.ide }) -join ","
Ok ($ides1 -eq $ides18) "T9 · con la 18 se ofrecen las mismas obras que con la 1 (las de Ruesma)"
Ok (@($c18.trabajadores).Count -lt @($c1.trabajadores).Count) "T9 · con la 18 solo se ven sus trabajadores"
if ($eusebio -gt 0) {
    Put-Json "$api/periodos/$Anio/$Mes/trabajadores/$eusebio/asignaciones?empresa=1" @{ lineas = @(@{ obra_ide = $obra.ide; porcentaje = 100 }) } | Out-Null
}
if ($de18 -gt 0) {
    Put-Json "$api/periodos/$Anio/$Mes/trabajadores/$de18/asignaciones?empresa=18" @{ lineas = @(@{ obra_ide = $obra.ide; porcentaje = 100 }) } | Out-Null
} else { Write-Host "  (no hay trabajadores activos de la 18: T9 no se puede ejercitar)" -ForegroundColor Yellow; $fallos++ }

# --- 3. T15 y T9: preflight (NO ejecutar) -----------------------------------
function Accion-De($pf, $trabajador) {
    foreach ($o in $pf.obras) { foreach ($a in $o.acciones) { if ($a.recurso_ide -eq $trabajador) { return $a } } }
    return $null
}
Write-Host "`n== T15 · preflight con la 1 (solo lectura) =="
$p1 = Invoke-RestMethod -Method Post "$api/periodos/$Anio/$Mes/registro/preflight?empresa=1" -ContentType "application/json" -Body "{}"
$a = Accion-De $p1 $eusebio
Write-Host ("  Eusebio: accion={0} recurso_ide={1} motivo={2}" -f $a.accion, $a.recurso_ide, $a.motivo)
Ok ($a -and $a.accion -eq "escribir" -and $a.recurso_ide -eq $eusebio) "Eusebio sale para escribir con su propio recurso"
Ok (@($p1.no_vigentes).Count -eq 0) "no_vigentes vacio"

Write-Host "`n== T9 · preflight con la 18 (solo lectura) =="
$p18 = Invoke-RestMethod -Method Post "$api/periodos/$Anio/$Mes/registro/preflight?empresa=18" -ContentType "application/json" -Body "{}"
$b = Accion-De $p18 $de18
Write-Host ("  trabajador de la 18 ({0}): accion={1} motivo={2}" -f $de18, $b.accion, $b.motivo)
foreach ($o in $p18.obras) { Write-Host ("  obra {0}: destino={1} (empresa {2}) ok={3}" -f $o.obra.codigo, $o.obra_destino.codigo, $o.obra_destino.empresa, $o.ok) }
Ok ($b -and $b.accion -eq "escribir") "la linea del trabajador de la 18 en una obra de Ruesma sale para escribir, no omitida"

$p1 | ConvertTo-Json -Depth 20 | Out-File -Encoding utf8 (Join-Path $env:TEMP "verif_f034_f026_e1.json")
$p18 | ConvertTo-Json -Depth 20 | Out-File -Encoding utf8 (Join-Path $env:TEMP "verif_f034_f026_e18.json")
Write-Host "`nRespuestas completas en %TEMP%\verif_f034_f026_e1.json y _e18.json"
Write-Host "RESULTADO: $(if ($fallos -eq 0) { 'OK' } else { "$fallos fallo(s)" })"
Write-Host "Falta lo visual: http://localhost:8080/?empresa=18 (obras de Ruesma; sin pulsar Registrar)."
