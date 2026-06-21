/**
 * modules/Transacciones/index.jsx
 *
 * Unifica Inbox + Transacciones en una sola pantalla.
 * Layout Outlook: barra superior | lista izquierda | detalle derecha.
 * Consume el endpoint /api/v1/inbox/ (no cambia la URL del backend).
 *
 * Controles (ver wireframe):
 *   - Filtro de fechas: Desde / Hasta
 *   - Busqueda por texto libre
 *   - Toggle All / Pending
 *   - Filtro por origen: Todos / PDF+Extractos / Mail / Mobile / Manual
 *   - Ordenamiento: By Date (campo) + Asc/Desc
 *
 * Issue #26: completitud es TEXT 'minimo'|'parcial'|'completo'
 */
import { useState, useEffect, useCallback, useRef } from 'react'
import toast from 'react-hot-toast'
import client from '@/api/client'

// ── Completitud como string (Issue #26) ───────────────────────────────────────
const COMPLETITUD_ORDER  = { minimo: 0, parcial: 1, completo: 2 }
const COMPLETITUD_BADGE  = {
  minimo:   'bg-red-100 text-red-600',
  parcial:  'bg-yellow-100 text-yellow-700',
  completo: 'bg-green-100 text-green-700',
}
const COMPLETITUD_DOT = {
  minimo:   'bg-red-500',
  parcial:  'bg-yellow-500',
  completo: 'bg-green-500',
}

const ORIGEN_ICON   = { email: '📧', pdf: '📄', mobile: '📱', manual: '✏️' }
const ORIGEN_LABEL  = { email: 'Mail', pdf: 'PDF / Extractos', mobile: 'Mobile', manual: 'Manual' }

// ── API ───────────────────────────────────────────────────────────────────────
const api = {
  listar:        (p) => client.get('/inbox/', { params: p }).then(r => r.data),
  confirmar:     (id) => client.post(`/inbox/${id}/confirmar`).then(r => r.data),
  descartar:     (id) => client.post(`/inbox/${id}/descartar`).then(r => r.data),
  editar:        (id, data) => client.patch(`/inbox/${id}`, data).then(r => r.data),
  confirmarLote: (ids) => client.post('/inbox/confirmar-lote', { ids }).then(r => r.data),
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function fmt(monto, moneda = 'COP') {
  if (monto == null) return '—'
  return new Intl.NumberFormat('es-CO', {
    style: 'currency', currency: moneda, maximumFractionDigits: 0
  }).format(monto)
}

function fmtFecha(f) {
  if (!f) return '—'
  return new Date(f).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: '2-digit' })
}

