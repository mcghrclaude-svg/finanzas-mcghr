/**
 * Layout.jsx v3
 *
 * Cambios:
 *   - Header eliminado completamente
 *   - El boton toggle del sidebar vive DENTRO del sidebar (punto rojo)
 *   - UndoBar sigue como snackbar flotante
 *   - El main no tiene padding propio -- cada modulo decide su padding
 */
import Sidebar from './Sidebar'
import UndoBar from '@/components/shared/UndoBar'

export default function Layout({ children }) {
  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden min-w-0">
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
      <UndoBar />
    </div>
  )
}
