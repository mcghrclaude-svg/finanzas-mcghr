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
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.config import settings
from backend.models.catalogo import Categoria, Cuenta, Contraparte, Persona

router = APIRouter()


# -- Schemas Pydantic --------------------------------------------------

class CategoriaCreate(BaseModel):
    id: str
    nombre: str
    nivel: int = 1
    id_padre: str | None = None
    tipo_patron_gasto: str = "variable_frecuente"

class CategoriaUpdate(BaseModel):
    nombre: str | None = None
    tipo_patron_gasto: str | None = None

class CuentaCreate(BaseModel):
    id: str
    nombre: str
    tipo: str | None = None
    banco: str | None = None
    moneda: str = "COP"
    es_corporativa: bool = False

class CuentaUpdate(BaseModel):
    nombre: str | None = None
    tipo: str | None = None
    banco: str | None = None
    moneda: str | None = None
    es_corporativa: bool | None = None

class ContraparteCreate(BaseModel):
    id: str
    nombre: str
    tipo: str | None = None

class ContraparteUpdate(BaseModel):
    nombre: str | None = None
    tipo: str | None = None

class PersonaCreate(BaseModel):
    id: str
    nombre: str
    alias: str | None = None

class PersonaUpdate(BaseModel):
    nombre: str | None = None
    alias: str | None = None


