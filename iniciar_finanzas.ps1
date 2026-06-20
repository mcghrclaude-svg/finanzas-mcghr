# iniciar_finanzas.ps1
# Arranca el stack completo de Finanzas MCGHR:
#   - Backend FastAPI en http://localhost:8000
#   - Frontend React en http://localhost:3000
#
# Uso desde barra de tareas o startup de Windows:
#   powershell -ExecutionPolicy Bypass -File "C:\Users\ghriz\finanzas-mcghr\iniciar_finanzas.ps1"

$REPO = "C:\Users\ghriz\finanzas-mcghr"
$PYTHON = "$REPO\venv\Scripts\python.exe"
$UVICORN = "$REPO\venv\Scripts\uvicorn.exe"
$NODE = "C:\Program Files\nodejs\npm.cmd"

# Verificar que el repo existe
if (-not (Test-Path $REPO)) {
    [System.Windows.Forms.MessageBox]::Show(
        "No se encuentra el repo en $REPO",
        "Finanzas MCGHR - Error",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Error
    )
    exit 1
}

Write-Host ""
Write-Host "======================================"
Write-Host "  Finanzas MCGHR -- Iniciando stack"
Write-Host "======================================"
Write-Host ""

# ── Backend ───────────────────────────────────────────────────────────────────

Write-Host "Iniciando backend en http://localhost:8000 ..."
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-Command",
    "cd '$REPO'; Write-Host 'BACKEND -- Finanzas MCGHR' -ForegroundColor Cyan; & '$UVICORN' backend.main:app --reload --port 8000"
) -WindowStyle Normal

Start-Sleep -Seconds 2

# ── Frontend ──────────────────────────────────────────────────────────────────

Write-Host "Iniciando frontend en http://localhost:3000 ..."
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-Command",
    "cd '$REPO\frontend'; Write-Host 'FRONTEND -- Finanzas MCGHR' -ForegroundColor Green; npm run dev"
) -WindowStyle Normal

Start-Sleep -Seconds 3

# ── Abrir browser ────────────────────────────────────────────────────────────

Write-Host "Abriendo http://localhost:3000 ..."
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "  Backend:  http://localhost:8000"
Write-Host "  API Docs: http://localhost:8000/docs"
Write-Host "  App:      http://localhost:3000"
Write-Host ""
Write-Host "  Para cerrar: cerrar las dos ventanas de PowerShell."
Write-Host ""
