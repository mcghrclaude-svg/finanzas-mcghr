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

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db

router = APIRouter()


@router.get("/")
async def listar_obligaciones(
    tipo: str | None = Query(None, description="DEUDA | SERVICIO | RECURRENTE"),
    solo_activas: bool = Query(True),
    vence_antes_de: str | None = Query(None, description="ISO 8601 date"),
    db: AsyncSession = Depends(get_db),
):
    # TODO: incluir estado de pago del mes corriente
    return {"items": []}


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
    # TODO: incluir historial de pagos y, si DEUDA, saldo de capital restante
    return {}


@router.patch("/{obligacion_id}")
async def editar_obligacion(obligacion_id: str, db: AsyncSession = Depends(get_db)):
    return {}


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
