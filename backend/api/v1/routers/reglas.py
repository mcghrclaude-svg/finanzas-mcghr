"""
Router: /api/v1/reglas
Gestión del motor de aprendizaje por confirmación humana.

Cómo funciona:
    Cuando el usuario confirma una transacción y cambia la categoría sugerida
    por el ETL, el sistema registra una regla de clasificación:
        patron (regex) → categoria_id, contraparte_id, tipo
    
    Las reglas se aplican en orden de prioridad (mayor peso primero).
    Las reglas del usuario siempre tienen prioridad sobre las reglas base.

Ejemplos de patrones:
    "NETFLIX.*"        → Entretenimiento / Suscripciones
    "BANCOLOMBIA TC"   → Transferencia bancaria (ignorar)
    "RAPPI.*"         → Alimentación / Domicilios
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db

router = APIRouter()


@router.get("/")
async def listar_reglas(
    activas: bool = Query(True),
    fuente: str | None = Query(None, description="usuario | sistema"),
    db: AsyncSession = Depends(get_db),
):
    """
    Devuelve reglas ordenadas por peso DESC.
    Las reglas 'sistema' son las sembradas en seed_catalogos.py.
    Las reglas 'usuario' se crean al confirmar transacciones con corrección.
    """
    return {"items": []}


@router.post("/", status_code=201)
async def crear_regla_manual(db: AsyncSession = Depends(get_db)):
    """
    Permite al usuario definir una regla explícitamente (sin pasar por confirmación).
    """
    return {}


@router.get("/{regla_id}")
async def detalle_regla(regla_id: str, db: AsyncSession = Depends(get_db)):
    return {}


@router.patch("/{regla_id}")
async def editar_regla(regla_id: str, db: AsyncSession = Depends(get_db)):
    # TODO: permite cambiar patron, categoria, peso o desactivar
    return {}


@router.delete("/{regla_id}", status_code=204)
async def eliminar_regla(regla_id: str, db: AsyncSession = Depends(get_db)):
    # TODO: solo reglas de fuente 'usuario'; las de 'sistema' no se borran
    return None


@router.post("/test")
async def probar_patron(db: AsyncSession = Depends(get_db)):
    """
    Prueba un patrón regex contra el historial de transacciones.
    Body: { patron: str }
    Devuelve ejemplos de transacciones que matchearían.
    Útil para validar una regla antes de guardarla.
    """
    return {"matches": [], "total": 0}
