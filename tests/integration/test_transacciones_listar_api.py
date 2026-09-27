"""
Tests de integracion: GET /api/v1/transacciones (listado real, item #1-2 del
plan "Home widgets v1" -- reemplaza el stub que devolvia siempre []).
"""

import uuid
from datetime import datetime, timezone

import pytest

from backend.models.catalogo import Categoria, Cuenta
from backend.models.transaccion import Transaccion, Tramo


async def _setup_catalogo(db):
    db.add(Categoria(id="CAT-MERC", nombre="Mercado", nivel=1, activa=True))
    db.add(Cuenta(id="CTA-BC", nombre="BC Debito", tipo="CC", banco="Bancolombia",
                  moneda="COP", activa=True))
    await db.flush()


async def _tx(db, *, fecha, monto, estado="confirmado", id_categoria="CAT-MERC"):
    tx_id = str(uuid.uuid4())
    db.add(Transaccion(
        id=tx_id, fecha=fecha, tipo="gasto", descripcion="Compra",
        estado=estado, revisado_humano=1 if estado == "confirmado" else 0,
        confianza=0.9, completitud="completo", id_categoria=id_categoria,
        fuente="manual", creado_en=datetime.now(timezone.utc),
        actualizado_en=datetime.now(timezone.utc),
    ))
    await db.flush()
    db.add(Tramo(id_transaccion=tx_id, numero_orden=1, id_cuenta_origen="CTA-BC",
                 monto_origen=monto, moneda_origen="COP", estado=estado))
    await db.flush()
    return tx_id


@pytest.mark.asyncio
async def test_listar_transacciones_devuelve_monto_y_moneda_planos(client, db_session):
    await _setup_catalogo(db_session)
    await _tx(db_session, fecha="2026-06-15", monto=142300.0)
    await db_session.commit()

    resp = await client.get("/api/v1/transacciones")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["monto"] == 142300.0
    assert items[0]["moneda"] == "COP"
    assert items[0]["id_categoria"] == "CAT-MERC"
    assert items[0]["tramos"][0]["id_cuenta_origen"] == "CTA-BC"


@pytest.mark.asyncio
async def test_listar_transacciones_filtra_por_estado(client, db_session):
    await _setup_catalogo(db_session)
    await _tx(db_session, fecha="2026-06-14", monto=68500.0, estado="pendiente")
    await _tx(db_session, fecha="2026-06-15", monto=142300.0, estado="confirmado")
    await db_session.commit()

    resp = await client.get("/api/v1/transacciones", params={"estado": "confirmado"})
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["monto"] == 142300.0

    resp_all = await client.get("/api/v1/transacciones", params={"estado": "all"})
    assert len(resp_all.json()["items"]) == 2


@pytest.mark.asyncio
async def test_listar_transacciones_orden_mas_reciente_primero(client, db_session):
    await _setup_catalogo(db_session)
    await _tx(db_session, fecha="2026-06-01", monto=1000.0)
    await _tx(db_session, fecha="2026-06-20", monto=2000.0)
    await _tx(db_session, fecha="2026-06-10", monto=3000.0)
    await db_session.commit()

    resp = await client.get("/api/v1/transacciones")
    fechas = [it["fecha"] for it in resp.json()["items"]]
    assert fechas == ["2026-06-20", "2026-06-10", "2026-06-01"]
