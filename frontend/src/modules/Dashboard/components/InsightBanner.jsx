/**
 * InsightBanner — aviso de patrón inusual, derivado en el cliente de
 * /presupuestos/resumen-por-categoria (mes calendario) -- no necesita
 * ningún endpoint nuevo. Elige la categoría nivel-1 con mayor % de
 * presupuesto consumido (>=80%); si ninguna llega a ese umbral, no
 * muestra nada.
 */
import { formatCOP } from '@/hooks/useDashboard'

const UMBRAL_AVISO = 0.8

export default function InsightBanner({ resumenCategorias }) {
  const items = (resumenCategorias ?? []).filter(c => c.nivel === 1 && c.presupuesto > 0)
  const candidato = items
    .map(c => ({ ...c, ratio: c.gasto_acumulado / c.presupuesto }))
    .filter(c => c.ratio >= UMBRAL_AVISO)
    .sort((a, b) => b.ratio - a.ratio)[0]

  if (!candidato) return null

  const pct = Math.round(candidato.ratio * 100)
  const sobrepasado = candidato.ratio >= 1

  return (
    <div className="bg-primary-50 border border-primary-100 rounded-xl px-4 py-2.5 flex gap-3 items-start">
      <span className="text-lg">💡</span>
      <div>
        <div className="text-sm font-semibold text-primary-800">
          {candidato.nombre} ya {sobrepasado ? 'superó' : 'consumió el'} {pct}% de su presupuesto
        </div>
        <div className="text-xs text-gray-500 mt-0.5">
          {formatCOP(candidato.gasto_acumulado)} de los {formatCOP(candidato.presupuesto)} presupuestados este mes.
        </div>
      </div>
    </div>
  )
}
