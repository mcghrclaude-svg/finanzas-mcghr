"""
Test de integracion: GET /api/v1/inbox/stats incluye pendientes_sms (item #3
del plan "Home widgets v1" -- conteo de pendientes leidos por SMS, columna
Transaccion.fuente='sms_bc', separado del conteo general de inbox).
"""

from datetime import datetime, timezone

import pytest

from backend.models.catalogo import Categoria
from backend.models.transaccion import Transaccion


async def _tx_pendiente(db, tx_id: str, fuente: str):
    db.add(Transaccion(
        id=tx_id,
        fecha="2026-06-15",
        tipo="gasto",
        estado="pendiente",
        revisado_humano=0,
        confianza=0.8,
        completitud="parcial",
        id_categoria="TEST-CAT",
        fuente=fuente,
        creado_en=datetime.now(timezone.utc),
        actualizado_en=datetime.now(timezone.utc),
    ))
    await db.flush()


@pytest.mark.asyncio
async def test_stats_cuenta_pendientes_sms_por_separado(client, db_session):
    db_session.add(Categoria(id="TEST-CAT", nombre="Test", nivel=1, activa=True))
    await db_session.flush()

    await _tx_pendiente(db_session, "TX-SMS-1", fuente="sms_bc")
    await _tx_pendiente(db_session, "TX-SMS-2", fuente="sms_bc")
    await _tx_pendiente(db_session, "TX-MAIL-1", fuente="gmail_hernan")
    await db_session.commit()

    resp = await client.get("/api/v1/inbox/stats")
    data = resp.json()
    assert data["pendientes"] == 3
    assert data["pendientes_sms"] == 2


@pytest.mark.asyncio
async def test_stats_pendientes_sms_cero_sin_datos(client):
    resp = await client.get("/api/v1/inbox/stats")
    assert resp.json()["pendientes_sms"] == 0
