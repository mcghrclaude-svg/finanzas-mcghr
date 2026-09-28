/**
 * modules/Dashboard/index.jsx -- Home (variante D: grilla de widgets)
 *
 * Reemplaza la version anterior (KPIs + BudgetCard oscuro + Ingresos/
 * Obligaciones panels) por el diseno acordado en el canvas de Home MCGHR:
 *   - KPIs (ingreso, gasto acumulado, saldo disponible) + pendientes
 *     (inbox + SMS)
 *   - Aviso de patron inusual (derivado en el cliente, sin backend nuevo)
 *   - Presupuesto por categoria con drill-down a subcategorias
 *   - Ultimas transacciones con edicion inline (reusa DetailPanel de
 *     Transacciones)
 *   - Evolucion patrimonio (activos vs deudas + desglose)
 *   - Personalizar widgets (persistido en backend, GET/PATCH /home-config)
 */
import { useNavigate } from 'react-router-dom'
import { useDashboard } from '@/hooks/useDashboard'
import MetricCard from './components/MetricCard'
import PendientesCard from './components/PendientesCard'
import GastoPorCategoriaPie from './components/GastoPorCategoriaPie'
import InsightBanner from './components/InsightBanner'
import PresupuestoCategorias from './components/PresupuestoCategorias'
import TransaccionesRecientes from './components/TransaccionesRecientes'
import EvolucionPatrimonio from './components/EvolucionPatrimonio'
import PersonalizarWidgets from './components/PersonalizarWidgets'
import { formatCOP } from '@/hooks/useDashboard'

export default function Dashboard() {
  const navigate = useNavigate()
  const hoy = new Date()
  const {
    resumen, ejecucion, inboxStats, homeConfig, transaccionesRecientes,
    patrimonio, patrimonioHistorico, categoriasConHijos, resumenCategorias,
    loading, error, refetch, cargarSubcategorias, actualizarHomeConfig,
  } = useDashboard(hoy.getFullYear(), hoy.getMonth() + 1)

  if (loading) return <div className="p-6 text-gray-400 text-sm">Loading...</div>
  if (error)   return <div className="p-6 text-red-500 text-sm">Error: {error}</div>

  const periodo = resumen?.periodo

  return (
    <div className="p-6 space-y-4 max-w-6xl">

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Home</h1>
          <p className="text-sm text-gray-400 mt-0.5">
            {new Date().toLocaleString('es-CO', { month: 'long', year: 'numeric' })}
            {periodo?.dias_transcurridos != null && (
              <> &nbsp;·&nbsp; día {periodo.dias_transcurridos} de {periodo.dias_totales}</>
            )}
          </p>
        </div>
        <PersonalizarWidgets homeConfig={homeConfig} onCambiar={actualizarHomeConfig} />
      </div>

      {/* Fila superior: mismo ancho total que antes tenian los 4 KPIs --
          2/3 son esos mismos 4 KPIs (grilla 2x2) y 1/3 es la torta de gasto
          por categoria, sin espacio en blanco de sobra. */}
      <div className="grid gap-3.5" style={{ gridTemplateColumns: '2fr 1fr' }}>
        <div className="grid grid-cols-2 gap-3">
          <MetricCard label="Income received" value={formatCOP(resumen?.ingresos_acreditados)}
            sub={`Credited ${periodo?.fecha_inicio ?? ''}`} />
          <MetricCard label="Spending to date" value={formatCOP(resumen?.gastos_acumulados)}
            sub="Ver detalle abajo" subColor="warning" />
          <MetricCard label="Available balance" value={formatCOP(resumen?.saldo_disponible_hoy)}
            sub={`Proyectado cierre ${formatCOP(resumen?.saldo_proyectado_cierre)}`} />
          <PendientesCard inboxStats={inboxStats} />
        </div>
        <GastoPorCategoriaPie resumenCategorias={resumenCategorias} categoriasConHijos={categoriasConHijos} />
      </div>

      <div className="grid grid-cols-4 gap-4">

        {homeConfig?.insight_visible && (
          <div className="col-span-3">
            <InsightBanner ejecucion={ejecucion} />
          </div>
        )}

        {homeConfig?.patrimonio_visible && (
          <div style={{ gridColumn: '4', gridRow: 'span 2' }}>
            <EvolucionPatrimonio patrimonio={patrimonio} patrimonioHistorico={patrimonioHistorico} />
          </div>
        )}

        <div className="col-span-3">
          <PresupuestoCategorias
            ejecucion={ejecucion}
            categoriasConHijos={categoriasConHijos}
            cargarSubcategorias={cargarSubcategorias}
          />
        </div>

        <div className="col-span-3">
          <TransaccionesRecientes items={transaccionesRecientes} onEditada={refetch} />
        </div>

        {homeConfig?.ask_visible && (
          <div style={{ gridColumn: '4' }} className="bg-white border border-gray-200 rounded-xl p-4 h-[300px] flex flex-col gap-3">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Preguntale a Claude</h2>
            <p className="text-xs text-gray-500 flex-1">
              "¿Por qué esta categoría viene tan alta este mes?"
            </p>
            <button onClick={() => navigate('/analitica')}
              className="px-3 py-2 text-sm font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
              🤖 Preguntar
            </button>
          </div>
        )}

      </div>
    </div>
  )
}
