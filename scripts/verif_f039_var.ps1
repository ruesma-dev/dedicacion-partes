# scripts/verif_f039_var.ps1
# Verificacion MANUAL de F-039 (T12 = paso M1, T13 = paso M2; design 8).
#
# Solo contra lo LOCAL: api y transfer locales, BBDD dedicacion LOCAL. Lee
# Sigrid por sigrid-api (solo lectura: los universos de postventa y VAR y el
# preflight no escriben nada) y escribe solo en el PostgreSQL LOCAL (sync, un
# periodo de prueba y las asignaciones de un trabajador en ese periodo). Las
# unicas llamadas son GET sync/preview, POST sync, POST periodos, GET
# cuadrante, PUT asignaciones y POST registro/preflight. Aunque el transfer
# local este en modo real, nada de esto escribe en Sigrid.
#
# Antes de lanzarlo (lo hace el humano):
#   1. Transfer local y api local desde la rama de F-039 (python main.py en
#      cada servicio); la api contra la BBDD LOCAL (PG_HOST=localhost).
#   2. Para M2, un periodo de prueba LOCAL sin otras asignaciones del
#      trabajador elegido (el script sustituye las suyas en ese periodo).
#
# Uso, desde la raiz del repo:
#   powershell -ExecutionPolicy Bypass -File scripts/verif_f039_var.ps1 -Paso M1 [-Anio 2026 -Mes 10]
#   powershell -ExecutionPolicy Bypass -File scripts/verif_f039_var.ps1 -Paso M2 -Anio AAAA -Mes MM

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
        -Headers @{ "X-Usuario" = "verif-f039" } -Body ($obj | ConvertTo-Json -Depth 5)
}
function Obra-De($cuadrante, $cod) {
    return @($cuadrante.obras | Where-Object { $_.cod -eq $cod })[0]
}

# --- 0. Servicios locales ---------------------------------------------------
$t = Invoke-RestMethod "http://127.0.0.1:8006/health"
Invoke-RestMethod "$api/health" | Out-Null
if ($t.modo_pruebas) { Write-Host "Transfer local en modo pruebas (obra $($t.obra_pruebas)); api ok." }
else { Write-Host "Transfer local en modo REAL: este script solo lee de Sigrid; api ok." -ForegroundColor Yellow }

