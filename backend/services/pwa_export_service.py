"""
pwa_export_service -- genera catalogos.json para la PWA mobile.

Contrato esperado por la PWA (pwa-gastos/src/api/catalogos.js):
    { categorias: [...], medios_de_pago: [...], monedas: [...] }
Cada item tiene forma {id, etiqueta}.

Se llama desde el endpoint POST /catalogos/export/pwa y, automaticamente,
despues de cada alta/edicion/inactivacion de categoria, cuenta o moneda.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.models.catalogo import Categoria, Cuenta, Moneda


async def exportar_catalogos_pwa(db: AsyncSession) -> dict:
    cats_result = await db.execute(
        select(Categoria)
        .where(Categoria.activa == True)  # noqa: E712
        .order_by(Categoria.nivel, Categoria.nombre)
    )
    cats = cats_result.scalars().all()

    cuentas_result = await db.execute(
        select(Cuenta)
        .where(Cuenta.activa == True)  # noqa: E712
        .order_by(Cuenta.nombre)
    )
    cuentas = cuentas_result.scalars().all()

    monedas_result = await db.execute(
        select(Moneda)
        .where(Moneda.activa == True)  # noqa: E712
        .order_by(Moneda.codigo)
    )
    monedas = monedas_result.scalars().all()

    payload = {
        "version": "1.0",
        "generado_en": datetime.now(timezone.utc).isoformat(),
        "categorias": [
            {
                "id": c.id,
                "etiqueta": c.nombre,
                "nivel": c.nivel,
                "id_padre": c.id_padre,
                "tipo_patron_gasto": c.tipo_patron_gasto,
            }
            for c in cats
        ],
        "medios_de_pago": [
            {"id": c.id, "etiqueta": c.nombre}
            for c in cuentas
        ],
        "monedas": [
            {"id": m.codigo, "etiqueta": f"{m.codigo} - {m.nombre}"}
            for m in monedas
        ],
    }

    onedrive = Path(settings.onedrive_path)
    pwa_dir = onedrive / "PWA"
    try:
        pwa_dir.mkdir(parents=True, exist_ok=True)
        ruta_json = pwa_dir / "catalogos.json"
        ruta_json.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"No se pudo escribir el archivo en OneDrive: {e}",
        )

    return {
        "ok": True,
        "ruta_archivo": str(ruta_json),
        "generado_en": payload["generado_en"],
        "categorias": len(cats),
        "medios_de_pago": len(cuentas),
        "monedas": len(monedas),
    }
