# CLAUDE.md -- Finanzas MCGHR
# Generado automaticamente por cerrar-sesion.ps1 -- 2026-06-29 22:04
# NO editar a mano. Editar el codigo real; este archivo se regenera solo.

## Inicio obligatorio de cada chat
1. web_fetch de este archivo:
   https://raw.githubusercontent.com/mcghrclaude-svg/finanzas-mcghr/main/CLAUDE.md
2. web_fetch del HANDOFF del dia:
   https://raw.githubusercontent.com/mcghrclaude-svg/finanzas-mcghr/main/docs/HANDOFF_20260629.md
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
| Analitica | STUB | 5 lineas |
| Backup | STUB | 4 lineas |
| Catalogos | IMPLEMENTADO | 318 lineas |
| Dashboard | IMPLEMENTADO | 182 lineas |
| Inbox | IMPLEMENTADO | 21 lineas |
| Inversiones | STUB | 4 lineas |
| Obligaciones | STUB | 4 lineas |
| Presupuesto | STUB | 4 lineas |
| Transacciones | IMPLEMENTADO | 830 lineas |

## Estado real de routers backend (api/v1/routers/)
| Router | Estado | Detalle |
|--------|--------|---------|
| analitica.py | IMPLEMENTADO | 72 lineas |
| backup.py | IMPLEMENTADO | 92 lineas |
| catalogos.py | IMPLEMENTADO | 465 lineas |
| dashboard.py | IMPLEMENTADO | 120 lineas |
| inbox.py | IMPLEMENTADO | 245 lineas |
| inversiones.py | IMPLEMENTADO | 98 lineas |
| obligaciones.py | IMPLEMENTADO | 89 lineas |
| presupuestos.py | IMPLEMENTADO | 150 lineas |
| reglas.py | IMPLEMENTADO | 73 lineas |
| reportes.py | IMPLEMENTADO | 86 lineas |
| transacciones.py | IMPLEMENTADO | 117 lineas |
| __init__.py | IMPLEMENTADO | 27 lineas |

## Ultimos 10 commits
69c864c docs: agregar seccion pendientes al HANDOFF -- deuda tecnica tamano_bytes
c740faa docs: auto-update 2026-06-29 22:03
ac47098 docs: agregar pendiente tamanyo_bytes en HANDOFF (deuda tecnica CITA-009)
f9cd73b docs: auto-update 2026-06-29 21:58
80ec82e sync: propagar mejoras de .claude\skills a mcp_lector_correos/server.py (CITA-012)
bf3a7ed docs: auto-update 2026-06-29 21:33
3695a62 chore: eliminar Dashboard legacy de pages/ (ADR-007, CITA-007)
9318d75 docs: auto-update 2026-06-29 21:26
3189ec2 docs: agregar ADR-013 -- separacion de entornos dev/prod en Claude Desktop
af9735c docs: auto-update 2026-06-29 21:09
