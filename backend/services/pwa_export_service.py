"""
pwa_export_service -- genera catalogos.json y resumen_categorias.json para
la PWA mobile.

Contrato de catalogos.json esperado por la PWA (pwa-gastos/src/api/catalogos.js):
    { categorias: [...], medios_de_pago: [...], monedas: [...] }
Cada item tiene forma {id, etiqueta}.

Se llama desde el endpoint POST /catalogos/export/pwa y, automaticamente,
despues de cada alta/edicion/inactivacion de categoria, cuenta o moneda.

NOTA -- cambio de contrato pendiente de documentar en ADR-016:
medios_de_pago ahora excluye cuentas con visible_pwa=False y cada item
suma el campo "propietario" (GHR | MC | Ambos) ademas de {id, etiqueta}.
Pendiente: actualizar la entrada de ADR-016 en la proxima sesion de
consolidacion de docs.

resumen_categorias.json (Bloque 4, Home de la PWA) sigue el mismo criterio
de raices/fallback que catalogos.json (ver _resolver_raices), pero en la
subcarpeta Resumen/ en vez de Catalogos/. La PWA no llama al backend por
HTTP directo -- ver docs/architecture.md ("Flujo mobile via JSON en
OneDrive" en vez de "API REST directa al backend", decision de Jun 2026)
-- asi que el resumen de presupuesto por categoria se exporta a este
archivo, offline-first, igual que categorias/monedas/medios de pago.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.models.catalogo import Categoria, Cuenta, Moneda
from backend.services.presupuesto_service import PresupuestoService


async def _resolver_raices(db: AsyncSession, subcarpeta: str) -> list[Path]:
    """Lee config_pwa_import.raices (una carpeta de OneDrive por persona) y
    devuelve la subcarpeta pedida bajo cada una. Si no hay ninguna raiz
    configurada, cae al default historico onedrive_path/<subcarpeta> para
    no romper instalaciones sin configurar."""
    raices_json = (await db.execute(
        text("SELECT raices FROM config_pwa_import WHERE id = 1")
    )).scalar_one_or_none()
    raices = json.loads(raices_json) if raices_json else []
    if not raices:
        raices = [str(Path(settings.onedrive_path))]
    return [Path(raiz) / subcarpeta for raiz in raices]


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

    # El JSON se escribe en cada raiz, no en un unico lugar -- si solo se
    # escribiera en una, cualquier celular que lea desde otra raiz nunca
    # veria catalogos actualizados (bug real que motivo este diseno, ver
    # ADR-018).
    catalogos_dirs = await _resolver_raices(db, "Catalogos")

    contenido = json.dumps(payload, ensure_ascii=False, indent=2)
    rutas_archivo: list[str] = []
    try:
        for catalogos_dir in catalogos_dirs:
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


async def exportar_resumen_categorias_pwa(db: AsyncSession) -> dict:
    """Genera resumen_categorias.json (gasto acumulado / presupuesto /
    promedio ultimos 3 meses por categoria, mes calendario actual) para el
    Home de la PWA. Mismo criterio de raices que catalogos.json, pero bajo
    la subcarpeta Resumen/ de cada una."""
    hoy = date.today()
    payload = await PresupuestoService(db).obtener_resumen_por_categoria(hoy.year, hoy.month)
    payload["generado_en"] = datetime.now(timezone.utc).isoformat()

    resumen_dirs = await _resolver_raices(db, "Resumen")

    contenido = json.dumps(payload, ensure_ascii=False, indent=2)
    rutas_archivo: list[str] = []
    for resumen_dir in resumen_dirs:
        resumen_dir.mkdir(parents=True, exist_ok=True)
        ruta_json = resumen_dir / "resumen_categorias.json"
        ruta_json.write_text(contenido, encoding="utf-8")
        rutas_archivo.append(str(ruta_json))

    return {
        "ok": True,
        "rutas_archivo": rutas_archivo,
        "generado_en": payload["generado_en"],
        "categorias": len(payload["categorias"]),
    }
