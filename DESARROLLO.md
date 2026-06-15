# Guía de desarrollo local — Finanzas MCGHR

## Requisitos
- Python 3.11+
- Node 20+
- Git

Docker es opcional — solo necesario para deploy a Raspberry Pi.

---

## Setup inicial (una sola vez)

```bash
git clone https://github.com/mcghrclaude-svg/finanzas-mcghr.git
cd finanzas-mcghr

# Backend
pip install -r requirements.txt

# Frontend
cd frontend && npm install && cd ..

# Config
cp .env.dev .env
# Editar .env: poner ANTHROPIC_API_KEY real
```

---

## Levantar el stack

```bash
# Terminal 1 — backend
uvicorn backend.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend && npm run dev
```

- API:  http://localhost:8000
- Docs: http://localhost:8000/docs
- App:  http://localhost:3000

---

## Escenarios de prueba del dashboard

El dashboard soporta tres modos de datos, combinables:

### A — Mock con histórico (default dev)

Simula el sistema después de 2 meses de uso.
El riesgo por velocidad está activo, la línea punteada es visible.

```env
VITE_USE_MOCK=true
VITE_MOCK_SCENARIO=con_historial
```

### B — Mock sin histórico (primer mes)

Simula el primer mes de uso del sistema.
Las tarjetas muestran barra gris y badge "⏳ Acumulando datos históricos".
No hay línea punteada, no hay ratio de riesgo.

```env
VITE_USE_MOCK=true
VITE_MOCK_SCENARIO=sin_historial
```

### C — API real con seed dummy (más cercano a producción)

Requiere backend corriendo + migración + seeds aplicados.

```bash
# 1. Aplicar migración de schema
sqlite3 "C:/Users/ghriz/OneDrive/Finanzas MCGHR/Generales/finanzas.db" \
  < scripts/migrations/002_dashboard_schema.sql

# 2. Seeds
python -m scripts.seed.seed_catalogos
python -m scripts.seed.seed_velocidad_historica

# 3. Cambiar .env
VITE_USE_MOCK=false

# 4. Levantar ambos servidores
uvicorn backend.main:app --reload --port 8000
cd frontend && npm run dev
```

En este modo el riesgo usa datos dummy pero la lógica de velocidad
es la real del backend.

---

## Migraciones de schema

No usamos Alembic por ahora. Scripts SQL manuales en `scripts/migrations/`:

```bash
# 001 — schema inicial
sqlite3 finanzas.db < scripts/migrations/001_initial.sql

# 002 — períodos financieros + velocidad histórica
sqlite3 "C:/Users/ghriz/OneDrive/Finanzas MCGHR/Generales/finanzas.db" \
  < scripts/migrations/002_dashboard_schema.sql
```

---

## Variables de entorno

| Variable | Descripción | Default |
|---|---|---|
| `DATABASE_URL` | Path SQLite con driver aiosqlite | OneDrive/finanzas.db |
| `ANTHROPIC_API_KEY` | Claude API | requerida |
| `VITE_API_URL` | URL del backend | http://localhost:8000 |
| `VITE_USE_MOCK` | `true` = mock, `false` = API real | `true` |
| `VITE_MOCK_SCENARIO` | `con_historial` \| `sin_historial` | `con_historial` |
