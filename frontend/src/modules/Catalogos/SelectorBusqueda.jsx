/**
 * SelectorBusqueda.jsx -- combobox generico con busqueda por texto. Tailwind
 * puro, sin dependencias externas (sin @headlessui/react).
 * opciones: [{ value, label }]
 */
import { useState, useRef, useEffect } from 'react'

export default function SelectorBusqueda({ value, onChange, opciones, placeholder, disabled, emptyLabel }) {
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const containerRef = useRef(null)

  useEffect(() => {
    function onClickFuera(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickFuera)
    return () => document.removeEventListener('mousedown', onClickFuera)
  }, [])

  const seleccionada = opciones.find(o => o.value === value) ?? null

  const filtradas = query === ''
    ? opciones
    : opciones.filter(o => o.label.toLowerCase().includes(query.toLowerCase()))

  function seleccionar(opt) {
    onChange(opt?.value ?? null)
    setQuery('')
    setOpen(false)
  }

  return (
    <div ref={containerRef} className="relative">
      <input
        type="text"
        value={open ? query : (seleccionada?.label ?? '')}
        onChange={e => { setQuery(e.target.value); setOpen(true) }}
        onFocus={() => { setQuery(''); setOpen(true) }}
        onKeyDown={e => e.key === 'Escape' && setOpen(false)}
        disabled={disabled}
        placeholder={placeholder}
        className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-primary-400 disabled:bg-gray-50 disabled:text-gray-400"
      />
      {open && (
        <div className="absolute z-10 mt-1 max-h-56 w-full overflow-auto rounded-lg bg-white py-1 shadow-lg border border-gray-200 text-sm">
          {emptyLabel && (
            <div
              onMouseDown={() => seleccionar(null)}
              className="px-3 py-2 cursor-pointer text-gray-500 hover:bg-primary-50"
            >
              {emptyLabel}
            </div>
          )}
          {filtradas.length === 0 ? (
            <div className="px-3 py-2 text-gray-400">Sin resultados</div>
          ) : (
            filtradas.map(opt => (
              <div
                key={opt.value}
                onMouseDown={() => seleccionar(opt)}
                className={`px-3 py-2 cursor-pointer hover:bg-primary-50 ${opt.value === value ? 'bg-primary-50 text-primary-700' : 'text-gray-900'}`}
              >
                {opt.label}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
