"""
Pydantic schemas para el modulo Transacciones (alta manual).
completitud es STRING ('minimo'|'parcial'|'completo'), no float (ADR-008).
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field, field_validator

ESTADOS_REEMBOLSO = {"pendiente", "solicitado", "recibido"}


class TransaccionCreate(BaseModel):
    descripcion: str = Field(..., min_length=1)
    monto: float = Field(..., gt=0)
    moneda: str = "COP"
    fecha: str = Field(..., description="YYYY-MM-DD")
    tipo: str = Field(..., description="gasto | ingreso | transferencia | ajuste")
    quien_pago: str = Field(..., description="GHR | MC | Unknown")
    id_cuenta_origen: str = Field(..., description="Cuenta usada para pagar (Paid With)")
    id_contraparte: Optional[str] = None
    id_categoria: Optional[str] = None
    es_recurrente: bool = False
    es_reembolsable: bool = False
    estado_reembolso: Optional[str] = None
    notas: Optional[str] = None

    @field_validator("estado_reembolso")
    @classmethod
    def estado_reembolso_valido(cls, v):
        if v is not None and v not in ESTADOS_REEMBOLSO:
            raise ValueError(f"estado_reembolso debe ser uno de: {ESTADOS_REEMBOLSO}")
        return v


class TransaccionCreateResponse(BaseModel):
    ok: bool = True
    id: str
