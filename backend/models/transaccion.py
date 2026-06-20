"""
Modelos: Transaccion, Tramo, Asiento

Alineado exactamente con la DB real (verificado con .schema transacciones).

Columnas de transacciones en la DB:
    id, fecha, fecha_hora, tipo, descripcion,
    id_categoria, id_categoria2, id_contraparte, quien_pago, para_quien,
    es_recurrente, id_recurrencia, estado, confianza, revisado_humano,
    fuente, id_correo, notas, fecha_procesado,
    completitud (TEXT), es_reembolsable, estado_reembolso,
    id_transaccion_reembolso, id_evento, estado_enriquecimiento,
    origen, id_persona
"""

from sqlalchemy import (
    Column, String, Numeric, DateTime, Boolean,
    ForeignKey, Text, Integer, Float
)
from sqlalchemy.orm import relationship
from backend.models.base import Base


class Transaccion(Base):
    __tablename__ = "transacciones"

    id = Column(String, primary_key=True)
    fecha = Column(String, nullable=False)          # TEXT en la DB
    fecha_hora = Column(String)                     # TEXT ISO 8601 con offset
    tipo = Column(String(20), nullable=False, default="gasto")
    descripcion = Column(Text)
    para_quien = Column(String)                     # GHR | MC | ambos

    # Estado
    estado = Column(String(20), default="confirmado")
    confianza = Column(Float, default=0.8)
    revisado_humano = Column(Integer, default=0)    # 0/1
    completitud = Column(String, default="completo") # TEXT: minimo|parcial|completo

    # Catalogos
    id_categoria = Column(String, ForeignKey("categorias.id"))
    id_categoria2 = Column(String, ForeignKey("categorias.id"))
    id_contraparte = Column(String, ForeignKey("contrapartes.id"))
    quien_pago = Column(String, ForeignKey("personas.id"))
    id_persona = Column(String, ForeignKey("personas.id"))

    # Recurrencia
    es_recurrente = Column(Integer, default=0)      # 0/1
    id_recurrencia = Column(String)

    # Reembolso
    es_reembolsable = Column(Integer, default=0)    # 0/1
    estado_reembolso = Column(String)
    id_transaccion_reembolso = Column(String, ForeignKey("transacciones.id"))

    # Fuente
    fuente = Column(String(30))
    id_correo = Column(String)
    origen = Column(String(20))                     # email | pdf | mobile | manual

    # Correlacion ETL (v1.2)
    id_evento = Column(String)
    estado_enriquecimiento = Column(String(20), default="inicial")

    # Auditoria
    notas = Column(Text)
    fecha_procesado = Column(String)
    creado_en = Column(DateTime(timezone=True))
    actualizado_en = Column(DateTime(timezone=True))

    # Relaciones
    tramos = relationship(
        "Tramo", back_populates="transaccion",
        foreign_keys="Tramo.id_transaccion"
    )
    asientos = relationship("Asiento", back_populates="transaccion")
    categoria = relationship("Categoria", foreign_keys=[id_categoria])
    contraparte = relationship("Contraparte", foreign_keys=[id_contraparte])
    persona = relationship("Persona", foreign_keys=[id_persona])


class Tramo(Base):
    __tablename__ = "tramos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_transaccion = Column(String, ForeignKey("transacciones.id"), nullable=False)
    numero_orden = Column(Integer, default=1)
    id_cuenta_origen = Column(String, ForeignKey("cuentas.id"))
    id_cuenta_destino = Column(String, ForeignKey("cuentas.id"))
    monto_origen = Column(Numeric(18, 4))
    moneda_origen = Column(String(3), default="COP")
    monto_destino = Column(Numeric(18, 4))
    moneda_destino = Column(String(3))
    tipo_cambio = Column(Numeric(18, 6))
    comision = Column(Numeric(18, 4))
    moneda_comision = Column(String(3))
    fecha_tramo = Column(String)
    descripcion = Column(Text)
    estado = Column(String(20), default="pendiente")

    transaccion = relationship(
        "Transaccion", back_populates="tramos",
        foreign_keys=[id_transaccion]
    )
    cuenta_origen = relationship("Cuenta", foreign_keys=[id_cuenta_origen])
    cuenta_destino = relationship("Cuenta", foreign_keys=[id_cuenta_destino])


class Asiento(Base):
    __tablename__ = "asientos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_tramo = Column(Integer, ForeignKey("tramos.id"))
    id_transaccion = Column(String, ForeignKey("transacciones.id"))
    id_cuenta = Column(String, ForeignKey("cuentas.id"))
    tipo = Column(String(10))
    monto = Column(Numeric(18, 4))
    moneda = Column(String(3), default="COP")
    fecha = Column(String)

    transaccion = relationship("Transaccion", back_populates="asientos")
