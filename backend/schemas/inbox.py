"""
Pydantic schemas para el modulo Inbox.
completitud es STRING ('minimo'|'parcial'|'completo'), no float.
"""

from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class InboxItemSummary(BaseModel):
    id: str
    origen: Optional[str] = None
    fecha: Optional[str] = None          # TEXT en la DB
    monto: Optional[Decimal] = None
    moneda: str = "COP"
    descripcion: Optional[str] = None
    id_categoria: Optional[str] = None
    nombre_categoria: Optional[str] = None
    id_contraparte: Optional[str] = None
    nombre_contraparte: Optional[str] = None
    confianza: Optional[float] = None
    completitud: Optional[str] = None    # 'minimo' | 'parcial' | 'completo'
    estado: str = "pendiente"
    creado_en: Optional[datetime] = None

    model_config = {"from_attributes": True}


class InboxItemRead(InboxItemSummary):
    tipo: Optional[str] = None
    es_reembolsable: bool = False
    id_persona: Optional[str] = None
    id_correo: Optional[str] = None
    notas: Optional[str] = None
    actualizado_en: Optional[datetime] = None

    model_config = {"from_attributes": True}


class InboxItemPatch(BaseModel):
    fecha: Optional[str] = None
    descripcion: Optional[str] = None
    id_categoria: Optional[str] = None
    id_contraparte: Optional[str] = None
    id_persona: Optional[str] = None
    es_reembolsable: Optional[bool] = None
    notas: Optional[str] = None


class ConfirmarRequest(BaseModel):
    id_categoria: Optional[str] = None
    notas: Optional[str] = None


class ConfirmarResponse(BaseModel):
    ok: bool
    id: str
    regla_creada: bool = False


class ConfirmarLoteRequest(BaseModel):
    ids: list[str] = Field(..., min_length=1, max_length=200)


class ConfirmarLoteResponse(BaseModel):
    confirmados: int
    errores: list[dict] = []


class InboxStatsOut(BaseModel):
    pendientes: int = 0
    alta_prioridad: int = 0
    confirmados_hoy: int = 0


class InboxListResponse(BaseModel):
    items: list[InboxItemSummary]
    next_cursor: Optional[str] = None
    total_pendientes: int = 0
