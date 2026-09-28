"""
Tests de integracion: GET /api/v1/presupuestos/ejecucion/{id_categoria}/subcategorias
-- drill-down del widget "Presupuesto por categoria" del Home (item #4 del
plan "Home widgets v1"). A diferencia de /ejecucion, una subcategoria sin
presupuesto cargado igual aparece, con monto_presupuestado=0.
"""

import uuid
from datetime import datetime, timezone

import pytest

from backend.models.catalogo import Categoria
from backend.models.transaccion import Transaccion, Tramo
from backend.models.presupuesto import Presupuesto


async def _setup_padre_e_hijos(db):
    db.add(Categoria(id="CAT-REST", nombre="Restaurantes", nivel=1, activa=True,
                      tipo_patron_gasto="variable_frecuente"))
    db.add(Categoria(id="CAT-REST-DOM", nombre="Domicilios", nivel=2, id_padre="CAT-REST",
                      activa=True, tipo_patron_gasto="variable_frecuente"))
    db.add(Categoria(id="CAT-REST-CAFE", nombre="Cafes", nivel=2, id_padre="CAT-REST",
                      activa=True, tipo_patron_gasto="variable_frecuente"))
    await db.flush()


async def _gasto(db, id_categoria, monto, fecha="2026-06-15"):
    tx_id = str(uuid.uuid4())
    db.add(Transaccion(
        id=tx_id, fecha=fecha, tipo="gasto", estado="confirmado", revisado_humano=1,
        confianza=0.9, completitud="completo", id_categoria=id_categoria,
        fuente="manual", creado_en=datetime.now(timezone.utc),
        actualizado_en=datetime.now(timezone.utc),
    ))
    await db.flush()
    db.add(Tramo(id_transaccion=tx_id, numero_orden=1, monto_origen=monto,
                 moneda_origen="COP", estado="confirmado"))
    await db.flush()


@pytest.mark.asyncio
async def test_subcategoria_sin_presupuesto_devuelve_cero(client, db_session):
    await _setup_padre_e_hijos(db_session)
    await _gasto(db_session, "CAT-REST-CAFE", 40_000.0)
    await db_session.commit()

    resp = await client.get(
        "/api/v1/presupuestos/ejecucion/CAT-REST/subcategorias",
        params={"anio": 2026, "mes": 6},
    )
    assert resp.status_code == 200
    items = {i["id_categoria"]: i for i in resp.json()["items"]}

    assert "CAT-REST-CAFE" in items
    assert items["CAT-REST-CAFE"]["monto_presupuestado"] == 0.0
    assert items["CAT-REST-CAFE"]["gasto_acumulado"] == 40_000.0
    assert items["CAT-REST-CAFE"]["pct_consumido"] == 0.0  # sin div por cero


@pytest.mark.asyncio
async def test_subcategoria_con_presupuesto_calcula_pct(client, db_session):
    await _setup_padre_e_hijos(db_session)
    await _gasto(db_session, "CAT-REST-DOM", 260_000.0)
    db_session.add(Presupuesto(
        id=str(uuid.uuid4()), anio=2026, mes=6,
        id_categoria="CAT-REST-DOM", monto_presupuestado=350_000,
    ))
    await db_session.commit()

    resp = await client.get(
        "/api/v1/presupuestos/ejecucion/CAT-REST/subcategorias",
        params={"anio": 2026, "mes": 6},
    )
    items = {i["id_categoria"]: i for i in resp.json()["items"]}
    assert items["CAT-REST-DOM"]["monto_presupuestado"] == 350_000.0
    assert round(items["CAT-REST-DOM"]["pct_consumido"], 3) == round(260_000 / 350_000, 3)


@pytest.mark.asyncio
async def test_subcategorias_de_categoria_sin_hijos_es_vacio(client, db_session):
    db_session.add(Categoria(id="CAT-SALUD", nombre="Salud", nivel=1, activa=True))
    await db_session.commit()

    resp = await client.get(
        "/api/v1/presupuestos/ejecucion/CAT-SALUD/subcategorias",
        params={"anio": 2026, "mes": 6},
    )
    assert resp.json()["items"] == []
