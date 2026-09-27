# instalar_autostart.ps1
# Registra el Panel de Control (tray_app.py) para que arranque oculto al
# iniciar sesion en Windows -- un acceso directo en la carpeta de Inicio del
# usuario (shell:startup) que corre pythonw.exe (sin ventana de consola,
# igual criterio que la tarea FinanzasMCGHR_ImportPWA ya corregida en
# backend/services/scheduled_task_service.py).
#
# Se probo primero con una Tarea Programada (trigger "al iniciar sesion",
# /SC ONLOGON) pero schtasks /Create rechaza ese trigger especifico con
# "Access is denied" para una cuenta no elevada en esta PC (confirmado:
# /SC MINUTE y /SC ONCE si funcionan sin admin, solo ONLOGON lo bloquea --
# es una proteccion real de Windows contra persistencia silenciosa, no un
# bug). La carpeta de Inicio es el mecanismo estandar de Windows para esto
# (el mismo que usan Slack, Discord, etc.) y no requiere privilegios.
#
# Uso (una sola vez, no hace falta reiniciar Windows para probarlo):
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\instalar_autostart.ps1
#
# Requisito previo: crear el venv propio de esta carpeta e instalar deps:
#   py -3.12 -m venv scripts\panel_control\venv
#   scripts\panel_control\venv\Scripts\pip install -r scripts\panel_control\requirements.txt

$ErrorActionPreference = "Continue"

$policy = Get-ExecutionPolicy -Scope Process
if ($policy -eq "Restricted" -or $policy -eq "AllSigned") {
    Write-Host ""
    Write-Host "   FAIL Falta el bypass de ExecutionPolicy. Corre primero:" -ForegroundColor Red
    Write-Host "        Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass" -ForegroundColor Yellow
    exit 1
}

$AQUI = Split-Path -Parent $MyInvocation.MyCommand.Path

try {
    $repoDetectado = git -C $AQUI rev-parse --show-toplevel 2>$null
} catch {}
if (-not $repoDetectado) {
    $repoDetectado = Read-Host "Ruta del repo finanzas-mcghr [C:\Users\ghriz\finanzas-mcghr]"
    if (-not $repoDetectado) { $repoDetectado = "C:\Users\ghriz\finanzas-mcghr" }
}
$REPO = $repoDetectado.Trim()

$PYTHONW = Join-Path $REPO "scripts\panel_control\venv\Scripts\pythonw.exe"
$TRAY_APP = Join-Path $REPO "scripts\panel_control\tray_app.py"
$PANEL_DIR = Join-Path $REPO "scripts\panel_control"
$STARTUP_DIR = [Environment]::GetFolderPath("Startup")
$LNK_PATH = Join-Path $STARTUP_DIR "FinanzasMCGHR_PanelControl.lnk"

if (-not (Test-Path $PYTHONW)) {
    Write-Host ""
    Write-Host "   FAIL No existe $PYTHONW" -ForegroundColor Red
    Write-Host "        Crea primero el venv propio de esta carpeta:" -ForegroundColor Yellow
    Write-Host "        py -3.12 -m venv scripts\panel_control\venv" -ForegroundColor White
    Write-Host "        scripts\panel_control\venv\Scripts\pip install -r scripts\panel_control\requirements.txt" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "======================================"
Write-Host "  Panel de Control -- Instalando autostart"
Write-Host "======================================"
Write-Host ""

try {
    $ws = New-Object -ComObject WScript.Shell
    $acceso = $ws.CreateShortcut($LNK_PATH)
    $acceso.TargetPath = $PYTHONW
    $acceso.Arguments = "`"$TRAY_APP`""
    $acceso.WorkingDirectory = $PANEL_DIR
    $acceso.Description = "Panel de Control MCGHR (bandeja del sistema)"
    $acceso.Save()
    Write-Host "  OK   Acceso directo creado en la carpeta de Inicio -- arranca oculto en cada inicio de sesion" -ForegroundColor Green
    Write-Host "       $LNK_PATH"
    Write-Host ""
    Write-Host "Para probarlo ahora mismo, sin cerrar sesion:" -ForegroundColor Cyan
    Write-Host "  & `"$PYTHONW`" `"$TRAY_APP`"" -ForegroundColor White
} catch {
    Write-Host "  FAIL No se pudo crear el acceso directo: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
