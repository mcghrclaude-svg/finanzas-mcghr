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
cd frontend
npm install
cd ..

# Config
cp .env.dev .env
# Editar .env: poner ANTHROPIC_API_KEY real
```

---

## Levantar el backend

```bash
# Desde la raíz del repo
uvicorn backend.main:app --reload --port 8000
```

Esto:
1. Crea las tablas SQLite si no existen (`finanzas.db`)
2. Levanta la API en http://localhost:8000
3. Docs interactivos en http://localhost:8000/docs

### Poblar datos iniciales

```bash
python -m scripts.seed.seed_catalogos
python -m scripts.seed.seed_presupuestos
python -m scripts.seed.seed_transacciones
```

---

## Levantar el frontend

```bash
cd frontend
npm run dev
```

Frontend en http://localhost:3000

### Modo mock vs API real

En `.env` (o `.env.dev`):

```env
# Datos mock (no necesita backend corriendo)
VITE_USE_MOCK=true

# API real (necesita backend en puerto 8000)
VITE_USE_MOCK=false
```

---

## Orden recomendado al arrancar desarrollo

1. `uvicorn backend.main:app --reload` (terminal 1)
2. `cd frontend && npm run dev` (terminal 2)
3. Abrir http://localhost:3000

---

## Migraciones de schema

No usamos Alembic por ahora. Las migraciones son scripts SQL manuales:

```bash
# Aplicar migr. 002 (períodos financieros + velocidad histórica)
sqlite3 "C:/Users/ghriz/OneDrive/Finanzas MCGHR/Generales/finanzas.db" \
  < scripts/migrations/002_dashboard_schema.sql
```

---

## Variables de entorno

| Variable | Descripción | Default dev |
|---|---|---|
| `DATABASE_URL` | Path SQLite | OneDrive/finanzas.db |
| `ANTHROPIC_API_KEY` | Claude API | requerida |
| `VITE_API_URL` | URL del backend | http://localhost:8000 |
| `VITE_USE_MOCK` | Datos mock en frontend | true |
