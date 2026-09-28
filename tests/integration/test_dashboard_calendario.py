"""
Test de integracion: GET /api/v1/dashboard/resumen usa mes calendario, no
periodo financiero -- mismo criterio que /presupuestos/resumen-por-categoria
y que la PWA. Antes de este cambio, con un PeriodoFinanciero abierto activo,
el resumen usaba las fechas del periodo (ej. 25-may a 24-jun) en vez del mes
calendario pedido por query param.
"""

import uuid
from datetime import date, datetime, timezone

import pytest

from backend.models.catalogo import Categoria
from backend.models.transaccion import Transaccion, Tramo
from backend.models.periodo import PeriodoFinanciero


async def _gasto(db, fecha, monto):
    tx_id = str(uuid.uuid4())
    db.add(Transaccion(
        id=tx_id, fecha=fecha, tipo="gasto", estado="confirmado", revisado_humano=1,
        confianza=0.9, completitud="completo", id_categoria="CAT-TEST",
        fuente="manual", creado_en=datetime.now(timezone.utc),
        actualizado_en=datetime.now(timezone.utc),
    ))
    await db.flush()
    db.add(Tramo(id_transaccion=tx_id, numero_orden=1, monto_origen=monto,
                 moneda_origen="COP", estado="confirmado"))
    await db.flush()


@pytest.mark.asyncio
async def test_resumen_ignora_periodo_financiero_usa_mes_calendario(client, db_session):
    db_session.add(Categoria(id="CAT-TEST", nombre="Test", nivel=1, activa=True))
    # Periodo financiero abierto que cruza dos meses calendario (25-may a 24-jun)
    db_session.add(PeriodoFinanciero(
        id="2026-06", anio=2026, mes=6,
        fecha_inicio=date(2026, 5, 25), fecha_fin_tentativa=date(2026, 6, 24),
        estado="abierto",
    ))
    await db_session.flush()

    # Dentro del periodo financiero pero FUERA del mes calendario de junio
    await _gasto(db_session, "2026-05-26", 999_000.0)
    # Dentro del mes calendario de junio
    await _gasto(db_session, "2026-06-01", 50_000.0)
    await db_session.commit()

    resp = await client.get("/api/v1/dashboard/resumen", params={"anio": 2026, "mes": 6})
    assert resp.status_code == 200
    data = resp.json()

    # Solo debe contar el gasto de junio calendario, no el de mayo (aunque
    # este dentro del periodo financiero abierto)
    assert data["gastos_acumulados"] == 50_000.0
    assert data["periodo"]["fecha_inicio"] == "2026-06-01"
    assert data["periodo"]["estado"] == "mes_calendario"


@pytest.mark.asyncio
async def test_resumen_sin_datos_no_rompe(client):
    resp = await client.get("/api/v1/dashboard/resumen", params={"anio": 2026, "mes": 6})
    assert resp.status_code == 200
    data = resp.json()
    assert data["gastos_acumulados"] == 0.0
    assert data["saldo_proyectado_cierre"] == 0.0
