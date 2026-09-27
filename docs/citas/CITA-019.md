# CITA-019 -- Agente commitea directo en main en vez de crear una rama primero

**Frecuencia:** 2 veces (mismo error, misma sesion)
**Nivel:** 1-AUTOMATIZADO

**Error:**
El agente hace cambios de codigo y los commitea parado en main, en vez de
crear la rama del tema primero (ADR-010). Pasa incluso despues de haber
creado y mergeado ramas correctamente antes en la misma sesion: al volver
a main tras un merge, el siguiente cambio -- a veces en un subsistema
distinto, por ejemplo scripts/panel_control despues de haber trabajado
frontend/backend -- se empieza a editar directo ahi por inercia, sin
acordarse de crear la rama nueva antes de tocar archivos.

**Prevencion automatizada:**
Hook pre-commit (.git/hooks/pre-commit) bloquea cualquier commit hecho
parado en main que toque archivos fuera de CLAUDE.md/docs/ (el
auto-update de cerrar-sesion.ps1 sigue permitido ahi, y un merge de
verdad -- MERGE_HEAD presente -- tambien). El mensaje de error trae el
comando exacto para mover lo que esta staged a una rama nueva sin perder
el trabajo.

**Senal de alarma para Hernan:**
Si un `git commit` se rechaza con "Estas por commitear directo en main
(CITA-019)", el hook esta funcionando como corresponde -- hay que crear
la rama del tema y volver a commitear ahi. Si en algun momento un commit
de codigo aparece igual en el historial de main sin pasar por un PR
mergeado, el hook no esta instalado en esa maquina (no viaja con
`git clone`, ver CITA-002 sobre instalacion de hooks) o alguien uso
`--no-verify` a proposito.
