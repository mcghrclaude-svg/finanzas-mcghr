"""
Router: /api/v1/catalogos
ABM de datos maestros: categorías, cuentas, contrapartes, personas, monedas.

Sub-routers montados en main.py bajo /api/v1/catalogos:
    /categorias         Jerarquía hasta 3 niveles
    /cuentas            Productos financieros (CC, TC, inversión, etc.)
    /contrapartes       Comercios, bancos, entidades
    /personas           GHR, MC y otros participantes
    /monedas            COP, USD, ARS, etc.

Regla: nunca borrado físico. Solo inactivación (activa = 0).
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db

router = APIRouter()

# ── Categorías ────────────────────────────────────────────────────────────────

@router.get("/categorias")
async def listar_categorias(
    nivel: int | None = Query(None, description="Filtrar por nivel 1, 2 o 3"),
    solo_activas: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    # TODO: devuelve árbol jerárquico completo
    return {"items": []}


@router.post("/categorias", status_code=201)
async def crear_categoria(db: AsyncSession = Depends(get_db)):
    # TODO: valida que id_padre existe si nivel > 1
    return {}


@router.patch("/categorias/{categoria_id}")
async def editar_categoria(categoria_id: str, db: AsyncSession = Depends(get_db)):
    return {}


@router.delete("/categorias/{categoria_id}", status_code=204)
async def inactivar_categoria(categoria_id: str, db: AsyncSession = Depends(get_db)):
    # TODO: soft delete — verifica que no tenga transacciones activas asociadas
    return None


# ── Cuentas / Productos financieros ──────────────────────────────────────────

@router.get("/cuentas")
async def listar_cuentas(
    titular: str | None = Query(None, description="GHR | MC"),
    solo_activas: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    return {"items": []}


@router.post("/cuentas", status_code=201)
async def crear_cuenta(db: AsyncSession = Depends(get_db)):
    return {}


@router.patch("/cuentas/{cuenta_id}")
async def editar_cuenta(cuenta_id: str, db: AsyncSession = Depends(get_db)):
    return {}


@router.delete("/cuentas/{cuenta_id}", status_code=204)
async def inactivar_cuenta(cuenta_id: str, db: AsyncSession = Depends(get_db)):
    return None


# ── Contrapartes ──────────────────────────────────────────────────────────────

@router.get("/contrapartes")
async def listar_contrapartes(
    tipo: str | None = Query(None),
    solo_activas: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    return {"items": []}


@router.post("/contrapartes", status_code=201)
async def crear_contraparte(db: AsyncSession = Depends(get_db)):
    return {}


@router.patch("/contrapartes/{contraparte_id}")
async def editar_contraparte(contraparte_id: str, db: AsyncSession = Depends(get_db)):
    return {}


@router.delete("/contrapartes/{contraparte_id}", status_code=204)
async def inactivar_contraparte(contraparte_id: str, db: AsyncSession = Depends(get_db)):
    return None


# ── Personas ──────────────────────────────────────────────────────────────────

@router.get("/personas")
async def listar_personas(db: AsyncSession = Depends(get_db)):
    return {"items": []}


@router.post("/personas", status_code=201)
async def crear_persona(db: AsyncSession = Depends(get_db)):
    return {}


@router.patch("/personas/{persona_id}")
async def editar_persona(persona_id: str, db: AsyncSession = Depends(get_db)):
    return {}
