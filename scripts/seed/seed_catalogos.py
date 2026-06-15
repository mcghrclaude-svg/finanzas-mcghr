"""
Seed de catálogos maestros:
    - categorias (3 niveles, con tipo_patron_gasto)
    - cuentas (6 cuentas activas)
    - reglas_clasificacion (7 reglas base del sistema)

Ejecución:
    python -m scripts.seed.seed_catalogos
"""

import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.models.base import Base
from backend.models.catalogo import Categoria, Cuenta
from backend.models.regla import Regla
from backend.core.config import settings

# ─── Categorías ───────────────────────────────────────────────────────────────
# (id, nombre, nivel, id_padre, tipo_patron_gasto)
CATEGORIAS = [
    # Nivel 1
    ("VIDA",   "Vida diaria",       1, None, "variable_frecuente"),
    ("HOGAR",  "Hogar",             1, None, "variable_frecuente"),
    ("SALUD",  "Salud",             1, None, "variable_esporadico"),
    ("EDU",    "Educación",         1, None, "variable_esporadico"),
    ("OCO",    "Ocio y cultura",    1, None, "variable_frecuente"),
    ("FIN",    "Finanzas",          1, None, "fijo_recurrente"),
    ("ING",    "Ingresos",          1, None, "fijo_unico"),
    # Nivel 2 — Vida diaria
    ("VIDA-MKT",   "Mercado / supermercado",  2, "VIDA",  "variable_frecuente"),
    ("VIDA-REST",  "Restaurantes",            2, "VIDA",  "variable_frecuente"),
    ("VIDA-DELIV", "Delivery (Rappi/iFood)",  2, "VIDA",  "variable_frecuente"),
    ("VIDA-TRANS", "Transporte",              2, "VIDA",  "variable_frecuente"),
    # Nivel 2 — Hogar
    ("HOGAR-ARR",  "Arriendo",                2, "HOGAR", "fijo_unico"),
    ("HOGAR-SERV", "Servicios públicos",      2, "HOGAR", "fijo_recurrente"),
    ("HOGAR-MANT", "Mantenimiento / mejoras", 2, "HOGAR", "variable_esporadico"),
    # Nivel 2 — Salud
    ("SALUD-MED",  "Medicamentos",            2, "SALUD", "variable_esporadico"),
    ("SALUD-CONS", "Consultas / exámenes",    2, "SALUD", "variable_esporadico"),
    # Nivel 2 — Ocio
    ("OCO-SUBS",   "Suscripciones digitales", 2, "OCO",   "fijo_recurrente"),
    ("OCO-SALIDAS","Salidas / entretenimiento",2, "OCO",  "variable_esporadico"),
    # Nivel 2 — Finanzas
    ("FIN-CUOTA",  "Cuotas préstamos",        2, "FIN",   "fijo_unico"),
    ("FIN-TC",     "Pago tarjeta crédito",    2, "FIN",   "fijo_unico"),
    ("FIN-INVER",  "Aportes inversión",       2, "FIN",   "fijo_recurrente"),
    # Nivel 2 — Ingresos
    ("ING-SAL",    "Salarios",                2, "ING",   "fijo_unico"),
    ("ING-INV",    "Rendimientos inversiones",2, "ING",   "variable_esporadico"),
]

# ─── Cuentas ──────────────────────────────────────────────────────────────────
# (id, nombre, tipo, banco, moneda)
CUENTAS = [
    ("BCO-CC-GHR",  "Bancolombia CC GHR",   "CC",       "Bancolombia",   "COP"),
    ("BCO-TC-GHR",  "Bancolombia TC GHR",   "TC",       "Bancolombia",   "COP"),
    ("BBVA-CC-GHR", "BBVA CC GHR",          "CC",       "BBVA",          "COP"),
    ("BBVA-TC-GHR", "BBVA TC GHR",          "TC",       "BBVA",          "COP"),
    ("NEQ-GHR",     "Nequi GHR",            "AHORRO",   "Nequi",         "COP"),
    ("IBKR-GHR",    "Interactive Brokers",  "INVERSION","IBKR",          "USD"),
]

# ─── Reglas base del sistema ──────────────────────────────────────────────────
# (patron_regex, id_categoria, descripcion)
REGLAS_BASE = [
    (r"(?i)netflix",                    "OCO-SUBS",   "Netflix"),
    (r"(?i)spotify",                    "OCO-SUBS",   "Spotify"),
    (r"(?i)rappi|ifood",                "VIDA-DELIV", "Delivery Rappi/iFood"),
    (r"(?i)uber|cabify|didi",           "VIDA-TRANS", "Transporte app"),
    (r"(?i)terpel|primax|mobil",        "VIDA-TRANS", "Combustible"),
    (r"(?i)exito|jumbo|carulla|ara",    "VIDA-MKT",   "Supermercado"),
    (r"(?i)claro|movistar|tigo",        "HOGAR-SERV", "Telecomunicaciones"),
]


async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        # Categorías
        for id_, nombre, nivel, id_padre, tipo_patron in CATEGORIAS:
            existing = await session.get(Categoria, id_)
            if not existing:
                session.add(Categoria(
                    id=id_, nombre=nombre, nivel=nivel,
                    id_padre=id_padre, tipo_patron_gasto=tipo_patron,
                ))

        # Cuentas
        for id_, nombre, tipo, banco, moneda in CUENTAS:
            existing = await session.get(Cuenta, id_)
            if not existing:
                session.add(Cuenta(
                    id=id_, nombre=nombre, tipo=tipo, banco=banco, moneda=moneda,
                ))

        # Reglas
        for patron, id_cat, desc in REGLAS_BASE:
            session.add(Regla(
                id=str(uuid.uuid4()),
                patron=patron,
                id_categoria=id_cat,
                descripcion=desc,
                fuente="sistema",
                peso=10,
            ))

        await session.commit()
    print("Seed completado.")


if __name__ == "__main__":
    asyncio.run(seed())
