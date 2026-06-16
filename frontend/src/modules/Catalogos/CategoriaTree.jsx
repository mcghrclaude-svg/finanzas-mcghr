/**
 * CategoriaTree.jsx — arbol jerarquico de categorias. Tailwind puro.
 */
import { useState } from 'react'

const PATRON_COLOR = {
  fijo_unico:          'bg-blue-100 text-blue-700',
  fijo_recurrente:     'bg-purple-100 text-purple-700',
  variable_frecuente:  'bg-green-100 text-green-700',
  variable_esporadico: 'bg-amber-100 text-amber-700',
}

function Fila({ cat, depth, expanded, onToggle, onEditar, onInactivar }) {
  const hasKids = cat.hijos?.length > 0
  const isOpen  = expanded[cat.id] !== false

  return (
    <>
      <tr className="hover:bg-gray-50 group">
        <td className="px-4 py-2.5">
          <div className="flex items-center gap-1.5" style={{ paddingLeft: `${depth * 24}px` }}>
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
            <span className="text-sm">{cat.icono ?? '📁'}</span>
            <span className={`text-sm text-gray-900 ${depth === 0 ? 'font-medium' : ''}`}>
              {cat.nombre}
            </span>
          </div>
        </td>
        <td className="px-4 py-2.5">
          <code className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded font-mono">
            {cat.id}
          </code>
        </td>
        <td className="px-4 py-2.5">
          <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${PATRON_COLOR[cat.tipo_patron_gasto] ?? 'bg-gray-100 text-gray-600'}`}>
            {cat.tipo_patron_gasto ?? '—'}
          </span>
        </td>
        <td className="px-4 py-2.5">
          <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${cat.activa !== false ? 'bg-success-100 text-success-500' : 'bg-gray-100 text-gray-400'}`}>
            {cat.activa !== false ? 'Activa' : 'Inactiva'}
          </span>
        </td>
        <td className="px-4 py-2.5 w-20">
          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={() => onEditar(cat)}
              className="p-1 rounded text-gray-400 hover:text-gray-700 hover:bg-gray-100 text-sm"
              title="Editar"
            >✏️</button>
            <button
              onClick={() => onInactivar(cat)}
              className="p-1 rounded text-gray-400 hover:text-danger-500 hover:bg-danger-100 text-sm"
              title={cat.activa !== false ? 'Inactivar' : 'Activar'}
            >{cat.activa !== false ? '🚫' : '✅'}</button>
          </div>
        </td>
      </tr>
      {hasKids && isOpen && cat.hijos.map(hijo => (
        <Fila
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
      <div className="bg-white border border-gray-200 rounded-xl py-20 text-center">
        <div className="text-4xl mb-3">🏷️</div>
        <p className="font-medium text-gray-700">Sin categorias</p>
        <p className="text-sm text-gray-400 mt-1">Usa el boton Nuevo para agregar la primera.</p>
      </div>
    )
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
      <table className="w-full">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            {['Nombre', 'ID', 'Patron de gasto', 'Estado', ''].map(h => (
              <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {items.map(cat => (
            <Fila
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
