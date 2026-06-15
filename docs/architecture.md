# Arquitectura Técnica — Plataforma Financiera MCGHR

**Versión:** 1.0  
**Última actualización:** Junio 2026  
**Generado con:** Claude.ai Pro (mcghr.claude@gmail.com)

---

## Visión general

La plataforma es una aplicación web local que corre en la PC de Hernan (Windows 11) y es accesible desde iPhone via red WiFi local o como PWA instalada. No tiene backend en la nube — toda la lógica y los datos viven en la PC o en una Raspberry Pi en la misma red doméstica.

```
┌─────────────────────────────────────────────────────────────────┐
│                        RED LOCAL / DOCKER                        │
│                                                                  │
│   ┌──────────────┐    REST API     ┌──────────────────────────┐ │
│   │   Frontend   │ ◄────────────► │   Backend (FastAPI)      │ │
│   │ React + Vite │                 │   Python 3.11+           │ │
│   │   (Nginx)    │                 │   Puerto 8000            │ │
│   │  Puerto 3000 │                 └──────────┬───────────────┘ │
│   └──────────────┘                            │                  │
│                                               │ SQLAlchemy       │
│   ┌──────────────┐                 ┌──────────▼───────────────┐ │
│   │  ETL Worker  │                 │   SQLite                 │ │
│   │finanzas_     │ ────────────►  │   finanzas.db            │ │
│   │familia.py    │                 │   (fuente de verdad)     │ │
│   └──────────────┘                 └──────────────────────────┘ │
│          │                                                        │
│          │ lee/escribe                                            │
│   ┌──────▼───────────────────────────────────────────────────┐  │
│   │              OneDrive (sincronizado)                      │  │
│   │  Inbox/ · Extractos/ · Facturas/ · Stage/ · Backups/     │  │
│   └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
         ▲                    ▲
         │ WiFi local         │ WiFi local
   ┌─────┴──────┐      ┌─────┴──────┐
   │  iPhone    │      │  iPhone    │
   │  (GHR)     │      │  (MC)      │
   │  PWA       │      │  PWA       │
   └────────────┘      └────────────┘
```

---

## Stack tecnológico

### Backend
| Componente | Tecnología | Razón |
|---|---|---|
| Framework web | FastAPI (Python 3.11+) | Async nativo, OpenAPI automático, más moderno que Flask |
| ORM | SQLAlchemy 2.x | Separa lógica de acceso a datos, migrations con Alembic |
| Base de datos | SQLite (WAL mode) | Sin servidor, escritura concurrente, portable |
| Servidor ASGI | Uvicorn | Estándar para FastAPI |
| Scheduler | APScheduler | Jobs automáticos: ETL periódico, backups, alertas |
| Claude API | anthropic SDK | Clasificación de transacciones, analítica conversacional |

### Frontend
| Componente | Tecnología | Razón |
|---|---|---|
| Framework UI | React 18 | Estado complejo, ecosistema maduro, ideal para Undo stack |
| Build tool | Vite | Builds ultrarrápidos, HMR en desarrollo |
| CSS | Tailwind CSS | Responsive sin media queries manuales, mantenible |
| Estado global | Zustand | Más simple que Redux, ideal para estado de sesión + Undo |
| Router | React Router v6 | Estándar de facto |
| HTTP client | Axios + React Query | Cache automático, loading states, revalidación |
| Gráficos | Recharts | Liviano, declarativo, bien integrado con React |

### Infraestructura
| Componente | Tecnología | Razón |
|---|---|---|
| Contenedores | Docker + Docker Compose | Portabilidad PC → Raspberry Pi en un comando |
| Web server | Nginx | Sirve frontend estático + proxy reverso al backend |
| PWA | Vite PWA Plugin | Instalación desde Safari/Chrome en iPhone |
| Sincronización mobile | OneDrive Personal | JSONs del mobile sincronizados sin servidor adicional |

---

## Capas de la arquitectura

### Regla fundamental de dependencias
Cada capa solo conoce a las capas por debajo de ella. Nunca al revés.

```
Capa 4: Frontend React          → Solo llama a la API REST
Capa 3: FastAPI (routers)       → Solo llama a servicios
Capa 2: Services (lógica)       → Solo llama a repositorios
Capa 1: Repositories (datos)    → Solo accede a SQLite via SQLAlchemy
```

### Separación UI / lógica — regla de oro
- El frontend **nunca** accede directamente a SQLite
- El backend **nunca** sabe cómo se ve la pantalla
- Rediseñar el frontend completo no requiere tocar una línea de Python
- Cambiar el backend (ej: migrar a PostgreSQL) no requiere tocar una línea de React

---

## Estructura de carpetas

