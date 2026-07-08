/**
 * Sidebar.jsx v3 -- estilo Outlook
 *
 * Cambios vs v2:
 *   - Boton toggle DENTRO del sidebar (arriba a la derecha del bloque lateral)
 *   - Sin Header separado -- el sidebar arranca desde arriba
 *   - Iconos grandes (text-xl) siempre, tanto collapsed como expanded
 *   - Collapsed: solo iconos + tooltip hover en label
 *   - Expanded: icono grande + label
 *   - Ancho ajustable por drag (resizable)
 *   - Grupos con chevron y submenu flotante en collapsed
 */
import { useState, useRef, useCallback, useEffect } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import useAppStore from '@/store/useAppStore'

const SIDEBAR_MIN  = 48   // collapsed (solo iconos)
const SIDEBAR_DEFAULT = 220
const SIDEBAR_MAX  = 320

const NAV_FLAT = [
  { to: '/dashboard',     label: 'Home',        icon: '🏠' },
  { to: '/transacciones', label: 'Transactions', icon: '📋' },
  { to: '/presupuesto',   label: 'Budget Mgmt',  icon: '💰' },
  { to: '/analitica',     label: 'AI Analysis',  icon: '🤖' },
]

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
      { to: '/backup',    label: 'Backup',   icon: '💾' },
      ...(import.meta.env.VITE_ENV === 'dev' ? [
        { to: '/tools',        label: 'Tools',       icon: '🔧' },
        { to: '/catalogos-v2', label: 'Catalogs V2', icon: '🌳' },
      ] : []),
    ],
  },
]

// ── NavItem ────────────────────────────────────────────────────────────────────
function NavItem({ to, label, icon, collapsed }) {
  return (
    <NavLink
      to={to}
      title={label}
      className={({ isActive }) =>
        `relative group flex items-center transition-colors rounded-lg mx-1 ${
          collapsed ? 'justify-center py-2.5 px-0' : 'gap-3 px-3 py-2.5'
        } ${
          isActive
            ? 'bg-primary-50 text-primary-700 font-medium'
            : 'text-gray-600 hover:bg-gray-100'
        }`
      }
    >
      <span className="text-xl flex-shrink-0">{icon}</span>
      {!collapsed && <span className="text-sm truncate">{label}</span>}
      {collapsed && (
        <span className="
          pointer-events-none absolute left-full ml-2 z-50
          px-2 py-1 text-xs font-medium text-white bg-gray-800 rounded whitespace-nowrap
          opacity-0 group-hover:opacity-100 transition-opacity duration-100
        ">
          {label}
        </span>
      )}
    </NavLink>
  )
}

// ── NavGroup ───────────────────────────────────────────────────────────────────
function NavGroup({ group, collapsed }) {
  const [open, setOpen] = useState(false)
  const location = useLocation()
  const isChildActive = group.items.some(i => location.pathname.startsWith(i.to))

  if (collapsed) {
    return (
      <div className="relative group mx-1">
        <button
          className={`w-full flex justify-center py-2.5 rounded-lg transition-colors ${
            isChildActive ? 'bg-primary-50 text-primary-700' : 'text-gray-500 hover:bg-gray-100'
          }`}
          title={group.label}
        >
          <span className="text-xl">{group.icon}</span>
        </button>
        {/* Submenu flotante en hover */}
        <div className="
          pointer-events-none group-hover:pointer-events-auto
          absolute left-full top-0 ml-2 z-50 min-w-44
          bg-white border border-gray-200 rounded-xl shadow-lg py-2
          opacity-0 group-hover:opacity-100 transition-opacity duration-150
        ">
          <div className="px-3 pb-1.5 mb-1 border-b border-gray-100">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">{group.label}</span>
          </div>
          {group.items.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-3 py-2 text-sm transition-colors ${
                  isActive ? 'text-primary-700 font-medium bg-primary-50' : 'text-gray-600 hover:bg-gray-50'
                }`
              }
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="mx-1">
      <button
        onClick={() => setOpen(o => !o)}
        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
          isChildActive ? 'text-primary-700' : 'text-gray-600 hover:bg-gray-100'
        }`}
      >
        <span className="text-xl flex-shrink-0">{group.icon}</span>
        <span className="flex-1 text-left">{group.label}</span>
        <span className={`text-xs text-gray-400 transition-transform duration-150 ${
          open || isChildActive ? 'rotate-90' : ''
        }`}>›</span>
      </button>
      {(open || isChildActive) && (
        <div className="ml-8 border-l border-gray-200 mt-0.5 mb-0.5">
          {group.items.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-2.5 pl-3 pr-3 py-2 text-sm rounded-r-lg transition-colors ${
                  isActive
                    ? 'text-primary-700 font-medium bg-primary-50'
                    : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'
                }`
              }
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Sidebar principal ──────────────────────────────────────────────────────────
export default function Sidebar() {
  const sidebarOpen = useAppStore(s => s.sidebarOpen)
  const toggleSidebar = useAppStore(s => s.toggleSidebar)
  const collapsed = !sidebarOpen

  // Ancho ajustable por drag
  const [width, setWidth] = useState(SIDEBAR_DEFAULT)
  const dragging = useRef(false)
  const startX = useRef(0)
  const startW = useRef(0)

  const onMouseDown = useCallback((e) => {
    if (collapsed) return
    dragging.current = true
    startX.current = e.clientX
    startW.current = width
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }, [collapsed, width])

  useEffect(() => {
    function onMove(e) {
      if (!dragging.current) return
      const delta = e.clientX - startX.current
      const newW = Math.max(SIDEBAR_MIN + 80, Math.min(SIDEBAR_MAX, startW.current + delta))
      setWidth(newW)
    }
    function onUp() {
      dragging.current = false
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
    return () => {
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
  }, [])

  const currentWidth = collapsed ? SIDEBAR_MIN : width

  return (
    <div className="relative flex-shrink-0 flex" style={{ width: currentWidth }}>
      <aside
        className="bg-white border-r border-gray-200 flex flex-col overflow-hidden h-full"
        style={{ width: currentWidth }}
      >
        {/* Logo + toggle en la misma fila */}
        <div className={`flex items-center border-b border-gray-200 flex-shrink-0 h-12 ${
          collapsed ? 'justify-center px-0' : 'px-3 gap-2'
        }`}>
          {!collapsed && (
            <span className="text-sm font-semibold text-primary-700 flex-1 truncate">
              👫 Finanzas MCGHR
            </span>
          )}
          {/* Boton toggle -- arriba a la derecha del sidebar */}
          <button
            onClick={toggleSidebar}
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors flex-shrink-0 text-sm"
          >
            {collapsed ? '▶' : '◀'}
          </button>
          {collapsed && (
            <span className="text-lg">👫</span>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 py-2 overflow-y-auto overflow-x-hidden space-y-0.5">
          {NAV_FLAT.map(item => (
            <NavItem key={item.to} {...item} collapsed={collapsed} />
          ))}

          <div className={`my-1.5 ${collapsed ? 'mx-2' : 'mx-3'} border-t border-gray-100`} />

          <NavGroup group={NAV_GROUPS[0]} collapsed={collapsed} />

          <div className={`my-1.5 ${collapsed ? 'mx-2' : 'mx-3'} border-t border-gray-100`} />

          <NavGroup group={NAV_GROUPS[1]} collapsed={collapsed} />
        </nav>
      </aside>

      {/* Handle para resize -- solo en expanded */}
      {!collapsed && (
        <div
          onMouseDown={onMouseDown}
          className="absolute right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-primary-200 transition-colors z-10"
          title="Drag to resize"
        />
      )}
    </div>
  )
}
