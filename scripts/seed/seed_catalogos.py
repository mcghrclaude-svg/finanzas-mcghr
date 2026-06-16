"""
Seed de catalogos maestros para entorno dev/test.
Carga: personas, cuentas, categorias, contrapartes, reglas base.

Ejecucion:
    python -m scripts.seed.seed_catalogos
"""
import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from backend.models.base import Base
from backend.models.catalogo import Categoria, Cuenta, Contraparte, Persona
from backend.models.regla import ReglaClasificacion  # fix: era "Regla"
from backend.core.config import settings

# ── Personas ──────────────────────────────────────────────────────────────────
PERSONAS = [
    ("GHR", "Hernan Rizzi", "GHR"),
    ("MC",  "Martha",       "MC"),
]

# ── Categorias ────────────────────────────────────────────────────────────────
# (id, nombre, nivel, id_padre, tipo_patron_gasto)
CATEGORIAS = [
    # Nivel 1
    ("VIDA",  "Vida diaria",    1, None, "variable_frecuente"),
    ("HOGAR", "Hogar",          1, None, "variable_frecuente"),
    ("SALUD", "Salud",          1, None, "variable_esporadico"),
    ("EDU",   "Educacion",      1, None, "variable_esporadico"),
    ("OCO",   "Ocio y cultura", 1, None, "variable_frecuente"),
    ("FIN",   "Finanzas",       1, None, "fijo_recurrente"),
    ("ING",   "Ingresos",       1, None, "fijo_unico"),
    # Nivel 2 — Vida diaria
    ("VIDA-MKT",   "Mercado / supermercado",   2, "VIDA",  "variable_frecuente"),
    ("VIDA-REST",  "Restaurantes",             2, "VIDA",  "variable_frecuente"),
    ("VIDA-DELIV", "Delivery (Rappi/iFood)",   2, "VIDA",  "variable_frecuente"),
    ("VIDA-TRANS", "Transporte",               2, "VIDA",  "variable_frecuente"),
    # Nivel 2 — Hogar
    ("HOGAR-ARR",  "Arriendo",                 2, "HOGAR", "fijo_unico"),
    ("HOGAR-SERV", "Servicios publicos",       2, "HOGAR", "fijo_recurrente"),
    ("HOGAR-MANT", "Mantenimiento / mejoras",  2, "HOGAR", "variable_esporadico"),
    # Nivel 2 — Salud
    ("SALUD-MED",  "Medicamentos",             2, "SALUD", "variable_esporadico"),
    ("SALUD-CONS", "Consultas / examenes",     2, "SALUD", "variable_esporadico"),
    # Nivel 2 — Ocio
    ("OCO-SUBS",   "Suscripciones digitales",  2, "OCO",   "fijo_recurrente"),
    ("OCO-SAL",    "Salidas / entretenimiento",2, "OCO",   "variable_esporadico"),
    # Nivel 2 — Finanzas
    ("FIN-CUOTA",  "Cuotas prestamos",         2, "FIN",   "fijo_unico"),
    ("FIN-TC",     "Pago tarjeta credito",     2, "FIN",   "fijo_unico"),
    ("FIN-INVER",  "Aportes inversion",        2, "FIN",   "fijo_recurrente"),
    # Nivel 2 — Ingresos
    ("ING-SAL",    "Salarios",                 2, "ING",   "fijo_unico"),
    ("ING-INV",    "Rendimientos inversiones", 2, "ING",   "variable_esporadico"),
    # Nivel 3 — Vida/Rest
    ("VIDA-REST-DEL", "Delivery restaurante",  3, "VIDA-REST", "variable_frecuente"),
    ("VIDA-REST-SAL", "Salidas a restaurante", 3, "VIDA-REST", "variable_frecuente"),
]

# ── Cuentas ───────────────────────────────────────────────────────────────────
# (id, nombre, tipo, banco, moneda)
CUENTAS = [
    ("BCO-CC-GHR",  "Bancolombia CC GHR",            "CC",       "Bancolombia",        "COP"),
    ("BCO-TC-GHR",  "Bancolombia TC GHR",            "TC",       "Bancolombia",        "COP"),
    ("BBVA-CC-GHR", "BBVA CC GHR",                   "CC",       "BBVA",               "COP"),
    ("BBVA-TC-GHR", "BBVA TC GHR",                   "TC",       "BBVA",               "COP"),
    ("OCO-TC-GHR",  "Occidente Visa Signature GHR",  "TC",       "Banco de Occidente", "COP"),
    ("NEQ-GHR",     "Nequi GHR",                     "AHORRO",   "Nequi",              "COP"),
    ("IBKR-GHR",    "Interactive Brokers GHR",       "INVERSION","IBKR",               "USD"),
    ("BCO-CC-MC",   "Bancolombia CC MC",             "CC",       "Bancolombia",        "COP"),
    ("BBVA-CC-MC",  "BBVA CC MC",                    "CC",       "BBVA",               "COP"),
    ("OCO-CC-MC",   "Banco de Occidente MC",         "CC",       "Banco de Occidente", "COP"),
    ("EFE-COP",     "Efectivo COP",                  "EFECTIVO", None,                 "COP"),
    ("EFE-USD",     "Efectivo USD",                  "EFECTIVO", None,                 "USD"),
]

