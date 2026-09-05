# INSTRUCCIONES DE EJECUCION:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\cerrar-sesion.ps1
# (normalmente no hace falta correrlo a mano -- el hook lo invoca automaticamente)

param(
    [string]$RepoPath = "",
    [switch]$AutoMode
)

$ErrorActionPreference = "Continue"

# Verificacion de ExecutionPolicy (solo en modo manual)
if (-not $AutoMode) {
    $policy = Get-ExecutionPolicy -Scope Process
    if ($policy -eq "Restricted" -or $policy -eq "AllSigned") {
        Write-Host ""
        Write-Host "   FAIL Falta el bypass de ExecutionPolicy. Corre primero:" -ForegroundColor Red
        Write-Host "        Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass" -ForegroundColor Yellow
        Write-Host ""
        exit 1
    }
}

# Auto-deteccion segura del repo
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
$RepoPath = $RepoPath.Trim()

if (-not (Test-Path $RepoPath)) {
    Write-Host "   FAIL No se encontro el repo en: $RepoPath" -ForegroundColor Red
    exit 1
}
Set-Location $RepoPath

# Guard anti-loop: no correr si el ultimo commit ya es nuestro
$lastMsg = git log -1 --pretty=%s 2>$null
if ($lastMsg -like "docs: auto-update*") { exit 0 }

Write-Host ">> Auditando repo y actualizando docs..." -ForegroundColor Cyan



function Get-EstadoArchivo {
    param($path)
    if (-not (Test-Path $path)) { return $null }
    $lines = @(Get-Content $path -ErrorAction SilentlyContinue)
    $count = $lines.Count
    $content = $lines -join "`n"
    $tieneTodo = $content -match "TODO"
    $esStubChico = ($count -le 10) -or ($content -match "en desarrollo") -or ($content -match "Proximamente")

    $estado = if ($esStubChico) {
        "STUB"
    } elseif ($tieneTodo) {
        "PARCIAL"
    } else {
        "IMPLEMENTADO"
    }

    return [PSCustomObject]@{
        Lineas = $count
        Estado = $estado
    }
}

$frontendMods = @()
$modPath = Join-Path $RepoPath "frontend\src\modules"
if (Test-Path $modPath) {
    foreach ($dir in @(Get-ChildItem $modPath -Directory -ErrorAction SilentlyContinue)) {
        $idx = Join-Path $dir.FullName "index.jsx"
        $info = Get-EstadoArchivo $idx
        if ($info) {
            $frontendMods += "| $($dir.Name) | $($info.Estado) | $($info.Lineas) lineas |"
        }
    }
}

$pwaMods = @()
$pwaModPath = Join-Path $RepoPath "pwa-gastos\src\modules"
if (Test-Path $pwaModPath) {
    foreach ($dir in @(Get-ChildItem $pwaModPath -Directory -ErrorAction SilentlyContinue)) {
        $idx = Join-Path $dir.FullName "index.jsx"
        $info = Get-EstadoArchivo $idx
        if ($info) {
            $pwaMods += "| $($dir.Name) | $($info.Estado) | $($info.Lineas) lineas |"
        }
    }
}

$backendRouters = @()
$routersPath = Join-Path $RepoPath "backend\api\v1\routers"
if (Test-Path $routersPath) {
    foreach ($f in @(Get-ChildItem $routersPath -Filter "*.py" -ErrorAction SilentlyContinue)) {
        $info = Get-EstadoArchivo $f.FullName
        if ($info) {
            $backendRouters += "| $($f.Name) | $($info.Estado) | $($info.Lineas) lineas |"
        }
    }
}

$ultimosCommits = (git log --oneline -10 2>$null) -join "`n"
$fecha = Get-Date -Format "yyyy-MM-dd HH:mm"



$warnings = @()

# CITA-006: Variables VITE_* en .env.dev
$envDev = Join-Path $RepoPath ".env.dev"
if (Test-Path $envDev) {
    $viteLines = @(Select-String -Path $envDev -Pattern "^VITE_" -ErrorAction SilentlyContinue)
    if ($viteLines.Count -gt 0) {
        $warnings += "CITA-006: .env.dev contiene variables VITE_* (moverlas a frontend/.env.local):"
        $viteLines | ForEach-Object { $warnings += "  $_" }
    }
}

# CITA-007: Modulos nuevos en pages/ en lugar de modules/
$pagesPath = Join-Path $RepoPath "frontend\src\pages"
if (Test-Path $pagesPath) {
    $pagesJsx = @(Get-ChildItem $pagesPath -Filter "*.jsx" -ErrorAction SilentlyContinue)
    if ($pagesJsx.Count -gt 0) {
        $warnings += "CITA-007: Archivos .jsx en src/pages/ (verificar si deberian estar en src/modules/):"
        $pagesJsx | ForEach-Object { $warnings += "  $($_.Name)" }
    }
}

