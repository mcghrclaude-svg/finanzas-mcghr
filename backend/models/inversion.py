from sqlalchemy import Column, String, Numeric, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from backend.models.base import Base


class Inversion(Base):
    __tablename__ = "inversiones"
    id = Column(String, primary_key=True)
    nombre = Column(String, nullable=False)
    tipo = Column(String, nullable=False)  # AHORRO | ACCIONES | INMUEBLE
    titular = Column(String)  # GHR | MC
    moneda = Column(String(3), default="COP")
    activa = Column(Boolean, default=True)

    posiciones = relationship("Posicion", back_populates="inversion")
    valuaciones = relationship("Valuacion", back_populates="inversion")


class Posicion(Base):
    __tablename__ = "posiciones"
    id = Column(String, primary_key=True)
    id_inversion = Column(String, ForeignKey("inversiones.id"))
    ticker = Column(String)
    cantidad = Column(Numeric(18, 6))
    precio_promedio = Column(Numeric(18, 4))
    inversion = relationship("Inversion", back_populates="posiciones")


class Valuacion(Base):
    __tablename__ = "valuaciones"
    id = Column(String, primary_key=True)
    id_inversion = Column(String, ForeignKey("inversiones.id"))
    fecha = Column(DateTime(timezone=True), nullable=False)
    valor = Column(Numeric(18, 4), nullable=False)
    moneda = Column(String(3), default="COP")
    inversion = relationship("Inversion", back_populates="valuaciones")
