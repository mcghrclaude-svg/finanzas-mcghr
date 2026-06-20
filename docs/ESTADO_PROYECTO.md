# ESTADO_PROYECTO.md — actualizado post-sesion Junio 2026
# Plataforma Financiera MCGHR

**Fecha:** Junio 2026
**Proposito:** Documento de handoff para retomar el proyecto en claude.ai con contexto completo.

---

## Que es este proyecto

Plataforma de gestion financiera familiar para GHR (Hernan) y MC (Martha).
Arquitectura de 5 capas:

1. **Capa 0 — Base de datos:** SQLite en OneDrive (`finanzas.db`) con schema
   de doble entrada contable, multi-moneda. Schema v1.2 aplicado.
2. **Capa 1 — ETL Claude Desktop:** Tarea programada diaria a las 4am.
   Procesa correos Gmail, PDFs en OneDrive y JSONs de la PWA.
   Escribe en SQLite via MCP sqlite.
3. **Capa 2 — Backend FastAPI:** API REST en http://localhost:8000
4. **Capa 3 — Frontend React:** http://localhost:3000
5. **Capa 4 — PWA Mobile:** Pendiente (Entrega 4)

---

## Como arrancar el stack

```powershell
# Opcion 1 — Script de arranque (recomendado)
powershell -ExecutionPolicy Bypass -File "C:\Users\ghriz\finanzas-mcghr\iniciar_finanzas.ps1"

# Opcion 2 — Manual
# Terminal 1:
cd C:\Users\ghriz\finanzas-mcghr
venv\Scripts\activate
uvicorn backend.main:app --reload --port 8000

# Terminal 2:
cd C:\Users\ghriz\finanzas-mcghr\frontend
npm run dev
```

URLs:
- App: http://localhost:3000
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

---

## Estado por componente

### Base de datos

| Item | Estado |
|---|---|
| Schema v1.1 (22 tablas + 5 vistas) | COMPLETO |
| Schema v1.2 (+id_evento, +estado_enriquecimiento) | COMPLETO — aplicado en OneDrive |
| Seed catalogos (25 cat, 12 cuentas, 22 contrapartes, 2 personas) | COMPLETO |
| Seed inbox (8 transacciones dummy para dev) | LISTO — ejecutar manualmente |

### Capa 1 — ETL (Claude Desktop)

| Item | Estado |
|---|---|
| Skills Python (lector_correos, desproteger_pdf, auditor) | COMPLETO |
| MCP server mcp_lector_correos | COMPLETO |
| Prompt tarea programada Claude Desktop | COMPLETO — docs/ETL_PROMPT_CLAUDE_DESKTOP.md |
| Tokens OAuth Gmail hernan | PENDIENTE — accion manual |
| Tokens OAuth Gmail malu | PENDIENTE — accion manual |
| Tarea programada configurada en Claude Desktop (4am) | PENDIENTE — accion manual |

### Capa 2 — Backend FastAPI

| Item | Estado | Tests |
|---|---|---|
| Core: database, config, exceptions | COMPLETO | — |
| Modelos SQLAlchemy (catalogo, transaccion, regla, inbox_mobile) | COMPLETO | — |
| Router catalogos (listar cat/cuentas/contrapartes/personas) | COMPLETO | 5/5 |
| Router catalogos export PWA | COMPLETO | 1/1 |
| Router inbox (7 endpoints) | COMPLETO | 13/13 |
| Resto de routers (transacciones, presupuestos, etc.) | TODO — placeholder | — |

**Total tests pasando: 18/18**

### Capa 3 — Frontend React

| Item | Estado |
|---|---|
| Estructura Vite + Tailwind + Zustand + React Query | COMPLETO |
| Layout + Sidebar + Header | COMPLETO |
| Modulo Catalogos | COMPLETO |
| Modulo Inbox | COMPLETO — pantalla funcional con 3 secciones |
| Dashboard | TODO — placeholder |
| Resto de modulos | TODO — placeholder |

### Capa 4 — PWA Mobile

| Item | Estado |
|---|---|
| Formato JSON OneDrive documentado | COMPLETO — docs/ETL_DISENO_FUNCIONAL.md |
| carpeta OneDrive/PWA/ creada | COMPLETO |
| catalogos.json generado por backend | COMPLETO — POST /catalogos/export/pwa |
| Codigo PWA (React instalable en iPhone) | PENDIENTE — Entrega 4 |

---

## Roadmap

### Punto 3 — ETL + Inbox

| Entrega | Descripcion | Estado |
|---|---|---|
| 3A | Backend inbox: service, repo, router, tests | COMPLETO |
| 3B | Schema v1.2 + prompt ETL Claude Desktop | COMPLETO |
| 3C | Frontend Inbox + export catalogos PWA | COMPLETO |

