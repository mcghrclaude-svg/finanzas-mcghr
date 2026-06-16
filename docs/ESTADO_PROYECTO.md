# Estado del proyecto — Finanzas MCGHR
**Fecha:** Junio 2026
**Proposito:** Documento de handoff para retomar el proyecto en claude.ai con contexto completo.

---

## Que es este proyecto

Plataforma de gestion financiera familiar para GHR (Hernan) y MC (Martha).
Arquitectura de 4 capas:

1. **Capa 0 — Base de datos:** SQLite en OneDrive (`finanzas.db`) con schema de doble entrada contable, multi-moneda
2. **Capa 1 — Scripts Claude Desktop:** Procesamiento automatico de correos bancarios -> clasificacion con Claude API -> insercion en DB
3. **Capa 2 — Backend FastAPI:** API REST para exposicion de datos
4. **Capa 3 — Frontend React:** Dashboard web local

---

## Estado por componente

### Base de datos (COMPLETO)
- **Archivo:** `C:\Users\ghriz\OneDrive\Finanzas MCGHR\Generales\finanzas.db`
- **Schema:** v1.1 aplicado — 22 tablas + 5 vistas
- **Tablas:** monedas, cuentas, categorias, personas, contrapartes, etiquetas, presupuestos, obligaciones, cuotas_obligacion, transacciones, tramos, asientos, posiciones, valuaciones, documentos, etiquetas_entidades, vinculos, correos_procesados, reglas_clasificacion, log_ejecuciones, items_transaccion, inbox_mobile
- **Vistas:** v_transacciones_completas, v_saldos_cuentas, v_presupuesto_vs_real, v_reembolsos_pendientes, v_inbox_pendiente
- **Modo WAL:** activado

### Scripts Claude Desktop — Capa 1 (CODIGO COMPLETO, SIN CONECTAR)

| Script | Ruta en repo | Estado |
|---|---|---|
| `finanzas_familia.py` | `src/finanzas_familia.py` | Codigo completo. Orquestador principal Fase 1 |
| `lector_correos.py` | `skills/lector_correos/lector_correos.py` | Codigo completo. Gmail + IMAP |
| `auditor_correos.py` | `skills/auditor_correos/auditor_correos.py` | Codigo completo. Detector de gaps |
| `desproteger_pdf.py` | `skills/desproteger_pdf/desproteger_pdf.py` | Codigo completo. Usa pikepdf |
| `server.py` (MCP) | `mcp_servers/mcp_lector_correos/server.py` | Codigo completo. FastMCP, 3 tools |

**Pendiente para activar Capa 1:**
- Configurar `config_correos.json` real en PC (NO va al repo)
- Ejecutar OAuth flow para obtener tokens Gmail de hernan y malu
- Cargar datos iniciales de catalogo: monedas, personas, cuentas bancarias reales

### Backend FastAPI — Capa 2

**Modulos COMPLETOS:**

| Archivo | Estado | Notas |
|---|---|---|
| `backend/schemas/catalogos.py` | COMPLETO | Schemas Pydantic v2, validacion IDs y niveles |
| `backend/repositories/catalogos_repo.py` | COMPLETO | CRUD + arbol manual + cascada inactivacion |
| `backend/api/v1/routers/catalogos.py` | COMPLETO | Reemplaza TODOs — categorias, cuentas, contrapartes, personas |
| `backend/repositories/presupuesto_repo.py` | COMPLETO | obtener_por_mes, gasto_acumulado, velocidad_historica, patrimonio |
| `backend/services/presupuesto_service.py` | COMPLETO | Logica riesgo por velocidad, proyeccion suavizada 70/30 |
| `backend/api/v1/routers/presupuestos.py` | COMPLETO | /ejecucion, /periodo-activo, CRUD |
| `backend/api/v1/routers/dashboard.py` | COMPLETO | /resumen — agrega 4 metricas en una sola llamada |
| `backend/models/periodo.py` | COMPLETO | PeriodoFinanciero |
| `backend/models/velocidad_historica.py` | COMPLETO | VelocidadHistorica |