# -- Categorias --------------------------------------------------------

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
async def crear_categoria(
    body: CategoriaCreate,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.get(Categoria, body.id)
    if existing:
        raise HTTPException(status_code=409, detail=f"Category '{body.id}' already exists")
    nueva = Categoria(
        id=body.id,
        nombre=body.nombre,
        nivel=body.nivel,
        id_padre=body.id_padre,
        tipo_patron_gasto=body.tipo_patron_gasto,
        activa=True,
    )
    db.add(nueva)
    await db.commit()
    await db.refresh(nueva)
    return {"id": nueva.id, "nombre": nueva.nombre}


@router.patch("/categorias/{categoria_id}")
async def editar_categoria(
    categoria_id: str,
    body: CategoriaUpdate,
    db: AsyncSession = Depends(get_db),
):
    cat = await db.get(Categoria, categoria_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    campos = body.model_dump(exclude_none=True)
    for k, v in campos.items():
        setattr(cat, k, v)
    await db.commit()
    await db.refresh(cat)
    return {"id": cat.id, "nombre": cat.nombre}


@router.delete("/categorias/{categoria_id}", status_code=204)
async def inactivar_categoria(
    categoria_id: str,
    db: AsyncSession = Depends(get_db),
):
    cat = await db.get(Categoria, categoria_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    cat.activa = not cat.activa
    await db.commit()
    return None


# -- Cuentas -----------------------------------------------------------

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
async def crear_cuenta(
    body: CuentaCreate,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.get(Cuenta, body.id)
    if existing:
        raise HTTPException(status_code=409, detail=f"Account '{body.id}' already exists")
    nueva = Cuenta(
        id=body.id,
        nombre=body.nombre,
        tipo=body.tipo,
        banco=body.banco,
        moneda=body.moneda,
        es_corporativa=body.es_corporativa,
        activa=True,
    )
    db.add(nueva)
    await db.commit()
    await db.refresh(nueva)
    return {"id": nueva.id, "nombre": nueva.nombre}


@router.patch("/cuentas/{cuenta_id}")
async def editar_cuenta(
    cuenta_id: str,
    body: CuentaUpdate,
    db: AsyncSession = Depends(get_db),
):
    cuenta = await db.get(Cuenta, cuenta_id)
    if not cuenta:
        raise HTTPException(status_code=404, detail="Account not found")
    campos = body.model_dump(exclude_none=True)
    for k, v in campos.items():
        setattr(cuenta, k, v)
    await db.commit()
    await db.refresh(cuenta)
    return {"id": cuenta.id, "nombre": cuenta.nombre}


@router.delete("/cuentas/{cuenta_id}", status_code=204)
async def inactivar_cuenta(
    cuenta_id: str,
    db: AsyncSession = Depends(get_db),
):
    cuenta = await db.get(Cuenta, cuenta_id)
    if not cuenta:
        raise HTTPException(status_code=404, detail="Account not found")
    cuenta.activa = not cuenta.activa
    await db.commit()
    return None


# -- Contrapartes ------------------------------------------------------

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
async def crear_contraparte(
    body: ContraparteCreate,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.get(Contraparte, body.id)
    if existing:
        raise HTTPException(status_code=409, detail=f"Entity '{body.id}' already exists")
    nueva = Contraparte(
        id=body.id,
        nombre=body.nombre,
        tipo=body.tipo,
        activa=True,
    )
    db.add(nueva)
    await db.commit()
    await db.refresh(nueva)
    return {"id": nueva.id, "nombre": nueva.nombre}


@router.patch("/contrapartes/{contraparte_id}")
async def editar_contraparte(
    contraparte_id: str,
    body: ContraparteUpdate,
    db: AsyncSession = Depends(get_db),
):
    cp = await db.get(Contraparte, contraparte_id)
    if not cp:
        raise HTTPException(status_code=404, detail="Entity not found")
    campos = body.model_dump(exclude_none=True)
    for k, v in campos.items():
        setattr(cp, k, v)
    await db.commit()
    await db.refresh(cp)
    return {"id": cp.id, "nombre": cp.nombre}


@router.delete("/contrapartes/{contraparte_id}", status_code=204)
async def inactivar_contraparte(
    contraparte_id: str,
    db: AsyncSession = Depends(get_db),
):
    cp = await db.get(Contraparte, contraparte_id)
    if not cp:
        raise HTTPException(status_code=404, detail="Entity not found")
    cp.activa = not cp.activa
    await db.commit()
    return None


# -- Personas ----------------------------------------------------------

@router.get("/personas")
async def listar_personas(db: AsyncSession = Depends(get_db)):
    q = select(Persona).order_by(Persona.nombre)
    result = await db.execute(q)
    personas = result.scalars().all()
    return {
        "items": [
            {"id": p.id, "nombre": p.nombre, "alias": p.alias, "activa": p.activa}
            for p in personas
        ]
    }


@router.post("/personas", status_code=201)
async def crear_persona(
    body: PersonaCreate,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.get(Persona, body.id)
    if existing:
        raise HTTPException(status_code=409, detail=f"Person '{body.id}' already exists")
    nueva = Persona(
        id=body.id,
        nombre=body.nombre,
        alias=body.alias,
        activa=True,
    )
    db.add(nueva)
    await db.commit()
    await db.refresh(nueva)
    return {"id": nueva.id, "nombre": nueva.nombre}


@router.patch("/personas/{persona_id}")
async def editar_persona(
    persona_id: str,
    body: PersonaUpdate,
    db: AsyncSession = Depends(get_db),
):
    persona = await db.get(Persona, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Person not found")
    campos = body.model_dump(exclude_none=True)
    for k, v in campos.items():
        setattr(persona, k, v)
    await db.commit()
    await db.refresh(persona)
    return {"id": persona.id, "nombre": persona.nombre}


@router.delete("/personas/{persona_id}", status_code=204)
async def inactivar_persona(
    persona_id: str,
    db: AsyncSession = Depends(get_db),
):
    persona = await db.get(Persona, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Person not found")
    persona.activa = not persona.activa
    await db.commit()
    return None


# -- Export PWA --------------------------------------------------------

@router.post("/export/pwa")
async def exportar_catalogos_pwa(db: AsyncSession = Depends(get_db)):
    """
    Genera catalogos.json con categorias, contrapartes y cuentas activas.
    Lo escribe en OneDrive/PWA/ para que la app mobile lo lea.
    """
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
