"""
Tests de integracion: PresupuestoService.obtener_ejecucion,
obtener_resumen_por_categoria y benchmark_categoria.

A diferencia de test_presupuesto_repo.py (que prueba las queries sueltas),
estos tests prueban el service completo: como combina periodo financiero,
presupuestos, gasto acumulado y velocidad historica en el resultado final
que consume el frontend/PWA. Usan la DB en memoria real (fixture
db_session) en vez de mocks, porque el service arma varias queries
encadenadas y mockear cada una por separado seria mas fragil que los
datos reales.
"""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from freezegun import freeze_time

from backend.models.catalogo import Categoria
from backend.models.presupuesto import Presupuesto
from backend.models.periodo import PeriodoFinanciero
from backend.models.transaccion import Transaccion, Tramo
from backend.models.velocidad_historica import VelocidadHistorica
from backend.services.presupuesto_service import PresupuestoService


# ---------------------------------------------------------------------------
# Helpers (mismo patron que tests/integration/test_presupuesto_repo.py)
# ---------------------------------------------------------------------------

def _id() -> str:
    return str(uuid.uuid4())


async def _categoria(db, id_, nombre=None, nivel=1, id_padre=None, tipo_patron="variable_frecuente"):
    cat = Categoria(id=id_, nombre=nombre or id_, nivel=nivel, id_padre=id_padre,
                     activa=True, tipo_patron_gasto=tipo_patron)
    db.add(cat)
    await db.flush()
    return cat


async def _presupuesto(db, anio, mes, id_categoria, monto):
    pres = Presupuesto(id=_id(), anio=anio, mes=mes, id_categoria=id_categoria,
                       monto_presupuestado=Decimal(str(monto)))
    db.add(pres)
    await db.flush()
    return pres


async def _gasto(db, id_categoria, monto, fecha):
    tx_id = _id()
    tx = Transaccion(
        id=tx_id, fecha=fecha, tipo="gasto", estado="confirmado",
        revisado_humano=1, confianza=0.9, completitud="completo",
        id_categoria=id_categoria, es_reembolsable=0,
        creado_en=datetime.now(timezone.utc), actualizado_en=datetime.now(timezone.utc),
    )
    db.add(tx)
    await db.flush()
    db.add(Tramo(id_transaccion=tx_id, numero_orden=1, monto_origen=monto,
                  moneda_origen="COP", estado="confirmado"))
    await db.flush()


async def _velocidad(db, id_categoria, id_periodo, velocidad_diaria, monto_total=None, dias_periodo=30):
    db.add(VelocidadHistorica(
        id=_id(), id_categoria=id_categoria, id_periodo=id_periodo,
        monto_total=Decimal(str(monto_total if monto_total is not None else velocidad_diaria * dias_periodo)),
        dias_periodo=dias_periodo, velocidad_diaria=Decimal(str(velocidad_diaria)),
    ))
    await db.flush()


# ---------------------------------------------------------------------------
# obtener_ejecucion -- calculo de dias segun periodo financiero activo
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@freeze_time("2026-06-10")
async def test_obtener_ejecucion_usa_fechas_del_periodo_activo(db_session):
    """Con un periodo financiero abierto, dias_transcurridos/dias_totales
    salen de sus fechas (25-may a 24-jun), no del mes calendario."""
    db_session.add(PeriodoFinanciero(
        id="2026-06", anio=2026, mes=6,
        fecha_inicio=date(2026, 5, 25), fecha_fin_tentativa=date(2026, 6, 24),
        estado="abierto",
    ))
    await db_session.commit()

    resultado = await PresupuestoService(db_session).obtener_ejecucion(2026, 6)

    assert resultado["periodo"]["id"] == "2026-06"
    assert resultado["periodo"]["estado"] == "abierto"
    assert resultado["periodo"]["dias_transcurridos"] == 17  # 25-may a 10-jun, inclusive
    assert resultado["periodo"]["dias_totales"] == 31        # 25-may a 24-jun, inclusive


