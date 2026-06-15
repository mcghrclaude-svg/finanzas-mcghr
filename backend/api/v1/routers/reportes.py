"""
Router: /api/v1/reportes
Consultas y reportes financieros precalculados.

Todos los endpoints son GET (solo lectura). Los datos se agregan en el momento
del request sobre SQLite — no hay caché persistente en Fase 1.

En Fase 3 se puede agregar materialización en background para reportes pesados.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db

router = APIRouter()


@router.get("/gastos-por-categoria")
async def gastos_por_categoria(
    anio: int = Query(...),
    mes: int = Query(...),
    titular: str | None = Query(None, description="GHR | MC | None=ambos"),
    db: AsyncSession = Depends(get_db),
):
    """
    Gasto real del mes por categoría con comparación vs presupuesto.
    Devuelve también variación % respecto al mes anterior y al promedio 3M.
    Usado por el Dashboard (tarjetas de categoría) y módulo de Presupuesto.
    """
    return {"items": [], "total_gastado": 0, "total_presupuestado": 0}


@router.get("/flujo-mensual")
async def flujo_mensual(
    meses: int = Query(12, description="Cuántos meses hacia atrás"),
    db: AsyncSession = Depends(get_db),
):
    """
    Ingresos vs egresos por mes. Base del gráfico de barras del Dashboard.
    """
    return {"items": []}


@router.get("/top-comercios")
async def top_comercios(
    anio: int = Query(...),
    mes: int = Query(...),
    limite: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Top contrapartes por monto gastado en el período."""
    return {"items": []}


@router.get("/evolucion-patrimonio")
async def evolucion_patrimonio(
    meses: int = Query(12),
    db: AsyncSession = Depends(get_db),
):
    """
    Patrimonio neto mes a mes. Calculado desde valuaciones + deudas activas.
    """
    return {"items": []}


@router.get("/reembolsos-pendientes")
async def reembolsos_pendientes(db: AsyncSession = Depends(get_db)):
    """
    Gastos marcados como reembolsables que aún no tienen transacción de reembolso vinculada.
    Usa la vista v_reembolsos_pendientes del schema.
    """
    return {"items": [], "total": 0}


@router.get("/exportar-excel")
async def exportar_excel(
    anio: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Genera finanzas_maestro.xlsx con los datos del año indicado.
    Escribe en OneDrive/Generales/ y devuelve la ruta del archivo.
    Reutiliza la lógica de exportar_excel.py (scripts/).
    """
    # TODO: invocar scripts/exportar_excel.py como módulo
    return {"ruta": None, "filas_exportadas": 0}
