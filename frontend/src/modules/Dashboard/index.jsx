/**
 * Dashboard — página principal de la plataforma financiera MCGHR.
 * Usa Tailwind CSS. Sin clases custom externas.
 *
 * Importa subcomponentes locales en ./components/
 * Hook de datos: @/hooks/useDashboard
 */
import { useState, useMemo } from 'react'
import { useDashboard, formatCOP } from '@/hooks/useDashboard'
import MetricCard from './components/MetricCard'
import BudgetCard from './components/BudgetCard'
import IngresosPanel from './components/IngresosPanel'
import ObligacionesPanel from './components/ObligacionesPanel'

const CARDS_DEFAULT = 3
const RIESGO_ORDEN = { critico: 0, alto: 1, ok: 2, sin_datos: 3, fijo: 4 }

export default function Dashboard() {
  const hoy = new Date()
  const { resumen, ejecucion, ingresos, obligaciones, loading, error, refetch } =
    useDashboard(hoy.getFullYear(), hoy.getMonth() + 1)

  const [pinnedIds, setPinnedIds] = useState(new Set())
  const [expanded, setExpanded] = useState(false)

  const itemsOrdenados = useMemo(() => {
    if (!ejecucion?.items) return []
    return [...ejecucion.items].sort((a, b) => {
      const aPin = pinnedIds.has(a.id_categoria) ? -1 : 0
      const bPin = pinnedIds.has(b.id_categoria) ? -1 : 0
      if (aPin !== bPin) return aPin - bPin
      return (RIESGO_ORDEN[a.nivel_riesgo] ?? 9) - (RIESGO_ORDEN[b.nivel_riesgo] ?? 9)
    })
  }, [ejecucion, pinnedIds])

  const itemsVisibles = expanded ? itemsOrdenados : itemsOrdenados.slice(0, CARDS_DEFAULT)

  function togglePin(id) {
    setPinnedIds(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const periodo = resumen?.periodo
  const fechaFinTentativa = periodo?.fecha_fin_real == null

  if (loading) return (
    <div className="flex items-center justify-center h-64 text-gray-400 text-sm">
      Cargando dashboard…
    </div>
  )
  if (error) return (
    <div className="flex items-center justify-center h-64 text-red-400 text-sm">
      Error: {error}
    </div>
  )

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">

      {/* ── Top bar ───────────────────────────────────────────────── */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-lg font-semibold text-gray-100 capitalize">
            {hoy.toLocaleString('es-CO', { month: 'long', year: 'numeric' })}
          </h1>
          <p className="text-xs text-gray-400 mt-0.5">
            {periodo?.dias_transcurridos} de {periodo?.dias_totales} días
            {' · '}
            {periodo?.fecha_inicio} →{' '}
            <span className={fechaFinTentativa ? 'italic text-gray-500' : ''}>
              {periodo?.fecha_fin_tentativa}{fechaFinTentativa ? '*' : ''}
            </span>
            {fechaFinTentativa && (
              <span
                className="ml-1 text-gray-500 cursor-help"
                title="Fecha de cierre tentativa — se confirma al acreditarse el salario."
              >?</span>
            )}
          </p>
        </div>
        <button
          onClick={refetch}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-xs text-gray-300 transition-colors"
        >
          📥 {resumen?.inbox_pendiente_count ?? 0} gastos x catalogar
        </button>
      </div>

      {/* ── 4 métricas ───────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Ingresos acreditados"
          value={formatCOP(resumen?.ingresos_acreditados)}
          sub={`Acred. ${periodo?.fecha_inicio ?? ''}`}
        />
        <MetricCard
          label="Gastos a hoy"
          value={formatCOP(resumen?.gastos_acumulados)}
          sub={`Proy. ${formatCOP(
            resumen ? resumen.ingresos_acreditados - resumen.saldo_proyectado_cierre : null
          )} al cierre`}
          subVariant="warning"
        />
        <MetricCard
          label="Saldo proy. al cierre"
          value={formatCOP(resumen?.saldo_proyectado_cierre)}
          sub={`Disponible hoy: ${formatCOP(resumen?.saldo_disponible_hoy)}`}
          tentative
        />
        <MetricCard
          label="Patrimonio neto"
          value={formatCOP(resumen?.patrimonio_neto)}
          sub={`+${formatCOP(resumen?.variacion_patrimonio_mes_anterior)} vs mes ant.`}
          subVariant="success"
        />
      </div>

      {/* ── Presupuesto x categoría ────────────────────────────────────────── */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">
            Status de presupuesto x categoría
          </span>
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-500">Por riesgo</span>
            <button
              onClick={() => setExpanded(e => !e)}
              className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
            >
              {expanded
                ? '↑ Mostrar menos'
                : `↓ Ver todas (${itemsOrdenados.length})`}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {itemsVisibles.map(item => (
            <BudgetCard
              key={item.id_categoria}
              item={item}
              pinned={pinnedIds.has(item.id_categoria)}
              onPin={() => togglePin(item.id_categoria)}
            />
          ))}
        </div>
      </div>

      {/* ── Ingresos + Obligaciones ─────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <IngresosPanel
          ingresos={ingresos}
          totalAcreditado={resumen?.ingresos_acreditados}
        />
        <ObligacionesPanel obligaciones={obligaciones} />
      </div>

      {/* ── Pregunta a Claude ───────────────────────────────────────────── */}
      <button className="w-full py-2.5 rounded-xl bg-gray-800 hover:bg-gray-700 text-xs text-gray-400 hover:text-gray-300 transition-colors text-left px-4">
        🤖 Preguntarle a Claude: ¿por qué restaurantes está en riesgo crítico? ↗
      </button>

    </div>
  )
}
