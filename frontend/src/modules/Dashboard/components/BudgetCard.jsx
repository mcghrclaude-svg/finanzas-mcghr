/**
 * BudgetCard — tarjeta de presupuesto por categoría.
 * Usa Tailwind. Soporta niveles: critico | alto | ok | fijo | sin_datos
 *
 * Props:
 *   item    — EjecucionItem
 *   pinned  — boolean
 *   onPin   — fn()
 */
import { useState } from 'react'
import { formatCOP } from '@/hooks/useDashboard'

const RIESGO_META = {
  critico:   { bar: 'bg-red-500',     pct: 'text-red-400',     badge: 'bg-red-950 text-red-300 border-red-800'     },
  alto:      { bar: 'bg-yellow-500',  pct: 'text-yellow-400',  badge: 'bg-yellow-950 text-yellow-300 border-yellow-800' },
  ok:        { bar: 'bg-emerald-500', pct: 'text-emerald-400', badge: 'bg-emerald-950 text-emerald-300 border-emerald-800' },
  fijo:      { bar: 'bg-emerald-500', pct: 'text-gray-300',    badge: 'bg-gray-800 text-gray-400 border-gray-700'  },
  sin_datos: { bar: 'bg-gray-600',    pct: 'text-gray-400',    badge: 'bg-gray-800 text-gray-500 border-dashed border-gray-700' },
}

export default function BudgetCard({ item, pinned, onPin }) {
  const [hover, setHover] = useState(false)
  const meta = RIESGO_META[item.nivel_riesgo] ?? RIESGO_META.sin_datos
  const pctBar   = Math.min(item.pct_consumido * 100, 100)
  const pctProj  = item.pct_esperado_hoy != null ? item.pct_esperado_hoy * 100 : null
  const overBudget = item.pct_consumido > 1
  const sinHist  = item.nivel_riesgo === 'sin_datos'

  const diasParaVencer = item.proximo_vencimiento
    ? Math.ceil((new Date(item.proximo_vencimiento) - new Date()) / 86_400_000)
    : null

  return (
    <div
      className="bg-gray-800 rounded-xl p-4 flex flex-col gap-3 group relative cursor-default"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      {/* Pin */}
      <button
        onClick={onPin}
        className="absolute top-3 right-3 text-base transition-opacity"
        style={{ opacity: pinned ? 1 : hover ? 0.5 : 0 }}
        title={pinned ? 'Desfijar' : 'Fijar'}
      >
        📌
      </button>

      {/* Cabecera */}
      <div className="flex items-center gap-2">
        <div
          className="w-2.5 h-2.5 rounded-full flex-shrink-0"
          style={{ background: item.color ?? '#6b7280' }}
        />
        <span className="text-sm font-medium text-gray-200 truncate">{item.nombre}</span>
      </div>

      {/* % consumido */}
      <div className="flex items-center gap-2">
        <span className={`text-2xl font-bold tabular-nums ${meta.pct}`}>
          {pctBar.toFixed(0)}%
        </span>
        {overBudget && (
          <span className="text-yellow-400 text-sm" title="Supera el presupuesto">⚠️</span>
        )}
      </div>

      {/* Barra de progreso */}
      <div className="relative h-1.5 bg-gray-700 rounded-full overflow-visible">
        <div
          className={`h-full rounded-full transition-all ${meta.bar}`}
          style={{ width: `${Math.min(pctBar, 100)}%` }}
        />
        {/* Línea punteada: solo si hay histórico y no es fijo */}
        {pctProj != null && item.nivel_riesgo !== 'fijo' && (
          <div
            className="absolute top-1/2 -translate-y-1/2 w-px h-3 bg-gray-400 opacity-60"
            style={{ left: `${Math.min(pctProj, 100)}%` }}
            title={`Esperado a hoy (histórico): ${pctProj.toFixed(0)}%`}
          />
        )}
      </div>

      {/* Tres cifras */}
      <div className="grid grid-cols-3 gap-1 text-center">
        {[['Presupuesto', item.monto_presupuestado, ''], ['Gastado', item.gasto_acumulado, item.nivel_riesgo === 'critico' ? 'text-red-400' : item.nivel_riesgo === 'alto' ? 'text-yellow-400' : ''], ['Proyectado', item.monto_proyectado, overBudget ? 'text-red-400' : '']]
          .map(([lbl, val, cls]) => (
            <div key={lbl}>
              <div className="text-xs text-gray-500">{lbl}</div>
              <div className={`text-xs font-medium text-gray-300 tabular-nums ${cls}`}>
                {formatCOP(val)}
              </div>
            </div>
          ))
        }
      </div>

      {/* Badge */}
      {item.nivel_riesgo === 'fijo' ? (
        <div className={`text-xs px-2 py-1 rounded-lg border ${meta.badge}`}>
          📅 Pago único · vence {diasParaVencer != null ? `en ${diasParaVencer} días` : item.proximo_vencimiento}
        </div>
      ) : sinHist ? (
        <div className={`text-xs px-2 py-1 rounded-lg border ${meta.badge}`}>
          ⏳ Acumulando datos históricos
        </div>
      ) : (
        <div className={`text-xs px-2 py-1 rounded-lg border ${meta.badge}`}>
          {item.nivel_riesgo === 'critico' && `🔥 Ritmo ${Math.round((item.ratio_riesgo - 1) * 100)}% mayor al histórico`}
          {item.nivel_riesgo === 'alto'    && `📈 ${Math.round((item.ratio_riesgo - 1) * 100)}% sobre ritmo histórico`}
          {item.nivel_riesgo === 'ok'      && `✓ En línea con histórico`}
        </div>
      )}
    </div>
  )
}
