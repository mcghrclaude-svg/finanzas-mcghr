"""
PresupuestoService — lógica de negocio para ejecución de presupuesto y riesgo.

Riesgo por velocidad de gasto (para categorías variable_frecuente / variable_esporadico):
    velocidad_actual  = gasto_acumulado / dias_transcurridos_en_periodo
    velocidad_hist    = promedio(velocidad_diaria últimos 3 períodos)
    ratio             = velocidad_actual / velocidad_hist

    ratio > 1.5  → CRÍTICO  (riesgo="critico",  color=rojo)
    ratio > 1.2  → ALTO     (riesgo="alto",     color=amarillo)
    ratio <= 1.2 → OK       (riesgo="ok",       color=verde)

Para categorías fijo_unico / fijo_recurrente:
    No se calcula ratio. Se retorna riesgo="fijo" + próximo_vencimiento.

Proyección al cierre del período:
    Usamos velocidad_actual (no factor lineal simple) para proyectar:
        monto_proyectado = velocidad_actual * dias_totales_periodo
    Si velocidad_hist disponible, ajustamos hacia el histórico con factor de suavizado:
        monto_proyectado = (velocidad_actual * 0.7 + velocidad_hist * 0.3) * dias_totales
    Esto evita que un día con gasto alto explote la proyección innecesariamente.
"""

import calendar
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from backend.repositories.presupuesto_repo import PresupuestoRepository

# Thresholds de riesgo
UMBRAL_CRITICO = 1.5
UMBRAL_ALTO = 1.2

# Factor de suavizado para proyección (cuánto peso tiene la vel. actual vs histórica)
FACTOR_SUAVIZADO_ACTUAL = 0.7
FACTOR_SUAVIZADO_HIST = 0.3


class PresupuestoService:
    def __init__(self, db: AsyncSession):
        self.repo = PresupuestoRepository(db)

    async def obtener_ejecucion_mes(
        self,
        anio: int,
        mes: int,
        id_periodo: str | None = None,
    ) -> dict:
        """
        Para cada categoría con presupuesto en el mes:
            - monto presupuestado
            - gasto real acumulado hasta hoy
            - velocidad actual (gasto / días transcurridos en período)
            - velocidad histórica (prom. 3 períodos anteriores)
            - ratio de riesgo
            - nivel de riesgo (critico | alto | ok | fijo)
            - monto proyectado al cierre del período
            - días hasta vencimiento (para fijo_unico)

        Si id_periodo se provee, usa las fechas reales del período financiero.
        Si no, usa el mes calendario (fallback para períodos no configurados).
        """
        hoy = date.today()
        dias_del_mes = calendar.monthrange(anio, mes)[1]
        dias_transcurridos = hoy.day
        # Factor de proyección lineal (solo usado como fallback cuando no hay hist.)
        factor_lineal = dias_del_mes / dias_transcurridos if dias_transcurridos > 0 else 1

        # TODO: implementar query real contra presupuestos + transacciones + velocidad_historica
        # Estructura esperada de cada item:
        # {
        #   "id_categoria": str,
        #   "nombre_categoria": str,
        #   "tipo_patron_gasto": str,
        #   "color_categoria": str,
        #   "monto_presupuestado": Decimal,
        #   "gasto_acumulado": Decimal,
        #   "velocidad_actual": Decimal,       # gasto/dia
        #   "velocidad_historica": Decimal,    # prom 3P o None
        #   "ratio_riesgo": float,             # None para fijo_unico
        #   "nivel_riesgo": str,               # critico|alto|ok|fijo
        #   "pct_consumido": float,            # 0.0–1.0+
        #   "pct_esperado_hoy": float,         # línea punteada del dashboard
        #   "monto_proyectado": Decimal,
        #   "proximo_vencimiento": date|None,  # solo fijo_unico
        # }
        return {
            "factor_proyeccion_lineal": factor_lineal,
            "dias_transcurridos": dias_transcurridos,
            "dias_del_mes": dias_del_mes,
            "items": [],
        }

    def calcular_riesgo(
        self,
        tipo_patron: str,
        velocidad_actual: float,
        velocidad_historica: float | None,
    ) -> tuple[str, float | None]:
        """
        Retorna (nivel_riesgo, ratio).
        nivel_riesgo: 'critico' | 'alto' | 'ok' | 'fijo'
        ratio: float | None  (None para categorías fijas)
        """
        if tipo_patron in ("fijo_unico", "fijo_recurrente"):
            return "fijo", None

        if velocidad_historica is None or velocidad_historica == 0:
            # Sin histórico: no podemos calcular ratio, usamos fallback ok
            return "ok", None

        ratio = velocidad_actual / velocidad_historica
        if ratio > UMBRAL_CRITICO:
            return "critico", ratio
        elif ratio > UMBRAL_ALTO:
            return "alto", ratio
        else:
            return "ok", ratio

    def calcular_proyeccion(
        self,
        gasto_acumulado: float,
        velocidad_actual: float,
        velocidad_historica: float | None,
        dias_totales_periodo: int,
        tipo_patron: str,
        monto_presupuestado: float,
    ) -> float:
        """
        Proyección al cierre del período usando velocidad suavizada.
        Para fijo_unico retorna directamente el monto presupuestado (ya sabemos el importe).
        """
        if tipo_patron == "fijo_unico":
            return monto_presupuestado

        if velocidad_historica and velocidad_historica > 0:
            velocidad_suavizada = (
                velocidad_actual * FACTOR_SUAVIZADO_ACTUAL
                + velocidad_historica * FACTOR_SUAVIZADO_HIST
            )
        else:
            velocidad_suavizada = velocidad_actual

        return velocidad_suavizada * dias_totales_periodo

    def calcular_pct_esperado_hoy(
        self,
        tipo_patron: str,
        velocidad_historica: float | None,
        monto_presupuestado: float,
        dias_transcurridos: int,
        dias_totales: int,
    ) -> float:
        """
        % esperado a hoy según patrón histórico — posición de la línea punteada
        vertical en la barra de progreso del dashboard.

        Para categorías sin histórico: usa distribución lineal (dias_trans/dias_total).
        Para fijo_unico: 0% hasta el día de vencimiento, 100% después.
        """
        if tipo_patron == "fijo_unico":
            # La línea punteada no aplica — el widget muestra badge de vencimiento
            return 0.0

        if velocidad_historica and monto_presupuestado > 0:
            gasto_esperado_hoy = velocidad_historica * dias_transcurridos
            return min(gasto_esperado_hoy / monto_presupuestado, 1.0)

        # Fallback lineal
        return dias_transcurridos / dias_totales if dias_totales > 0 else 0.0

    async def benchmark_categoria(self, id_categoria: str) -> dict:
        """
        Gasto histórico de la categoría: último período, prom. 3P, prom. 6P.
        Mostrado al usuario al definir el presupuesto de una categoría.
        """
        # TODO: implementar query contra velocidad_historica
        return {"ultimo_periodo": 0, "promedio_3p": 0, "promedio_6p": 0}
