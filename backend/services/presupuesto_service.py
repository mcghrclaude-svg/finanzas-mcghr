from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from backend.repositories.presupuesto_repo import PresupuestoRepository


class PresupuestoService:
    def __init__(self, db: AsyncSession):
        self.repo = PresupuestoRepository(db)

    async def obtener_ejecucion_mes(self, anio: int, mes: int) -> dict:
        """
        Para cada categoría con presupuesto en el mes:
            - monto presupuestado
            - gasto real acumulado
            - proyección al cierre del mes
        Fórmula proyección: gasto_a_hoy / dias_transcurridos * dias_del_mes
        """
        hoy = date.today()
        dias_transcurridos = hoy.day
        import calendar
        dias_del_mes = calendar.monthrange(anio, mes)[1]
        factor = dias_del_mes / dias_transcurridos if dias_transcurridos > 0 else 1

        # TODO: implementar query real
        return {"factor_proyeccion": factor, "items": []}

    async def benchmark_categoria(self, id_categoria: str) -> dict:
        """
        Gasto histórico de la categoría: último mes, 3M promedio, 6M promedio.
        Mostrado al usuario al definir el presupuesto de una categoría.
        """
        return {"ultimo_mes": 0, "promedio_3m": 0, "promedio_6m": 0}
