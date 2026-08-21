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

from sqlalchemy import text

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


async def _crear_config_pwa_import(db, raices=None):
    # config_pwa_import no tiene modelo SQLAlchemy (raw SQL a proposito, ver
    # docstring de pwa_config.py) -- create_all no la crea, hay que armarla
    # a mano en tests que ejercitan el endpoint de export.
    await db.execute(text("""
        CREATE TABLE config_pwa_import (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            intervalo_minutos INTEGER NOT NULL DEFAULT 60,
            raices TEXT NOT NULL DEFAULT '[]',
            actualizado_en TEXT
        )
    """))
    await db.execute(
        text("INSERT INTO config_pwa_import (id, intervalo_minutos, raices) VALUES (1, 60, :raices)"),
        {"raices": json.dumps(raices or [])},
    )


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
async def test_export_pwa_sin_raices_configuradas(client, db_session, tmp_path):
    """Sin raices en config_pwa_import, cae al default onedrive_path/Catalogos."""
    await _insertar_catalogo_basico(db_session)
    await _crear_config_pwa_import(db_session, raices=[])
    await db_session.commit()

    with patch("backend.services.pwa_export_service.settings") as mock_settings:
        mock_settings.onedrive_path = str(tmp_path)

        resp = await client.post("/api/v1/catalogos/export/pwa")

    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["categorias"] == 2
    assert data["medios_de_pago"] == 1

    json_path = tmp_path / "Catalogos" / "catalogos.json"
    assert json_path.exists()
    contenido = json.loads(json_path.read_text(encoding="utf-8"))
    assert contenido["version"] == "1.0"
    assert len(contenido["categorias"]) == 2
    assert len(contenido["medios_de_pago"]) == 1


@pytest.mark.asyncio
async def test_export_pwa_escribe_en_cada_raiz(client, db_session, tmp_path):
    """Con varias raices configuradas (una por persona), catalogos.json se
    escribe en la carpeta Catalogos/ de CADA una -- no solo en la primera.
    Este es el fix del bug real: antes solo se escribia en un unico lugar."""
    await _insertar_catalogo_basico(db_session)
    raiz_ghr = tmp_path / "OneDriveGHR"
    raiz_mc = tmp_path / "OneDriveMC"
    await _crear_config_pwa_import(db_session, raices=[str(raiz_ghr), str(raiz_mc)])
    await db_session.commit()

    resp = await client.post("/api/v1/catalogos/export/pwa")

    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert len(data["rutas_archivo"]) == 2

    for raiz in (raiz_ghr, raiz_mc):
        json_path = raiz / "Catalogos" / "catalogos.json"
        assert json_path.exists()
        contenido = json.loads(json_path.read_text(encoding="utf-8"))
        assert len(contenido["categorias"]) == 2
