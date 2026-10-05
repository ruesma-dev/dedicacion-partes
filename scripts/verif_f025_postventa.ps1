# scripts/verif_f025_postventa.ps1
# Verificacion MANUAL de F-025 (T13 = paso M1, T14 = paso M2; design 8).
#
# Solo contra lo LOCAL: api y transfer locales, BBDD dedicacion LOCAL. Lee
# Sigrid por sigrid-api (solo lectura: el universo de postventa y el preflight
# no escriben nada) y escribe solo en el PostgreSQL LOCAL (sync, un periodo de
# prueba y las asignaciones de un trabajador en ese periodo). Las unicas
# llamadas son GET sync/preview, POST sync, POST periodos, GET cuadrante,
# PUT asignaciones y POST registro/preflight. Aunque el transfer local este
# en modo real, nada de esto escribe en Sigrid.
#
# Antes de lanzarlo (lo hace el humano):
#   1. Transfer local y api local desde la rama de F-025 (python main.py en
#      cada servicio); la api contra la BBDD LOCAL (PG_HOST=localhost).
#   2. Para M2, un periodo de prueba LOCAL sin otras asignaciones del
#      trabajador elegido (el script sustituye las suyas en ese periodo).
#
# Uso, desde la raiz del repo:
#   powershell -ExecutionPolicy Bypass -File scripts/verif_f025_postventa.ps1 -Paso M1 [-Anio 2026 -Mes 10]
#   powershell -ExecutionPolicy Bypass -File scripts/verif_f025_postventa.ps1 -Paso M2 -Anio AAAA -Mes MM

