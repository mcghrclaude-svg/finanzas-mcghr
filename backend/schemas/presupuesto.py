from pydantic import BaseModel
from decimal import Decimal
from typing import Optional


class PresupuestoBase(BaseModel):
    anio: int
    mes: int
    id_categoria: str
    monto_presupuestado: Decimal
    moneda: str = "COP"


class PresupuestoCreate(PresupuestoBase):
    pass


class PresupuestoUpdate(BaseModel):
    monto_presupuestado: Optional[Decimal] = None


class PresupuestoRead(PresupuestoBase):
    id: str
    nombre_categoria: Optional[str] = None

    model_config = {"from_attributes": True}


class EjecucionCategoria(BaseModel):
    """Presupuesto + ejecución real para una categoría en un mes."""
    id_categoria: str
    nombre_categoria: str
    monto_presupuestado: Decimal
    monto_gastado: Decimal
    monto_proyectado: Decimal  # gasto_a_hoy / dias_transcurridos * dias_mes
    porcentaje_ejecutado: float
    desviacion_porcentaje: float  # positivo = sobre presupuesto
    alerta: bool  # True si proyectado > presupuestado * 1.1