# CITA-009: Caracteres no-ASCII en archivos del ultimo commit
# Excepcion: emojis/simbolos usados como iconos de UI/navegacion (Sidebar,
# botones, labels de menu, spinners) no cuentan como violacion. Se excluyen
# antes del chequeo:
#   - pares subrogados con alto D83C-D83E (pictogramas U+1F000-1FBFF: la
#     inmensa mayoria de los emojis estandar, ej. tag/banco/calendario)
#   - simbolos BMP U+2190-21FF (Arrows, ej. flecha circular de refresh)
#   - simbolos BMP U+2300-23FF (Misc Technical, ej. reloj de arena)
#   - simbolos BMP U+25A0-27BF (Geometric Shapes / Misc Symbols / Dingbats,
#     ej. engranaje, triangulos de coleccion) -- deliberadamente arranca en
#     25A0 para NO incluir Box Drawing (2500-257F), que son separadores de
#     comentario, no iconos
#   - selector de variacion U+FE0F y ZWJ U+200D (usados en secuencias emoji)
# La regla de ASCII puro sigue aplicando de lleno a texto real fuera de
# estos rangos: acentos, enie, guiones largos, separadores de comentario,
# etc. -- ver CITA-009.md.
$archivosCommit = @(git diff HEAD~1 --name-only 2>$null | Where-Object { $_ -match "\.(py|jsx|js|ps1|md)$" })
foreach ($archivo in $archivosCommit) {
    $rutaCompleta = Join-Path $RepoPath $archivo
    if (Test-Path $rutaCompleta) {
        $contenido = Get-Content $rutaCompleta -Raw -Encoding utf8 -ErrorAction SilentlyContinue
        $altoIni = [char]0xD83C; $altoFin = [char]0xD83E
        $bajoIni = [char]0xDC00; $bajoFin = [char]0xDFFF
        $flechaIni = [char]0x2190; $flechaFin = [char]0x21FF
        $tecIni    = [char]0x2300; $tecFin    = [char]0x23FF
        $simIni    = [char]0x25A0; $simFin    = [char]0x27BF
        $vs16      = [char]0xFE0F; $zwj       = [char]0x200D
        $patronEmoji    = "[$altoIni-$altoFin][$bajoIni-$bajoFin]"
        $patronSimbolos = "[$flechaIni-$flechaFin$tecIni-$tecFin$simIni-$simFin$vs16$zwj]"
        $sinEmojis = $contenido -replace $patronEmoji, '' -replace $patronSimbolos, ''
        if ($sinEmojis -match "[^\x00-\x7F]") {
            $warnings += "CITA-009: Caracteres no-ASCII detectados en: $archivo"
        }
    }
}

# Mostrar warnings
if ($warnings.Count -gt 0) {
    Write-Host ""
    Write-Host "   WARN Verificaciones CITA fallidas:" -ForegroundColor Yellow
    $warnings | ForEach-Object { Write-Host "        $_" -ForegroundColor Yellow }
    Write-Host ""
}



$claudeMdPath = Join-Path $RepoPath "CLAUDE.md"
$claudeMd = @"
# CLAUDE.md -- Finanzas MCGHR
# Generado automaticamente por cerrar-sesion.ps1 -- $fecha
# NO editar a mano. Editar el codigo real; este archivo se regenera solo.

## Inicio obligatorio de cada chat
1. web_fetch de este archivo:
   https://raw.githubusercontent.com/mcghrclaude-svg/finanzas-mcghr/main/CLAUDE.md
2. web_fetch del HANDOFF del dia:
   https://raw.githubusercontent.com/mcghrclaude-svg/finanzas-mcghr/main/docs/HANDOFF_$(Get-Date -Format 'yyyyMMdd').md
3. web_fetch del ADR para contexto de decisiones:
   https://raw.githubusercontent.com/mcghrclaude-svg/finanzas-mcghr/main/docs/ADR.md
4. web_fetch del CITA para evitar errores conocidos:
   https://raw.githubusercontent.com/mcghrclaude-svg/finanzas-mcghr/main/docs/CITA.md
NO usar project_knowledge_search -- puede estar desactualizado.

## Reglas de arquitectura (ver ADR.md para detalle y contexto)
- Base SQLAlchemy: backend/models/base.py (ADR-002)
- Frontend: Tailwind puro, sin CSS custom (ADR-004)
- Variables VITE_*: frontend/.env.local, nunca en .env.dev (ADR-005)
- IDs de catalogos: autogenerados como slug (ADR-006)
- Modulos nuevos: frontend/src/modules/ no en pages/ (ADR-007)
- completitud en DB: TEXT 'minimo'|'parcial'|'completo', nunca float (ADR-008)
- conftest.py: importar todos los modelos antes de create_all (ADR-011)

## Reglas de scripts PowerShell (ver CITA.md para detalle)
- SIEMPRE: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass (CITA-001)
- NUNCA: ErrorActionPreference = Stop a nivel global (CITA-002)
- SIEMPRE: @() alrededor de Get-ChildItem antes de .Count (CITA-003)
- SIEMPRE: default explicito en Read-Host (CITA-002)
- NUNCA: git rev-parse sin try-catch cuando el script corre fuera del repo (CITA-002)
- NUNCA: caracteres no-ASCII en codigo o comentarios (CITA-009)

