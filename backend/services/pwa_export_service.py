"""
pwa_export_service -- genera catalogos.json para la PWA mobile.

Contrato esperado por la PWA (pwa-gastos/src/api/catalogos.js):
    { categorias: [...], medios_de_pago: [...], monedas: [...] }
Cada item tiene forma {id, etiqueta}.

Se llama desde el endpoint POST /catalogos/export/pwa y, automaticamente,
despues de cada alta/edicion/inactivacion de categoria, cuenta o moneda.

NOTA -- cambio de contrato pendiente de documentar en ADR-016:
medios_de_pago ahora excluye cuentas con visible_pwa=False y cada item
suma el campo "propietario" (GHR | MC | Ambos) ademas de {id, etiqueta}.
Pendiente: actualizar la entrada de ADR-016 en la proxima sesion de
consolidacion de docs.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select, text
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
        .where(Cuenta.activa == True, Cuenta.visible_pwa == True)  # noqa: E712
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
            {"id": c.id, "etiqueta": c.nombre, "propietario": c.propietario}
            for c in cuentas
        ],
        "monedas": [
            {"id": m.codigo, "etiqueta": f"{m.codigo} - {m.nombre}"}
            for m in monedas
        ],
    }

    # Las raices se leen de la config guardada en la pantalla PWA
    # (config_pwa_import.raices) -- una carpeta de OneDrive por persona
    # (la propia, la de Martha como carpeta compartida, etc.). El JSON se
    # escribe en cada raiz, no en un unico lugar -- si solo se escribiera
    # en una, cualquier celular que lea desde otra raiz nunca veria
    # catalogos actualizados (bug real que motivo este diseno, ver ADR-018).
    # Si todavia no se configuro ninguna raiz, se cae al default historico
    # (onedrive_path/Catalogos) para no romper instalaciones sin configurar.
    raices_json = (await db.execute(
        text("SELECT raices FROM config_pwa_import WHERE id = 1")
    )).scalar_one_or_none()
    raices = json.loads(raices_json) if raices_json else []
    if not raices:
        raices = [str(Path(settings.onedrive_path))]

    contenido = json.dumps(payload, ensure_ascii=False, indent=2)
    rutas_archivo: list[str] = []
    try:
        for raiz in raices:
            catalogos_dir = Path(raiz) / "Catalogos"
            catalogos_dir.mkdir(parents=True, exist_ok=True)
            ruta_json = catalogos_dir / "catalogos.json"
            ruta_json.write_text(contenido, encoding="utf-8")
            rutas_archivo.append(str(ruta_json))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"No se pudo escribir el archivo en OneDrive: {e}",
        )

    return {
        "ok": True,
        "rutas_archivo": rutas_archivo,
        "generado_en": payload["generado_en"],
        "categorias": len(cats),
        "medios_de_pago": len(cuentas),
        "monedas": len(monedas),
    }
