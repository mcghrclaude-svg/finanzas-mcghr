import { Link } from 'react-router-dom'

// Placeholder: a futuro va a descargar un JSON pre-calculado desde la
// carpeta de resumen configurada, cachearlo en IndexedDB, y renderizar el
// dashboard mensual a partir de esa copia local. Formato aun no definido.
export default function ResumenMes() {
  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="mx-auto max-w-md">
        <div className="flex items-center gap-3 mb-6">
          <Link to="/" className="text-blue-600 text-sm font-medium">{'<- Volver'}</Link>
          <h1 className="text-xl font-semibold text-gray-900">Resumen del mes</h1>
        </div>
        <p className="text-sm text-gray-500">Proximamente.</p>
      </div>
    </div>
  )
}
