/**
 * ObligacionesPanel — próximas obligaciones del período.
 * Props:
 *   obligaciones: array de { id, nombre, fecha_vencimiento, dias_restantes, monto, estado }
 */
import { formatCOP } from '../../hooks/useDashboard'

const ICONOS_OBLIG = {
  'OBL-1': '🏢',
  'OBL-2': '📄',
  'OBL-3': '🔌',
  'OBL-4': '📺',
}

const ESTADO_STYLE = {
  pendiente:  { bg: 'var(--color-background-warning)', color: 'var(--color-text-warning)', label: 'pendiente' },
  pagado:     { bg: 'var(--color-background-success)', color: 'var(--color-text-success)', label: 'pagado' },
  por_vencer: { bg: 'var(--color-background-secondary)', color: 'var(--color-text-secondary)', label: 'por vencer' },
}

export default function ObligacionesPanel({ obligaciones }) {
  return (
    <div className="panel">
      <div className="panel-title">Próximas obligaciones</div>
      {obligaciones.map(ob => {
        const estilo = ESTADO_STYLE[ob.estado] ?? ESTADO_STYLE.por_vencer
        return (
          <div key={ob.id} className="oblig-item">
            <span style={{ fontSize: '15px', color: 'var(--color-text-secondary)', flexShrink: 0 }}>
              {ICONOS_OBLIG[ob.id] ?? '📌'}
            </span>
            <div className="oblig-info">
              <div className="oblig-name">{ob.nombre}</div>
              <div className="oblig-fecha">
                vence {ob.fecha_vencimiento} · en {ob.dias_restantes} días
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '12px', fontWeight: 500 }}>{formatCOP(ob.monto)}</div>
              <div
                className="ob-badge"
                style={{ background: estilo.bg, color: estilo.color }}
              >
                {estilo.label}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
