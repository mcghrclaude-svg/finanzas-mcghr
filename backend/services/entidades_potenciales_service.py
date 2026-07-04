"""
Confirmacion de EntidadPotencial (propuestas del ETL pendientes de catalogo).

Compartido entre backend/api/v1/routers/inbox.py (confirmar desde una
transaccion puntual) y backend/api/v1/routers/catalogos.py (confirmar desde
la pestana Catalogos > Pending). Al confirmar una EP, todas las EPs
pendientes con el mismo tipo + valor_propuesto (propuestas para otras
transacciones) se confirman tambien, para que no queden mostrando el valor
como propuesta sin confirmar pese a que la entidad ya existe en el catalogo.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.catalogo import Categoria, Cuenta, Contraparte, EntidadPotencial
from backend.models.transaccion import Transaccion, Tramo


def _slug(nombre: str) -> str:
    s = unicodedata.normalize("NFD", nombre.upper())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^A-Z0-9\s-]", "", s).strip().replace(" ", "-")
    return s[:20]


async def slug_unico(nombre: str, db: AsyncSession, modelo) -> str:
    result = await db.execute(select(modelo.id))
    existentes = {row[0] for row in result.all()}
    base = _slug(nombre)
    if base not in existentes:
        return base
    i = 2
    while f"{base}-{i}" in existentes:
        i += 1
    return f"{base}-{i}"


async def _aplicar_a_transaccion(ep: EntidadPotencial, nuevo_id: str, db: AsyncSession) -> None:
    trx = await db.get(Transaccion, ep.id_transaccion)
    if not trx:
        return
    if ep.tipo == "contraparte":
        trx.id_contraparte = nuevo_id
    elif ep.tipo == "categoria":
        trx.id_categoria = nuevo_id
    elif ep.tipo == "cuenta":
        q_tramo = (
            select(Tramo)
            .where(Tramo.id_transaccion == ep.id_transaccion)
            .order_by(Tramo.numero_orden)
            .limit(1)
        )
        tramo = (await db.execute(q_tramo)).scalars().first()
        if tramo:
            tramo.id_cuenta_origen = nuevo_id


async def confirmar_ep(ep: EntidadPotencial, db: AsyncSession) -> str:
    """
    Crea la entrada de catalogo para ep y confirma toda EntidadPotencial
    pendiente con el mismo tipo + valor_propuesto (incluida ep). Devuelve
    el id nuevo creado en el catalogo.
    """
    if ep.tipo == "contraparte":
        nuevo_id = await slug_unico(ep.valor_propuesto, db, Contraparte)
        db.add(Contraparte(id=nuevo_id, nombre=ep.valor_propuesto, tipo="COMERCIO", activa=True))
    elif ep.tipo == "cuenta":
        nuevo_id = await slug_unico(ep.valor_propuesto, db, Cuenta)
        db.add(Cuenta(id=nuevo_id, nombre=ep.valor_propuesto, activa=True))
    elif ep.tipo == "categoria":
        nuevo_id = await slug_unico(ep.valor_propuesto, db, Categoria)
        db.add(Categoria(id=nuevo_id, nombre=ep.valor_propuesto, nivel=1, activa=True))
    else:
        raise ValueError(f"Tipo desconocido: {ep.tipo}")

    q_hermanas = select(EntidadPotencial).where(
        EntidadPotencial.tipo == ep.tipo,
        EntidadPotencial.valor_propuesto == ep.valor_propuesto,
        EntidadPotencial.estado == "pendiente",
    )
    eps_hermanas = (await db.execute(q_hermanas)).scalars().all()

    ahora = datetime.now(timezone.utc).isoformat()
    for ep_h in eps_hermanas:
        await _aplicar_a_transaccion(ep_h, nuevo_id, db)
        ep_h.estado = "confirmado"
        ep_h.resuelto_en = ahora

    return nuevo_id
