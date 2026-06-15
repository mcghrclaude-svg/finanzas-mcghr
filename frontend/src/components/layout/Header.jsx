import useAppStore from '@/store/useAppStore'

export default function Header() {
  const toggle = useAppStore(s => s.toggleSidebar)
  const { undoStack, redoStack, undo, redo } = useAppStore()

  return (
    <header className="h-14 bg-white border-b border-gray-200 flex items-center px-4 gap-4 flex-shrink-0">
      <button onClick={toggle} className="p-1.5 rounded hover:bg-gray-100 text-gray-500">
        ☰
      </button>
      <div className="flex items-center gap-2 ml-auto">
        <button
          onClick={undo}
          disabled={!undoStack.length}
          title="Deshacer (Ctrl+Z)"
          className="p-1.5 rounded hover:bg-gray-100 disabled:opacity-30 text-sm"
        >
          ↩ Deshacer
        </button>
        <button
          onClick={redo}
          disabled={!redoStack.length}
          title="Rehacer (Ctrl+Y)"
          className="p-1.5 rounded hover:bg-gray-100 disabled:opacity-30 text-sm"
        >
          Rehacer ↪
        </button>
      </div>
    </header>
  )
}
