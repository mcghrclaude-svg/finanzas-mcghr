/**
 * PersonalizarWidgets — muestra/oculta los widgets opcionales del Home
 * (banner de insight, Evolución patrimonio, Ask Claude). La preferencia
 * vive en el backend (GET/PATCH /home-config), no en localStorage, para que
 * sea la misma sin importar el dispositivo. Presupuesto, transacciones y
 * los KPIs no son opcionales.
 */
import { useState, useRef, useEffect } from 'react'

const OPCIONES = [
  { key: 'insight_visible', label: 'Aviso de patrón inusual' },
  { key: 'patrimonio_visible', label: 'Evolución patrimonio' },
  { key: 'ask_visible', label: 'Preguntale a Claude' },
]

export default function PersonalizarWidgets({ homeConfig, onCambiar }) {
  const [abierto, setAbierto] = useState(false)
  const ref = useRef()

  useEffect(() => {
    function handler(e) {
      if (ref.current && !ref.current.contains(e.target)) setAbierto(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  if (!homeConfig) return null

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setAbierto(o => !o)}
        className="px-4 py-2 text-sm font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
      >
        ⚙︎ Personalizar widgets
      </button>
      {abierto && (
        <div className="absolute right-0 top-[calc(100%+6px)] z-20 w-60 bg-white border border-gray-200 rounded-xl shadow-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Widgets opcionales</span>
            <button onClick={() => setAbierto(false)} className="text-primary-600 text-xs font-medium">✕</button>
          </div>
          {OPCIONES.map(o => (
            <label key={o.key} className="flex items-center gap-2 text-sm py-1 cursor-pointer">
              <input
                type="checkbox"
                checked={!!homeConfig[o.key]}
                onChange={e => onCambiar({ [o.key]: e.target.checked })}
                className="w-4 h-4 accent-primary-600"
              />
              {o.label}
            </label>
          ))}
          <div className="text-[10px] text-gray-400 mt-2 pt-2 border-t border-gray-100">
            Presupuesto, transacciones y KPIs no se pueden ocultar.
          </div>
        </div>
      )}
    </div>
  )
}
