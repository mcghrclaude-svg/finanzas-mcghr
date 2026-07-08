# orquestador_pipeline.ps1 -- corre extraccion.py y despues correlacion.py
# en orden sincronico sobre la DB de dev, para un rango de fechas explicito.
#
# INSTRUCCIONES DE EJECUCION:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\scripts\etl\orquestador_pipeline.ps1 -FechaDesde 2026-06-01 -FechaHasta 2026-06-30
#   .\scripts\etl\orquestador_pipeline.ps1 -RepoPath C:\Users\ghriz\finanzas-mcghr -FechaDesde 2026-06-01 -FechaHasta 2026-06-30

param(
    [string]$RepoPath = "",
    [Parameter(Mandatory=$true)]
    [string]$FechaDesde,
    [Parameter(Mandatory=$true)]
    [string]$FechaHasta
)

$ErrorActionPreference = "Continue"

$policy = Get-ExecutionPolicy -Scope Process
if ($policy -eq "Restricted" -or $policy -eq "AllSigned") {
    Write-Host ""
    Write-Host "   FAIL Falta el bypass de ExecutionPolicy. Corre primero:" -ForegroundColor Red
    Write-Host "        Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass" -ForegroundColor Yellow
    exit 1
}

if (-not $RepoPath) {
    try {
        $detected = git rev-parse --show-toplevel 2>$null
        if ($LASTEXITCODE -eq 0 -and $detected) { $RepoPath = $detected }
    } catch {}
}
if (-not $RepoPath) {
    $RepoPath = Read-Host "Ruta del repo finanzas-mcghr [C:\Users\ghriz\finanzas-mcghr]"
    if (-not $RepoPath) { $RepoPath = "C:\Users\ghriz\finanzas-mcghr" }
}
Set-Location $RepoPath.Trim()

$pythonExe = Join-Path $RepoPath.Trim() "venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Host "   AVISO No se encontro venv\Scripts\python.exe -- usando 'python' del PATH" -ForegroundColor Yellow
    $pythonExe = "python"
}

Write-Host ""
Write-Host "=== Paso 1: extraccion.py ($FechaDesde -> $FechaHasta) ===" -ForegroundColor Cyan
& $pythonExe "scripts\etl\extraccion.py" --fecha-desde $FechaDesde --fecha-hasta $FechaHasta
if ($LASTEXITCODE -ne 0) {
    Write-Host "   FAIL extraccion.py termino con codigo $LASTEXITCODE -- no se corre correlacion.py" -ForegroundColor Red
    exit 1
}
Write-Host "   OK   extraccion.py completo" -ForegroundColor Green

$candidatosPath = "staging\candidatos_${FechaDesde}_${FechaHasta}.json"
if (-not (Test-Path $candidatosPath)) {
    Write-Host "   FAIL No se encontro el archivo de candidatos esperado: $candidatosPath" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== Paso 2: correlacion.py ===" -ForegroundColor Cyan
& $pythonExe "scripts\etl\correlacion.py" --input $candidatosPath
if ($LASTEXITCODE -ne 0) {
    Write-Host "   FAIL correlacion.py termino con codigo $LASTEXITCODE" -ForegroundColor Red
    exit 1
}
Write-Host "   OK   correlacion.py completo" -ForegroundColor Green

Write-Host ""
Write-Host "Pipeline completo. Para ver el resultado:" -ForegroundColor Cyan
Write-Host "  $pythonExe scripts\etl\inspeccionar_pipeline.py" -ForegroundColor White
exit 0
