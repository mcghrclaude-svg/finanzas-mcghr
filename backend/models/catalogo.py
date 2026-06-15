"""
Modelos: Categoria, Cuenta, Contraparte, Persona
Datos maestros del sistema.
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

    # Clasificación del patrón de gasto — controla cómo se calcula el riesgo
    # en el dashboard y cómo se proyecta el gasto al cierre del período.
    #
    # fijo_unico       → un solo pago por período (arriendo, cuota préstamo)
    #                    → mostrar badge "vence DD-MMM" en lugar de barra de velocidad
    # fijo_recurrente  → cobro automático mensual (Netflix, Spotify, Claro)
    #                    → esperado en fecha conocida; riesgo bajo si no hay extras
    # variable_frecuente → múltiples gastos distribuidos a lo largo del mes (mercado, Rappi)
    #                    → comparar velocidad diaria vs histórico
    # variable_esporadico → gastos irregulares, pocos por período (salud, viajes)
    #                    → umbral de riesgo más tolerante; no alertar si hay 0 días sin gasto
    tipo_patron_gasto = Column(
        String(30),
        default="variable_frecuente"
        # fijo_unico | fijo_recurrente | variable_frecuente | variable_esporadico
    )


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
