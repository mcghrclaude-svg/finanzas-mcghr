"""
Pydantic schemas para el modulo Inbox.
completitud es STRING ('minimo'|'parcial'|'completo'), no float.
"""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class TramoOut(BaseModel):
    id: int
    numero_orden: int
    id_cuenta_origen: Optional[str] = None
    nombre_cuenta_origen: Optional[str] = None
    id_cuenta_destino: Optional[str] = None
    nombre_cuenta_destino: Optional[str] = None
    monto_origen: Optional[float] = None
    moneda_origen: Optional[str] = None
    monto_destino: Optional[float] = None
    moneda_destino: Optional[str] = None
    model_config = {"from_attributes": True}


class InboxItemSummary(BaseModel):
    id: str
    origen: Optional[str] = None
    fecha: Optional[str] = None
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
    quien_pago: Optional[str] = None
    para_quien: Optional[str] = None
    es_recurrente: bool = False
    es_reembolsable: bool = False
    estado_reembolso: Optional[str] = None
    id_persona: Optional[str] = None
    id_correo: Optional[str] = None
    notas: Optional[str] = None
    tramos: list[TramoOut] = []
    actualizado_en: Optional[datetime] = None
    model_config = {"from_attributes": True}


class InboxItemPatch(BaseModel):
    # Campos de la transaccion
    fecha: Optional[str] = None
    descripcion: Optional[str] = None
    id_categoria: Optional[str] = None
    id_contraparte: Optional[str] = None
    id_persona: Optional[str] = None
    es_reembolsable: Optional[bool] = None
    notas: Optional[str] = None
    tipo: Optional[str] = None
    quien_pago: Optional[str] = None
    para_quien: Optional[str] = None
    es_recurrente: Optional[bool] = None
    estado_reembolso: Optional[str] = None
    id_correo: Optional[str] = None
    # Cuenta del primer tramo (solo para transacciones de un solo tramo)
    id_cuenta_origen_tramo1: Optional[str] = None


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
