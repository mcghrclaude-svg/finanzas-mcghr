/**
 * BudgetCard — tarjeta de presupuesto por categoría.
 *
 * Props:
 *   item: EjecucionItem (shape = EJECUCION_MOCK.items[n])
 *   pinned: boolean
 *   onPin: fn()
 *
 * Comportamiento:
 *   - Barra de progreso: % consumido, color por nivel de riesgo
 *   - Línea punteada: pct_esperado_hoy (posición histórica esperada)
 *   - Badge de riesgo o badge de vencimiento (para fijo_unico)
 *   - Botón pin: visible en hover o cuando está pinneado
 */
import { useState } from 'react'
import { formatCOP, nivelRiesgoMeta } from '../../hooks/useDashboard'

export default function BudgetCard({ item, pinned, onPin }) {
  const [hover, setHover] = useState(false)
  const meta = nivelRiesgoMeta(item.nivel_riesgo)
  const pctBar = Math.min(item.pct_consumido * 100, 100).toFixed(0)
  const pctProj = (item.pct_esperado_hoy * 100).toFixed(0)
  const overBudget = item.pct_consumido > 1

  const diasParaVencer = item.proximo_vencimiento
    ? Math.ceil((new Date(item.proximo_vencimiento) - new Date()) / 86_400_000)
    : null

  return (
    <div
      className="budget-card"
      draggable
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      {/* Botón pin — visible en hover o si está pinneado */}
      <button
        className={`pin-btn${pinned ? ' pinned' : ''}`}
        onClick={onPin}
        title={pinned ? 'Fijada' : 'Fijar'}
        style={{
          opacity: pinned ? 1 : hover ? 0.6 : 0,
          color: pinned ? 'var(--color-text-warning)' : 'var(--color-text-secondary)',
        }}
        aria-label={pinned ? 'Desfijar categoría' : 'Fijar categoría'}
      >
        📌
      </button>

      {/* Cabecera: punto de color + nombre */}
      <div className="bc-cat-row">
        <div className="cat-dot" style={{ background: item.color }} />
        <div className="bc-cat">{item.nombre}</div>
      </div>

      {/* % consumido + alerta si supera presupuesto */}
      <div className="pct-label-row">
        <span className={`pct-label ${meta.pctClass}`}>
          {pctBar}%
        </span>
        {overBudget && (
          <span title="Supera el presupuesto" aria-label="Supera el presupuesto">⚠</span>
        )}
      </div>

      {/* Barra de progreso + línea punteada */}
      <div className="progress-wrap">
        <div
          className={`progress-bar ${meta.barClass}`}
          style={{ width: `${pctBar}%` }}
          role="progressbar"
          aria-valuenow={pctBar}
          aria-valuemin={0}
          aria-valuemax={100}
        />
        {item.nivel_riesgo !== 'fijo' && (
          <div
            className="progress-proj"
            style={{ left: `${pctProj}%` }}
            title={`Esperado a hoy: ${pctProj}%`}
          />
        )}
      </div>

      {/* Tres cifras: Presupuesto | Gastado hoy | Proyectado */}
      <div className="bc-nums">
        <div className="bc-num-item">
          <div className="bc-num-label">Presupuesto</div>
          <div className="bc-num-value">{formatCOP(item.monto_presupuestado)}</div>
        </div>
        <div className="bc-num-item">
          <div className="bc-num-label">Gastado hoy</div>
          <div className={`bc-num-value ${item.nivel_riesgo === 'critico' ? 'over' : item.nivel_riesgo === 'alto' ? 'warn' : ''}`}>
            {formatCOP(item.gasto_acumulado)}
          </div>
        </div>
        <div className="bc-num-item">
          <div className="bc-num-label">Proyectado</div>
          <div className={`bc-num-value ${overBudget ? 'over' : ''}`}>
            {formatCOP(item.monto_proyectado)}
          </div>
        </div>
      </div>

      {/* Badge de riesgo o badge de vencimiento */}
      {item.nivel_riesgo === 'fijo' ? (
        <div className={`risk-badge risk-fijo`}>
          📅 Pago único · vence {diasParaVencer != null ? `en ${diasParaVencer} días` : item.proximo_vencimiento}
        </div>
      ) : (
        <div className={`risk-badge ${meta.colorClass}`}>
          {item.nivel_riesgo === 'critico' && '🔥'}
          {item.nivel_riesgo === 'alto' && '📈'}
          {item.nivel_riesgo === 'ok' && '✓'}
          {' '}
          {item.nivel_riesgo === 'critico' && `Ritmo ${Math.round((item.ratio_riesgo - 1) * 100)}% mayor al histórico`}
          {item.nivel_riesgo === 'alto' && `${Math.round((item.ratio_riesgo - 1) * 100)}% sobre ritmo histórico`}
          {item.nivel_riesgo === 'ok' && 'En línea con histórico'}
        </div>
      )}
    </div>
  )
}
