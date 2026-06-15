/**
 * IngresosPanel — panel de ingresos del período, agrupados por fuente (no por persona).
 * Props:
 *   ingresos: array de { id, nombre, monto, estado, fecha }
 *   totalAcreditado: number
 */
import { formatCOP } from '../../hooks/useDashboard'

const ICONOS = {
  'ING-SAL': '💼',
  'ING-ACC': '📊',
  'ING-ARR': '🏬',
  'ING-INT': '🐷',
}

export default function IngresosPanel({ ingresos, totalAcreditado }) {
  return (
    <div className="panel">
      <div className="panel-title">Ingresos del período (por fuente)</div>
      {ingresos.map(ing => (
        <div key={ing.id} className="ingr-row">
          <span className="ingr-label">
            {ICONOS[ing.id] ?? '💰'} {ing.nombre}{' '}
            {ing.estado === 'acreditado' && <span className="acred-pill">acreditado</span>}
            {ing.estado === 'no_registrado' && <span className="pend-pill">no reg.</span>}
          </span>
          <span className={`ingr-val ${ing.monto ? 'text-success' : 'text-muted'}`}>
            {formatCOP(ing.monto)}
          </span>
        </div>
      ))}
      <div className="ingr-total-row">
        <span style={{ fontSize: '12px', fontWeight: 500 }}>Total acreditado</span>
        <span style={{ fontSize: '15px', fontWeight: 500 }} className="text-success">
          {formatCOP(totalAcreditado)}
        </span>
      </div>
    </div>
  )
}
