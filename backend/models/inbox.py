from sqlalchemy import Column, String, Numeric, DateTime, JSON
from backend.models.base import Base


class InboxMobile(Base):
    """
    Transacciones propuestas por el ETL pendientes de confirmación humana.
    Fuentes: correo email, PDF, captura mobile (JSON OneDrive), manual.
    """
    __tablename__ = "inbox_mobile"
    id = Column(String, primary_key=True)
    origen = Column(String)  # email | pdf | mobile | manual
    estado = Column(String, default="pendiente")  # pendiente | confirmado | descartado
    raw_data = Column(JSON)  # datos originales parseados
    # Campos propuestos por el ETL (pueden ser editados por el usuario):
    fecha_propuesta = Column(DateTime(timezone=True))
    monto_propuesto = Column(Numeric(18, 4))
    moneda_propuesta = Column(String(3))
    descripcion_propuesta = Column(String)
    categoria_propuesta = Column(String)
    contraparte_propuesta = Column(String)
    completitud = Column(Numeric(3, 2))  # 0.0 - 1.0
    confianza_clasificacion = Column(Numeric(3, 2))
    creado_en = Column(DateTime(timezone=True))
    procesado_en = Column(DateTime(timezone=True))
