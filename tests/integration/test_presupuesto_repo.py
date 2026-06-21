"""
Tests de integracion: presupuesto_repo -- issues #23, #24, #25, #27

Cubre:
    #23 -- obtener_gasto_acumulado_periodo usa tramos.monto_origen (no transacciones.monto)
    #24 -- filtros usan tipo='gasto' y estado='confirmado' (minusculas, sin 'a' final)
    #25 -- obtener_conteo_inbox_pendiente cuenta transacciones, no inbox_mobile
    #27 -- filtros de fecha usan strings ISO (fecha es TEXT en la DB)
"""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select

from backend.models.presupuesto import Presupuesto
from backend.models.periodo import PeriodoFinanciero
from backend.models.transaccion import Transaccion, Tramo
from backend.models.catalogo import Categoria, Cuenta, Persona
from backend.repositories.presupuesto_repo import PresupuestoRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _id():
    return str(uuid.uuid4())


async def _setup_catalogo(db):
    db.add(Categoria(id="CAT-ALIM", nombre="Alimentacion", nivel=1, activa=True,
                     tipo_patron_gasto="variable_frecuente"))
    db.add(Cuenta(id="CTA-BC", nombre="BC CC", tipo="CC", banco="Bancolombia",
                  moneda="COP", activa=True))
    db.add(Persona(id="P-GHR", nombre="Hernan", alias="GHR", activa=True))
    await db.flush()


async def _insertar_tx_con_tramo(
    db,
    monto: float,
    tipo: str = "gasto",
    estado: str = "confirmado",
    fecha: str = "2026-06-15",
    id_categoria: str = "CAT-ALIM",
) -> tuple[Transaccion, Tramo]:
    tx_id = _id()
    tx = Transaccion(
        id=tx_id,
        fecha=fecha,
        tipo=tipo,
        estado=estado,
        revisado_humano=1 if estado == "confirmado" else 0,
        confianza=0.9,
        completitud="completo",
        id_categoria=id_categoria,
        fuente="gmail_hernan",
        creado_en=datetime.now(timezone.utc),
        actualizado_en=datetime.now(timezone.utc),
    )
    db.add(tx)
    await db.flush()

    tramo = Tramo(
        id_transaccion=tx_id,
        numero_orden=1,
        monto_origen=monto,
        moneda_origen="COP",
        estado="confirmado" if estado == "confirmado" else "pendiente",
    )
    db.add(tramo)
    await db.flush()
    return tx, tramo


# ---------------------------------------------------------------------------
# Tests issue #23 y #24: gasto_acumulado usa tramos y tipos correctos
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_gasto_acumulado_suma_desde_tramos(client, db_session):
    """#23: el monto viene de tramos.monto_origen, no de transacciones.monto."""
    await _setup_catalogo(db_session)
    await _insertar_tx_con_tramo(db_session, monto=45000.0, tipo="gasto",
                                  estado="confirmado", fecha="2026-06-15")
    await _insertar_tx_con_tramo(db_session, monto=30000.0, tipo="gasto",
                                  estado="confirmado", fecha="2026-06-20")
    await db_session.commit()

    repo = PresupuestoRepository(db_session)
    total = await repo.obtener_gasto_acumulado_periodo(
        "CAT-ALIM", date(2026, 6, 1), date(2026, 6, 30)
    )
    assert total == Decimal("75000")


@pytest.mark.asyncio
async def test_gasto_acumulado_excluye_pendientes(client, db_session):
    """#24: solo cuenta estado='confirmado', no 'pendiente'."""
    await _setup_catalogo(db_session)
    await _insertar_tx_con_tramo(db_session, monto=45000.0, tipo="gasto",
                                  estado="confirmado", fecha="2026-06-15")
    await _insertar_tx_con_tramo(db_session, monto=99000.0, tipo="gasto",
                                  estado="pendiente", fecha="2026-06-15")
    await db_session.commit()

    repo = PresupuestoRepository(db_session)
    total = await repo.obtener_gasto_acumulado_periodo(
        "CAT-ALIM", date(2026, 6, 1), date(2026, 6, 30)
    )
    assert total == Decimal("45000")


@pytest.mark.asyncio
async def test_gasto_acumulado_excluye_ingresos(client, db_session):
    """#24: solo cuenta tipo='gasto', no 'ingreso'."""
    await _setup_catalogo(db_session)
    await _insertar_tx_con_tramo(db_session, monto=45000.0, tipo="gasto",
                                  estado="confirmado", fecha="2026-06-15")
    await _insertar_tx_con_tramo(db_session, monto=1000000.0, tipo="ingreso",
                                  estado="confirmado", fecha="2026-06-15")
    await db_session.commit()

    repo = PresupuestoRepository(db_session)
    total = await repo.obtener_gasto_acumulado_periodo(
        "CAT-ALIM", date(2026, 6, 1), date(2026, 6, 30)
    )
    assert total == Decimal("45000")


