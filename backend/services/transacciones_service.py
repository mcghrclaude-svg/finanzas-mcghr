"""
TransaccionesService -- logica de negocio para alta manual y listado de
transacciones.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.transaccion import Transaccion
from backend.repositories.transacciones_repository import TransaccionesRepository
from backend.core.exceptions import NotFoundError


def _serializar(tx: Transaccion) -> dict:
    tramos_ordenados = sorted(tx.tramos, key=lambda t: t.numero_orden)
    tramo1 = tramos_ordenados[0] if tramos_ordenados else None
    return {
        "id": tx.id,
        "fecha": tx.fecha,
        "fecha_hora": tx.fecha_hora,
        "tipo": tx.tipo,
        "descripcion": tx.descripcion,
        "estado": tx.estado,
        "confianza": tx.confianza,
        "revisado_humano": bool(tx.revisado_humano),
        "completitud": tx.completitud,
        "id_categoria": tx.id_categoria,
        "id_categoria2": tx.id_categoria2,
        "id_contraparte": tx.id_contraparte,
        "quien_pago": tx.quien_pago,
        "es_recurrente": bool(tx.es_recurrente),
        "id_recurrencia": tx.id_recurrencia,
        "es_reembolsable": bool(tx.es_reembolsable),
        "estado_reembolso": tx.estado_reembolso,
        "fuente": tx.fuente,
        "origen": tx.origen,
        "notas": tx.notas,
        # Flatten conveniente: el monto/moneda "principal" vive en el tramo 1,
        # pero la mayoria de las pantallas lo muestran como si fuera un campo
        # de la transaccion.
        "monto": tramo1.monto_origen if tramo1 else None,
        "moneda": tramo1.moneda_origen if tramo1 else "COP",
        "tramos": [
            {
                "id": t.id,
                "numero_orden": t.numero_orden,
                "id_cuenta_origen": t.id_cuenta_origen,
                "id_cuenta_destino": t.id_cuenta_destino,
                "monto_origen": t.monto_origen,
                "moneda_origen": t.moneda_origen,
                "estado": t.estado,
            }
            for t in tramos_ordenados
        ],
    }


class TransaccionesService:
    def __init__(self, db: AsyncSession):
        self.repo = TransaccionesRepository(db)

    async def listar(self, **filtros) -> dict:
        limit = filtros.get("limit") or 50
        items, next_cursor = await self.repo.listar(**filtros)
        total = await self.repo.contar(**{
            k: v for k, v in filtros.items() if k not in ("cursor", "limit")
        })
        return {
            "items": [_serializar(tx) for tx in items],
            "next_cursor": next_cursor,
            "total": total,
        }

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
