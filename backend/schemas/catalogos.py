"""
Schemas Pydantic para catalogos maestros.
Fuente oficial: el router importa estas clases, no las duplica.
Solo ASCII en comentarios.
"""
from pydantic import BaseModel, field_validator
from typing import Optional
import re

ID_RE = re.compile(r"^[A-Z0-9_-]{1,30}$")
MONEDA_CODIGO_RE = re.compile(r"^[A-Z]{3}$")

def validar_id(v: str) -> str:
    if not ID_RE.match(v):
        raise ValueError("ID debe ser mayusculas, sin espacios, max 30 chars")
    return v

def validar_nombre_sin_barra(v: str | None) -> str | None:
    if v and "/" in v:
        raise ValueError("El nombre no puede contener '/'; usa '-' en su lugar")
    return v


# -- Categoria ---------------------------------------------------------

PATRONES_GASTO = {"fijo_unico", "fijo_recurrente", "variable_frecuente", "variable_esporadico"}

class CategoriaBase(BaseModel):
    nombre: str
    nivel: int = 1
    id_padre: Optional[str] = None
    tipo_patron_gasto: str = "variable_frecuente"

    @field_validator("nombre")
    @classmethod
    def nombre_sin_barra(cls, v):
        return validar_nombre_sin_barra(v)

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
    tipo_patron_gasto: Optional[str] = None

    @field_validator("nombre")
    @classmethod
    def nombre_sin_barra(cls, v):
        return validar_nombre_sin_barra(v)

    @field_validator("tipo_patron_gasto")
    @classmethod
    def patron_valido(cls, v):
        if v is not None and v not in PATRONES_GASTO:
            raise ValueError(f"tipo_patron_gasto debe ser uno de: {PATRONES_GASTO}")
        return v


# -- Cuenta --------------------------------------------------------------

class CuentaBase(BaseModel):
    nombre: str
    tipo: Optional[str] = None
    banco: Optional[str] = None
    moneda: str = "COP"
    es_corporativa: bool = False

class CuentaCreate(CuentaBase):
    id: str

    @field_validator("id")
    @classmethod
    def id_valido(cls, v):
        return validar_id(v)

class CuentaUpdate(BaseModel):
    nombre: Optional[str] = None
    tipo: Optional[str] = None
    banco: Optional[str] = None
    moneda: Optional[str] = None
    es_corporativa: Optional[bool] = None


# -- Contraparte -----------------------------------------------------------

class ContraparteBase(BaseModel):
    nombre: str
    tipo: Optional[str] = None

class ContraparteCreate(ContraparteBase):
    id: str

    @field_validator("id")
    @classmethod
    def id_valido(cls, v):
        return validar_id(v)

class ContraparteUpdate(BaseModel):
    nombre: Optional[str] = None
    tipo: Optional[str] = None


# -- Persona -----------------------------------------------------------------

class PersonaBase(BaseModel):
    nombre: str
    alias: Optional[str] = None

class PersonaCreate(PersonaBase):
    id: str

    @field_validator("id")
    @classmethod
    def id_valido(cls, v):
        return validar_id(v)

class PersonaUpdate(BaseModel):
    nombre: Optional[str] = None
    alias: Optional[str] = None


# -- Moneda --------------------------------------------------------------

class MonedaCreate(BaseModel):
    codigo: str
    nombre: str
    simbolo: Optional[str] = None

    @field_validator("codigo")
    @classmethod
    def codigo_valido(cls, v):
        v = v.strip().upper()
        if not MONEDA_CODIGO_RE.match(v):
            raise ValueError("codigo debe ser 3 letras mayusculas (formato ISO 4217, ej: COP, USD)")
        return v

class MonedaUpdate(BaseModel):
    nombre: Optional[str] = None
    simbolo: Optional[str] = None
