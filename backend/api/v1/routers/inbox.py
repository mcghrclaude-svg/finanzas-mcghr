"""
Router: /api/v1/inbox
Cola de revision humana: transacciones propuestas por el ETL pendientes de confirmacion.

Flujo:
    1. ETL (tarea programada Claude Desktop, 4am) escribe en `transacciones`
       con estado='pendiente', revisado_humano=0, confianza y completitud calculadas.
    2. Esta API expone la cola para que el frontend muestre los items al usuario.
    3. El usuario confirma, edita o descarta cada item.
    4. Al confirmar con correccion de categoria, se genera regla de aprendizaje.

Orden de items: completitud ASC (los mas incompletos primero).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, HTTPException
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
# GET /inbox/stats  — va ANTES de /{inbox_id} para no capturar "stats" como ID
# ---------------------------------------------------------------------------

@router.get("/stats", response_model=InboxStatsOut)
async def stats_inbox(db: AsyncSession = Depends(get_db)):
    """
    Contadores rapidos para el badge de notificacion del Dashboard.
    pendientes: total sin revisar.
    alta_prioridad: pendientes con confianza < 0.60.
    confirmados_hoy: confirmados en el dia de hoy.
    """
    service = InboxService(db)
    return await service.stats()


# ---------------------------------------------------------------------------
# GET /inbox
# ---------------------------------------------------------------------------

@router.get("/", response_model=InboxListResponse)
async def listar_inbox(
    estado: str = Query("pendiente", description="pendiente | confirmado | anulado"),
    origen: str | None = Query(None, description="email | pdf | mobile | manual"),
    cursor: str | None = Query(None, description="Paginacion por cursor"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista items del inbox ordenados por completitud ASC.
    Por defecto muestra solo los pendientes sin revisar.
    """
    service = InboxService(db)
    resultado = await service.listar(
        estado=estado,
        origen=origen,
        cursor=cursor,
        limit=limit,
    )

    items_out = [
        InboxItemSummary(
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
            completitud=float(tx.completitud) if tx.completitud is not None else None,
            estado=tx.estado,
            creado_en=tx.creado_en,
        )
        for tx in resultado["items"]
    ]

    return InboxListResponse(
        items=items_out,
        next_cursor=resultado["next_cursor"],
        total_pendientes=resultado["total_pendientes"],
    )


# ---------------------------------------------------------------------------
# POST /inbox/confirmar-lote  — va ANTES de /{inbox_id}
# ---------------------------------------------------------------------------

@router.post("/confirmar-lote", response_model=ConfirmarLoteResponse)
async def confirmar_lote(
    body: ConfirmarLoteRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Confirma multiples items en una sola operacion.
    Util para confirmar rapidamente los items de alta confianza.
    """
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
    """Detalle completo de un item, incluyendo datos crudos del ETL."""
    service = InboxService(db)
    tx = await service.obtener(inbox_id)

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
        completitud=float(tx.completitud) if tx.completitud is not None else None,
        estado=tx.estado,
        es_reembolsable=bool(tx.es_reembolsable),
        id_persona=tx.id_persona,
        id_correo=tx.id_correo,
        notas=tx.notas,
        creado_en=tx.creado_en,
        actualizado_en=tx.actualizado_en,
    )


# ---------------------------------------------------------------------------
# PATCH /inbox/{inbox_id}
# ---------------------------------------------------------------------------

@router.patch("/{inbox_id}", response_model=InboxItemRead)
async def editar_inbox_item(
    inbox_id: str,
    body: InboxItemPatch,
    db: AsyncSession = Depends(get_db),
):
    """
    Edita campos de un item antes de confirmar.
    Solo actualiza los campos presentes en el body (los None se ignoran).
    """
    service = InboxService(db)
    campos = body.model_dump(exclude_none=True)
    tx = await service.editar(inbox_id, campos)

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
        completitud=float(tx.completitud) if tx.completitud is not None else None,
        estado=tx.estado,
        es_reembolsable=bool(tx.es_reembolsable),
        id_persona=tx.id_persona,
        id_correo=tx.id_correo,
        notas=tx.notas,
        creado_en=tx.creado_en,
        actualizado_en=tx.actualizado_en,
    )


# ---------------------------------------------------------------------------
# POST /inbox/{inbox_id}/confirmar
# ---------------------------------------------------------------------------

@router.post("/{inbox_id}/confirmar", response_model=ConfirmarResponse)
async def confirmar_inbox_item(
    inbox_id: str,
    body: ConfirmarRequest = ConfirmarRequest(),
    db: AsyncSession = Depends(get_db),
):
    """
    Confirma el item. Lo mueve a estado='confirmado', revisado_humano=1.
    Si id_categoria difiere de la propuesta original, crea regla de aprendizaje.
    Idempotente: confirmar dos veces no duplica ni da error.
    """
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
    """
    Descarta el item. Estado pasa a 'anulado'.
    Usar cuando el correo/documento no corresponde a una transaccion financiera.
    """
    service = InboxService(db)
    return await service.descartar(inbox_id)


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------

def _monto_tx(tx):
    """Extrae el monto del primer tramo si existe, o del campo monto si lo tiene."""
    if tx.tramos:
        tramo = next(
            (t for t in tx.tramos if t.numero_orden == 1),
            tx.tramos[0] if tx.tramos else None
        )
        if tramo and tramo.monto_origen is not None:
            return tramo.monto_origen
    return None


def _moneda_tx(tx):
    if tx.tramos:
        tramo = next(
            (t for t in tx.tramos if t.numero_orden == 1),
            tx.tramos[0] if tx.tramos else None
        )
        if tramo and tramo.moneda_origen:
            return tramo.moneda_origen
    return "COP"
