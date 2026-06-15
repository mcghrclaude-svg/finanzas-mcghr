"""
Repository: acceso a datos para transacciones.

Patrón Repository:
    - Encapsula todas las queries SQLAlchemy
    - Los services NO usan la sesión DB directamente
    - Facilita mocking en tests unitarios
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.transaccion import Transaccion


class TransaccionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: str) -> Transaccion | None:
        result = await self.db.execute(select(Transaccion).where(Transaccion.id == id))
        return result.scalar_one_or_none()

    async def list_with_filters(self, filtros: dict, cursor: str | None, limit: int) -> list[Transaccion]:
        # TODO: aplicar filtros dinámicos y cursor pagination
        result = await self.db.execute(select(Transaccion).limit(limit))
        return list(result.scalars().all())

    async def create(self, datos: dict) -> Transaccion:
        # TODO: implementar
        pass

    async def update(self, id: str, cambios: dict) -> Transaccion | None:
        # TODO: implementar
        pass

    async def soft_delete(self, id: str) -> bool:
        t = await self.get_by_id(id)
        if not t:
            return False
        t.estado = "anulada"
        await self.db.commit()
        return True
