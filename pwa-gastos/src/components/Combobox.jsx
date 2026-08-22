import { useState } from 'react'
import { Combobox as HuiCombobox } from '@headlessui/react'

// Combobox generico con busqueda, sobre @headlessui/react.
// options: [{ id, etiqueta }]
export default function Combobox({ label, options, value, onChange, placeholder }) {
  const [query, setQuery] = useState('')

  const filtradas = query === ''
    ? options
    : options.filter((o) => o.etiqueta.toLowerCase().includes(query.toLowerCase()))

  const seleccionada = options.find((o) => o.id === value) ?? null

  return (
    <HuiCombobox immediate value={seleccionada} onChange={(opt) => onChange(opt?.id ?? null)}>
      {label && <HuiCombobox.Label className="block text-sm font-medium text-gray-700 mb-1">{label}</HuiCombobox.Label>}
      <div className="relative">
        <HuiCombobox.Input
          className="w-full rounded-lg border border-gray-300 py-2 px-3 text-base focus:border-blue-500 focus:ring-blue-500"
          displayValue={(opt) => opt?.etiqueta ?? ''}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
        />
        <HuiCombobox.Options className="absolute z-10 mt-1 max-h-56 w-full overflow-auto rounded-lg bg-white py-1 shadow-lg border border-gray-200 text-sm">
          {filtradas.length === 0 ? (
            <div className="px-3 py-2 text-gray-500">Sin resultados</div>
          ) : (
            filtradas.map((opt) => (
              <HuiCombobox.Option
                key={opt.id}
                value={opt}
                className={({ active }) =>
                  `px-3 py-2 cursor-pointer ${active ? 'bg-blue-600 text-white' : 'text-gray-900'}`
                }
              >
                {opt.etiqueta}
              </HuiCombobox.Option>
            ))
          )}
        </HuiCombobox.Options>
      </div>
    </HuiCombobox>
  )
}
