import Sidebar from './Sidebar'
import Header from './Header'
import UndoBar from '@/components/shared/UndoBar'
import useAppStore from '@/store/useAppStore'

export default function Layout({ children }) {
  const sidebarOpen = useAppStore(s => s.sidebarOpen)

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <Sidebar open={sidebarOpen} />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header />
        <UndoBar />
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
