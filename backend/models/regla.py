from sqlalchemy import Column, String, Numeric, Boolean, DateTime
from backend.models.base import Base


class ReglaClasificacion(Base):
    __tablename__ = "reglas_clasificacion"
    id = Column(String, primary_key=True)
    patron = Column(String, nullable=False)  # regex
    id_categoria = Column(String)
    id_contraparte = Column(String)
    tipo_transaccion = Column(String)
    peso = Column(Numeric(5, 2), default=1.0)  # mayor peso = mayor prioridad
    fuente = Column(String, default="usuario")  # usuario | sistema
    activa = Column(Boolean, default=True)
    creado_en = Column(DateTime(timezone=True))
    ultima_coincidencia = Column(DateTime(timezone=True))
    total_coincidencias = Column(Numeric, default=0)
