"""
Modelo: VelocidadHistorica

Almacena la velocidad de gasto diaria promedio por categoría,
calculada al cierre de cada período financiero.

Uso principal: cálculo de riesgo en el dashboard de presupuesto.

Fórmula de riesgo:
    velocidad_actual = gasto_acumulado_hoy / dias_transcurridos
    velocidad_historica = (esta tabla, promedio 3 períodos)
    ratio_riesgo = velocidad_actual / velocidad_historica

    ratio > 1.5  → CRÍTICO  (rojo)
    ratio > 1.2  → ALTO     (amarillo)
    ratio <= 1.2 → OK       (verde)

Para categorías tipo 'fijo_unico' (arriendo, cuota préstamo) NO se calcula
velocidad — se muestra badge de próximo vencimiento en cambio.
"""

from sqlalchemy import Column, String, Numeric, Integer, ForeignKey, Date
from backend.models.base import Base


class VelocidadHistorica(Base):
    __tablename__ = "velocidad_historica"

    id = Column(String, primary_key=True)
    id_categoria = Column(String, ForeignKey("categorias.id"), nullable=False)
    id_periodo = Column(String, ForeignKey("periodos_financieros.id"), nullable=False)

    # Monto total gastado en la categoría durante el período
    monto_total = Column(Numeric(18, 4), nullable=False)

    # Cantidad de días reales del período (fecha_fin_real - fecha_inicio)
    dias_periodo = Column(Integer, nullable=False)

    # monto_total / dias_periodo — la métrica clave
    velocidad_diaria = Column(Numeric(18, 4), nullable=False)

    # Cuántos días del período hubo al menos un gasto (días activos)
    # Útil para diferenciar gasto esporádico de gasto continuo
    dias_con_gasto = Column(Integer, default=0)

    calculado_en = Column(Date)  # fecha en que se calculó (al cierre del período)
