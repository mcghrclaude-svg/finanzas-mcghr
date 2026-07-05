# CITA-013 -- Hook autogenerador causa conflictos de merge entre branches paralelas

**Frecuencia:** 1 vez detectada (2026-06-29, merge de chat-sync-mcp-lector-correos a main)
**Nivel:** 3-CONTEXTO

**Error:**
cerrar-sesion.ps1 corre automaticamente despues de cada commit (via hook) y
regenera CLAUDE.md y docs/HANDOFF_{fecha}.md por completo, basandose en el
estado de git en el momento exacto de ese commit (ultimos commits, warnings
CITA detectados, archivos tocados hoy). Si dos commits ocurren en branches
distintas el mismo dia -- por ejemplo una sesion de Claude Code trabajando en
una branch tematica, y otra accion (sesion separada, o el mismo hook corriendo
sobre main) commiteando directo en main -- cada uno regenera su propia version
de CLAUDE.md y del HANDOFF del dia, con contenido distinto pero igualmente
"correcto" en su momento. Al mergear esas branches, ambas versiones autogeneradas
chocan en conflicto, aunque el contenido real (codigo, CITA.md, docs escritos
a mano) se mergea sin problema.

**Lo que paso esta vez:**
La branch chat-sync-mcp-lector-correos sincronizo server.py y agrego CITA-012.
En paralelo, otra accion creo docs/PENDIENTES.md y el hook commiteo eso
directo en main. Al hacer git merge chat-sync-mcp-lector-correos sobre main,
git reporto CONFLICT (content) en CLAUDE.md y en docs/HANDOFF_20260629.md --
ambos generados automaticamente, ninguno editado a mano. El contenido real
(docs/CITA.md, mcp_servers/mcp_lector_correos/server.py) se mergeo limpio,
sin conflicto.

**Resolucion:**
Como ambos archivos en conflicto son 100% regenerables, no hace falta
resolver el conflicto linea por linea. Tomar cualquiera de las dos versiones
como base temporal y dejar que el proximo commit los regenere correctamente:
  git checkout --ours CLAUDE.md
  git checkout --ours docs/HANDOFF_{fecha}.md
  git add CLAUDE.md docs/HANDOFF_{fecha}.md
  git commit -m "merge: <branch> -- CLAUDE.md y HANDOFF se regeneran en proximo commit"
  git push
El siguiente commit (aunque sea trivial) dispara el hook y deja ambos
archivos consistentes con el estado real de main.

**Prevencion:**
No hay automatizacion hoy que evite el conflicto en si -- es consecuencia
de tener contenido autogenerado no-determinista en mas de una branch activa
el mismo dia. Mitigacion de proceso:
- Evitar que el hook corra sobre main directamente mientras hay una branch
  tematica abierta con cambios pendientes de mergear
- Si aparece CONFLICT solo en CLAUDE.md y/o docs/HANDOFF_*.md, no investigar
  el contenido -- aplicar la resolucion de arriba directamente
- Si el conflicto aparece tambien en otro archivo (codigo, ADR.md, CITA.md),
  ESO si requiere revision manual -- no usar --ours a ciegas en esos casos

**Senal de alarma para Hernan:**
Si un git merge reporta CONFLICT (content) y los archivos listados son
unicamente CLAUDE.md y/o docs/HANDOFF_*.md, es este escenario. Si aparecen
otros archivos en la lista de conflicto, frenar y pedir diagnostico real
antes de resolver con --ours.