```
finanzas-mcghr/
│
├── backend/
│   ├── main.py                     ← FastAPI app, registro de routers, CORS
│   ├── config.py                   ← Lee config_correos.json y env vars
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── routers/
│   │       │   ├── transacciones.py
│   │       │   ├── presupuestos.py
│   │       │   ├── obligaciones.py
│   │       │   ├── inversiones.py
│   │       │   ├── catalogos.py    ← categorías, cuentas, contrapartes, personas
│   │       │   ├── inbox.py        ← inbox_mobile
│   │       │   ├── reportes.py
│   │       │   ├── analitica.py    ← integración Claude API
│   │       │   └── backup.py
│   │       └── schemas/            ← Pydantic models (request/response)
│   │           ├── transacciones.py
│   │           ├── presupuestos.py
│   │           └── ...
│   │
│   ├── services/                   ← Lógica de negocio pura (sin HTTP)
│   │   ├── transacciones.py        ← Confirmar, editar, clasificar
│   │   ├── presupuestos.py         ← Calcular ejecución y proyección
│   │   ├── obligaciones.py         ← Control de pagos y alertas
│   │   ├── inversiones.py          ← ROI, patrimonio neto
│   │   ├── clasificador.py         ← Reglas de clasificación + Claude API
│   │   ├── analitica.py            ← Análisis con Claude API
│   │   └── backup.py               ← Generación y restore de backups
│   │
│   ├── repositories/               ← Acceso a datos (SQLAlchemy queries)
│   │   ├── transacciones.py
│   │   ├── presupuestos.py
│   │   └── ...
│   │
│   ├── models/                     ← SQLAlchemy ORM models (mapeo al schema)
│   │   ├── transacciones.py
│   │   ├── catalogos.py
│   │   └── ...
│   │
│   └── core/
│       ├── database.py             ← Engine, SessionLocal, Base
│       └── exceptions.py           ← Excepciones de dominio
│
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx                 ← Router principal
│   │   │
│   │   ├── modules/                ← Una carpeta por módulo funcional
│   │   │   ├── Dashboard/
│   │   │   │   ├── index.jsx
│   │   │   │   ├── TarjetaPresupuesto.jsx
│   │   │   │   └── AlertasPanel.jsx
│   │   │   ├── Transacciones/
│   │   │   │   ├── ColaPendientes.jsx
│   │   │   │   ├── ListaTransacciones.jsx
│   │   │   │   └── FormManual.jsx
│   │   │   ├── Presupuesto/
│   │   │   ├── Obligaciones/
│   │   │   ├── Inversiones/
│   │   │   ├── Catalogos/
│   │   │   └── Backup/
│   │   │
│   │   ├── components/             ← Componentes UI reutilizables
│   │   │   ├── UndoBar.jsx         ← Barra de Undo/Redo siempre visible
│   │   │   ├── ConfirmDialog.jsx   ← Modal de confirmación de guardado
│   │   │   ├── AlertaSinGuardar.jsx
│   │   │   └── ...
│   │   │
│   │   ├── hooks/
│   │   │   ├── useUndo.js          ← Stack de Undo/Redo en memoria
│   │   │   ├── useTransacciones.js ← React Query hooks
│   │   │   └── ...
│   │   │
│   │   ├── store/
│   │   │   └── session.js          ← Zustand: estado de sesión, undo stack
│   │   │
│   │   └── api/
│   │       ├── client.js           ← Axios instance con base URL
│   │       ├── transacciones.js    ← Llamadas a /api/v1/transacciones
│   │       └── ...
│   │
│   ├── public/
│   │   └── manifest.json           ← Config PWA (nombre, iconos, display)
│   │
│   └── vite.config.js
│
├── etl/                            ← Scripts de ingesta (ETL)
│   ├── finanzas_familia.py         ← Orquestador principal (ya existente)
│   └── backup.py                   ← Script standalone de backup/restore
│
├── skills/                         ← Skills reutilizables (ya existentes)
│   ├── lector_correos/
│   ├── desproteger_pdf/
│   └── auditor_correos/
│
├── schema/                         ← Migraciones SQL incrementales
│   ├── finanzas_v1.sql
│   ├── finanzas_v1_1.sql           ← Versión actual
│   └── finanzas_v1_2.sql           ← Próxima migración (cuando aplique)
│
├── docs/                           ← Documentación del proyecto
│   ├── functional_spec.md          ← Especificación funcional
│   ├── architecture.md             ← Este documento
│   ├── schema_v1.md                ← Documentación del schema
│   └── api.md                      ← Documentación de la API REST (pendiente)
│
├── tests/
│   ├── backend/
│   │   ├── test_clasificador.py
│   │   ├── test_presupuesto.py
│   │   └── test_backup.py
│   └── frontend/                   ← Tests de componentes críticos
│
├── docker-compose.yml              ← Despliegue completo en un comando
├── Dockerfile.backend
├── Dockerfile.frontend
├── nginx.conf
├── .env.example                    ← Variables de entorno documentadas
├── config_correos.json             ← Configuración del proyecto (no en git)
├── CLAUDE.md                       ← Contexto del proyecto para IA
├── README.md                       ← Instrucciones de instalación y uso
└── CHANGELOG.md                    ← Historial de versiones
```

