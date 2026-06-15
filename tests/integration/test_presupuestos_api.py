import pytest


@pytest.mark.asyncio
async def test_listar_presupuestos_vacio(client):
    resp = await client.get("/api/v1/presupuestos")
    assert resp.status_code == 200
    assert resp.json()["items"] == []
