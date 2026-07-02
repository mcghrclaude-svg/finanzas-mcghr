"""
Punto de entrada de la API FastAPI — Finanzas MCGHR.

Arrancar en desarrollo:
    uvicorn backend.main:app --reload --port 8000

Entornos:
    dev:     PORT=8000, DB en OneDrive
    test:    PORT=8001, DB en memoria
    staging: PORT=8003, DB en OneDrive (copia)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings
from backend.core.database import engine
from backend.models import Base  # importa todos los modelos para create_all

# Routers
from backend.api.v1.routers import (
    transacciones,
    presupuestos,
    obligaciones,
    inversiones,
    catalogos,
    inbox,
    reglas,
    reportes,
    analitica,
    backup,
    dashboard,
    tools,
)

app = FastAPI(
    title="Finanzas MCGHR API",
    version="0.1.0",
    description="Plataforma de gestión financiera familiar MCGHR",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — permite el frontend en dev (localhost:3000) y staging (localhost:3003)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3003",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
PREFIX = "/api/v1"
app.include_router(transacciones.router,  prefix=f"{PREFIX}/transacciones",  tags=["transacciones"])
app.include_router(presupuestos.router,   prefix=f"{PREFIX}/presupuestos",   tags=["presupuestos"])
app.include_router(obligaciones.router,   prefix=f"{PREFIX}/obligaciones",   tags=["obligaciones"])
app.include_router(inversiones.router,    prefix=f"{PREFIX}/inversiones",    tags=["inversiones"])
app.include_router(catalogos.router,      prefix=f"{PREFIX}/catalogos",      tags=["catalogos"])
app.include_router(inbox.router,          prefix=f"{PREFIX}/inbox",          tags=["inbox"])
app.include_router(reglas.router,         prefix=f"{PREFIX}/reglas",         tags=["reglas"])
app.include_router(reportes.router,       prefix=f"{PREFIX}/reportes",       tags=["reportes"])
app.include_router(analitica.router,      prefix=f"{PREFIX}/analitica",      tags=["analitica"])
app.include_router(backup.router,         prefix=f"{PREFIX}/backup",         tags=["backup"])
app.include_router(dashboard.router,      prefix=f"{PREFIX}/dashboard",      tags=["dashboard"])
app.include_router(tools.router,          prefix=f"{PREFIX}/tools",          tags=["tools"])


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "version": app.version}


@app.on_event("startup")
async def on_startup():
    """
    Crea las tablas si no existen.
    En producción usar migraciones SQL manuales (scripts/migrations/).
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
