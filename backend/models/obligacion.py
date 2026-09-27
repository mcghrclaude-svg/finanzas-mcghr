from sqlalchemy import Column, String, Numeric, DateTime, Boolean, Integer, ForeignKey
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

    # Carga manual por ahora (v1.8) -- el diseno final es derivarlo de los
    # pagos reales vinculados via POST /obligaciones/{id}/registrar-pago, no
    # de una amortizacion teorica. Ver schema/finanzas_v1_8.sql.
    saldo_pendiente = Column(Numeric(18, 4))


class SaldoObligacionHistorico(Base):
    """Una fila por cada vez que se actualiza saldo_pendiente -- serie
    temporal real (aunque rala) para el widget Evolucion patrimonio."""
    __tablename__ = "saldo_obligacion_historico"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_obligacion = Column(String, ForeignKey("obligaciones.id"), nullable=False)
    fecha = Column(DateTime(timezone=True), nullable=False)
    saldo = Column(Numeric(18, 4), nullable=False)
