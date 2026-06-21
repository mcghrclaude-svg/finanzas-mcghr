/**
 * modules/Transacciones/index.jsx v3
 *
 * Cambios vs v2:
 *   - "By Date" -> dropdown: By Date | By Amount
 *   - Search con icono lupa integrado
 *   - Panel detalle con campos EDITABLES (respetan tipo de dato)
 *   - Campo categoria: dropdown tipo arbol navegable
 *   - Preview del archivo adjunto (imagen embebida, PDF iframe, o link)
 *   - Undo/Redo en la barra superior junto a Refresh
 *   - Lista izquierda con ancho ajustable por drag
 *   - Sin header propio (el layout ya no tiene header)
 *   - Undo/Redo tooltips en ingles
 *
 * Issue #26: completitud es TEXT 'minimo'|'parcial'|'completo'
 */
import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import client from '@/api/client'
import useAppStore from '@/store/useAppStore'

// ── Completitud (Issue #26) ────────────────────────────────────────────────────
const COMPLETITUD_DOT = {
  minimo:   'bg-red-500',
  parcial:  'bg-yellow-500',
  completo: 'bg-green-500',
}
const COMPLETITUD_BADGE = {
  minimo:   'bg-red-100 text-red-600',
  parcial:  'bg-yellow-100 text-yellow-700',
  completo: 'bg-green-100 text-green-700',
}
const COMPLETITUD_ORDER = { minimo: 0, parcial: 1, completo: 2 }

const ORIGEN_ICON  = { email: '📧', pdf: '📄', mobile: '📱', manual: '✏️' }
const ORIGEN_LABEL = { email: 'Mail', pdf: 'PDF / Extractos', mobile: 'Mobile', manual: 'Manual' }

const LIST_MIN = 220
const LIST_DEFAULT = 280
const LIST_MAX = 480

// ── API ───────────────────────────────────────────────────────────────────────
const api = {
  listar:        (p) => client.get('/inbox/', { params: p }).then(r => r.data),
  confirmar:     (id) => client.post(`/inbox/${id}/confirmar`).then(r => r.data),
  descartar:     (id) => client.post(`/inbox/${id}/descartar`).then(r => r.data),
  editar:        (id, data) => client.patch(`/inbox/${id}`, data).then(r => r.data),
  confirmarLote: (ids) => client.post('/inbox/confirmar-lote', { ids }).then(r => r.data),
  getCategorias: () => client.get('/catalogos/categorias?flat=true').then(r => r.data),
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function fmt(monto, moneda = 'COP') {
  if (monto == null) return '—'
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: moneda, maximumFractionDigits: 0 }).format(monto)
}

function fmtFecha(f) {
  if (!f) return '—'
  return new Date(f).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: '2-digit' })
}

