"""
Modelos: Transaccion, Tramo, Asiento

Mapean exactamente las tablas de finanzas.db.

Schema real de transacciones (columnas existentes en la DB):
    v1.0 original:   id, fecha, tipo, descripcion, id_categoria, id_categoria2,
                     id_contraparte, quien_pago, para_quien, es_recurrente,
                     id_recurrencia, estado, confianza, revisado_humano,
                     fuente, id_correo, notas, fecha_procesado
    v1.1 agrega:     completitud, es_reembolsable, estado_reembolso,
                     id_transaccion_reembolso
    v1.2 agrega:     id_evento, estado_enriquecimiento
    v1.2c agrega:    origen, id_persona

Columnas que NO existen en la DB (no incluir en el modelo):
    fecha_hora   -- redundante con fecha, nunca se creo en la DB
    monto        -- el monto vive en tramos.monto_origen
    moneda       -- la moneda vive en tramos.moneda_origen
    id_cuenta    -- la cuenta vive en tramos.id_cuenta_origen
"""

from sqlalchemy import (
    Column, String, Numeric, DateTime, Boolean,
    ForeignKey, Text, Integer
)
from sqlalchemy.orm import relationship
from backend.models.base import Base


class Transaccion(Base):
    __tablename__ = "transacciones"

    id = Column(String, primary_key=True)
    fecha = Column(DateTime(timezone=True), nullable=False)
    tipo = Column(String(20), nullable=False)
    descripcion = Column(Text)
    para_quien = Column(String(20))

    estado = Column(String(20), default="pendiente")
    confianza = Column(Numeric(3, 2), default=0.0)
    revisado_humano = Column(Boolean, default=False)
    completitud = Column(Numeric(3, 2), default=1.0)

    id_categoria = Column(String, ForeignKey("categorias.id"))
    id_categoria2 = Column(String, ForeignKey("categorias.id"))
    id_contraparte = Column(String, ForeignKey("contrapartes.id"))
    quien_pago = Column(String, ForeignKey("personas.id"))
    id_persona = Column(String, ForeignKey("personas.id"))

    es_recurrente = Column(Boolean, default=False)
    id_recurrencia = Column(String)

    es_reembolsable = Column(Boolean, default=False)
    estado_reembolso = Column(String(20))
    id_transaccion_reembolso = Column(String, ForeignKey("transacciones.id"))

    fuente = Column(String(30))
    id_correo = Column(String)
    origen = Column(String(20))

    id_evento = Column(String)
    estado_enriquecimiento = Column(String(20), default="inicial")

    notas = Column(Text)
    fecha_procesado = Column(String)
    creado_en = Column(DateTime(timezone=True))
    actualizado_en = Column(DateTime(timezone=True))

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
