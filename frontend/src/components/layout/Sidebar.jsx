import { NavLink } from 'react-router-dom'

const nav = [
  { to: '/dashboard',      label: 'Dashboard',      icon: '📊' },
  { to: '/inbox',          label: 'Inbox',           icon: '📥' },
  { to: '/transacciones',  label: 'Transacciones',   icon: '💳' },
  { to: '/presupuesto',    label: 'Presupuesto',     icon: '💰' },
  { to: '/obligaciones',   label: 'Obligaciones',    icon: '🗓️' },
  { to: '/inversiones',    label: 'Inversiones',     icon: '📈' },
  { to: '/analitica',      label: 'Análisis IA',     icon: '🤖' },
  { to: '/catalogos',      label: 'Catálogos',       icon: '🗂️' },
  { to: '/backup',         label: 'Backup',          icon: '💾' },
]

export default function Sidebar({ open }) {
  if (!open) return null
  return (
    <aside className="w-60 bg-white border-r border-gray-200 flex flex-col flex-shrink-0">
      <div className="h-14 flex items-center px-4 border-b border-gray-200">
        <span className="font-semibold text-primary-700">🏠 Finanzas MCGHR</span>
      </div>
      <nav className="flex-1 py-4 space-y-0.5 overflow-y-auto">
        {nav.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
                isActive
                  ? 'bg-primary-50 text-primary-700 font-medium'
                  : 'text-gray-600 hover:bg-gray-50'
              }`
            }
          >
            <span className="text-base">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
