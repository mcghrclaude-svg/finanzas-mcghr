"""
Modelos: Transaccion, Tramo, Asiento

Mapean las tablas del schema v1.1 + preparados para v1.2.
Los campos id_evento y estado_enriquecimiento se agregan via
migracion SQL en schema/finanzas_v1_2.sql (Entrega 3B).
"""

from sqlalchemy import Column, String, Numeric, DateTime, Boolean, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship
from backend.models.base import Base


class Transaccion(Base):
    __tablename__ = "transacciones"

    id = Column(String, primary_key=True)

    # Datos del evento
    fecha = Column(DateTime(timezone=True), nullable=False)
    fecha_hora = Column(String)                         # ISO 8601 con offset
    tipo = Column(String(20), nullable=False)           # gasto | ingreso | transferencia | ajuste
    descripcion = Column(Text)
    para_quien = Column(String(20))                     # GHR | MC | ambos

    # Estado
    estado = Column(String(20), default="pendiente")    # confirmado | pendiente | anulado
    confianza = Column(Numeric(3, 2), default=0.0)      # 0.0 - 1.0
    revisado_humano = Column(Boolean, default=False)
    completitud = Column(Numeric(3, 2), default=1.0)    # 0.0 - 1.0

    # Catalogos
    id_categoria = Column(String, ForeignKey("categorias.id"))
    id_categoria2 = Column(String, ForeignKey("categorias.id"))
    id_contraparte = Column(String, ForeignKey("contrapartes.id"))
    id_persona = Column(String, ForeignKey("personas.id"))
    quien_pago = Column(String, ForeignKey("personas.id"))

    # Flags
    es_recurrente = Column(Boolean, default=False)
    id_recurrencia = Column(String)
    es_reembolsable = Column(Boolean, default=False)
    estado_reembolso = Column(String(20))               # pendiente | gestionado | reembolsado
    id_transaccion_reembolso = Column(String, ForeignKey("transacciones.id"))

    # Fuente
    fuente = Column(String(30))                         # gmail_hernan | sms_bc | manual | foto_factura
    id_correo = Column(String)
    origen = Column(String(20))                         # email | pdf | mobile | manual

    # Correlacion ETL (schema v1.2 — columnas agregadas via ALTER TABLE)
    # id_evento y estado_enriquecimiento se usan via texto directo en queries
    # hasta que se aplique finanzas_v1_2.sql

    # Notas y auditoria
    notas = Column(Text)
    fecha_procesado = Column(String)                    # ISO 8601 con offset
    creado_en = Column(DateTime(timezone=True))
    actualizado_en = Column(DateTime(timezone=True))

    # Relaciones
    tramos = relationship("Tramo", back_populates="transaccion",
                          foreign_keys="Tramo.id_transaccion")
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
    fecha_tramo = Column(String)                        # ISO 8601 con offset
    descripcion = Column(Text)
    estado = Column(String(20), default="confirmado")   # confirmado | pendiente | rechazado

    transaccion = relationship("Transaccion", back_populates="tramos",
                               foreign_keys=[id_transaccion])
    cuenta_origen = relationship("Cuenta", foreign_keys=[id_cuenta_origen])
    cuenta_destino = relationship("Cuenta", foreign_keys=[id_cuenta_destino])


class Asiento(Base):
    __tablename__ = "asientos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_tramo = Column(Integer, ForeignKey("tramos.id"))
    id_transaccion = Column(String, ForeignKey("transacciones.id"))
    id_cuenta = Column(String, ForeignKey("cuentas.id"))
    tipo = Column(String(10))                           # debito | credito
    monto = Column(Numeric(18, 4))
    moneda = Column(String(3), default="COP")
    fecha = Column(String)                              # ISO 8601 con offset

    transaccion = relationship("Transaccion", back_populates="asientos")
