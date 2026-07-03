# detener_finanzas.ps1
# Detiene el stack completo de Finanzas MCGHR iniciado por iniciar_finanzas.ps1:
#   - Backend FastAPI (uvicorn)
#   - Frontend React (npm run dev)
#
# Uso:
#   powershell -ExecutionPolicy Bypass -File "C:\Users\ghriz\finanzas-mcghr\detener_finanzas.ps1"

$REPO = "C:\Users\ghriz\finanzas-mcghr"
$LOGDIR = "$REPO\logs"

function Stop-ProcessTree {
    param([int]$ProcessId)

    $children = @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$ProcessId" -ErrorAction SilentlyContinue)
    foreach ($child in $children) {
        Stop-ProcessTree -ProcessId $child.ProcessId
    }

    $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($proc) {
        Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "  OK   Proceso $ProcessId ($($proc.ProcessName)) detenido"
    }
}

function Stop-Servicio {
    param([string]$Nombre, [string]$PidFile)

    if (-not (Test-Path $PidFile)) {
        Write-Host "  --   $Nombre : no hay PID guardado (no estaba corriendo o ya se detuvo)"
        return
    }

    $procId = (Get-Content $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
    if (-not $procId) {
        Write-Host "  --   $Nombre : PID file vacio"
        Remove-Item $PidFile -ErrorAction SilentlyContinue
        return
    }

    $procId = [int]$procId
    if (Get-Process -Id $procId -ErrorAction SilentlyContinue) {
        Write-Host "Deteniendo $Nombre (PID $procId) ..."
        Stop-ProcessTree -ProcessId $procId
    } else {
        Write-Host "  --   $Nombre : el proceso $procId ya no existe"
    }

    Remove-Item $PidFile -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "======================================"
Write-Host "  Finanzas MCGHR -- Deteniendo stack"
Write-Host "======================================"
Write-Host ""

Stop-Servicio -Nombre "Backend"  -PidFile "$LOGDIR\backend.pid"
Stop-Servicio -Nombre "Frontend" -PidFile "$LOGDIR\frontend.pid"

Write-Host ""
Write-Host "  Listo."
Write-Host ""
