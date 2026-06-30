"""
Router: /api/v1/inbox
Cola de revision humana: transacciones propuestas por el ETL pendientes de confirmacion.

completitud es TEXT en la DB: 'minimo' | 'parcial' | 'completo'
confianza es REAL en la DB: 0.0 - 1.0
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from backend.core.database import get_db
from backend.models.transaccion import Tramo
from backend.services.inbox_service import InboxService
from backend.schemas.inbox import (
    InboxListResponse,
    InboxItemSummary,
    InboxItemRead,
    InboxItemPatch,
    TramoOut,
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
    # estado='all' significa sin filtro de estado (muestra confirmadas y pendientes)
    estado_filtro = None if estado == "all" else estado
    resultado = await service.listar(estado=estado_filtro, origen=origen,
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

    # Separar el campo del tramo del resto
    campos = body.model_dump(exclude_none=True)
    id_cuenta_tramo1 = campos.pop("id_cuenta_origen_tramo1", None)

    # Editar la transaccion
    tx = await service.editar(inbox_id, campos)

    # Si viene id_cuenta_origen_tramo1 y la transaccion tiene exactamente un tramo,
    # actualizar ese tramo. Si tiene mas de un tramo, ignorar (multi-tramo no se
    # edita desde el panel de inbox).
    if id_cuenta_tramo1 and tx.tramos and len(tx.tramos) == 1:
        await db.execute(
            update(Tramo)
            .where(Tramo.id == tx.tramos[0].id)
            .values(id_cuenta_origen=id_cuenta_tramo1)
        )
        await db.flush()
        # Recargar para que el response refleje el cambio
        tx = await service.obtener(inbox_id)

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


def _tramo_to_out(t) -> TramoOut:
    return TramoOut(
        id=t.id,
        numero_orden=t.numero_orden or 1,
        id_cuenta_origen=t.id_cuenta_origen,
        nombre_cuenta_origen=t.cuenta_origen.nombre if t.cuenta_origen else None,
        id_cuenta_destino=t.id_cuenta_destino,
        nombre_cuenta_destino=t.cuenta_destino.nombre if t.cuenta_destino else None,
        monto_origen=t.monto_origen,
        moneda_origen=t.moneda_origen,
        monto_destino=t.monto_destino,
        moneda_destino=t.moneda_destino,
    )


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
        completitud=tx.completitud,
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
        quien_pago=tx.quien_pago,
        para_quien=tx.para_quien,
        es_recurrente=bool(tx.es_recurrente),
        id_categoria=tx.id_categoria,
        nombre_categoria=tx.categoria.nombre if tx.categoria else None,
        id_contraparte=tx.id_contraparte,
        nombre_contraparte=tx.contraparte.nombre if tx.contraparte else None,
        confianza=float(tx.confianza) if tx.confianza is not None else None,
        completitud=tx.completitud,
        estado=tx.estado,
        es_reembolsable=bool(tx.es_reembolsable),
        estado_reembolso=tx.estado_reembolso,
        id_persona=tx.id_persona,
        id_correo=tx.id_correo,
        notas=tx.notas,
        tramos=[_tramo_to_out(t) for t in (tx.tramos or [])],
        creado_en=tx.creado_en,
        actualizado_en=tx.actualizado_en,
    )