# --- 1. Periodo de prueba (BBDD local) ----------------------------------------
$periodo = "$api/periodos/$Anio/$Mes"
Invoke-RestMethod -Method Post "$api/periodos" -ContentType "application/json" `
    -Body (@{ anio = $Anio; mes = $Mes } | ConvertTo-Json) | Out-Null

if ($Paso -eq "M1") {
    # --- M1 (T12): preview, sync y cuadrante ----------------------------------
    Write-Host "`n== M1 - preview (no escribe) =="
    $o = (Invoke-RestMethod "$api/sync/preview").obras
    Write-Host ("  brutas={0} total={1} excluidas_por_codigo={2} entradas_var={3} obra_var={4} motivo_var={5} motivo_postventa={6}" -f `
        $o.brutas, $o.total, $o.excluidas_por_codigo, $o.entradas_var, $o.obra_var, $o.motivo_var, $o.motivo_postventa)
    Write-Host ("  muestra_excluidas_por_codigo: {0}" -f ($o.muestra_excluidas_por_codigo | ConvertTo-Json -Compress))
    Ok ($o.excluidas_por_codigo -eq 240) "excluidas_por_codigo = 240 (real: $($o.excluidas_por_codigo))"
    Ok ($o.entradas_var -eq 1) "entradas_var = 1 (real: $($o.entradas_var))"
    Ok ($o.obra_var -eq "VAR") "obra_var = VAR (real: $($o.obra_var))"
    Ok ($null -eq $o.motivo_var) "motivo_var nulo: hay universo VAR"
    Ok ($null -eq $o.motivo_postventa) "motivo_postventa nulo: hay universo de postventa"

    Write-Host "`n== M1 - sync (solo BBDD local) =="
    (Invoke-RestMethod -Method Post "$api/sync") | ConvertTo-Json -Depth 5 -Compress | Write-Host

    Write-Host "`n== M1 - cuadrante con la 1 =="
    $c1 = Invoke-RestMethod "$periodo/cuadrante?empresa=1"
    $entrada = Obra-De $c1 "VAR-29"
    if ($entrada) {
        Write-Host ("  VAR-29: ide={0} activa={1} admite_postventa={2} descripcion={3}" -f `
            $entrada.ide, $entrada.activa, $entrada.admite_postventa, $entrada.descripcion)
    }
    Ok ($entrada -and $entrada.ide -eq -417055 -and $entrada.activa) "VAR-29 ofrecida (ide -417055, activa)"
    $var = Obra-De $c1 "VAR"
    Ok (-not $var -or -not $var.activa) "la obra VAR no se ofrece como obra normal"
    Ok (-not (Obra-De $c1 "150414")) "150414 no se ofrece"
    $seis = @($c1.obras | Where-Object { $_.cod -match "[0-9]{6}" -and $_.activa })
    Ok ($seis.Count -eq 0) "ninguna obra activa con 6 o mas digitos seguidos (real: $($seis.Count))"
}
else {
    # --- M2 (T13): preflight de una linea en VAR-29 y otra en obra normal ------
    Write-Host "`n== M2 - periodo $Anio-$('{0:D2}' -f $Mes): asignaciones de prueba (BBDD local) =="
    $c1 = Invoke-RestMethod "$periodo/cuadrante?empresa=1"
    $entrada = Obra-De $c1 "VAR-29"
    $normal = @($c1.obras | Where-Object { $_.activa -and $_.ide -gt 0 -and $_.cod -notmatch "[0-9]{6}" })[0]
    $quien = @($c1.trabajadores | Where-Object { $_.activo -and $_.empresa -eq 1 })[0]
    if (-not ($entrada -and $entrada.activa -and $normal -and $quien)) {
        throw "Falta la entrada VAR-29, una obra normal activa o un trabajador vigente: lanza antes el paso M1."
    }
    Write-Host ("  trabajador {0} ({1}); VAR-29 y {2} normal" -f $quien.ide, $quien.nombre, $normal.cod)
    Put-Json "$periodo/trabajadores/$($quien.ide)/asignaciones?empresa=1" @{ lineas = @(
        @{ obra_ide = $entrada.ide; es_postventa = $false; porcentaje = 50 },
        @{ obra_ide = $normal.ide; es_postventa = $false; porcentaje = 50 }) } | Out-Null

    Write-Host "`n== M2 - preflight (solo lectura) =="
    $pf = Invoke-RestMethod -Method Post "$periodo/registro/preflight?empresa=1" `
        -ContentType "application/json" -Body (@{ trabajador_ide = $quien.ide } | ConvertTo-Json)
    foreach ($g in $pf.obras) {
        Write-Host ("  obra {0} (ide {1}): ok={2} forzada_pruebas={3} acciones={4}" -f `
            $g.obra.codigo, $g.obra.ide, $g.ok, $g.forzada_pruebas, @($g.acciones).Count)
        foreach ($a in @($g.acciones)) {
            Write-Host ("    {0} paride={1} partida_cod={2} metodo={3} caa_cod={4} motivo={5}" -f `
                $a.accion, $a.paride, $a.partida_cod, $a.partida_metodo, $a.caa_cod, $a.motivo)
        }
    }
    $gvar = @($pf.obras | Where-Object { $_.obra.codigo -eq "VAR" })[0]
    $av = @($gvar.acciones | Where-Object { $_.partida_metodo -eq "var" })[0]
    Ok ($gvar -and $gvar.ok) "el grupo de la obra VAR responde ok"
    Ok ($av -and $av.accion -eq "escribir") "la linea de VAR-29 se escribiria"
    Ok ($av -and $av.paride -eq 417055 -and $av.partida_cod -eq "29") "con paride 417055 y partida 29"
    if ($gvar.forzada_pruebas) {
        Ok ($av -and $av.caa_cod -like "$($gvar.obra_destino.codigo).*") "cuenta del centro de la obra de pruebas (real: $($av.caa_cod))"
    }
    else {
        Ok ($av -and $av.caa_cod -like "VAR.CIMO*") "cuenta VAR.CIMO* del centro de la obra VAR (real: $($av.caa_cod))"
    }
    Ok (@($pf.no_vigentes).Count -eq 0) "no_vigentes vacio"
    $pf | ConvertTo-Json -Depth 20 | Out-File -Encoding utf8 (Join-Path $env:TEMP "verif_f039_m2.json")
    Write-Host "  Respuesta completa en %TEMP%\verif_f039_m2.json"
}

Write-Host "`nRESULTADO $($Paso): $(if ($fallos -eq 0) { 'OK' } else { "$fallos fallo(s)" })"
Write-Host "No se pulsa Registrar: este script no escribe en Sigrid."
