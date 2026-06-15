"""
Plataforma Financiera MCGHR — Backend
FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings
from backend.core.database import create_tables
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
)

app = FastAPI(
    title="Plataforma Financiera MCGHR",
    description="API para gestión financiera familiar — GHR & MC",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — permite acceso desde el frontend y desde el iPhone en red local
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    create_tables()


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "env": settings.env}


# Routers
app.include_router(transacciones.router, prefix="/api/v1/transacciones", tags=["transacciones"])
app.include_router(presupuestos.router, prefix="/api/v1/presupuestos", tags=["presupuestos"])
app.include_router(obligaciones.router, prefix="/api/v1/obligaciones", tags=["obligaciones"])
app.include_router(inversiones.router, prefix="/api/v1/inversiones", tags=["inversiones"])
app.include_router(catalogos.router, prefix="/api/v1/catalogos", tags=["catalogos"])
app.include_router(inbox.router, prefix="/api/v1/inbox", tags=["inbox"])
app.include_router(reglas.router, prefix="/api/v1/reglas", tags=["reglas"])
app.include_router(reportes.router, prefix="/api/v1/reportes", tags=["reportes"])
app.include_router(analitica.router, prefix="/api/v1/analitica", tags=["analitica"])
app.include_router(backup.router, prefix="/api/v1/backup", tags=["backup"])
