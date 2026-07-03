# iniciar_finanzas.ps1
# Arranca el stack completo de Finanzas MCGHR en background (sin ventanas visibles):
#   - Backend FastAPI en http://localhost:8000
#   - Frontend React en http://localhost:3000
#
# Uso desde barra de tareas o startup de Windows:
#   powershell -ExecutionPolicy Bypass -File "C:\Users\ghriz\finanzas-mcghr\iniciar_finanzas.ps1"
#
# Para detener el stack: .\detener_finanzas.ps1

$REPO = "C:\Users\ghriz\finanzas-mcghr"
$PYTHON = "$REPO\venv\Scripts\python.exe"
$UVICORN = "$REPO\venv\Scripts\uvicorn.exe"
$NODE = "C:\Program Files\nodejs\npm.cmd"
$LOGDIR = "$REPO\logs"

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

if (-not (Test-Path $LOGDIR)) {
    New-Item -ItemType Directory -Path $LOGDIR | Out-Null
}

Write-Host ""
Write-Host "======================================"
Write-Host "  Finanzas MCGHR -- Iniciando stack"
Write-Host "======================================"
Write-Host ""

# -- Backend --------------------------------------------------------------

Write-Host "Iniciando backend en http://localhost:8000 (background, sin ventana) ..."
$backendProc = Start-Process -FilePath $UVICORN `
    -ArgumentList @("backend.main:app", "--reload", "--port", "8000") `
    -WorkingDirectory $REPO `
    -WindowStyle Hidden `
    -RedirectStandardOutput "$LOGDIR\backend.log" `
    -RedirectStandardError "$LOGDIR\backend.err.log" `
    -PassThru
Set-Content -Path "$LOGDIR\backend.pid" -Value $backendProc.Id

Start-Sleep -Seconds 2

# -- Frontend -------------------------------------------------------------

Write-Host "Iniciando frontend en http://localhost:3000 (background, sin ventana) ..."
$frontendProc = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c `"$NODE`" run dev" `
    -WorkingDirectory "$REPO\frontend" `
    -WindowStyle Hidden `
    -RedirectStandardOutput "$LOGDIR\frontend.log" `
    -RedirectStandardError "$LOGDIR\frontend.err.log" `
    -PassThru
Set-Content -Path "$LOGDIR\frontend.pid" -Value $frontendProc.Id

Start-Sleep -Seconds 3

# -- Abrir browser ----------------------------------------------------------

Write-Host "Abriendo http://localhost:3000 ..."
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "  Backend:  http://localhost:8000"
Write-Host "  API Docs: http://localhost:8000/docs"
Write-Host "  App:      http://localhost:3000"
Write-Host ""
Write-Host "  Logs:     $LOGDIR\backend.log / $LOGDIR\frontend.log"
Write-Host "  Para detener: .\detener_finanzas.ps1"
Write-Host ""
