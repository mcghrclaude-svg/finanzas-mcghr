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
import InsightBanner, { seleccionarInsight } from './components/InsightBanner'
import PresupuestoCategorias from './components/PresupuestoCategorias'
import TransaccionesRecientes from './components/TransaccionesRecientes'
import EvolucionPatrimonio from './components/EvolucionPatrimonio'
import PersonalizarWidgets from './components/PersonalizarWidgets'
import { formatCOP } from '@/hooks/useDashboard'

export default function Dashboard() {
  const navigate = useNavigate()
  const hoy = new Date()
  const {
    resumen, inboxStats, homeConfig, transaccionesRecientes,
    patrimonio, patrimonioHistorico, categoriasConHijos, resumenCategorias,
    loading, error, refetch, actualizarHomeConfig,
  } = useDashboard(hoy.getFullYear(), hoy.getMonth() + 1)

  if (loading) return <div className="p-6 text-gray-400 text-sm">Loading...</div>
  if (error)   return <div className="p-6 text-red-500 text-sm">Error: {error}</div>

  const periodo = resumen?.periodo
  const insight = seleccionarInsight(resumenCategorias)

  return (
    <div className="p-6 space-y-3 max-w-6xl">

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

      {/* Fila superior: KPIs (ancho) + torta angosta, misma altura -- la
          torta tiene ancho fijo chico, no una fraccion del ancho total, y
          ya no usa h-full (eso hacia que estirara todo el alto disponible
          de una columna compartida con Patrimonio, dejandola gigante y
          tapando lo de abajo). */}
      <div className="grid gap-3" style={{ gridTemplateColumns: '1fr 190px' }}>
        <div className="grid grid-cols-2 gap-2.5">
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

      {homeConfig?.insight_visible && insight && (
        <InsightBanner insight={insight} />
      )}

      {/* Presupuesto por categoria: ancho completo de la pagina (no
          columna angosta) para que entren 3 categorias por fila y solo
          2 filas en vez de 3. */}
      <PresupuestoCategorias
        resumenCategorias={resumenCategorias}
        categoriasConHijos={categoriasConHijos}
      />

      {/* Fila inferior: Transacciones (ancho) + Patrimonio y Ask Claude
          apilados en la misma columna angosta que la torta arriba. */}
      <div className="grid gap-3" style={{ gridTemplateColumns: '1fr 190px' }}>
        <TransaccionesRecientes items={transaccionesRecientes} onEditada={refetch} />

        <div className="flex flex-col gap-3">
          {homeConfig?.patrimonio_visible && (
            <EvolucionPatrimonio patrimonio={patrimonio} patrimonioHistorico={patrimonioHistorico} />
          )}

          {homeConfig?.ask_visible && (
            <div className="bg-white border border-gray-200 rounded-xl p-4 flex flex-col gap-3">
              <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Preguntale a Claude</h2>
              <p className="text-xs text-gray-500">
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
    </div>
  )
}
