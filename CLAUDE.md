# CLAUDE.md -- Finanzas MCGHR
# Generado automaticamente por cerrar-sesion.ps1 -- 2026-09-27 20:25
# NO editar a mano. Editar el codigo real; este archivo se regenera solo.

## Inicio obligatorio de cada chat
1. web_fetch de este archivo:
   https://raw.githubusercontent.com/mcghrclaude-svg/finanzas-mcghr/main/CLAUDE.md
2. web_fetch del HANDOFF del dia:
   https://raw.githubusercontent.com/mcghrclaude-svg/finanzas-mcghr/main/docs/HANDOFF_20260927.md
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
- SIEMPRE crear la rama del tema ANTES del primer cambio de codigo, aunque
  el chat ya haya mergeado otra rama antes -- volver a main tras un merge
  no habilita a seguir commiteando ahi (CITA-019, bloqueado por hook)

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
| Catalogos | PARCIAL | 550 lineas |
| Dashboard | IMPLEMENTADO | 116 lineas |
| Inbox | IMPLEMENTADO | 21 lineas |
| Inversiones | STUB | 4 lineas |
| Obligaciones | STUB | 4 lineas |
| Presupuesto | IMPLEMENTADO | 236 lineas |
| PWA | IMPLEMENTADO | 272 lineas |
| Tools | PARCIAL | 410 lineas |
| Transacciones | IMPLEMENTADO | 744 lineas |

## Estado real de modulos PWA (pwa-gastos/src/modules)
| Modulo | Estado | Detalle |
|--------|--------|---------|
| Actividad | PARCIAL | 115 lineas |
| Bandeja | STUB | 16 lineas |
| Configuracion | IMPLEMENTADO | 294 lineas |
| Home | PARCIAL | 221 lineas |
| NuevoGasto | IMPLEMENTADO | 373 lineas |
| ResumenMes | STUB | 18 lineas |

## Estado real de routers backend (api/v1/routers/)
| Router | Estado | Detalle |
|--------|--------|---------|
| analitica.py | PARCIAL | 72 lineas |
| backup.py | PARCIAL | 92 lineas |
| catalogos.py | IMPLEMENTADO | 518 lineas |
| dashboard.py | PARCIAL | 107 lineas |
| home_config.py | IMPLEMENTADO | 64 lineas |
| inbox.py | IMPLEMENTADO | 358 lineas |
| inversiones.py | PARCIAL | 111 lineas |
| obligaciones.py | PARCIAL | 113 lineas |
| presupuestos.py | IMPLEMENTADO | 239 lineas |
| pwa_config.py | IMPLEMENTADO | 191 lineas |
| reglas.py | PARCIAL | 73 lineas |
| reportes.py | PARCIAL | 135 lineas |
| tools.py | PARCIAL | 434 lineas |
| transacciones.py | PARCIAL | 173 lineas |
| __init__.py | IMPLEMENTADO | 33 lineas |

## Ultimos 10 commits
9ff36f5 feat(home): unifica todo el Home a mes calendario y compacta el layout
88089d6 docs: auto-update 2026-09-27 20:06
d54d6f4 feat(home): agrega torta de gasto por categoria y compacta el layout (variante K)
be68a3e docs: auto-update 2026-09-27 19:31
8f29375 feat(home): reconstruye la pagina Home segun la variante D aprobada
2147263 docs: auto-update 2026-09-27 19:19
749287f refactor(transacciones): extrae DetailPanel y helpers compartidos a archivos propios
224ffb5 docs: auto-update 2026-09-27 14:52
ad467e4 fix(backend): saca caracteres no-ASCII de las lineas que agrego en este chat (CITA-009)
1c10ae5 docs: auto-update 2026-09-27 14:50
