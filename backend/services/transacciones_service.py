"""
TransaccionesService -- logica de negocio para alta manual de transacciones.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.transacciones_repository import TransaccionesRepository
from backend.core.exceptions import NotFoundError


class TransaccionesService:
    def __init__(self, db: AsyncSession):
        self.repo = TransaccionesRepository(db)

    async def crear(self, campos: dict) -> dict:
        tx = await self.repo.crear_manual(campos)
        return {"ok": True, "id": tx.id}

    async def agregar_adjunto(
        self, tx_id: str, nombre_archivo: str, ruta: str,
        tipo_mime: str | None, tipo_vinculo: str = "factura",
    ) -> dict:
        tx = await self.repo.obtener_por_id(tx_id)
        if not tx:
            raise NotFoundError("transaccion", tx_id)

        vinculo = await self.repo.agregar_documento(
            tx_id, nombre_archivo, ruta, tipo_mime, tipo_vinculo,
        )
        return {"ok": True, "id": vinculo.id}
