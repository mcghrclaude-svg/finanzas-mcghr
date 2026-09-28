/**
 * InsightBanner — aviso de patrón inusual, derivado en el cliente de los
 * mismos campos que ya devuelve /presupuestos/ejecucion (ratio_riesgo,
 * nivel_riesgo) -- no necesita ningún endpoint nuevo. Si ninguna categoría
 * viene alto/crítico, no se muestra nada.
 */
import { formatCOP } from '@/hooks/useDashboard'

export default function InsightBanner({ ejecucion }) {
  const items = ejecucion?.items ?? []
  const candidato = items
    .filter(i => (i.nivel_riesgo === 'critico' || i.nivel_riesgo === 'alto') && i.ratio_riesgo)
    .sort((a, b) => b.ratio_riesgo - a.ratio_riesgo)[0]

  if (!candidato) return null

  const pctSobreRitmo = Math.round((candidato.ratio_riesgo - 1) * 100)

  return (
    <div className="bg-primary-50 border border-primary-100 rounded-xl px-5 py-4 flex gap-3 items-start">
      <span className="text-lg">💡</span>
      <div>
        <div className="text-sm font-semibold text-primary-800">
          {candidato.nombre} viene {pctSobreRitmo}% por encima de tu ritmo habitual
        </div>
        <div className="text-xs text-gray-500 mt-0.5">
          Ya llevas {formatCOP(candidato.gasto_acumulado)} de los {formatCOP(candidato.monto_presupuestado)} presupuestados.
          Si el ritmo sigue así, cerrarías en {formatCOP(candidato.monto_proyectado)}.
        </div>
      </div>
    </div>
  )
}