## Reglas de proceso
- Leer archivo real antes de modificarlo -- mostrar output del web_fetch (CITA-004)
- Verificar PRAGMA table_info antes de modificar modelos de DB (CITA-005)
- Si un fix falla: diagnostico antes del segundo intento (CITA-010)
- Commits: listar archivos explicitos, nunca git add -A (CITA-008)

## Entornos -- Claude Code y Claude Desktop
- DB desarrollo: data/dev/finanzas_dev.db -- usar MCP sqlite_dev
- DB produccion: OneDrive/Finanzas MCGHR/Generales/finanzas.db -- NO escribir en sesiones de desarrollo
- Filesystem desarrollo: MCP filesystem_dev (C:\Users\ghriz\finanzas-mcghr)
- Filesystem produccion: MCP filesystem (OneDrive) -- NO tocar en sesiones de desarrollo
- Branch: nunca commitear directo en main -- usar branch por tema (ADR-010)
- Claude Code lee este archivo automaticamente al iniciar sesion en el repo

## Estado real de modulos frontend (src/modules/)
| Modulo | Estado | Detalle |
|--------|--------|---------|
$($frontendMods -join "`n")

## Estado real de modulos PWA (pwa-gastos/src/modules)
| Modulo | Estado | Detalle |
|--------|--------|---------|
$($pwaMods -join "`n")

## Estado real de routers backend (api/v1/routers/)
| Router | Estado | Detalle |
|--------|--------|---------|
$($backendRouters -join "`n")

## Ultimos 10 commits
$ultimosCommits
"@

Set-Content -Path $claudeMdPath -Value $claudeMd -Encoding utf8
Write-Host "   OK   CLAUDE.md regenerado" -ForegroundColor Green



$handoffDir = Join-Path $RepoPath "docs"
if (-not (Test-Path $handoffDir)) { New-Item -ItemType Directory -Path $handoffDir | Out-Null }
$handoffPath = Join-Path $handoffDir ("HANDOFF_" + (Get-Date -Format "yyyyMMdd") + ".md")

$commitsHoy = (git log --since="midnight" --oneline 2>$null) -join "`n"
$archivosHoy = @(git log --since="midnight" --name-only --pretty=format: 2>$null |
    Where-Object { $_ -ne "" } | Sort-Object -Unique) -join "`n"

$handoff = @"
# Handoff -- $fecha

## Commits de hoy
$commitsHoy

## Archivos tocados hoy
$archivosHoy

## Warnings CITA de esta sesion
$($warnings -join "`n")

## URLs para el proximo chat
CLAUDE.md:  https://raw.githubusercontent.com/mcghrclaude-svg/finanzas-mcghr/main/CLAUDE.md
HANDOFF:    https://raw.githubusercontent.com/mcghrclaude-svg/finanzas-mcghr/main/docs/HANDOFF_$(Get-Date -Format 'yyyyMMdd').md
ADR:        https://raw.githubusercontent.com/mcghrclaude-svg/finanzas-mcghr/main/docs/ADR.md
CITA:       https://raw.githubusercontent.com/mcghrclaude-svg/finanzas-mcghr/main/docs/CITA.md
"@

Set-Content -Path $handoffPath -Value $handoff -Encoding utf8
Write-Host "   OK   Handoff actualizado: docs/HANDOFF_$(Get-Date -Format 'yyyyMMdd').md" -ForegroundColor Green



git add CLAUDE.md docs/HANDOFF_*.md 2>$null
$staged = git diff --cached --name-only 2>$null
if ($staged) {
    git commit -m "docs: auto-update $fecha" --quiet 2>$null

    git rev-parse --abbrev-ref --symbolic-full-name "@{u}" 2>$null | Out-Null
    $tieneUpstream = ($LASTEXITCODE -eq 0)

    if (-not $tieneUpstream) {
        Write-Host "   WARN Sin upstream configurado, docs commiteados localmente" -ForegroundColor Yellow
    } else {
        git push --quiet 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   OK   Docs commiteados y pusheados" -ForegroundColor Green
        } else {
            Write-Host "   WARN Docs commiteados localmente, el push fallo" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "   OK   Sin cambios en docs" -ForegroundColor Green
}

# Contar grupos de advertencias (no lineas individuales)
$warningGroups = 0
if ($warnings.Count -gt 0) {
    $warnings | ForEach-Object { if ($_ -notlike "  *") { $warningGroups++ } }
}
if ($warningGroups -gt 0) {
    Write-Host ""
    Write-Host "   WARN Hay $warningGroups advertencia(s) CITA pendientes de resolver." -ForegroundColor Yellow
    Write-Host "        Ver detalle arriba." -ForegroundColor Yellow
}




