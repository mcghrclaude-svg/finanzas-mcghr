"""
Router: /api/v1/presupuestos

Endpoints:
    GET    /                        Lista presupuestos (filtro por anio/mes)
    POST   /                        Crear presupuesto mensual por categoría
    GET    /{anio}/{mes}            Presupuesto completo de un mes con ejecución real
    PUT    /{anio}/{mes}/{categoria} Editar monto presupuestado
    DELETE /{anio}/{mes}/{categoria} Eliminar presupuesto de una categoría
    GET    /{anio}/{mes}/proyeccion  Proyección de cierre del mes en curso
    GET    /benchmark/{categoria}   Gasto histórico últimos 1/3/6 meses para benchmark
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db

router = APIRouter()


@router.get("/")
async def listar_presupuestos(
    anio: int | None = Query(None),
    mes: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    # TODO: implementar con PresupuestosService
    return {"items": []}


@router.post("/", status_code=201)
async def crear_presupuesto(db: AsyncSession = Depends(get_db)):
    # TODO: implementar con PresupuestosService
    return {}


@router.get("/{anio}/{mes}")
async def obtener_presupuesto_mes(
    anio: int, mes: int, db: AsyncSession = Depends(get_db)
):
    # TODO: incluye ejecución real y proyección
    return {}


@router.put("/{anio}/{mes}/{id_categoria}")
async def editar_presupuesto(
    anio: int, mes: int, id_categoria: str, db: AsyncSession = Depends(get_db)
):
    # TODO: implementar con PresupuestosService
    return {}


@router.delete("/{anio}/{mes}/{id_categoria}", status_code=204)
async def eliminar_presupuesto(
    anio: int, mes: int, id_categoria: str, db: AsyncSession = Depends(get_db)
):
    # TODO: implementar con PresupuestosService
    return None


@router.get("/{anio}/{mes}/proyeccion")
async def proyeccion_cierre(
    anio: int, mes: int, db: AsyncSession = Depends(get_db)
):
    """
    Proyección de cierre: gastado / días_transcurridos * días_del_mes.
    Devuelve alerta si proyección > 90% del presupuesto antes del día 20.
    """
    # TODO: implementar con PresupuestosService
    return {"categorias": []}


@router.get("/benchmark/{id_categoria}")
async def benchmark_categoria(
    id_categoria: str,
    meses: int = Query(6, description="Últimos N meses: 1, 3 o 6"),
    db: AsyncSession = Depends(get_db),
):
    """Gasto histórico real para usar como referencia al definir el presupuesto."""
    # TODO: implementar con PresupuestosService
    return {"promedio_mensual": 0, "detalle": []}
