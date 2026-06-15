"""
Modelos: Transaccion, Tramo, Asiento

Mapean las tablas del schema v1.1:
    transacciones   — movimiento financiero cabecera
    tramos          — desagregación por persona/cuenta (para gastos compartidos)
    asientos        — partida doble contable

TODO: implementar campos completos según schema/finanzas_v1_1.sql
"""

from sqlalchemy import Column, String, Numeric, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.models.base import Base


class Transaccion(Base):
    __tablename__ = "transacciones"

    id = Column(String, primary_key=True)
    fecha = Column(DateTime(timezone=True), nullable=False)
    monto = Column(Numeric(18, 4), nullable=False)
    moneda = Column(String(3), default="COP")
    tipo = Column(String(20), nullable=False)  # GASTO | INGRESO | TRANSFERENCIA
    estado = Column(String(20), default="confirmada")  # confirmada | anulada
    descripcion = Column(Text)
    completitud = Column(Numeric(3, 2), default=1.0)
    es_recurrente = Column(Boolean, default=False)
    es_reembolsable = Column(Boolean, default=False)
    estado_reembolso = Column(String(20))  # pendiente | recibido | None
    id_transaccion_reembolso = Column(String, ForeignKey("transacciones.id"))
    id_categoria = Column(String, ForeignKey("categorias.id"))
    id_cuenta = Column(String, ForeignKey("cuentas.id"))
    id_contraparte = Column(String, ForeignKey("contrapartes.id"))
    id_persona = Column(String, ForeignKey("personas.id"))
    origen = Column(String(20))  # email | pdf | mobile | manual
    creado_en = Column(DateTime(timezone=True))
    actualizado_en = Column(DateTime(timezone=True))

    tramos = relationship("Tramo", back_populates="transaccion")
    asientos = relationship("Asiento", back_populates="transaccion")


class Tramo(Base):
    __tablename__ = "tramos"
    # TODO: campos completos
    id = Column(String, primary_key=True)
    id_transaccion = Column(String, ForeignKey("transacciones.id"))
    transaccion = relationship("Transaccion", back_populates="tramos")


class Asiento(Base):
    __tablename__ = "asientos"
    # TODO: campos completos (partida_doble: debe/haber)
    id = Column(String, primary_key=True)
    id_transaccion = Column(String, ForeignKey("transacciones.id"))
    transaccion = relationship("Transaccion", back_populates="asientos")
