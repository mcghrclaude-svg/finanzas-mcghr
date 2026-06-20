"""
Router: /api/v1/inbox
Cola de revision humana: transacciones propuestas por el ETL pendientes de confirmacion.

completitud es TEXT en la DB: 'minimo' | 'parcial' | 'completo'
confianza es REAL en la DB: 0.0 - 1.0
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.services.inbox_service import InboxService
from backend.schemas.inbox import (
    InboxListResponse,
    InboxItemSummary,
    InboxItemRead,
    InboxItemPatch,
    ConfirmarRequest,
    ConfirmarResponse,
    ConfirmarLoteRequest,
    ConfirmarLoteResponse,
    InboxStatsOut,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# GET /inbox/stats
# ---------------------------------------------------------------------------

@router.get("/stats", response_model=InboxStatsOut)
async def stats_inbox(db: AsyncSession = Depends(get_db)):
    service = InboxService(db)
    return await service.stats()


# ---------------------------------------------------------------------------
# GET /inbox/
# ---------------------------------------------------------------------------

@router.get("/", response_model=InboxListResponse)
async def listar_inbox(
    estado: str = Query("pendiente"),
    origen: str | None = Query(None),
    cursor: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    service = InboxService(db)
    resultado = await service.listar(estado=estado, origen=origen,
                                     cursor=cursor, limit=limit)
    items_out = [_tx_to_summary(tx) for tx in resultado["items"]]
    return InboxListResponse(
        items=items_out,
        next_cursor=resultado["next_cursor"],
        total_pendientes=resultado["total_pendientes"],
    )


# ---------------------------------------------------------------------------
# POST /inbox/confirmar-lote
# ---------------------------------------------------------------------------

@router.post("/confirmar-lote", response_model=ConfirmarLoteResponse)
async def confirmar_lote(
    body: ConfirmarLoteRequest,
    db: AsyncSession = Depends(get_db),
):
    service = InboxService(db)
    return await service.confirmar_lote(body.ids)


# ---------------------------------------------------------------------------
# GET /inbox/{inbox_id}
# ---------------------------------------------------------------------------

@router.get("/{inbox_id}", response_model=InboxItemRead)
async def detalle_inbox_item(
    inbox_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = InboxService(db)
    tx = await service.obtener(inbox_id)
    return _tx_to_read(tx)


# ---------------------------------------------------------------------------
# PATCH /inbox/{inbox_id}
# ---------------------------------------------------------------------------

@router.patch("/{inbox_id}", response_model=InboxItemRead)
async def editar_inbox_item(
    inbox_id: str,
    body: InboxItemPatch,
    db: AsyncSession = Depends(get_db),
):
    service = InboxService(db)
    campos = body.model_dump(exclude_none=True)
    tx = await service.editar(inbox_id, campos)
    return _tx_to_read(tx)


# ---------------------------------------------------------------------------
# POST /inbox/{inbox_id}/confirmar
# ---------------------------------------------------------------------------

@router.post("/{inbox_id}/confirmar", response_model=ConfirmarResponse)
async def confirmar_inbox_item(
    inbox_id: str,
    body: ConfirmarRequest = ConfirmarRequest(),
    db: AsyncSession = Depends(get_db),
):
    service = InboxService(db)
    return await service.confirmar(
        tx_id=inbox_id,
        id_categoria=body.id_categoria,
        notas=body.notas,
    )


# ---------------------------------------------------------------------------
# POST /inbox/{inbox_id}/descartar
# ---------------------------------------------------------------------------

@router.post("/{inbox_id}/descartar")
async def descartar_inbox_item(
    inbox_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = InboxService(db)
    return await service.descartar(inbox_id)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _monto_tx(tx):
    if tx.tramos:
        tramo = next((t for t in tx.tramos if t.numero_orden == 1),
                     tx.tramos[0] if tx.tramos else None)
        if tramo and tramo.monto_origen is not None:
            return tramo.monto_origen
    return None


def _moneda_tx(tx):
    if tx.tramos:
        tramo = next((t for t in tx.tramos if t.numero_orden == 1),
                     tx.tramos[0] if tx.tramos else None)
        if tramo and tramo.moneda_origen:
            return tramo.moneda_origen
    return "COP"


def _tx_to_summary(tx) -> InboxItemSummary:
    return InboxItemSummary(
        id=tx.id,
        origen=tx.origen,
        fecha=tx.fecha,
        monto=_monto_tx(tx),
        moneda=_moneda_tx(tx),
        descripcion=tx.descripcion,
        id_categoria=tx.id_categoria,
        nombre_categoria=tx.categoria.nombre if tx.categoria else None,
        id_contraparte=tx.id_contraparte,
        nombre_contraparte=tx.contraparte.nombre if tx.contraparte else None,
        confianza=float(tx.confianza) if tx.confianza is not None else None,
        completitud=tx.completitud,        # STRING: minimo|parcial|completo
        estado=tx.estado,
        creado_en=tx.creado_en,
    )


def _tx_to_read(tx) -> InboxItemRead:
    return InboxItemRead(
        id=tx.id,
        origen=tx.origen,
        fecha=tx.fecha,
        monto=_monto_tx(tx),
        moneda=_moneda_tx(tx),
        descripcion=tx.descripcion,
        tipo=tx.tipo,
        id_categoria=tx.id_categoria,
        nombre_categoria=tx.categoria.nombre if tx.categoria else None,
        id_contraparte=tx.id_contraparte,
        nombre_contraparte=tx.contraparte.nombre if tx.contraparte else None,
        confianza=float(tx.confianza) if tx.confianza is not None else None,
        completitud=tx.completitud,        # STRING: minimo|parcial|completo
        estado=tx.estado,
        es_reembolsable=bool(tx.es_reembolsable),
        id_persona=tx.id_persona,
        id_correo=tx.id_correo,
        notas=tx.notas,
        creado_en=tx.creado_en,
        actualizado_en=tx.actualizado_en,
    )
