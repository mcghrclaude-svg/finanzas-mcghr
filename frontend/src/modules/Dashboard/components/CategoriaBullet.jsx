/**
 * CategoriaBullet — una fila del widget "Presupuesto por categoría", al
 * estilo de las etiquetas de la PWA (pwa-gastos/src/components/BulletChart):
 * barra con el gasto acumulado, monto real y presupuestado superpuestos
 * sobre la barra (no como texto aparte). El punto de riesgo se deriva del
 * simple gasto/presupuesto (>=100% crítico, >=80% alto) -- mismo criterio
 * que la PWA, no el modelo de velocidad_actual/historica del período
 * financiero (que el Home ya no usa, ver ADR mes-calendario).
 */
import { formatCOP } from '@/hooks/useDashboard'
import { colorDeterministico } from '../colorCategoria'

const UMBRAL_ALTO = 0.8
const UMBRAL_CRITICO = 1.0

function clamp(v, lo, hi) {
  return Math.min(Math.max(v, lo), hi)
}

export default function CategoriaBullet({ item, tieneHijos = false, onDrill }) {
  const gasto = item.gasto_acumulado ?? 0
  const presupuesto = item.presupuesto ?? item.monto_presupuestado ?? 0
  const scale = 1.15 * Math.max(gasto, presupuesto || gasto || 1)
  const fillPct = gasto > 0 ? clamp((gasto / scale) * 100, 0.8, 100) : 0
  const markPct = presupuesto > 0 ? clamp((presupuesto / scale) * 100, 0, 100) : null

  const ratio = presupuesto > 0 ? gasto / presupuesto : 0
  const critico = ratio >= UMBRAL_CRITICO
  const alto = !critico && ratio >= UMBRAL_ALTO

  const labelGastoPct = clamp(fillPct, 6, 94)
  const labelPresPct = markPct !== null ? clamp(markPct, 6, 94) : null

  const color = item.color ?? colorDeterministico(item.id_categoria)

  return (
    <button
      onClick={tieneHijos ? onDrill : undefined}
      className={`w-full text-left ${tieneHijos ? 'cursor-pointer group' : 'cursor-default'}`}
    >
      <div className="flex items-center gap-1.5 mb-0.5">
        <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: color }} />
        <span className={`text-xs font-semibold text-gray-900 truncate ${tieneHijos ? 'group-hover:text-primary-700' : ''}`}>
          {item.nombre}
        </span>
        {critico && (
          <span className="flex-shrink-0 inline-flex items-center justify-center w-3.5 h-3.5 rounded-full bg-red-600 text-white text-[9px] font-bold">!</span>
        )}
        {alto && (
          <span className="flex-shrink-0 inline-flex items-center justify-center w-3.5 h-3.5 rounded-full bg-amber-500 text-white text-[9px] font-bold">!</span>
        )}
        {tieneHijos && <span className="ml-auto text-gray-300 text-xs flex-shrink-0">›</span>}
      </div>

      <div className="relative h-8">
        {markPct !== null && (
          <span
            className="absolute text-[9.5px] font-bold whitespace-nowrap bg-white px-1 rounded"
            style={{ left: `${labelPresPct}%`, top: -2, color: '#8b5cf6', transform: 'translateX(-50%)' }}
          >
            {formatCOP(presupuesto)}
          </span>
        )}
        <div className="absolute left-0 right-0 h-2 bg-gray-100 rounded-full" style={{ top: 12 }}>
          <div className="h-full rounded-full transition-all" style={{ width: `${fillPct}%`, background: color }} />
          {markPct !== null && (
            <div
              className="absolute -top-0.5 w-0.5 h-3 rounded-sm"
              style={{ left: `${markPct}%`, background: '#8b5cf6' }}
            />
          )}
        </div>
        <span
          className="absolute text-[9.5px] font-bold whitespace-nowrap bg-white px-1 rounded"
          style={{ left: `${labelGastoPct}%`, top: 22, color, transform: 'translateX(-50%)' }}
        >
          {formatCOP(gasto)}
        </span>
      </div>
    </button>
  )
}
