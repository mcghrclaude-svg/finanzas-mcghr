from sqlalchemy import Column, Integer, String, Float, ForeignKey
from backend.models.base import Base


class Vinculo(Base):
    __tablename__ = "vinculos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_documento = Column(String, ForeignKey("documentos.id"), nullable=False)
    id_transaccion = Column(String, ForeignKey("transacciones.id"), nullable=False)
    tipo_vinculo = Column(String, nullable=False)   # factura | extracto
    confianza = Column(Float)
    fecha_vinculo = Column(String, nullable=False)
    creado_por = Column(String, nullable=False, default="claude")
