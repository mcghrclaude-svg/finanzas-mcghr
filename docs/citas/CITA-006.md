# CITA-006 -- Variables VITE_* en .env.dev rompen el backend

**Frecuencia:** 2 veces
**Nivel:** 2-HOOK

**Error:**
El agente pone variables VITE_* en .env.dev junto con las del backend.
pydantic-settings rechaza variables desconocidas y el backend no arranca.

**Prevencion:**
cerrar-sesion.ps1 verifica que .env.dev no contenga variables VITE_*.
Si las encuentra, muestra un warning con la linea exacta a mover.
Las variables VITE_* van SIEMPRE en frontend/.env.local.

**Senal de alarma para Hernan:**
Si el backend no arranca y el error menciona "extra inputs are not permitted"
o una variable VITE_*, este error esta ocurriendo.
