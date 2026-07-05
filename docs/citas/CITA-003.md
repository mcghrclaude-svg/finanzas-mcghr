# CITA-003 -- Get-ChildItem sin @() falla con un solo resultado en StrictMode

**Frecuencia:** 2 veces
**Nivel:** 1-AUTOMATIZADO

**Error:**
Get-ChildItem puede devolver un objeto unico (no array) cuando encuentra
un solo archivo. Con Set-StrictMode activo, llamar .Count sobre ese objeto
lanza "The property Count cannot be found on this object".

**Prevencion automatizada:**
Siempre envolver Get-ChildItem en @():
  $archivos = @(Get-ChildItem $ruta -Filter "*.py" -ErrorAction SilentlyContinue)
  $count = $archivos.Count

**Senal de alarma para Hernan:**
Error "The property Count cannot be found on this object" en scripts PS1.
