/**
 * TablaGenerica.jsx
 * Tabla reutilizable para cuentas, contrapartes y personas.
 * Recibe columnas con render opcional y acciones por fila.
 */
export default function TablaGenerica({ columnas, items, onEditar, onInactivar }) {
  if (!items?.length) {
    return (
      <div className="text-center py-20 text-gray-400">
        <div className="text-4xl mb-3">📋</div>
        <div className="font-medium text-gray-600">Sin registros</div>
        <div className="text-sm mt-1">Usa el boton Nuevo para agregar el primero.</div>
      </div>
    )
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
      <table className="w-full">
        <thead className="bg-gray-50">
          <tr>
            {columnas.map(col => (
              <th
                key={col.key}
                className="px-4 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider"
              >
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
                <td key={col.key} className="px-4 py-2.5 text-sm text-gray-700">
                  {col.render
                    ? col.render(item[col.key], item)
                    : col.key === 'id'
                      ? <code className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">{item[col.key]}</code>
                      : (item[col.key] ?? '—')
                  }
                </td>
              ))}
              <td className="px-4 py-2.5">
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => onEditar(item)}
                    className="p-1 rounded text-gray-400 hover:text-gray-700 hover:bg-gray-100 text-xs"
                    title="Editar"
                  >
                    ✏️
                  </button>
                  <button
                    onClick={() => onInactivar(item)}
                    className="p-1 rounded text-gray-400 hover:text-red-600 hover:bg-red-50 text-xs"
                    title={item.activa !== false ? 'Inactivar' : 'Activar'}
                  >
                    {item.activa !== false ? '🚫' : '✅'}
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
