"""
Tests de integracion para /api/v1/catalogos.
Usa DB en memoria — no toca la DB de OneDrive.
Corre con: pytest tests/integration/test_catalogos.py -v
"""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

BASE = "/api/v1/catalogos"


# ── Categorias ────────────────────────────────────────────────────────────────

class TestCategorias:
    async def test_listar_vacio(self, client: AsyncClient):
        r = await client.get(f"{BASE}/categorias")
        assert r.status_code == 200
        assert r.json() == []

    async def test_crear_nivel1(self, client: AsyncClient):
        r = await client.post(f"{BASE}/categorias", json={
            "id": "VIDA", "nombre": "Vida diaria", "nivel": 1,
            "tipo_patron_gasto": "variable_frecuente"
        })
        assert r.status_code == 201
        assert r.json()["id"] == "VIDA"

    async def test_crear_nivel2_con_padre(self, client: AsyncClient):
        await client.post(f"{BASE}/categorias", json={
            "id": "VIDA", "nombre": "Vida diaria", "nivel": 1,
            "tipo_patron_gasto": "variable_frecuente"
        })
        r = await client.post(f"{BASE}/categorias", json={
            "id": "VIDA-REST", "nombre": "Restaurantes", "nivel": 2,
            "id_padre": "VIDA", "tipo_patron_gasto": "variable_frecuente"
        })
        assert r.status_code == 201

    async def test_crear_padre_inexistente_rechazado(self, client: AsyncClient):
        r = await client.post(f"{BASE}/categorias", json={
            "id": "HIJO", "nombre": "Hijo", "nivel": 2,
            "id_padre": "NO-EXISTE", "tipo_patron_gasto": "variable_frecuente"
        })
        assert r.status_code == 422

    async def test_duplicado_rechazado(self, client: AsyncClient):
        await client.post(f"{BASE}/categorias", json={
            "id": "VIDA", "nombre": "Vida diaria", "nivel": 1,
            "tipo_patron_gasto": "variable_frecuente"
        })
        r = await client.post(f"{BASE}/categorias", json={
            "id": "VIDA", "nombre": "Duplicado", "nivel": 1,
            "tipo_patron_gasto": "variable_frecuente"
        })
        assert r.status_code == 409

    async def test_nivel_invalido_rechazado(self, client: AsyncClient):
        r = await client.post(f"{BASE}/categorias", json={
            "id": "X", "nombre": "X", "nivel": 5,
            "tipo_patron_gasto": "variable_frecuente"
        })
        assert r.status_code == 422

    async def test_patron_invalido_rechazado(self, client: AsyncClient):
        r = await client.post(f"{BASE}/categorias", json={
            "id": "X", "nombre": "X", "nivel": 1,
            "tipo_patron_gasto": "no_existe"
        })
        assert r.status_code == 422

    async def test_editar_nombre(self, client: AsyncClient):
        await client.post(f"{BASE}/categorias", json={
            "id": "VIDA", "nombre": "Vida diaria", "nivel": 1,
            "tipo_patron_gasto": "variable_frecuente"
        })
        r = await client.patch(f"{BASE}/categorias/VIDA", json={"nombre": "Vida"})
        assert r.status_code == 200
        assert r.json()["nombre"] == "Vida"

    async def test_inactivar(self, client: AsyncClient):
        await client.post(f"{BASE}/categorias", json={
            "id": "VIDA", "nombre": "Vida diaria", "nivel": 1,
            "tipo_patron_gasto": "variable_frecuente"
        })
        r = await client.delete(f"{BASE}/categorias/VIDA")
        assert r.status_code == 200
        r2 = await client.get(f"{BASE}/categorias/VIDA")
        assert r2.json()["activa"] == False

    async def test_flat_endpoint(self, client: AsyncClient):
        await client.post(f"{BASE}/categorias", json={
            "id": "VIDA", "nombre": "Vida diaria", "nivel": 1,
            "tipo_patron_gasto": "variable_frecuente"
        })
        r = await client.get(f"{BASE}/categorias?flat=true")
        assert r.status_code == 200
        assert any(c["id"] == "VIDA" for c in r.json())


# ── Cuentas ───────────────────────────────────────────────────────────────────

