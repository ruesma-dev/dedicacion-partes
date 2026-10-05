# scripts/verif_f032_empresas.ps1
# F-032 · verificación MANUAL: sync real contra la BBDD LOCAL y nombres del
# selector desde Sigrid. Lee Sigrid (solo lectura, por sigrid-api); escribe
# solo en el PostgreSQL local. No toca el transfer ni Sigrid.
# Requiere la API (8090) arrancada desde la rama de F-032 (o `dev` con F-032).
# Uso, desde la raíz del repo: powershell -ExecutionPolicy Bypass -File scripts/verif_f032_empresas.ps1

$ErrorActionPreference = "Stop"
$api = "http://127.0.0.1:8090/api/v1"
$fallos = 0
function Ok($cond, $txt) {
    if ($cond) { Write-Host "  OK    $txt" -ForegroundColor Green }
    else { Write-Host "  FALLA $txt" -ForegroundColor Red; $script:fallos++ }
}
Invoke-RestMethod "$api/health" | Out-Null; Write-Host "API: ok"

Write-Host "`n== 1. Preview (no escribe) =="
$pv = Invoke-RestMethod "$api/sync/preview"
$pe = $pv.empresas
Write-Host ("  empresas leídas={0}  sin número={1}  de baja={2}" -f $pe.leidas, $pe.sin_numero, ($pe.de_baja | ConvertTo-Json -Compress))
Ok ($pe.leidas -ge 19) "el preview lee al menos las 19 empresas que conocemos ($($pe.leidas))"

Write-Host "`n== 2. Sync real (solo BBDD local) =="
$sy = Invoke-RestMethod -Method Post "$api/sync"
$sy | ConvertTo-Json -Depth 5 -Compress | Write-Host
Ok ($null -ne $sy.empresas) "el sync informa de las empresas"

Write-Host "`n== 3. GET /empresas (lo que ve el selector) =="
$e = Invoke-RestMethod "$api/empresas"
$e.empresas | ForEach-Object { Write-Host ("  {0} = {1}{2}" -f $_.empresa, $_.nombre, $(if ($_.de_baja) { "  (de baja)" } else { "" })) }
$n = @{}; $e.empresas | ForEach-Object { $n[[int]$_.empresa] = $_.nombre }
Ok ($e.por_defecto -eq 1) "la por defecto sigue siendo la 1"
Ok ($n[18] -eq "RUESMA SERVICIOS SL") "18 = RUESMA SERVICIOS SL"
Ok ($n[31] -eq "UTE RUESMA-INESCO TOLEDO") "31 = UTE RUESMA-INESCO TOLEDO"
Ok (@($e.empresas | Where-Object { $_.nombre -like "Empresa *" }).Count -eq 0) "ninguna sale como «Empresa N»"
Ok (@($e.empresas).Count -eq 3) "el selector sigue ofreciendo las mismas 3 empresas (1, 18, 31)"

Write-Host "`nRESULTADO F-032 (API): $(if ($fallos -eq 0) { 'OK' } else { "$fallos fallo(s)" })"
Write-Host "Falta mirar el selector en http://localhost:8080 (ver chat)."
