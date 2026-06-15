/**
 * MetricCard — una de las 4 tarjetas de métricas del dashboard.
 * Props:
 *   label: string
 *   value: string          — ya formateado (ej: "$23.0M")
 *   sub: string            — texto secundario
 *   subColor: string       — 'success' | 'warning' | 'danger' | ''
 *   onDetail: fn | null    — si se provee, muestra botón +
 */
import { useState } from 'react'

export default function MetricCard({ label, value, sub, subColor = '', onDetail }) {
  const [showPlus, setShowPlus] = useState(false)

  return (
    <div
      className="metric-card"
      onMouseEnter={() => setShowPlus(true)}
      onMouseLeave={() => setShowPlus(false)}
    >
      {onDetail && (
        <button
          className="metric-expand"
          onClick={onDetail}
          title="Ver detalle"
          style={{ opacity: showPlus ? 0.7 : 0 }}
          aria-label={`Ver detalle de ${label}`}
        >
          +
        </button>
      )}
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
      {sub && <div className={`metric-sub ${subColor ? `text-${subColor}` : ''}`}>{sub}</div>}
    </div>
  )
}