### Punto 4 — PWA Mobile (proximo)

| Entrega | Descripcion |
|---|---|
| 4A | PWA React: captura rapida de gastos desde iPhone |
| 4B | Integracion con ETL via OneDrive |

### Punto 5 — Completar routers backend (futuro)

Transacciones, presupuestos, obligaciones, inversiones, reportes, dashboard real.

---

## Decisiones de arquitectura (Junio 2026)

| Decision | Resultado | Razon |
|---|---|---|
| Motor del ETL | Claude Desktop tarea programada /schedule (no script Python) | Sin costo adicional API, razonamiento sofisticado, scheduler nativo |
| Schedule ETL | Diario a las 4am | Peticion del usuario |
| ETL escribe en DB | Directo a SQLite via MCP sqlite | Independiente del backend |
| Aprendizaje ETL | Lee reglas_clasificacion + ultimas 50 tx confirmadas como contexto | Mas preciso que solo regex |
| Correlacion eventos | Campo id_evento en transacciones (hash monto+cuenta+fecha) | Unifica notificacion + factura + extracto en una sola tx |
| Enriquecimiento | Campo estado_enriquecimiento (inicial/enriquecido/completo) | Seguimiento del ciclo contable |
| Catalogos para PWA | Backend exporta JSON a OneDrive, PWA lo lee desde ahi | Sin llamadas API desde el celular |
| PWA comunicacion | JSONs en OneDrive, sin API calls | Sin servidor adicional |
| Script arranque | iniciar_finanzas.ps1 en raiz del repo | Un click desde barra de tareas |

---

## Acciones manuales pendientes (por el usuario)

| # | Accion | Instrucciones |
|---|---|---|
| 1 | Seed inbox en DB dev | Ver instrucciones en docs/INSTRUCCIONES_POST_INSTALACION.md |
| 2 | Tokens OAuth Gmail hernan | Ver instrucciones en docs/INSTRUCCIONES_POST_INSTALACION.md |
| 3 | Tokens OAuth Gmail malu | Ver instrucciones en docs/INSTRUCCIONES_POST_INSTALACION.md |
| 4 | Configurar tarea ETL en Claude Desktop | Ver docs/ETL_CONFIGURACION_CLAUDE_DESKTOP.md |
| 5 | Agregar script arranque a barra de tareas | Ver instrucciones en docs/INSTRUCCIONES_POST_INSTALACION.md |

---

## Issues abiertos

| # | Titulo | Prioridad |
|---|---|---|
| #2 | Tokens OAuth Gmail hernan y malu | ALTA — bloqueante para ETL |
| #4 | Configurar autoforward iPhone Martha | MEDIA |
| #5 | Regenerar token GitHub | URGENTE |
| #8 | Configurar tarea programada ETL Claude Desktop | ALTA |
| #9 | Implementar routers backend pendientes | MEDIA |
| #10 | PWA Mobile — Entrega 4 | BAJA |

---

## Lo que NO esta en el repo (por seguridad)

| Archivo | Ubicacion en PC | Razon |
|---|---|---|
| `config_correos.json` | `C:\Users\ghriz\.claude\` | Credenciales — en .gitignore |
| Tokens OAuth Gmail | `C:\Users\ghriz\.gmail-mcp\tokens\` | Tokens sensibles |
| `finanzas.db` | OneDrive | DB con datos reales — en .gitignore |
| `.env` / `.env.prod` | raiz del repo local | Variables con valores reales |

---

## Documentacion del Punto 3

| Documento | Contenido |
|---|---|
| `docs/ETL_DISENO_FUNCIONAL.md` | Flujo completo, correlacion eventos, clasificacion |
| `docs/ETL_PROMPT_CLAUDE_DESKTOP.md` | Prompt completo de la tarea programada del ETL |
| `docs/ETL_CONFIGURACION_CLAUDE_DESKTOP.md` | Como configurar la tarea en Claude Desktop |
| `docs/DISENO_3A_INBOX_BACKEND.md` | Endpoints inbox, logica, aprendizaje |
| `docs/DISENO_3B_ETL_PROMPT.md` | Schema v1.2, diseño del prompt |
| `docs/DISENO_3C_FRONTEND_INBOX_PWA.md` | Frontend Inbox, export catalogos, formato PWA |
| `docs/INSTRUCCIONES_POST_INSTALACION.md` | Pasos manuales pendientes con instrucciones detalladas |

---

*Ultima actualizacion: Junio 2026 — Plataforma Financiera MCGHR*
