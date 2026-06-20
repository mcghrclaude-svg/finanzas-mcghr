/**
 * Sidebar.jsx — Version A
 * Navegacion multinivel, labels en ingles, chevron para grupos.
 * Cambios vs original:
 *   - Dashboard -> Home
 *   - Presupuesto -> Budget Mgmt
 *   - Grupo "Financial View": Debt (Obligaciones) + Investments (Inversiones)
 *   - Grupo "Settings": Catalogs (Catalogos)
 *   - Icono header: pareja feliz
 *   - Toggle sidebar: flechas << >> en lugar de hamburguer
 */
import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import useAppStore from '@/store/useAppStore'

// Items planos (sin grupo)
const NAV_ITEMS = [
  { to: '/dashboard',     label: 'Home',         icon: '🏠' },
  { to: '/inbox',         label: 'Inbox',         icon: '📥' },
  { to: '/transacciones', label: 'Transactions',  icon: '💳' },
  { to: '/presupuesto',   label: 'Budget Mgmt',   icon: '💰' },
  { to: '/analitica',     label: 'AI Analysis',   icon: '🤖' },
  { to: '/backup',        label: 'Backup',        icon: '💾' },
]

// Grupos con submenus
const NAV_GROUPS = [
  {
    id: 'financial',
    label: 'Financial View',
    icon: '📊',
    items: [
      { to: '/obligaciones', label: 'Debt',        icon: '🗓️' },
      { to: '/inversiones',  label: 'Investments', icon: '📈' },
    ],
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: '⚙️',
    items: [
      { to: '/catalogos', label: 'Catalogs', icon: '🗂️' },
    ],
  },
]

// Orden de renderizado
const NAV_ORDER = [
  'home', 'inbox', 'transactions', 'budget',
  'financial', // grupo
  'ai', 'settings', // grupo
  'backup',
]

function NavGroup({ group }) {
  const [open, setOpen] = useState(false)

  return (
    <div>
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-gray-600 hover:bg-gray-50 transition-colors"
      >
        <span className="text-base">{group.icon}</span>
        <span className="flex-1 text-left">{group.label}</span>
        <span className={`text-xs text-gray-400 transition-transform duration-150 ${open ? 'rotate-90' : ''}`}>
          ›
        </span>
      </button>
      {open && (
        <div className="ml-4 border-l border-gray-100">
          {group.items.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 pl-4 pr-4 py-2 text-sm transition-colors ${
                  isActive
                    ? 'text-primary-700 font-medium bg-primary-50'
                    : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'
                }`
              }
            >
              <span className="text-sm">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </div>
      )}
    </div>
  )
}

export default function Sidebar({ open }) {
  if (!open) return null
  return (
    <aside className="w-60 bg-white border-r border-gray-200 flex flex-col flex-shrink-0">
      {/* Header */}
      <div className="h-14 flex items-center px-4 border-b border-gray-200">
        <span className="font-semibold text-primary-700">👫 Finanzas MCGHR</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-2 overflow-y-auto">
        {/* Items planos hasta Financial View */}
        {NAV_ITEMS.slice(0, 4).map(item => (
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

        {/* Grupo Financial View */}
        <NavGroup group={NAV_GROUPS[0]} />

        {/* Items intermedios: AI Analysis */}
        {NAV_ITEMS.slice(4, 5).map(item => (
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

        {/* Grupo Settings */}
        <NavGroup group={NAV_GROUPS[1]} />

        {/* Backup al final */}
        {NAV_ITEMS.slice(5).map(item => (
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
