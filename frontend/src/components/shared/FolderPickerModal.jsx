/**
 * FolderPickerModal.jsx -- navegador de filesystem local (mismo esqueleto
 * visual que pwa-gastos/src/components/OneDrivePickerModal.jsx, pero contra
 * el filesystem plano via /api/v1/pwa-config/browse-folders en vez de
 * Graph API -- sin login, son carpetas de OneDrive ya sincronizadas en
 * esta PC).
 */
import { useEffect, useState } from 'react'
import { pwaConfigApi } from '@/api/pwaConfig'

function segmentosBreadcrumb(path) {
  if (!path) return []
  const partes = path.split('\\').filter(Boolean)
  return partes.map((nombre, i) => ({
    nombre,
    ruta: i === 0 ? `${nombre}\\` : partes.slice(0, i + 1).join('\\'),
  }))
}

export default function FolderPickerModal({ initialPath, onPick, onCancel }) {
  const [path, setPath] = useState(initialPath || null)
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  async function cargarNivel(rutaAMostrar) {
    setLoading(true)
    setError(null)
    try {
      const data = await pwaConfigApi.browseFolders(rutaAMostrar ?? '')
      setPath(data.path)
      setItems(data.items ?? [])
    } catch (e) {
      setError(e.message)
      setItems([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { cargarNivel(initialPath) }, []) // eslint-disable-line react-hooks/exhaustive-deps

  function abrirCarpeta(folder) {
    cargarNivel(folder.ruta)
  }

  function irARaiz() {
    cargarNivel(null)
  }

  function irABreadcrumb(ruta) {
    cargarNivel(ruta)
  }

  function elegirEstaCarpeta() {
    onPick(path)
  }

  const crumbs = segmentosBreadcrumb(path)

  return (
    <div
      className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4"
      onClick={e => e.target === e.currentTarget && onCancel()}
    >
      <div className="bg-white rounded-xl shadow-lg w-full max-w-lg h-[70vh] flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
          <p className="text-sm font-medium text-gray-700">Choose a folder</p>
          <button onClick={onCancel} className="text-gray-500 hover:text-gray-800 text-sm">
            Close
          </button>
        </div>

        <div className="flex items-center gap-1 px-4 py-2 border-b border-gray-100 text-sm text-gray-600 overflow-x-auto whitespace-nowrap">
          <button
            onClick={irARaiz}
            disabled={!path}
            className={!path ? 'font-medium text-gray-900' : 'text-primary-600 hover:underline'}
          >
            This PC
          </button>
          {crumbs.map((c, i) => (
            <span key={c.ruta} className="flex items-center gap-1">
              <span className="text-gray-300">/</span>
              <button
                onClick={() => irABreadcrumb(c.ruta)}
                disabled={i === crumbs.length - 1}
                className={i === crumbs.length - 1 ? 'font-medium text-gray-900' : 'text-primary-600 hover:underline'}
              >
                {c.nombre}
              </button>
            </span>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto px-2 py-2">
          {loading && <p className="text-sm text-gray-500 px-2 py-4">Loading...</p>}
          {error && <p className="text-sm text-danger-600 px-2 py-4 break-words">{error}</p>}
          {!loading && !error && items.length === 0 && (
            <p className="text-sm text-gray-500 px-2 py-4">No subfolders here.</p>
          )}
          {!loading && !error && items.map(folder => (
            <button
              key={folder.ruta}
              onClick={() => abrirCarpeta(folder)}
              className="w-full flex items-center gap-2 px-2 py-2 text-left text-sm rounded-lg hover:bg-gray-100"
            >
              <span className="text-gray-400 shrink-0">📁</span>
              <span className="text-gray-900 truncate">{folder.nombre}</span>
            </button>
          ))}
        </div>

        <div className="px-4 py-3 border-t border-gray-200">
          <button
            onClick={elegirEstaCarpeta}
            disabled={!path}
            className="w-full rounded-lg bg-primary-600 text-white font-medium py-2.5 hover:bg-primary-700 disabled:opacity-50"
          >
            {path ? `Choose this folder (${path})` : 'Pick a drive first'}
          </button>
        </div>
      </div>
    </div>
  )
}
