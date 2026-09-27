"""
InversionesService -- patrimonio (activos vs. deudas) para el widget
"Evolucion patrimonio" del Home, y helpers de detalle por cuenta/prestamo.

Activos: reales, desde Inversion/Valuacion (via PresupuestoRepository, que ya
tenia esta cuenta para el dashboard clasico).
Deudas: saldo_pendiente cargado a mano en Obligacion (v1.8) -- ver
backend/models/obligacion.py para el porque.
"""

from __future__ import annotations

import calendar
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.inversiones_repository import InversionesRepository
from backend.repositories.obligaciones_repository import ObligacionesRepository
from backend.repositories.presupuesto_repo import PresupuestoRepository


def _meses_hacia_atras(anio: int, mes: int, n: int) -> list[tuple[int, int]]:
    """(anio, mes) de los ultimos n meses calendario, terminando en el mes
    dado, en orden ascendente (mas viejo primero)."""
    idx = anio * 12 + (mes - 1)
    return [((idx - i) // 12, (idx - i) % 12 + 1) for i in range(n - 1, -1, -1)]


def _serie_mensual_asof(
    eventos: list[tuple[str, date, Decimal]],
    anio_hasta: int,
    mes_hasta: int,
    meses: int,
) -> list[dict]:
    """Para cada uno de los ultimos `meses` meses calendario (terminando en
    anio_hasta/mes_hasta), suma el ultimo valor conocido de cada entidad con
    fecha <= fin de ese mes. Una entidad sin ningun evento todavia a esa
    fecha simplemente no suma -- no se rellena con 0, para no inventar datos
    que no existen (historial real, aunque sea ralo)."""
    por_entidad: dict[str, list[tuple[date, Decimal]]] = {}
    for id_entidad, fecha, valor in eventos:
        por_entidad.setdefault(id_entidad, []).append((fecha, valor))
    for lst in por_entidad.values():
        lst.sort(key=lambda t: t[0])

    serie = []
    for anio, mes in _meses_hacia_atras(anio_hasta, mes_hasta, meses):
        fin_mes = date(anio, mes, calendar.monthrange(anio, mes)[1])
        total = Decimal(0)
        hay_dato = False
        for lst in por_entidad.values():
            valor_asof = None
            for fecha_ev, valor in lst:
                if fecha_ev <= fin_mes:
                    valor_asof = valor
                else:
                    break
            if valor_asof is not None:
                total += valor_asof
                hay_dato = True
        serie.append({
            "anio": anio,
            "mes": mes,
            "total": float(total) if hay_dato else None,
        })
    return serie


class InversionesService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = InversionesRepository(db)
        self.obligaciones_repo = ObligacionesRepository(db)
        self.presupuesto_repo = PresupuestoRepository(db)

    async def resumen_patrimonio(self, fecha: str | None = None) -> dict:
        activos_total, _ = await self.presupuesto_repo.obtener_patrimonio_neto()

        obligaciones_deuda = await self.obligaciones_repo.listar(tipo="DEUDA", solo_activas=True)
        deudas_total = sum(
            (Decimal(str(o.saldo_pendiente)) for o in obligaciones_deuda if o.saldo_pendiente is not None),
            Decimal(0),
        )

        inversiones = await self.repo.listar_activas()
        ultimas = await self.repo.ultima_valuacion_por_inversion()

        detalle_activos = [
            {
                "id": inv.id,
                "nombre": inv.nombre,
                "tipo": inv.tipo,
                "valor": float(ultimas[inv.id].valor) if inv.id in ultimas else None,
            }
            for inv in inversiones
        ]
        detalle_deudas = [
            {
                "id": o.id,
                "nombre": o.nombre,
                "saldo_pendiente": float(o.saldo_pendiente) if o.saldo_pendiente is not None else None,
            }
            for o in obligaciones_deuda
        ]

        return {
            "fecha": fecha,
            "activos_total": float(activos_total),
            "deudas_total": float(deudas_total),
            "patrimonio_neto": float(activos_total - deudas_total),
            "detalle_activos": detalle_activos,
            "detalle_deudas": detalle_deudas,
        }

    async def historico_patrimonio(self, meses: int = 12) -> dict:
        hoy = date.today()

        valuaciones = await self.repo.valuaciones_activas()
        eventos_activos = [
            (v.id_inversion, v.fecha.date() if hasattr(v.fecha, "date") else v.fecha, Decimal(str(v.valor)))
            for v in valuaciones
        ]
        serie_activos = _serie_mensual_asof(eventos_activos, hoy.year, hoy.month, meses)

        historico_deudas = await self.obligaciones_repo.historico_saldo()
        eventos_deudas = [
            (h.id_obligacion, h.fecha.date() if hasattr(h.fecha, "date") else h.fecha, Decimal(str(h.saldo)))
            for h in historico_deudas
        ]
        serie_deudas = _serie_mensual_asof(eventos_deudas, hoy.year, hoy.month, meses)

        puntos = []
        for act, deu in zip(serie_activos, serie_deudas):
            puntos.append({
                "anio": act["anio"],
                "mes": act["mes"],
                "activos_total": act["total"],
                "deudas_total": deu["total"],
            })

        return {"meses": meses, "puntos": puntos}
