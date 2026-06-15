from sqlalchemy import Column, String, DateTime, Boolean
from backend.models.base import Base


class Documento(Base):
    __tablename__ = "documentos"
    id = Column(String, primary_key=True)
    nombre_archivo = Column(String, nullable=False)
    ruta = Column(String, nullable=False)
    tipo_mime = Column(String)
    hash_sha256 = Column(String)
    estado = Column(String, default="stage")  # stage | clasificado
    origen_dispositivo = Column(String)  # PC | iPhone_GHR | iPhone_MC
    procesado = Column(Boolean, default=False)
    creado_en = Column(DateTime(timezone=True))
