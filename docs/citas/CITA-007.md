# CITA-007 -- Modulos nuevos creados en pages/ en lugar de modules/

**Frecuencia:** 2 veces
**Nivel:** 2-HOOK

**Error:**
El agente crea un modulo nuevo en frontend/src/pages/ en lugar de
frontend/src/modules/. App.jsx importa desde modules/, asi que
el modulo en pages/ nunca se renderiza aunque el codigo sea correcto.

**Prevencion:**
cerrar-sesion.ps1 detecta archivos .jsx nuevos en src/pages/ y muestra
un warning indicando que probablemente deberian estar en src/modules/.

**Senal de alarma para Hernan:**
Si navegas a una URL y ves el placeholder "en desarrollo" aunque
el agente dijo que implemento el modulo, este error puede estar ocurriendo.
