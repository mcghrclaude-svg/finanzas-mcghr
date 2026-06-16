/**
 * MetricCard — tarjeta de métrica del top del dashboard.
 *
 * Props:
 *   label: string
 *   value: string          (ya formateado, ej: "$23.0M")
 *   sub: string            (texto secundario)
 *   subVariant: '' | 'warning' | 'success'
 *   tentative: boolean     (muestra asterisco en label)
 */
export default function MetricCard({ label, value, sub, subVariant, tentative }) {
  const subColor = {
    warning: 'text-yellow-400',
    success: 'text-emerald-400',
    '': 'text-gray-500',
  }[subVariant ?? ''] ?? 'text-gray-500'

  return (
    <div className="bg-gray-800 rounded-xl p-4 flex flex-col gap-1 group relative">
      <span className="text-xs text-gray-400 font-medium">
        {label}{tentative && <span className="text-gray-600"> *</span>}
      </span>
      <span className="text-2xl font-bold text-gray-100 tabular-nums">
        {value}
      </span>
      {sub && (
        <span className={`text-xs ${subColor} mt-0.5`}>{sub}</span>
      )}
      {/* Botón + hover — futuro: abrir detalle */}
      <button
        className="absolute top-3 right-3 opacity-0 group-hover:opacity-40 hover:!opacity-100 text-gray-400 text-xs transition-opacity"
        onClick={() => {}}
        title="Ver detalle"
      >
        +
      </button>
    </div>
  )
}
