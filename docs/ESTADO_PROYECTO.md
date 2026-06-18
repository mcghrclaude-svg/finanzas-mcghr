# Estado del proyecto — Finanzas MCGHR
**Fecha:** Junio 2026
**Proposito:** Documento de handoff para retomar el proyecto en claude.ai con contexto completo.

---

## Que es este proyecto

Plataforma de gestion financiera familiar para GHR (Hernan) y MC (Martha).
Arquitectura de 4 capas:

1. **Capa 0 — Base de datos:** SQLite en OneDrive (`finanzas.db`) con schema
   de doble entrada contable, multi-moneda
2. **Capa 1 — ETL Claude Desktop:** Tarea programada que corre diariamente a las
   4am. Procesa correos Gmail, PDFs en OneDrive y JSONs de la PWA. Clasifica con
   razonamiento de Claude Desktop. Escribe en SQLite via MCP sqlite.
3. **Capa 2 — Backend FastAPI:** API REST para que el frontend lea y escriba datos.
4. **Capa 3 — Frontend React:** Dashboard + Inbox + gestion de catalogos.
5. **Capa 4 — PWA Mobile:** App instalable en iPhone para captura rapida de gastos.
   Comunica via JSONs en OneDrive (no via API).

---

## Estado por componente

### Base de datos

| Item | Estado |
|---|---|
| Schema v1.1 aplicado (22 tablas + 5 vistas) | COMPLETO |
| Schema v1.2 (campos correlacion ETL) | PENDIENTE — Entrega 3B |
| Seed catalogos (25 categorias, 12 cuentas, 22 contrapartes, 2 personas) | COMPLETO |

### Capa 1 — ETL (Claude Desktop)

| Item | Estado |
|---|---|
| Skill lector_correos.py | COMPLETO — codigo listo |
| Skill desproteger_pdf.py | COMPLETO — codigo listo |
| Skill auditor_correos.py | COMPLETO — codigo listo |
| MCP server mcp_lector_correos | COMPLETO — codigo listo |
| Tokens OAuth Gmail hernan y malu | PENDIENTE — accion manual |
| config_correos.json real en PC | PENDIENTE — accion manual |
| Prompt tarea programada Claude Desktop | PENDIENTE — Entrega 3B |
| Tarea programada configurada (4am daily) | PENDIENTE — Entrega 3B |

**Nota arquitectural importante (Junio 2026):**
El ETL NO es un script Python standalone que llama a Claude API.
Es una tarea programada de Claude Desktop (/schedule) que usa los MCP tools
configurados en la PC. Claude Desktop es el motor de razonamiento y
orquestacion. Los skills Python son herramientas que Claude Desktop invoca.
Ver: `docs/ETL_DISENO_FUNCIONAL.md`

### Capa 2 — Backend FastAPI

| Item | Estado |
|---|---|
| Estructura de carpetas y main.py | COMPLETO |
| Modelos SQLAlchemy (backend/models/) | COMPLETO |
| Core: database.py, config.py, exceptions.py | COMPLETO |
| Router catalogos + service + repo + tests | COMPLETO — 22/22 tests passing |
| Router inbox + service + repo + tests | PENDIENTE — Entrega 3A |
| Router transacciones (implementacion real) | PENDIENTE |
| Router presupuestos (implementacion real) | PENDIENTE |
| Resto de routers | PENDIENTE |
| Endpoint export catalogos para PWA | PENDIENTE — Entrega 3C |

### Capa 3 — Frontend React

| Item | Estado |
|---|---|
| Estructura Vite + Tailwind + Zustand | COMPLETO |
| Modulo Catalogos | COMPLETO |
| Modulo Inbox | PENDIENTE — Entrega 3C |
| Dashboard | COMPLETO (con mock data) |
| Resto de modulos | PENDIENTE |

### Capa 4 — PWA Mobile

| Item | Estado |
|---|---|
| Diseno funcional | PENDIENTE — Entrega 4 |
| Implementacion | PENDIENTE — Entrega 4 |

---

## Roadmap de entregas activo

