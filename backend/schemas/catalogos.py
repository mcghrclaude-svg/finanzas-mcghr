"""
Schemas Pydantic para catalogos maestros.
Alineados con backend/models/catalogo.py exactamente.
Solo ASCII en comentarios.
"""
from pydantic import BaseModel, field_validator
from typing import Optional, Any
import re

ID_RE = re.compile(r"^[A-Z0-9_-]{1,30}$")

def validar_id(v: str) -> str:
    if not ID_RE.match(v):
        raise ValueError("ID debe ser mayusculas, sin espacios, max 30 chars")
    return v


# ── Categoria ─────────────────────────────────────────────────────────────────

PATRONES_GASTO = {"fijo_unico", "fijo_recurrente", "variable_frecuente", "variable_esporadico"}

class CategoriaBase(BaseModel):
    nombre: str
    nivel: int = 1
    id_padre: Optional[str] = None
    activa: bool = True
    tipo_patron_gasto: str = "variable_frecuente"

    @field_validator("nivel")
    @classmethod
    def nivel_valido(cls, v):
        if v not in (1, 2, 3):
            raise ValueError("nivel debe ser 1, 2 o 3")
        return v

    @field_validator("tipo_patron_gasto")
    @classmethod
    def patron_valido(cls, v):
        if v not in PATRONES_GASTO:
            raise ValueError(f"tipo_patron_gasto debe ser uno de: {PATRONES_GASTO}")
        return v

class CategoriaCreate(CategoriaBase):
    id: str

    @field_validator("id")
    @classmethod
    def id_valido(cls, v):
        return validar_id(v)

class CategoriaUpdate(BaseModel):
    nombre: Optional[str] = None
    activa: Optional[bool] = None
    tipo_patron_gasto: Optional[str] = None

# Read usa dict para el arbol (viene de _construir_arbol, no ORM directo)
class CategoriaRead(CategoriaBase):
    id: str
    hijos: list[Any] = []
    model_config = {"from_attributes": True}

class CategoriaFlat(CategoriaBase):
    id: str
    model_config = {"from_attributes": True}


# ── Cuenta ────────────────────────────────────────────────────────────────────

class CuentaBase(BaseModel):
    nombre: str
    tipo: Optional[str] = None
    banco: Optional[str] = None
    moneda: str = "COP"
    es_corporativa: bool = False
    activa: bool = True

class CuentaCreate(CuentaBase):
    id: str

    @field_validator("id")
    @classmethod
    def id_valido(cls, v):
        return validar_id(v)

class CuentaUpdate(BaseModel):
    nombre: Optional[str] = None
    banco: Optional[str] = None
    activa: Optional[bool] = None

class CuentaRead(CuentaBase):
    id: str
    model_config = {"from_attributes": True}


# ── Contraparte ───────────────────────────────────────────────────────────────

class ContraparteBase(BaseModel):
    nombre: str
    tipo: Optional[str] = None
    activa: bool = True

class ContraparteCreate(ContraparteBase):
    id: str

    @field_validator("id")
    @classmethod
    def id_valido(cls, v):
        return validar_id(v)

class ContraparteUpdate(BaseModel):
    nombre: Optional[str] = None
    tipo: Optional[str] = None
    activa: Optional[bool] = None

class ContraparteRead(ContraparteBase):
    id: str
    model_config = {"from_attributes": True}


# ── Persona ───────────────────────────────────────────────────────────────────

class PersonaBase(BaseModel):
    nombre: str
    alias: Optional[str] = None
    activa: bool = True

class PersonaCreate(PersonaBase):
    id: str

    @field_validator("id")
    @classmethod
    def id_valido(cls, v):
        return validar_id(v)

class PersonaUpdate(BaseModel):
    nombre: Optional[str] = None
    alias: Optional[str] = None
    activa: Optional[bool] = None

class PersonaRead(PersonaBase):
    id: str
    model_config = {"from_attributes": True}


# ── Respuesta generica ────────────────────────────────────────────────────────

class MsgResponse(BaseModel):
    ok: bool = True
    msg: str
