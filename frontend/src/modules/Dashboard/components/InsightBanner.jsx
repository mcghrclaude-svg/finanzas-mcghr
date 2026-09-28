/**
 * InsightBanner — aviso de patrón inusual, derivado en el cliente de
 * /presupuestos/resumen-por-categoria (mes calendario) -- no necesita
 * ningún endpoint nuevo. Elige la categoría nivel-1 con mayor % de
 * presupuesto consumido (>=80%); si ninguna llega a ese umbral, no hay
 * nada que mostrar.
 *
 * `seleccionarInsight` se exporta aparte para que el layout del Home
 * pueda decidir si reserva o no la celda de la grilla ANTES de renderizar
 * -- un <div> vacío (banner que decide no mostrar nada por dentro) igual
 * ocupa lugar en un grid con filas auto, y descuadra el alto de la fila
 * de al lado (Evolución patrimonio, que sí ocupa 2 filas).
 */
import { formatCOP } from '@/hooks/useDashboard'

const UMBRAL_AVISO = 0.8

export function seleccionarInsight(resumenCategorias) {
  const items = (resumenCategorias ?? []).filter(c => c.nivel === 1 && c.presupuesto > 0)
  return items
    .map(c => ({ ...c, ratio: c.gasto_acumulado / c.presupuesto }))
    .filter(c => c.ratio >= UMBRAL_AVISO)
    .sort((a, b) => b.ratio - a.ratio)[0] ?? null
}

export default function InsightBanner({ insight }) {
  if (!insight) return null

  const pct = Math.round(insight.ratio * 100)
  const sobrepasado = insight.ratio >= 1

  return (
    <div className="bg-primary-50 border border-primary-100 rounded-xl px-4 py-2.5 flex gap-3 items-start">
      <span className="text-lg">💡</span>
      <div>
        <div className="text-sm font-semibold text-primary-800">
          {insight.nombre} ya {sobrepasado ? 'superó' : 'consumió el'} {pct}% de su presupuesto
        </div>
        <div className="text-xs text-gray-500 mt-0.5">
          {formatCOP(insight.gasto_acumulado)} de los {formatCOP(insight.presupuesto)} presupuestados este mes.
        </div>
      </div>
    </div>
  )
}
