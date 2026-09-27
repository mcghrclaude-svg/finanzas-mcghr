"""
Tests de integracion: GET/PATCH /api/v1/home-config -- preferencia de que
widgets se ven en el Home. Vive en el backend (no localStorage), item #3 del
plan "Home widgets v1".
"""

import pytest


@pytest.mark.asyncio
async def test_obtener_config_default(client):
    resp = await client.get("/api/v1/home-config")
    assert resp.status_code == 200
    assert resp.json() == {
        "insight_visible": True,
        "patrimonio_visible": True,
        "ask_visible": True,
    }


@pytest.mark.asyncio
async def test_actualizar_config_persiste(client):
    resp = await client.patch("/api/v1/home-config", json={"patrimonio_visible": False})
    assert resp.status_code == 200
    assert resp.json()["patrimonio_visible"] is False
    # Los otros campos no se tocan
    assert resp.json()["insight_visible"] is True

    releido = await client.get("/api/v1/home-config")
    assert releido.json()["patrimonio_visible"] is False


@pytest.mark.asyncio
async def test_actualizar_config_multiples_campos(client):
    resp = await client.patch("/api/v1/home-config", json={
        "insight_visible": False, "ask_visible": False,
    })
    data = resp.json()
    assert data["insight_visible"] is False
    assert data["ask_visible"] is False
    assert data["patrimonio_visible"] is True
