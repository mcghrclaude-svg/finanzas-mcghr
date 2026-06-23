# INSTRUCCIONES DE EJECUCION:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\chequear-conflictos.ps1 -Tema ux

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

$archivosBranch = @(git diff main...$branch --name-only 2>$null)

$otrasBranches = @(git branch -a 2>$null |
    ForEach-Object { $_.Trim() -replace '^\*\s*','' -replace '^remotes/origin/','' } |
    Where-Object { $_ -like "chat-*" -and $_ -ne $branch } |
    Sort-Object -Unique)

$conflictos = @()
foreach ($otra in $otrasBranches) {
    $archivosOtra = @(git diff main...$otra --name-only 2>$null)
    $solapados = $archivosBranch | Where-Object { $archivosOtra -contains $_ }
    if ($solapados) {
        $conflictos += [PSCustomObject]@{ Branch = $otra; Archivos = $solapados }
    }
}

Write-Host ""
if ($conflictos.Count -eq 0) {
    Write-Host "   OK   Sin solapamiento con otras branches activas." -ForegroundColor Green
    Write-Host "   Podes mergear a main:" -ForegroundColor Cyan
    Write-Host "     git checkout main" -ForegroundColor White
    Write-Host "     git merge $branch" -ForegroundColor White
    Write-Host "     git push" -ForegroundColor White
} else {
    Write-Host "   STOP Hay archivos en conflicto con otra branch activa:" -ForegroundColor Red
    foreach ($c in $conflictos) {
        Write-Host ""
        Write-Host "   Branch en conflicto: $($c.Branch)" -ForegroundColor Yellow
        $c.Archivos | ForEach-Object { Write-Host "     - $_" }
    }
    Write-Host ""
    Write-Host "   NO mergees todavia. Llevale este resultado al chat de '$($conflictos[0].Branch)'" -ForegroundColor Red
    Write-Host "   y pedile que haga git pull origin main antes de que vos mergees." -ForegroundColor Red
}
Write-Host ""