// ── Dropdown de categorias tipo arbol ─────────────────────────────────────────
function CategoriaTreeSelect({ value, onChange, categorias }) {
  const [open, setOpen] = useState(false)
  const ref = useRef()

  useEffect(() => {
    function handler(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const cat = categorias.find(c => c.id === value)

  function renderItems(items, depth = 0) {
    return items.map(c => (
      <div key={c.id}>
        <button
          onClick={() => { onChange(c.id); setOpen(false) }}
          className={`w-full text-left flex items-center gap-1.5 py-1.5 pr-3 text-sm transition-colors hover:bg-gray-50 ${
            value === c.id ? 'text-primary-700 font-medium bg-primary-50' : 'text-gray-700'
          }`}
          style={{ paddingLeft: `${12 + depth * 16}px` }}
        >
          {c.icono && <span className="text-sm">{c.icono}</span>}
          <span>{c.nombre}</span>
          <span className="ml-auto text-xs text-gray-400 font-mono">{c.id}</span>
        </button>
        {c.hijos?.length > 0 && renderItems(c.hijos, depth + 1)}
      </div>
    ))
  }

  // Construir arbol desde lista plana
  const roots = categorias.filter(c => !c.id_padre)
  function buildTree(cats) {
    return cats.map(c => ({
      ...c,
      hijos: buildTree(categorias.filter(x => x.id_padre === c.id))
    }))
  }
  const tree = buildTree(roots)

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full text-left flex items-center justify-between px-3 py-2 text-sm border border-gray-200 rounded-lg hover:border-primary-400 focus:outline-none focus:border-primary-400 bg-white"
      >
        <span className={cat ? 'text-gray-900' : 'text-gray-400'}>
          {cat ? `${cat.icono ?? ''} ${cat.nombre}` : '— Select category —'}
        </span>
        <span className="text-xs text-gray-400">▾</span>
      </button>
      {open && (
        <div className="absolute top-full left-0 right-0 mt-1 z-50 bg-white border border-gray-200 rounded-xl shadow-lg max-h-60 overflow-y-auto">
          <button
            onClick={() => { onChange(null); setOpen(false) }}
            className="w-full text-left px-3 py-2 text-sm text-gray-400 hover:bg-gray-50 border-b border-gray-100"
          >
            — No category —
          </button>
          {renderItems(tree)}
        </div>
      )}
    </div>
  )
}

// ── Preview de archivo adjunto ────────────────────────────────────────────────
function FilePreview({ item }) {
  const ruta = item?.ruta_documento || item?.documento_url
  if (!ruta) return (
    <div className="flex items-center justify-center h-32 text-gray-300 text-sm border border-dashed border-gray-200 rounded-lg">
      No attachment
    </div>
  )

  const ext = ruta.split('.').pop()?.toLowerCase()
  const isImage = ['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext)
  const isPdf   = ext === 'pdf'

  if (isImage) {
    return (
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <img src={ruta} alt="Attachment" className="w-full object-contain max-h-48" />
      </div>
    )
  }

  if (isPdf) {
    return (
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <iframe
          src={ruta}
          title="PDF preview"
          className="w-full h-48"
          onError={() => {}}
        />
        <div className="px-3 py-2 bg-gray-50 border-t border-gray-200">
          <a href={ruta} target="_blank" rel="noopener noreferrer" className="text-xs text-primary-600 hover:underline">
            📄 Open PDF in new window
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="px-3 py-2 border border-gray-200 rounded-lg">
      <a href={ruta} target="_blank" rel="noopener noreferrer" className="text-xs text-primary-600 hover:underline">
        📎 Open attachment in new window
      </a>
    </div>
  )
}

// ── Panel de detalle editable ─────────────────────────────────────────────────
function DetailPanel({ item, categorias, onConfirmar, onDescartar, onEditar }) {
  const { undo, redo, undoStack, redoStack } = useAppStore()
  const [vals, setVals] = useState({})
  const [dirty, setDirty] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!item) return
    setVals({
      descripcion_propuesta: item.descripcion_propuesta ?? '',
      monto_propuesto:       item.monto_propuesto ?? '',
      moneda_propuesta:      item.moneda_propuesta ?? 'COP',
      fecha_propuesta:       item.fecha_propuesta ? item.fecha_propuesta.slice(0, 10) : '',
      categoria_propuesta:   item.categoria_propuesta ?? '',
      contraparte_propuesta: item.contraparte_propuesta ?? '',
    })
    setDirty(false)
  }, [item?.id])

  function set(key, value) {
    setVals(prev => ({ ...prev, [key]: value }))
    setDirty(true)
  }

  async function handleSaveAndConfirm() {
    setSaving(true)
    try {
      if (dirty) await onEditar(item.id, vals)
      await onConfirmar(item.id)
    } finally {
      setSaving(false)
    }
  }

  if (!item) return (
    <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
      Select a transaction to review
    </div>
  )

  return (
    <div className="flex-1 flex flex-col overflow-hidden">

      {/* Barra superior del panel: titulo + undo/redo + refresh */}
      <div className="flex items-center justify-between px-5 py-2.5 border-b border-gray-100 bg-white flex-shrink-0">
        <div className="flex items-center gap-2">
          <span>{ORIGEN_ICON[item.origen] ?? '📋'}</span>
          <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">
            {ORIGEN_LABEL[item.origen] ?? item.origen}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={undo}
            disabled={!undoStack.length}
            title="Undo (Ctrl+Z)"
            className="p-1.5 rounded hover:bg-gray-100 disabled:opacity-25 text-gray-400 text-sm"
          >↩</button>
          <button
            onClick={redo}
            disabled={!redoStack.length}
            title="Redo (Ctrl+Y)"
            className="p-1.5 rounded hover:bg-gray-100 disabled:opacity-25 text-gray-400 text-sm"
          >↪</button>
          <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium ml-2 ${COMPLETITUD_BADGE[item.completitud] ?? ''}">
            {item.completitud}
          </span>
        </div>
      </div>

      {/* Contenido scrollable */}
      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">

        {/* Warning minimal */}
        {item.completitud === 'minimo' && (
          <div className="bg-red-50 border border-red-100 text-red-600 text-xs rounded-lg px-3 py-2">
            Minimal data — please review all fields before confirming.
          </div>
        )}

        {/* Campos editables */}
        <div className="grid grid-cols-2 gap-x-4 gap-y-3">

          {/* Description */}
          <div className="col-span-2">
            <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Description</label>
            <input
              type="text"
              value={vals.descripcion_propuesta ?? ''}
              onChange={e => set('descripcion_propuesta', e.target.value)}
              placeholder="Transaction description"
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-primary-400"
            />
          </div>

          {/* Amount */}
          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Amount</label>
            <input
              type="number"
              step="0.01"
              value={vals.monto_propuesto ?? ''}
              onChange={e => set('monto_propuesto', parseFloat(e.target.value) || null)}
              placeholder="0.00"
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-primary-400"
            />
          </div>

          {/* Currency */}
          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Currency</label>
            <select
              value={vals.moneda_propuesta ?? 'COP'}
              onChange={e => set('moneda_propuesta', e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-primary-400 bg-white"
            >
              {['COP', 'USD', 'ARS', 'EUR'].map(m => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>

          {/* Date */}
          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Date</label>
            <input
              type="date"
              value={vals.fecha_propuesta ?? ''}
              onChange={e => set('fecha_propuesta', e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-primary-400"
            />
          </div>

          {/* Counterpart */}
          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Counterpart</label>
            <input
              type="text"
              value={vals.contraparte_propuesta ?? ''}
              onChange={e => set('contraparte_propuesta', e.target.value)}
              placeholder="Store, bank, person..."
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-primary-400"
            />
          </div>

          {/* Category -- dropdown tipo arbol */}
          <div className="col-span-2">
            <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Category</label>
            <CategoriaTreeSelect
              value={vals.categoria_propuesta}
              onChange={v => set('categoria_propuesta', v)}
              categorias={categorias}
            />
          </div>

          {/* Confidence (readonly) */}
          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Confidence</label>
            <div className="px-3 py-2 text-sm text-gray-500 bg-gray-50 border border-gray-200 rounded-lg">
              {item.confianza_clasificacion != null
                ? `${Math.round(item.confianza_clasificacion * 100)}%`
                : '—'}
            </div>
          </div>

          {/* Source (readonly) */}
          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Source</label>
            <div className="px-3 py-2 text-sm text-gray-500 bg-gray-50 border border-gray-200 rounded-lg">
              {ORIGEN_LABEL[item.origen] ?? item.origen ?? '—'}
            </div>
          </div>
        </div>

        {/* Preview archivo */}
        <div>
          <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Attachment</label>
          <FilePreview item={item} />
        </div>
      </div>

      {/* Acciones */}
      <div className="flex gap-2 px-5 py-3 border-t border-gray-100 bg-white flex-shrink-0">
        <button
          onClick={handleSaveAndConfirm}
          disabled={saving}
          className="flex-1 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
        >
          {saving ? 'Saving...' : dirty ? 'Save & Confirm' : 'Confirm'}
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

// ── Fila de lista ─────────────────────────────────────────────────────────────
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
          <span className={`w-1.5 h-1.5 rounded-full ${COMPLETITUD_DOT[item.completitud] ?? 'bg-gray-300'}`} />
          <span className="text-xs text-gray-400">{item.completitud ?? '—'}</span>
        </div>
      </div>
    </button>
  )
}

// ── Toolbar ───────────────────────────────────────────────────────────────────
function Toolbar({ filtros, onFiltro, busqueda, onBusqueda, modo, onModo, onRefresh }) {
  const { undo, redo, undoStack, redoStack } = useAppStore()
  const [origenOpen, setOrigenOpen] = useState(false)
  const [sortOpen,   setSortOpen]   = useState(false)
  const origenRef = useRef()
  const sortRef   = useRef()

  useEffect(() => {
    function handler(e) {
      if (origenRef.current && !origenRef.current.contains(e.target)) setOrigenOpen(false)
      if (sortRef.current && !sortRef.current.contains(e.target)) setSortOpen(false)
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

  const sortOpts = [
    { value: 'fecha',  label: 'By Date' },
    { value: 'monto',  label: 'By Amount' },
  ]

  return (
    <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-200 bg-white flex-shrink-0 flex-wrap">

      {/* Fechas */}
      <input
        type="date"
        value={filtros.desde}
        onChange={e => onFiltro({ ...filtros, desde: e.target.value })}
        className="text-xs border border-gray-200 rounded px-2 py-1.5 text-gray-600 focus:outline-none focus:border-primary-400"
        title="From"
      />
      <span className="text-xs text-gray-400">—</span>
      <input
        type="date"
        value={filtros.hasta}
        onChange={e => onFiltro({ ...filtros, hasta: e.target.value })}
        className="text-xs border border-gray-200 rounded px-2 py-1.5 text-gray-600 focus:outline-none focus:border-primary-400"
        title="To"
      />

      <div className="w-px h-5 bg-gray-200" />

      {/* Origen */}
      <div className="relative" ref={origenRef}>
        <button
          onClick={() => setOrigenOpen(o => !o)}
          className="flex items-center gap-1.5 text-xs border border-gray-200 rounded px-2.5 py-1.5 text-gray-600 hover:bg-gray-50"
        >
          <span className="text-gray-400">≡</span>
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

      {/* Sort: dropdown By Date / By Amount + asc/desc */}
      <div className="flex items-center gap-1" ref={sortRef}>
        <button
          onClick={() => onFiltro({ ...filtros, sortDir: filtros.sortDir === 'asc' ? 'desc' : 'asc' })}
          className="text-xs border border-gray-200 rounded-l px-2 py-1.5 text-gray-600 hover:bg-gray-50 border-r-0"
          title={filtros.sortDir === 'asc' ? 'Ascending' : 'Descending'}
        >
          {filtros.sortDir === 'asc' ? '↑' : '↓'}
        </button>
        <div className="relative">
          <button
            onClick={() => setSortOpen(o => !o)}
            className="text-xs border border-gray-200 rounded-r px-2.5 py-1.5 text-gray-600 hover:bg-gray-50 flex items-center gap-1"
          >
            <span>{sortOpts.find(s => s.value === filtros.sortBy)?.label ?? 'By Date'}</span>
            <span className="text-gray-400">▾</span>
          </button>
          {sortOpen && (
            <div className="absolute top-full left-0 mt-1 z-50 bg-white border border-gray-200 rounded-lg shadow-lg py-1 min-w-32">
              {sortOpts.map(s => (
                <button
                  key={s.value}
                  onClick={() => { onFiltro({ ...filtros, sortBy: s.value }); setSortOpen(false) }}
                  className={`w-full flex items-center gap-2 px-3 py-2 text-sm text-left hover:bg-gray-50 ${
                    filtros.sortBy === s.value ? 'text-primary-700 font-medium' : 'text-gray-700'
                  }`}
                >
                  {filtros.sortBy === s.value && <span className="text-primary-600 text-xs">✓</span>}
                  {s.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="w-px h-5 bg-gray-200" />

      {/* Search con lupa */}
      <div className="relative flex-1 min-w-40">
        <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 text-xs pointer-events-none">🔍</span>
        <input
          type="text"
          placeholder="Search transactions..."
          value={busqueda}
          onChange={e => onBusqueda(e.target.value)}
          className="w-full pl-7 pr-3 py-1.5 text-xs border border-gray-200 rounded focus:outline-none focus:border-primary-400"
        />
      </div>

      <div className="w-px h-5 bg-gray-200" />

      {/* Toggle All / Pending */}
      <div className="flex rounded border border-gray-200 overflow-hidden">
        {['all', 'pending'].map(m => (
          <button
            key={m}
            onClick={() => onModo(m)}
            className={`text-xs px-3 py-1.5 transition-colors ${
              modo === m ? 'bg-primary-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'
            }`}
          >
            {m === 'all' ? 'All' : 'Pending'}
          </button>
        ))}
      </div>

      <div className="w-px h-5 bg-gray-200" />

      {/* Undo / Redo / Refresh */}
      <div className="flex items-center gap-1">
        <button
          onClick={undo}
          disabled={!undoStack.length}
          title="Undo (Ctrl+Z)"
          className="p-1.5 rounded hover:bg-gray-100 disabled:opacity-25 text-gray-400 text-sm"
        >↩</button>
        <button
          onClick={redo}
          disabled={!redoStack.length}
          title="Redo (Ctrl+Y)"
          className="p-1.5 rounded hover:bg-gray-100 disabled:opacity-25 text-gray-400 text-sm"
        >↪</button>
        <button
          onClick={onRefresh}
          title="Refresh"
          className="p-1.5 rounded hover:bg-gray-100 text-gray-400 text-sm"
        >↻</button>
      </div>
    </div>
  )
}

// ── Componente principal ──────────────────────────────────────────────────────
export default function Transacciones() {
  const [items,      setItems]      = useState([])
  const [categorias, setCategorias] = useState([])
  const [loading,    setLoading]    = useState(false)
  const [selected,   setSelected]   = useState(null)
  const [busqueda,   setBusqueda]   = useState('')
  const [modo,       setModo]       = useState('pending')
  const [filtros,    setFiltros]    = useState({
    desde:   '',
    hasta:   '',
    origen:  'all',
    sortDir: 'desc',
    sortBy:  'fecha',
  })

  // Ancho ajustable de la lista
  const [listWidth, setListWidth] = useState(LIST_DEFAULT)
  const dragging = useRef(false)
  const startX   = useRef(0)
  const startW   = useRef(0)

  const onMouseDown = useCallback((e) => {
    dragging.current = true
    startX.current = e.clientX
    startW.current = listWidth
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }, [listWidth])

  useEffect(() => {
    function onMove(e) {
      if (!dragging.current) return
      const delta = e.clientX - startX.current
      const newW = Math.max(LIST_MIN, Math.min(LIST_MAX, startW.current + delta))
      setListWidth(newW)
    }
    function onUp() {
      dragging.current = false
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
    return () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp) }
  }, [])

  const cargar = useCallback(async () => {
    setLoading(true)
    try {
      const [dataRes, catsRes] = await Promise.all([
        api.listar({
          estado: modo === 'pending' ? 'pendiente' : undefined,
          origen: filtros.origen !== 'all' ? filtros.origen : undefined,
          limit: 200,
        }),
        api.getCategorias().catch(() => []),
      ])

      let result = dataRes.items ?? []

      // Ordenar
      result = result.sort((a, b) => {
        const field = filtros.sortBy === 'monto' ? 'monto_propuesto' : 'fecha_propuesta'
        const va = a[field] ?? (filtros.sortBy === 'monto' ? 0 : '')
        const vb = b[field] ?? (filtros.sortBy === 'monto' ? 0 : '')
        if (filtros.sortBy === 'monto') {
          return filtros.sortDir === 'asc' ? va - vb : vb - va
        }
        return filtros.sortDir === 'asc' ? String(va).localeCompare(String(vb)) : String(vb).localeCompare(String(va))
      })

      setItems(result)
      setCategorias(catsRes)
      if (result.length > 0 && !selected) setSelected(result[0])
    } catch (e) {
      toast.error('Error: ' + (e.response?.data?.detail ?? e.message))
    } finally {
      setLoading(false)
    }
  }, [modo, filtros])

  useEffect(() => { cargar() }, [cargar])

  const itemsFiltrados = items.filter(item => {
    if (busqueda) {
      const q = busqueda.toLowerCase()
      if (!Object.values(item).some(v => String(v ?? '').toLowerCase().includes(q))) return false
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

  async function handleEditar(id, data) {
    await api.editar(id, data)
  }

  const pendientes = items.filter(i => i.completitud !== 'completo').length

  return (
    <div className="flex flex-col h-screen">

      {/* Barra de titulo */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-white flex-shrink-0">
        <div>
          <h1 className="text-base font-semibold text-gray-900">📋 Transactions</h1>
          <p className="text-xs text-gray-500">
            {items.length} total · <span className="text-yellow-600">{pendientes} need review</span>
          </p>
        </div>
      </div>

      {/* Toolbar */}
      <Toolbar
        filtros={filtros}
        onFiltro={setFiltros}
        busqueda={busqueda}
        onBusqueda={setBusqueda}
        modo={modo}
        onModo={setModo}
        onRefresh={cargar}
      />

      {/* Cuerpo: lista + handle + detalle */}
      <div className="flex flex-1 overflow-hidden">

        {/* Lista con ancho ajustable */}
        <div
          className="flex-shrink-0 border-r border-gray-200 overflow-y-auto bg-white"
          style={{ width: listWidth }}
        >
          {loading ? (
            <div className="flex items-center justify-center py-10 text-gray-400 text-xs">Loading...</div>
          ) : itemsFiltrados.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-gray-400">
              <div className="text-3xl mb-2">✅</div>
              <p className="text-sm font-medium text-gray-600">All clear</p>
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

        {/* Handle resize de la lista */}
        <div
          onMouseDown={onMouseDown}
          className="w-1 flex-shrink-0 cursor-col-resize hover:bg-primary-200 transition-colors"
          title="Drag to resize"
        />

        {/* Panel detalle */}
        <DetailPanel
          item={selected}
          categorias={categorias}
          onConfirmar={handleConfirmar}
          onDescartar={handleDescartar}
          onEditar={handleEditar}
        />
      </div>
    </div>
  )
}
