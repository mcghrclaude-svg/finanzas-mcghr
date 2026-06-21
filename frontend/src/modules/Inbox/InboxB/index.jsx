/**
 * InboxB/index.jsx -- Inbox Version B
 *
 * Enfoque: TRIAJE EN MASA (bulk triage)
 * Inspiracion: Gmail + Linear
 *
 * Layout: tabla densa con seleccion multiple, acciones en lote.
 * Cada fila muestra todo lo necesario para confirmar/descartar sin abrir detalle.
 * Los items con completitud 'minimo' tienen fondo ligeramente rosado para destacar.
 * Confirmacion en lote para los 'completo' -- un click, muchos confirmados.
 *
 * Issue #26: completitud es TEXT -- 'minimo' | 'parcial' | 'completo'
 */
import { useState, useEffect, useCallback } from 'react'
import toast from 'react-hot-toast'
import client from '@/api/client'

// ── Constantes de completitud (Issue #26) ─────────────────────────────────────
const COMPLETITUD_ORDER = { minimo: 0, parcial: 1, completo: 2 }

const COMPLETITUD_ROW_BG = {
  minimo:   'bg-red-50/50',
  parcial:  '',
  completo: '',
}

const COMPLETITUD_BADGE = {
  minimo:   'bg-danger-100 text-danger-500',
  parcial:  'bg-warning-100 text-warning-500',
  completo: 'bg-success-100 text-success-500',
}

const ORIGEN_ICON = { email: '📧', pdf: '📄', mobile: '📱', manual: '✏️' }

// ── API ───────────────────────────────────────────────────────────────────────
const inboxApi = {
  listar:        (p) => client.get('/inbox/', { params: p }).then(r => r.data),
  confirmar:     (id) => client.post(`/inbox/${id}/confirmar`).then(r => r.data),
  descartar:     (id) => client.post(`/inbox/${id}/descartar`).then(r => r.data),
  confirmarLote: (ids) => client.post('/inbox/confirmar-lote', { ids }).then(r => r.data),
}

function sortByCompletitud(items) {
  return [...items].sort((a, b) =>
    (COMPLETITUD_ORDER[a.completitud] ?? 99) - (COMPLETITUD_ORDER[b.completitud] ?? 99)
  )
}

function formatMonto(monto, moneda = 'COP') {
  if (monto == null) return '—'
  return new Intl.NumberFormat('es-CO', {
    style: 'currency', currency: moneda, maximumFractionDigits: 0
  }).format(monto)
}

function formatFecha(fecha) {
  if (!fecha) return '—'
  return new Date(fecha).toLocaleDateString('es-CO', { day: '2-digit', month: 'short' })
}

