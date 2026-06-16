/**
 * ModalForm.jsx
 * Modal generico de alta/edicion para todas las entidades del catalogo.
 * Campos definidos en el padre (index.jsx) como array de { key, label, type, ... }
 */
export default function ModalForm({ titulo, campos, values, onChange, isEdit, onClose, onGuardar, guardando }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm"
      onClick={e => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[88vh] overflow-y-auto">

        {/* Header */}
        <div className="flex items-center justify-between px-6 pt-5 pb-0">
          <h2 className="text-base font-semibold text-gray-900">{titulo}</h2>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-4 grid gap-4">
          {campos.map(campo => {
            const disabled = isEdit && campo.disabled_on_edit
            return (
              <div key={campo.key}>
                <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
                  {campo.label} {campo.required && <span className="text-red-500">*</span>}
                </label>

                {campo.type === 'select' ? (
                  <select
                    value={values[campo.key] ?? ''}
                    onChange={e => onChange(campo.key, e.target.value)}
                    disabled={disabled}
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-primary-400 bg-white disabled:bg-gray-50 disabled:text-gray-400"
                  >
                    <option value="">— Seleccionar —</option>
                    {campo.options?.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                ) : campo.type === 'textarea' ? (
                  <textarea
                    value={values[campo.key] ?? ''}
                    onChange={e => onChange(campo.key, e.target.value)}
                    disabled={disabled}
                    rows={3}
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-primary-400 disabled:bg-gray-50 disabled:text-gray-400"
                  />
                ) : (
                  <input
                    type={campo.type ?? 'text'}
                    value={values[campo.key] ?? ''}
                    onChange={e => onChange(campo.key, campo.uppercase ? e.target.value.toUpperCase() : e.target.value)}
                    disabled={disabled}
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-primary-400 disabled:bg-gray-50 disabled:text-gray-400"
                  />
                )}

                {campo.hint && (
                  <p className="mt-1 text-xs text-gray-400">{campo.hint}</p>
                )}
              </div>
            )
          })}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 px-6 pb-5">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50"
          >
            Cancelar
          </button>
          <button
            onClick={onGuardar}
            disabled={guardando}
            className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50"
          >
            {guardando ? 'Guardando...' : isEdit ? 'Guardar cambios' : 'Crear'}
          </button>
        </div>
      </div>
    </div>
  )
}
