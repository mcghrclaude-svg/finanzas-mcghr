/**
 * GastoPorCategoriaPie — widget "Gasto por categoría" del Home: torta con
 * la distribución del gasto (no vs. presupuesto, eso ya lo muestra
 * Presupuesto por categoría -- acá es una categoría relativa a las otras).
 * Etiquetas flotando sobre cada porción, sin leyenda aparte. Click en una
 * porción con subcategorías hace drill-down, con "← Atrás" para volver --
 * navegación propia, independiente de Presupuesto por categoría.
 *
 * Fuente: /presupuestos/resumen-por-categoria (gasto acumulado del mes
 * calendario, con rollup jerárquico) -- mismo mes calendario que usa todo
 * el resto del Home (KPIs, Presupuesto por categoría), así que el total
 * de esta torta sí coincide con el KPI "Gasto acumulado" de arriba.
 */
import { useState, useMemo } from 'react'
import { colorDeterministico } from '../colorCategoria'

const CX = 90, CY = 90, R = 80

function arco(a0, a1) {
  const rad = Math.PI / 180
  const x1 = CX + R * Math.cos(a0 * rad), y1 = CY + R * Math.sin(a0 * rad)
  const x2 = CX + R * Math.cos(a1 * rad), y2 = CY + R * Math.sin(a1 * rad)
  const large = (a1 - a0) > 180 ? 1 : 0
  return `M ${CX} ${CY} L ${x1.toFixed(2)} ${y1.toFixed(2)} A ${R} ${R} 0 ${large} 1 ${x2.toFixed(2)} ${y2.toFixed(2)} Z`
}

export default function GastoPorCategoriaPie({ resumenCategorias, categoriasConHijos }) {
  const [pila, setPila] = useState([]) // [{id, nombre}]
  const nivelActual = pila.length > 0 ? pila[pila.length - 1] : null

  const items = useMemo(() => {
    const lista = resumenCategorias ?? []
    const nivel = nivelActual
      ? lista.filter(c => c.id_padre === nivelActual.id)
      : lista.filter(c => c.nivel === 1)
    return nivel
      .filter(c => (c.gasto_acumulado ?? 0) > 0)
      .sort((a, b) => b.gasto_acumulado - a.gasto_acumulado)
  }, [resumenCategorias, nivelActual])

  const total = items.reduce((s, c) => s + c.gasto_acumulado, 0) || 1

  let ang = -90
  const slices = items.map(c => {
    const grados = (c.gasto_acumulado / total) * 360
    const a0 = ang, a1 = ang + grados
    const path = arco(a0, a1)
    const medio = (a0 + a1) / 2
    const rad = Math.PI / 180
    const labelR = R * 0.64
    const labelX = CX + labelR * Math.cos(medio * rad)
    const labelY = CY + labelR * Math.sin(medio * rad)
    const pct = Math.round((c.gasto_acumulado / total) * 100)
    ang += grados
    const tieneHijos = categoriasConHijos.has(c.id_categoria)
    const primeraPalabra = c.nombre.split(' ')[0]
    const label = grados >= 28 ? `${primeraPalabra}\n${pct}%` : `${pct}%`
    return {
      id: c.id_categoria, nombre: c.nombre, color: c.color ?? colorDeterministico(c.id_categoria),
      path, labelX, labelY, label, tieneHijos,
    }
  })

  function drill(slice) {
    if (!slice.tieneHijos) return
    setPila(p => [...p, { id: slice.id, nombre: slice.nombre }])
  }

  function volver() {
    setPila(p => p.slice(0, -1))
  }

  return (
    <div className="card bg-white border border-gray-200 rounded-xl p-2.5 flex flex-col items-center gap-1 h-full">
      <div className="w-full flex items-center justify-between min-h-[15px]">
        {nivelActual ? (
          <div className="flex items-center gap-2 text-[11px]">
            <button onClick={volver} className="text-primary-600 hover:text-primary-700 font-semibold">← Atrás</button>
            <span className="text-gray-600 font-medium">{nivelActual.nombre}</span>
          </div>
        ) : (
          <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Gasto por categoría</span>
        )}
      </div>

      {slices.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-xs text-gray-400 italic">Sin gasto para mostrar.</div>
      ) : (
        <div className="relative" style={{ width: 180, height: 180 }}>
          <svg viewBox="0 0 180 180" width="180" height="180">
            {slices.map(s => (
              <path
                key={s.id}
                d={s.path}
                style={{ fill: s.color, stroke: '#fff', strokeWidth: 1.5, cursor: s.tieneHijos ? 'pointer' : 'default' }}
                onClick={() => drill(s)}
              />
            ))}
          </svg>
          {slices.map(s => (
            <span
              key={s.id}
              style={{
                position: 'absolute', left: s.labelX, top: s.labelY, transform: 'translate(-50%, -50%)',
                fontSize: 10.5, fontWeight: 700, color: '#fff', textShadow: '0 1px 2px rgba(0,0,0,.35)',
                pointerEvents: 'none', textAlign: 'center', lineHeight: 1.15, whiteSpace: 'pre-line',
              }}
            >
              {s.label}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
