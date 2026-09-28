"""
ObligacionesRepository -- acceso a datos para compromisos financieros y
recurrentes (DEUDA | SERVICIO | RECURRENTE).
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.obligacion import Obligacion, SaldoObligacionHistorico


class ObligacionesRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def listar(
        self,
        tipo: str | None = None,
        solo_activas: bool = True,
    ) -> list[Obligacion]:
        q = select(Obligacion)
        if tipo:
            q = q.where(Obligacion.tipo == tipo)
        if solo_activas:
            q = q.where(Obligacion.activa == True)  # noqa: E712
        q = q.order_by(Obligacion.nombre)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def obtener_por_id(self, obligacion_id: str) -> Obligacion | None:
        return await self.db.get(Obligacion, obligacion_id)

    async def actualizar(self, obligacion_id: str, campos: dict) -> Obligacion | None:
        obligacion = await self.obtener_por_id(obligacion_id)
        if not obligacion:
            return None

        saldo_nuevo = campos.get("saldo_pendiente")
        cambia_saldo = "saldo_pendiente" in campos and saldo_nuevo != obligacion.saldo_pendiente

        for campo, valor in campos.items():
            setattr(obligacion, campo, valor)

        if cambia_saldo:
            self.db.add(SaldoObligacionHistorico(
                id_obligacion=obligacion_id,
                fecha=datetime.now(timezone.utc),
                saldo=saldo_nuevo,
            ))

        await self.db.flush()
        return obligacion

    async def historico_saldo(self, meses: int = 12) -> list[SaldoObligacionHistorico]:
        """Todas las filas de historico dentro de la ventana pedida, para
        agregarlas por mes (suma de saldo_pendiente de todas las obligaciones
        activas de tipo DEUDA) desde el servicio de patrimonio."""
        q = (
            select(SaldoObligacionHistorico)
            .order_by(SaldoObligacionHistorico.fecha.asc())
        )
        result = await self.db.execute(q)
        return list(result.scalars().all())
