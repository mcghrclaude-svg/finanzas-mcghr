from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.presupuesto import Presupuesto


class PresupuestoRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_mes(self, anio: int, mes: int) -> list[Presupuesto]:
        result = await self.db.execute(
            select(Presupuesto).where(
                Presupuesto.anio == anio,
                Presupuesto.mes == mes,
            )
        )
        return list(result.scalars().all())

    async def create(self, datos: dict) -> Presupuesto:
        # TODO: implementar
        pass

    async def update_monto(self, id: str, monto) -> Presupuesto | None:
        # TODO: implementar
        pass

    async def delete(self, id: str) -> bool:
        # TODO: implementar
        pass
