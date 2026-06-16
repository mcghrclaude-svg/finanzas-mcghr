/**
 * CategoriaTree.jsx
 * Arbol jerarquico de categorias con expand/collapse y acciones por fila.
 */
import { useState } from 'react'

function FilaCategoria({ cat, depth, expanded, onToggle, onEditar, onInactivar }) {
  const hasKids = cat.hijos?.length > 0
  const isOpen  = expanded[cat.id] !== false

  return (
    <>
      <tr className="hover:bg-gray-50 group">
        <td className="px-4 py-2.5 flex items-center gap-1.5" style={{ paddingLeft: `${16 + depth * 24}px` }}>
          {/* Toggle */}
          {hasKids ? (
            <button
              onClick={() => onToggle(cat.id)}
              className="w-5 h-5 flex items-center justify-center rounded text-xs text-gray-400 hover:bg-gray-200 flex-shrink-0"
            >
              {isOpen ? '▾' : '▸'}
            </button>
          ) : (
            <span className="w-5 flex-shrink-0" />
          )}
          <span className="text-base">{cat.icono ?? '📁'}</span>
          <span className="text-sm text-gray-900">{cat.nombre}</span>
        </td>
        <td className="px-4 py-2.5">
          <code className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">{cat.id}</code>
        </td>
        <td className="px-4 py-2.5">
          <span className="text-xs text-gray-500">{cat.tipo_patron_gasto ?? '—'}</span>
        </td>
        <td className="px-4 py-2.5">
          {cat.activa !== false
            ? <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">Activa</span>
            : <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-500">Inactiva</span>
          }
        </td>
        <td className="px-4 py-2.5">
          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={() => onEditar(cat)}
              className="p-1 rounded text-gray-400 hover:text-gray-700 hover:bg-gray-100 text-xs"
              title="Editar"
            >
              ✏️
            </button>
            <button
              onClick={() => onInactivar(cat)}
              className="p-1 rounded text-gray-400 hover:text-red-600 hover:bg-red-50 text-xs"
              title={cat.activa !== false ? 'Inactivar' : 'Activar'}
            >
              {cat.activa !== false ? '🚫' : '✅'}
            </button>
          </div>
        </td>
      </tr>
      {hasKids && isOpen && cat.hijos.map(hijo => (
        <FilaCategoria
          key={hijo.id}
          cat={hijo}
          depth={depth + 1}
          expanded={expanded}
          onToggle={onToggle}
          onEditar={onEditar}
          onInactivar={onInactivar}
        />
      ))}
    </>
  )
}

export default function CategoriaTree({ items, onEditar, onInactivar }) {
  const [expanded, setExpanded] = useState({})

  function onToggle(id) {
    setExpanded(prev => ({ ...prev, [id]: prev[id] === false ? true : false }))
  }

  if (!items?.length) {
    return (
      <div className="text-center py-20 text-gray-400">
        <div className="text-4xl mb-3">🏷️</div>
        <div className="font-medium text-gray-600">Sin categorias</div>
        <div className="text-sm mt-1">Usa el boton Nuevo para agregar la primera.</div>
      </div>
    )
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
      <table className="w-full">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Nombre</th>
            <th className="px-4 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">ID</th>
            <th className="px-4 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Patron gasto</th>
            <th className="px-4 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Estado</th>
            <th className="px-4 py-2.5 w-20"></th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {items.map(cat => (
            <FilaCategoria
              key={cat.id}
              cat={cat}
              depth={0}
              expanded={expanded}
              onToggle={onToggle}
              onEditar={onEditar}
              onInactivar={onInactivar}
            />
          ))}
        </tbody>
      </table>
    </div>
  )
}
