"""
Tests de integracion: /api/v1/reportes/reembolsos-pendientes

Cubre el reemplazo del stub por una consulta real (Business Expense /
gasto reembolsable pendiente de que el empleador lo devuelva).
"""

import uuid
from datetime import datetime, timezone

import pytest

from backend.models.transaccion import Transaccion, Tramo
from backend.models.catalogo import Categoria, Cuenta, Persona, Contraparte


def _id():
    return str(uuid.uuid4())


async def _insertar_reembolsable(
    db,
    monto: float,
    estado_reembolso: str,
    moneda: str = "COP",
    tipo_cambio: float | None = None,
    fecha: str = "2026-06-15",
):
    tx_id = _id()
    tx = Transaccion(
        id=tx_id,
        fecha=fecha,
        tipo="gasto",
        descripcion="Almuerzo cliente",
        estado="confirmado",
        revisado_humano=1,
        completitud="completo",
        confianza=0.9,
        id_categoria="CAT-ALIM",
        id_contraparte="CP-REST",
        quien_pago="P-GHR",
        es_reembolsable=True,
        estado_reembolso=estado_reembolso,
        fuente="manual",
        creado_en=datetime.now(timezone.utc),
        actualizado_en=datetime.now(timezone.utc),
    )
    db.add(tx)
    await db.flush()

    tramo = Tramo(
        id_transaccion=tx_id,
        numero_orden=1,
        id_cuenta_origen="CTA-BC",
        monto_origen=monto,
        moneda_origen=moneda,
        tipo_cambio=tipo_cambio,
        estado="confirmado",
    )
    db.add(tramo)
    await db.flush()
    return tx_id


@pytest.mark.asyncio
async def test_reembolsos_pendientes_vacio(client):
    resp = await client.get("/api/v1/reportes/reembolsos-pendientes")
    assert resp.status_code == 200
    assert resp.json() == {"items": [], "total": 0}


@pytest.mark.asyncio
async def test_reembolsos_pendientes_incluye_pendiente_y_solicitado(client, db_session):
    db_session.add(Categoria(id="CAT-ALIM", nombre="Alimentacion", nivel=1, activa=True))
    db_session.add(Cuenta(id="CTA-BC", nombre="BC CC", tipo="CC", banco="Bancolombia",
                           moneda="COP", activa=True))
    db_session.add(Persona(id="P-GHR", nombre="Hernan", alias="GHR", activa=True))
    db_session.add(Contraparte(id="CP-REST", nombre="Restaurante X", tipo="COMERCIO", activa=True))
    await db_session.flush()

    await _insertar_reembolsable(db_session, monto=45000.0, estado_reembolso="pendiente")
    await _insertar_reembolsable(db_session, monto=30000.0, estado_reembolso="solicitado")
    await db_session.commit()

    resp = await client.get("/api/v1/reportes/reembolsos-pendientes")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] == 75000.0
    assert {item["cuenta_pago"] for item in data["items"]} == {"BC CC"}
    assert {item["contraparte"] for item in data["items"]} == {"Restaurante X"}


@pytest.mark.asyncio
async def test_reembolsos_pendientes_excluye_ya_recibido(client, db_session):
    db_session.add(Categoria(id="CAT-ALIM", nombre="Alimentacion", nivel=1, activa=True))
    db_session.add(Cuenta(id="CTA-BC", nombre="BC CC", tipo="CC", banco="Bancolombia",
                           moneda="COP", activa=True))
    db_session.add(Persona(id="P-GHR", nombre="Hernan", alias="GHR", activa=True))
    db_session.add(Contraparte(id="CP-REST", nombre="Restaurante X", tipo="COMERCIO", activa=True))
    await db_session.flush()

    await _insertar_reembolsable(db_session, monto=45000.0, estado_reembolso="recibido")
    await db_session.commit()

    resp = await client.get("/api/v1/reportes/reembolsos-pendientes")
    assert resp.status_code == 200
    assert resp.json() == {"items": [], "total": 0}


@pytest.mark.asyncio
async def test_reembolsos_pendientes_convierte_moneda_extranjera(client, db_session):
    db_session.add(Categoria(id="CAT-ALIM", nombre="Alimentacion", nivel=1, activa=True))
    db_session.add(Cuenta(id="CTA-BC", nombre="BC CC", tipo="CC", banco="Bancolombia",
                           moneda="COP", activa=True))
    db_session.add(Persona(id="P-GHR", nombre="Hernan", alias="GHR", activa=True))
    db_session.add(Contraparte(id="CP-REST", nombre="Restaurante X", tipo="COMERCIO", activa=True))
    await db_session.flush()

    await _insertar_reembolsable(db_session, monto=100.0, estado_reembolso="pendiente",
                                  moneda="USD", tipo_cambio=4000.0)
    await db_session.commit()

    resp = await client.get("/api/v1/reportes/reembolsos-pendientes")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"][0]["monto_cop_estimado"] == 400000.0
    assert data["total"] == 400000.0
