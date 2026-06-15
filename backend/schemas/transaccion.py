"""
Pydantic schemas para el módulo de transacciones.

Convención de nombres:
    XxxBase     — campos comunes
    XxxCreate   — campos para POST (sin id, sin timestamps)
    XxxUpdate   — campos para PATCH (todos Optional)
    XxxRead     — respuesta completa (con id, timestamps, relaciones)
    XxxSummary  — versión compacta para listas

TODO: implementar validadores y ejemplos completos.
"""

from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional


class TransaccionBase(BaseModel):
    fecha: datetime
    monto: Decimal
    moneda: str = "COP"
    tipo: str  # GASTO | INGRESO | TRANSFERENCIA
    descripcion: Optional[str] = None
    id_categoria: Optional[str] = None
    id_cuenta: Optional[str] = None
    id_contraparte: Optional[str] = None
    id_persona: Optional[str] = None
    es_recurrente: bool = False
    es_reembolsable: bool = False


class TransaccionCreate(TransaccionBase):
    pass


class TransaccionUpdate(BaseModel):
    fecha: Optional[datetime] = None
    monto: Optional[Decimal] = None
    descripcion: Optional[str] = None
    id_categoria: Optional[str] = None
    id_contraparte: Optional[str] = None
    es_reembolsable: Optional[bool] = None
    estado_reembolso: Optional[str] = None


class TransaccionSummary(BaseModel):
    id: str
    fecha: datetime
    monto: Decimal
    moneda: str
    tipo: str
    descripcion: Optional[str]
    nombre_categoria: Optional[str]
    nombre_contraparte: Optional[str]
    estado: str

    model_config = {"from_attributes": True}


class TransaccionRead(TransaccionSummary):
    id_categoria: Optional[str]
    id_cuenta: Optional[str]
    id_contraparte: Optional[str]
    id_persona: Optional[str]
    completitud: Optional[float]
    es_recurrente: bool
    es_reembolsable: bool
    estado_reembolso: Optional[str]
    origen: Optional[str]
    creado_en: Optional[datetime]
    actualizado_en: Optional[datetime]
