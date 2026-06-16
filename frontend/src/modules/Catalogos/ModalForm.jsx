/**
 * ModalConfirm.jsx
 * Dialogo de confirmacion para inactivar/activar un registro.
 */
export default function ModalConfirm({ item, onClose, onConfirmar, guardando }) {
  const inactivar = item?.activa !== false

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm"
      onClick={e => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm">
        <div className="px-6 pt-5">
          <h2 className="text-base font-semibold text-gray-900">
            {inactivar ? 'Inactivar registro' : 'Activar registro'}
          </h2>
        </div>
        <div className="px-6 py-4">
          <p className="text-sm text-gray-700">
            {inactivar
              ? `Vas a inactivar "${item?.nombre}".`
              : `Vas a activar "${item?.nombre}".`}
          </p>
          <p className="text-xs text-gray-400 mt-1">
            {inactivar
              ? 'El registro no se elimina — queda inactivo y no aparece en selects.'
              : 'El registro volvera a estar disponible en el sistema.'}
          </p>
        </div>
        <div className="flex justify-end gap-2 px-6 pb-5">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50"
          >
            Cancelar
          </button>
          <button
            onClick={onConfirmar}
            disabled={guardando}
            className={`px-4 py-2 text-sm font-medium text-white rounded-lg disabled:opacity-50 ${
              inactivar ? 'bg-red-600 hover:bg-red-700' : 'bg-green-600 hover:bg-green-700'
            }`}
          >
            {guardando ? 'Procesando...' : inactivar ? 'Inactivar' : 'Activar'}
          </button>
        </div>
      </div>
    </div>
  )
}
