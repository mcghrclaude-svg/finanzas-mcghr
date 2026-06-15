"""
Router: /api/v1/dashboard

Endpoint principal del dashboard de finanzas MCGHR.
Agrega en una sola llamada todas las métricas del top del dashboard:
    - Período financiero activo
    - Ingresos acreditados en el período
    - Gastos acumulados hasta hoy
    - Saldo disponible hoy (ingresos - gastos)
    - Saldo proyectado al cierre (ingresos - proyección gastos)
    - Patrimonio neto (activos inversión - deudas)
    - Variación patrimonio vs período anterior
    - Count de inbox pendiente (badge de catalogación)

Diseñado para ser llamado una sola vez al cargar el dashboard.
Las tarjetas de presupuesto se cargan por separado desde /presupuestos/ejecucion.
"""

from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from backend.core.database import get_db
from backend.repositories.presupuesto_repo import PresupuestoRepository
from backend.services.presupuesto_service import PresupuestoService

router = APIRouter()


@router.get("/resumen")
async def resumen_dashboard(
    anio: int | None = Query(None, description="Año (default: actual)"),
    mes: int | None = Query(None, description="Mes 1-12 (default: actual)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Métricas consolidadas del dashboard. Llamada única al montar la página.

    El frontend usa estos datos para:
      - Top bar: título del período y fechas
      - 4 metric cards: ingresos, gastos, saldo proy., patrimonio
      - Badge del inbox
    """
    hoy = date.today()
    anio = anio or hoy.year
    mes = mes or hoy.month

    repo = PresupuestoRepository(db)
    service = PresupuestoService(db)

    # Período activo
    periodo = await repo.obtener_periodo_activo()

    if periodo:
        fecha_inicio = periodo.fecha_inicio
        fecha_hasta = min(hoy, periodo.fecha_fin_real or hoy)
        dias_transcurridos = (hoy - fecha_inicio).days + 1
        fecha_fin_ref = periodo.fecha_fin_real or periodo.fecha_fin_tentativa
        dias_totales = (fecha_fin_ref - fecha_inicio).days + 1
    else:
        import calendar
        fecha_inicio = date(anio, mes, 1)
        fecha_hasta = hoy
        dias_transcurridos = hoy.day
        dias_totales = calendar.monthrange(anio, mes)[1]

    dias_transcurridos = max(dias_transcurridos, 1)

    # Ingresos acreditados en el período
    ingresos = await repo.obtener_ingresos_periodo(fecha_inicio, fecha_hasta)

    # Gastos acumulados hasta hoy
    gastos = await repo.obtener_gastos_totales_periodo(fecha_inicio, fecha_hasta)

    # Saldo disponible hoy
    saldo_disponible = ingresos - gastos

    # Proyección de gastos al cierre (suma de monto_proyectado de cada categoría)
    # Reutilizamos obtener_ejecucion para no duplicar lógica
    ejecucion = await service.obtener_ejecucion(anio, mes)
    gastos_proyectados = sum(
        Decimal(str(item["monto_proyectado"])) for item in ejecucion["items"]
    )
    saldo_proyectado = ingresos - gastos_proyectados

    # Patrimonio neto
    activos, pasivos = await repo.obtener_patrimonio_neto()
    patrimonio_neto = activos - pasivos

    # Variación vs período anterior (simplificado: no disponible sin 2 períodos)
    # TODO: calcular cuando haya datos históricos reales
    variacion_patrimonio = Decimal("0")

    # Badge inbox
    inbox_count = await repo.obtener_conteo_inbox_pendiente()

    # Serializar período
    periodo_data = None
    if periodo:
        periodo_data = {
            "id": periodo.id,
            "fecha_inicio": str(periodo.fecha_inicio),
            "fecha_fin_tentativa": str(periodo.fecha_fin_tentativa),
            "fecha_fin_real": str(periodo.fecha_fin_real) if periodo.fecha_fin_real else None,
            "estado": periodo.estado,
            "dias_transcurridos": dias_transcurridos,
            "dias_totales": dias_totales,
        }

    return {
        "periodo": periodo_data,
        "ingresos_acreditados": float(ingresos),
        "gastos_acumulados": float(gastos),
        "saldo_disponible_hoy": float(saldo_disponible),
        "saldo_proyectado_cierre": float(saldo_proyectado),
        "patrimonio_neto": float(patrimonio_neto),
        "variacion_patrimonio_mes_anterior": float(variacion_patrimonio),
        "inbox_pendiente_count": inbox_count,
    }
