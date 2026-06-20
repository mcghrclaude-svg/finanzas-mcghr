/**
 * Header.jsx — Version A
 * Cambios:
 *   - Toggle sidebar: muestra << cuando esta abierto, >> cuando esta cerrado
 *   - Elimina el texto "Deshacer/Rehacer" y usa solo iconos con tooltip
 */
import useAppStore from '@/store/useAppStore'

export default function Header() {
  const toggle      = useAppStore(s => s.toggleSidebar)
  const sidebarOpen = useAppStore(s => s.sidebarOpen)
  const { undoStack, redoStack, undo, redo } = useAppStore()

  return (
    <header className="h-14 bg-white border-b border-gray-200 flex items-center px-4 gap-3 flex-shrink-0">
      {/* Toggle sidebar con direccion clara */}
      <button
        onClick={toggle}
        className="p-1.5 rounded hover:bg-gray-100 text-gray-500 text-sm font-medium transition-colors"
        title={sidebarOpen ? 'Hide sidebar' : 'Show sidebar'}
        aria-label={sidebarOpen ? 'Ocultar barra lateral' : 'Mostrar barra lateral'}
      >
        {sidebarOpen ? '◀' : '▶'}
      </button>

      <div className="flex items-center gap-1 ml-auto">
        <button
          onClick={undo}
          disabled={!undoStack.length}
          title="Deshacer (Ctrl+Z)"
          className="p-1.5 rounded hover:bg-gray-100 disabled:opacity-30 text-gray-500 text-sm transition-colors"
          aria-label="Deshacer"
        >
          ↩
        </button>
        <button
          onClick={redo}
          disabled={!redoStack.length}
          title="Rehacer (Ctrl+Y)"
          className="p-1.5 rounded hover:bg-gray-100 disabled:opacity-30 text-gray-500 text-sm transition-colors"
          aria-label="Rehacer"
        >
          ↪
        </button>
      </div>
    </header>
  )
}
