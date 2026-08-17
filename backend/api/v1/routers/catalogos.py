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

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.models.catalogo import Categoria, Cuenta, Contraparte, Persona, Moneda, EntidadPotencial
from backend.models.transaccion import Transaccion
from backend.schemas.catalogos import (
    CategoriaCreate,
    CategoriaUpdate,
    CuentaCreate,
    CuentaUpdate,
    ContraparteCreate,
    ContraparteUpdate,
    PersonaCreate,
    PersonaUpdate,
    MonedaCreate,
    MonedaUpdate,
)
from backend.services.entidades_potenciales_service import confirmar_ep
from backend.services.pwa_export_service import exportar_catalogos_pwa as generar_catalogos_pwa

router = APIRouter()


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
    await generar_catalogos_pwa(db)
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
    await generar_catalogos_pwa(db)
    return {"id": cat.id, "nombre": cat.nombre}


@router.delete("/categorias/{categoria_id}", status_code=204)
async def inactivar_categoria(
    categoria_id: str,
    db: AsyncSession = Depends(get_db),
):
    cat = await db.get(Categoria, categoria_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    if cat.activa:
        hijos_activos = await db.execute(
            select(Categoria.id).where(
                Categoria.id_padre == categoria_id,
                Categoria.activa == True,  # noqa: E712
            )
        )
        if hijos_activos.scalars().first():
            raise HTTPException(
                status_code=409,
                detail="Cannot deactivate a category that has active child categories",
            )
    cat.activa = not cat.activa
    await db.commit()
    await generar_catalogos_pwa(db)
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
                "propietario": c.propietario,
                "visible_pwa": c.visible_pwa,
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
        propietario=body.propietario,
        visible_pwa=body.visible_pwa,
        activa=True,
    )
    db.add(nueva)
    await db.commit()
    await db.refresh(nueva)
    await generar_catalogos_pwa(db)
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
    # exclude_unset (no exclude_none): el frontend manda el objeto completo
    # en cada edicion, incluyendo moneda=None cuando el usuario la vacia --
    # con exclude_none ese None se descartaria y moneda nunca se podria
    # "limpiar" de vuelta a NULL via edicion.
    campos = body.model_dump(exclude_unset=True)
    for k, v in campos.items():
        setattr(cuenta, k, v)
    await db.commit()
    await db.refresh(cuenta)
    await generar_catalogos_pwa(db)
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
    await generar_catalogos_pwa(db)
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


# -- Monedas -------------------------------------------------------------

@router.get("/monedas")
async def listar_monedas(
    solo_activas: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    q = select(Moneda)
    if solo_activas:
        q = q.where(Moneda.activa == True)  # noqa: E712
    q = q.order_by(Moneda.codigo)
    result = await db.execute(q)
    monedas = result.scalars().all()
    return {
        "items": [
            {"id": m.codigo, "nombre": m.nombre, "simbolo": m.simbolo, "activa": m.activa}
            for m in monedas
        ]
    }


@router.post("/monedas", status_code=201)
async def crear_moneda(
    body: MonedaCreate,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.get(Moneda, body.codigo)
    if existing:
        raise HTTPException(status_code=409, detail=f"Currency '{body.codigo}' already exists")
    nueva = Moneda(
        codigo=body.codigo,
        nombre=body.nombre,
        simbolo=body.simbolo,
        activa=True,
    )
    db.add(nueva)
    await db.commit()
    await db.refresh(nueva)
    await generar_catalogos_pwa(db)
    return {"id": nueva.codigo, "nombre": nueva.nombre}


@router.patch("/monedas/{codigo}")
async def editar_moneda(
    codigo: str,
    body: MonedaUpdate,
    db: AsyncSession = Depends(get_db),
):
    moneda = await db.get(Moneda, codigo)
    if not moneda:
        raise HTTPException(status_code=404, detail="Currency not found")
    campos = body.model_dump(exclude_none=True)
    for k, v in campos.items():
        setattr(moneda, k, v)
    await db.commit()
    await db.refresh(moneda)
    await generar_catalogos_pwa(db)
    return {"id": moneda.codigo, "nombre": moneda.nombre}


@router.delete("/monedas/{codigo}", status_code=204)
async def inactivar_moneda(
    codigo: str,
    db: AsyncSession = Depends(get_db),
):
    moneda = await db.get(Moneda, codigo)
    if not moneda:
        raise HTTPException(status_code=404, detail="Currency not found")
    moneda.activa = not moneda.activa
    await db.commit()
    await generar_catalogos_pwa(db)
    return None


# -- Entidades potenciales (propuestas por ETL) ------------------------

@router.get("/pendientes")
async def listar_pendientes(db: AsyncSession = Depends(get_db)):
    q = (
        select(EntidadPotencial, Transaccion.descripcion, Transaccion.fecha)
        .join(Transaccion, EntidadPotencial.id_transaccion == Transaccion.id)
        .where(EntidadPotencial.estado == "pendiente")
        .order_by(EntidadPotencial.creado_en.desc())
    )
    rows = (await db.execute(q)).all()
    return {
        "items": [
            {
                "id": ep.id,
                "tipo": ep.tipo,
                "valor_propuesto": ep.valor_propuesto,
                "id_transaccion": ep.id_transaccion,
                "trx_descripcion": desc,
                "trx_fecha": fecha,
                "creado_en": ep.creado_en,
            }
            for ep, desc, fecha in rows
        ]
    }


@router.post("/pendientes/{ep_id}/confirmar", status_code=201)
async def confirmar_pendiente(ep_id: int, db: AsyncSession = Depends(get_db)):
    ep = await db.get(EntidadPotencial, ep_id)
    if not ep:
        raise HTTPException(status_code=404, detail="Entidad potencial no encontrada")
    if ep.estado != "pendiente":
        raise HTTPException(status_code=409, detail=f"Estado actual: {ep.estado}")

    try:
        nuevo_id = await confirmar_ep(ep, db)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    await db.commit()
    return {"ok": True, "nuevo_id": nuevo_id, "tipo": ep.tipo}


@router.post("/pendientes/{ep_id}/descartar", status_code=200)
async def descartar_pendiente(ep_id: int, db: AsyncSession = Depends(get_db)):
    ep = await db.get(EntidadPotencial, ep_id)
    if not ep:
        raise HTTPException(status_code=404, detail="Entidad potencial no encontrada")
    if ep.estado != "pendiente":
        raise HTTPException(status_code=409, detail=f"Estado actual: {ep.estado}")
    ep.estado = "descartado"
    ep.resuelto_en = datetime.now(timezone.utc).isoformat()
    await db.commit()
    return {"ok": True}


# -- Export PWA --------------------------------------------------------

@router.post("/export/pwa")
async def exportar_pwa_endpoint(db: AsyncSession = Depends(get_db)):
    """
    Genera catalogos.json con categorias, medios_de_pago (cuentas) y monedas
    activas. Lo escribe en OneDrive/PWA/ para que la app mobile lo lea.
    """
    return await generar_catalogos_pwa(db)
