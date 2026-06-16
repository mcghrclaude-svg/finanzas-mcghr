/**
 * IngresosPanel — panel de ingresos por fuente.
 * Props:
 *   ingresos: IngresoItem[]
 *   totalAcreditado: number
 */
import { formatCOP } from '@/hooks/useDashboard'

const ESTADO_META = {
  acreditado:    { dot: 'bg-emerald-500', text: 'text-emerald-400', label: 'Acreditado' },
  no_registrado: { dot: 'bg-gray-600',    text: 'text-gray-500',    label: 'No registrado' },
  pendiente:     { dot: 'bg-yellow-500',  text: 'text-yellow-400',  label: 'Pendiente' },
}

export default function IngresosPanel({ ingresos = [], totalAcreditado }) {
  return (
    <div className="bg-gray-800 rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">Ingresos</span>
        <span className="text-sm font-bold text-gray-100 tabular-nums">{formatCOP(totalAcreditado)}</span>
      </div>
      <div className="space-y-2">
        {ingresos.map(ing => {
          const meta = ESTADO_META[ing.estado] ?? ESTADO_META.no_registrado
          return (
            <div key={ing.id} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className={`w-1.5 h-1.5 rounded-full ${meta.dot}`} />
                <span className="text-xs text-gray-300">{ing.nombre}</span>
              </div>
              <div className="text-right">
                {ing.monto != null ? (
                  <span className="text-xs font-medium text-gray-200 tabular-nums">{formatCOP(ing.monto)}</span>
                ) : (
                  <span className={`text-xs ${meta.text}`}>{meta.label}</span>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
