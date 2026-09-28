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
      className="relative bg-gray-100 border border-gray-200 rounded-xl p-3 cursor-default transition-shadow hover:shadow-sm h-full flex flex-col justify-center"
      onMouseEnter={() => setShowPlus(true)}
      onMouseLeave={() => setShowPlus(false)}
    >
      {onDetail && (
        <button
          onClick={onDetail}
          title="Ver detalle"
          aria-label={`Ver detalle de ${label}`}
          className="absolute top-2 right-2 w-5 h-5 flex items-center justify-center rounded-full bg-white text-gray-400 hover:text-gray-700 text-xs border border-gray-200 transition-opacity"
          style={{ opacity: showPlus ? 1 : 0 }}
        >
          +
        </button>
      )}
      <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
        {label}
      </div>
      <div className="text-xl font-bold text-gray-900">
        {value}
      </div>
      {sub && (
        <div className={`text-[10.5px] mt-0.5 ${subColorClass}`}>
          {sub}
        </div>
      )}
    </div>
  )
}
