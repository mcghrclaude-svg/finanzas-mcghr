"""
Tests unitarios: PresupuestoService -- motor de riesgo y proyeccion.

Cubre los tres metodos privados que son el "cerebro" de los indicadores
de presupuesto (Home de la PWA y dashboard):
    _calcular_riesgo       -- nivel (critico/alto/ok/fijo) segun velocidad de gasto
    _calcular_proyeccion    -- monto proyectado al cierre del periodo
    _calcular_pct_esperado  -- linea punteada de gasto esperado a hoy

Son funciones puras sobre Decimal -- no tocan self.db ni self.repo, por
eso se instancia el service con db=None y se llaman directo, sin mocks
ni fixtures de base de datos.

Nota: reemplaza al test_presupuesto_service.py anterior, que probaba un
metodo obtener_ejecucion_mes()/factor_proyeccion que nunca llego a
implementarse asi (quedo de un boceto temprano, antes de que la logica
real -- la de este archivo -- se escribiera en obtener_ejecucion()).
"""

from decimal import Decimal

from backend.services.presupuesto_service import PresupuestoService


def _service() -> PresupuestoService:
    return PresupuestoService(db=None)


# ---------------------------------------------------------------------------
# _calcular_riesgo
# ---------------------------------------------------------------------------

def test_riesgo_fijo_unico_siempre_es_fijo():
    """Un pago unico (arriendo, cuota) no se evalua por velocidad -- va directo a 'fijo'."""
    nivel, ratio = _service()._calcular_riesgo("fijo_unico", Decimal("999999"), Decimal("1"))
    assert nivel == "fijo"
    assert ratio is None


def test_riesgo_fijo_recurrente_siempre_es_fijo():
    """Igual que fijo_unico -- un cobro automatico mensual tampoco compara velocidad."""
    nivel, ratio = _service()._calcular_riesgo("fijo_recurrente", Decimal("999999"), Decimal("1"))
    assert nivel == "fijo"
    assert ratio is None


def test_riesgo_sin_historico_es_ok():
    """Categoria nueva sin velocidad historica: no hay con que comparar, cae en 'ok'."""
    nivel, ratio = _service()._calcular_riesgo("variable_frecuente", Decimal("500"), None)
    assert nivel == "ok"
    assert ratio is None


def test_riesgo_historico_cero_es_ok():
    """Guard contra division por cero cuando la velocidad historica es 0."""
    nivel, ratio = _service()._calcular_riesgo("variable_frecuente", Decimal("500"), Decimal("0"))
    assert nivel == "ok"
    assert ratio is None


def test_riesgo_critico_sobre_umbral_1_5():
    nivel, ratio = _service()._calcular_riesgo("variable_frecuente", Decimal("160"), Decimal("100"))
    assert nivel == "critico"
    assert ratio == 1.6


def test_riesgo_alto_entre_1_2_y_1_5():
    nivel, ratio = _service()._calcular_riesgo("variable_frecuente", Decimal("130"), Decimal("100"))
    assert nivel == "alto"
    assert ratio == 1.3


def test_riesgo_ok_bajo_1_2():
    nivel, ratio = _service()._calcular_riesgo("variable_frecuente", Decimal("110"), Decimal("100"))
    assert nivel == "ok"
    assert ratio == 1.1


def test_riesgo_limite_exacto_1_2_no_es_alto():
    """El umbral alto es estrictamente '>' -- ratio==1.2 todavia cae en 'ok'."""
    nivel, _ = _service()._calcular_riesgo("variable_frecuente", Decimal("120"), Decimal("100"))
    assert nivel == "ok"


def test_riesgo_limite_exacto_1_5_no_es_critico():
    """Idem umbral critico -- ratio==1.5 cae en 'alto', no en 'critico'."""
    nivel, _ = _service()._calcular_riesgo("variable_frecuente", Decimal("150"), Decimal("100"))
    assert nivel == "alto"


