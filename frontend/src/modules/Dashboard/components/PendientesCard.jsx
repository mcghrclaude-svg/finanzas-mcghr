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
      className="text-left bg-gray-100 border border-gray-200 rounded-xl p-2.5 hover:shadow-sm transition-shadow h-full flex flex-col justify-center"
    >
      <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-0.5">
        Pendientes de revisión
      </div>
      <div className="flex flex-col">
        <div className="flex items-center justify-between text-xs py-px">
          <span className="text-gray-600">📥 Inbox</span>
          <span className="font-bold text-gray-900">{pendientes}</span>
        </div>
        <div className="flex items-center justify-between text-xs py-px border-t border-dashed border-gray-300">
          <span className="text-gray-600">💬 SMS</span>
          <span className="font-bold text-gray-900">{pendientesSms}</span>
        </div>
      </div>
    </button>
  )
}
