/**
 * ObligacionesPanel — próximas obligaciones de pago.
 * Props:
 *   obligaciones: ObligacionItem[]
 */
import { formatCOP } from '@/hooks/useDashboard'

const ESTADO_META = {
  pendiente:  { dot: 'bg-red-500',     text: 'text-red-400',     label: 'Pendiente'  },
  por_vencer: { dot: 'bg-yellow-500',  text: 'text-yellow-400',  label: 'Por vencer' },
  pagado:     { dot: 'bg-emerald-500', text: 'text-emerald-400', label: 'Pagado'     },
}

export default function ObligacionesPanel({ obligaciones = [] }) {
  return (
    <div className="bg-gray-800 rounded-xl p-4">
      <div className="mb-3">
        <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">Obligaciones próximas</span>
      </div>
      <div className="space-y-2">
        {obligaciones.map(obl => {
          const meta = ESTADO_META[obl.estado] ?? ESTADO_META.por_vencer
          return (
            <div key={obl.id} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className={`w-1.5 h-1.5 rounded-full ${meta.dot}`} />
                <div>
                  <div className="text-xs text-gray-300">{obl.nombre}</div>
                  <div className="text-xs text-gray-500">
                    {obl.dias_restantes != null
                      ? obl.dias_restantes <= 0
                        ? 'Hoy'
                        : `en ${obl.dias_restantes} días`
                      : obl.fecha_vencimiento}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs font-medium text-gray-200 tabular-nums">{formatCOP(obl.monto)}</div>
                <div className={`text-xs ${meta.text}`}>{meta.label}</div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
