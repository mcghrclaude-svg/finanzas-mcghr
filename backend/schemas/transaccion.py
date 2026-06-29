"""
Pydantic schemas para el modulo de transacciones.

Convencion de nombres:
    XxxBase     -- campos comunes
    XxxCreate   -- campos para POST (sin id, sin timestamps)
    XxxUpdate   -- campos para PATCH (todos Optional)
    XxxRead     -- respuesta completa (con id, timestamps, relaciones)
    XxxSummary  -- version compacta para listas

NOTA: monto y moneda NO estan en transacciones -- viven en tramos.monto_origen.
completitud es TEXT: 'minimo' | 'parcial' | 'completo' (ADR-008, nunca float).
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TransaccionBase(BaseModel):
    fecha: str
    tipo: str  # gasto | ingreso | transferencia | ajuste | inversion | devolucion
    descripcion: Optional[str] = None
    id_categoria: Optional[str] = None
    id_categoria2: Optional[str] = None
    id_contraparte: Optional[str] = None
    quien_pago: Optional[str] = None
    para_quien: Optional[str] = None
    id_persona: Optional[str] = None
    es_recurrente: bool = False
    es_reembolsable: bool = False


class TransaccionCreate(TransaccionBase):
    pass


class TransaccionUpdate(BaseModel):
    fecha: Optional[str] = None
    tipo: Optional[str] = None
    descripcion: Optional[str] = None
    id_categoria: Optional[str] = None
    id_categoria2: Optional[str] = None
    id_contraparte: Optional[str] = None
    quien_pago: Optional[str] = None
    para_quien: Optional[str] = None
    id_persona: Optional[str] = None
    es_recurrente: Optional[bool] = None
    es_reembolsable: Optional[bool] = None
    estado_reembolso: Optional[str] = None
    estado: Optional[str] = None
    notas: Optional[str] = None


class TransaccionSummary(BaseModel):
    id: str
    fecha: str
    tipo: str
    descripcion: Optional[str]
    nombre_categoria: Optional[str]
    nombre_contraparte: Optional[str]
    estado: Optional[str]
    completitud: Optional[str]  # 'minimo' | 'parcial' | 'completo' -- nunca float (ADR-008)

    model_config = {"from_attributes": True}


class TransaccionRead(TransaccionSummary):
    fecha_hora: Optional[str]
    id_categoria: Optional[str]
    id_categoria2: Optional[str]
    id_contraparte: Optional[str]
    quien_pago: Optional[str]
    para_quien: Optional[str]
    id_persona: Optional[str]
    es_recurrente: bool
    es_reembolsable: bool
    estado_reembolso: Optional[str]
    fuente: Optional[str]
    origen: Optional[str]       # canal de origen del registro (distinto de fuente)
    id_evento: Optional[str]    # agrupa eventos del mismo hecho economico (ADR-012)
    estado_enriquecimiento: Optional[str]  # 'inicial' | 'enriquecido' | 'completo'
    revisado_humano: Optional[int]
    confianza: Optional[float]
    notas: Optional[str]
    fecha_procesado: Optional[str]
    creado_en: Optional[datetime]
    actualizado_en: Optional[datetime]
