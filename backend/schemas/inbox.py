"""
Pydantic schemas para el modulo Inbox.

InboxItemSummary  -- version compacta para lista
InboxItemRead     -- detalle completo
InboxItemPatch    -- campos editables (todos Optional)
ConfirmarRequest  -- body de POST /confirmar
ConfirmarLoteRequest -- body de POST /confirmar-lote
InboxStatsOut     -- respuesta de GET /stats
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Sub-schemas reutilizables
# ---------------------------------------------------------------------------

class CategoriaRef(BaseModel):
    id: str
    nombre: str

    model_config = {"from_attributes": True}


class ContraparteRef(BaseModel):
    id: str
    nombre: str

    model_config = {"from_attributes": True}


class CuentaRef(BaseModel):
    id: str
    nombre: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Item del inbox — version lista
# ---------------------------------------------------------------------------

class InboxItemSummary(BaseModel):
    id: str
    origen: Optional[str] = None          # email | pdf | mobile | manual
    fecha: Optional[datetime] = None
    monto: Optional[Decimal] = None
    moneda: str = "COP"
    descripcion: Optional[str] = None
    id_categoria: Optional[str] = None
    nombre_categoria: Optional[str] = None
    id_contraparte: Optional[str] = None
    nombre_contraparte: Optional[str] = None
    id_cuenta: Optional[str] = None
    nombre_cuenta: Optional[str] = None
    confianza: Optional[float] = None
    completitud: Optional[float] = None
    estado_enriquecimiento: Optional[str] = None
    estado: str = "pendiente"
    creado_en: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Item del inbox — detalle completo
# ---------------------------------------------------------------------------

class InboxItemRead(InboxItemSummary):
    tipo: Optional[str] = None            # gasto | ingreso | transferencia
    es_reembolsable: bool = False
    id_persona: Optional[str] = None
    fuente_raw: Optional[str] = None      # texto crudo del correo/pdf parseado
    id_correo: Optional[str] = None       # ID del correo Gmail fuente
    notas: Optional[str] = None
    actualizado_en: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# PATCH — editar campos antes de confirmar
# ---------------------------------------------------------------------------

class InboxItemPatch(BaseModel):
    fecha: Optional[datetime] = None
    monto: Optional[Decimal] = None
    moneda: Optional[str] = None
    descripcion: Optional[str] = None
    id_categoria: Optional[str] = None
    id_cuenta: Optional[str] = None
    id_contraparte: Optional[str] = None
    id_persona: Optional[str] = None
    es_reembolsable: Optional[bool] = None
    notas: Optional[str] = None


# ---------------------------------------------------------------------------
# POST /confirmar
# ---------------------------------------------------------------------------

class ConfirmarRequest(BaseModel):
    id_categoria: Optional[str] = Field(
        None,
        description="Si difiere de la categoria propuesta, crea regla de aprendizaje"
    )
    notas: Optional[str] = None


class ConfirmarResponse(BaseModel):
    ok: bool
    id: str
    regla_creada: bool = False


# ---------------------------------------------------------------------------
# POST /confirmar-lote
# ---------------------------------------------------------------------------

class ConfirmarLoteRequest(BaseModel):
    ids: list[str] = Field(..., min_length=1, max_length=200)


class ConfirmarLoteResponse(BaseModel):
    confirmados: int
    errores: list[dict] = []


# ---------------------------------------------------------------------------
# GET /stats
# ---------------------------------------------------------------------------

class InboxStatsOut(BaseModel):
    pendientes: int = 0
    alta_prioridad: int = 0    # confianza < 0.60
    confirmados_hoy: int = 0


# ---------------------------------------------------------------------------
# Respuesta de lista paginada
# ---------------------------------------------------------------------------

class InboxListResponse(BaseModel):
    items: list[InboxItemSummary]
    next_cursor: Optional[str] = None
    total_pendientes: int = 0