# ---------------------------------------------------------------------------
# _calcular_proyeccion
# ---------------------------------------------------------------------------

def test_proyeccion_fijo_unico_devuelve_el_presupuestado_sin_importar_velocidad():
    """Un pago unico proyecta el monto presupuestado tal cual, ignora velocidad."""
    resultado = _service()._calcular_proyeccion(
        vel_actual=Decimal("999"), vel_hist=Decimal("1"),
        dias_totales=30, tipo_patron="fijo_unico",
        monto_presupuestado=Decimal("1500000"),
    )
    assert resultado == Decimal("1500000")


def test_proyeccion_pondera_actual_70_historico_30():
    """vel_suavizada = actual*0.7 + historico*0.3; proyectado = vel_suavizada * dias_totales."""
    resultado = _service()._calcular_proyeccion(
        vel_actual=Decimal("100"), vel_hist=Decimal("50"),
        dias_totales=30, tipo_patron="variable_frecuente",
        monto_presupuestado=Decimal("2000"),
    )
    vel_suavizada_esperada = Decimal("100") * Decimal("0.7") + Decimal("50") * Decimal("0.3")
    assert resultado == vel_suavizada_esperada * 30


def test_proyeccion_sin_historico_usa_solo_velocidad_actual():
    """Categoria nueva sin historico: proyecta solo con la velocidad actual."""
    resultado = _service()._calcular_proyeccion(
        vel_actual=Decimal("100"), vel_hist=None,
        dias_totales=30, tipo_patron="variable_frecuente",
        monto_presupuestado=Decimal("2000"),
    )
    assert resultado == Decimal("100") * 30


def test_proyeccion_historico_cero_se_trata_como_sin_historico():
    """Guard contra division/ponderacion invalida cuando el historico es 0."""
    resultado = _service()._calcular_proyeccion(
        vel_actual=Decimal("100"), vel_hist=Decimal("0"),
        dias_totales=30, tipo_patron="variable_frecuente",
        monto_presupuestado=Decimal("2000"),
    )
    assert resultado == Decimal("100") * 30


# ---------------------------------------------------------------------------
# _calcular_pct_esperado
# ---------------------------------------------------------------------------

def test_pct_esperado_fijo_unico_es_cero():
    """Un pago unico no tiene 'linea punteada' de gasto esperado dia a dia."""
    pct = _service()._calcular_pct_esperado(
        "fijo_unico", Decimal("100"), Decimal("2000"), dias_transcurridos=15,
    )
    assert pct == 0.0


def test_pct_esperado_calcula_gasto_esperado_sobre_presupuesto():
    """gasto_esperado_hoy = vel_hist * dias_transcurridos; pct = eso / presupuesto."""
    pct = _service()._calcular_pct_esperado(
        "variable_frecuente", Decimal("50"), Decimal("1000"), dias_transcurridos=10,
    )
    assert pct == 0.5  # (50*10) / 1000


def test_pct_esperado_se_recorta_a_100_por_ciento():
    """Si lo esperado ya supera el presupuesto, no debe pasar de 1.0 (100%)."""
    pct = _service()._calcular_pct_esperado(
        "variable_frecuente", Decimal("200"), Decimal("1000"), dias_transcurridos=10,
    )
    assert pct == 1.0  # (200*10)/1000 = 2.0, recortado a 1.0


def test_pct_esperado_sin_historico_cae_a_fallback_50_por_ciento():
    """Sin velocidad historica no hay forma de estimar -- fallback fijo de 50%."""
    pct = _service()._calcular_pct_esperado(
        "variable_frecuente", None, Decimal("1000"), dias_transcurridos=10,
    )
    assert pct == 0.5


def test_pct_esperado_presupuesto_cero_cae_a_fallback_50_por_ciento():
    """Guard contra division por cero cuando el presupuesto es 0."""
    pct = _service()._calcular_pct_esperado(
        "variable_frecuente", Decimal("50"), Decimal("0"), dias_transcurridos=10,
    )
    assert pct == 0.5
