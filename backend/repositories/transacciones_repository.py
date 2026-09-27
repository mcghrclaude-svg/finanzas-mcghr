"""
TransaccionesRepository -- acceso a datos para alta manual de transacciones
y listado con filtros (usado por la pantalla de Transacciones y por el
widget de "Ultimas transacciones" del Home).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.transaccion import Transaccion, Tramo
from backend.models.documento import Documento
from backend.models.vinculo import Vinculo


class TransaccionesRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _aplicar_filtros(self, q, *, estado, origen, desde, hasta, id_categoria,
                          id_cuenta, quien_pago, tipo, id_contraparte,
                          es_recurrente, estado_reembolso):
        if estado:
            q = q.where(Transaccion.estado == estado)
        if origen:
            q = q.where(Transaccion.origen == origen)
        if desde:
            q = q.where(Transaccion.fecha >= desde)
        if hasta:
            q = q.where(Transaccion.fecha <= hasta)
        if id_categoria:
            q = q.where(Transaccion.id_categoria == id_categoria)
        if quien_pago:
            q = q.where(Transaccion.quien_pago == quien_pago)
        if tipo:
            q = q.where(Transaccion.tipo == tipo)
        if id_contraparte:
            q = q.where(Transaccion.id_contraparte == id_contraparte)
        if es_recurrente is not None:
            q = q.where(Transaccion.es_recurrente == (1 if es_recurrente else 0))
        if estado_reembolso:
            q = q.where(Transaccion.estado_reembolso == estado_reembolso)
        if id_cuenta:
            # EXISTS en vez de join: un join duplicaria la fila de Transaccion
            # por cada Tramo que matchee (ej. transferencias con 2 tramos).
            existe_tramo = (
                select(Tramo.id)
                .where(Tramo.id_transaccion == Transaccion.id)
                .where(or_(
                    Tramo.id_cuenta_origen == id_cuenta,
                    Tramo.id_cuenta_destino == id_cuenta,
                ))
                .exists()
            )
            q = q.where(existe_tramo)
        return q

    async def listar(
        self,
        estado: str | None = None,
        origen: str | None = None,
        cursor: str | None = None,
        limit: int = 50,
        desde: str | None = None,
        hasta: str | None = None,
        id_categoria: str | None = None,
        id_cuenta: str | None = None,
        quien_pago: str | None = None,
        tipo: str | None = None,
        id_contraparte: str | None = None,
        es_recurrente: bool | None = None,
        estado_reembolso: str | None = None,
    ) -> tuple[list[Transaccion], str | None]:
        q = select(Transaccion).options(
            selectinload(Transaccion.tramos).selectinload(Tramo.cuenta_origen),
            selectinload(Transaccion.tramos).selectinload(Tramo.cuenta_destino),
        )
        q = self._aplicar_filtros(
            q, estado=estado, origen=origen, desde=desde, hasta=hasta,
            id_categoria=id_categoria, id_cuenta=id_cuenta, quien_pago=quien_pago,
            tipo=tipo, id_contraparte=id_contraparte, es_recurrente=es_recurrente,
            estado_reembolso=estado_reembolso,
        )
        if cursor:
            q = q.where(Transaccion.id > cursor)

        # Mas recientes primero -- fecha es TEXT ISO (YYYY-MM-DD), el orden
        # lexicografico coincide con el cronologico.
        q = q.order_by(Transaccion.fecha.desc(), Transaccion.id.desc())
        q = q.limit(limit + 1)

        result = await self.db.execute(q)
        items = result.scalars().all()

        next_cursor = None
        if len(items) > limit:
            items = items[:limit]
            next_cursor = items[-1].id

        return list(items), next_cursor

    async def contar(
        self,
        estado: str | None = None,
        origen: str | None = None,
        desde: str | None = None,
        hasta: str | None = None,
        id_categoria: str | None = None,
        id_cuenta: str | None = None,
        quien_pago: str | None = None,
        tipo: str | None = None,
        id_contraparte: str | None = None,
        es_recurrente: bool | None = None,
        estado_reembolso: str | None = None,
    ) -> int:
        q = self._aplicar_filtros(
            select(func.count(Transaccion.id)),
            estado=estado, origen=origen, desde=desde, hasta=hasta,
            id_categoria=id_categoria, id_cuenta=id_cuenta, quien_pago=quien_pago,
            tipo=tipo, id_contraparte=id_contraparte, es_recurrente=es_recurrente,
            estado_reembolso=estado_reembolso,
        )
        result = await self.db.execute(q)
        return result.scalar() or 0

    async def obtener_por_id(self, tx_id: str) -> Transaccion | None:
        return await self.db.get(Transaccion, tx_id)

    async def crear_manual(self, campos: dict) -> Transaccion:
        ahora = datetime.now(timezone.utc)
        tx_id = str(uuid.uuid4())

        tx = Transaccion(
            id=tx_id,
            fecha=campos["fecha"],
            tipo=campos["tipo"],
            descripcion=campos["descripcion"],
            id_categoria=campos.get("id_categoria"),
            id_contraparte=campos.get("id_contraparte"),
            quien_pago=campos["quien_pago"],
            es_recurrente=campos.get("es_recurrente", False),
            es_reembolsable=campos.get("es_reembolsable", False),
            estado_reembolso=campos.get("estado_reembolso"),
            notas=campos.get("notas"),
            estado="confirmado",
            revisado_humano=1,
            completitud="completo",
            confianza=1.0,
            origen="manual",
            fuente="manual",
            creado_en=ahora,
            actualizado_en=ahora,
        )
        self.db.add(tx)

        tramo = Tramo(
            id_transaccion=tx_id,
            numero_orden=1,
            id_cuenta_origen=campos["id_cuenta_origen"],
            monto_origen=campos["monto"],
            moneda_origen=campos.get("moneda", "COP"),
            estado="confirmado",
        )
        self.db.add(tramo)

        await self.db.flush()
        return tx

    async def agregar_documento(
        self, tx_id: str, nombre_archivo: str, ruta: str,
        tipo_mime: str | None, tipo_vinculo: str,
    ) -> Vinculo:
        ahora = datetime.now(timezone.utc)
        doc_id = str(uuid.uuid4())

        doc = Documento(
            id=doc_id,
            nombre_archivo=nombre_archivo,
            ruta=ruta,
            tipo_mime=tipo_mime,
            estado="clasificado",
            origen_dispositivo="PC",
            procesado=True,
            creado_en=ahora,
        )
        self.db.add(doc)

        vinculo = Vinculo(
            id_documento=doc_id,
            id_transaccion=tx_id,
            tipo_vinculo=tipo_vinculo,
            confianza=1.0,
            fecha_vinculo=ahora.isoformat(),
            creado_por="usuario",
        )
        self.db.add(vinculo)

        await self.db.flush()
        return vinculo
