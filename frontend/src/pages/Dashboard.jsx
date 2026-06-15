/**
 * Dashboard — página principal de la plataforma financiera MCGHR.
 *
 * Estructura:
 *   TopBar (período + badge inbox)
 *   MetricGrid (4 tarjetas: ingresos, gastos, saldo proy., patrimonio)
 *   BudgetSection (tarjetas de presupuesto ordenadas por riesgo, con pin y expand)
 *   BottomPanels (ingresos por fuente | obligaciones próximas)
 *   ClaudeAsk (pregunta rápida al análisis IA)
 *
 * Estado local:
 *   pinnedIds: Set<string>  — categorías fijadas por el usuario
 *   expanded: boolean       — si se muestran todas las tarjetas o solo las N primeras
 *   CARDS_DEFAULT: número de tarjetas visibles por defecto según viewport
 */

import { useState, useMemo } from 'react'
import { useDashboard, formatCOP } from '../hooks/useDashboard'
import MetricCard from '../components/dashboard/MetricCard'
import BudgetCard from '../components/dashboard/BudgetCard'
import IngresosPanel from '../components/dashboard/IngresosPanel'
import ObligacionesPanel from '../components/dashboard/ObligacionesPanel'
import './Dashboard.css'

const CARDS_DEFAULT = 3   // TODO: calcular según viewport (3 desktop, 2 tablet, 1 mobile)

export default function Dashboard() {
  const hoy = new Date()
  const { resumen, ejecucion, ingresos, obligaciones, loading, error, refetch } =
    useDashboard(hoy.getFullYear(), hoy.getMonth() + 1)

  const [pinnedIds, setPinnedIds] = useState(new Set())
  const [expanded, setExpanded] = useState(false)

  // Ordenar items: pinneados primero, luego por nivel de riesgo
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

  // ── Período ──────────────────────────────────────────────────────────────
  const periodo = resumen?.periodo
  const fechaFinTentativa = periodo?.fecha_fin_real == null

  // ── Loading / Error ───────────────────────────────────────────────────────
  if (loading) return <div className="dashboard-loading">Cargando dashboard…</div>
  if (error)   return <div className="dashboard-error">Error: {error}</div>

  return (
    <div className="dashboard">

      {/* ── Top bar ─────────────────────────────────────────────────────── */}
      <div className="top-bar">
        <div>
          <div className="top-bar-title">
            {new Date().toLocaleString('es-CO', { month: 'long', year: 'numeric' })}
          </div>
          <div className="top-bar-sub">
            {periodo?.dias_transcurridos} de {periodo?.dias_totales} días · período{' '}
            {periodo?.fecha_inicio} →{' '}
            <span className={fechaFinTentativa ? 'date-tentativa' : ''}>
              {periodo?.fecha_fin_tentativa}{fechaFinTentativa ? '*' : ''}
            </span>
            {fechaFinTentativa && (
              <span
                className="period-hint"
                title="Fecha de cierre tentativa — se confirma al acreditarse el salario."
              >?</span>
            )}
          </div>
        </div>
        <button className="badge-inbox">
          📥 {resumen?.inbox_pendiente_count} gastos x catalogar
        </button>
      </div>

      {/* ── 4 métricas ──────────────────────────────────────────────────── */}
      <div className="metric-grid">
        <MetricCard
          label="Ingresos acreditados"
          value={formatCOP(resumen?.ingresos_acreditados)}
          sub={`Salarios acred. ${periodo?.fecha_inicio}`}
          subColor=""
          onDetail={() => console.log('TODO: detalle ingresos — issue #15')}
        />
        <MetricCard
          label="Gastos jun (a hoy)"
          value={formatCOP(resumen?.gastos_acumulados)}
          sub={`Proy. ${formatCOP(resumen?.saldo_proyectado_cierre > 0
            ? resumen.ingresos_acreditados - resumen.saldo_proyectado_cierre
            : null)} al cierre`}
          subColor="warning"
          onDetail={() => console.log('TODO: detalle gastos — issue #14')}
        />
        <MetricCard
          label="Saldo proy. al cierre*"
          value={formatCOP(resumen?.saldo_proyectado_cierre)}
          sub={`Disponible hoy: ${formatCOP(resumen?.saldo_disponible_hoy)}`}
          subColor=""
          onDetail={() => console.log('TODO: detalle saldo')}
        />
        <MetricCard
          label="Patrimonio neto"
          value={formatCOP(resumen?.patrimonio_neto)}
          sub={`+${formatCOP(resumen?.variacion_patrimonio_mes_anterior)} vs mes anterior`}
          subColor="success"
          onDetail={() => console.log('TODO: detalle patrimonio')}
        />
      </div>

      {/* ── Presupuesto x categoría ──────────────────────────────────────── */}
      <div className="section-header">
        <div className="section-label">Status de presupuesto x categoría</div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span style={{ fontSize: 11, color: 'var(--color-text-secondary)' }}>Por riesgo</span>
          <button
            className="expand-btn"
            onClick={() => setExpanded(e => !e)}
          >
            {expanded
              ? '↑ Mostrar menos'
              : `↓ Ver todas (${itemsOrdenados.length})`}
          </button>
        </div>
      </div>

      <div className="budget-grid">
        {itemsVisibles.map(item => (
          <BudgetCard
            key={item.id_categoria}
            item={item}
            pinned={pinnedIds.has(item.id_categoria)}
            onPin={() => togglePin(item.id_categoria)}
          />
        ))}
      </div>

      {/* ── Ingresos + Obligaciones ──────────────────────────────────────── */}
      <div className="two-col">
        <IngresosPanel
          ingresos={ingresos}
          totalAcreditado={resumen?.ingresos_acreditados}
        />
        <ObligacionesPanel obligaciones={obligaciones} />
      </div>

      {/* ── Pregunta a Claude ────────────────────────────────────────────── */}
      <button className="ask-btn">
        🤖 Preguntarle a Claude: ¿por qué restaurantes está en riesgo crítico? ↗
      </button>

    </div>
  )
}
