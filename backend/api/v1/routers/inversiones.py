"""
Router: /api/v1/inversiones
Registro y seguimiento de activos de inversión.

Tipos de activo:
    AHORRO      Cuentas de ahorro / CDTs / depósitos a plazo
    ACCIONES    Posiciones en Interactive Brokers (IBKR) u otros brokers
    INMUEBLE    Propiedades (en uso, en alquiler, en construcción / pozo)

Flujo de valuación:
    Cada activo tiene una tabla `valuaciones` con snapshots fechados.
    El valor neto patrimonial (VNP) se calcula como:
        suma de valuaciones más recientes de cada activo − deudas activas

Importación IBKR:
    Los statements PDF mensuales de Interactive Brokers se procesan por el ETL
    y actualizan las tablas `posiciones` y `valuaciones` automáticamente.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db

router = APIRouter()


@router.get("/")
async def listar_inversiones(
    tipo: str | None = Query(None, description="AHORRO | ACCIONES | INMUEBLE"),
    titular: str | None = Query(None, description="GHR | MC"),
    db: AsyncSession = Depends(get_db),
):
    return {"items": []}


@router.post("/", status_code=201)
async def crear_inversion(db: AsyncSession = Depends(get_db)):
    return {}


@router.get("/patrimonio")
async def resumen_patrimonio(
    fecha: str | None = Query(None, description="ISO 8601 date; default=hoy"),
    db: AsyncSession = Depends(get_db),
):
    """
    Valor neto patrimonial (VNP) a la fecha indicada.
    VNP = Σ activos valuados − Σ deudas activas (capital restante)
    """
    return {
        "fecha": fecha,
        "activos_total": 0,
        "deudas_total": 0,
        "patrimonio_neto": 0,
        "detalle": [],
    }


@router.get("/{inversion_id}")
async def detalle_inversion(inversion_id: str, db: AsyncSession = Depends(get_db)):
    # TODO: incluir historial de valuaciones, posiciones y flujos de caja
    return {}


@router.patch("/{inversion_id}")
async def editar_inversion(inversion_id: str, db: AsyncSession = Depends(get_db)):
    return {}


@router.post("/{inversion_id}/valuacion")
async def agregar_valuacion(
    inversion_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Registra un nuevo snapshot de valor de mercado para el activo.
    Para ACCIONES: precio × cantidad de posiciones abiertas.
    Para INMUEBLE: valor de tasación o precio de compra ajustado.
    """
    return {}


@router.get("/{inversion_id}/roi")
async def calcular_roi(
    inversion_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    ROI = (valor_actual − costo_total_invertido + flujos_recibidos) / costo_total_invertido
    Flujos incluyen: alquileres cobrados, dividendos, intereses recibidos.
    """
    return {"roi_porcentaje": 0, "costo_total": 0, "valor_actual": 0, "flujos": 0}


@router.delete("/{inversion_id}", status_code=204)
async def cerrar_inversion(inversion_id: str, db: AsyncSession = Depends(get_db)):
    # TODO: marcar como cerrado con fecha de cierre, no borrado físico
    return None
