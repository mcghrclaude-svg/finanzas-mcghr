"""
Capa de servicio: lógica de negocio para transacciones.
Intermediario entre routers y repositories.

Responsabilidades:
    - Validar reglas de negocio (ej: no anular si tiene reembolso vinculado)
    - Orquestar múltiples repositorios en una operación
    - Disparar actualización de reglas de clasificación al confirmar con corrección
    - Calcular campos derivados (completitud, etc.)

NO hace acceso directo a la DB — eso es exclusivo de los repositories.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from backend.repositories.transaccion_repo import TransaccionRepository


class TransaccionService:
    def __init__(self, db: AsyncSession):
        self.repo = TransaccionRepository(db)

    async def listar(self, filtros: dict) -> list:
        # TODO: aplicar filtros, paginar
        return []

    async def obtener(self, id: str):
        return await self.repo.get_by_id(id)

    async def crear(self, datos: dict):
        # TODO: calcular completitud, asignar origen='manual'
        return await self.repo.create(datos)

    async def editar(self, id: str, cambios: dict):
        # TODO: si cambia categoria, evaluar crear regla de clasificacion
        return await self.repo.update(id, cambios)

    async def confirmar(self, id: str):
        # TODO: mueve de inbox a transacciones
        pass

    async def descartar(self, id: str):
        pass

    async def anular(self, id: str):
        # TODO: verificar que no tenga reembolso vinculado activo
        return await self.repo.soft_delete(id)
