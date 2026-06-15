"""
Modelos: Categoria, Cuenta, Contraparte, Persona
Datos maestros del sistema.
TODO: campos completos según schema v1.1
"""

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from backend.models.base import Base


class Categoria(Base):
    __tablename__ = "categorias"
    id = Column(String, primary_key=True)
    nombre = Column(String, nullable=False)
    nivel = Column(Integer, default=1)
    id_padre = Column(String, ForeignKey("categorias.id"))
    activa = Column(Boolean, default=True)


class Cuenta(Base):
    __tablename__ = "cuentas"
    id = Column(String, primary_key=True)
    nombre = Column(String, nullable=False)
    tipo = Column(String)  # CC | TC | AHORRO | INVERSION
    banco = Column(String)
    moneda = Column(String(3), default="COP")
    es_corporativa = Column(Boolean, default=False)
    activa = Column(Boolean, default=True)


class Contraparte(Base):
    __tablename__ = "contrapartes"
    id = Column(String, primary_key=True)
    nombre = Column(String, nullable=False)
    tipo = Column(String)  # COMERCIO | BANCO | PERSONA | ENTIDAD
    activa = Column(Boolean, default=True)


class Persona(Base):
    __tablename__ = "personas"
    id = Column(String, primary_key=True)
    nombre = Column(String, nullable=False)
    alias = Column(String)  # GHR | MC
    activa = Column(Boolean, default=True)