@pytest.mark.asyncio
@freeze_time("2026-07-10")
async def test_obtener_ejecucion_sin_periodo_cae_a_mes_calendario(db_session):
    """Sin periodo financiero abierto, usa el mes calendario (dia 1 a hoy)."""
    resultado = await PresupuestoService(db_session).obtener_ejecucion(2026, 7)

    assert resultado["periodo"]["id"] is None
    assert resultado["periodo"]["estado"] == "sin_configurar"
    assert resultado["periodo"]["dias_transcurridos"] == 10  # hoy.day
    assert resultado["periodo"]["dias_totales"] == 31        # julio tiene 31 dias


# ---------------------------------------------------------------------------
# obtener_ejecucion -- orden por nivel de riesgo y fallback de categoria
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@freeze_time("2026-08-10")
async def test_obtener_ejecucion_ordena_items_critico_alto_ok_fijo(db_session):
    """Los items deben salir ordenados: critico, alto, ok, fijo -- sin
    importar el orden en que se cargaron los presupuestos."""
    await _categoria(db_session, "CAT-OK", tipo_patron="variable_frecuente")
    await _categoria(db_session, "CAT-CRIT", tipo_patron="variable_frecuente")
    await _categoria(db_session, "CAT-FIJO", tipo_patron="fijo_unico")
    await _categoria(db_session, "CAT-ALTO", tipo_patron="variable_frecuente")

    for cat_id in ("CAT-OK", "CAT-CRIT", "CAT-FIJO", "CAT-ALTO"):
        await _presupuesto(db_session, 2026, 8, cat_id, 1000)

    # dias_transcurridos = 10 (fallback calendario). vel_hist = 10/dia para
    # las variables. vel_actual = gasto_acumulado / 10.
    await _velocidad(db_session, "CAT-OK", "2026-07", velocidad_diaria=10)
    await _velocidad(db_session, "CAT-CRIT", "2026-07", velocidad_diaria=10)
    await _velocidad(db_session, "CAT-ALTO", "2026-07", velocidad_diaria=10)

    await _gasto(db_session, "CAT-OK", 100, "2026-08-05")     # vel_actual=10 -> ratio 1.0 -> ok
    await _gasto(db_session, "CAT-CRIT", 200, "2026-08-05")   # vel_actual=20 -> ratio 2.0 -> critico
    await _gasto(db_session, "CAT-ALTO", 130, "2026-08-05")   # vel_actual=13 -> ratio 1.3 -> alto
    await db_session.commit()

    resultado = await PresupuestoService(db_session).obtener_ejecucion(2026, 8)

    assert [item["id_categoria"] for item in resultado["items"]] == [
        "CAT-CRIT", "CAT-ALTO", "CAT-OK", "CAT-FIJO",
    ]
    assert [item["nivel_riesgo"] for item in resultado["items"]] == [
        "critico", "alto", "ok", "fijo",
    ]


@pytest.mark.asyncio
@freeze_time("2026-09-15")
async def test_obtener_ejecucion_presupuesto_sin_categoria_usa_id_como_nombre(db_session):
    """Si el presupuesto apunta a una categoria que ya no existe en el
    catalogo, no debe romper: usa el id como nombre y el patron por defecto."""
    await _presupuesto(db_session, 2026, 9, "CAT-BORRADA", 1000)
    await db_session.commit()

    resultado = await PresupuestoService(db_session).obtener_ejecucion(2026, 9)

    assert len(resultado["items"]) == 1
    item = resultado["items"][0]
    assert item["nombre"] == "CAT-BORRADA"
    assert item["tipo_patron_gasto"] == "variable_frecuente"
    assert item["nivel_riesgo"] == "ok"  # sin velocidad historica -> ok


