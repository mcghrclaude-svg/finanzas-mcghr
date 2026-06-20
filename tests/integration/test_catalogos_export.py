"""
Tests de integracion: /api/v1/catalogos

Cubre:
    - GET /catalogos/categorias retorna items
    - GET /catalogos/cuentas retorna items
    - GET /catalogos/contrapartes retorna items
    - POST /catalogos/export/pwa genera el JSON (mock filesystem)
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from backend.models.catalogo import Categoria, Cuenta, Contraparte, Persona


async def _insertar_catalogo_basico(db):
    db.add(Categoria(id="CAT1", nombre="Alimentacion", nivel=1, activa=True,
                     tipo_patron_gasto="variable_frecuente"))
    db.add(Categoria(id="CAT2", nombre="Transporte", nivel=1, activa=True,
                     tipo_patron_gasto="variable_frecuente"))
    db.add(Cuenta(id="CTA1", nombre="BC CC", tipo="CC", banco="Bancolombia",
                  moneda="COP", activa=True))
    db.add(Contraparte(id="CP1", nombre="Rappi", tipo="COMERCIO", activa=True))
    db.add(Persona(id="P1", nombre="Hernan", alias="GHR", activa=True))
    await db.flush()


@pytest.mark.asyncio
async def test_listar_categorias_vacio(client):
    resp = await client.get("/api/v1/catalogos/categorias")
    assert resp.status_code == 200
    assert resp.json()["items"] == []


@pytest.mark.asyncio
async def test_listar_categorias_con_datos(client, db_session):
    await _insertar_catalogo_basico(db_session)
    await db_session.commit()

    resp = await client.get("/api/v1/catalogos/categorias")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 2
    ids = [i["id"] for i in items]
    assert "CAT1" in ids
    assert "CAT2" in ids


@pytest.mark.asyncio
async def test_listar_cuentas(client, db_session):
    await _insertar_catalogo_basico(db_session)
    await db_session.commit()

    resp = await client.get("/api/v1/catalogos/cuentas")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == "CTA1"


@pytest.mark.asyncio
async def test_listar_contrapartes(client, db_session):
    await _insertar_catalogo_basico(db_session)
    await db_session.commit()

    resp = await client.get("/api/v1/catalogos/contrapartes")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["nombre"] == "Rappi"


@pytest.mark.asyncio
async def test_export_pwa(client, db_session, tmp_path):
    """POST /catalogos/export/pwa genera el JSON correctamente."""
    await _insertar_catalogo_basico(db_session)
    await db_session.commit()

    # Patchear onedrive_path para que escriba en tmp_path
    with patch("backend.api.v1.routers.catalogos.settings") as mock_settings:
        mock_settings.onedrive_path = str(tmp_path)

        resp = await client.post("/api/v1/catalogos/export/pwa")

    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["categorias"] == 2
    assert data["contrapartes"] == 1
    assert data["cuentas"] == 1

    # Verificar que el archivo se escribio
    json_path = tmp_path / "PWA" / "catalogos.json"
    assert json_path.exists()
    contenido = json.loads(json_path.read_text(encoding="utf-8"))
    assert contenido["version"] == "1.0"
    assert len(contenido["categorias"]) == 2
    assert len(contenido["contrapartes"]) == 1
