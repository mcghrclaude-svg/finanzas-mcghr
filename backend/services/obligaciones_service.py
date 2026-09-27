"""
ObligacionesService -- logica de negocio para compromisos financieros y
recurrentes.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.obligacion import Obligacion
from backend.repositories.obligaciones_repository import ObligacionesRepository
from backend.core.exceptions import NotFoundError


def _serializar(o: Obligacion) -> dict:
    return {
        "id": o.id,
        "nombre": o.nombre,
        "tipo": o.tipo,
        "monto_cuota": float(o.monto_cuota) if o.monto_cuota is not None else None,
        "moneda": o.moneda,
        "dia_vencimiento": o.dia_vencimiento,
        "dias_aviso_anticipado": o.dias_aviso_anticipado,
        "activa": bool(o.activa),
        "fecha_inicio": o.fecha_inicio.isoformat() if o.fecha_inicio else None,
        "fecha_fin": o.fecha_fin.isoformat() if o.fecha_fin else None,
        "capital_inicial": float(o.capital_inicial) if o.capital_inicial is not None else None,
        "tasa_interes_anual": float(o.tasa_interes_anual) if o.tasa_interes_anual is not None else None,
        "plazo_meses": o.plazo_meses,
        "saldo_pendiente": float(o.saldo_pendiente) if o.saldo_pendiente is not None else None,
    }


class ObligacionesService:
    def __init__(self, db: AsyncSession):
        self.repo = ObligacionesRepository(db)

    async def listar(self, tipo: str | None = None, solo_activas: bool = True) -> dict:
        items = await self.repo.listar(tipo=tipo, solo_activas=solo_activas)
        return {"items": [_serializar(o) for o in items]}

    async def detalle(self, obligacion_id: str) -> dict:
        obligacion = await self.repo.obtener_por_id(obligacion_id)
        if not obligacion:
            raise NotFoundError("obligacion", obligacion_id)
        return _serializar(obligacion)

    async def editar(self, obligacion_id: str, campos: dict) -> dict:
        campos_limpios = {k: v for k, v in campos.items() if v is not None}
        obligacion = await self.repo.actualizar(obligacion_id, campos_limpios)
        if not obligacion:
            raise NotFoundError("obligacion", obligacion_id)
        return _serializar(obligacion)