param(
    [Parameter(Mandatory = $true)][ValidateSet("M1", "M2")][string]$Paso,
    [int]$Anio = (Get-Date).Year,
    [int]$Mes = (Get-Date).Month
)
$ErrorActionPreference = "Stop"
$api = "http://127.0.0.1:8090/api/v1"
$fallos = 0
function Ok($cond, $txt) {
    if ($cond) { Write-Host "  OK    $txt" -ForegroundColor Green }
    else { Write-Host "  FALLA $txt" -ForegroundColor Red; $script:fallos++ }
}
function Put-Json($url, $obj) {
    Invoke-RestMethod -Method Put -Uri $url -ContentType "application/json" `
        -Headers @{ "X-Usuario" = "verif-f025" } -Body ($obj | ConvertTo-Json -Depth 5)
}
function Obra-De($cuadrante, $cod) {
    return @($cuadrante.obras | Where-Object { $_.cod -eq $cod })[0]
}

# --- 0. Servicios locales ---------------------------------------------------
$t = Invoke-RestMethod "http://127.0.0.1:8006/health"
Invoke-RestMethod "$api/health" | Out-Null
if ($t.modo_pruebas) { Write-Host "Transfer local en modo pruebas (obra $($t.obra_pruebas)); api ok." }
else { Write-Host "Transfer local en modo REAL: este script solo lee de Sigrid; api ok." -ForegroundColor Yellow }
Ok ($t.postventa_registrar) "el transfer local tiene POSTVENTA_REGISTRAR=true"

# --- 1. Periodo de prueba (BBDD local) ----------------------------------------
$periodo = "$api/periodos/$Anio/$Mes"
Invoke-RestMethod -Method Post "$api/periodos" -ContentType "application/json" `
    -Body (@{ anio = $Anio; mes = $Mes } | ConvertTo-Json) | Out-Null

if ($Paso -eq "M1") {
    # --- M1 (T13): preview, sync y cuadrante ----------------------------------
    Write-Host "`n== M1 - preview (no escribe) =="
    $o = (Invoke-RestMethod "$api/sync/preview").obras
    Write-Host ("  brutas={0} total={1} admiten_postventa={2} solo_postventa={3} motivo_postventa={4}" -f `
        $o.brutas, $o.total, $o.admiten_postventa, $o.solo_postventa, $o.motivo_postventa)
    Write-Host ("  excluidas_por_estado: {0}" -f ($o.excluidas_por_estado | ConvertTo-Json -Compress))
    Ok ($o.admiten_postventa -eq 83) "admiten_postventa = 83 (D2 = B; real: $($o.admiten_postventa))"
    Ok ($o.solo_postventa -eq 73) "solo_postventa = 73 (real: $($o.solo_postventa))"
    Ok ($null -eq $o.motivo_postventa) "motivo_postventa nulo: hay universo"

    Write-Host "`n== M1 - sync (solo BBDD local) =="
    (Invoke-RestMethod -Method Post "$api/sync") | ConvertTo-Json -Depth 5 -Compress | Write-Host

    Write-Host "`n== M1 - cuadrante con la 1 y con la 18 =="
    $c1 = Invoke-RestMethod "$periodo/cuadrante?empresa=1"
    $c18 = Invoke-RestMethod "$periodo/cuadrante?empresa=18"
    $marcas1 = @($c1.obras | ForEach-Object { "$($_.ide):$($_.activa):$($_.admite_postventa)" }) -join ","
    $marcas18 = @($c18.obras | ForEach-Object { "$($_.ide):$($_.activa):$($_.admite_postventa)" }) -join ","
    Ok ($marcas1 -eq $marcas18) "con la 18 se ofrecen las mismas obras, con las mismas marcas, que con la 1"
    foreach ($cod in @("0656", "0660", "0669", "0689")) {
        $obra = Obra-De $c1 $cod
        Write-Host ("  {0}: activa={1} admite_postventa={2} estado={3}" -f $cod, $obra.activa, $obra.admite_postventa, $obra.estado_sigrid)
        Ok ($obra -and -not $obra.activa -and $obra.admite_postventa) "$cod cerrada y ofrecida solo como Postv-"
    }
    foreach ($cod in @("CP", "OT", "191105")) {
        $obra = Obra-De $c1 $cod
        Write-Host ("  {0}: {1}" -f $cod, $(if ($obra) { "activa=$($obra.activa) admite_postventa=$($obra.admite_postventa)" } else { "no ofrecida" }))
        Ok (-not $obra -or -not $obra.admite_postventa) "$cod fuera del universo de postventa"
    }
}
else {
    # --- M2 (T14): preflight de una Postv-0656 y una obra sin postventa -------
    Write-Host "`n== M2 - periodo $Anio-$('{0:D2}' -f $Mes): asignaciones de prueba (BBDD local) =="
    $c1 = Invoke-RestMethod "$periodo/cuadrante?empresa=1"
    $pv = Obra-De $c1 "0656"
    $normal = @($c1.obras | Where-Object { $_.activa -and -not $_.admite_postventa })[0]
    $quien = @($c1.trabajadores | Where-Object { $_.activo -and $_.empresa -eq 1 })[0]
    if (-not ($pv -and $pv.admite_postventa -and $normal -and $quien)) {
        throw "Falta la obra 0656 con postventa, una obra sin postventa o un trabajador vigente: lanza antes el paso M1."
    }
    Write-Host ("  trabajador {0} ({1}); Postv-{2} y {3} normal" -f $quien.ide, $quien.nombre, $pv.cod, $normal.cod)
    Put-Json "$periodo/trabajadores/$($quien.ide)/asignaciones?empresa=1" @{ lineas = @(
        @{ obra_ide = $pv.ide; es_postventa = $true; porcentaje = 50 },
        @{ obra_ide = $normal.ide; es_postventa = $false; porcentaje = 50 }) } | Out-Null

    Write-Host "`n== M2 - preflight (solo lectura) =="
    $pf = Invoke-RestMethod -Method Post "$periodo/registro/preflight?empresa=1" `
        -ContentType "application/json" -Body (@{ trabajador_ide = $quien.ide } | ConvertTo-Json)
    foreach ($g in $pf.obras) {
        Write-Host ("  obra {0}: ok={1} capitulo_postventa={2} partidas_postventa={3}" -f `
            $g.obra.codigo, $g.ok, ($g.capitulo_postventa | ConvertTo-Json -Compress), @($g.partidas_postventa).Count)
    }
    $gpv = @($pf.obras | Where-Object { $_.obra.codigo -eq $pv.cod })[0]
    $gno = @($pf.obras | Where-Object { $_.obra.codigo -eq $normal.cod })[0]
    Ok ($gpv -and $gpv.capitulo_postventa.cod -eq "0656") "la linea Postv-0656 casa con la partida 0656"
    Ok ($gno -and @($gno.partidas_postventa).Count -eq 0) "partidas_postventa vacio en la obra sin postventa (R8)"
    Ok (@($pf.no_vigentes).Count -eq 0) "no_vigentes vacio"
    $pf | ConvertTo-Json -Depth 20 | Out-File -Encoding utf8 (Join-Path $env:TEMP "verif_f025_m2.json")
    Write-Host "  Respuesta completa en %TEMP%\verif_f025_m2.json"
}

Write-Host "`nRESULTADO $($Paso): $(if ($fallos -eq 0) { 'OK' } else { "$fallos fallo(s)" })"
Write-Host "No se pulsa Registrar: este script no escribe en Sigrid."
