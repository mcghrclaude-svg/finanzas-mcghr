/**
 * ModalForm.jsx — modal de alta/edicion. Tailwind puro.
 */
import SelectorBusqueda from './SelectorBusqueda'

export default function ModalForm({ titulo, campos, values, onChange, isEdit, onClose, onGuardar, guardando, extra, onInactivar }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm"
      onClick={e => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[88vh] overflow-y-auto">

        <div className="flex items-center justify-between px-6 pt-5 pb-4 border-b border-gray-100">
          <h2 className="text-base font-semibold text-gray-900">{titulo}</h2>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-600 text-sm"
          >✕</button>
        </div>

        <div className="px-6 py-5 space-y-4">
          {campos.map(campo => {
            const disabled = isEdit && campo.lock_on_edit
            const opciones = typeof campo.options === 'function' ? campo.options(values, extra) : campo.options

            return (
              <div key={campo.key}>
                {campo.type !== 'checkbox' && (
                  <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
                    {campo.label}{campo.required && <span className="text-danger-500 ml-0.5">*</span>}
                  </label>
                )}

                {campo.type === 'checkbox' ? (
                  <label className="flex items-center gap-2 text-sm text-gray-700">
                    <input
                      type="checkbox"
                      checked={values[campo.key] ?? false}
                      onChange={e => onChange(campo.key, e.target.checked)}
                      disabled={disabled}
                      className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-400"
                    />
                    {campo.label}
                  </label>
                ) : campo.type === 'buscador' ? (
                  <SelectorBusqueda
                    value={values[campo.key] ?? null}
                    onChange={v => onChange(campo.key, v)}
                    opciones={opciones ?? []}
                    placeholder={campo.placeholder}
                    disabled={disabled}
                    emptyLabel={campo.emptyLabel}
                  />
                ) : campo.type === 'select' ? (
                  <select
                    value={values[campo.key] ?? ''}
                    onChange={e => onChange(campo.key, e.target.value)}
                    disabled={disabled}
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-primary-400 bg-white disabled:bg-gray-50 disabled:text-gray-400"
                  >
                    <option value="">— Seleccionar —</option>
                    {opciones?.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                ) : (
                  <input
                    type="text"
                    value={values[campo.key] ?? ''}
                    onChange={e => {
                      let v = e.target.value
                      if (campo.upper) v = v.toUpperCase()
                      if (campo.noSlash) v = v.replaceAll('/', '-')
                      onChange(campo.key, v)
                    }}
                    disabled={disabled}
                    placeholder={campo.hint}
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-primary-400 disabled:bg-gray-50 disabled:text-gray-400"
                  />
                )}

                {campo.hint && !disabled && (
                  <p className="mt-1 text-xs text-gray-400">{campo.hint}</p>
                )}
              </div>
            )
          })}
        </div>

        <div className="flex justify-end gap-2 px-6 pb-5">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={onGuardar}
            disabled={guardando}
            className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
          >
            {guardando ? 'Guardando...' : isEdit ? 'Guardar cambios' : 'Crear'}
          </button>
          {isEdit && onInactivar && (
            <button
              onClick={onInactivar}
              disabled={guardando}
              className={`px-4 py-2 text-sm font-medium border rounded-lg disabled:opacity-50 transition-colors ${
                values.activa !== false
                  ? 'text-danger-600 border-danger-200 hover:bg-danger-50'
                  : 'text-success-600 border-success-200 hover:bg-success-50'
              }`}
            >
              {values.activa !== false ? 'Inactivar' : 'Activar'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
