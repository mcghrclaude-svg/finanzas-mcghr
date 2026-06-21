/**
 * InboxA/index.jsx -- Inbox Version A
 *
 * Enfoque: REVISION UNA POR UNA
 * Inspiracion: YNAB + Copilot
 *
 * Layout: lista de tarjetas a la izquierda, panel de detalle/edicion a la derecha.
 * El usuario hace clic en una tarjeta y ve todos los campos editables antes de confirmar.
 * Las tarjetas se ordenan por prioridad: 'minimo' primero, luego 'parcial', luego 'completo'.
 *
 * Issue #26: completitud es TEXT -- 'minimo' | 'parcial' | 'completo'
 * Nunca se compara contra numeros flotantes.
 */
import { useState, useEffect, useCallback } from 'react'
import toast from 'react-hot-toast'
import client from '@/api/client'

// ── Constantes de completitud (Issue #26) ─────────────────────────────────────
const COMPLETITUD_ORDER = { minimo: 0, parcial: 1, completo: 2 }

const COMPLETITUD_META = {
  minimo:   { label: 'Minimal',  color: 'bg-danger-100 text-danger-500',   dot: 'bg-danger-500',   ring: 'ring-danger-200' },
  parcial:  { label: 'Partial',  color: 'bg-warning-100 text-warning-500', dot: 'bg-warning-500',  ring: 'ring-warning-200' },
  completo: { label: 'Complete', color: 'bg-success-100 text-success-500', dot: 'bg-success-500',  ring: 'ring-success-200' },
}

const ORIGEN_ICON = { email: '📧', pdf: '📄', mobile: '📱', manual: '✏️' }

// ── API ───────────────────────────────────────────────────────────────────────
const inboxApi = {
  listar:         (p) => client.get('/inbox/', { params: p }).then(r => r.data),
  confirmar:      (id) => client.post(`/inbox/${id}/confirmar`).then(r => r.data),
  descartar:      (id) => client.post(`/inbox/${id}/descartar`).then(r => r.data),
  editar:         (id, data) => client.patch(`/inbox/${id}`, data).then(r => r.data),
  confirmarLote:  (ids) => client.post('/inbox/confirmar-lote', { ids }).then(r => r.data),
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function sortByCompletitud(items) {
  return [...items].sort((a, b) =>
    (COMPLETITUD_ORDER[a.completitud] ?? 99) - (COMPLETITUD_ORDER[b.completitud] ?? 99)
  )
}

function formatMonto(monto, moneda = 'COP') {
  if (monto == null) return '—'
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: moneda, maximumFractionDigits: 0 }).format(monto)
}

function formatFecha(fecha) {
  if (!fecha) return '—'
  return new Date(fecha).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}

