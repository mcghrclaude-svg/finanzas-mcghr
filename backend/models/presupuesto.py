from sqlalchemy import Column, String, Numeric, Integer, ForeignKey
from backend.models.base import Base


class Presupuesto(Base):
    __tablename__ = "presupuestos"

    id = Column(String, primary_key=True)
    anio = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)
    id_categoria = Column(String, ForeignKey("categorias.id"), nullable=False)
    monto_presupuestado = Column(Numeric(18, 4), nullable=False)
    moneda = Column(String(3), default="COP")

    # FK al período financiero correspondiente (25-anterior → 24-actual).
    # Puede ser NULL para presupuestos históricos cargados antes de implementar períodos.
    id_periodo = Column(String, ForeignKey("periodos_financieros.id"))
