"""
Router: /api/v1/obligaciones
Gestión de compromisos financieros y recurrentes.

Tipos cubiertos:
    DEUDA       Préstamos con tabla de amortización (capital + intereses)
    SERVICIO    Facturas recurrentes con fecha de vencimiento variable
    RECURRENTE  Pagos fijos: alquiler, suscripciones, cuotas sin interés

Flujo de recordatorios:
    Cada obligación define `dias_aviso_anticipado`. Un job de background
    (scheduler.py, Fase 2) escribe alertas en la tabla `alertas` cuando
    se acerca el vencimiento o cuando no se detecta el pago esperado.
"""

from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.services.obligaciones_service import ObligacionesService

router = APIRouter()


class ObligacionUpdate(BaseModel):
    nombre: str | None = None
    monto_cuota: Decimal | None = None
    dia_vencimiento: int | None = None
    dias_aviso_anticipado: int | None = None
    activa: bool | None = None
    # Carga manual (v1.8) -- ver comentario en backend/models/obligacion.py
    saldo_pendiente: Decimal | None = None


@router.get("/")
async def listar_obligaciones(
    tipo: str | None = Query(None, description="DEUDA | SERVICIO | RECURRENTE"),
    solo_activas: bool = Query(True),
    vence_antes_de: str | None = Query(None, description="ISO 8601 date"),
    db: AsyncSession = Depends(get_db),
):
    # TODO: incluir estado de pago del mes corriente; vence_antes_de sin usar todavia
    service = ObligacionesService(db)
    return await service.listar(tipo=tipo, solo_activas=solo_activas)


@router.post("/", status_code=201)
async def crear_obligacion(db: AsyncSession = Depends(get_db)):
    # TODO: si tipo=DEUDA, crear tabla de amortización automática
    return {}


@router.get("/vencimientos")
async def proximos_vencimientos(
    dias: int = Query(30, description="Horizonte en días"),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista obligaciones con vencimiento en los próximos `dias` días.
    Usado por el Dashboard para la sección de alertas.
    """
    return {"items": []}


@router.get("/pendientes-pago")
async def obligaciones_sin_pago(
    db: AsyncSession = Depends(get_db),
):
    """
    Obligaciones cuyo pago esperado del mes corriente no se detectó
    en transacciones confirmadas. Genera alerta en dashboard.
    """
    return {"items": []}


@router.get("/{obligacion_id}")
async def detalle_obligacion(obligacion_id: str, db: AsyncSession = Depends(get_db)):
    # TODO: incluir historial de pagos (Despues, ver POST /registrar-pago)
    service = ObligacionesService(db)
    return await service.detalle(obligacion_id)


@router.patch("/{obligacion_id}")
async def editar_obligacion(
    obligacion_id: str,
    body: ObligacionUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Edicion manual, incluyendo saldo_pendiente. Cada cambio de
    saldo_pendiente queda registrado en saldo_obligacion_historico (ver
    ObligacionesRepository.actualizar)."""
    service = ObligacionesService(db)
    return await service.editar(obligacion_id, body.model_dump(exclude_unset=True))


@router.post("/{obligacion_id}/registrar-pago")
async def registrar_pago_manual(
    obligacion_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Registra pago manual cuando no hay correo/extracto disponible.
    Crea transacción confirmada y la vincula a esta obligación.
    """
    return {}


@router.delete("/{obligacion_id}", status_code=204)
async def inactivar_obligacion(obligacion_id: str, db: AsyncSession = Depends(get_db)):
    # TODO: soft delete — activa = 0
    return None
