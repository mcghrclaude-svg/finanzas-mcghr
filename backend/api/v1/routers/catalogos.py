"""
Router: /api/v1/catalogos
ABM de datos maestros: categorias, cuentas, contrapartes, personas.
+ Endpoint de exportacion de catalogos para la PWA mobile.

Sub-routers:
    GET /categorias             Lista jerarquica
    POST /categorias            Crear
    PATCH /categorias/{id}      Editar
    DELETE /categorias/{id}     Inactivar (soft delete)
    (idem para cuentas, contrapartes, personas)

    POST /export/pwa            Genera catalogos.json en OneDrive para la PWA

Regla: nunca borrado fisico. Solo inactivacion (activa = 0).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.config import settings
from backend.models.catalogo import Categoria, Cuenta, Contraparte, Persona

router = APIRouter()


# ── Categorias ────────────────────────────────────────────────────────────────

@router.get("/categorias")
async def listar_categorias(
    nivel: int | None = Query(None, description="1 | 2 | 3"),
    solo_activas: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    """Devuelve lista plana de categorias. El frontend arma el arbol."""
    q = select(Categoria)
    if solo_activas:
        q = q.where(Categoria.activa == True)  # noqa: E712
    if nivel is not None:
        q = q.where(Categoria.nivel == nivel)
    q = q.order_by(Categoria.nivel, Categoria.nombre)
    result = await db.execute(q)
    cats = result.scalars().all()
    return {
        "items": [
            {
                "id": c.id,
                "nombre": c.nombre,
                "nivel": c.nivel,
                "id_padre": c.id_padre,
                "tipo_patron_gasto": c.tipo_patron_gasto,
                "activa": c.activa,
            }
            for c in cats
        ]
    }


@router.post("/categorias", status_code=201)
async def crear_categoria(db: AsyncSession = Depends(get_db)):
    # TODO: implementar con schema Pydantic
    return {}


@router.patch("/categorias/{categoria_id}")
async def editar_categoria(categoria_id: str, db: AsyncSession = Depends(get_db)):
    # TODO: implementar
    return {}


@router.delete("/categorias/{categoria_id}", status_code=204)
async def inactivar_categoria(categoria_id: str, db: AsyncSession = Depends(get_db)):
    # TODO: soft delete
    return None


# ── Cuentas ───────────────────────────────────────────────────────────────────

@router.get("/cuentas")
async def listar_cuentas(
    titular: str | None = Query(None, description="GHR | MC"),
    solo_activas: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    q = select(Cuenta)
    if solo_activas:
        q = q.where(Cuenta.activa == True)  # noqa: E712
    q = q.order_by(Cuenta.nombre)
    result = await db.execute(q)
    cuentas = result.scalars().all()
    return {
        "items": [
            {
                "id": c.id,
                "nombre": c.nombre,
                "tipo": c.tipo,
                "banco": c.banco,
                "moneda": c.moneda,
                "es_corporativa": c.es_corporativa,
                "activa": c.activa,
            }
            for c in cuentas
        ]
    }


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
    q = select(Contraparte)
    if solo_activas:
        q = q.where(Contraparte.activa == True)  # noqa: E712
    if tipo:
        q = q.where(Contraparte.tipo == tipo)
    q = q.order_by(Contraparte.nombre)
    result = await db.execute(q)
    cps = result.scalars().all()
    return {
        "items": [
            {"id": c.id, "nombre": c.nombre, "tipo": c.tipo, "activa": c.activa}
            for c in cps
        ]
    }


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
    q = select(Persona).where(Persona.activa == True).order_by(Persona.nombre)  # noqa: E712
    result = await db.execute(q)
    personas = result.scalars().all()
    return {
        "items": [
            {"id": p.id, "nombre": p.nombre, "alias": p.alias, "activa": p.activa}
            for p in personas
        ]
    }


@router.post("/personas", status_code=201)
async def crear_persona(db: AsyncSession = Depends(get_db)):
    return {}


@router.patch("/personas/{persona_id}")
async def editar_persona(persona_id: str, db: AsyncSession = Depends(get_db)):
    return {}


# ── Export PWA ────────────────────────────────────────────────────────────────

@router.post("/export/pwa")
async def exportar_catalogos_pwa(db: AsyncSession = Depends(get_db)):
    """
    Genera catalogos.json con categorias, contrapartes y cuentas activas.
    Lo escribe en OneDrive/PWA/ para que la app mobile lo lea.

    Llamar cada vez que se modifica el catalogo, o manualmente desde
    la pantalla de Catalogos con el boton "Actualizar datos del celular".
    """
    # Leer datos
    cats_result = await db.execute(
        select(Categoria)
        .where(Categoria.activa == True)  # noqa: E712
        .order_by(Categoria.nivel, Categoria.nombre)
    )
    cats = cats_result.scalars().all()

    cps_result = await db.execute(
        select(Contraparte)
        .where(Contraparte.activa == True)  # noqa: E712
        .order_by(Contraparte.nombre)
    )
    cps = cps_result.scalars().all()

    cuentas_result = await db.execute(
        select(Cuenta)
        .where(Cuenta.activa == True)  # noqa: E712
        .order_by(Cuenta.nombre)
    )
    cuentas = cuentas_result.scalars().all()

    # Armar JSON
    payload = {
        "version": "1.0",
        "generado_en": datetime.now(timezone.utc).isoformat(),
        "categorias": [
            {
                "id": c.id,
                "nombre": c.nombre,
                "nivel": c.nivel,
                "id_padre": c.id_padre,
                "tipo_patron_gasto": c.tipo_patron_gasto,
            }
            for c in cats
        ],
        "contrapartes": [
            {"id": c.id, "nombre": c.nombre, "tipo": c.tipo}
            for c in cps
        ],
        "cuentas": [
            {"id": c.id, "nombre": c.nombre, "tipo": c.tipo, "banco": c.banco}
            for c in cuentas
        ],
    }

    # Escribir en OneDrive
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
        "contrapartes": len(cps),
        "cuentas": len(cuentas),
    }
