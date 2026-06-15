# Estado del proyecto — Finanzas MCGHR
**Fecha:** Junio 2026  
**Propósito:** Documento de handoff para retomar el proyecto en claude.ai con contexto completo.

---

## Qué es este proyecto

Plataforma de gestión financiera familiar para GHR (Hernan) y MC (Martha).  
Arquitectura de 4 capas:

1. **Capa 0 — Base de datos:** SQLite en OneDrive (`finanzas.db`) con schema de doble entrada contable, multi-moneda
2. **Capa 1 — Scripts Claude Desktop:** Procesamiento automático de correos bancarios → clasificación con Claude API → inserción en DB
3. **Capa 2 — Backend FastAPI:** API REST para exposición de datos (en construcción)
4. **Capa 3 — Frontend React:** Dashboard web local (en construcción)

---

## Estado por componente

### ✅ Base de datos (COMPLETO)
- **Archivo:** `C:\Users\ghriz\OneDrive\Finanzas MCGHR\Generales\finanzas.db`
- **Schema:** v1.1 aplicado — 22 tablas + 5 vistas
- **Tablas:** monedas, cuentas, categorias, personas, contrapartes, etiquetas, presupuestos, obligaciones, cuotas_obligacion, transacciones, tramos, asientos, posiciones, valuaciones, documentos, etiquetas_entidades, vinculos, correos_procesados, reglas_clasificacion, log_ejecuciones, items_transaccion, inbox_mobile
- **Vistas:** v_transacciones_completas, v_saldos_cuentas, v_presupuesto_vs_real, v_reembolsos_pendientes, v_inbox_pendiente
- **Modo WAL:** activado
- **Datos:** vacía — sin datos iniciales de catálogo todavía (ver Issue #2)

### ✅ Scripts Claude Desktop — Capa 1 (CÓDIGO COMPLETO, SIN CONECTAR)
Código real subido al repo. Funciona de forma standalone pero aún no está conectado a datos reales:

| Script | Ruta en repo | Estado |
|---|---|---|
| `finanzas_familia.py` | `src/finanzas_familia.py` | Código completo. Orquestador principal Fase 1 |
| `lector_correos.py` | `skills/lector_correos/lector_correos.py` | Código completo. Gmail + IMAP |
| `auditor_correos.py` | `skills/auditor_correos/auditor_correos.py` | Código completo. Detector de gaps |
| `desproteger_pdf.py` | `skills/desproteger_pdf/desproteger_pdf.py` | Código completo. Usa pikepdf |
| `server.py` (MCP) | `mcp_servers/mcp_lector_correos/server.py` | Código completo. FastMCP, 3 tools |

**Pendiente para activar Capa 1:**
- Configurar `config_correos.json` real en PC (NO va al repo — ver `.gitignore`)
- Ejecutar OAuth flow para obtener tokens Gmail de hernan y malu
- Cargar datos iniciales de catálogo (Issue #2): monedas, personas, cuentas bancarias reales

### ⚠️ Backend FastAPI — Capa 2 (ESTRUCTURA VACÍA)
- `backend/main.py` — existe y tiene la estructura completa con 11 routers declarados
- `backend/api/`, `backend/models/`, `backend/services/`, `backend/schemas/`, `backend/repositories/`, `backend/core/` — **carpetas vacías** (solo `__init__.py`)
- `scripts/migrations/`, `scripts/seed/` — **carpetas vacías**
- `tests/` — tiene `conftest.py` pero todos los subdirectorios vacíos

**El backend no arranca** — los imports en `main.py` fallarán hasta que se implementen los módulos.

### ⚠️ Frontend React — Capa 3 (ESTRUCTURA PARCIAL)
- `frontend/` tiene estructura real: `index.html`, `package.json`, `vite.config.js`, `tailwind.config.js`, `src/`
- Stack: React 18 + Vite + Tailwind + Zustand + React Query + Recharts
- `npm install` ejecutado en PC — `node_modules/` presente localmente
- Estado del código en `src/`: **desconocido** — no se auditó en esta sesión

---

## Issues abiertos (prioridad de trabajo)

| # | Título | Prioridad | Notas |
|---|---|---|---|
| #2 | Definir datos iniciales del catálogo | **ALTA** — bloqueante para Capa 1 | Monedas, personas GHR/MC, cuentas bancarias reales |
| #3 | Diseñar prompt de sesión para procesamiento de correos | ALTA | Necesario para activar `finanzas_familia.py` |
| #4 | Configurar autoforward iPhone Martha | MEDIA | Manual — lo hace Martha en su iPhone |
| #5 | Regenerar token GitHub | **URGENTE** | Token anterior expuesto en chat. Acción manual del usuario |
| #6 | Implementar app web local Flask para revisión humana | MEDIA | Fase 2 — localhost:5050 |
| #9 | Diseñar app mobile web — captura rápida iPhone | BAJA | Fase futura |
| #10 | Diseñar procesador de Inbox mobile en Claude Desktop | BAJA | Fase futura |
| #11 | Importación histórica PST Hotmail | BAJA | Fase futura |

---

## Lo que NO está en el repo (por seguridad)

| Archivo | Ubicación en PC | Razón |
|---|---|---|
| `config_correos.json` | `C:\Users\ghriz\.claude\` | Contiene credenciales reales — en `.gitignore` |
| `activar.ps1` | `C:\Users\ghriz\.claude\` | Script de activación local |
| `instalar.ps1` | `C:\Users\ghriz\.claude\` | Script de instalación local |
| Tokens OAuth Gmail | `C:\Users\ghriz\.gmail-mcp\tokens\` | Tokens sensibles |
| `finanzas.db` | OneDrive | Base de datos con datos reales — en `.gitignore` |
| `.env` / `.env.prod` | raíz del repo local | Variables con valores reales — en `.gitignore` |

---

## Próximos pasos recomendados (en orden)

1. **Issue #5 (URGENTE):** Usuario regenera token GitHub manualmente en github.com/settings/personal-access-tokens
2. **Issue #2:** Crear script SQL con datos iniciales del catálogo (monedas, personas, cuentas reales de GHR y MC)
3. **Issue #3:** Diseñar prompt de sesión para `finanzas_familia.py`
4. **Capa 2:** Implementar `backend/core/` (config, database), luego modelos, luego routers uno a uno
5. **Capa 3:** Auditar y completar `frontend/src/`
