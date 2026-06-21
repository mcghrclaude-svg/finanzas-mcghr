/**
 * Layout.jsx
 * El Sidebar ahora maneja su propio ancho segun el estado open/collapsed.
 * No le pasamos `open` como prop -- el Sidebar lee el store directamente.
 */
import Sidebar from './Sidebar'
import Header from './Header'
import UndoBar from '@/components/shared/UndoBar'

export default function Layout({ children }) {
  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden min-w-0">
        <Header />
        <UndoBar />
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
