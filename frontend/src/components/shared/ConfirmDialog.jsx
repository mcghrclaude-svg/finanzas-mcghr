/**
 * Diálogo de confirmación reutilizable para acciones destructivas.
 * Uso:
 *   <ConfirmDialog
 *     open={open}
 *     titulo="Descartar transacción"
 *     mensaje="Esta acción no se puede deshacer. ¿Continuar?"
 *     onConfirm={handleConfirm}
 *     onCancel={() => setOpen(false)}
 *     peligroso  // botón rojo
 *   />
 */

export default function ConfirmDialog({ open, titulo, mensaje, onConfirm, onCancel, peligroso }) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onCancel} />
      <div className="relative bg-white rounded-xl shadow-xl p-6 w-full max-w-sm mx-4">
        <h2 className="font-semibold text-gray-900 mb-2">{titulo}</h2>
        <p className="text-gray-600 text-sm mb-6">{mensaje}</p>
        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm rounded-lg border border-gray-200 hover:bg-gray-50"
          >
            Cancelar
          </button>
          <button
            onClick={onConfirm}
            className={`px-4 py-2 text-sm rounded-lg text-white font-medium ${
              peligroso ? 'bg-red-600 hover:bg-red-700' : 'bg-primary-600 hover:bg-primary-700'
            }`}
          >
            Confirmar
          </button>
        </div>
      </div>
    </div>
  )
}
