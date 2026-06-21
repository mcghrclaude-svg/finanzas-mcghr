/**
 * Sidebar.jsx -- estilo Outlook/Office 365
 *
 * Collapsed: iconos grandes (text-xl) con tooltip en hover -- igual a Outlook
 * Expanded:  icono + label, grupos con chevron
 *
 * Orden de menu:
 *   Home
 *   Transactions  (unifica inbox + transacciones, URL /transacciones)
 *   Budget Mgmt
 *   AI Analysis
 *   [grupo] Financial View > Debt, Investments
 *   Backup
 *   [grupo] Settings > Catalogs
 */
import { useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import useAppStore from '@/store/useAppStore'

// ── Items planos ──────────────────────────────────────────────────────────────
const NAV_FLAT = [
  { to: '/dashboard',     label: 'Home',         icon: '🏠' },
  { to: '/transacciones', label: 'Transactions',  icon: '📋' },
  { to: '/presupuesto',   label: 'Budget Mgmt',   icon: '💰' },
  { to: '/analitica',     label: 'AI Analysis',   icon: '🤖' },
]

const NAV_BOTTOM = [
  { to: '/backup', label: 'Backup', icon: '💾' },
]

// ── Grupos ────────────────────────────────────────────────────────────────────
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

// ── Componente NavItem (funciona en collapsed y expanded) ─────────────────────
function NavItem({ to, label, icon, collapsed }) {
  return (
    <NavLink
      to={to}
      title={collapsed ? label : undefined}
      className={({ isActive }) =>
        `relative group flex items-center transition-colors ${
          collapsed
            ? 'justify-center w-full py-3 px-0'
            : 'gap-3 px-4 py-2.5'
        } text-sm ${
          isActive
            ? 'bg-primary-50 text-primary-700 font-medium'
            : 'text-gray-600 hover:bg-gray-100'
        }`
      }
    >
      <span className={collapsed ? 'text-xl' : 'text-base w-5 text-center flex-shrink-0'}>
        {icon}
      </span>
      {!collapsed && <span>{label}</span>}

      {/* Tooltip en collapsed */}
      {collapsed && (
        <span className="
          pointer-events-none absolute left-full ml-2 z-50
          px-2 py-1 text-xs font-medium text-white bg-gray-800 rounded whitespace-nowrap
          opacity-0 group-hover:opacity-100 transition-opacity duration-150
        ">
          {label}
        </span>
      )}
    </NavLink>
  )
}

// ── Componente NavGroup ───────────────────────────────────────────────────────
function NavGroup({ group, collapsed }) {
  const [open, setOpen] = useState(false)
  const location = useLocation()
  const isChildActive = group.items.some(i => location.pathname.startsWith(i.to))

  if (collapsed) {
    // En collapsed: mostrar solo el icono del grupo, con tooltip
    return (
      <div className="relative group">
        <button
          onClick={() => setOpen(o => !o)}
          className={`w-full flex justify-center py-3 transition-colors ${
            isChildActive ? 'text-primary-700 bg-primary-50' : 'text-gray-500 hover:bg-gray-100'
          }`}
          title={group.label}
        >
          <span className="text-xl">{group.icon}</span>
        </button>
        {/* Tooltip con submenu en collapsed */}
        <div className="
          pointer-events-none group-hover:pointer-events-auto
          absolute left-full top-0 ml-2 z-50 min-w-40
          bg-white border border-gray-200 rounded-lg shadow-lg py-1
          opacity-0 group-hover:opacity-100 transition-opacity duration-150
        ">
          <div className="px-3 py-1.5 text-xs font-semibold text-gray-400 uppercase tracking-wider border-b border-gray-100 mb-1">
            {group.label}
          </div>
          {group.items.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-2 px-3 py-2 text-sm transition-colors ${
                  isActive ? 'text-primary-700 font-medium' : 'text-gray-600 hover:bg-gray-50'
                }`
              }
            >
              <span>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </div>
      </div>
    )
  }

  // Expanded
  return (
    <div>
      <button
        onClick={() => setOpen(o => !o)}
        className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
          isChildActive ? 'text-primary-700' : 'text-gray-600 hover:bg-gray-100'
        }`}
      >
        <span className="text-base w-5 text-center flex-shrink-0">{group.icon}</span>
        <span className="flex-1 text-left">{group.label}</span>
        <span className={`text-xs text-gray-400 transition-transform duration-150 ${open || isChildActive ? 'rotate-90' : ''}`}>
          ›
        </span>
      </button>
      {(open || isChildActive) && (
        <div className="ml-5 border-l border-gray-200">
          {group.items.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-2.5 pl-4 pr-4 py-2 text-sm transition-colors ${
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

// ── Sidebar principal ─────────────────────────────────────────────────────────
export default function Sidebar() {
  const sidebarOpen = useAppStore(s => s.sidebarOpen)
  const collapsed = !sidebarOpen

  return (
    <aside className={`
      bg-white border-r border-gray-200 flex flex-col flex-shrink-0
      transition-all duration-200
      ${collapsed ? 'w-14' : 'w-56'}
    `}>
      {/* Logo */}
      <div className={`
        h-14 flex items-center border-b border-gray-200 flex-shrink-0
        ${collapsed ? 'justify-center px-0' : 'px-4 gap-2'}
      `}>
        {collapsed ? (
          <span className="text-xl" title="Finanzas MCGHR">👫</span>
        ) : (
          <>
            <span className="text-lg">👫</span>
            <span className="text-sm font-semibold text-primary-700 truncate">Finanzas MCGHR</span>
          </>
        )}
      </div>

      {/* Nav principal */}
      <nav className="flex-1 py-1 overflow-y-auto overflow-x-hidden">
        {/* Items planos superiores */}
        {NAV_FLAT.map(item => (
          <NavItem key={item.to} {...item} collapsed={collapsed} />
        ))}

        {/* Separador */}
        <div className={`my-1 ${collapsed ? 'mx-3' : 'mx-4'} border-t border-gray-100`} />

        {/* Grupo Financial View */}
        <NavGroup group={NAV_GROUPS[0]} collapsed={collapsed} />

        {/* Separador */}
        <div className={`my-1 ${collapsed ? 'mx-3' : 'mx-4'} border-t border-gray-100`} />

        {/* Backup */}
        {NAV_BOTTOM.map(item => (
          <NavItem key={item.to} {...item} collapsed={collapsed} />
        ))}

        {/* Grupo Settings */}
        <NavGroup group={NAV_GROUPS[1]} collapsed={collapsed} />
      </nav>
    </aside>
  )
}
