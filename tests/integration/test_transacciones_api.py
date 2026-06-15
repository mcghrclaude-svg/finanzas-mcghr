"""
Tests de integración: /api/v1/transacciones
Usa el client fixture que monta la app con DB en memoria.
"""

import pytest


@pytest.mark.asyncio
async def test_health(client):
    """Smoke test: el servidor responde."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_listar_transacciones_vacio(client):
    """Sin datos, listar devuelve lista vacía sin error."""
    resp = await client.get("/api/v1/transacciones")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["items"] == []


@pytest.mark.asyncio
async def test_transaccion_no_encontrada(client):
    resp = await client.get("/api/v1/transacciones/id-inexistente")
    assert resp.status_code == 404
