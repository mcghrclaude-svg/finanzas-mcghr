"""
Router: /api/v1/inbox
Cola de entrada desde el ETL: transacciones propuestas pendientes de confirmación.

Flujo:
    1. ETL procesa correos / PDFs / JSONs mobile y escribe en `inbox_mobile`
       con estado = 'pendiente' y completitud calculada (0.0 – 1.0)
    2. Esta API expone el inbox para que la web app muestre la cola de revisión
    3. El usuario confirma, edita o descarta cada ítem
    4. Al confirmar, se crea la transacción definitiva en `transacciones`

Nota: las transacciones ya confirmadas por el ETL con alta confianza
(completitud >= 0.85 y regla de clasificación matcheada) se mueven directamente
a `transacciones` y NO pasan por esta cola.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db

router = APIRouter()


@router.get("/")
async def listar_inbox(
    estado: str = Query("pendiente", description="pendiente | confirmado | descartado"),
    origen: str | None = Query(None, description="email | pdf | mobile | manual"),
    cursor: str | None = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista ítems del inbox. Por defecto muestra solo los pendientes.
    Ordena por completitud ASC (los más incompletos primero — requieren más atención).
    """
    return {"items": [], "next_cursor": None}


@router.get("/stats")
async def stats_inbox(db: AsyncSession = Depends(get_db)):
    """
    Contadores rápidos para el badge de notificación del Dashboard.
    Devuelve: total pendientes, pendientes con completitud < 0.5 (alta prioridad).
    """
    return {"pendientes": 0, "alta_prioridad": 0, "confirmados_hoy": 0}


@router.get("/{inbox_id}")
async def detalle_inbox_item(inbox_id: str, db: AsyncSession = Depends(get_db)):
    # TODO: incluir raw_data y sugerencias de clasificación del ETL
    return {}


@router.patch("/{inbox_id}")
async def editar_inbox_item(inbox_id: str, db: AsyncSession = Depends(get_db)):
    """
    Permite editar campos antes de confirmar:
    monto, fecha, categoría, cuenta, contraparte, descripción.
    """
    return {}


@router.post("/{inbox_id}/confirmar")
async def confirmar_inbox_item(
    inbox_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Mueve el ítem de inbox a transacciones confirmadas.
    Si hubo corrección de categoría, genera/actualiza regla de clasificación.
    """
    return {}


@router.post("/{inbox_id}/descartar")
async def descartar_inbox_item(
    inbox_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Marca el ítem como descartado (no es una transacción financiera).
    Ejemplo: correo de confirmación de login, newsletter bancario.
    """
    return {}


@router.post("/confirmar-lote")
async def confirmar_lote(
    db: AsyncSession = Depends(get_db),
):
    """
    Confirma múltiples ítems en una sola operación.
    Body: { ids: [str], ...campos_comunes_opcionales }
    """
    return {"confirmados": 0, "errores": []}
