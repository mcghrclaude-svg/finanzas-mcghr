"""
Router: /api/v1/transacciones
Gestión de transacciones financieras — el módulo central de la app.

Endpoints:
    GET    /                    Lista paginada con filtros
    POST   /                    Crear transacción manual
    GET    /pendientes          Cola de confirmación (estado=pendiente)
    GET    /{id}                Detalle de una transacción
    PATCH  /{id}                Editar campos de una transacción
    POST   /{id}/confirmar      Confirmar transacción pendiente
    POST   /{id}/descartar      Descartar transacción pendiente
    DELETE /{id}                Inactivar transacción (soft delete)
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
# from backend.api.v1.schemas.transacciones import (
#     TransaccionCreate, TransaccionUpdate, TransaccionResponse, TransaccionListResponse
# )
# from backend.services.transacciones import TransaccionesService

router = APIRouter()


@router.get("/")
async def listar_transacciones(
    db: AsyncSession = Depends(get_db),
    cursor: str | None = Query(None),
    limit: int = Query(50, le=200),
    desde: str | None = Query(None, description="Fecha inicio YYYY-MM-DD"),
    hasta: str | None = Query(None, description="Fecha fin YYYY-MM-DD"),
    id_categoria: str | None = Query(None),
    id_cuenta: str | None = Query(None),
    quien_pago: str | None = Query(None, description="GHR | MC"),
    tipo: str | None = Query(None, description="gasto | ingreso | transferencia"),
    id_contraparte: str | None = Query(None),
    es_recurrente: bool | None = Query(None),
    estado_reembolso: str | None = Query(None),
):
    """Lista transacciones confirmadas con filtros y paginación por cursor."""
    # TODO: implementar con TransaccionesService
    return {"items": [], "next_cursor": None, "total": 0}


@router.post("/", status_code=201)
async def crear_transaccion(
    # body: TransaccionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Crea una transacción manual. Va directo a estado confirmado."""
    # TODO: implementar con TransaccionesService
    return {}


@router.get("/pendientes")
async def listar_pendientes(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, le=200),
):
    """Cola de confirmación — transacciones propuestas por el ETL pendientes de revisión."""
    # TODO: implementar con TransaccionesService
    return {"items": [], "total": 0}


@router.get("/{transaccion_id}")
async def obtener_transaccion(
    transaccion_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Detalle completo de una transacción incluyendo tramos y documentos vinculados."""
    # TODO: implementar con TransaccionesService
    return {}


@router.patch("/{transaccion_id}")
async def editar_transaccion(
    transaccion_id: str,
    # body: TransaccionUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Edita campos de una transacción. Genera entrada en reglas_clasificacion si hay corrección."""
    # TODO: implementar con TransaccionesService
    return {}


@router.post("/{transaccion_id}/confirmar")
async def confirmar_transaccion(
    transaccion_id: str,
    # body: TransaccionUpdate | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Confirma una transacción pendiente (con o sin edición previa)."""
    # TODO: implementar con TransaccionesService
    return {}


@router.post("/{transaccion_id}/descartar")
async def descartar_transaccion(
    transaccion_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Descarta una transacción pendiente — no se registra en el sistema."""
    # TODO: implementar con TransaccionesService
    return {}


@router.delete("/{transaccion_id}")
async def inactivar_transaccion(
    transaccion_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Soft delete — marca la transacción como anulada. Nunca borra datos."""
    # TODO: implementar con TransaccionesService
    return {}