### Punto 3 — ETL + Inbox (en progreso)

| Entrega | Descripcion | Estado |
|---|---|---|
| 3A | Backend Inbox: service + repo + router real + tests + seed | PENDIENTE |
| 3B | Schema v1.2 + prompt ETL Claude Desktop + config tarea programada | PENDIENTE |
| 3C | Frontend pantalla Inbox + endpoint export catalogos PWA | PENDIENTE |

**Orden:** 3A → validar → 3B → validar → 3C → validar

### Punto 4 — PWA Mobile (futuro)

| Entrega | Descripcion |
|---|---|
| 4A | PWA React: captura rapida, foto, catalogacion opcional |
| 4B | Formato JSON OneDrive + integracion con ETL |

---

## Decisiones de arquitectura registradas (Junio 2026)

| Decision | Resultado | Razon |
|---|---|---|
| Motor del ETL | Claude Desktop tarea programada (no script Python + Claude API) | Sin costo adicional de API, razonamiento mas sofisticado, /schedule nativo |
| Schedule ETL | Diario a las 4am | Peticion del usuario |
| ETL escribe en DB | Directo a SQLite via MCP sqlite (no via API REST) | ETL debe funcionar independientemente del backend |
| Aprendizaje ETL | Lee reglas_clasificacion + ultimas 50 tx confirmadas como contexto | Mas preciso que solo patrones regex |
| Correlacion eventos | Campo id_evento en transacciones (hash monto+cuenta+fecha) | Permite unificar notificacion + factura + extracto en una sola tx |
| Enriquecimiento | Campo estado_enriquecimiento (inicial/enriquecido/completo) | Saber si una tx todavia puede recibir mas datos |
| Catalogos para PWA | Backend exporta JSON a OneDrive, PWA lo lee desde ahi | Sin llamadas API desde el celular, funciona offline |
| PWA comunicacion | JSONs en OneDrive, sin API calls | Sin servidor adicional, funciona sin PC encendida |

---

## Issues abiertos

| # | Titulo | Prioridad | Notas |
|---|---|---|---|
| #2 | Tokens OAuth Gmail hernan y malu | ALTA — bloqueante para ETL real | Accion manual del usuario |
| #3 | config_correos.json real en PC | ALTA — bloqueante para ETL real | No va al repo |
| #4 | Configurar autoforward iPhone Martha | MEDIA | Martha debe hacerlo en su iPhone |
| #5 | Regenerar token GitHub | URGENTE | Token anterior expuesto en chat |
| #7 | Schema v1.2 — campos correlacion ETL | ALTA — Entrega 3B | id_evento + estado_enriquecimiento |
| #8 | Prompt ETL Claude Desktop | ALTA — Entrega 3B | Ver docs/DISENO_3B_ETL_PROMPT.md |

---

## Lo que NO esta en el repo (por seguridad)

| Archivo | Ubicacion en PC | Razon |
|---|---|---|
| `config_correos.json` | `C:\Users\ghriz\.claude\` | Contiene credenciales — en .gitignore |
| Tokens OAuth Gmail | `C:\Users\ghriz\.gmail-mcp\tokens\` | Tokens sensibles |
| `finanzas.db` | OneDrive | DB con datos reales — en .gitignore |
| `.env` / `.env.prod` | raiz del repo local | Variables con valores reales |

---

## Documentacion del Punto 3

| Documento | Contenido |
|---|---|
| `docs/ETL_DISENO_FUNCIONAL.md` | Que hace el ETL, flujo completo, correlacion de eventos, clasificacion |
| `docs/DISENO_3A_INBOX_BACKEND.md` | Endpoints inbox, logica de negocio, aprendizaje por confirmacion |
| `docs/DISENO_3B_ETL_PROMPT.md` | Schema v1.2, borrador del prompt ETL, configuracion Claude Desktop |
| `docs/DISENO_3C_FRONTEND_INBOX_PWA.md` | Pantalla Inbox React, exportacion catalogos, formato JSON PWA |

---

*Ultima actualizacion: Junio 2026 — Plataforma Financiera MCGHR*
