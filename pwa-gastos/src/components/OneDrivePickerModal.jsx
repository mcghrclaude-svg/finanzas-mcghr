import { useEffect, useState } from 'react'
import { getAccessToken, getMyDriveId, listChildren } from '../api/graphClient'
import { FolderIcon } from './icons'

// Selector de carpetas propio, sobre Graph API directa. Reemplaza al widget
// oficial "OneDrive File Picker v8" de Microsoft (iframe + postMessage):
// tras horas de debugging (target del form, URL del endpoint, input de
// access_token, scope de SharePoint bloqueado para cuentas personales por
// AADSTS9002332) se confirmo manualmente que un fetch directo a Graph
// (mismo token de Files.ReadWrite.All que ya usa el resto de la app) resuelve
// lo mismo con muchisimo menos superficie de fallo.
const RAIZ = { id: 'root', nombre: 'Mi OneDrive' }

export default function OneDrivePickerModal({ account, onPick, onCancel }) {
  const [driveId, setDriveId] = useState(null)
  const [path, setPath] = useState([RAIZ])
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const nivelActual = path[path.length - 1]

  async function cargarNivel(drive, itemId) {
    setLoading(true)
    setError(null)
    try {
      const token = await getAccessToken(account)
      const children = await listChildren(token, drive, itemId)
      setItems(children.filter((c) => c.folder))
    } catch (err) {
      setError(String(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    (async () => {
      try {
        const token = await getAccessToken(account)
        const drive = await getMyDriveId(token)
        setDriveId(drive)
        await cargarNivel(drive, RAIZ.id)
      } catch (err) {
        setError(String(err))
        setLoading(false)
      }
    })()
  }, [account])

  function abrirCarpeta(folder) {
    setPath([...path, { id: folder.id, nombre: folder.name }])
    cargarNivel(driveId, folder.id)
  }

  function irABreadcrumb(index) {
    setPath(path.slice(0, index + 1))
    cargarNivel(driveId, path[index].id)
  }

  function elegirEstaCarpeta() {
    onPick({ driveId, itemId: nivelActual.id, nombre: nivelActual.nombre })
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-lg h-[80vh] flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200">
          <p className="text-sm font-medium text-gray-700">Elegir carpeta de OneDrive</p>
          <button onClick={onCancel} className="text-gray-500 hover:text-gray-800 text-sm">
            Cerrar
          </button>
        </div>

        <div className="flex items-center gap-1 px-4 py-2 border-b border-gray-100 text-sm text-gray-600 overflow-x-auto whitespace-nowrap">
          {path.map((p, i) => (
            <span key={p.id} className="flex items-center gap-1">
              {i > 0 && <span className="text-gray-300">&gt;</span>}
              <button
                onClick={() => irABreadcrumb(i)}
                disabled={i === path.length - 1}
                className={i === path.length - 1 ? 'font-medium text-gray-900' : 'text-blue-600 hover:underline'}
              >
                {p.nombre}
              </button>
            </span>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto px-2 py-2">
          {loading && <p className="text-sm text-gray-500 px-2 py-4">Cargando...</p>}
          {error && <p className="text-sm text-red-600 px-2 py-4 break-words">{error}</p>}
          {!loading && !error && items.length === 0 && (
            <p className="text-sm text-gray-500 px-2 py-4">No hay subcarpetas aca.</p>
          )}
          {!loading && !error && items.map((folder) => (
            <button
              key={folder.id}
              onClick={() => abrirCarpeta(folder)}
              className="w-full flex items-center gap-2 px-2 py-2 text-left text-sm rounded-lg hover:bg-gray-100"
            >
              <FolderIcon className="w-5 h-5 text-gray-400 shrink-0" />
              <span className="text-gray-900 truncate">{folder.name}</span>
            </button>
          ))}
        </div>

        <div className="px-4 py-3 border-t border-gray-200">
          <button
            onClick={elegirEstaCarpeta}
            disabled={!driveId}
            className="w-full rounded-lg bg-blue-600 text-white font-medium py-2.5 hover:bg-blue-700 disabled:opacity-50"
          >
            Elegir esta carpeta ({nivelActual.nombre})
          </button>
        </div>
      </div>
    </div>
  )
}
