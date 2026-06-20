"""
Seed de inbox para desarrollo.
Crea 8 transacciones pendientes con distintas fuentes, confianzas y completitudes.

Requiere que seed_catalogos ya fue ejecutado (necesita categorias y contrapartes).

Ejecucion:
    venv\\Scripts\\activate
    python -m scripts.seed.seed_inbox

Idempotente: usa INSERT OR IGNORE via SQLAlchemy.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, text

import backend.models  # noqa: F401 -- registra todos los modelos
from backend.models.base import Base
from backend.models.transaccion import Transaccion, Tramo
from backend.core.config import settings


ITEMS_SEED = [
    # (descripcion, origen, confianza, completitud, id_categoria, monto, id_contraparte, id_correo)
    (
        "Cobro Netflix mensual",
        "email", 0.96, 0.95,
        "OCO-SUBS", Decimal("42900.00"),
        "CP-NETFLIX", "gmail_msg_netflix_001",
    ),
    (
        "Pedido Rappi restaurante",
        "email", 0.78, 0.80,
        "ALIM-REST", Decimal("67500.00"),
        "CP-RAPPI", "gmail_msg_rappi_001",
    ),
    (
        "Transferencia recibida origen desconocido",
        "email", 0.45, 0.40,
        None, Decimal("1200000.00"),
        None, "gmail_msg_tx_001",
    ),
    (
        "Cargo TC Bancolombia extracto",
        "pdf", 0.88, 0.90,
        "VIDA-TRANS", Decimal("85000.00"),
        "CP-UBER", None,
    ),
    (
        "Cargo sin descripcion legible",
        "pdf", 0.38, 0.25,
        None, Decimal("215000.00"),
        None, None,
    ),
    (
        "Foto factura farmacia (catalogada en PWA)",
        "mobile", 1.00, 1.00,
        "SALUD-MED", Decimal("35000.00"),
        None, None,
    ),
    (
        "Foto factura sin datos adicionales",
        "mobile", 0.55, 0.35,
        None, Decimal("48000.00"),
        None, None,
    ),
    (
        "Cobro Spotify Premium",
        "email", 0.97, 0.95,
        "OCO-SUBS", Decimal("17900.00"),
        "CP-SPOTIFY", "gmail_msg_spotify_001",
    ),
]


async def seed():
    engine = create_async_engine(settings.db_url, echo=False)
    SessionLocal = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    async with SessionLocal() as db:
        print("\nSeed inbox — Finanzas MCGHR")
        print("=" * 50)

        creados = 0
        saltados = 0

        for (desc, origen, conf, comp, id_cat, monto, id_cp, id_correo) in ITEMS_SEED:
            tx_id = f"SEED-INB-{uuid.uuid4().hex[:12].upper()}"

            # Verificar si ya existe una con la misma descripcion y origen
            q = select(Transaccion).where(
                Transaccion.descripcion == desc,
                Transaccion.origen == origen,
                Transaccion.estado == "pendiente",
            )
            result = await db.execute(q)
            existente = result.scalar_one_or_none()

            if existente:
                print(f"  SKIP (ya existe): {desc[:45]}")
                saltados += 1
                continue

            # Resolver id_categoria y id_contraparte contra la DB
            id_cat_real = await _resolver_categoria(db, id_cat)
            id_cp_real = await _resolver_contraparte(db, id_cp)

            tx = Transaccion(
                id=tx_id,
                fecha=datetime(2026, 6, 15, 10, 0, 0, tzinfo=timezone.utc),
                tipo="gasto",
                descripcion=desc,
                estado="pendiente",
                revisado_humano=False,
                confianza=Decimal(str(conf)),
                completitud=Decimal(str(comp)),
                origen=origen,
                id_categoria=id_cat_real,
                id_contraparte=id_cp_real,
                id_correo=id_correo,
                fuente="gmail_hernan" if origen == "email" else origen,
                creado_en=datetime.now(timezone.utc),
                actualizado_en=datetime.now(timezone.utc),
            )
            db.add(tx)
            await db.flush()

            tramo = Tramo(
                id_transaccion=tx_id,
                numero_orden=1,
                monto_origen=monto,
                moneda_origen="COP",
                estado="pendiente",
            )
            db.add(tramo)
            await db.flush()

            icon = "v" if conf >= 0.85 else ("~" if conf >= 0.60 else "!")
            print(f"  [{icon}] {desc[:45]:<45} {origen:<8} conf={conf:.0%}")
            creados += 1

        await db.commit()
        print(f"\n  Creados: {creados}  |  Saltados: {saltados}")
        print("=" * 50)

    await engine.dispose()


async def _resolver_categoria(db, id_cat):
    if not id_cat:
        return None
    from backend.models.catalogo import Categoria
    q = select(Categoria).where(Categoria.id == id_cat, Categoria.activa == True)  # noqa
    result = await db.execute(q)
    cat = result.scalar_one_or_none()
    return cat.id if cat else None


async def _resolver_contraparte(db, id_cp):
    if not id_cp:
        return None
    from backend.models.catalogo import Contraparte
    q = select(Contraparte).where(Contraparte.id == id_cp, Contraparte.activa == True)  # noqa
    result = await db.execute(q)
    cp = result.scalar_one_or_none()
    return cp.id if cp else None


if __name__ == "__main__":
    asyncio.run(seed())
