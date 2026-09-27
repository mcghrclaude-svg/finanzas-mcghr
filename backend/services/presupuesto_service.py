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


def _mes_relativo(anio: int, mes: int, meses_atras: int) -> tuple[int, int]:
    """(anio, mes) - meses_atras, con acarreo de anio. mes es 1-12."""
    indice = (anio * 12 + (mes - 1)) - meses_atras
    return indice // 12, indice % 12 + 1


class PresupuestoService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PresupuestoRepository(db)

    async def _periodo_activo_y_fechas(self, anio: int, mes: int):
        """Resuelve el periodo financiero activo (o fallback a mes calendario)
        y las fechas/dias derivados que necesita el calculo de ejecucion.
        Compartido por obtener_ejecucion y obtener_ejecucion_subcategorias."""
        hoy = date.today()
        periodo = await self.repo.obtener_periodo_activo()

        if periodo:
            fecha_inicio = periodo.fecha_inicio
            fecha_hasta = min(hoy, periodo.fecha_fin_real or hoy)
            dias_transcurridos = (hoy - fecha_inicio).days + 1
            fecha_fin_ref = periodo.fecha_fin_real or periodo.fecha_fin_tentativa
            dias_totales = (fecha_fin_ref - fecha_inicio).days + 1
        else:
            fecha_inicio = date(anio, mes, 1)
            fecha_hasta = hoy
            dias_totales = calendar.monthrange(anio, mes)[1]
            dias_transcurridos = hoy.day

        dias_transcurridos = max(dias_transcurridos, 1)
        return periodo, fecha_inicio, fecha_hasta, dias_transcurridos, dias_totales

    async def _construir_item_ejecucion(
        self,
        id_categoria: str,
        nombre_fallback: str,
        cat: Categoria | None,
        monto_presupuestado: Decimal,
        fecha_inicio: date,
        fecha_hasta: date,
        dias_transcurridos: int,
        dias_totales: int,
    ) -> dict:
        """Calcula riesgo/velocidad/proyeccion para una categoria (o
        subcategoria) dada. `monto_presupuestado` puede ser 0 cuando no hay
        presupuesto cargado a ese nivel -- el resto de las cuentas sigue
        funcionando (pct_consumido/pct_esperado_hoy quedan en 0)."""
        tipo_patron = cat.tipo_patron_gasto if cat else "variable_frecuente"
        nombre = cat.nombre if cat else nombre_fallback

        gasto_acumulado = await self.repo.obtener_gasto_acumulado_periodo(
            id_categoria, fecha_inicio, fecha_hasta
        )

        hist = await self.repo.obtener_velocidad_historica(id_categoria, n_periodos=3)
        vel_hist: Decimal | None = None
        if hist:
            vel_hist = sum(h.velocidad_diaria for h in hist) / len(hist)

        vel_actual = gasto_acumulado / Decimal(dias_transcurridos)

        nivel_riesgo, ratio = self._calcular_riesgo(tipo_patron, vel_actual, vel_hist)
        monto_proyectado = self._calcular_proyeccion(
            vel_actual, vel_hist, dias_totales, tipo_patron, monto_presupuestado
        )
        pct_consumido = float(gasto_acumulado / monto_presupuestado) if monto_presupuestado else 0.0
        pct_esperado_hoy = self._calcular_pct_esperado(
            tipo_patron, vel_hist, monto_presupuestado, dias_transcurridos,
        )

        return {
            "id_categoria": id_categoria,
            "nombre": nombre,
            "tipo_patron_gasto": tipo_patron,
            "monto_presupuestado": float(monto_presupuestado),
            "gasto_acumulado": float(gasto_acumulado),
            "velocidad_actual": float(vel_actual),
            "velocidad_historica": float(vel_hist) if vel_hist is not None else None,
            "ratio_riesgo": float(ratio) if ratio is not None else None,
            "nivel_riesgo": nivel_riesgo,
            "pct_consumido": round(pct_consumido, 4),
            "pct_esperado_hoy": round(pct_esperado_hoy, 4),
            "monto_proyectado": float(monto_proyectado),
            # Próximo vencimiento (solo fijo_unico): lo calculamos desde obligaciones.
            # Por ahora None — el endpoint de obligaciones lo enriquece si es necesario.
            "proximo_vencimiento": None,
        }

    async def obtener_ejecucion(
        self,
        anio: int,
        mes: int,
    ) -> dict:
        """
        Construye la lista completa de items de ejecución de presupuesto
        para el período activo o el mes calendario dado.

        Enumera desde Presupuesto (no desde Categoria): en la práctica esto
        limita el resultado a categorías nivel-1 porque hoy solo se cargan
        presupuestos ahí. Para el drill-down a subcategorías ver
        obtener_ejecucion_subcategorias, que enumera desde Categoria y no
        requiere que exista un Presupuesto.

        Retorna estructura lista para serializar por el router.
        """
        periodo, fecha_inicio, fecha_hasta, dias_transcurridos, dias_totales = (
            await self._periodo_activo_y_fechas(anio, mes)
        )

        presupuestos = await self.repo.obtener_por_mes(anio, mes)

        cat_ids = [p.id_categoria for p in presupuestos]
        cats = {}
        if cat_ids:
            result = await self.db.execute(
                select(Categoria).where(Categoria.id.in_(cat_ids))
            )
            cats = {c.id: c for c in result.scalars().all()}

        items = []
        for pres in presupuestos:
            item = await self._construir_item_ejecucion(
                pres.id_categoria,
                pres.id_categoria,
                cats.get(pres.id_categoria),
                Decimal(str(pres.monto_presupuestado)),
                fecha_inicio, fecha_hasta, dias_transcurridos, dias_totales,
            )
            items.append(item)

        # Ordenar: critico → alto → ok → fijo
        orden = {"critico": 0, "alto": 1, "ok": 2, "fijo": 3}
        items.sort(key=lambda x: orden.get(x["nivel_riesgo"], 9))

        return {
            "periodo": self._serializar_periodo(periodo, fecha_inicio, dias_transcurridos, dias_totales),
            "items": items,
        }

    async def obtener_ejecucion_subcategorias(
        self,
        anio: int,
        mes: int,
        id_padre: str,
    ) -> dict:
        """
        Mismo cálculo de riesgo/velocidad/proyección que obtener_ejecucion,
        pero para las subcategorías (hijos directos) de `id_padre`. A
        diferencia de obtener_ejecucion, enumera desde Categoria (no desde
        Presupuesto): una subcategoría sin presupuesto cargado igual aparece,
        con monto_presupuestado=0 (sin marca de presupuesto en la UI) en vez
        de quedar afuera. Usado por el drill-down del widget de Home.
        """
        periodo, fecha_inicio, fecha_hasta, dias_transcurridos, dias_totales = (
            await self._periodo_activo_y_fechas(anio, mes)
        )

        result = await self.db.execute(
            select(Categoria).where(
                Categoria.id_padre == id_padre,
                Categoria.activa == True,  # noqa: E712
            )
        )
        hijos = result.scalars().all()

        presupuestos = await self.repo.obtener_por_mes(anio, mes)
        presupuesto_por_cat = {
            p.id_categoria: Decimal(str(p.monto_presupuestado)) for p in presupuestos
        }

        items = []
        for cat in hijos:
            monto_presupuestado = presupuesto_por_cat.get(cat.id, Decimal(0))
            item = await self._construir_item_ejecucion(
                cat.id, cat.nombre, cat, monto_presupuestado,
                fecha_inicio, fecha_hasta, dias_transcurridos, dias_totales,
            )
            items.append(item)

        orden = {"critico": 0, "alto": 1, "ok": 2, "fijo": 3}
        items.sort(key=lambda x: orden.get(x["nivel_riesgo"], 9))

        return {
            "periodo": self._serializar_periodo(periodo, fecha_inicio, dias_transcurridos, dias_totales),
            "id_padre": id_padre,
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

    async def obtener_resumen_por_categoria(self, anio: int, mes: int) -> dict:
        """
        Resumen para el Home de la PWA: por cada categoria (nivel 1/2/3,
        lista plana -- el frontend arma el arbol), gasto acumulado del mes
        calendario (dia 1 al dia de hoy si es el mes actual), presupuesto
        del mes, y promedio del total gastado en los ultimos 3 meses
        calendario. Una categoria con hijos suma su propio valor (si tiene
        presupuesto/gasto asignado directo) + el de todos sus descendientes.
        """
        hoy = date.today()
        fecha_inicio_mes = date(anio, mes, 1)
        if (anio, mes) == (hoy.year, hoy.month):
            fecha_hasta_mes = hoy
        else:
            fecha_hasta_mes = date(anio, mes, calendar.monthrange(anio, mes)[1])

        anio_3m_atras, mes_3m_atras = _mes_relativo(anio, mes, 3)
        anio_1m_atras, mes_1m_atras = _mes_relativo(anio, mes, 1)
        fecha_inicio_3m = date(anio_3m_atras, mes_3m_atras, 1)
        fecha_fin_3m = date(anio_1m_atras, mes_1m_atras, calendar.monthrange(anio_1m_atras, mes_1m_atras)[1])

        categorias = await self.repo.listar_categorias_activas()
        gasto_mes = await self.repo.obtener_gasto_por_categoria_rango(fecha_inicio_mes, fecha_hasta_mes)
        gasto_3m = await self.repo.obtener_gasto_por_categoria_rango(fecha_inicio_3m, fecha_fin_3m)
        presupuestos = await self.repo.obtener_por_mes(anio, mes)
        presupuesto_por_cat = {p.id_categoria: Decimal(str(p.monto_presupuestado)) for p in presupuestos}

        hijos_por_padre: dict[str | None, list[Categoria]] = {}
        for cat in categorias:
            hijos_por_padre.setdefault(cat.id_padre, []).append(cat)

        cero = Decimal(0)
        totales: dict[str, dict[str, Decimal]] = {}

        def calcular(cat: Categoria) -> dict[str, Decimal]:
            propio = {
                "gasto_acumulado": gasto_mes.get(cat.id, cero),
                "presupuesto": presupuesto_por_cat.get(cat.id, cero),
                "promedio_ultimos_3_meses": gasto_3m.get(cat.id, cero) / Decimal(3),
            }
            for hijo in hijos_por_padre.get(cat.id, []):
                hijo_total = calcular(hijo)
                for clave in propio:
                    propio[clave] += hijo_total[clave]
            totales[cat.id] = propio
            return propio

        for raiz in hijos_por_padre.get(None, []):
            calcular(raiz)

        items = [
            {
                "id_categoria": cat.id,
                "nivel": cat.nivel,
                "id_padre": cat.id_padre,
                "nombre": cat.nombre,
                **{k: float(v) for k, v in totales.get(cat.id, {
                    "gasto_acumulado": gasto_mes.get(cat.id, cero),
                    "presupuesto": presupuesto_por_cat.get(cat.id, cero),
                    "promedio_ultimos_3_meses": gasto_3m.get(cat.id, cero) / Decimal(3),
                }).items()},
            }
            for cat in categorias
        ]

        categorias_nivel1 = [c for c in categorias if c.nivel == 1]
        total = {
            "gasto_acumulado": float(sum((totales[c.id]["gasto_acumulado"] for c in categorias_nivel1), cero)),
            "presupuesto": float(sum((totales[c.id]["presupuesto"] for c in categorias_nivel1), cero)),
            "promedio_ultimos_3_meses": float(
                sum((totales[c.id]["promedio_ultimos_3_meses"] for c in categorias_nivel1), cero)
            ),
        }

        return {
            "mes": {"anio": anio, "mes": mes},
            "total": total,
            "categorias": items,
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