---

## Sistema Undo / Redo

El Undo es un stack en memoria gestionado por Zustand en el frontend. No persiste entre sesiones.

```javascript
// Estructura del stack
{
  past: [estado1, estado2, ...],   // acciones anteriores
  present: estadoActual,            // estado actual
  future: [estadoN, ...]           // acciones deshechas (para Redo)
}
```

**Ciclo de vida:**
1. Usuario realiza una acción → estado actual se mueve a `past`, nuevo estado es `present`
2. Usuario presiona Undo → `present` va a `future`, último item de `past` es el nuevo `present`
3. Usuario presiona Redo → `present` va a `past`, primero de `future` es el nuevo `present`
4. Usuario intenta Guardar → modal de confirmación → si confirma, API call → stack se vacía
5. Usuario intenta cerrar con stack no vacío → alerta de pérdida de cambios

**Qué entra al stack:** toda acción que modifica datos (confirmar transacción, editar campo, descartar, asignar categoría, cambiar monto). Las acciones de solo lectura no entran al stack.

---

## Flujo mobile (iPhone)

```
iPhone (PWA)                OneDrive                 PC (ETL)
─────────────               ─────────                ────────────────
Usuario registra  ──────►  Escribe JSON  ──────►   ETL detecta JSON
gasto en campo            en Inbox/               nuevo en Inbox/
                                                        │
                                                   Llama Claude API
                                                   para parsear/validar
                                                        │
                                                   Escribe en SQLite:
                                                   - transacciones (pendiente)
                                                   - inbox_mobile (procesado)
                                                        │
                                              App web muestra en
                                              cola de confirmación
```

Los JSONs del inbox mobile siguen este formato mínimo:
```json
{
  "tipo": "tx_nuevo",
  "fecha_creacion": "2026-06-15T16:00:00-05:00",
  "dispositivo": "iphone_ghr",
  "datos": {
    "fecha": "2026-06-15",
    "monto": 45000,
    "moneda": "COP",
    "descripcion": "Almuerzo",
    "completitud": "minimo"
  }
}
```

---

## API REST — Convenciones

- Base URL: `/api/v1/`
- Autenticación Fase 1: ninguna (red local)
- Formato: JSON en request y response
- Errores: RFC 7807 (Problem Details)
- Paginación: cursor-based (`?cursor=X&limit=50`)
- Fechas: ISO 8601 con timezone (`2026-06-15T16:00:00-05:00`)
- Montos: siempre en la moneda original + campo `monto_cop_estimado`

**Grupos de endpoints:**
```
/api/v1/transacciones/          ← CRUD + confirmar + descartar
/api/v1/transacciones/pendientes/  ← Cola de confirmación
/api/v1/presupuestos/           ← CRUD + ejecución + proyección
/api/v1/obligaciones/           ← CRUD + estado de pagos
/api/v1/inversiones/            ← CRUD + ROI + patrimonio neto
/api/v1/catalogos/categorias/   ← ABM categorías
/api/v1/catalogos/cuentas/      ← ABM cuentas/productos
/api/v1/catalogos/contrapartes/ ← ABM contrapartes
/api/v1/catalogos/personas/     ← ABM personas
/api/v1/inbox/                  ← Estado de inbox mobile
/api/v1/reglas/                 ← ABM reglas de clasificación
/api/v1/reportes/dashboard/     ← Datos del dashboard
/api/v1/analitica/chat/         ← Sesión conversacional con Claude
/api/v1/backup/generar/         ← Genera backup completo
/api/v1/backup/estado/          ← Estado del último backup
```

La documentación completa de cada endpoint estará en `docs/api.md`.

---

## Backup y Restore

### Contenido del archivo de backup

```
mcghr_backup_YYYYMMDD_HHMMSS.zip
├── db/
│   └── finanzas.db                 ← Base de datos completa
├── config/
│   ├── config_correos.json
│   └── .env                        ← Variables de entorno (cifradas)
├── credentials/
│   └── gmail_tokens/               ← Tokens OAuth (cifrados con AES-256)
├── documentos/
│   ├── GHR/Extractos/...
│   ├── GHR/Facturas/...
│   ├── MC/Extractos/...
│   └── Stage/...
├── manifest.json                   ← Metadatos del backup (versión, fecha, hash)
└── restore.py                      ← Script de restore standalone (incluido en el zip)
```

