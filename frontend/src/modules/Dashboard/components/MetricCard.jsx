/**
 * MetricCard.jsx — Version A
 * Cambio: fondo gris suave en lugar del azul/gris oscuro anterior.
 * bg-gray-100 con borde sutil — neutro, legible, sin agresividad visual.
 */
import { useState } from 'react'

export default function MetricCard({ label, value, sub, subColor = '', onDetail }) {
  const [showPlus, setShowPlus] = useState(false)

  const subColorClass = {
    success: 'text-success-500',
    warning: 'text-warning-500',
    danger:  'text-danger-500',
  }[subColor] ?? 'text-gray-400'

  return (
    <div
      className="relative bg-gray-100 border border-gray-200 rounded-xl p-5 cursor-default transition-shadow hover:shadow-sm"
      onMouseEnter={() => setShowPlus(true)}
      onMouseLeave={() => setShowPlus(false)}
    >
      {onDetail && (
        <button
          onClick={onDetail}
          title="Ver detalle"
          aria-label={`Ver detalle de ${label}`}
          className="absolute top-3 right-3 w-6 h-6 flex items-center justify-center rounded-full bg-white text-gray-400 hover:text-gray-700 text-sm border border-gray-200 transition-opacity"
          style={{ opacity: showPlus ? 1 : 0 }}
        >
          +
        </button>
      )}
      <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
        {label}
      </div>
      <div className="text-2xl font-bold text-gray-900 mb-1">
        {value}
      </div>
      {sub && (
        <div className={`text-xs ${subColorClass}`}>
          {sub}
        </div>
      )}
    </div>
  )
}
