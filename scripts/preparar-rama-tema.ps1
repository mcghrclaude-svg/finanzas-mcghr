# INSTRUCCIONES DE EJECUCION:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\preparar-rama-tema.ps1 -Tema ux
#   .\preparar-rama-tema.ps1 -Tema backend

param(
    [string]$RepoPath = "",
    [Parameter(Mandatory=$true)]
    [string]$Tema
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

$branch = "chat-$Tema"

git fetch origin --quiet 2>$null
git checkout main --quiet 2>$null
git pull origin main --quiet 2>$null

$existe = git branch --list $branch 2>$null
if ($existe) {
    git checkout $branch --quiet 2>$null
    git merge main --quiet -m "merge: sync main -> $branch" 2>$null
    Write-Host "   OK   Branch '$branch' actualizada con los ultimos cambios de main" -ForegroundColor Green
} else {
    git checkout -b $branch --quiet 2>$null
    Write-Host "   OK   Branch '$branch' creada desde main" -ForegroundColor Green
}

Write-Host ""
Write-Host "Trabaja normalmente en el chat de '$Tema'." -ForegroundColor Cyan
Write-Host "Al terminar la sesion, corre:" -ForegroundColor Cyan
Write-Host "  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass" -ForegroundColor White
Write-Host "  .\scripts\chequear-conflictos.ps1 -Tema $Tema" -ForegroundColor White