### Comando de restore
```bash
python restore.py mcghr_backup_20260615_120000.zip
# El script valida integridad, pide confirmación y restaura todo
```

---

## Docker Compose

```yaml
# docker-compose.yml (referencia)
services:
  backend:
    build: ./Dockerfile.backend
    ports: ["8000:8000"]
    volumes:
      - ./data:/app/data          # finanzas.db
      - ./config:/app/config      # config_correos.json
      - onedrive:/app/onedrive    # documentos sincronizados
    environment:
      - ANTHROPIC_API_KEY
      - OUTLOOK_APP_PASSWORD

  frontend:
    build: ./Dockerfile.frontend
    ports: ["3000:3000"]
    depends_on: [backend]

  nginx:
    image: nginx:alpine
    ports: ["80:80"]
    volumes: [./nginx.conf:/etc/nginx/nginx.conf]
    depends_on: [frontend, backend]
```

Con esto, la migración a Raspberry Pi es:
```bash
git clone https://github.com/mcghrclaude-svg/finanzas-mcghr
cp .env.example .env  # completar variables
docker-compose up -d
```

---

## Decisiones de diseño registradas

| Fecha | Decisión | Alternativa descartada | Razón |
|---|---|---|---|
| Jun 2026 | FastAPI sobre Flask | Flask | Async nativo, mejor DX, OpenAPI automático |
| Jun 2026 | SQLite sobre PostgreSQL | PostgreSQL | Sin servidor, portable, suficiente para escala familiar |
| Jun 2026 | React sobre Vue | Vue | Mayor ecosistema, mejor manejo de estado complejo para Undo |
| Jun 2026 | Zustand sobre Redux | Redux | Más simple, menos boilerplate, suficiente para este caso |
| Jun 2026 | Undo en memoria (no persiste) | Undo persistido en BD | Complejidad innecesaria; grabar es la confirmación explícita |
| Jun 2026 | PWA responsive sobre app nativa | React Native | Sin App Store, mismo código, menor mantenimiento |
| Jun 2026 | Flujo mobile via JSON en OneDrive | API REST directa al backend | Sin depender de que la PC esté encendida; usa infraestructura ya disponible |
| Jun 2026 | Backup completo (no incremental) | Incremental | Simplicidad de restore; el tamaño de datos no lo justifica |
| Jun 2026 | Seguridad por red local en Fase 1 | Auth desde el inicio | Reduce complejidad del MVP; se agrega en Fase 2 |
| Jun 2026 | ETL como proceso separado | ETL embebido en el backend | Permite correr el ETL independientemente de la app web |

---

## Variables de entorno requeridas

```bash
# .env.example
ANTHROPIC_API_KEY=sk-ant-...          # Claude API (console.anthropic.com)
OUTLOOK_APP_PASSWORD=...               # Contraseña de app Microsoft (Hotmail/Outlook)
DB_PATH=/app/data/finanzas.db         # Ruta a SQLite
ONEDRIVE_PATH=/app/onedrive           # Ruta a carpeta sincronizada de OneDrive
CONFIG_PATH=/app/config/config_correos.json
BACKUP_RETENTION_DAYS=90              # Días a retener backups
BACKUP_PATH=/app/data/backups         # Dónde guardar los backups
LOG_LEVEL=INFO
```

---

## Herramientas de desarrollo recomendadas

- **IDE:** VS Code con extensiones Python, ESLint, Prettier, Tailwind CSS IntelliSense
- **Cliente API:** Bruno o Insomnia (para probar endpoints durante desarrollo)
- **SQLite viewer:** DB Browser for SQLite (para inspección directa de la BD)
- **Git:** commits semánticos (`feat:`, `fix:`, `docs:`, `refactor:`, `chore:`)

---

## Para continuar este proyecto desde cero

Si estás leyendo esto desde una herramienta de IA (Codex, Grok, otro Claude), el orden recomendado es:

1. Leer `CLAUDE.md` — contexto general del proyecto
2. Leer `docs/functional_spec.md` — qué hace la app
3. Leer este documento — cómo está construida
4. Leer `docs/schema_v1.md` — estructura de datos
5. Leer `docs/api.md` — endpoints REST (cuando esté disponible)
6. El código ya existente está en `src/` (ETL) y `skills/` (skills reutilizables)
7. El schema SQL está en `schema/finanzas_v1_1.sql`

El próximo paso de desarrollo es implementar el backend FastAPI con los endpoints de `/api/v1/transacciones/` y `/api/v1/transacciones/pendientes/`, conectado al schema v1.1.

---

*Documento generado en Junio 2026 — Plataforma Financiera MCGHR*
