"""
InboxService — logica de negocio para el modulo Inbox.

Orquesta el repositorio y aplica validaciones de negocio.
No accede a la DB directamente.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.inbox_repository import InboxRepository
from backend.core.exceptions import NotFoundError, ConflictError


class InboxService:
    def __init__(self, db: AsyncSession):
        self.repo = InboxRepository(db)

    # ------------------------------------------------------------------
    # Listar
    # ------------------------------------------------------------------

    async def listar(
        self,
        estado: str = "pendiente",
        origen: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = 50,
    ) -> dict:
        items, next_cursor = await self.repo.listar(
            estado=estado,
            origen=origen,
            cursor=cursor,
            limit=limit,
        )
        total = await self.repo.contar_pendientes()

        return {
            "items": items,
            "next_cursor": next_cursor,
            "total_pendientes": total,
        }

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    async def stats(self) -> dict:
        return {
            "pendientes": await self.repo.contar_pendientes(),
            "alta_prioridad": await self.repo.contar_alta_prioridad(),
            "confirmados_hoy": await self.repo.contar_confirmados_hoy(),
        }

    # ------------------------------------------------------------------
    # Detalle
    # ------------------------------------------------------------------

    async def obtener(self, tx_id: str):
        tx = await self.repo.obtener_por_id(tx_id)
        if not tx:
            raise NotFoundError("transaccion", tx_id)
        return tx

    # ------------------------------------------------------------------
    # Editar
    # ------------------------------------------------------------------

    async def editar(self, tx_id: str, campos: dict):
        tx = await self.repo.obtener_por_id(tx_id)
        if not tx:
            raise NotFoundError("transaccion", tx_id)

        if tx.estado not in ("pendiente", "confirmado"):
            raise ConflictError(
                f"No se puede editar una transaccion en estado '{tx.estado}'"
            )

        campos_limpios = {k: v for k, v in campos.items() if v is not None}
        return await self.repo.actualizar(tx_id, campos_limpios)

    # ------------------------------------------------------------------
    # Confirmar
    # ------------------------------------------------------------------

    async def confirmar(
        self,
        tx_id: str,
        id_categoria: Optional[str] = None,
        notas: Optional[str] = None,
    ) -> dict:
        tx = await self.repo.obtener_por_id(tx_id)
        if not tx:
            raise NotFoundError("transaccion", tx_id)

        if tx.estado == "anulado":
            raise ConflictError("No se puede confirmar una transaccion anulada")

        tx_actualizada, regla_creada = await self.repo.confirmar(
            tx_id=tx_id,
            id_categoria_corregida=id_categoria,
            notas=notas,
        )

        return {
            "ok": True,
            "id": tx_id,
            "regla_creada": regla_creada,
        }

    # ------------------------------------------------------------------
    # Descartar
    # ------------------------------------------------------------------

    async def descartar(self, tx_id: str) -> dict:
        tx = await self.repo.obtener_por_id(tx_id)
        if not tx:
            raise NotFoundError("transaccion", tx_id)

        if tx.estado == "confirmado" and tx.revisado_humano:
            raise ConflictError(
                "La transaccion ya fue confirmada. Anulala desde el modulo de transacciones."
            )

        await self.repo.descartar(tx_id)
        return {"ok": True, "id": tx_id}

    # ------------------------------------------------------------------
    # Confirmar lote
    # ------------------------------------------------------------------

    async def confirmar_lote(self, ids: list[str]) -> dict:
        confirmados = 0
        errores = []

        for tx_id in ids:
            try:
                await self.confirmar(tx_id)
                confirmados += 1
            except Exception as e:
                errores.append({"id": tx_id, "error": str(e)})

        return {"confirmados": confirmados, "errores": errores}
