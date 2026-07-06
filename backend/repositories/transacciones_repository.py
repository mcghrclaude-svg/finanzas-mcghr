"""
TransaccionesRepository -- acceso a datos para alta manual de transacciones.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.transaccion import Transaccion, Tramo
from backend.models.documento import Documento
from backend.models.vinculo import Vinculo


class TransaccionesRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

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
