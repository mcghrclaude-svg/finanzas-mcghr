# CITA -- Common Issues To Avoid
# Finanzas MCGHR

Registro de errores repetidos en el proyecto y como prevenirlos.
Este archivo es el indice. El detalle completo de cada CITA vive en
docs/citas/CITA-0XX.md (usar la URL de la columna Archivo para web_fetch).
Actualizado automaticamente por cerrar-sesion.ps1 al cierre de cada sesion.

Nivel de prevencion:
  1-AUTOMATIZADO  El artefacto mismo detecta y bloquea el error
  2-HOOK          cerrar-sesion.ps1 o un git hook lo verifica
  3-CONTEXTO      Solo en contexto: reduce frecuencia, no garantiza prevencion

Senal de alarma: lo que Hernan puede observar sin conocimiento tecnico
para detectar que este error esta ocurriendo. Ver detalle completo en
el archivo individual de cada CITA.

---

| CITA | Titulo | Nivel | Archivo |
|------|--------|-------|---------|
| CITA-001 | Omitir Set-ExecutionPolicy en instrucciones de scripts PS1 | 1-AUTOMATIZADO | https://raw.githubusercontent.com/mcghrclaude-svg/finanzas-mcghr/main/docs/citas/CITA-001.md |
| CITA-002 | ErrorActionPreference Stop rompe scripts que corren fuera del repo | 1-AUTOMATIZADO | https://raw.githubusercontent.com/mcghrclaude-svg/finanzas-mcghr/main/docs/citas/CITA-002.md |
| CITA-003 | Get-ChildItem sin @() falla con un solo resultado en StrictMode | 1-AUTOMATIZADO | https://raw.githubusercontent.com/mcghrclaude-svg/finanzas-mcghr/main/docs/citas/CITA-003.md |
| CITA-004 | Asumir contenido de archivos sin leerlos en el turno actual | 3-CONTEXTO | https://raw.githubusercontent.com/mcghrclaude-svg/finanzas-mcghr/main/docs/citas/CITA-004.md |
| CITA-005 | Asumir schema de DB sin verificar la tabla real | 3-CONTEXTO | https://raw.githubusercontent.com/mcghrclaude-svg/finanzas-mcghr/main/docs/citas/CITA-005.md |
| CITA-006 | Variables VITE_* en .env.dev rompen el backend | 2-HOOK | https://raw.githubusercontent.com/mcghrclaude-svg/finanzas-mcghr/main/docs/citas/CITA-006.md |
| CITA-007 | Modulos nuevos creados en pages/ en lugar de modules/ | 2-HOOK | https://raw.githubusercontent.com/mcghrclaude-svg/finanzas-mcghr/main/docs/citas/CITA-007.md |
| CITA-008 | Commits con git add -A mezclan cambios de chats distintos | 1-AUTOMATIZADO | https://raw.githubusercontent.com/mcghrclaude-svg/finanzas-mcghr/main/docs/citas/CITA-008.md |
| CITA-009 | Caracteres especiales en codigo generan errores de encoding | 2-HOOK | https://raw.githubusercontent.com/mcghrclaude-svg/finanzas-mcghr/main/docs/citas/CITA-009.md |
| CITA-010 | Loop de fix sin diagnostico previo | 3-CONTEXTO | https://raw.githubusercontent.com/mcghrclaude-svg/finanzas-mcghr/main/docs/citas/CITA-010.md |
| CITA-011 | Inconsistencia interna entre archivos del mismo entregable | 1-AUTOMATIZADO | https://raw.githubusercontent.com/mcghrclaude-svg/finanzas-mcghr/main/docs/citas/CITA-011.md |
| CITA-012 | Divergencia silenciosa entre .claude\skills y el repo | 3-CONTEXTO | https://raw.githubusercontent.com/mcghrclaude-svg/finanzas-mcghr/main/docs/citas/CITA-012.md |
| CITA-013 | Hook autogenerador causa conflictos de merge entre branches paralelas | 3-CONTEXTO | https://raw.githubusercontent.com/mcghrclaude-svg/finanzas-mcghr/main/docs/citas/CITA-013.md |
