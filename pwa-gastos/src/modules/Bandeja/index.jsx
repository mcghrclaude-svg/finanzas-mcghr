import { Link } from 'react-router-dom'

// STUB -- placeholder sin funcionalidad real todavia (Bloque 4, PASO B).
export default function Bandeja() {
  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="mx-auto max-w-md">
        <div className="flex items-center gap-3 mb-6">
          <Link to="/" className="text-blue-600 text-sm font-medium">{'<- Volver'}</Link>
          <h1 className="text-xl font-semibold text-gray-900">Bandeja</h1>
        </div>
        <p className="text-sm text-gray-500 text-center mt-12">Proximamente</p>
      </div>
    </div>
  )
}