# ---------------------------------------------------------------------------
# obtener_resumen_por_categoria -- rollup jerarquico (Home de la PWA)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_resumen_por_categoria_suma_hijos_en_el_padre_sin_duplicar_el_total(db_session):
    """El padre debe mostrar su propio gasto + el de sus hijos, pero el
    total general no debe contar al hijo dos veces (solo suma nivel 1)."""
    await _categoria(db_session, "CAT-PADRE", nivel=1)
    await _categoria(db_session, "CAT-HIJO", nivel=2, id_padre="CAT-PADRE")

    await _presupuesto(db_session, 2026, 3, "CAT-PADRE", 2000)
    await _presupuesto(db_session, 2026, 3, "CAT-HIJO", 800)

    await _gasto(db_session, "CAT-PADRE", 1000, "2026-03-10")
    await _gasto(db_session, "CAT-HIJO", 500, "2026-03-12")
    await db_session.commit()

    # "Hoy" en otro mes -> marzo 2026 se trata como mes cerrado (mes completo).
    with freeze_time("2026-05-01"):
        resultado = await PresupuestoService(db_session).obtener_resumen_por_categoria(2026, 3)

    por_id = {item["id_categoria"]: item for item in resultado["categorias"]}
    assert por_id["CAT-HIJO"]["gasto_acumulado"] == 500.0
    assert por_id["CAT-PADRE"]["gasto_acumulado"] == 1500.0  # propio (1000) + hijo (500)
    assert por_id["CAT-PADRE"]["presupuesto"] == 2800.0      # propio (2000) + hijo (800)

    # El total general solo suma categorias de nivel 1 -- si sumara tambien
    # el hijo (que ya esta incluido en el padre) darian 2000, no 1500.
    assert resultado["total"]["gasto_acumulado"] == 1500.0
    assert resultado["total"]["presupuesto"] == 2800.0


@pytest.mark.asyncio
@freeze_time("2026-04-10")
async def test_resumen_por_categoria_mes_en_curso_no_cuenta_gastos_futuros(db_session):
    """Para el mes actual, el rango de gasto va del dia 1 a HOY (10-abr),
    no al mes completo -- un gasto cargado a fecha futura del mismo mes
    no debe sumarse todavia."""
    await _categoria(db_session, "CAT-X", nivel=1)
    await _gasto(db_session, "CAT-X", 300, "2026-04-05")   # antes de hoy -> cuenta
    await _gasto(db_session, "CAT-X", 999, "2026-04-15")   # despues de hoy -> no cuenta
    await db_session.commit()

    resultado = await PresupuestoService(db_session).obtener_resumen_por_categoria(2026, 4)

    item = next(i for i in resultado["categorias"] if i["id_categoria"] == "CAT-X")
    assert item["gasto_acumulado"] == 300.0


# ---------------------------------------------------------------------------
# benchmark_categoria
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_benchmark_categoria_sin_historico_devuelve_ceros(db_session):
    """Categoria sin ningun periodo cerrado todavia -- no debe romper, ceros."""
    resultado = await PresupuestoService(db_session).benchmark_categoria("CAT-NUEVA")
    assert resultado == {"ultimo_periodo": 0, "promedio_3p": 0, "promedio_6p": 0}


@pytest.mark.asyncio
async def test_benchmark_categoria_promedia_3_y_6_periodos(db_session):
    """Con 6 periodos historicos, promedio_3p usa los 3 mas recientes y
    promedio_6p los 6 -- ordenados por id_periodo descendente."""
    montos_por_periodo = [
        ("2026-01", 350, 10), ("2026-02", 400, 12), ("2026-03", 450, 14),
        ("2026-04", 500, 16), ("2026-05", 550, 18), ("2026-06", 600, 20),
    ]
    for id_periodo, monto, vel in montos_por_periodo:
        await _velocidad(db_session, "CAT-BENCH", id_periodo, velocidad_diaria=vel, monto_total=monto)
    await db_session.commit()

    resultado = await PresupuestoService(db_session).benchmark_categoria("CAT-BENCH")

    assert resultado["ultimo_periodo"] == 600.0                    # periodo mas reciente (2026-06)
    assert resultado["promedio_3p"] == 550.0                       # (600+550+500)/3
    assert resultado["promedio_6p"] == 475.0                       # promedio de los 6
    assert resultado["velocidad_diaria_promedio_3p"] == 18.0       # (20+18+16)/3
