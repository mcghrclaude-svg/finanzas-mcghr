"""
PresupuestoRepository — acceso a datos para presupuestos, períodos y velocidad histórica.

Métodos principales consumidos por PresupuestoService:
    obtener_por_mes             → lista de Presupuesto del mes
    obtener_periodo_activo      → PeriodoFinanciero con estado='abierto'
    obtener_gasto_acumulado     → suma de transacciones GASTO en el período
    obtener_velocidad_historica → VelocidadHistorica de los últimos N períodos
    obtener_conteo_inbox        → items pendientes en inbox_mobile
    obtener_patrimonio          → suma activos − suma deudas
"""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.presupuesto import Presupuesto
from backend.models.periodo import PeriodoFinanciero
from backend.models.velocidad_historica import VelocidadHistorica
from backend.models.transaccion import Transaccion
from backend.models.inbox import InboxMobile
from backend.models.inversion import Inversion, Valuacion
from backend.models.obligacion import Obligacion


class PresupuestoRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Presupuestos ──────────────────────────────────────────────────────────

    async def obtener_por_mes(self, anio: int, mes: int) -> list[Presupuesto]:
        result = await self.db.execute(
            select(Presupuesto).where(
                Presupuesto.anio == anio,
                Presupuesto.mes == mes,
            )
        )
        return list(result.scalars().all())

    async def upsert(self, anio: int, mes: int, id_categoria: str, monto: Decimal, id_periodo: str | None = None) -> Presupuesto:
        result = await self.db.execute(
            select(Presupuesto).where(
                Presupuesto.anio == anio,
                Presupuesto.mes == mes,
                Presupuesto.id_categoria == id_categoria,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.monto_presupuestado = monto
            if id_periodo:
                existing.id_periodo = id_periodo
        else:
            existing = Presupuesto(
                id=str(uuid.uuid4()),
                anio=anio, mes=mes,
                id_categoria=id_categoria,
                monto_presupuestado=monto,
                id_periodo=id_periodo,
            )
            self.db.add(existing)
        await self.db.flush()
        return existing

    async def eliminar(self, anio: int, mes: int, id_categoria: str) -> bool:
        result = await self.db.execute(
            select(Presupuesto).where(
                Presupuesto.anio == anio,
                Presupuesto.mes == mes,
                Presupuesto.id_categoria == id_categoria,
            )
        )
        p = result.scalar_one_or_none()
        if not p:
            return False
        await self.db.delete(p)
        await self.db.flush()
        return True

    # ── Períodos financieros ─────────────────────────────────────────────────

    async def obtener_periodo_activo(self) -> PeriodoFinanciero | None:
        result = await self.db.execute(
            select(PeriodoFinanciero)
            .where(PeriodoFinanciero.estado == "abierto")
            .order_by(PeriodoFinanciero.fecha_inicio.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def obtener_periodo_por_id(self, id_periodo: str) -> PeriodoFinanciero | None:
        return await self.db.get(PeriodoFinanciero, id_periodo)

    async def listar_periodos(self, limit: int = 12) -> list[PeriodoFinanciero]:
        result = await self.db.execute(
            select(PeriodoFinanciero)
            .order_by(PeriodoFinanciero.fecha_inicio.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    # ── Gastos acumulados en un período ────────────────────────────────────────

    async def obtener_gasto_acumulado_periodo(
        self,
        id_categoria: str,
        fecha_inicio: date,
        fecha_hasta: date,
    ) -> Decimal:
        """
        Suma de transacciones tipo GASTO confirmadas para una categoría
        entre fecha_inicio y fecha_hasta (inclusive).
        """
        result = await self.db.execute(
            select(func.coalesce(func.sum(Transaccion.monto), 0)).where(
                and_(
                    Transaccion.id_categoria == id_categoria,
                    Transaccion.tipo == "GASTO",
                    Transaccion.estado == "confirmada",
                    Transaccion.fecha >= fecha_inicio,
                    Transaccion.fecha <= fecha_hasta,
                )
            )
        )
        return Decimal(str(result.scalar()))

    async def obtener_gastos_totales_periodo(
        self,
        fecha_inicio: date,
        fecha_hasta: date,
    ) -> Decimal:
        """Total de gastos confirmados en el período (todas las categorías)."""
        result = await self.db.execute(
            select(func.coalesce(func.sum(Transaccion.monto), 0)).where(
                and_(
                    Transaccion.tipo == "GASTO",
                    Transaccion.estado == "confirmada",
                    Transaccion.fecha >= fecha_inicio,
                    Transaccion.fecha <= fecha_hasta,
                )
            )
        )
        return Decimal(str(result.scalar()))

    async def obtener_ingresos_periodo(
        self,
        fecha_inicio: date,
        fecha_hasta: date,
    ) -> Decimal:
        """Suma de transacciones tipo INGRESO confirmadas en el período."""
        result = await self.db.execute(
            select(func.coalesce(func.sum(Transaccion.monto), 0)).where(
                and_(
                    Transaccion.tipo == "INGRESO",
                    Transaccion.estado == "confirmada",
                    Transaccion.fecha >= fecha_inicio,
                    Transaccion.fecha <= fecha_hasta,
                )
            )
        )
        return Decimal(str(result.scalar()))

    # ── Velocidad histórica ────────────────────────────────────────────────────

    async def obtener_velocidad_historica(
        self,
        id_categoria: str,
        n_periodos: int = 3,
    ) -> list[VelocidadHistorica]:
        """
        Retorna los últimos N registros de velocidad_historica para la categoría,
        ordenados por período descendente (más reciente primero).
        Usado para calcular el promedio histórico de velocidad diaria.
        """
        result = await self.db.execute(
            select(VelocidadHistorica)
            .where(VelocidadHistorica.id_categoria == id_categoria)
            .order_by(VelocidadHistorica.id_periodo.desc())
            .limit(n_periodos)
        )
        return list(result.scalars().all())

    # ── Inbox (para badge dashboard) ─────────────────────────────────────────

    async def obtener_conteo_inbox_pendiente(self) -> int:
        result = await self.db.execute(
            select(func.count(InboxMobile.id)).where(
                InboxMobile.estado == "pendiente"
            )
        )
        return result.scalar() or 0

    # ── Patrimonio neto ─────────────────────────────────────────────────────

    async def obtener_patrimonio_neto(self) -> tuple[Decimal, Decimal]:
        """
        Retorna (activos_totales, pasivos_totales).
        activos = suma últimas valuaciones de inversiones activas
        pasivos = suma saldo_pendiente de obligaciones activas tipo DEUDA
        patrimonio_neto = activos - pasivos
        """
        # Última valuación por inversión
        # Subconsulta: max(valuacion.fecha) por inversion
        subq = (
            select(
                Valuacion.id_inversion,
                func.max(Valuacion.fecha).label("max_fecha")
            )
            .group_by(Valuacion.id_inversion)
            .subquery()
        )
        activos_result = await self.db.execute(
            select(func.coalesce(func.sum(Valuacion.valor_total_cop), 0))
            .join(subq, and_(
                Valuacion.id_inversion == subq.c.id_inversion,
                Valuacion.fecha == subq.c.max_fecha,
            ))
            .join(Inversion, Inversion.id == Valuacion.id_inversion)
            .where(Inversion.activa == True)
        )
        activos = Decimal(str(activos_result.scalar() or 0))

        pasivos_result = await self.db.execute(
            select(func.coalesce(func.sum(Obligacion.saldo_pendiente), 0))
            .where(
                and_(
                    Obligacion.tipo == "DEUDA",
                    Obligacion.activa == True,
                )
            )
        )
        pasivos = Decimal(str(pasivos_result.scalar() or 0))

        return activos, pasivos