@pytest.mark.asyncio
async def test_gastos_totales_suma_todas_categorias(client, db_session):
    """#23 y #24: gastos_totales suma todas las categorias confirmadas."""
    await _setup_catalogo(db_session)
    db_session.add(Categoria(id="CAT-TRANS", nombre="Transporte", nivel=1,
                              activa=True, tipo_patron_gasto="variable_frecuente"))
    await db_session.flush()

    await _insertar_tx_con_tramo(db_session, monto=45000.0, tipo="gasto",
                                  estado="confirmado", fecha="2026-06-15",
                                  id_categoria="CAT-ALIM")
    await _insertar_tx_con_tramo(db_session, monto=20000.0, tipo="gasto",
                                  estado="confirmado", fecha="2026-06-15",
                                  id_categoria="CAT-TRANS")
    await db_session.commit()

    repo = PresupuestoRepository(db_session)
    total = await repo.obtener_gastos_totales_periodo(
        date(2026, 6, 1), date(2026, 6, 30)
    )
    assert total == Decimal("65000")


@pytest.mark.asyncio
async def test_ingresos_periodo(client, db_session):
    """#23 y #24: ingresos suma tipo='ingreso' confirmados desde tramos."""
    await _setup_catalogo(db_session)
    await _insertar_tx_con_tramo(db_session, monto=5000000.0, tipo="ingreso",
                                  estado="confirmado", fecha="2026-06-25")
    await _insertar_tx_con_tramo(db_session, monto=45000.0, tipo="gasto",
                                  estado="confirmado", fecha="2026-06-15")
    await db_session.commit()

    repo = PresupuestoRepository(db_session)
    total = await repo.obtener_ingresos_periodo(
        date(2026, 6, 1), date(2026, 6, 30)
    )
    assert total == Decimal("5000000")


# ---------------------------------------------------------------------------
# Tests issue #25: conteo inbox usa transacciones
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_conteo_inbox_cuenta_tx_pendientes(client, db_session):
    """#25: conteo inbox cuenta transacciones pendientes, no inbox_mobile."""
    await _setup_catalogo(db_session)
    await _insertar_tx_con_tramo(db_session, monto=45000.0, tipo="gasto",
                                  estado="pendiente", fecha="2026-06-15")
    await _insertar_tx_con_tramo(db_session, monto=30000.0, tipo="gasto",
                                  estado="pendiente", fecha="2026-06-15")
    await _insertar_tx_con_tramo(db_session, monto=20000.0, tipo="gasto",
                                  estado="confirmado", fecha="2026-06-15")
    await db_session.commit()

    repo = PresupuestoRepository(db_session)
    conteo = await repo.obtener_conteo_inbox_pendiente()
    assert conteo == 2


@pytest.mark.asyncio
async def test_conteo_inbox_cero_sin_pendientes(client, db_session):
    """#25: retorna 0 cuando no hay transacciones pendientes."""
    repo = PresupuestoRepository(db_session)
    conteo = await repo.obtener_conteo_inbox_pendiente()
    assert conteo == 0


# ---------------------------------------------------------------------------
# Tests issue #27: filtros de fecha como strings ISO
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_filtro_fecha_excluye_fuera_de_rango(client, db_session):
    """#27: transacciones fuera del rango de fecha no se suman."""
    await _setup_catalogo(db_session)
    # Dentro del rango
    await _insertar_tx_con_tramo(db_session, monto=45000.0, tipo="gasto",
                                  estado="confirmado", fecha="2026-06-15")
    # Fuera del rango (mes anterior)
    await _insertar_tx_con_tramo(db_session, monto=99000.0, tipo="gasto",
                                  estado="confirmado", fecha="2026-05-31")
    await db_session.commit()

    repo = PresupuestoRepository(db_session)
    total = await repo.obtener_gasto_acumulado_periodo(
        "CAT-ALIM", date(2026, 6, 1), date(2026, 6, 30)
    )
    assert total == Decimal("45000")


@pytest.mark.asyncio
async def test_filtro_fecha_inclusivo_en_limites(client, db_session):
    """#27: las fechas limite son inclusivas."""
    await _setup_catalogo(db_session)
    await _insertar_tx_con_tramo(db_session, monto=10000.0, tipo="gasto",
                                  estado="confirmado", fecha="2026-06-01")
    await _insertar_tx_con_tramo(db_session, monto=20000.0, tipo="gasto",
                                  estado="confirmado", fecha="2026-06-30")
    await db_session.commit()

    repo = PresupuestoRepository(db_session)
    total = await repo.obtener_gasto_acumulado_periodo(
        "CAT-ALIM", date(2026, 6, 1), date(2026, 6, 30)
    )
    assert total == Decimal("30000")
