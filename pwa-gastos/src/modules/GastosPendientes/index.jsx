import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useMsal, useIsAuthenticated } from '@azure/msal-react'
import { db } from '../../db/db'
import { TrashIcon } from '../../components/icons'
import { syncPendientes } from '../../utils/sync'

export default function GastosPendientes() {
  const { accounts } = useMsal()
  const isAuthenticated = useIsAuthenticated()
  const account = accounts[0]
  const [gastos, setGastos] = useState([])
  const [sincronizando, setSincronizando] = useState(false)
  const [mensaje, setMensaje] = useState(null)

  async function recargar() {
    const todos = await db.gastosPendientes.orderBy('localId').reverse().toArray()
    setGastos(todos)
  }

  useEffect(() => {
    recargar()
  }, [])

  async function eliminar(localId) {
    await db.gastosPendientes.delete(localId)
    recargar()
  }

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
          <h1 className="text-xl font-semibold text-gray-900">Gastos sin Replicar</h1>
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
          <p className="text-sm text-gray-500">No hay gastos sin replicar -- todo esta subido a OneDrive.</p>
        ) : (
          <div className="flex flex-col gap-2">
            {gastos.map((g) => (
              <div key={g.localId} className="bg-white rounded-xl shadow-sm p-3 flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">{g.monto} {g.id_moneda}</p>
                  <p className="text-sm text-gray-500">{g.fecha} - {g.id_categoria} - {g.quien}</p>
                </div>
                <button
                  onClick={() => eliminar(g.localId)}
                  aria-label="Eliminar"
                  className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                >
                  <TrashIcon className="w-5 h-5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
