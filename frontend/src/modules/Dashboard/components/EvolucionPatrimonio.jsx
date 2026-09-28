/**
 * EvolucionPatrimonio — activos vs. deudas, con desglose por cuenta y por
 * préstamo. La serie histórica viene de /inversiones/patrimonio/historico
 * (mensual, as-of fin de cada mes) -- el eje de tiempo dinámico
 * semanas→años que se evaluó en el diseño queda para cuando el backend
 * agregue también una granularidad semanal (ver plan, sección "Después");
 * por ahora, con poco historial simplemente se muestra un aviso en vez de
 * un gráfico vacío o engañoso.
 */
import { formatCOP } from '@/hooks/useDashboard'

const MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

function construirLineas(puntos) {
  const conDatos = puntos.filter(p => p.activos_total != null || p.deudas_total != null)
  if (conDatos.length < 2) return null

  const valores = conDatos.flatMap(p => [p.activos_total, p.deudas_total]).filter(v => v != null)
  const max = Math.max(...valores, 1)
  const W = 260, H = 60
  const paso = W / (conDatos.length - 1)

  const puntosA = []
  const puntosD = []
  conDatos.forEach((p, i) => {
    const x = i * paso
    if (p.activos_total != null) puntosA.push(`${x},${H - (p.activos_total / max) * H}`)
    if (p.deudas_total != null) puntosD.push(`${x},${H - (p.deudas_total / max) * H}`)
  })

  return { puntosA: puntosA.join(' '), puntosD: puntosD.join(' '), etiquetas: conDatos.map(p => MESES[p.mes - 1]) }
}

export default function EvolucionPatrimonio({ patrimonio, patrimonioHistorico }) {
  const lineas = patrimonioHistorico ? construirLineas(patrimonioHistorico.puntos) : null

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 flex flex-col gap-3">
      <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Evolución patrimonio</h2>

      {lineas ? (
        <svg viewBox="0 0 260 60" width="100%" height="60">
          <polyline points={lineas.puntosA} fill="none" stroke="#16a34a" strokeWidth="2.3" />
          <polyline points={lineas.puntosD} fill="none" stroke="#dc2626" strokeWidth="2.3" />
        </svg>
      ) : (
        <div className="h-[60px] flex items-center justify-center text-xs text-gray-400 italic">
          Acumulando historial mensual todavía.
        </div>
      )}

      <div className="text-xs flex flex-col gap-1">
        <div className="flex justify-between">
          <span className="text-success-500 font-medium">● Activos</span>
          <b>{formatCOP(patrimonio?.activos_total)}</b>
        </div>
        <div className="flex justify-between">
          <span className="text-danger-500 font-medium">● Deudas</span>
          <b>{formatCOP(patrimonio?.deudas_total)}</b>
        </div>
        <div className="flex justify-between border-t border-gray-100 pt-1">
          <span className="text-gray-400 font-medium">Neto</span>
          <b>{formatCOP(patrimonio?.patrimonio_neto)}</b>
        </div>
      </div>

      {patrimonio?.detalle_activos?.length > 0 && (
        <div className="border-t border-gray-100 pt-2">
          <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">Activos por cuenta</div>
          <div className="flex flex-col gap-0.5 text-xs">
            {patrimonio.detalle_activos.map(a => (
              <div key={a.id} className="flex justify-between text-gray-600">
                <span className="truncate">{a.nombre}</span>
                <b className="flex-shrink-0">{formatCOP(a.valor)}</b>
              </div>
            ))}
          </div>
        </div>
      )}

      {patrimonio?.detalle_deudas?.length > 0 && (
        <div className="border-t border-gray-100 pt-2">
          <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">Deudas por préstamo</div>
          <div className="flex flex-col gap-0.5 text-xs">
            {patrimonio.detalle_deudas.map(d => (
              <div key={d.id} className="flex justify-between text-gray-600">
                <span className="truncate">{d.nombre}</span>
                <b className="flex-shrink-0">{formatCOP(d.saldo_pendiente)}</b>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="text-[10px] text-gray-400">Cuentas · excluye carro y moto</div>
    </div>
  )
}
