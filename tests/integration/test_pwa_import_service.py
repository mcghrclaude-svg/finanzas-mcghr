"""
Tests de integracion: backend/services/pwa_import_service.py

Cubre puntualmente el nuevo campo es_reembolsable ("Business Expense")
que viaja en el JSON que sube la PWA movil via OneDrive.
"""

import uuid
from datetime import datetime, timezone

import pytest

from backend.models.catalogo import Categoria, Cuenta, Moneda
from backend.models.transaccion import Transaccion
from backend.services.pwa_import_service import importar_gasto


async def _setup_catalogo(db):
    db.add(Categoria(id="CAT-ALIM", nombre="Alimentacion", nivel=1, activa=True))
    db.add(Cuenta(id="CTA-BC", nombre="BC CC", tipo="CC", banco="Bancolombia",
                   moneda="COP", activa=True))
    db.add(Moneda(codigo="COP", simbolo="$", nombre="Peso colombiano", activa=True))
    await db.flush()


def _gasto_base(**overrides):
    gasto = {
        "id": str(uuid.uuid4()),
        "fecha": "2026-06-15",
        "id_categoria": "CAT-ALIM",
        "monto": 45000,
        "id_moneda": "COP",
        "id_medio_pago": "CTA-BC",
        "quien": "GHR",
        "creado_en": datetime.now(timezone.utc).isoformat(),
    }
    gasto.update(overrides)
    return gasto


@pytest.mark.asyncio
async def test_importar_gasto_reembolsable_setea_estado_pendiente(db_session):
    await _setup_catalogo(db_session)
    gasto = _gasto_base(es_reembolsable=True)

    resultado = await importar_gasto(db_session, gasto, None, None, None)
    await db_session.commit()

    assert resultado.ok
    tx = await db_session.get(Transaccion, resultado.id_transaccion)
    assert bool(tx.es_reembolsable) is True
    assert tx.estado_reembolso == "pendiente"


@pytest.mark.asyncio
async def test_importar_gasto_no_reembolsable_por_default(db_session):
    """Compatibilidad con JSONs subidos antes de que este campo existiera."""
    await _setup_catalogo(db_session)
    gasto = _gasto_base()  # sin es_reembolsable

    resultado = await importar_gasto(db_session, gasto, None, None, None)
    await db_session.commit()

    assert resultado.ok
    tx = await db_session.get(Transaccion, resultado.id_transaccion)
    assert bool(tx.es_reembolsable) is False
    assert tx.estado_reembolso is None


@pytest.mark.asyncio
async def test_importar_gasto_es_reembolsable_false_explicito(db_session):
    await _setup_catalogo(db_session)
    gasto = _gasto_base(es_reembolsable=False)

    resultado = await importar_gasto(db_session, gasto, None, None, None)
    await db_session.commit()

    assert resultado.ok
    tx = await db_session.get(Transaccion, resultado.id_transaccion)
    assert bool(tx.es_reembolsable) is False
    assert tx.estado_reembolso is None
