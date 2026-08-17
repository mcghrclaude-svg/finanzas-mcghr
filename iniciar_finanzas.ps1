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

# Chequea si un servicio ya esta corriendo, leyendo su PID file.
# Devuelve el proceso vivo si lo encuentra, o $null si no hay nada corriendo.
function Get-ServicioVivo {
    param([string]$PidFile)

    if (-not (Test-Path $PidFile)) {
        return $null
    }
    $procId = (Get-Content $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
    if (-not $procId) {
        return $null
    }
    $proc = Get-Process -Id ([int]$procId) -ErrorAction SilentlyContinue
    return $proc
}

Write-Host ""
Write-Host "======================================"
Write-Host "  Finanzas MCGHR -- Iniciando stack"
Write-Host "======================================"
Write-Host ""

# -- Backend --------------------------------------------------------------

$backendVivo = Get-ServicioVivo -PidFile "$LOGDIR\backend.pid"
if ($backendVivo) {
    Write-Host "  AVISO: el backend ya esta corriendo (PID $($backendVivo.Id)). No se arranca uno nuevo."
    Write-Host "         Si queres reiniciarlo, corre primero .\detener_finanzas.ps1"
} else {
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
}

# -- Frontend -------------------------------------------------------------

$frontendVivo = Get-ServicioVivo -PidFile "$LOGDIR\frontend.pid"
if ($frontendVivo) {
    Write-Host "  AVISO: el frontend ya esta corriendo (PID $($frontendVivo.Id)). No se arranca uno nuevo."
    Write-Host "         Si queres reiniciarlo, corre primero .\detener_finanzas.ps1"
} else {
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
}

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
