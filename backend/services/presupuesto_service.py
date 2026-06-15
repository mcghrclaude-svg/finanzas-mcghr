"""
PresupuestoService — lógica de negocio para ejecución de presupuesto y riesgo.

Riesgo por velocidad (categorías variable_*):
    ratio = velocidad_actual / velocidad_hist_promedio
    > 1.5  → critico
    > 1.2  → alto
    <= 1.2 → ok

Proyección suavizada:
    vel_suavizada = vel_actual * 0.7 + vel_hist * 0.3
    proyectado = vel_suavizada * dias_totales_periodo

Línea punteada (pct_esperado_hoy):
    gasto_esperado_hoy = vel_hist * dias_transcurridos
    pct_esperado = gasto_esperado_hoy / monto_presupuestado
"""

import calendar
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.presupuesto_repo import PresupuestoRepository
from backend.models.catalogo import Categoria
from sqlalchemy import select

# Thresholds
UMBRAL_CRITICO = 1.5
UMBRAL_ALTO = 1.2
FACTOR_ACTUAL = Decimal("0.7")
FACTOR_HIST = Decimal("0.3")


class PresupuestoService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PresupuestoRepository(db)

    async def obtener_ejecucion(
        self,
        anio: int,
        mes: int,
    ) -> dict:
        """
        Construye la lista completa de items de ejecución de presupuesto
        para el período activo o el mes calendario dado.

        Retorna estructura lista para serializar por el router.
        """
        hoy = date.today()

        # Período financiero activo
        periodo = await self.repo.obtener_periodo_activo()

        if periodo:
            fecha_inicio = periodo.fecha_inicio
            # hasta hoy o fecha_fin_real, lo que sea menor
            fecha_hasta = min(hoy, periodo.fecha_fin_real or hoy)
            dias_transcurridos = (hoy - fecha_inicio).days + 1
            # dias totales: si hay fecha_fin_real usamos real, sino tentativa
            fecha_fin_ref = periodo.fecha_fin_real or periodo.fecha_fin_tentativa
            dias_totales = (fecha_fin_ref - fecha_inicio).days + 1
        else:
            # Fallback a mes calendario
            fecha_inicio = date(anio, mes, 1)
            fecha_hasta = hoy
            dias_totales = calendar.monthrange(anio, mes)[1]
            dias_transcurridos = hoy.day

        dias_transcurridos = max(dias_transcurridos, 1)

        # Presupuestos del mes
        presupuestos = await self.repo.obtener_por_mes(anio, mes)

        # Cargar categorias en un dict
        cat_ids = [p.id_categoria for p in presupuestos]
        cats = {}
        if cat_ids:
            result = await self.db.execute(
                select(Categoria).where(Categoria.id.in_(cat_ids))
            )
            cats = {c.id: c for c in result.scalars().all()}

        items = []
        for pres in presupuestos:
            cat = cats.get(pres.id_categoria)
            tipo_patron = cat.tipo_patron_gasto if cat else "variable_frecuente"
            nombre = cat.nombre if cat else pres.id_categoria

            # Gasto acumulado hasta hoy en el período
            gasto_acumulado = await self.repo.obtener_gasto_acumulado_periodo(
                pres.id_categoria, fecha_inicio, fecha_hasta
            )

            # Velocidad histórica promedio (3 períodos anteriores)
            hist = await self.repo.obtener_velocidad_historica(pres.id_categoria, n_periodos=3)
            vel_hist: Decimal | None = None
            if hist:
                vel_hist = sum(h.velocidad_diaria for h in hist) / len(hist)

            # Velocidad actual
            vel_actual = gasto_acumulado / Decimal(dias_transcurridos)

            # Riesgo y proyección
            nivel_riesgo, ratio = self._calcular_riesgo(tipo_patron, vel_actual, vel_hist)
            monto_proyectado = self._calcular_proyeccion(
                vel_actual, vel_hist, dias_totales, tipo_patron,
                Decimal(str(pres.monto_presupuestado))
            )
            pct_consumido = float(
                gasto_acumulado / Decimal(str(pres.monto_presupuestado))
            ) if pres.monto_presupuestado else 0
            pct_esperado_hoy = self._calcular_pct_esperado(
                tipo_patron, vel_hist,
                Decimal(str(pres.monto_presupuestado)),
                dias_transcurridos,
            )

            # Próximo vencimiento (solo fijo_unico): lo calculamos desde obligaciones
            # Por ahora None — el endpoint de obligaciones lo enriquece si es necesario
            proximo_vencimiento = None

            items.append({
                "id_categoria": pres.id_categoria,
                "nombre": nombre,
                "tipo_patron_gasto": tipo_patron,
                "monto_presupuestado": float(pres.monto_presupuestado),
                "gasto_acumulado": float(gasto_acumulado),
                "velocidad_actual": float(vel_actual),
                "velocidad_historica": float(vel_hist) if vel_hist is not None else None,
                "ratio_riesgo": float(ratio) if ratio is not None else None,
                "nivel_riesgo": nivel_riesgo,
                "pct_consumido": round(pct_consumido, 4),
                "pct_esperado_hoy": round(pct_esperado_hoy, 4),
                "monto_proyectado": float(monto_proyectado),
                "proximo_vencimiento": proximo_vencimiento,
            })

        # Ordenar: critico → alto → ok → fijo
        orden = {"critico": 0, "alto": 1, "ok": 2, "fijo": 3}
        items.sort(key=lambda x: orden.get(x["nivel_riesgo"], 9))

        return {
            "periodo": self._serializar_periodo(periodo, fecha_inicio, dias_transcurridos, dias_totales),
            "items": items,
        }

    def _calcular_riesgo(
        self,
        tipo_patron: str,
        vel_actual: Decimal,
        vel_hist: Decimal | None,
    ) -> tuple[str, float | None]:
        if tipo_patron in ("fijo_unico", "fijo_recurrente"):
            return "fijo", None
        if vel_hist is None or vel_hist == 0:
            return "ok", None
        ratio = float(vel_actual / vel_hist)
        if ratio > UMBRAL_CRITICO:
            return "critico", ratio
        if ratio > UMBRAL_ALTO:
            return "alto", ratio
        return "ok", ratio

    def _calcular_proyeccion(
        self,
        vel_actual: Decimal,
        vel_hist: Decimal | None,
        dias_totales: int,
        tipo_patron: str,
        monto_presupuestado: Decimal,
    ) -> Decimal:
        if tipo_patron == "fijo_unico":
            return monto_presupuestado
        if vel_hist and vel_hist > 0:
            vel_suavizada = vel_actual * FACTOR_ACTUAL + vel_hist * FACTOR_HIST
        else:
            vel_suavizada = vel_actual
        return vel_suavizada * Decimal(dias_totales)

    def _calcular_pct_esperado(
        self,
        tipo_patron: str,
        vel_hist: Decimal | None,
        monto_presupuestado: Decimal,
        dias_transcurridos: int,
    ) -> float:
        if tipo_patron == "fijo_unico":
            return 0.0
        if vel_hist and vel_hist > 0 and monto_presupuestado > 0:
            gasto_esperado = vel_hist * Decimal(dias_transcurridos)
            return min(float(gasto_esperado / monto_presupuestado), 1.0)
        return 0.5  # fallback: 50% si no hay histórico

    def _serializar_periodo(self, periodo, fecha_inicio, dias_transcurridos, dias_totales) -> dict:
        if periodo:
            return {
                "id": periodo.id,
                "fecha_inicio": str(periodo.fecha_inicio),
                "fecha_fin_tentativa": str(periodo.fecha_fin_tentativa),
                "fecha_fin_real": str(periodo.fecha_fin_real) if periodo.fecha_fin_real else None,
                "estado": periodo.estado,
                "dias_transcurridos": dias_transcurridos,
                "dias_totales": dias_totales,
            }
        return {
            "id": None,
            "fecha_inicio": str(fecha_inicio),
            "fecha_fin_tentativa": None,
            "fecha_fin_real": None,
            "estado": "sin_configurar",
            "dias_transcurridos": dias_transcurridos,
            "dias_totales": dias_totales,
        }

    async def benchmark_categoria(self, id_categoria: str) -> dict:
        hist = await self.repo.obtener_velocidad_historica(id_categoria, n_periodos=6)
        if not hist:
            return {"ultimo_periodo": 0, "promedio_3p": 0, "promedio_6p": 0}
        velocidades = [float(h.velocidad_diaria) for h in hist]
        dias = [h.dias_periodo for h in hist]
        montos = [float(h.monto_total) for h in hist]
        return {
            "ultimo_periodo": montos[0] if montos else 0,
            "promedio_3p": sum(montos[:3]) / len(montos[:3]) if montos[:3] else 0,
            "promedio_6p": sum(montos) / len(montos) if montos else 0,
            "velocidad_diaria_promedio_3p": sum(velocidades[:3]) / len(velocidades[:3]) if velocidades[:3] else 0,
        }
