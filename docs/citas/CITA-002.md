# CITA-002 -- ErrorActionPreference Stop rompe scripts que corren fuera del repo

**Frecuencia:** 3 veces
**Nivel:** 1-AUTOMATIZADO

**Error:**
$ErrorActionPreference = "Stop" a nivel global hace que un comando git
que falla (porque el script corre fuera del repo) detenga todo el script
antes de llegar al Read-Host de fallback. El usuario ve un error rojo
y no puede ingresar la ruta del repo.

**Prevencion automatizada:**
Nunca usar $ErrorActionPreference = "Stop" a nivel global en scripts PS1.
Patron obligatorio para deteccion del repo:
  $ErrorActionPreference = "Continue"
  try {
      $detected = git rev-parse --show-toplevel 2>$null
      if ($LASTEXITCODE -eq 0 -and $detected) { $RepoPath = $detected }
  } catch {}
  if (-not $RepoPath) {
      $RepoPath = Read-Host "Ruta del repo [C:\Users\ghriz\finanzas-mcghr]"
      if (-not $RepoPath) { $RepoPath = "C:\Users\ghriz\finanzas-mcghr" }
  }

**Senal de alarma para Hernan:**
Si el script muestra un error rojo con "fatal: not a git repository"
y termina sin pedirte la ruta, este error esta ocurriendo.