# ── Contrapartes ──────────────────────────────────────────────────────────────
# (id, nombre, tipo)
CONTRAPARTES = [
    # Supermercados
    ("EXITO",     "Exito",              "COMERCIO"),
    ("CARULLA",   "Carulla",            "COMERCIO"),
    ("D1",        "D1",                 "COMERCIO"),
    ("JUMBO",     "Jumbo",              "COMERCIO"),
    # Delivery / transporte
    ("RAPPI",     "Rappi",              "COMERCIO"),
    ("UBER-EATS", "Uber Eats",          "COMERCIO"),
    ("UBER",      "Uber",               "COMERCIO"),
    ("INDRIVER",  "InDriver",           "COMERCIO"),
    ("TERPEL",    "Terpel",             "COMERCIO"),
    # Suscripciones
    ("NETFLIX",   "Netflix",            "COMERCIO"),
    ("SPOTIFY",   "Spotify",            "COMERCIO"),
    ("DISNEY",    "Disney+",            "COMERCIO"),
    ("HBO",       "Max (HBO)",          "COMERCIO"),
    ("APPLE",     "Apple",              "COMERCIO"),
    # Bancos
    ("BANCOL",    "Bancolombia",        "BANCO"),
    ("BBVA-CO",   "BBVA Colombia",      "BANCO"),
    ("BCO-OCC",   "Banco de Occidente", "BANCO"),
    ("NEQUI",     "Nequi",              "BANCO"),
    # Inversiones
    ("IBKR",      "Interactive Brokers","ENTIDAD"),
    # Gobierno
    ("DIAN",      "DIAN",               "ENTIDAD"),
    # Telco
    ("CLARO",     "Claro",              "COMERCIO"),
    ("MOVISTAR",  "Movistar",           "COMERCIO"),
]

# ── Reglas de clasificacion base ──────────────────────────────────────────────
# (patron_regex, id_categoria, descripcion)
REGLAS = [
    (r"(?i)netflix",                  "OCO-SUBS",   "Netflix"),
    (r"(?i)spotify",                  "OCO-SUBS",   "Spotify"),
    (r"(?i)disney",                   "OCO-SUBS",   "Disney+"),
    (r"(?i)rappi|ifood",              "VIDA-DELIV",  "Delivery Rappi/iFood"),
    (r"(?i)uber\s?eats",              "VIDA-DELIV",  "Uber Eats"),
    (r"(?i)\buber\b|cabify|didi|indriver", "VIDA-TRANS", "Transporte app"),
    (r"(?i)terpel|primax|mobil|texaco", "VIDA-TRANS","Combustible"),
    (r"(?i)exito|jumbo|carulla|d1\b|ara\b", "VIDA-MKT", "Supermercado"),
    (r"(?i)claro|movistar|tigo",      "HOGAR-SERV", "Telecomunicaciones"),
    (r"(?i)cuota|prestamo|credito",   "FIN-CUOTA",  "Cuota prestamo"),
]


# ── Seed principal ────────────────────────────────────────────────────────────

async def seed():
    engine = create_async_engine(settings.db_url, echo=False)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with Session() as session:
        # Personas
        for id_, nombre, alias in PERSONAS:
            if not await session.get(Persona, id_):
                session.add(Persona(id=id_, nombre=nombre, alias=alias))

        await session.flush()

        # Categorias — en orden de nivel para respetar FK
        for id_, nombre, nivel, id_padre, patron in sorted(CATEGORIAS, key=lambda x: x[2]):
            if not await session.get(Categoria, id_):
                session.add(Categoria(
                    id=id_, nombre=nombre, nivel=nivel,
                    id_padre=id_padre, tipo_patron_gasto=patron,
                ))

        await session.flush()

        # Cuentas
        for id_, nombre, tipo, banco, moneda in CUENTAS:
            if not await session.get(Cuenta, id_):
                session.add(Cuenta(id=id_, nombre=nombre, tipo=tipo, banco=banco, moneda=moneda))

        # Contrapartes
        for id_, nombre, tipo in CONTRAPARTES:
            if not await session.get(Contraparte, id_):
                session.add(Contraparte(id=id_, nombre=nombre, tipo=tipo))

        # Reglas de clasificacion
        for patron, id_cat, desc in REGLAS:
            session.add(ReglaClasificacion(
                id=str(uuid.uuid4()),
                patron=patron,
                id_categoria=id_cat,
                fuente="sistema",
                peso=10,
            ))

        await session.commit()

    print("Seed completado:")
    print(f"  Personas:     {len(PERSONAS)}")
    print(f"  Categorias:   {len(CATEGORIAS)}")
    print(f"  Cuentas:      {len(CUENTAS)}")
    print(f"  Contrapartes: {len(CONTRAPARTES)}")
    print(f"  Reglas:       {len(REGLAS)}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
