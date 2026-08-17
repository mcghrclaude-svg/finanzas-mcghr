import { Link } from 'react-router-dom'
import { Cog6ToothIcon } from '../../components/icons'

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="mx-auto max-w-md">
        <div className="flex items-center justify-between mb-8 pt-2">
          <h1 className="text-2xl font-semibold text-gray-900">Gastos MCGHR</h1>
          <Link to="/configuracion" aria-label="Configuracion" className="p-2 text-gray-600 hover:text-gray-900">
            <Cog6ToothIcon className="w-7 h-7" />
          </Link>
        </div>

        <div className="flex flex-col gap-4">
          <Link
            to="/nuevo-gasto"
            className="rounded-xl bg-blue-600 text-white text-lg font-medium py-5 text-center shadow-sm hover:bg-blue-700"
          >
            Agregar gasto
          </Link>
          <Link
            to="/pendientes"
            className="rounded-xl bg-white text-gray-900 text-lg font-medium py-5 text-center shadow-sm border border-gray-200 hover:bg-gray-50"
          >
            Ver gastos pendientes
          </Link>
          <button
            disabled
            className="rounded-xl bg-gray-100 text-gray-400 text-lg font-medium py-5 text-center cursor-not-allowed"
          >
            Resumen del mes
          </button>
        </div>
      </div>
    </div>
  )
}
