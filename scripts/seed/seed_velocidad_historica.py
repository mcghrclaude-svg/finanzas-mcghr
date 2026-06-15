"""
Seed de velocidad histórica dummy — para desarrollo sin datos reales.

Crea registros en `velocidad_historica` para los períodos cerrados
2026-04 y 2026-05, cubriendo solo categorías variable_* (las que
necesitan histórico para el cálculo de riesgo).

Las categorías fijo_unico y fijo_recurrente no necesitan histórico
— el backend retorna nivel 'fijo' directamente.

Ejecución (luego de seed_catalogos y 002_dashboard_schema.sql):
    python -m scripts.seed.seed_velocidad_historica

Idempotente: usa INSERT OR IGNORE en SQLite.
"""

import asyncio
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from backend.core.config import settings

# ── Datos dummy ────────────────────────────────────────────────────────
#
# (id_categoria, periodo, monto_total, dias_periodo, velocidad_diaria, dias_con_gasto)
# Velocidades en COP/día. Varianza leve entre períodos para simular
# el comportamiento real (nunca dos meses idénticos).
#
# Período 2026-04: 25-mar → 24-abr = 30 días
# Período 2026-05: 25-abr → 24-may = 30 días

DUMMY_VELOCIDAD = [
    # Restaurantes — categoría variable frecuente, gasto alto
    ("VIDA-REST",  "2026-04", 470_400,  30, 15_680, 22),
    ("VIDA-REST",  "2026-05", 501_900,  30, 16_730, 24),

    # Transporte
    ("VIDA-TRANS", "2026-04", 468_000,  30, 15_600, 20),
    ("VIDA-TRANS", "2026-05", 481_500,  30, 16_050, 21),

    # Mercado / supermercado
    ("VIDA-MKT",   "2026-04", 1_440_000, 30, 48_000, 12),
    ("VIDA-MKT",   "2026-05", 1_530_000, 30, 51_000, 13),

    # Delivery
    ("VIDA-DELIV", "2026-04", 180_000,  30,  6_000, 8),
    ("VIDA-DELIV", "2026-05", 210_000,  30,  7_000, 9),

    # Mantenimiento hogar (esporadico — a veces 0)
    ("HOGAR-MANT", "2026-04",  90_000,  30,  3_000, 2),
    ("HOGAR-MANT", "2026-05",       0,  30,      0, 0),

    # Medicamentos
    ("SALUD-MED",  "2026-04",  45_000,  30,  1_500, 3),
    ("SALUD-MED",  "2026-05",  75_000,  30,  2_500, 4),

    # Consultas médicas
    ("SALUD-CONS", "2026-04",  90_000,  30,  3_000, 2),
    ("SALUD-CONS", "2026-05",  60_000,  30,  2_000, 1),

    # Salidas / ocio
    ("OCO-SALIDAS","2026-04", 250_000,  30,  8_333, 4),
    ("OCO-SALIDAS","2026-05", 180_000,  30,  6_000, 3),

    # Aportes a inversión (fijo_recurrente pero con variabilidad de monto)
    # Incluido para benchmark — el riesgo será 'fijo' de todas formas
    ("FIN-INVER",  "2026-04", 2_000_000, 30, 66_667, 1),
    ("FIN-INVER",  "2026-05", 2_000_000, 30, 66_667, 1),
]


async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        insertados = 0
        omitidos = 0
        for id_cat, id_per, monto, dias, vel_diaria, dias_con_gasto in DUMMY_VELOCIDAD:
            # Chequear si ya existe
            existing = await session.execute(
                text(
                    "SELECT id FROM velocidad_historica "
                    "WHERE id_categoria = :cat AND id_periodo = :per"
                ),
                {"cat": id_cat, "per": id_per},
            )
            if existing.scalar_one_or_none():
                omitidos += 1
                continue

            await session.execute(
                text(
                    """
                    INSERT INTO velocidad_historica
                      (id, id_categoria, id_periodo, monto_total, dias_periodo,
                       velocidad_diaria, dias_con_gasto, calculado_en)
                    VALUES
                      (:id, :cat, :per, :monto, :dias, :vel, :dias_gasto, :hoy)
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "cat": id_cat,
                    "per": id_per,
                    "monto": monto,
                    "dias": dias,
                    "vel": vel_diaria,
                    "dias_gasto": dias_con_gasto,
                    "hoy": str(date.today()),
                },
            )
            insertados += 1

        await session.commit()

    print(f"velocidad_historica seed: {insertados} insertados, {omitidos} ya existían")
    print("Categorías cubiertas: VIDA-REST, VIDA-TRANS, VIDA-MKT, VIDA-DELIV,")
    print("  HOGAR-MANT, SALUD-MED, SALUD-CONS, OCO-SALIDAS, FIN-INVER")
    print("Períodos: 2026-04 y 2026-05 (30 días cada uno)")


if __name__ == "__main__":
    asyncio.run(seed())
