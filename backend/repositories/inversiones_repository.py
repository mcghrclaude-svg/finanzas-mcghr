"""
InversionesRepository -- acceso a datos para activos de inversion
(AHORRO | ACCIONES | INMUEBLE).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.inversion import Inversion, Valuacion


class InversionesRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def listar_activas(self) -> list[Inversion]:
        q = select(Inversion).where(Inversion.activa == True).order_by(Inversion.nombre)  # noqa: E712
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def ultima_valuacion_por_inversion(self) -> dict[str, Valuacion]:
        """Ultima valuacion (por fecha) de cada inversion activa -- para el
        desglose 'por cuenta' del widget de patrimonio."""
        q = (
            select(Valuacion)
            .join(Inversion, Valuacion.id_inversion == Inversion.id)
            .where(Inversion.activa == True)  # noqa: E712
            .order_by(Valuacion.id_inversion, Valuacion.fecha.desc())
        )
        result = await self.db.execute(q)
        ultimas: dict[str, Valuacion] = {}
        for val in result.scalars().all():
            ultimas.setdefault(val.id_inversion, val)
        return ultimas

    async def valuaciones_activas(self) -> list[Valuacion]:
        """Todas las valuaciones de inversiones activas, para reconstruir la
        serie mensual del widget de patrimonio (Evolucion patrimonio)."""
        q = (
            select(Valuacion)
            .join(Inversion, Valuacion.id_inversion == Inversion.id)
            .where(Inversion.activa == True)  # noqa: E712
            .order_by(Valuacion.fecha.asc())
        )
        result = await self.db.execute(q)
        return list(result.scalars().all())
