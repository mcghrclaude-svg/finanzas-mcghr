import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useMsal, useIsAuthenticated } from '@azure/msal-react'
import { db } from '../../db/db'
import { useCatalogos } from '../../hooks/useCatalogos'
import { syncPendientes } from '../../utils/sync'
import { ExclamationTriangleIcon } from '../../components/icons'

const DIAS_VENTANA = 7

function formatearFechaCorta(fechaISO) {
  const fecha = new Date(fechaISO)
  if (Number.isNaN(fecha.getTime())) return fechaISO
  const partes = new Intl.DateTimeFormat('es-CO', { day: '2-digit', month: 'short' }).formatToParts(fecha)
  const dia = partes.find((p) => p.type === 'day')?.value ?? ''
  const mes = partes.find((p) => p.type === 'month')?.value ?? ''
  return `${dia}/${mes}`
}

// Fusiona la vieja "Gastos sin Replicar" con una vista de historial: no
// solo pendientes de subir, sino los ultimos 7 dias de actividad completa
// (mas cualquier gasto que siga sin sincronizar aunque sea mas viejo -- ver
// regla de purga en utils/sync.js).
export default function Actividad() {
  const { accounts } = useMsal()
  const isAuthenticated = useIsAuthenticated()
  const account = accounts[0]
  const { catalogos } = useCatalogos()
  const [gastos, setGastos] = useState([])
  const [sincronizando, setSincronizando] = useState(false)
  const [mensaje, setMensaje] = useState(null)

  const nombrePorCategoria = new Map(catalogos.categorias.map((c) => [c.id, c.etiqueta]))

  async function recargar() {
    const todos = await db.gastos.toArray()
    const limite = new Date()
    limite.setDate(limite.getDate() - DIAS_VENTANA)
    const visibles = todos.filter((g) => g.estado !== 'sincronizado' || new Date(g.fecha) >= limite)
    visibles.sort((a, b) => (a.fecha < b.fecha ? 1 : a.fecha > b.fecha ? -1 : 0))
    setGastos(visibles)
  }

  useEffect(() => {
    recargar()
  }, [])

  async function sincronizarAhora() {
    if (!isAuthenticated) {
      setMensaje('Inicia sesion con Microsoft primero')
      return
    }
    setSincronizando(true)
    setMensaje(null)
    try {
      const { subidos, fallidos, motivo } = await syncPendientes(account)
      if (motivo === 'sin-carpeta-configurada') {
        setMensaje('Configura la carpeta de gastos primero')
      } else {
        setMensaje(`Subidos: ${subidos}${fallidos ? `, fallidos: ${fallidos}` : ''}`)
      }
      recargar()
    } catch (err) {
      setMensaje(`Error al sincronizar: ${err}`)
    } finally {
      setSincronizando(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="mx-auto max-w-md">
        <div className="flex items-center gap-3 mb-6">
          <Link to="/" className="text-blue-600 text-sm font-medium">{'<- Volver'}</Link>
          <h1 className="text-xl font-semibold text-gray-900">Actividad</h1>
        </div>

        <button
          onClick={sincronizarAhora}
          disabled={sincronizando}
          className="w-full mb-4 rounded-lg bg-blue-600 text-white font-medium py-2.5 hover:bg-blue-700 disabled:opacity-50"
        >
          {sincronizando ? 'Sincronizando...' : 'Sincronizar ahora'}
        </button>
        {mensaje && <p className="text-sm text-gray-600 mb-4">{mensaje}</p>}

        {gastos.length === 0 ? (
          <p className="text-sm text-gray-500">No hay actividad reciente.</p>
        ) : (
          <div className="flex flex-col gap-2">
            {gastos.map((g) => (
              <Link
                key={g.localId}
                to={`/nuevo-gasto/${g.id}`}
                className="bg-white rounded-xl shadow-sm p-3 flex items-center justify-between gap-2 hover:bg-gray-50"
              >
                <div className="min-w-0">
                  <p className="font-medium text-gray-900 truncate">
                    {formatearFechaCorta(g.fecha)} - {g.monto} {g.id_moneda}
                  </p>
                  <p className="text-sm text-gray-500 truncate">
                    {nombrePorCategoria.get(g.id_categoria) ?? g.id_categoria}
                  </p>
                </div>
                {g.estado === 'error' && (
                  <ExclamationTriangleIcon className="w-5 h-5 text-red-600 shrink-0" />
                )}
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
