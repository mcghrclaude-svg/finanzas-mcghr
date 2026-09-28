/**
 * modules/Transacciones/index.jsx v6
 *
 * Cambios vs v5:
 *   - Grid 4 columnas en el panel de detalle
 *   - Fila 1: Description (3 cols) | Amount (1 col)
 *   - Fila 2: Currency | Date | Tipo | Quien Pago
 *   - Fila 3: Counterpart (2 cols) | Paid With | Es Recurrente
 *   - Fila 4: Category (2 cols) | Es Reembolsable | Estado Reembolso
 *   - Fila 5: Source | Confidence | Notas (2 cols)
 *   - Fila 6: Attachment compacto con boton "abrir en nueva ventana"
 *   - ID Correo eliminado del formulario
 *
 * Issue #26: completitud es TEXT 'minimo'|'parcial'|'completo'
 */
import { useState, useEffect, useCallback, useRef, Component } from 'react'
import toast from 'react-hot-toast'
import client from '@/api/client'
import useAppStore from '@/store/useAppStore'
import DetailPanel from './DetailPanel'
import { api, fmt, fmtFecha, INPUT, SELECT, CHECK, AutocompleteSelect, COMPLETITUD_DOT } from './shared'

// -- Error Boundary ----------------------------------------------------
class TransaccionesErrorBoundary extends Component {
  constructor(props) { super(props); this.state = { error: null } }
  static getDerivedStateFromError(error) { return { error } }
  render() {
    if (this.state.error) {
      return (
        <div className="flex flex-col items-center justify-center h-full gap-3 text-gray-500">
          <p className="text-sm font-medium">Error loading Transactions</p>
          <p className="text-xs text-gray-400">{this.state.error.message}</p>
          <button onClick={() => this.setState({ error: null })}
            className="text-xs px-3 py-1.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
            Retry
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

// -- Constantes --------------------------------------------------------
const LIST_MIN     = 220
const LIST_DEFAULT = 280
const LIST_MAX     = 480

const FILTROS_INICIAL = {
  desde:   '',
  hasta:   '',
  origen:  'all',
  persona: 'all',
  sortDir: 'desc',
  sortBy:  'fecha',
}

// -- AddTransactionModal ------------------------------------------------
const EMPTY_TRX_MANUAL = {
  descripcion: '', monto: '', moneda: 'COP', fecha: '', tipo: '', quien_pago: '',
  id_contraparte: null, id_cuenta_origen: null, es_recurrente: false,
  id_categoria: null, es_reembolsable: false, estado_reembolso: '', notas: '',
}
const REQUIRED_TRX_KEYS = ['descripcion', 'monto', 'fecha', 'tipo', 'quien_pago', 'id_cuenta_origen']

function ModalField({ label, children, cols = 1, required = false, error = false }) {
  const spanClass = cols === 4 ? 'col-span-4' : cols === 3 ? 'col-span-3' : cols === 2 ? 'col-span-2' : ''
  return (
    <div className={`min-w-0 ${spanClass}`}>
      <label className={`block text-xs font-semibold uppercase tracking-wider mb-0.5 ${error ? 'text-red-600' : 'text-gray-400'}`}>
        {label}
      </label>
      {children}
      {required && (
        <p className={`mt-0.5 text-[10px] ${error ? 'text-red-500 font-medium' : 'text-gray-300'}`}>Requerido</p>
      )}
    </div>
  )
}

function NewAttachmentsZone({ files, onAdd, onRemove }) {
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef()

  function handleFiles(fileList) {
    const arr = Array.from(fileList)
    if (arr.length) onAdd(arr)
  }

  return (
    <div>
      <div
        onDragOver={e => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={e => { e.preventDefault(); setDragOver(false); handleFiles(e.dataTransfer.files) }}
        className={`relative min-h-[38px] border border-dashed rounded-lg p-1.5 pr-9 transition-colors ${
          dragOver ? 'border-primary-400 bg-primary-50/40' : 'border-gray-200'
        }`}
      >
        {files.length === 0 ? (
          <p className="text-xs text-gray-400 italic px-1 py-1">Drag & drop a file here, or click +</p>
        ) : (
          <div className="space-y-1">
            {files.map((f, i) => (
              <div key={i} className="flex items-center gap-2 px-2 py-1 bg-gray-50 border border-gray-200 rounded-lg">
                <span className="text-xs text-gray-600 truncate flex-1" title={f.name}>{f.name}</span>
                <button type="button" onClick={() => onRemove(i)} tabIndex={-1}
                  className="text-gray-300 hover:text-red-500 text-xs flex-shrink-0">✕</button>
              </div>
            ))}
          </div>
        )}
        <button type="button" onClick={() => inputRef.current?.click()}
          className="absolute top-1.5 right-1.5 w-6 h-6 flex items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-500 hover:bg-gray-50 hover:text-primary-600 text-sm font-semibold flex-shrink-0">
          +
        </button>
      </div>
      <input ref={inputRef} type="file" multiple className="hidden"
        onChange={e => { handleFiles(e.target.files); e.target.value = '' }} />
    </div>
  )
}

function AddTransactionModal({ open, onClose, categorias, contrapartes, cuentas, onCreated }) {
  const [vals,   setVals]   = useState(EMPTY_TRX_MANUAL)
  const [files,  setFiles]  = useState([])
  const [errors, setErrors] = useState(new Set())
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (open) {
      setVals(EMPTY_TRX_MANUAL)
      setFiles([])
      setErrors(new Set())
      setSaving(false)
    }
  }, [open])

  if (!open) return null

  function set(key, value) {
    setVals(prev => ({ ...prev, [key]: value }))
    setErrors(prev => {
      if (!prev.has(key)) return prev
      const next = new Set(prev)
      next.delete(key)
      return next
    })
  }

  function validar() {
    const faltantes = new Set()
    for (const key of REQUIRED_TRX_KEYS) {
      const v = vals[key]
      if (v === '' || v === null || v === undefined) faltantes.add(key)
    }
    setErrors(faltantes)
    return faltantes
  }

  function limpiar() {
    setVals(EMPTY_TRX_MANUAL)
    setFiles([])
    setErrors(new Set())
  }

  async function guardar(cerrarAlTerminar) {
    if (validar().size > 0) {
      toast.error('Complete los campos requeridos')
      return
    }
    setSaving(true)
    try {
      const payload = {
        descripcion: vals.descripcion,
        monto: Number(vals.monto),
        moneda: vals.moneda || 'COP',
        fecha: vals.fecha,
        tipo: vals.tipo,
        quien_pago: vals.quien_pago,
        id_cuenta_origen: vals.id_cuenta_origen,
        id_contraparte: vals.id_contraparte,
        id_categoria: vals.id_categoria,
        es_recurrente: !!vals.es_recurrente,
        es_reembolsable: !!vals.es_reembolsable,
        estado_reembolso: vals.estado_reembolso || null,
        notas: vals.notas || null,
      }
      const { data } = await client.post('/transacciones/', payload)

      for (const file of files) {
        const form = new FormData()
        form.append('file', file)
        form.append('tipo_vinculo', 'factura')
        await client.post(`/transacciones/${data.id}/documentos`, form, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
      }

      toast.success('Transaction created')
      onCreated?.()
      if (cerrarAlTerminar) onClose()
      else limpiar()
    } catch (e) {
      toast.error(e.message)
    } finally {
      setSaving(false)
    }
  }

  const catOpts    = (Array.isArray(categorias)  ? categorias  : []).map(c => ({ id: c.id, label: c.nombre }))
  const cpOpts     = (Array.isArray(contrapartes) ? contrapartes : []).map(c => ({ id: c.id, label: c.nombre }))
  const cuentaOpts = (Array.isArray(cuentas)      ? cuentas     : []).map(c => ({ id: c.id, label: c.nombre }))

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm"
      onClick={e => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl flex flex-col">

        <div className="flex items-center justify-between px-5 pt-4 pb-3 border-b border-gray-100 flex-shrink-0">
          <h2 className="text-base font-semibold text-gray-900">New Transaction</h2>
          <button onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-600 text-sm">✕</button>
        </div>

        <div className="px-5 py-3">
          <div className="grid grid-cols-4 gap-x-2.5 gap-y-2.5">

            <ModalField label="Description" cols={3} required error={errors.has('descripcion')}>
              <input type="text" value={vals.descripcion} onChange={e => set('descripcion', e.target.value)}
                placeholder="Transaction description" className={INPUT} />
            </ModalField>
            <ModalField label="Amount" required error={errors.has('monto')}>
              <input type="number" value={vals.monto} onChange={e => set('monto', e.target.value)}
                placeholder="0" className={INPUT} />
            </ModalField>

            <ModalField label="Currency">
              <input type="text" value={vals.moneda} onChange={e => set('moneda', e.target.value.toUpperCase())}
                maxLength={3} className={INPUT} />
            </ModalField>
            <ModalField label="Date" required error={errors.has('fecha')}>
              <input type="date" value={vals.fecha} onChange={e => set('fecha', e.target.value)} className={INPUT} />
            </ModalField>
            <ModalField label="Tipo" required error={errors.has('tipo')}>
              <select value={vals.tipo} onChange={e => set('tipo', e.target.value)} className={SELECT}>
                <option value="">-- Select --</option>
                <option value="gasto">Gasto</option>
                <option value="ingreso">Ingreso</option>
                <option value="transferencia">Transferencia</option>
                <option value="ajuste">Ajuste</option>
              </select>
            </ModalField>
            <ModalField label="Quien Pago" required error={errors.has('quien_pago')}>
              <select value={vals.quien_pago} onChange={e => set('quien_pago', e.target.value)} className={SELECT}>
                <option value="">-- Select --</option>
                <option value="GHR">GHR (Hernan)</option>
                <option value="MC">MC (Martha)</option>
                <option value="Unknown">Unknown</option>
              </select>
            </ModalField>

            <ModalField label="Counterpart" cols={2}>
              <AutocompleteSelect value={vals.id_contraparte} onChange={v => set('id_contraparte', v)}
                options={cpOpts} placeholder="Search entity..." />
            </ModalField>
            <ModalField label="Paid With" required error={errors.has('id_cuenta_origen')}>
              <AutocompleteSelect value={vals.id_cuenta_origen} onChange={v => set('id_cuenta_origen', v)}
                options={cuentaOpts} placeholder="Select account..." />
            </ModalField>
            <ModalField label="Es Recurrente">
              <div className={CHECK}>
                <input type="checkbox" id="new_chk_recurrente" checked={!!vals.es_recurrente}
                  onChange={e => set('es_recurrente', e.target.checked)}
                  className="w-4 h-4 accent-primary-600 flex-shrink-0" />
                <label htmlFor="new_chk_recurrente" className="text-sm text-gray-700 cursor-pointer">
                  {vals.es_recurrente ? 'Yes' : 'No'}
                </label>
              </div>
            </ModalField>

            <ModalField label="Category" cols={2}>
              <AutocompleteSelect value={vals.id_categoria} onChange={v => set('id_categoria', v)}
                options={catOpts} placeholder="Search category..." />
            </ModalField>
            <ModalField label="Es Reembolsable">
              <div className={CHECK}>
                <input type="checkbox" id="new_chk_reembolsable" checked={!!vals.es_reembolsable}
                  onChange={e => set('es_reembolsable', e.target.checked)}
                  className="w-4 h-4 accent-primary-600 flex-shrink-0" />
                <label htmlFor="new_chk_reembolsable" className="text-sm text-gray-700 cursor-pointer">
                  {vals.es_reembolsable ? 'Yes' : 'No'}
                </label>
              </div>
            </ModalField>
            <ModalField label="Estado Reembolso">
              <select value={vals.estado_reembolso} onChange={e => set('estado_reembolso', e.target.value)} className={SELECT}>
                <option value="">-- N/A --</option>
                <option value="pendiente">Pendiente</option>
                <option value="solicitado">Solicitado</option>
                <option value="recibido">Recibido</option>
              </select>
            </ModalField>

            <ModalField label="Notas" cols={4}>
              <textarea value={vals.notas} onChange={e => set('notas', e.target.value)}
                placeholder="Notes..." rows={1}
                className="w-full px-2.5 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-primary-400 resize-none h-[34px]" />
            </ModalField>

            <ModalField label="Attachments" cols={4}>
              <NewAttachmentsZone
                files={files}
                onAdd={added => setFiles(prev => [...prev, ...added])}
                onRemove={idx => setFiles(prev => prev.filter((_, i) => i !== idx))}
              />
            </ModalField>

          </div>
        </div>

        <div className="flex gap-2 px-5 py-3.5 border-t border-gray-100 flex-shrink-0">
          <button onClick={onClose} disabled={saving}
            className="px-4 py-2 text-sm font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors">
            Cancel
          </button>
          <button onClick={limpiar} disabled={saving}
            className="px-4 py-2 text-sm font-medium text-red-600 border border-red-200 rounded-lg hover:bg-red-50 disabled:opacity-50 transition-colors">
            Clear
          </button>
          <div className="flex-1" />
          <button onClick={() => guardar(false)} disabled={saving}
            className="px-4 py-2 text-sm font-medium text-primary-600 border border-primary-600 rounded-lg hover:bg-primary-50 disabled:opacity-50 transition-colors">
            Save & New
          </button>
          <button onClick={() => guardar(true)} disabled={saving}
            className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors">
            {saving ? 'Saving...' : 'Save & Close'}
          </button>
        </div>
      </div>
    </div>
  )
}

// -- TrxRow ------------------------------------------------------------
function TrxRow({ item, selected, onClick }) {
  const isMin = item.completitud === 'minimo'
  return (
    <button onClick={() => onClick(item)}
      className={`w-full text-left px-3 py-2.5 border-b border-gray-100 transition-colors ${
        selected
          ? 'bg-primary-50 border-l-2 border-l-primary-500'
          : isMin
            ? 'bg-red-50/40 hover:bg-red-50 border-l-2 border-l-transparent'
            : 'hover:bg-gray-50 border-l-2 border-l-transparent'
      }`}
    >
      <div className="flex items-start justify-between gap-2 mb-0.5">
        <span className="text-xs font-medium text-gray-900 truncate"
          title={item.descripcion || item.nombre_contraparte}>
          {item.descripcion || item.nombre_contraparte || 'No description'}
        </span>
        <span className="text-xs font-semibold text-gray-900 flex-shrink-0 whitespace-nowrap">
          {fmt(item.monto, item.moneda)}
        </span>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-400">{fmtFecha(item.fecha)}</span>
        <div className="flex items-center gap-1">
          <span className={`w-1.5 h-1.5 rounded-full ${COMPLETITUD_DOT[item.completitud] ?? 'bg-gray-300'}`} />
          <span className="text-xs text-gray-400">{item.completitud ?? '-'}</span>
        </div>
      </div>
    </button>
  )
}

// -- DropdownFilter ----------------------------------------------------
function DropdownFilter({ value, options, onChange }) {
  const [open, setOpen] = useState(false)
  const ref = useRef()

  useEffect(() => {
    function handler(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const current = options.find(o => o.value === value)

  return (
    <div className="relative" ref={ref}>
      <button onClick={() => setOpen(o => !o)}
        className="flex items-center gap-1.5 text-xs border border-gray-200 rounded px-2.5 py-1.5 text-gray-600 hover:bg-gray-50">
        <span>{current?.label ?? options[0]?.label}</span>
        <span className="text-gray-400">▾</span>
      </button>
      {open && (
        <div className="absolute top-full left-0 mt-1 z-50 bg-white border border-gray-200 rounded-lg shadow-lg py-1 min-w-40">
          {options.map(o => (
            <button key={o.value} onClick={() => { onChange(o.value); setOpen(false) }}
              className={`w-full flex items-center gap-2 px-3 py-2 text-sm text-left hover:bg-gray-50 ${
                value === o.value ? 'text-primary-700 font-medium' : 'text-gray-700'
              }`}>
              {value === o.value && <span className="text-primary-600 text-xs">✓</span>}
              {o.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

// -- Toolbar -----------------------------------------------------------
function Toolbar({ filtros, onFiltro, busqueda, onBusqueda, modo, onModo, onRefresh, onClearFilters }) {
  const { undo, redo, undoStack, redoStack } = useAppStore()

  const origenes = [
    { value: 'all',    label: 'All Sources' },
    { value: 'pdf',    label: 'PDF / Extractos' },
    { value: 'email',  label: 'Mail' },
    { value: 'mobile', label: 'Mobile' },
    { value: 'manual', label: 'Manual' },
  ]
  const personas = [
    { value: 'all',     label: 'All People' },
    { value: 'MC',      label: 'MC (Martha)' },
    { value: 'GHR',     label: 'GHR (Hernan)' },
    { value: 'Unknown', label: 'Unknown' },
  ]
  const sortOpts = [
    { value: 'fecha', label: 'By Date' },
    { value: 'monto', label: 'By Amount' },
  ]

  const hayFiltrosActivos =
    filtros.desde || filtros.hasta ||
    filtros.origen !== 'all' || filtros.persona !== 'all' ||
    filtros.sortDir !== 'desc' || filtros.sortBy !== 'fecha' ||
    busqueda

  return (
    <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-200 bg-white flex-shrink-0 flex-wrap">

      <input type="date" value={filtros.desde}
        onChange={e => onFiltro({ ...filtros, desde: e.target.value })}
        className="text-xs border border-gray-200 rounded px-2 py-1.5 text-gray-600 focus:outline-none focus:border-primary-400"
        title="From" />
      <span className="text-xs text-gray-400">–</span>
      <input type="date" value={filtros.hasta}
        onChange={e => onFiltro({ ...filtros, hasta: e.target.value })}
        className="text-xs border border-gray-200 rounded px-2 py-1.5 text-gray-600 focus:outline-none focus:border-primary-400"
        title="To" />

      <div className="w-px h-5 bg-gray-200" />

      <DropdownFilter value={filtros.origen}  options={origenes} onChange={v => onFiltro({ ...filtros, origen: v })} />
      <DropdownFilter value={filtros.persona} options={personas} onChange={v => onFiltro({ ...filtros, persona: v })} />

      <div className="flex items-center">
        <button
          onClick={() => onFiltro({ ...filtros, sortDir: filtros.sortDir === 'asc' ? 'desc' : 'asc' })}
          className="text-xs border border-gray-200 rounded-l px-2 py-1.5 text-gray-600 hover:bg-gray-50 border-r-0"
          title={filtros.sortDir === 'asc' ? 'Ascending' : 'Descending'}>
          {filtros.sortDir === 'asc' ? '↑' : '↓'}
        </button>
        <div className="border-t border-b border-r border-gray-200 rounded-r">
          <DropdownFilter value={filtros.sortBy} options={sortOpts} onChange={v => onFiltro({ ...filtros, sortBy: v })} />
        </div>
      </div>

      <div className="w-px h-5 bg-gray-200" />

      <div className="relative flex-1 min-w-36">
        <input type="text" placeholder="Search transactions..." value={busqueda}
          onChange={e => onBusqueda(e.target.value)}
          className="w-full px-3 py-1.5 text-xs border border-gray-200 rounded focus:outline-none focus:border-primary-400" />
      </div>

      <div className="w-px h-5 bg-gray-200" />

      <div className="flex rounded border border-gray-200 overflow-hidden">
        {['all', 'pending'].map(m => (
          <button key={m} onClick={() => onModo(m)}
            className={`text-xs px-3 py-1.5 transition-colors ${
              modo === m ? 'bg-primary-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'
            }`}>
            {m === 'all' ? 'All' : 'Pending'}
          </button>
        ))}
      </div>

      {hayFiltrosActivos && (
        <button onClick={onClearFilters}
          className="text-xs px-2.5 py-1.5 border border-gray-200 rounded text-gray-500 hover:bg-gray-50 hover:text-gray-700 transition-colors"
          title="Clear all filters">
          ✕ Clear
        </button>
      )}

      <div className="w-px h-5 bg-gray-200" />

      <div className="flex items-center gap-1">
        <button onClick={undo} disabled={!undoStack.length} title="Undo (Ctrl+Z)"
          className="p-1.5 rounded hover:bg-gray-100 disabled:opacity-25 text-gray-400 text-sm">↩</button>
        <button onClick={redo} disabled={!redoStack.length} title="Redo (Ctrl+Y)"
          className="p-1.5 rounded hover:bg-gray-100 disabled:opacity-25 text-gray-400 text-sm">↪</button>
        <button onClick={onRefresh} title="Refresh"
          className="p-1.5 rounded hover:bg-gray-100 text-gray-400 text-sm">↻</button>
      </div>
    </div>
  )
}

// -- Componente principal ----------------------------------------------
function TransaccionesInner() {
  const [items,        setItems]        = useState([])
  const [categorias,   setCategorias]   = useState([])
  const [contrapartes, setContrapartes] = useState([])
  const [cuentas,      setCuentas]      = useState([])
  const [loading,      setLoading]      = useState(false)
  const [selected,     setSelected]     = useState(null)
  const [busqueda,     setBusqueda]     = useState('')
  const [modo,         setModo]         = useState('pending')
  const [filtros,      setFiltros]      = useState(FILTROS_INICIAL)
  const [showAddModal, setShowAddModal] = useState(false)

  const [listWidth, setListWidth] = useState(LIST_DEFAULT)
  const dragging = useRef(false)
  const startX   = useRef(0)
  const startW   = useRef(0)

  const onMouseDown = useCallback((e) => {
    dragging.current = true
    startX.current   = e.clientX
    startW.current   = listWidth
    document.body.style.cursor     = 'col-resize'
    document.body.style.userSelect = 'none'
  }, [listWidth])

  useEffect(() => {
    function onMove(e) {
      if (!dragging.current) return
      setListWidth(Math.max(LIST_MIN, Math.min(LIST_MAX, startW.current + e.clientX - startX.current)))
    }
    function onUp() {
      dragging.current = false
      document.body.style.cursor     = ''
      document.body.style.userSelect = ''
    }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
    return () => {
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
  }, [])

  const cargar = useCallback(async () => {
    setLoading(true)
    try {
      const [dataRes, catsRes, cpsRes, cuentasRes] = await Promise.all([
        api.listar({
          estado: modo === 'pending' ? 'pendiente' : 'all',
          origen: filtros.origen !== 'all' ? filtros.origen : undefined,
          limit: 200,
        }),
        api.getCategorias().catch(() => ({ items: [] })),
        api.getContrapartes().catch(() => ({ items: [] })),
        api.getCuentas().catch(() => ({ items: [] })),
      ])

      let result = dataRes.items ?? []
      result = result.sort((a, b) => {
        const field = filtros.sortBy === 'monto' ? 'monto' : 'fecha'
        const va = a[field] ?? (filtros.sortBy === 'monto' ? 0 : '')
        const vb = b[field] ?? (filtros.sortBy === 'monto' ? 0 : '')
        if (filtros.sortBy === 'monto') return filtros.sortDir === 'asc' ? va - vb : vb - va
        return filtros.sortDir === 'asc'
          ? String(va).localeCompare(String(vb))
          : String(vb).localeCompare(String(va))
      })

      setItems(result)
      setCategorias(Array.isArray(catsRes)    ? catsRes    : (catsRes?.items    ?? []))
      setContrapartes(Array.isArray(cpsRes)   ? cpsRes     : (cpsRes?.items     ?? []))
      setCuentas(Array.isArray(cuentasRes)    ? cuentasRes : (cuentasRes?.items ?? []))

      if (result.length > 0 && !selected) setSelected(result[0])
    } catch (e) {
      toast.error('Error: ' + (e.response?.data?.detail ?? e.message))
    } finally {
      setLoading(false)
    }
  }, [modo, filtros])

  useEffect(() => { cargar() }, [cargar])

  function handleClearFilters() {
    setFiltros(FILTROS_INICIAL)
    setBusqueda('')
    setModo('pending')
  }

  const itemsFiltrados = items.filter(item => {
    if (busqueda) {
      const q = busqueda.toLowerCase()
      if (!Object.values(item).some(v => String(v ?? '').toLowerCase().includes(q))) return false
    }
    if (filtros.desde && item.fecha && item.fecha < filtros.desde) return false
    if (filtros.hasta && item.fecha && item.fecha > filtros.hasta) return false
    if (filtros.persona !== 'all') {
      if (filtros.persona === 'Unknown') {
        if (item.quien_pago && item.quien_pago !== 'Unknown') return false
      } else {
        if (item.quien_pago !== filtros.persona) return false
      }
    }
    return true
  })

  async function handleConfirmar(id) {
    try {
      await api.confirmar(id)
      toast.success('Confirmed')
      setSelected(items.find(i => i.id !== id) ?? null)
      cargar()
    } catch (e) {
      toast.error(e.response?.data?.detail ?? e.message)
    }
  }

  async function handleDescartar(id) {
    try {
      await api.descartar(id)
      toast.success('Discarded')
      setSelected(items.find(i => i.id !== id) ?? null)
      cargar()
    } catch (e) {
      toast.error(e.response?.data?.detail ?? e.message)
    }
  }

  async function handleEditar(id, data) {
    await api.editar(id, data)
  }

  // Agrega al catalogo en memoria la entidad recien creada al confirmar una EP,
  // para que AutocompleteSelect pueda resolver su label sin esperar un refetch.
  function handleCatalogoActualizado(tipo, nuevoItem) {
    const setters = {
      contraparte: setContrapartes,
      categoria:   setCategorias,
      cuenta:      setCuentas,
    }
    const setter = setters[tipo]
    if (!setter) return
    setter(prev => {
      const lista = Array.isArray(prev) ? prev : []
      return lista.some(x => x.id === nuevoItem.id) ? lista : [...lista, nuevoItem]
    })
  }

  const pendientes = items.filter(i => i.estado === 'pendiente').length

  return (
    <div className="flex flex-col h-full">

      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-white flex-shrink-0">
        <div>
          <h1 className="text-base font-semibold text-gray-900">Transactions</h1>
          <p className="text-xs text-gray-500">
            {items.length} total · <span className="text-yellow-600">{pendientes} need review</span>
          </p>
        </div>
        <button onClick={() => setShowAddModal(true)}
          className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors">
          Add New
        </button>
      </div>

      <AddTransactionModal
        open={showAddModal}
        onClose={() => setShowAddModal(false)}
        categorias={categorias}
        contrapartes={contrapartes}
        cuentas={cuentas}
        onCreated={cargar}
      />

      <Toolbar
        filtros={filtros}     onFiltro={setFiltros}
        busqueda={busqueda}   onBusqueda={setBusqueda}
        modo={modo}           onModo={setModo}
        onRefresh={cargar}    onClearFilters={handleClearFilters}
      />

      <div className="flex flex-1 overflow-hidden">
        <div className="flex-shrink-0 border-r border-gray-200 overflow-y-auto bg-white"
          style={{ width: listWidth }}>
          {loading ? (
            <div className="flex items-center justify-center py-10 text-gray-400 text-xs">Loading...</div>
          ) : itemsFiltrados.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-gray-400">
              <p className="text-sm font-medium text-gray-600">All clear</p>
            </div>
          ) : itemsFiltrados.map(item => (
            <TrxRow key={item.id} item={item}
              selected={selected?.id === item.id} onClick={setSelected} />
          ))}
        </div>

        <div onMouseDown={onMouseDown}
          className="w-1 flex-shrink-0 cursor-col-resize hover:bg-primary-200 transition-colors" />

        <DetailPanel
          item={selected}
          categorias={categorias}
          contrapartes={contrapartes}
          cuentas={cuentas}
          onConfirmar={handleConfirmar}
          onDescartar={handleDescartar}
          onEditar={handleEditar}
          onCatalogoActualizado={handleCatalogoActualizado}
          onRecargar={cargar}
        />
      </div>
    </div>
  )
}

export default function Transacciones() {
  return (
    <TransaccionesErrorBoundary>
      <TransaccionesInner />
    </TransaccionesErrorBoundary>
  )
}
