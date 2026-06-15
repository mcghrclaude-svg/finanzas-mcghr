/**
 * Barra flotante que aparece cuando hay acciones en la pila de Undo.
 * Similar al snackbar de Google Sheets: "[Accion] Deshacer"
 */

import useAppStore from '@/store/useAppStore'

export default function UndoBar() {
  const { undoStack, undo } = useAppStore()
  if (!undoStack.length) return null
  const ultima = undoStack[undoStack.length - 1]

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50">
      <div className="bg-gray-800 text-white text-sm px-4 py-2.5 rounded-lg shadow-lg flex items-center gap-4">
        <span>{ultima.descripcion}</span>
        <button
          onClick={undo}
          className="font-semibold text-primary-300 hover:text-primary-200 uppercase text-xs tracking-wide"
        >
          Deshacer
        </button>
      </div>
    </div>
  )
}