**Modulos PENDIENTES (estructura vacia):**
- `backend/api/v1/routers/`: transacciones, obligaciones, inversiones, inbox, reglas, reportes, analitica, backup
- `backend/schemas/`: solo catalogos.py completo
- `backend/services/`: solo presupuesto_service.py completo

**Bugs corregidos:**
- `backend/models/__init__.py` — importaba `Regla` pero la clase es `ReglaClasificacion`. Corregido.
- `backend/main.py` — usa `on_event` (deprecated). Pendiente migrar a `lifespan` (issue #20).

### Scripts y tests

| Archivo | Estado |
|---|---|
| `scripts/seed/seed_catalogos.py` | COMPLETO — 2 personas, 25 cats, 12 cuentas, 22 contrapartes, 10 reglas |
| `scripts/seed/seed_velocidad_historica.py` | COMPLETO — datos dummy 2026-04 y 2026-05 para desarrollo |
| `scripts/migrations/002_dashboard_schema.sql` | COMPLETO — periodos_financieros, velocidad_historica |
| `tests/conftest.py` | CORREGIDO — importa todos los modelos antes de create_all |
| `tests/integration/test_catalogos.py` | COMPLETO — 22/22 tests passing |

### Frontend React — Capa 3

**Modulos COMPLETOS (Tailwind puro, sin CSS custom):**

| Modulo | Ruta | Estado |
|---|---|---|
| Dashboard | `frontend/src/modules/Dashboard/` | COMPLETO — index.jsx + 4 subcomponentes Tailwind |
| Catalogos | `frontend/src/modules/Catalogos/` | COMPLETO — index, CategoriaTree, TablaGenerica, ModalForm, ModalConfirm |

**Archivos de soporte:**

| Archivo | Estado |
|---|---|
| `frontend/src/hooks/useDashboard.js` | COMPLETO — mock/API toggle, formatCOP, nivelRiesgoMeta |
| `frontend/src/mock/dashboardMock.js` | COMPLETO — 2 escenarios: con_historial / sin_historial |
| `frontend/src/api/client.js` | COMPLETO — axios con interceptor errores FastAPI |
| `frontend/src/api/catalogos.js` | COMPLETO — cliente API catalogos |
| `frontend/postcss.config.js` | COMPLETO — requerido para Tailwind v3 + Vite |

**Modulos PENDIENTES (placeholder):**
- `frontend/src/modules/`: Transacciones, Inbox, Presupuesto, Obligaciones, Inversiones, Analitica, Backup

**Nota arquitectura frontend:**
- `App.jsx` importa de `modules/` (NO de `pages/`)
- `pages/Dashboard.jsx` y `components/dashboard/*` quedan como referencia historica, no se usan
- Clases de color custom disponibles: `primary-{50,500,600,700,900}`, `danger-{500,100}`, `warning-{500,100}`, `success-{500,100}`

---

## Lo que NO esta en el repo (por seguridad)

| Archivo | Ubicacion en PC | Razon |
|---|---|---|
| `config_correos.json` | `C:\Users\ghriz\.claude\` | Contiene credenciales reales |
| Tokens OAuth Gmail | `C:\Users\ghriz\.gmail-mcp\tokens\` | Tokens sensibles |
| `finanzas.db` | OneDrive | Base de datos con datos reales |
| `.env` / `.env.prod` | raiz del repo local | Variables con valores reales |
| `frontend/.env.local` | `frontend/` | Variables VITE_* con valores reales |

---

## Proximos pasos recomendados (en orden)

1. Seed real: ejecutar `seed_catalogos.py` con backend corriendo y verificar en Swagger
2. Issue #19 (ASCII): limpiar caracteres especiales de archivos Python existentes
3. Issue #21 (FRONTEND-MOCK): agregar modo mock al modulo Catalogos
4. Implementar modulo Transacciones (backend + frontend)
5. Conectar Capa 1 (lector_correos) con DB real
