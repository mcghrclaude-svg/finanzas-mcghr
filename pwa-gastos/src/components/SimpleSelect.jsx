import { Listbox } from '@headlessui/react'

// Select simple sin texto libre ni filtro: tocar despliega la lista
// completa, un tap selecciona y cierra. Para catalogos chicos y estables
// (Moneda, Medio de pago). Para campos que necesitan busqueda (ej:
// Categoria) usar Combobox en su lugar.
// options: [{ id, etiqueta }]
export default function SimpleSelect({ label, options, value, onChange, placeholder }) {
  const seleccionada = options.find((o) => o.id === value) ?? null

  return (
    <Listbox value={seleccionada} onChange={(opt) => onChange(opt?.id ?? null)}>
      {label && <Listbox.Label className="block text-sm font-medium text-gray-700 mb-1">{label}</Listbox.Label>}
      <div className="relative">
        <Listbox.Button className="w-full rounded-lg border border-gray-300 py-2 px-3 text-base text-left focus:border-blue-500 focus:ring-blue-500">
          <span className={`block truncate ${seleccionada ? 'text-gray-900' : 'text-gray-400'}`}>
            {seleccionada ? seleccionada.etiqueta : (placeholder ?? 'Seleccionar...')}
          </span>
        </Listbox.Button>
        <Listbox.Options className="absolute z-10 mt-1 max-h-56 w-full overflow-auto rounded-lg bg-white py-1 shadow-lg border border-gray-200 text-sm">
          {options.length === 0 ? (
            <div className="px-3 py-2 text-gray-500">Sin opciones</div>
          ) : (
            options.map((opt) => (
              <Listbox.Option
                key={opt.id}
                value={opt}
                className={({ active }) =>
                  `px-3 py-2 cursor-pointer ${active ? 'bg-blue-600 text-white' : 'text-gray-900'}`
                }
              >
                {opt.etiqueta}
              </Listbox.Option>
            ))
          )}
        </Listbox.Options>
      </div>
    </Listbox>
  )
}
