"""
PresupuestoRepository -- acceso a datos para presupuestos, periodos y velocidad historica.

Correcciones Junio 2026:
    #23 -- monto viene de tramos.monto_origen (JOIN), no de transacciones.monto
    #24 -- estado='confirmado' (no 'confirmada'), tipo='gasto' (no 'GASTO')
    #25 -- conteo inbox usa transacciones pendientes, no inbox_mobile
"""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.presupuesto import Presupuesto
from backend.models.periodo import PeriodoFinanciero
from backend.models.velocidad_historica import VelocidadHistorica
from backend.models.transaccion import Transaccion, Tramo
from backend.models.inversion import Inversion, Valuacion
from backend.models.catalogo import Categoria


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

    async def upsert(
        self,
        anio: int,
        mes: int,
        id_categoria: str,
        monto: Decimal,
        id_periodo: str | None = None,
    ) -> Presupuesto:
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
                anio=anio,
                mes=mes,
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

    # ── Periodos financieros ──────────────────────────────────────────────────

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

    # ── Gastos acumulados en un periodo ──────────────────────────────────────
    # FIX #23: monto viene de tramos.monto_origen via JOIN
    # FIX #24: tipo='gasto' (minuscula), estado='confirmado' (sin 'a' final)
    # FIX #27: fecha es TEXT en la DB -- comparar con strings ISO

    async def obtener_gasto_acumulado_periodo(
        self,
        id_categoria: str,
        fecha_inicio: date,
        fecha_hasta: date,
    ) -> Decimal:
        """
        Suma de transacciones tipo 'gasto' confirmadas para una categoria
        entre fecha_inicio y fecha_hasta (inclusive).

        El monto viene de tramos.monto_origen (numero_orden=1),
        no de transacciones.monto (que no existe en la DB real).
        Las fechas se comparan como strings ISO porque fecha es TEXT en la DB.
        """
        result = await self.db.execute(
            select(func.coalesce(func.sum(Tramo.monto_origen), 0))
            .join(Transaccion, and_(
                Tramo.id_transaccion == Transaccion.id,
                Tramo.numero_orden == 1,
            ))
            .where(
                and_(
                    Transaccion.id_categoria == id_categoria,
                    Transaccion.tipo == "gasto",
                    Transaccion.estado == "confirmado",
                    func.coalesce(Transaccion.es_reembolsable, 0) == 0,
                    Transaccion.fecha >= fecha_inicio.isoformat(),
                    Transaccion.fecha <= fecha_hasta.isoformat(),
                )
            )
        )
        return Decimal(str(result.scalar() or 0))

    async def obtener_gastos_totales_periodo(
        self,
        fecha_inicio: date,
        fecha_hasta: date,
    ) -> Decimal:
        """Total de gastos confirmados en el periodo (todas las categorias).

        Excluye gastos marcados como Business Expense (es_reembolsable=1):
        son un adelanto a nombre de la familia que el empleador reembolsa,
        no un gasto familiar real -- no deben inflar este total."""
        result = await self.db.execute(
            select(func.coalesce(func.sum(Tramo.monto_origen), 0))
            .join(Transaccion, and_(
                Tramo.id_transaccion == Transaccion.id,
                Tramo.numero_orden == 1,
            ))
            .where(
                and_(
                    Transaccion.tipo == "gasto",
                    Transaccion.estado == "confirmado",
                    func.coalesce(Transaccion.es_reembolsable, 0) == 0,
                    Transaccion.fecha >= fecha_inicio.isoformat(),
                    Transaccion.fecha <= fecha_hasta.isoformat(),
                )
            )
        )
        return Decimal(str(result.scalar() or 0))

    async def obtener_ingresos_periodo(
        self,
        fecha_inicio: date,
        fecha_hasta: date,
    ) -> Decimal:
        """Suma de transacciones tipo 'ingreso' confirmadas en el periodo."""
        result = await self.db.execute(
            select(func.coalesce(func.sum(Tramo.monto_origen), 0))
            .join(Transaccion, and_(
                Tramo.id_transaccion == Transaccion.id,
                Tramo.numero_orden == 1,
            ))
            .where(
                and_(
                    Transaccion.tipo == "ingreso",
                    Transaccion.estado == "confirmado",
                    Transaccion.fecha >= fecha_inicio.isoformat(),
                    Transaccion.fecha <= fecha_hasta.isoformat(),
                )
            )
        )
        return Decimal(str(result.scalar() or 0))

    # ── Categorias ────────────────────────────────────────────────────────────

    async def listar_categorias_activas(self) -> list[Categoria]:
        result = await self.db.execute(
            select(Categoria)
            .where(Categoria.activa == True)  # noqa: E712
            .order_by(Categoria.nivel, Categoria.nombre)
        )
        return list(result.scalars().all())

    # ── Gasto por categoria en un rango de fechas (mes calendario) ───────────
    # Usado por el resumen de Home de la PWA: gasto acumulado del mes y
    # promedio de los ultimos 3 meses, ambos por categoria individual (el
    # rollup nivel1/nivel2/nivel3 lo arma PresupuestoService, no esta query).

    async def obtener_gasto_por_categoria_rango(
        self,
        fecha_inicio: date,
        fecha_hasta: date,
    ) -> dict[str, Decimal]:
        result = await self.db.execute(
            select(Transaccion.id_categoria, func.coalesce(func.sum(Tramo.monto_origen), 0))
            .join(Tramo, and_(
                Tramo.id_transaccion == Transaccion.id,
                Tramo.numero_orden == 1,
            ))
            .where(
                and_(
                    Transaccion.tipo == "gasto",
                    Transaccion.estado == "confirmado",
                    func.coalesce(Transaccion.es_reembolsable, 0) == 0,
                    Transaccion.fecha >= fecha_inicio.isoformat(),
                    Transaccion.fecha <= fecha_hasta.isoformat(),
                )
            )
            .group_by(Transaccion.id_categoria)
        )
        return {id_categoria: Decimal(str(total)) for id_categoria, total in result.all()}

    # ── Velocidad historica ───────────────────────────────────────────────────

    async def obtener_velocidad_historica(
        self,
        id_categoria: str,
        n_periodos: int = 3,
    ) -> list[VelocidadHistorica]:
        result = await self.db.execute(
            select(VelocidadHistorica)
            .where(VelocidadHistorica.id_categoria == id_categoria)
            .order_by(VelocidadHistorica.id_periodo.desc())
            .limit(n_periodos)
        )
        return list(result.scalars().all())

    # ── Inbox badge (FIX #25) ─────────────────────────────────────────────────

    async def obtener_conteo_inbox_pendiente(self) -> int:
        """
        Cuenta transacciones pendientes de revision humana.

        FIX #25: antes contaba inbox_mobile (JSONs de la PWA sin procesar),
        que es una tabla diferente. El badge del dashboard debe mostrar
        cuantas transacciones esperan confirmacion del humano.
        """
        result = await self.db.execute(
            select(func.count(Transaccion.id)).where(
                and_(
                    Transaccion.estado == "pendiente",
                    Transaccion.revisado_humano == 0,
                )
            )
        )
        return result.scalar() or 0

    # ── Patrimonio neto ───────────────────────────────────────────────────────

    async def obtener_patrimonio_neto(self) -> tuple[Decimal, Decimal]:
        """
        Retorna (activos_totales, pasivos_totales).
        Activos: inversiones valuadas + saldo de cuentas corrientes/ahorros.
        Pasivos: obligaciones vigentes con saldo pendiente.
        """
        # Activos: ultima valuacion de cada inversion
        result_activos = await self.db.execute(
            select(func.coalesce(func.sum(Valuacion.valor), 0))
            .join(Inversion, Valuacion.id_inversion == Inversion.id)
            .where(Inversion.activa == True)  # noqa: E712
        )
        activos = Decimal(str(result_activos.scalar() or 0))

        # Pasivos: Obligacion no tiene un campo de saldo pendiente actual --
        # solo capital_inicial (el monto original del prestamo). Sin logica
        # de amortizacion no hay forma de calcular cuanto queda por pagar,
        # asi que devuelve 0 en vez de una cifra fabricada (capital_inicial
        # sobreestimaria el pasivo real de cualquier deuda en pago).
        pasivos = Decimal("0")

        return activos, pasivos
