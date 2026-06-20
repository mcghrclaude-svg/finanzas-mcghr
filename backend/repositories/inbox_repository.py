"""
InboxRepository — acceso a datos para el modulo Inbox.
Corregido para usar tipos nativos (float, str) en lugar de Decimal,
alineado con la DB real donde confianza=REAL y completitud=TEXT.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.transaccion import Transaccion
from backend.models.catalogo import Categoria, Contraparte, Cuenta
from backend.models.regla import ReglaClasificacion


class InboxRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def listar(
        self,
        estado: str = "pendiente",
        origen: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = 50,
    ) -> tuple[list[Transaccion], Optional[str]]:
        q = (
            select(Transaccion)
            .options(
                selectinload(Transaccion.categoria),
                selectinload(Transaccion.contraparte),
                selectinload(Transaccion.tramos),
            )
            .where(Transaccion.estado == estado)
        )

        if estado == "pendiente":
            q = q.where(Transaccion.revisado_humano == 0)

        if origen:
            q = q.where(Transaccion.origen == origen)

        if cursor:
            q = q.where(Transaccion.id > cursor)

        q = q.order_by(Transaccion.completitud.asc(), Transaccion.creado_en.asc())
        q = q.limit(limit + 1)

        result = await self.db.execute(q)
        items = result.scalars().all()

        next_cursor = None
        if len(items) > limit:
            items = items[:limit]
            next_cursor = items[-1].id

        return list(items), next_cursor

    async def contar_pendientes(self) -> int:
        q = select(func.count()).where(
            and_(
                Transaccion.estado == "pendiente",
                Transaccion.revisado_humano == 0,
            )
        )
        result = await self.db.execute(q)
        return result.scalar() or 0

    async def contar_alta_prioridad(self) -> int:
        """Pendientes con confianza < 0.60."""
        q = select(func.count()).where(
            and_(
                Transaccion.estado == "pendiente",
                Transaccion.revisado_humano == 0,
                Transaccion.confianza < 0.60,
            )
        )
        result = await self.db.execute(q)
        return result.scalar() or 0

    async def contar_confirmados_hoy(self) -> int:
        hoy = datetime.now(timezone.utc).date()
        q = select(func.count()).where(
            and_(
                Transaccion.estado == "confirmado",
                Transaccion.revisado_humano == 1,
                func.date(Transaccion.actualizado_en) == str(hoy),
            )
        )
        result = await self.db.execute(q)
        return result.scalar() or 0

    async def obtener_por_id(self, tx_id: str) -> Optional[Transaccion]:
        q = (
            select(Transaccion)
            .options(
                selectinload(Transaccion.categoria),
                selectinload(Transaccion.contraparte),
                selectinload(Transaccion.tramos),
            )
            .where(Transaccion.id == tx_id)
        )
        result = await self.db.execute(q)
        return result.scalar_one_or_none()

    async def actualizar(self, tx_id: str, campos: dict) -> Optional[Transaccion]:
        campos["actualizado_en"] = datetime.now(timezone.utc)
        await self.db.execute(
            update(Transaccion).where(Transaccion.id == tx_id).values(**campos)
        )
        await self.db.flush()
        return await self.obtener_por_id(tx_id)

    async def confirmar(
        self,
        tx_id: str,
        id_categoria_corregida: Optional[str] = None,
        notas: Optional[str] = None,
    ) -> tuple[Optional[Transaccion], bool]:
        tx = await self.obtener_por_id(tx_id)
        if not tx:
            return None, False

        if tx.estado == "confirmado" and tx.revisado_humano:
            return tx, False

        hubo_correccion = (
            id_categoria_corregida is not None
            and id_categoria_corregida != tx.id_categoria
        )

        campos: dict = {
            "estado": "confirmado",
            "revisado_humano": 1,
            "actualizado_en": datetime.now(timezone.utc),
        }
        if id_categoria_corregida:
            campos["id_categoria"] = id_categoria_corregida
        if notas:
            campos["notas"] = notas

        await self.db.execute(
            update(Transaccion).where(Transaccion.id == tx_id).values(**campos)
        )
        await self.db.flush()

        regla_creada = False
        if hubo_correccion and tx.fuente:
            regla_creada = await self._crear_o_actualizar_regla(tx, id_categoria_corregida)

        tx_actualizada = await self.obtener_por_id(tx_id)
        return tx_actualizada, regla_creada

    async def descartar(self, tx_id: str) -> Optional[Transaccion]:
        tx = await self.obtener_por_id(tx_id)
        if not tx:
            return None

        await self.db.execute(
            update(Transaccion)
            .where(Transaccion.id == tx_id)
            .values(
                estado="anulado",
                revisado_humano=1,
                actualizado_en=datetime.now(timezone.utc),
            )
        )
        await self.db.flush()
        return await self.obtener_por_id(tx_id)

    async def _crear_o_actualizar_regla(
        self, tx: Transaccion, id_categoria_nueva: str
    ) -> bool:
        if not tx.id_correo:
            return False

        patron = tx.id_correo[:50]

        q = select(ReglaClasificacion).where(
            and_(
                ReglaClasificacion.patron == patron,
                ReglaClasificacion.activa == True,  # noqa: E712
            )
        )
        result = await self.db.execute(q)
        regla_existente = result.scalar_one_or_none()

        ahora = datetime.now(timezone.utc)

        if regla_existente:
            regla_existente.id_categoria = id_categoria_nueva
            regla_existente.id_contraparte = tx.id_contraparte
            regla_existente.ultima_coincidencia = ahora
            regla_existente.total_coincidencias = (regla_existente.total_coincidencias or 0) + 1
            await self.db.flush()
        else:
            nueva_regla = ReglaClasificacion(
                id=str(uuid.uuid4()),
                patron=patron,
                id_categoria=id_categoria_nueva,
                id_contraparte=tx.id_contraparte,
                tipo_transaccion=tx.tipo,
                peso=1.0,
                fuente="usuario",
                activa=True,
                creado_en=ahora,
                ultima_coincidencia=ahora,
                total_coincidencias=1,
            )
            self.db.add(nueva_regla)
            await self.db.flush()

        return True
