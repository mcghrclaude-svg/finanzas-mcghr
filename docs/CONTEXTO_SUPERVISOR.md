# CONTEXTO_SUPERVISOR.md
# Estado del proyecto al 2026-07-04
# Para iniciar un nuevo chat supervisor sin perder contexto

## Objetivo del proyecto
App de finanzas personales para la familia Rizzi (GHR=Hernan, MC=Martha).
Stack: FastAPI backend, React frontend, SQLite, Claude Desktop como ETL.

## Estado actual
- UX de Transacciones: funcional con revision de transacciones pendientes
- Catalogos: funcional con pestana Pending para EPs del ETL
- Settings > Tools: funcional (solo en dev, VITE_ENV=dev)
- ETL: disenado y documentado, prompt listo, NO configurado en Cowork todavia
- DB dev: migraciones v1.0 a v1.4b aplicadas

## Issues abiertos (GitHub)
- #47 [bug/alta] Contraparte confirmada no aparece al recargar transaccion
- #40 [bug/baja] cerrar-sesion.ps1 mensaje falso de push (ya mergeado el fix)
- #33 [feature] PEN-001: renombrar tamano_bytes
- #34 [feature] PEN-002: UX para correccion manual de correlaciones ETL
- #35 [feature] PEN-003: ETL modo rango de fechas
- #36 [feature] PEN-004: ETL propone entidades nuevas (implementado parcialmente)
- #37 [feature] PEN-005: pantalla admin dev (implementado como Tools)
- #38 [feature] PEN-006: ABM reglas clasificacion y periodos financieros
- #39 [feature] PEN-007: guard Tools en produccion con pin

## Proximo paso critico
Configurar el ETL en Cowork de Claude Desktop para hacer la primera
prueba real con data de Gmail. Ver docs/ETL_PROMPT_CLAUDE_DESKTOP.md
y docs/ETL_CONFIGURACION_CLAUDE_DESKTOP.md.

## Pendiente de seguridad
Rotar el GitHub Personal Access Token en claude_desktop_config.json
(estuvo expuesto en una conversacion). Ir a:
github.com > Settings > Developer settings > Personal access tokens

## Reglas de supervision (para el chat supervisor)
- Siempre pedir diagnostico antes de aprobar cambios
- Verificar con PRAGMA/SELECT antes de cualquier migracion
- Aprobar diff antes de cualquier commit
- Una tarea = un commit, nunca mezclar
- Merge a main siempre con chequear-conflictos.ps1 primero
- Si hay conflicto solo en CLAUDE.md y HANDOFF: usar --ours (CITA-013)
- Cuando Code se compacta: cortar, mergear lo que esta listo, nueva sesion
- Senal de alarma: si Code propone modificar un archivo sin haberlo leido
  en ese turno, frenar (CITA-004)
