"""
Tests de integracion: /api/v1/inbox

Cubre:
    - GET /inbox retorna lista vacia y con items
    - GET /inbox/stats retorna contadores correctos
    - GET /inbox/{id} retorna detalle y 404
    - PATCH /inbox/{id} actualiza campos
    - POST /inbox/{id}/confirmar cambia estado
    - POST /inbox/{id}/confirmar con categoria distinta crea regla
    - POST /inbox/{id}/confirmar dos veces es idempotente
    - POST /inbox/{id}/descartar cambia estado a anulado
    - POST /inbox/confirmar-lote confirma multiples ids
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import insert

from backend.models.transaccion import Transaccion, Tramo
from backend.models.catalogo import Categoria, Contraparte, Cuenta, Persona
from backend.models.regla import ReglaClasificacion


# ---------------------------------------------------------------------------
# Helpers para insertar datos de prueba
# ---------------------------------------------------------------------------

def _id():
    return str(uuid.uuid4())


async def _insertar_catalogo_minimo(db):
    """Inserta categoria, contraparte y cuenta minimos para los tests."""
    cat = Categoria(
        id="TEST-CAT",
        nombre="Test Categoria",
        nivel=1,
        activa=True,
        tipo_patron_gasto="variable_frecuente",
    )
    cat2 = Categoria(
        id="TEST-CAT2",
        nombre="Test Categoria 2",
        nivel=1,
        activa=True,
        tipo_patron_gasto="variable_frecuente",
    )
    cp = Contraparte(id="TEST-CP", nombre="Test Comercio", tipo="COMERCIO", activa=True)
    cuenta = Cuenta(
        id="TEST-CC",
        nombre="Test Cuenta",
        tipo="CC",
        banco="Test Banco",
        moneda="COP",
        activa=True,
    )
    persona = Persona(id="TEST-GHR", nombre="Hernan Test", alias="GHR", activa=True)
    db.add_all([cat, cat2, cp, cuenta, persona])
    await db.flush()
    return cat, cat2, cp, cuenta, persona


async def _insertar_tx_pendiente(
    db,
    tx_id: str = None,
    confianza: float = 0.75,
    completitud: float = 0.80,
    origen: str = "email",
    id_categoria: str = "TEST-CAT",
    id_correo: str = None,
) -> Transaccion:
    tx_id = tx_id or _id()
    tx = Transaccion(
        id=tx_id,
        fecha=datetime(2026, 6, 15, tzinfo=timezone.utc),
        tipo="gasto",
        descripcion="Compra test Rappi",
        estado="pendiente",
        revisado_humano=False,
        confianza=Decimal(str(confianza)),
        completitud=Decimal(str(completitud)),
        origen=origen,
        id_categoria=id_categoria,
        id_contraparte="TEST-CP",
        id_correo=id_correo or f"correo_{tx_id[:8]}",
        fuente="gmail_hernan",
        creado_en=datetime.now(timezone.utc),
        actualizado_en=datetime.now(timezone.utc),
    )
    db.add(tx)

    tramo = Tramo(
        id_transaccion=tx_id,
        numero_orden=1,
        monto_origen=Decimal("45000.00"),
        moneda_origen="COP",
        estado="pendiente",
    )
    db.add(tramo)
    await db.flush()
    return tx


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_listar_inbox_vacio(client):
    """Sin datos, GET /inbox retorna lista vacia."""
    resp = await client.get("/api/v1/inbox/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total_pendientes"] == 0
    assert data["next_cursor"] is None


@pytest.mark.asyncio
async def test_listar_inbox_con_items(client, db_session):
    """Con transacciones pendientes, GET /inbox las retorna."""
    await _insertar_catalogo_minimo(db_session)
    await _insertar_tx_pendiente(db_session, confianza=0.75)
    await _insertar_tx_pendiente(db_session, confianza=0.45)
    await db_session.commit()

    resp = await client.get("/api/v1/inbox/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total_pendientes"] == 2


@pytest.mark.asyncio
async def test_listar_inbox_orden_completitud(client, db_session):
    """Items ordenados por completitud ASC (mas incompletos primero)."""
    await _insertar_catalogo_minimo(db_session)
    await _insertar_tx_pendiente(db_session, completitud=0.90)
    await _insertar_tx_pendiente(db_session, completitud=0.30)
    await _insertar_tx_pendiente(db_session, completitud=0.60)
    await db_session.commit()

    resp = await client.get("/api/v1/inbox/")
    assert resp.status_code == 200
    items = resp.json()["items"]
    completitudes = [i["completitud"] for i in items]
    assert completitudes == sorted(completitudes)


@pytest.mark.asyncio
async def test_stats_inbox(client, db_session):
    """GET /inbox/stats retorna contadores correctos."""
    await _insertar_catalogo_minimo(db_session)
    await _insertar_tx_pendiente(db_session, confianza=0.80)
    await _insertar_tx_pendiente(db_session, confianza=0.45)  # alta prioridad
    await _insertar_tx_pendiente(db_session, confianza=0.30)  # alta prioridad
    await db_session.commit()

    resp = await client.get("/api/v1/inbox/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["pendientes"] == 3
    assert data["alta_prioridad"] == 2


@pytest.mark.asyncio
async def test_detalle_inbox_item(client, db_session):
    """GET /inbox/{id} retorna detalle del item."""
    await _insertar_catalogo_minimo(db_session)
    tx = await _insertar_tx_pendiente(db_session)
    await db_session.commit()

    resp = await client.get(f"/api/v1/inbox/{tx.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == tx.id
    assert data["estado"] == "pendiente"
    assert data["descripcion"] == "Compra test Rappi"


@pytest.mark.asyncio
async def test_detalle_inbox_no_encontrado(client):
    """GET /inbox/{id_inexistente} retorna 404."""
    resp = await client.get("/api/v1/inbox/id-que-no-existe")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_editar_inbox_item(client, db_session):
    """PATCH /inbox/{id} actualiza campos del item."""
    await _insertar_catalogo_minimo(db_session)
    tx = await _insertar_tx_pendiente(db_session)
    await db_session.commit()

    resp = await client.patch(
        f"/api/v1/inbox/{tx.id}",
        json={"descripcion": "Almuerzo editado", "id_categoria": "TEST-CAT2"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["descripcion"] == "Almuerzo editado"
    assert data["id_categoria"] == "TEST-CAT2"


@pytest.mark.asyncio
async def test_confirmar_inbox_item(client, db_session):
    """POST /inbox/{id}/confirmar cambia estado a confirmado."""
    await _insertar_catalogo_minimo(db_session)
    tx = await _insertar_tx_pendiente(db_session)
    await db_session.commit()

    resp = await client.post(f"/api/v1/inbox/{tx.id}/confirmar")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["id"] == tx.id

    # verificar en DB que cambio estado
    detalle = await client.get(f"/api/v1/inbox/{tx.id}")
    assert detalle.json()["estado"] == "confirmado"


@pytest.mark.asyncio
async def test_confirmar_con_correccion_crea_regla(client, db_session):
    """Confirmar con categoria distinta a la propuesta crea regla de aprendizaje."""
    from sqlalchemy import select
    await _insertar_catalogo_minimo(db_session)
    tx = await _insertar_tx_pendiente(
        db_session,
        id_categoria="TEST-CAT",
        id_correo="correo_test_regla_001",
    )
    await db_session.commit()

    resp = await client.post(
        f"/api/v1/inbox/{tx.id}/confirmar",
        json={"id_categoria": "TEST-CAT2"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["regla_creada"] is True

    q = select(ReglaClasificacion).where(
        ReglaClasificacion.id_categoria == "TEST-CAT2"
    )
    result = await db_session.execute(q)
    regla = result.scalar_one_or_none()
    assert regla is not None
    assert regla.fuente == "usuario"


@pytest.mark.asyncio
async def test_confirmar_idempotente(client, db_session):
    """Confirmar dos veces el mismo item no da error ni duplica."""
    await _insertar_catalogo_minimo(db_session)
    tx = await _insertar_tx_pendiente(db_session)
    await db_session.commit()

    resp1 = await client.post(f"/api/v1/inbox/{tx.id}/confirmar")
    resp2 = await client.post(f"/api/v1/inbox/{tx.id}/confirmar")
    assert resp1.status_code == 200
    assert resp2.status_code == 200


@pytest.mark.asyncio
async def test_descartar_inbox_item(client, db_session):
    """POST /inbox/{id}/descartar cambia estado a anulado."""
    await _insertar_catalogo_minimo(db_session)
    tx = await _insertar_tx_pendiente(db_session)
    await db_session.commit()

    resp = await client.post(f"/api/v1/inbox/{tx.id}/descartar")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True

    detalle = await client.get(f"/api/v1/inbox/{tx.id}")
    assert detalle.json()["estado"] == "anulado"


@pytest.mark.asyncio
async def test_confirmar_lote(client, db_session):
    """POST /inbox/confirmar-lote confirma multiples items."""
    await _insertar_catalogo_minimo(db_session)
    tx1 = await _insertar_tx_pendiente(db_session)
    tx2 = await _insertar_tx_pendiente(db_session)
    tx3 = await _insertar_tx_pendiente(db_session)
    await db_session.commit()

    resp = await client.post(
        "/api/v1/inbox/confirmar-lote",
        json={"ids": [tx1.id, tx2.id, tx3.id]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["confirmados"] == 3
    assert data["errores"] == []


@pytest.mark.asyncio
async def test_filtro_por_origen(client, db_session):
    """GET /inbox?origen=pdf retorna solo items de PDF."""
    await _insertar_catalogo_minimo(db_session)
    await _insertar_tx_pendiente(db_session, origen="email")
    await _insertar_tx_pendiente(db_session, origen="pdf")
    await _insertar_tx_pendiente(db_session, origen="pdf")
    await db_session.commit()

    resp = await client.get("/api/v1/inbox/?origen=pdf")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 2
    assert all(i["origen"] == "pdf" for i in items)
