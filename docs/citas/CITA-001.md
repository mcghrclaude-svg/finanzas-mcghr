# CITA-001 -- Omitir Set-ExecutionPolicy en instrucciones de scripts PS1

**Frecuencia:** 4+ veces en multiples chats
**Nivel:** 1-AUTOMATIZADO

**Error:**
El agente entrega scripts PS1 o instrucciones de ejecucion sin incluir
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass.
El usuario ve "cannot be loaded, not digitally signed" y el script no corre.

**Prevencion automatizada:**
Cada script PS1 generado debe tener en las primeras 3 lineas:
  # INSTRUCCIONES DE EJECUCION:
  #   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  #   .\nombre-del-script.ps1
Y ademas, verificacion en codigo al inicio del script:
  $policy = Get-ExecutionPolicy -Scope Process
  if ($policy -eq "Restricted" -or $policy -eq "AllSigned") { ... exit 1 }

**Senal de alarma para Hernan:**
Si el agente te da un comando de PS1 sin que la primera linea sea
Set-ExecutionPolicy, el paso esta faltando.
