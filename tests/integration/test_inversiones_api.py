"""
Tests de integracion: /api/v1/inversiones/patrimonio (+/historico) -- item #6
del plan "Home widgets v1". Activos reales desde Inversion/Valuacion, deudas
reales desde Obligacion.saldo_pendiente (carga manual, v1.8).
"""

from datetime import datetime, timezone

import pytest

from backend.models.inversion import Inversion, Valuacion
from backend.models.obligacion import Obligacion


@pytest.mark.asyncio
async def test_resumen_patrimonio_suma_activos_y_deudas_reales(client, db_session):
    db_session.add(Inversion(id="INV-AH", nombre="Ahorros Bancolombia", tipo="AHORRO", activa=True))
    await db_session.flush()
    db_session.add(Valuacion(id="VAL-1", id_inversion="INV-AH",
                              fecha=datetime(2026, 6, 1, tzinfo=timezone.utc), valor=42_000_000))
    db_session.add(Obligacion(id="OBL-HIP", nombre="Hipotecario", tipo="DEUDA",
                               activa=True, saldo_pendiente=28_000_000))
    await db_session.commit()

    resp = await client.get("/api/v1/inversiones/patrimonio")
    assert resp.status_code == 200
    data = resp.json()
    assert data["activos_total"] == 42_000_000.0
    assert data["deudas_total"] == 28_000_000.0
    assert data["patrimonio_neto"] == 14_000_000.0
    assert data["detalle_activos"][0]["nombre"] == "Ahorros Bancolombia"
    assert data["detalle_deudas"][0]["saldo_pendiente"] == 28_000_000.0


@pytest.mark.asyncio
async def test_resumen_patrimonio_sin_datos_es_cero(client):
    resp = await client.get("/api/v1/inversiones/patrimonio")
    data = resp.json()
    assert data["activos_total"] == 0.0
    assert data["deudas_total"] == 0.0
    assert data["patrimonio_neto"] == 0.0


@pytest.mark.asyncio
async def test_historico_patrimonio_sin_datos_devuelve_puntos_nulos(client):
    resp = await client.get("/api/v1/inversiones/patrimonio/historico", params={"meses": 3})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["puntos"]) == 3
    assert all(p["activos_total"] is None for p in data["puntos"])
    assert all(p["deudas_total"] is None for p in data["puntos"])


@pytest.mark.asyncio
async def test_historico_patrimonio_usa_ultima_valuacion_al_cierre_del_mes(client, db_session):
    db_session.add(Inversion(id="INV-AH", nombre="Ahorros", tipo="AHORRO", activa=True))
    await db_session.flush()
    # Dos valuaciones del mismo mes -- debe quedarse con la mas reciente.
    db_session.add(Valuacion(id="VAL-1", id_inversion="INV-AH",
                              fecha=datetime(2026, 6, 5, tzinfo=timezone.utc), valor=40_000_000))
    db_session.add(Valuacion(id="VAL-2", id_inversion="INV-AH",
                              fecha=datetime(2026, 6, 20, tzinfo=timezone.utc), valor=42_000_000))
    await db_session.commit()

    resp = await client.get("/api/v1/inversiones/patrimonio/historico", params={"meses": 1})
    punto = resp.json()["puntos"][0]
    assert punto["activos_total"] == 42_000_000.0