// ── Barra superior de herramientas ────────────────────────────────────────────
function Toolbar({ filtros, onFiltro, busqueda, onBusqueda, modo, onModo }) {
  const [origenOpen, setOrigenOpen] = useState(false)
  const origenRef = useRef()

  // Cierra el dropdown al click fuera
  useEffect(() => {
    function handler(e) {
      if (origenRef.current && !origenRef.current.contains(e.target)) setOrigenOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const origenes = [
    { value: 'all',    label: 'All sources' },
    { value: 'pdf',    label: 'PDF / Extractos' },
    { value: 'email',  label: 'Mail' },
    { value: 'mobile', label: 'Mobile' },
    { value: 'manual', label: 'Manual' },
  ]

  return (
    <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-200 bg-white flex-shrink-0 flex-wrap">

      {/* Filtro fechas */}
      <div className="flex items-center gap-1">
        <input
          type="date"
          value={filtros.desde}
          onChange={e => onFiltro({ ...filtros, desde: e.target.value })}
          className="text-xs border border-gray-200 rounded px-2 py-1.5 text-gray-600 focus:outline-none focus:border-primary-400"
          title="From date"
        />
        <span className="text-xs text-gray-400">—</span>
        <input
          type="date"
          value={filtros.hasta}
          onChange={e => onFiltro({ ...filtros, hasta: e.target.value })}
          className="text-xs border border-gray-200 rounded px-2 py-1.5 text-gray-600 focus:outline-none focus:border-primary-400"
          title="To date"
        />
      </div>

      <div className="w-px h-5 bg-gray-200" />

      {/* Filtro origen con dropdown */}
      <div className="relative" ref={origenRef}>
        <button
          onClick={() => setOrigenOpen(o => !o)}
          className="flex items-center gap-1.5 text-xs border border-gray-200 rounded px-2.5 py-1.5 text-gray-600 hover:bg-gray-50 focus:outline-none"
        >
          <span>≡</span>
          <span>{origenes.find(o => o.value === filtros.origen)?.label ?? 'All sources'}</span>
          <span className="text-gray-400">▾</span>
        </button>
        {origenOpen && (
          <div className="absolute top-full left-0 mt-1 z-50 bg-white border border-gray-200 rounded-lg shadow-lg py-1 min-w-40">
            {origenes.map(o => (
              <button
                key={o.value}
                onClick={() => { onFiltro({ ...filtros, origen: o.value }); setOrigenOpen(false) }}
                className={`w-full flex items-center gap-2 px-3 py-2 text-sm text-left hover:bg-gray-50 ${
                  filtros.origen === o.value ? 'text-primary-700 font-medium' : 'text-gray-700'
                }`}
              >
                {filtros.origen === o.value && <span className="text-primary-600 text-xs">✓</span>}
                {o.label}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Ordenamiento */}
      <div className="flex items-center gap-1">
        <button
          onClick={() => onFiltro({ ...filtros, sortDir: filtros.sortDir === 'asc' ? 'desc' : 'asc' })}
          className="text-xs border border-gray-200 rounded px-2 py-1.5 text-gray-600 hover:bg-gray-50"
          title={filtros.sortDir === 'asc' ? 'Ascending' : 'Descending'}
        >
          {filtros.sortDir === 'asc' ? '↑' : '↓'}
        </button>
        <span className="text-xs text-gray-500">By Date</span>
      </div>

      <div className="w-px h-5 bg-gray-200" />

      {/* Busqueda */}
      <input
        type="text"
        placeholder="Search transactions..."
        value={busqueda}
        onChange={e => onBusqueda(e.target.value)}
        className="flex-1 min-w-40 text-xs border border-gray-200 rounded px-3 py-1.5 text-gray-700 focus:outline-none focus:border-primary-400"
      />

      <div className="w-px h-5 bg-gray-200" />

      {/* Toggle All / Pending */}
      <div className="flex rounded border border-gray-200 overflow-hidden">
        {['all', 'pending'].map(m => (
          <button
            key={m}
            onClick={() => onModo(m)}
            className={`text-xs px-3 py-1.5 transition-colors ${
              modo === m
                ? 'bg-primary-600 text-white'
                : 'bg-white text-gray-600 hover:bg-gray-50'
            }`}
          >
            {m === 'all' ? 'All' : 'Pending'}
          </button>
        ))}
      </div>
    </div>
  )
}

// ── Fila de la lista ──────────────────────────────────────────────────────────
function TrxRow({ item, selected, onClick }) {
  const isMin = item.completitud === 'minimo'
  return (
    <button
      onClick={() => onClick(item)}
      className={`w-full text-left px-3 py-2.5 border-b border-gray-100 transition-colors ${
        selected
          ? 'bg-primary-50 border-l-2 border-l-primary-500'
          : isMin
            ? 'bg-red-50/40 hover:bg-red-50 border-l-2 border-l-transparent'
            : 'hover:bg-gray-50 border-l-2 border-l-transparent'
      }`}
    >
      <div className="flex items-start justify-between gap-2 mb-0.5">
        <div className="flex items-center gap-1.5 min-w-0">
          <span className="text-sm flex-shrink-0">{ORIGEN_ICON[item.origen] ?? '📋'}</span>
          <span className="text-xs font-medium text-gray-900 truncate">
            {item.descripcion_propuesta || item.contraparte_propuesta || 'No description'}
          </span>
        </div>
        <span className="text-xs font-semibold text-gray-900 flex-shrink-0 whitespace-nowrap">
          {fmt(item.monto_propuesto, item.moneda_propuesta)}
        </span>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-400">{fmtFecha(item.fecha_propuesta)}</span>
        <div className="flex items-center gap-1">
          <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${COMPLETITUD_DOT[item.completitud] ?? 'bg-gray-300'}`} />
          <span className="text-xs text-gray-400">{item.completitud ?? '—'}</span>
        </div>
      </div>
    </button>
  )
}

// ── Panel de detalle ──────────────────────────────────────────────────────────
function DetailPanel({ item, onConfirmar, onDescartar, onRefresh }) {
  if (!item) return (
    <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
      Select a transaction to review
    </div>
  )

  return (
    <div className="flex-1 overflow-y-auto p-5 space-y-5">

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span>{ORIGEN_ICON[item.origen] ?? '📋'}</span>
            <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">
              {ORIGEN_LABEL[item.origen] ?? item.origen}
            </span>
          </div>
          <h2 className="text-base font-semibold text-gray-900">
            {item.descripcion_propuesta || item.contraparte_propuesta || 'Transaction detail'}
          </h2>
        </div>
        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${COMPLETITUD_BADGE[item.completitud] ?? ''}`}>
          {item.completitud ?? '—'}
        </span>
      </div>

      {/* Datos */}
      <div className="grid grid-cols-2 gap-x-6 gap-y-4">
        {[
          { label: 'Amount',      value: fmt(item.monto_propuesto, item.moneda_propuesta) },
          { label: 'Date',        value: fmtFecha(item.fecha_propuesta) },
          { label: 'Category',    value: item.categoria_propuesta || '—' },
          { label: 'Counterpart', value: item.contraparte_propuesta || '—' },
          { label: 'Confidence',  value: item.confianza_clasificacion != null ? `${Math.round(item.confianza_clasificacion * 100)}%` : '—' },
          { label: 'Source',      value: ORIGEN_LABEL[item.origen] ?? item.origen ?? '—' },
        ].map(f => (
          <div key={f.label}>
            <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-0.5">{f.label}</div>
            <div className="text-sm text-gray-900">{f.value}</div>
          </div>
        ))}
      </div>

      {/* Warning */}
      {item.completitud === 'minimo' && (
        <div className="bg-red-50 border border-red-100 text-red-600 text-xs rounded-lg px-3 py-2">
          Minimal data — please review all fields before confirming.
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
export default function Transacciones() {
  const [items,    setItems]    = useState([])
  const [loading,  setLoading]  = useState(false)
  const [selected, setSelected] = useState(null)
  const [busqueda, setBusqueda] = useState('')
  const [modo,     setModo]     = useState('pending') // all | pending
  const [filtros,  setFiltros]  = useState({
    desde:   '',
    hasta:   '',
    origen:  'all',
    sortDir: 'desc',
  })

  const cargar = useCallback(async () => {
    setLoading(true)
    try {
      const params = {
        estado: modo === 'pending' ? 'pendiente' : undefined,
        origen: filtros.origen !== 'all' ? filtros.origen : undefined,
        limit:  200,
      }
      const data = await api.listar(params)
      let result = data.items ?? []

      // Ordenar por fecha
      result = result.sort((a, b) => {
        const da = a.fecha_propuesta ?? ''
        const db = b.fecha_propuesta ?? ''
        return filtros.sortDir === 'asc' ? da.localeCompare(db) : db.localeCompare(da)
      })

      setItems(result)
      if (result.length > 0 && !selected) setSelected(result[0])
    } catch (e) {
      toast.error('Error: ' + (e.response?.data?.detail ?? e.message))
    } finally {
      setLoading(false)
    }
  }, [modo, filtros])

  useEffect(() => { cargar() }, [cargar])

  // Filtrado por busqueda y fechas (client-side)
  const itemsFiltrados = items.filter(item => {
    if (busqueda) {
      const q = busqueda.toLowerCase()
      const match = Object.values(item).some(v => String(v ?? '').toLowerCase().includes(q))
      if (!match) return false
    }
    if (filtros.desde && item.fecha_propuesta && item.fecha_propuesta < filtros.desde) return false
    if (filtros.hasta && item.fecha_propuesta && item.fecha_propuesta > filtros.hasta) return false
    return true
  })

  async function handleConfirmar(id) {
    try {
      await api.confirmar(id)
      toast.success('Confirmed')
      const next = items.find(i => i.id !== id)
      setSelected(next ?? null)
      cargar()
    } catch (e) {
      toast.error(e.response?.data?.detail ?? e.message)
    }
  }

  async function handleDescartar(id) {
    try {
      await api.descartar(id)
      toast.success('Discarded')
      const next = items.find(i => i.id !== id)
      setSelected(next ?? null)
      cargar()
    } catch (e) {
      toast.error(e.response?.data?.detail ?? e.message)
    }
  }

  const pendientes = items.filter(i => i.completitud !== 'completo').length

  return (
    <div className="flex flex-col h-full -m-6">

      {/* Barra superior */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-white flex-shrink-0">
        <div>
          <h1 className="text-base font-semibold text-gray-900">📋 Transactions</h1>
          <p className="text-xs text-gray-500">
            {items.length} total · <span className="text-yellow-600">{pendientes} need review</span>
          </p>
        </div>
        <button onClick={cargar} className="text-xs text-gray-400 hover:text-gray-600 px-2 py-1 rounded hover:bg-gray-100">
          ↻ Refresh
        </button>
      </div>

      {/* Mini barra de herramientas */}
      <Toolbar
        filtros={filtros}
        onFiltro={setFiltros}
        busqueda={busqueda}
        onBusqueda={setBusqueda}
        modo={modo}
        onModo={setModo}
      />

      {/* Cuerpo: lista + detalle */}
      <div className="flex flex-1 overflow-hidden">

        {/* Lista */}
        <div className="w-72 flex-shrink-0 border-r border-gray-200 overflow-y-auto bg-white">
          {loading ? (
            <div className="flex items-center justify-center py-10 text-gray-400 text-xs">Loading...</div>
          ) : itemsFiltrados.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-gray-400">
              <div className="text-3xl mb-2">✅</div>
              <p className="text-sm font-medium text-gray-600">All clear</p>
              <p className="text-xs mt-1">No transactions to review.</p>
            </div>
          ) : (
            itemsFiltrados.map(item => (
              <TrxRow
                key={item.id}
                item={item}
                selected={selected?.id === item.id}
                onClick={setSelected}
              />
            ))
          )}
        </div>

        {/* Panel detalle */}
        <DetailPanel
          item={selected}
          onConfirmar={handleConfirmar}
          onDescartar={handleDescartar}
          onRefresh={cargar}
        />
      </div>
    </div>
  )
}
