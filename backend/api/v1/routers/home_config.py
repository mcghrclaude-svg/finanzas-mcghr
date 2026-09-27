"""
Router: /api/v1/home-config
Preferencia de que widgets se ven en el Home (banner de insight, Evolucion
patrimonio, Ask Claude). Vive en el backend -- no en localStorage -- para que
sea la misma configuracion sin importar el dispositivo.

La tabla config_home_widgets (fila unica, id=1) no tiene modelo SQLAlchemy --
mismo criterio que config_pwa_import (ver pwa_config.py): es una tabla de
configuracion, se lee/escribe con SQL directo.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db

router = APIRouter()


class HomeWidgetsConfig(BaseModel):
    insight_visible: bool
    patrimonio_visible: bool
    ask_visible: bool


class HomeWidgetsConfigUpdate(BaseModel):
    insight_visible: bool | None = None
    patrimonio_visible: bool | None = None
    ask_visible: bool | None = None


async def _leer(db: AsyncSession) -> dict:
    row = (await db.execute(
        text("SELECT insight_visible, patrimonio_visible, ask_visible FROM config_home_widgets WHERE id = 1")
    )).mappings().first()
    if row is None:
        raise HTTPException(status_code=500, detail="config_home_widgets sin fila inicial -- revisar migracion v1.8")
    return {
        "insight_visible": bool(row["insight_visible"]),
        "patrimonio_visible": bool(row["patrimonio_visible"]),
        "ask_visible": bool(row["ask_visible"]),
    }


@router.get("", response_model=HomeWidgetsConfig)
async def obtener_config(db: AsyncSession = Depends(get_db)):
    return await _leer(db)


@router.patch("", response_model=HomeWidgetsConfig)
async def actualizar_config(body: HomeWidgetsConfigUpdate, db: AsyncSession = Depends(get_db)):
    campos = body.model_dump(exclude_none=True)
    if campos:
        set_clause = ", ".join(f"{k} = :{k}" for k in campos)
        await db.execute(
            text(f"UPDATE config_home_widgets SET {set_clause} WHERE id = 1"),
            campos,
        )
        await db.commit()
    return await _leer(db)
