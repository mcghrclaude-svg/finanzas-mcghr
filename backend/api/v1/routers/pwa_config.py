"""
Router: /api/v1/pwa-config
Configuracion de la importacion automatica de gastos de la PWA mobile:
intervalo, raices de OneDrive (una por persona -- la propia, la de Martha
como carpeta compartida, etc.), y control de la Tarea Programada de Windows
que corre scripts/import_pwa_gastos.py. Cada raiz implica pendientes/,
procesados/, Catalogos/ y Resumen/ debajo -- no son campos separados
(ver ADR-018).

La tabla config_pwa_import (fila unica id=1) y log_ejecuciones_mobile no
tienen modelo SQLAlchemy -- mismo criterio que log_ejecuciones/tools.py:
son tablas de configuracion/auditoria del ETL, se leen con SQL directo.
"""

from __future__ import annotations

import asyncio
import json
import string
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.database import get_db
from backend.services import scheduled_task_service as sched

router = APIRouter()


class PwaConfigUpdate(BaseModel):
    intervalo_minutos: int
    raices: list[str]


class ToggleRequest(BaseModel):
    habilitado: bool


async def _leer_config(db: AsyncSession) -> dict:
    row = (await db.execute(
        text("SELECT * FROM config_pwa_import WHERE id = 1")
    )).mappings().first()
    if row is None:
        raise HTTPException(status_code=500, detail="config_pwa_import sin fila inicial -- revisar migracion v1.5")
    data = dict(row)
    data["raices"] = json.loads(data["raices"] or "[]")
    return data


@router.get("")
async def obtener_config(db: AsyncSession = Depends(get_db)):
    config = await _leer_config(db)
    estado = await asyncio.to_thread(sched.consultar_estado)
    return {
        **config,
        "tarea_existe": estado.existe,
        "tarea_habilitada": estado.habilitada,
        "proxima_ejecucion": estado.proxima_ejecucion,
        "ultimo_resultado_tarea": estado.ultimo_resultado,
    }


@router.put("")
async def actualizar_config(body: PwaConfigUpdate, db: AsyncSession = Depends(get_db)):
    estado_previo = await asyncio.to_thread(sched.consultar_estado)

    await db.execute(
        text("""
            UPDATE config_pwa_import
            SET intervalo_minutos = :intervalo,
                raices = :raices,
                actualizado_en = datetime('now')
            WHERE id = 1
        """),
        {
            "intervalo": body.intervalo_minutos,
            "raices": json.dumps(body.raices),
        },
    )
    await db.commit()

    # Cada raiz es padre de pendientes/ y procesados/ (import_pwa_gastos.py)
    # y de Catalogos/ (pwa_export_service.py) -- se crean eagerly aca para
    # que la primera corrida de la tarea programada no tire el alerta
    # "Carpeta pendientes/ no encontrada" sobre una raiz recien elegida.
    for raiz in body.raices:
        for subcarpeta in ("pendientes", "procesados", "Catalogos", "Resumen"):
            (Path(raiz) / subcarpeta).mkdir(parents=True, exist_ok=True)

    # Si ya existia una tarea, se recrea con la config nueva (schtasks no
    # permite cambiar comando/intervalo con /Change) preservando si estaba
    # pausada.
    if estado_previo.existe:
        await asyncio.to_thread(
            sched.crear_o_actualizar, body.intervalo_minutos, settings.env, body.raices
        )
        if not estado_previo.habilitada:
            await asyncio.to_thread(sched.pausar)

    return await obtener_config(db)


@router.post("/toggle")
async def toggle_tarea(body: ToggleRequest, db: AsyncSession = Depends(get_db)):
    estado = await asyncio.to_thread(sched.consultar_estado)

    if body.habilitado:
        if not estado.existe:
            config = await _leer_config(db)
            if not config["raices"]:
                raise HTTPException(status_code=422, detail="Configura al menos una carpeta raiz antes de activar")
            await asyncio.to_thread(
                sched.crear_o_actualizar, config["intervalo_minutos"], settings.env, config["raices"]
            )
        else:
            await asyncio.to_thread(sched.reanudar)
    else:
        if estado.existe:
            await asyncio.to_thread(sched.pausar)

    nuevo_estado = await asyncio.to_thread(sched.consultar_estado)
    return {"ok": True, "tarea_habilitada": nuevo_estado.habilitada}


@router.get("/browse-folders")
async def browse_folders(path: str = Query("")):
    """
    Navega el filesystem local (carpetas de OneDrive sincronizadas en esta
    PC -- sin Graph API, sin login). Sin sandboxing a una carpeta base
    (app de escritorio de un solo usuario).

    path vacio -> lista de unidades de disco.
    path con valor -> subcarpetas inmediatas de esa ruta.
    """
    path = (path or "").strip()

    if not path:
        unidades = [
            {"nombre": str(Path(f"{letra}:\\")), "ruta": str(Path(f"{letra}:\\"))}
            for letra in string.ascii_uppercase
            if Path(f"{letra}:\\").exists()
        ]
        return {"path": None, "items": unidades}

    try:
        base = Path(path).resolve()
    except (OSError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Ruta invalida: {e}")

    if not base.is_dir():
        raise HTTPException(status_code=400, detail=f"No es una carpeta: {base}")

    try:
        entradas = sorted(base.iterdir(), key=lambda p: p.name.lower())
    except PermissionError:
        raise HTTPException(status_code=400, detail=f"Sin permiso para leer: {base}")
    except OSError as e:
        raise HTTPException(status_code=400, detail=f"No se pudo leer la carpeta: {e}")

    items = []
    for entrada in entradas:
        try:
            if entrada.is_dir():
                items.append({"nombre": entrada.name, "ruta": str(entrada)})
        except (PermissionError, OSError):
            # Un item puntual restringido (ej. "System Volume Information")
            # no tumba el listado completo -- se salta.
            continue

    return {"path": str(base), "items": items}


@router.get("/historial")
async def historial(limit: int = Query(20, le=100), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        text("SELECT * FROM log_ejecuciones_mobile ORDER BY fecha_inicio DESC LIMIT :limit"),
        {"limit": limit},
    )).mappings().all()
    items = []
    for r in rows:
        row = dict(r)
        try:
            row["alertas"] = json.loads(row.get("alertas") or "{}")
        except (json.JSONDecodeError, TypeError):
            row["alertas"] = {}
        items.append(row)
    return {"items": items}
