/**
 * PendientesCard — Inbox por catalogar + SMS por confirmar, en el mismo
 * espacio que ocupaba antes solo el badge de Inbox.
 */
import { useNavigate } from 'react-router-dom'

export default function PendientesCard({ inboxStats }) {
  const navigate = useNavigate()
  const pendientes = inboxStats?.pendientes ?? 0
  const pendientesSms = inboxStats?.pendientes_sms ?? 0

  return (
    <button
      onClick={() => navigate('/transacciones')}
      className="text-left bg-gray-100 border border-gray-200 rounded-xl p-5 hover:shadow-sm transition-shadow"
    >
      <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
        Pendientes de revisión
      </div>
      <div className="flex flex-col gap-1">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">📥 Inbox por catalogar</span>
          <span className="font-bold text-gray-900">{pendientes}</span>
        </div>
        <div className="flex items-center justify-between text-sm pt-1 border-t border-dashed border-gray-300">
          <span className="text-gray-600">💬 SMS por confirmar</span>
          <span className="font-bold text-gray-900">{pendientesSms}</span>
        </div>
      </div>
    </button>
  )
}
