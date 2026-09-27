import json
from unittest.mock import patch, AsyncMock

import pytest
from sqlalchemy import text


async def _crear_config_pwa_import(db, raices=None):
    # conftest.py ya crea config_pwa_import con su fila unica (id=1) para
    # toda la suite -- aca solo se pisa el valor de raices para el caso de
    # este test (mismo patron que test_catalogos_export.py).
    await db.execute(
        text("UPDATE config_pwa_import SET raices = :raices WHERE id = 1"),
        {"raices": json.dumps(raices or [])},
    )


@pytest.mark.asyncio
async def test_listar_presupuestos_vacio(client):
    resp = await client.get("/api/v1/presupuestos")
    assert resp.status_code == 200
    assert resp.json()["items"] == []


@pytest.mark.asyncio
async def test_guardar_presupuesto_batch_crea_varias(client, db_session, tmp_path):
    await _crear_config_pwa_import(db_session, raices=[str(tmp_path)])
    await db_session.commit()

    resp = await client.post("/api/v1/presupuestos/batch", json={
        "anio": 2026, "mes": 9,
        "items": [
            {"id_categoria": "CAT-VIVIENDA", "monto_presupuestado": "2000000"},
            {"id_categoria": "CAT-ALIM", "monto_presupuestado": "1200000"},
        ],
    })
    assert resp.status_code == 201
    items = resp.json()["items"]
    assert len(items) == 2
    montos = {i["id_categoria"]: i["monto_presupuestado"] for i in items}
    assert montos["CAT-VIVIENDA"] == 2000000.0
    assert montos["CAT-ALIM"] == 1200000.0

    listado = await client.get("/api/v1/presupuestos", params={"anio": 2026, "mes": 9})
    assert len(listado.json()["items"]) == 2


@pytest.mark.asyncio
async def test_guardar_presupuesto_batch_upsert_no_duplica(client, db_session, tmp_path):
    """Llamar /batch dos veces sobre la misma categoria actualiza el monto,
    no crea una segunda fila (mismo comportamiento que POST / individual)."""
    await _crear_config_pwa_import(db_session, raices=[str(tmp_path)])
    await db_session.commit()

    await client.post("/api/v1/presupuestos/batch", json={
        "anio": 2026, "mes": 9,
        "items": [{"id_categoria": "CAT-ALIM", "monto_presupuestado": "1000000"}],
    })
    resp = await client.post("/api/v1/presupuestos/batch", json={
        "anio": 2026, "mes": 9,
        "items": [{"id_categoria": "CAT-ALIM", "monto_presupuestado": "1500000"}],
    })
    assert resp.status_code == 201

    listado = await client.get("/api/v1/presupuestos", params={"anio": 2026, "mes": 9})
    items = listado.json()["items"]
    assert len(items) == 1
    assert items[0]["monto_presupuestado"] == 1500000.0


@pytest.mark.asyncio
async def test_guardar_presupuesto_batch_dispara_export_pwa_una_sola_vez(client):
    """El endpoint /batch existe justamente para no regenerar el JSON de la
    PWA una vez por categoria -- se graban 3 categorias y el export se llama
    una unica vez al final."""
    with patch(
        "backend.api.v1.routers.presupuestos.exportar_resumen_categorias_pwa",
        new_callable=AsyncMock,
    ) as mock_export:
        resp = await client.post("/api/v1/presupuestos/batch", json={
            "anio": 2026, "mes": 9,
            "items": [
                {"id_categoria": "CAT-A", "monto_presupuestado": "100000"},
                {"id_categoria": "CAT-B", "monto_presupuestado": "200000"},
                {"id_categoria": "CAT-C", "monto_presupuestado": "300000"},
            ],
        })
    assert resp.status_code == 201
    assert mock_export.call_count == 1


@pytest.mark.asyncio
async def test_crear_presupuesto_individual_dispara_export_pwa(client, db_session, tmp_path):
    await _crear_config_pwa_import(db_session, raices=[])
    await db_session.commit()

    with patch("backend.services.pwa_export_service.settings") as mock_settings:
        mock_settings.onedrive_path = str(tmp_path)
        resp = await client.post("/api/v1/presupuestos", json={
            "anio": 2026, "mes": 9,
            "id_categoria": "CAT-ALIM", "monto_presupuestado": "500000",
        })

    assert resp.status_code == 201
    json_path = tmp_path / "Resumen" / "resumen_categorias.json"
    assert json_path.exists()


@pytest.mark.asyncio
async def test_eliminar_presupuesto_dispara_export_pwa(client, db_session, tmp_path):
    await _crear_config_pwa_import(db_session, raices=[])
    await db_session.commit()

    with patch("backend.services.pwa_export_service.settings") as mock_settings:
        mock_settings.onedrive_path = str(tmp_path)
        await client.post("/api/v1/presupuestos", json={
            "anio": 2026, "mes": 9,
            "id_categoria": "CAT-ALIM", "monto_presupuestado": "500000",
        })
        json_path = tmp_path / "Resumen" / "resumen_categorias.json"
        json_path.unlink()  # confirmar que el DELETE lo regenera, no que ya estaba

        resp = await client.delete("/api/v1/presupuestos/2026/9/CAT-ALIM")

    assert resp.status_code == 204
    assert json_path.exists()
