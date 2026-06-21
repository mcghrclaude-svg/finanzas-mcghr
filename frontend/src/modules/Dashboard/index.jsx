/**
 * modules/Dashboard/index.jsx v3
 *
 * Cambios:
 *   - Badge "N gastos x catalogar" consume conteo real del backend (/inbox/stats)
 *   - Click en el badge navega a /transacciones
 *   - Sin padding propio en el contenedor raiz (el Layout ya no tiene p-6)
 */
import { useState, useMemo, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDashboard, formatCOP } from '@/hooks/useDashboard'
import MetricCard from './components/MetricCard'
import BudgetCard from './components/BudgetCard'
import IngresosPanel from './components/IngresosPanel'
import ObligacionesPanel from './components/ObligacionesPanel'
import client from '@/api/client'

const CARDS_DEFAULT = 3

export default function Dashboard() {
  const navigate = useNavigate()
  const hoy = new Date()
  const { resumen, ejecucion, ingresos, obligaciones, loading, error } =
    useDashboard(hoy.getFullYear(), hoy.getMonth() + 1)

  // Conteo real de pendientes desde /inbox/stats
  const [pendingCount, setPendingCount] = useState(null)
  useEffect(() => {
    client.get('/inbox/stats')
      .then(r => setPendingCount(r.data?.pendiente ?? r.data?.total_pendiente ?? null))
      .catch(() => setPendingCount(null))
  }, [])

  // Fallback al campo del resumen del dashboard si stats no esta disponible
  const inboxCount = pendingCount ?? resumen?.inbox_pendiente_count ?? 0

  const [pinnedIds, setPinnedIds] = useState(new Set())
  const [expanded,  setExpanded]  = useState(false)

  const RIESGO_ORDEN = { critico: 0, alto: 1, ok: 2, fijo: 3 }
  const itemsOrdenados = useMemo(() => {
    if (!ejecucion) return []
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

  if (loading) return <div className="p-6 text-gray-400 text-sm">Loading dashboard...</div>
  if (error)   return <div className="p-6 text-red-500 text-sm">Error: {error}</div>

  const periodo = resumen?.periodo
  const fechaFinTentativa = periodo?.fecha_fin_real == null

  return (
    <div className="p-6 space-y-6 max-w-6xl">

      {/* Top bar */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 capitalize">
            {new Date().toLocaleString('es-CO', { month: 'long', year: 'numeric' })}
          </h1>
          <p className="text-sm text-gray-400 mt-0.5">
            {periodo?.dias_transcurridos} de {periodo?.dias_totales} dias &nbsp;·&nbsp;
            {periodo?.fecha_inicio} &rarr;&nbsp;
            <span className={fechaFinTentativa ? 'italic' : ''}>
              {periodo?.fecha_fin_tentativa}{fechaFinTentativa ? '*' : ''}
            </span>
            {fechaFinTentativa && (
              <span
                className="ml-1 inline-flex items-center justify-center w-4 h-4 rounded-full bg-gray-200 text-gray-500 text-xs cursor-help"
                title="Fecha tentativa -- se confirma al acreditarse el salario"
              >?</span>
            )}
          </p>
        </div>

        {/* Badge inbox -- conteo real, navega a /transacciones */}
        {inboxCount > 0 && (
          <button
            onClick={() => navigate('/transacciones')}
            className="inline-flex items-center gap-2 px-4 py-2 bg-gray-900 text-white text-sm rounded-xl hover:bg-gray-800 transition-colors"
          >
            <span>📥</span>
            <span>{inboxCount} pending to categorize</span>
          </button>
        )}
      </div>

      {/* 4 metricas */}
      <div className="grid grid-cols-4 gap-4">
        <MetricCard
          label="Income received"
          value={formatCOP(resumen?.ingresos_acreditados)}
          sub={`Credited ${periodo?.fecha_inicio}`}
          subColor=""
          onDetail={() => {}}
        />
        <MetricCard
          label="Spending to date"
          value={formatCOP(resumen?.gastos_acumulados)}
          sub={`Projected ${formatCOP(resumen?.saldo_proyectado_cierre > 0
            ? resumen.ingresos_acreditados - resumen.saldo_proyectado_cierre
            : null)} at close`}
          subColor="warning"
          onDetail={() => {}}
        />
        <MetricCard
          label="Projected balance"
          value={formatCOP(resumen?.saldo_proyectado_cierre)}
          sub={`Available today: ${formatCOP(resumen?.saldo_disponible_hoy)}`}
          subColor=""
          onDetail={() => {}}
        />
        <MetricCard
          label="Net worth"
          value={formatCOP(resumen?.patrimonio_neto)}
          sub={`+${formatCOP(resumen?.variacion_patrimonio_mes_anterior)} vs last month`}
          subColor="success"
          onDetail={() => {}}
        />
      </div>

      {/* Presupuesto x categoria */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Budget status by category
          </h2>
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-400">By risk</span>
            <button
              onClick={() => setExpanded(e => !e)}
              className="text-xs text-primary-600 hover:text-primary-700 font-medium"
            >
              {expanded ? '↑ Show less' : `↓ Show all (${itemsOrdenados.length})`}
            </button>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-4">
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

      {/* Ingresos + Obligaciones */}
      <div className="grid grid-cols-2 gap-4">
        <IngresosPanel ingresos={ingresos} totalAcreditado={resumen?.ingresos_acreditados} />
        <ObligacionesPanel obligaciones={obligaciones} />
      </div>

      {/* Ask Claude */}
      <div
        className="flex items-center gap-3 px-4 py-3 bg-white border border-gray-200 rounded-xl cursor-pointer hover:border-gray-300 transition-colors"
        onClick={() => navigate('/analitica')}
      >
        <span className="text-lg">🤖</span>
        <span className="text-sm text-gray-400">Ask Claude about your finances...</span>
        <span className="ml-auto text-xs text-gray-300">↗</span>
      </div>
    </div>
  )
}
