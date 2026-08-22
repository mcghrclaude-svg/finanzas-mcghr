import { Link } from 'react-router-dom'
import { Cog6ToothIcon } from '../../components/icons'

// __APP_BUILD_DATE__ llega en ISO 8601 (build-time, ver vite.config.js).
// Se normaliza a America/Bogota aca, no en el build, para que el valor
// crudo quede disponible sin perder informacion si en el futuro hace
// falta otro formato u otra zona horaria.
function formatearFechaBuild(iso) {
  if (!iso) return null
  const fecha = new Date(iso)
  if (Number.isNaN(fecha.getTime())) return null
  const partes = new Intl.DateTimeFormat('es-CO', {
    timeZone: 'America/Bogota',
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).formatToParts(fecha)
  const valor = (tipo) => partes.find((p) => p.type === tipo)?.value ?? ''
  return `${valor('day')}/${valor('month')}/${valor('year')} ${valor('hour')}:${valor('minute')}`
}

export default function Home() {
  const fechaBuild = formatearFechaBuild(__APP_BUILD_DATE__)

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
            Gastos sin Replicar
          </Link>
          <button
            disabled
            className="rounded-xl bg-gray-100 text-gray-400 text-lg font-medium py-5 text-center cursor-not-allowed"
          >
            Resumen del mes
          </button>
        </div>

        <p className="mt-8 text-center text-xs text-gray-400">
          v{__APP_VERSION__}
          {fechaBuild && <><br />{fechaBuild}</>}
        </p>
      </div>
    </div>
  )
}