// ── Componente badge de completitud ───────────────────────────────────────────
function BadgeCompletitud({ value }) {
  const meta = COMPLETITUD_META[value] ?? COMPLETITUD_META.parcial
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${meta.color}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${meta.dot}`} />
      {meta.label}
    </span>
  )
}

// ── Tarjeta de item ───────────────────────────────────────────────────────────
function InboxCard({ item, selected, onClick }) {
  const meta = COMPLETITUD_META[item.completitud] ?? COMPLETITUD_META.parcial
  return (
    <button
      onClick={() => onClick(item)}
      className={`w-full text-left p-4 border rounded-xl transition-all ${
        selected
          ? `ring-2 ${meta.ring} border-transparent bg-white shadow-sm`
          : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
      }`}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-base flex-shrink-0">{ORIGEN_ICON[item.origen] ?? '📋'}</span>
          <span className="text-sm font-medium text-gray-900 truncate">
            {item.descripcion || item.contraparte_propuesta || 'Sin descripcion'}
          </span>
        </div>
        <BadgeCompletitud value={item.completitud} />
      </div>
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-400">{formatFecha(item.fecha_propuesta)}</span>
        <span className="text-sm font-semibold text-gray-900">
          {formatMonto(item.monto_propuesto, item.moneda_propuesta)}
        </span>
      </div>
      {item.completitud === 'minimo' && (
        <div className="mt-2 text-xs text-danger-500">Requires manual review</div>
      )}
    </button>
  )
}

// ── Panel de detalle/edicion ──────────────────────────────────────────────────
function DetailPanel({ item, onConfirmar, onDescartar, onEditar }) {
  const [editing, setEditing] = useState(false)
  const [vals, setVals] = useState({})

  useEffect(() => {
    setVals({
      monto:        item.monto_propuesto ?? '',
      descripcion:  item.descripcion_propuesta ?? '',
      categoria:    item.categoria_propuesta ?? '',
      contraparte:  item.contraparte_propuesta ?? '',
    })
    setEditing(false)
  }, [item.id])

  const meta = COMPLETITUD_META[item.completitud] ?? COMPLETITUD_META.parcial

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-5">

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-lg">{ORIGEN_ICON[item.origen] ?? '📋'}</span>
            <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">{item.origen}</span>
          </div>
          <h2 className="text-base font-semibold text-gray-900">
            {item.descripcion || item.contraparte_propuesta || 'Transaction detail'}
          </h2>
        </div>
        <BadgeCompletitud value={item.completitud} />
      </div>

      {/* Datos propuestos */}
      <div className="grid grid-cols-2 gap-4">
        {[
          { label: 'Amount',       value: formatMonto(item.monto_propuesto, item.moneda_propuesta) },
          { label: 'Date',         value: formatFecha(item.fecha_propuesta) },
          { label: 'Category',     value: item.categoria_propuesta || '—' },
          { label: 'Counterpart',  value: item.contraparte_propuesta || '—' },
          { label: 'Confidence',   value: item.confianza_clasificacion != null ? `${Math.round(item.confianza_clasificacion * 100)}%` : '—' },
          { label: 'Source',       value: item.origen || '—' },
        ].map(f => (
          <div key={f.label}>
            <div className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-0.5">{f.label}</div>
            <div className="text-sm text-gray-900">{f.value}</div>
          </div>
        ))}
      </div>

      {/* Warning si completitud es minimo */}
      {item.completitud === 'minimo' && (
        <div className="bg-danger-100 text-danger-500 text-xs rounded-lg px-3 py-2">
          This transaction has minimal data. Please review all fields before confirming.
        </div>
      )}

      {/* Acciones */}
      <div className="flex gap-2 pt-2 border-t border-gray-100">
        <button
          onClick={() => onConfirmar(item.id)}
          className="flex-1 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
        >
          Confirm
        </button>
        <button
          onClick={() => onDescartar(item.id)}
          className="px-4 py-2 text-sm font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
        >
          Discard
        </button>
      </div>
    </div>
  )
}

// ── Componente principal ──────────────────────────────────────────────────────
export default function InboxA() {
  const [items,    setItems]    = useState([])
  const [loading,  setLoading]  = useState(false)
  const [selected, setSelected] = useState(null)
  const [filter,   setFilter]   = useState('all') // all | minimo | parcial | completo

  const cargar = useCallback(async () => {
    setLoading(true)
    try {
      const data = await inboxApi.listar({ estado: 'pendiente', limit: 100 })
      const sorted = sortByCompletitud(data.items ?? [])
      setItems(sorted)
      if (sorted.length > 0 && !selected) setSelected(sorted[0])
    } catch (e) {
      toast.error('Error loading inbox: ' + (e.response?.data?.detail ?? e.message))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { cargar() }, [cargar])

  async function handleConfirmar(id) {
    try {
      await inboxApi.confirmar(id)
      toast.success('Transaction confirmed')
      const next = items.find(i => i.id !== id)
      setSelected(next ?? null)
      cargar()
    } catch (e) {
      toast.error(e.response?.data?.detail ?? e.message)
    }
  }

  async function handleDescartar(id) {
    try {
      await inboxApi.descartar(id)
      toast.success('Discarded')
      const next = items.find(i => i.id !== id)
      setSelected(next ?? null)
      cargar()
    } catch (e) {
      toast.error(e.response?.data?.detail ?? e.message)
    }
  }

  // Filtrado por completitud
  const itemsFiltrados = filter === 'all'
    ? items
    : items.filter(i => i.completitud === filter)

  const counts = {
    all:      items.length,
    minimo:   items.filter(i => i.completitud === 'minimo').length,
    parcial:  items.filter(i => i.completitud === 'parcial').length,
    completo: items.filter(i => i.completitud === 'completo').length,
  }

  return (
    <div className="space-y-4">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">📥 Inbox</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {counts.all} pending · {counts.minimo} need review
          </p>
        </div>
        <button onClick={cargar} className="px-3 py-1.5 text-sm text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50">
          ↻ Refresh
        </button>
      </div>

      {/* Filtros por completitud */}
      <div className="flex gap-2">
        {[
          { key: 'all',     label: `All (${counts.all})` },
          { key: 'minimo',  label: `Minimal (${counts.minimo})`,  color: 'text-danger-500' },
          { key: 'parcial', label: `Partial (${counts.parcial})`,  color: 'text-warning-500' },
          { key: 'completo',label: `Complete (${counts.completo})`,color: 'text-success-500' },
        ].map(f => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
              filter === f.key
                ? 'bg-primary-50 border-primary-200 text-primary-700 font-medium'
                : `border-gray-200 ${f.color ?? 'text-gray-600'} hover:bg-gray-50`
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Layout principal: lista + detalle */}
      {loading ? (
        <div className="flex items-center justify-center py-20 text-gray-400 text-sm">
          Loading...
        </div>
      ) : items.length === 0 ? (
        <div className="text-center py-20">
          <div className="text-4xl mb-3">✅</div>
          <p className="font-medium text-gray-700">Inbox is clear</p>
          <p className="text-sm text-gray-400 mt-1">No pending transactions to review.</p>
        </div>
      ) : (
        <div className="grid grid-cols-5 gap-4">
          {/* Lista */}
          <div className="col-span-2 space-y-2 max-h-[calc(100vh-280px)] overflow-y-auto pr-1">
            {itemsFiltrados.map(item => (
              <InboxCard
                key={item.id}
                item={item}
                selected={selected?.id === item.id}
                onClick={setSelected}
              />
            ))}
          </div>

          {/* Panel detalle */}
          <div className="col-span-3">
            {selected ? (
              <DetailPanel
                item={selected}
                onConfirmar={handleConfirmar}
                onDescartar={handleDescartar}
              />
            ) : (
              <div className="flex items-center justify-center h-64 text-gray-400 text-sm">
                Select a transaction to review
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
