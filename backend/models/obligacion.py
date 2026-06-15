from sqlalchemy import Column, String, Numeric, DateTime, Boolean, Integer
from backend.models.base import Base


class Obligacion(Base):
    __tablename__ = "obligaciones"
    id = Column(String, primary_key=True)
    nombre = Column(String, nullable=False)
    tipo = Column(String, nullable=False)  # DEUDA | SERVICIO | RECURRENTE
    monto_cuota = Column(Numeric(18, 4))
    moneda = Column(String(3), default="COP")
    dia_vencimiento = Column(Integer)  # día del mes: 1-31
    dias_aviso_anticipado = Column(Integer, default=3)
    activa = Column(Boolean, default=True)
    fecha_inicio = Column(DateTime(timezone=True))
    fecha_fin = Column(DateTime(timezone=True))
    # Para DEUDA:
    capital_inicial = Column(Numeric(18, 4))
    tasa_interes_anual = Column(Numeric(6, 4))
    plazo_meses = Column(Integer)
