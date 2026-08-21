"""
Router: /api/v1/reportes
Consultas y reportes financieros precalculados.

Todos los endpoints son GET (solo lectura). Los datos se agregan en el momento
del request sobre SQLite — no hay caché persistente en Fase 1.

En Fase 3 se puede agregar materialización en background para reportes pesados.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.models.transaccion import Transaccion, Tramo
from backend.models.catalogo import Contraparte, Persona, Cuenta

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
    Gastos marcados como Business Expense con estado_reembolso en
    pendiente|gestionado -- todavia no llego el reembolso del empleador.

    Replica en SQLAlchemy la logica de la vista v_reembolsos_pendientes
    (schema/finanzas_v1_1.sql) en vez de consultarla directo: la vista es
    SQL crudo fuera de Base.metadata, asi que un DB creado solo con
    create_all() (como el de los tests, y potencialmente un dev/prod que
    nunca corrio ese script de migracion puntual) no la tiene.
    """
    result = await db.execute(
        select(
            Transaccion.id,
            Transaccion.fecha,
            Transaccion.descripcion,
            Transaccion.estado_reembolso,
            Contraparte.nombre.label("contraparte"),
            Persona.nombre.label("quien_pago"),
            Cuenta.nombre.label("cuenta_pago"),
            Cuenta.es_corporativa,
            Tramo.monto_origen.label("monto"),
            Tramo.moneda_origen.label("moneda"),
            Tramo.tipo_cambio,
            Transaccion.notas,
        )
        .outerjoin(Contraparte, Transaccion.id_contraparte == Contraparte.id)
        .outerjoin(Persona, Transaccion.quien_pago == Persona.id)
        .outerjoin(Tramo, and_(
            Tramo.id_transaccion == Transaccion.id,
            Tramo.numero_orden == 1,
        ))
        .outerjoin(Cuenta, Tramo.id_cuenta_origen == Cuenta.id)
        .where(
            Transaccion.es_reembolsable == True,  # noqa: E712
            Transaccion.estado_reembolso.in_(["pendiente", "gestionado"]),
        )
        .order_by(Transaccion.fecha.desc())
    )

    items = []
    for row in result.mappings().all():
        item = dict(row)
        tipo_cambio = item.pop("tipo_cambio", None)
        monto = item["monto"] or 0
        item["monto_cop_estimado"] = (
            monto if item["moneda"] == "COP" else (monto * tipo_cambio if tipo_cambio else None)
        )
        items.append(item)

    total = sum(item["monto_cop_estimado"] or 0 for item in items)
    return {"items": items, "total": total}


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