// ── Fila de la tabla ──────────────────────────────────────────────────────────
function InboxRow({ item, checked, onCheck, onConfirmar, onDescartar }) {
  const rowBg = COMPLETITUD_ROW_BG[item.completitud] ?? ''

  return (
    <tr className={`border-b border-gray-100 hover:bg-gray-50/80 transition-colors group ${rowBg}`}>
      {/* Checkbox */}
      <td className="pl-4 py-3 w-8">
        <input
          type="checkbox"
          checked={checked}
          onChange={() => onCheck(item.id)}
          className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
        />
      </td>

      {/* Origen */}
      <td className="px-3 py-3 w-8">
        <span title={item.origen} className="text-base">{ORIGEN_ICON[item.origen] ?? '📋'}</span>
      </td>

      {/* Descripcion */}
      <td className="px-3 py-3">
        <div className="text-sm font-medium text-gray-900 truncate max-w-xs">
          {item.descripcion_propuesta || item.contraparte_propuesta || 'No description'}
        </div>
        {item.categoria_propuesta && (
          <div className="text-xs text-gray-400 mt-0.5">{item.categoria_propuesta}</div>
        )}
      </td>

      {/* Fecha */}
      <td className="px-3 py-3 text-sm text-gray-500 whitespace-nowrap">
        {formatFecha(item.fecha_propuesta)}
      </td>

      {/* Monto */}
      <td className="px-3 py-3 text-sm font-semibold text-gray-900 whitespace-nowrap text-right">
        {formatMonto(item.monto_propuesto, item.moneda_propuesta)}
      </td>

      {/* Completitud */}
      <td className="px-3 py-3">
        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${COMPLETITUD_BADGE[item.completitud] ?? ''}`}>
          {item.completitud ?? '—'}
        </span>
      </td>

      {/* Confianza */}
      <td className="px-3 py-3 text-sm text-gray-500">
        {item.confianza_clasificacion != null
          ? `${Math.round(item.confianza_clasificacion * 100)}%`
          : '—'}
      </td>

      {/* Acciones inline */}
      <td className="px-3 py-3 w-24">
        <div className="flex gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={() => onConfirmar(item.id)}
            className="px-2.5 py-1 text-xs font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700 transition-colors"
            title="Confirm"
          >
            ✓
          </button>
          <button
            onClick={() => onDescartar(item.id)}
            className="px-2.5 py-1 text-xs font-medium text-gray-600 border border-gray-200 rounded-md hover:bg-gray-100 transition-colors"
            title="Discard"
          >
            ✕
          </button>
        </div>
      </td>
    </tr>
  )
}

// ── Componente principal ──────────────────────────────────────────────────────
export default function InboxB() {
  const [items,    setItems]    = useState([])
  const [loading,  setLoading]  = useState(false)
  const [selected, setSelected] = useState(new Set())
  const [filter,   setFilter]   = useState('all')
  const [bulkLoading, setBulkLoading] = useState(false)

  const cargar = useCallback(async () => {
    setLoading(true)
    try {
      const data = await inboxApi.listar({ estado: 'pendiente', limit: 200 })
      setItems(sortByCompletitud(data.items ?? []))
      setSelected(new Set())
    } catch (e) {
      toast.error('Error: ' + (e.response?.data?.detail ?? e.message))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { cargar() }, [cargar])

  // Seleccion multiple
  function toggleOne(id) {
    setSelected(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  function toggleAll() {
    if (selected.size === itemsFiltrados.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(itemsFiltrados.map(i => i.id)))
    }
  }

  // Seleccionar todos los 'completo' con un click
  function selectCompletos() {
    const ids = items.filter(i => i.completitud === 'completo').map(i => i.id)
    setSelected(new Set(ids))
  }

  async function handleConfirmar(id) {
    try {
      await inboxApi.confirmar(id)
      toast.success('Confirmed')
      cargar()
    } catch (e) {
      toast.error(e.response?.data?.detail ?? e.message)
    }
  }

  async function handleDescartar(id) {
    try {
      await inboxApi.descartar(id)
      toast.success('Discarded')
      cargar()
    } catch (e) {
      toast.error(e.response?.data?.detail ?? e.message)
    }
  }

  async function handleBulkConfirmar() {
    if (selected.size === 0) return
    setBulkLoading(true)
    try {
      const result = await inboxApi.confirmarLote([...selected])
      toast.success(`${result.confirmados ?? selected.size} transactions confirmed`)
      cargar()
    } catch (e) {
      toast.error(e.response?.data?.detail ?? e.message)
    } finally {
      setBulkLoading(false)
    }
  }

  // Filtrado
  const itemsFiltrados = filter === 'all'
    ? items
    : items.filter(i => i.completitud === filter)

  const counts = {
    all:      items.length,
    minimo:   items.filter(i => i.completitud === 'minimo').length,
    parcial:  items.filter(i => i.completitud === 'parcial').length,
    completo: items.filter(i => i.completitud === 'completo').length,
  }

  const allChecked = itemsFiltrados.length > 0 && selected.size === itemsFiltrados.length

  return (
    <div className="space-y-4">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">📥 Inbox</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {counts.all} pending &nbsp;·&nbsp;
            <span className="text-danger-500">{counts.minimo} need attention</span>
          </p>
        </div>
        <div className="flex gap-2">
          {counts.completo > 0 && (
            <button
              onClick={selectCompletos}
              className="px-3 py-1.5 text-xs font-medium text-success-500 border border-success-100 bg-success-100 rounded-lg hover:bg-green-100 transition-colors"
            >
              Select all complete ({counts.completo})
            </button>
          )}
          <button onClick={cargar} className="px-3 py-1.5 text-sm text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50">
            ↻
          </button>
        </div>
      </div>

      {/* Barra de acciones en lote */}
      {selected.size > 0 && (
        <div className="flex items-center gap-3 px-4 py-2.5 bg-primary-50 border border-primary-100 rounded-xl">
          <span className="text-sm font-medium text-primary-700">
            {selected.size} selected
          </span>
          <button
            onClick={handleBulkConfirmar}
            disabled={bulkLoading}
            className="px-3 py-1.5 text-xs font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
          >
            {bulkLoading ? 'Confirming...' : `Confirm ${selected.size}`}
          </button>
          <button
            onClick={() => setSelected(new Set())}
            className="text-xs text-gray-500 hover:text-gray-700"
          >
            Clear selection
          </button>
        </div>
      )}

      {/* Filtros */}
      <div className="flex gap-2">
        {[
          { key: 'all',     label: `All (${counts.all})`,              cls: '' },
          { key: 'minimo',  label: `Minimal (${counts.minimo})`,       cls: 'text-danger-500' },
          { key: 'parcial', label: `Partial (${counts.parcial})`,      cls: 'text-warning-500' },
          { key: 'completo',label: `Complete (${counts.completo})`,    cls: 'text-success-500' },
        ].map(f => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
              filter === f.key
                ? 'bg-primary-50 border-primary-200 text-primary-700 font-medium'
                : `border-gray-200 ${f.cls || 'text-gray-600'} hover:bg-gray-50`
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Tabla */}
      {loading ? (
        <div className="flex items-center justify-center py-20 text-gray-400 text-sm">Loading...</div>
      ) : items.length === 0 ? (
        <div className="text-center py-20">
          <div className="text-4xl mb-3">✅</div>
          <p className="font-medium text-gray-700">Inbox is clear</p>
          <p className="text-sm text-gray-400 mt-1">No pending transactions.</p>
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="pl-4 py-2.5 w-8">
                  <input
                    type="checkbox"
                    checked={allChecked}
                    onChange={toggleAll}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                </th>
                <th className="px-3 py-2.5 w-8" />
                <th className="px-3 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Description</th>
                <th className="px-3 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Date</th>
                <th className="px-3 py-2.5 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Amount</th>
                <th className="px-3 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Completeness</th>
                <th className="px-3 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Confidence</th>
                <th className="px-3 py-2.5 w-24" />
              </tr>
            </thead>
            <tbody>
              {itemsFiltrados.map(item => (
                <InboxRow
                  key={item.id}
                  item={item}
                  checked={selected.has(item.id)}
                  onCheck={toggleOne}
                  onConfirmar={handleConfirmar}
                  onDescartar={handleDescartar}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
