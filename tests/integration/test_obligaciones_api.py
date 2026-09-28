"""
Tests de integracion: /api/v1/obligaciones -- listado real y edicion de
saldo_pendiente (carga manual, item #4-5 del plan "Home widgets v1").
"""

import pytest

from backend.models.obligacion import Obligacion


async def _crear_obligacion(db, **kwargs):
    defaults = dict(
        id="OBL-HIP", nombre="Credito hipotecario", tipo="DEUDA",
        capital_inicial=40_000_000, activa=True,
    )
    defaults.update(kwargs)
    db.add(Obligacion(**defaults))
    await db.flush()


@pytest.mark.asyncio
async def test_listar_obligaciones_filtra_tipo(client, db_session):
    await _crear_obligacion(db_session, id="OBL-HIP", tipo="DEUDA")
    await _crear_obligacion(db_session, id="OBL-NET", nombre="Netflix", tipo="RECURRENTE",
                             capital_inicial=None)
    await db_session.commit()

    resp = await client.get("/api/v1/obligaciones", params={"tipo": "DEUDA"})
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == "OBL-HIP"


@pytest.mark.asyncio
async def test_editar_saldo_pendiente_registra_historico(client, db_session):
    await _crear_obligacion(db_session)
    await db_session.commit()

    resp = await client.patch("/api/v1/obligaciones/OBL-HIP", json={"saldo_pendiente": "28000000"})
    assert resp.status_code == 200
    assert resp.json()["saldo_pendiente"] == 28000000.0

    from sqlalchemy import text
    fila = (await db_session.execute(
        text("SELECT saldo FROM saldo_obligacion_historico WHERE id_obligacion = 'OBL-HIP'")
    )).first()
    assert fila is not None
    assert float(fila[0]) == 28000000.0


@pytest.mark.asyncio
async def test_editar_saldo_pendiente_sin_cambio_no_duplica_historico(client, db_session):
    await _crear_obligacion(db_session, saldo_pendiente=28_000_000)
    await db_session.commit()

    await client.patch("/api/v1/obligaciones/OBL-HIP", json={"saldo_pendiente": "28000000"})

    from sqlalchemy import text
    filas = (await db_session.execute(
        text("SELECT COUNT(*) FROM saldo_obligacion_historico WHERE id_obligacion = 'OBL-HIP'")
    )).scalar()
    assert filas == 0


@pytest.mark.asyncio
async def test_obligacion_no_encontrada(client):
    resp = await client.patch("/api/v1/obligaciones/no-existe", json={"saldo_pendiente": "1"})
    assert resp.status_code == 404
