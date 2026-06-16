/**
 * TablaGenerica.jsx — tabla reutilizable. Tailwind puro.
 */
export default function TablaGenerica({ columnas, items, onEditar, onInactivar }) {
  if (!items?.length) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl py-20 text-center">
        <div className="text-4xl mb-3">📋</div>
        <p className="font-medium text-gray-700">Sin registros</p>
        <p className="text-sm text-gray-400 mt-1">Usa el boton Nuevo para agregar el primero.</p>
      </div>
    )
  }

  function renderCelda(col, item) {
    const val = item[col.key]

    if (col.estado) {
      return val !== false
        ? <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-success-100 text-success-500">Activa</span>
        : <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-400">Inactiva</span>
    }

    if (col.badge) {
      return <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-primary-50 text-primary-700">{val ?? '—'}</span>
    }

    if (col.mono) {
      return <code className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded font-mono">{val ?? '—'}</code>
    }

    return <span className="text-sm text-gray-700">{val ?? '—'}</span>
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
      <table className="w-full">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            {columnas.map(col => (
              <th key={col.key} className="px-4 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                {col.label}
              </th>
            ))}
            <th className="px-4 py-2.5 w-20" />
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {items.map(item => (
            <tr key={item.id} className="hover:bg-gray-50 group">
              {columnas.map(col => (
                <td key={col.key} className="px-4 py-2.5">
                  {renderCelda(col, item)}
                </td>
              ))}
              <td className="px-4 py-2.5">
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => onEditar(item)}
                    className="p-1 rounded text-gray-400 hover:text-gray-700 hover:bg-gray-100 text-sm"
                    title="Editar"
                  >✏️</button>
                  <button
                    onClick={() => onInactivar(item)}
                    className="p-1 rounded text-gray-400 hover:text-danger-500 hover:bg-danger-100 text-sm"
                    title={item.activa !== false ? 'Inactivar' : 'Activar'}
                  >{item.activa !== false ? '🚫' : '✅'}</button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