class TestCuentas:
    async def test_crear_cuenta(self, client: AsyncClient):
        r = await client.post(f"{BASE}/cuentas", json={
            "id": "BCO-CC-GHR", "nombre": "Bancolombia CC GHR",
            "tipo": "CC", "banco": "Bancolombia", "moneda": "COP"
        })
        assert r.status_code == 201
        assert r.json()["id"] == "BCO-CC-GHR"

    async def test_listar_cuentas(self, client: AsyncClient):
        await client.post(f"{BASE}/cuentas", json={
            "id": "BCO-CC-GHR", "nombre": "Bancolombia CC GHR",
            "tipo": "CC", "moneda": "COP"
        })
        r = await client.get(f"{BASE}/cuentas?solo_activas=false")
        assert len(r.json()) >= 1

    async def test_duplicado_rechazado(self, client: AsyncClient):
        await client.post(f"{BASE}/cuentas", json={
            "id": "BCO-CC-GHR", "nombre": "Banco CC", "tipo": "CC", "moneda": "COP"
        })
        r = await client.post(f"{BASE}/cuentas", json={
            "id": "BCO-CC-GHR", "nombre": "Duplicado", "tipo": "CC", "moneda": "COP"
        })
        assert r.status_code == 409

    async def test_inactivar_cuenta(self, client: AsyncClient):
        await client.post(f"{BASE}/cuentas", json={
            "id": "BCO-CC-GHR", "nombre": "Banco CC", "tipo": "CC", "moneda": "COP"
        })
        r = await client.delete(f"{BASE}/cuentas/BCO-CC-GHR")
        assert r.status_code == 200
        r2 = await client.get(f"{BASE}/cuentas/BCO-CC-GHR")
        assert r2.json()["activa"] == False

    async def test_no_encontrada(self, client: AsyncClient):
        r = await client.get(f"{BASE}/cuentas/NO-EXISTE")
        assert r.status_code == 404


# ── Contrapartes ──────────────────────────────────────────────────────────────

class TestContrapartes:
    async def test_crear_contraparte(self, client: AsyncClient):
        r = await client.post(f"{BASE}/contrapartes", json={
            "id": "RAPPI", "nombre": "Rappi", "tipo": "COMERCIO"
        })
        assert r.status_code == 201

    async def test_filtro_por_tipo(self, client: AsyncClient):
        await client.post(f"{BASE}/contrapartes", json={"id": "RAPPI", "nombre": "Rappi", "tipo": "COMERCIO"})
        await client.post(f"{BASE}/contrapartes", json={"id": "BANCOL", "nombre": "Bancolombia", "tipo": "BANCO"})
        r = await client.get(f"{BASE}/contrapartes?tipo=BANCO&solo_activas=false")
        ids = [c["id"] for c in r.json()]
        assert "BANCOL" in ids
        assert "RAPPI" not in ids

    async def test_id_invalido(self, client: AsyncClient):
        r = await client.post(f"{BASE}/contrapartes", json={
            "id": "tiene espacios", "nombre": "X", "tipo": "COMERCIO"
        })
        assert r.status_code == 422


# ── Personas ──────────────────────────────────────────────────────────────────

class TestPersonas:
    async def test_crear_persona(self, client: AsyncClient):
        r = await client.post(f"{BASE}/personas", json={
            "id": "GHR", "nombre": "Hernan Rizzi", "alias": "GHR"
        })
        assert r.status_code == 201

    async def test_listar_personas(self, client: AsyncClient):
        await client.post(f"{BASE}/personas", json={"id": "GHR", "nombre": "Hernan", "alias": "GHR"})
        await client.post(f"{BASE}/personas", json={"id": "MC", "nombre": "Martha", "alias": "MC"})
        r = await client.get(f"{BASE}/personas?solo_activas=false")
        assert len(r.json()) == 2

    async def test_inactivar_persona(self, client: AsyncClient):
        await client.post(f"{BASE}/personas", json={"id": "GHR", "nombre": "Hernan", "alias": "GHR"})
        r = await client.delete(f"{BASE}/personas/GHR")
        assert r.status_code == 200
        r2 = await client.get(f"{BASE}/personas/GHR")
        assert r2.json()["activa"] == False


# ── Health ────────────────────────────────────────────────────────────────────

async def test_health(client: AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
