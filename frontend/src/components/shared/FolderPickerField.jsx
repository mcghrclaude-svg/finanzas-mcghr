/**
 * FolderPickerField.jsx -- fila "label + carpeta elegida + boton Choose",
 * mismo patron visual que FolderRow de pwa-gastos/src/modules/Configuracion.
 * Envuelve FolderPickerModal para campos de carpeta unica.
 */
import { useState } from 'react'
import FolderPickerModal from './FolderPickerModal'

export default function FolderPickerField({ label, value, onChange, initialPath }) {
  const [abierto, setAbierto] = useState(false)

  function handlePick(ruta) {
    setAbierto(false)
    onChange(ruta)
  }

  return (
    <div>
      <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
        {label}
      </label>
      <div className="flex items-center justify-between gap-3 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2.5">
        <code className="text-xs text-gray-700 truncate">
          {value || <span className="text-gray-400 italic">Not configured</span>}
        </code>
        <button
          onClick={() => setAbierto(true)}
          className="shrink-0 px-3 py-1.5 text-xs font-medium text-primary-700 border border-primary-200 rounded-lg hover:bg-primary-50"
        >
          Choose
        </button>
      </div>

      {abierto && (
        <FolderPickerModal
          initialPath={value || initialPath}
          onPick={handlePick}
          onCancel={() => setAbierto(false)}
        />
      )}
    </div>
  )
}
