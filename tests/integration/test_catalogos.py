"""
Tests de integracion para /api/v1/catalogos.
Alineados con el contrato real del router catalogos.py actual:
  - GETs devuelven {"items": [...]}
  - POSTs devuelven {} (scaffold -- sin body de respuesta todavia)
  - DELETEs devuelven 204 No Content
  - No hay GET /{id} implementado aun
  - Las validaciones de negocio (duplicados, nivel invalido) aun no estan implementadas
"""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

BASE = "/api/v1/catalogos"


# ── Categorias ────────────────────────────────────────────────────────────────

class TestCategorias:
    async def test_listar_devuelve_items(self, client: AsyncClient):
        """GET /categorias devuelve {"items": []}"""
        r = await client.get(f"{BASE}/categorias")
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    async def test_listar_vacio(self, client: AsyncClient):
        r = await client.get(f"{BASE}/categorias")
        assert r.json()["items"] == []

    async def test_crear_devuelve_201(self, client: AsyncClient):
        """POST /categorias devuelve 201 (scaffold -- body vacio por ahora)"""
        r = await client.post(f"{BASE}/categorias", json={
            "id": "VIDA", "nombre": "Vida diaria", "nivel": 1,
            "tipo_patron_gasto": "variable_frecuente"
        })
        assert r.status_code == 201

    async def test_crear_nivel2(self, client: AsyncClient):
        r = await client.post(f"{BASE}/categorias", json={
            "id": "VIDA-REST", "nombre": "Restaurantes", "nivel": 2,
            "id_padre": "VIDA", "tipo_patron_gasto": "variable_frecuente"
        })
        assert r.status_code == 201

    async def test_editar_devuelve_200(self, client: AsyncClient):
        """PATCH /categorias/{id} devuelve 200"""
        r = await client.patch(f"{BASE}/categorias/VIDA", json={"nombre": "Vida"})
        assert r.status_code == 200

    async def test_inactivar_devuelve_204(self, client: AsyncClient):
        """DELETE /categorias/{id} devuelve 204 No Content"""
        r = await client.delete(f"{BASE}/categorias/VIDA")
        assert r.status_code == 204

    async def test_filtro_solo_activas(self, client: AsyncClient):
        r = await client.get(f"{BASE}/categorias?solo_activas=false")
        assert r.status_code == 200
        assert "items" in r.json()

    async def test_filtro_por_nivel(self, client: AsyncClient):
        r = await client.get(f"{BASE}/categorias?nivel=1")
        assert r.status_code == 200
        assert "items" in r.json()


# ── Cuentas ───────────────────────────────────────────────────────────────────

class TestCuentas:
    async def test_listar_devuelve_items(self, client: AsyncClient):
        r = await client.get(f"{BASE}/cuentas")
        assert r.status_code == 200
        assert "items" in r.json()

    async def test_listar_vacio(self, client: AsyncClient):
        r = await client.get(f"{BASE}/cuentas")
        assert r.json()["items"] == []

    async def test_crear_devuelve_201(self, client: AsyncClient):
        r = await client.post(f"{BASE}/cuentas", json={
            "id": "BCO-CC-GHR", "nombre": "Bancolombia CC GHR",
            "tipo": "CC", "banco": "Bancolombia", "moneda": "COP"
        })
        assert r.status_code == 201

    async def test_editar_devuelve_200(self, client: AsyncClient):
        r = await client.patch(f"{BASE}/cuentas/BCO-CC-GHR", json={"nombre": "Banco CC"})
        assert r.status_code == 200

    async def test_inactivar_devuelve_204(self, client: AsyncClient):
        r = await client.delete(f"{BASE}/cuentas/BCO-CC-GHR")
        assert r.status_code == 204

    async def test_filtro_solo_activas(self, client: AsyncClient):
        r = await client.get(f"{BASE}/cuentas?solo_activas=false")
        assert r.status_code == 200
        assert "items" in r.json()

    async def test_filtro_por_titular(self, client: AsyncClient):
        r = await client.get(f"{BASE}/cuentas?titular=GHR")
        assert r.status_code == 200
        assert "items" in r.json()


# ── Contrapartes ──────────────────────────────────────────────────────────────

class TestContrapartes:
    async def test_listar_devuelve_items(self, client: AsyncClient):
        r = await client.get(f"{BASE}/contrapartes")
        assert r.status_code == 200
        assert "items" in r.json()

    async def test_crear_devuelve_201(self, client: AsyncClient):
        r = await client.post(f"{BASE}/contrapartes", json={
            "id": "RAPPI", "nombre": "Rappi", "tipo": "COMERCIO"
        })
        assert r.status_code == 201

    async def test_filtro_por_tipo(self, client: AsyncClient):
        r = await client.get(f"{BASE}/contrapartes?tipo=COMERCIO")
        assert r.status_code == 200
        assert "items" in r.json()

    async def test_editar_devuelve_200(self, client: AsyncClient):
        r = await client.patch(f"{BASE}/contrapartes/RAPPI", json={"nombre": "Rappi Colombia"})
        assert r.status_code == 200

    async def test_inactivar_devuelve_204(self, client: AsyncClient):
        r = await client.delete(f"{BASE}/contrapartes/RAPPI")
        assert r.status_code == 204


# ── Personas ──────────────────────────────────────────────────────────────────

class TestPersonas:
    async def test_listar_devuelve_items(self, client: AsyncClient):
        r = await client.get(f"{BASE}/personas")
        assert r.status_code == 200
        assert "items" in r.json()

    async def test_crear_devuelve_201(self, client: AsyncClient):
        r = await client.post(f"{BASE}/personas", json={
            "id": "GHR", "nombre": "Hernan Rizzi", "alias": "GHR"
        })
        assert r.status_code == 201

    async def test_editar_devuelve_200(self, client: AsyncClient):
        r = await client.patch(f"{BASE}/personas/GHR", json={"nombre": "Hernan"})
        assert r.status_code == 200


# ── Health ────────────────────────────────────────────────────────────────────

async def test_health(client: AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
