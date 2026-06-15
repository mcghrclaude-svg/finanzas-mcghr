"""
Router: /api/v1/presupuestos

Endpoints:
    GET    /                           Lista presupuestos (filtro por anio/mes)
    POST   /                           Crear/actualizar presupuesto mensual
    DELETE /{anio}/{mes}/{id_categoria} Eliminar presupuesto de una categoría
    GET    /ejecucion                  Ejecución del período activo (dashboard principal)
    GET    /periodo-activo             Período financiero abierto
    GET    /benchmark/{id_categoria}   Gasto histórico para benchmark al presupuestar
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.repositories.presupuesto_repo import PresupuestoRepository
from backend.services.presupuesto_service import PresupuestoService

router = APIRouter()


# ── Schemas inline (simples, sin archivo separado por ahora) ────────────────

class PresupuestoCreate(BaseModel):
    anio: int
    mes: int
    id_categoria: str
    monto_presupuestado: Decimal
    id_periodo: str | None = None


# ── Endpoints ─────────────────────────────────────────────────────────

@router.get("/ejecucion")
async def ejecucion_presupuesto(
    anio: int = Query(..., description="Año del período"),
    mes: int = Query(..., description="Mes del período (1–12)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Ejecución de presupuesto por categoría para el período dado.
    Incluye riesgo por velocidad de gasto vs histórico, proyección suavizada
    y posición de la línea punteada esperada a hoy.

    Es el endpoint principal que alimenta las tarjetas de presupuesto del dashboard.
    """
    service = PresupuestoService(db)
    return await service.obtener_ejecucion(anio, mes)


@router.get("/periodo-activo")
async def periodo_activo(db: AsyncSession = Depends(get_db)):
    """
    Período financiero actualmente abierto.
    Retorna fecha_fin_tentativa (en itálica en el dashboard)
    y fecha_fin_real (null si el salario aún no se acreditó).
    """
    repo = PresupuestoRepository(db)
    periodo = await repo.obtener_periodo_activo()
    if not periodo:
        raise HTTPException(status_code=404, detail="No hay período financiero activo configurado")
    return {
        "id": periodo.id,
        "anio": periodo.anio,
        "mes": periodo.mes,
        "fecha_inicio": str(periodo.fecha_inicio),
        "fecha_fin_tentativa": str(periodo.fecha_fin_tentativa),
        "fecha_fin_real": str(periodo.fecha_fin_real) if periodo.fecha_fin_real else None,
        "estado": periodo.estado,
        "dia_acreditacion_salario": periodo.dia_acreditacion_salario,
    }


@router.get("/")
async def listar_presupuestos(
    anio: int | None = Query(None),
    mes: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    repo = PresupuestoRepository(db)
    if anio and mes:
        items = await repo.obtener_por_mes(anio, mes)
        return {"items": [
            {
                "id": p.id,
                "anio": p.anio,
                "mes": p.mes,
                "id_categoria": p.id_categoria,
                "monto_presupuestado": float(p.monto_presupuestado),
                "moneda": p.moneda,
                "id_periodo": p.id_periodo,
            }
            for p in items
        ]}
    return {"items": []}


@router.post("/", status_code=201)
async def crear_o_actualizar_presupuesto(
    body: PresupuestoCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Crea o actualiza el presupuesto de una categoría para un mes dado.
    Si ya existe (anio + mes + id_categoria), actualiza el monto.
    """
    repo = PresupuestoRepository(db)
    p = await repo.upsert(
        anio=body.anio,
        mes=body.mes,
        id_categoria=body.id_categoria,
        monto=body.monto_presupuestado,
        id_periodo=body.id_periodo,
    )
    await db.commit()
    return {
        "id": p.id,
        "anio": p.anio,
        "mes": p.mes,
        "id_categoria": p.id_categoria,
        "monto_presupuestado": float(p.monto_presupuestado),
    }


@router.delete("/{anio}/{mes}/{id_categoria}", status_code=204)
async def eliminar_presupuesto(
    anio: int,
    mes: int,
    id_categoria: str,
    db: AsyncSession = Depends(get_db),
):
    repo = PresupuestoRepository(db)
    ok = await repo.eliminar(anio, mes, id_categoria)
    if not ok:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    await db.commit()
    return None


@router.get("/benchmark/{id_categoria}")
async def benchmark_categoria(
    id_categoria: str,
    db: AsyncSession = Depends(get_db),
):
    """Gasto histórico de la categoría para usar como referencia al presupuestar."""
    service = PresupuestoService(db)
    return await service.benchmark_categoria(id_categoria)
