"""
Router: /api/v1/dashboard

Endpoint principal del Home de escritorio.
Agrega en una sola llamada todas las metricas del top del dashboard:
    - Ingresos acreditados en el mes calendario
    - Gastos acumulados hasta hoy (mes calendario)
    - Saldo disponible hoy (ingresos - gastos)
    - Saldo proyectado al cierre (ritmo simple: gasto_acumulado/dia * dias_totales)
    - Patrimonio neto (activos inversion - deudas)
    - Variacion patrimonio vs periodo anterior
    - Count de inbox pendiente (badge de catalogacion)

Usa mes calendario en todo el Home (no periodo financiero de salario) para
ser consistente con /presupuestos/resumen-por-categoria (que ya usa mes
calendario, mismo criterio que la PWA) -- ver ADR pendiente de registrar.
El concepto de periodo financiero (PeriodoFinanciero, dia_acreditacion_salario)
sigue existiendo para Budget Mgmt y /presupuestos/ejecucion, que no cambian.

Disenado para ser llamado una sola vez al cargar el Home.
"""

import calendar
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from backend.core.database import get_db
from backend.repositories.presupuesto_repo import PresupuestoRepository

router = APIRouter()


@router.get("/resumen")
async def resumen_dashboard(
    anio: int | None = Query(None, description="Anio (default: actual)"),
    mes: int | None = Query(None, description="Mes 1-12 (default: actual)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Metricas consolidadas del Home. Llamada unica al montar la pagina.

    El frontend usa estos datos para:
      - Top bar: dia del mes calendario transcurrido
      - 4 metric cards: ingresos, gastos, saldo proy., patrimonio
      - Badge del inbox
    """
    hoy = date.today()
    anio = anio or hoy.year
    mes = mes or hoy.month

    repo = PresupuestoRepository(db)

    fecha_inicio = date(anio, mes, 1)
    ultimo_dia = calendar.monthrange(anio, mes)[1]
    fecha_fin_mes = date(anio, mes, ultimo_dia)
    es_mes_actual = (anio, mes) == (hoy.year, hoy.month)
    fecha_hasta = hoy if es_mes_actual else fecha_fin_mes
    dias_transcurridos = max(hoy.day if es_mes_actual else ultimo_dia, 1)
    dias_totales = ultimo_dia

    # Ingresos acreditados en el mes calendario
    ingresos = await repo.obtener_ingresos_periodo(fecha_inicio, fecha_hasta)

    # Gastos acumulados hasta hoy (mes calendario)
    gastos = await repo.obtener_gastos_totales_periodo(fecha_inicio, fecha_hasta)

    # Saldo disponible hoy
    saldo_disponible = ingresos - gastos

    # Proyeccion simple por ritmo (sin modelo de velocidad por categoria):
    # gasto_acumulado / dias_transcurridos * dias_totales
    gastos_proyectados = (gastos / Decimal(dias_transcurridos)) * Decimal(dias_totales)
    saldo_proyectado = ingresos - gastos_proyectados

    # Patrimonio neto
    activos, pasivos = await repo.obtener_patrimonio_neto()
    patrimonio_neto = activos - pasivos

    # Variacion vs mes anterior (simplificado: no disponible sin historico real)
    # TODO: calcular cuando haya datos historicos reales
    variacion_patrimonio = Decimal("0")

    # Badge inbox
    inbox_count = await repo.obtener_conteo_inbox_pendiente()

    periodo_data = {
        "id": None,
        "fecha_inicio": str(fecha_inicio),
        "fecha_fin_tentativa": str(fecha_fin_mes),
        "fecha_fin_real": str(fecha_fin_mes) if not es_mes_actual else None,
        "estado": "mes_calendario",
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
