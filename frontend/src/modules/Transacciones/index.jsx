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
const ORIGEN_LABEL = {
  email: 'Mail', pdf: 'PDF / Extractos', mobile: 'Mobile', manual: 'Manual',
}

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

// -- API ---------------------------------------------------------------
const api = {
  listar:               (p) => client.get('/inbox/', { params: p }).then(r => r.data),
  confirmar:            (id) => client.post(`/inbox/${id}/confirmar`).then(r => r.data),
  descartar:            (id) => client.post(`/inbox/${id}/descartar`).then(r => r.data),
  editar:               (id, data) => client.patch(`/inbox/${id}`, data).then(r => r.data),
  getCategorias:        () => client.get('/catalogos/categorias?solo_activas=true').then(r => r.data),
  getContrapartes:      () => client.get('/catalogos/contrapartes?solo_activas=true').then(r => r.data),
  getCuentas:           () => client.get('/catalogos/cuentas?solo_activas=true').then(r => r.data),
  getEPs:               (id) => client.get(`/inbox/${id}/entidades-potenciales`).then(r => r.data),
  confirmarEP:          (trxId, epId) => client.post(`/inbox/${trxId}/entidades-potenciales/${epId}/confirmar`).then(r => r.data),
  getVinculos:          (id) => client.get(`/inbox/${id}/vinculos`).then(r => r.data),
}

// -- Helpers -----------------------------------------------------------
function fmt(monto, moneda = 'COP') {
  if (monto == null) return '-'
  return new Intl.NumberFormat('es-CO', {
    style: 'currency', currency: moneda, maximumFractionDigits: 0,
  }).format(monto)
}

function fmtFecha(f) {
  if (!f) return '-'
  return new Date(f).toLocaleDateString('es-CO', {
    day: '2-digit', month: 'short', year: '2-digit',
  })
}

// -- AutocompleteSelect ------------------------------------------------
function AutocompleteSelect({ value, onChange, options = [], placeholder = 'Select...', proposedLabel = null }) {
  const [query, setQuery] = useState('')
  const [open,  setOpen]  = useState(false)
  const ref = useRef()

  useEffect(() => {
    function handler(e) {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false)
        setQuery('')
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const selected = options.find(o => o.id === value)
  const filtered = (query.trim()
    ? options.filter(o => o.label.toLowerCase().includes(query.toLowerCase()))
    : options
  ).slice().sort((a, b) => (b.proposed ? 1 : 0) - (a.proposed ? 1 : 0))

  // Propuesta pendiente de EP: solo informativa, no cuenta como valor seleccionado.
  // Se pinta como placeholder (nunca como el value real del input) para que quede
  // claro que el campo no esta completo hasta click en Confirm o eleccion manual.
  const showProposed = !open && !selected && !!proposedLabel

  function handleSelect(opt) {
    onChange(opt ? opt.id : null)
    setOpen(false)
    setQuery('')
  }

  return (
    <div className="relative" ref={ref}>
      <div className={`flex items-center border rounded-lg bg-white hover:border-primary-400 focus-within:border-primary-400 h-[34px] ${
        showProposed ? 'border-red-200 bg-red-50/40' : 'border-gray-200'
      }`}>
        <input
          type="text"
          value={open ? query : (selected?.label ?? '')}
          onChange={e => { setQuery(e.target.value); if (!open) setOpen(true) }}
          onFocus={() => setOpen(true)}
          placeholder={showProposed ? `⚠ ${proposedLabel}` : placeholder}
          title={showProposed ? `Propuesta pendiente (sin confirmar): ${proposedLabel}` : (!open && selected ? selected.label : undefined)}
          className={`flex-1 min-w-0 px-2.5 py-1.5 text-sm bg-transparent focus:outline-none rounded-lg truncate ${
            showProposed ? 'placeholder-red-600 placeholder:font-semibold' : ''
          }`}
        />
        {value && (
          <button onClick={() => handleSelect(null)} tabIndex={-1}
            className="px-1.5 text-gray-300 hover:text-gray-500 text-xs flex-shrink-0">✕</button>
        )}
        <button onClick={() => setOpen(o => !o)} tabIndex={-1}
          className="px-1.5 text-gray-400 text-xs flex-shrink-0">▾</button>
      </div>
      {open && (
        <div className="absolute top-full left-0 right-0 mt-1 z-50 bg-white border border-gray-200 rounded-xl shadow-lg max-h-52 overflow-y-auto">
          <button onClick={() => handleSelect(null)}
            className="w-full text-left px-3 py-2 text-sm text-gray-400 hover:bg-gray-50 border-b border-gray-100">
            -- None --
          </button>
          {filtered.length === 0
            ? <div className="px-3 py-2 text-xs text-gray-400">No results</div>
            : filtered.map(opt => (
              <button key={opt.id} onClick={() => handleSelect(opt)}
                title={opt.proposed ? 'Propuesta automatica del ETL, pendiente de confirmar' : undefined}
                className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-50 ${
                  opt.proposed
                    ? 'text-red-600 font-semibold'
                    : value === opt.id ? 'text-primary-700 font-medium bg-primary-50' : 'text-gray-700'
                }`}>
                {opt.label}
              </button>
            ))
          }
        </div>
      )}
    </div>
  )
}

// -- AttachmentList ----------------------------------------------------
const TIPO_VINCULO_BADGE = {
  factura:  'bg-blue-100 text-blue-700',
  extracto: 'bg-purple-100 text-purple-700',
}

function AttachmentModal({ preview, onClose }) {
  useEffect(() => {
    function onKey(e) { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div onClick={onClose}
      className="fixed inset-0 z-[100] bg-black/60 flex items-center justify-center p-6">
      <div onClick={e => e.stopPropagation()}
        className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[85vh] flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 flex-shrink-0">
          <span className="text-sm font-medium text-gray-700 truncate">{preview.nombre}</span>
          <button onClick={onClose} title="Close"
            className="p-1 rounded hover:bg-gray-100 text-gray-400 text-sm flex-shrink-0">✕</button>
        </div>
        <div className="flex-1 overflow-auto bg-gray-50 flex items-center justify-center">
          {preview.isImage && (
            <img src={preview.url} alt={preview.nombre} className="max-w-full max-h-full object-contain" />
          )}
          {preview.isPdf && (
            <iframe src={preview.url} title={preview.nombre} className="w-full h-full min-h-[70vh]" />
          )}
        </div>
      </div>
    </div>
  )
}

function AttachmentList({ vinculos = [] }) {
  const [preview, setPreview] = useState(null)

  if (vinculos.length === 0) return (
    <span className="text-xs text-gray-400 italic">No attachments</span>
  )

  return (
    <div className="space-y-1.5">
      {vinculos.map(v => {
        const url  = v.url ?? ''
        const ext  = (v.nombre_archivo ?? '').split('.').pop()?.toLowerCase()
        const isImage = ['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext)
        const isPdf   = ext === 'pdf'
        const nombre  = v.nombre_archivo || v.id_documento

        const BtnExpand = () => (
          <button type="button" onClick={() => setPreview({ url, nombre, isImage, isPdf })} title="Expand"
            className="inline-flex items-center justify-center w-6 h-6 rounded text-gray-400 hover:text-primary-600 hover:bg-gray-100 transition-colors flex-shrink-0">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="w-3.5 h-3.5">
              <path d="M3 3h4v1.5H4.5v7h7V10H13v4H3V3z"/>
              <path d="M9 3h4v4h-1.5V5.56L7.28 9.78 6.22 8.72 10.44 4.5H9V3z"/>
            </svg>
          </button>
        )

        return (
          <div key={v.id} className="border border-gray-200 rounded-lg overflow-hidden">
            <div className="flex items-center gap-2 px-2 py-1 bg-gray-50 border-b border-gray-200">
              <span className={`inline-flex px-1.5 py-0.5 rounded text-xs font-semibold ${TIPO_VINCULO_BADGE[v.tipo_vinculo] ?? 'bg-gray-100 text-gray-600'}`}>
                {v.tipo_vinculo}
              </span>
              <span className="text-xs text-gray-600 truncate flex-1" title={nombre}>{nombre}</span>
              <BtnExpand />
            </div>
            {url && isImage && (
              <img src={url} alt={nombre} className="w-full object-contain max-h-24" />
            )}
            {url && isPdf && (
              <iframe src={url} title={nombre} className="w-full h-24" />
            )}
          </div>
        )
      })}
      {preview && <AttachmentModal preview={preview} onClose={() => setPreview(null)} />}
    </div>
  )
}

// -- Field helper ------------------------------------------------------
function Field({ label, children, cols = 1, hasPending = false }) {
  const spanClass = cols === 4 ? 'col-span-4' : cols === 3 ? 'col-span-3' : cols === 2 ? 'col-span-2' : ''
  return (
    <div className={`min-w-0 ${spanClass}`}>
      <label className={`block text-xs font-semibold uppercase tracking-wider mb-0.5 ${hasPending ? 'text-red-600' : 'text-gray-400'}`}>
        {label}{hasPending && ' ⚠'}
      </label>
      {children}
    </div>
  )
}

// -- Clases de input reutilizables ------------------------------------
const INPUT  = "w-full px-2.5 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-primary-400 h-[34px]"
const SELECT = "w-full px-2.5 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-primary-400 bg-white h-[34px]"
const RO     = "px-2.5 py-1.5 text-sm text-gray-500 bg-gray-50 border border-gray-200 rounded-lg truncate h-[34px] overflow-hidden"
const CHECK  = "flex items-center gap-2 px-2.5 border border-gray-200 rounded-lg bg-white h-[34px]"

// -- DetailPanel -------------------------------------------------------
function DetailPanel({ item, categorias, contrapartes, cuentas, onConfirmar, onDescartar, onEditar, onCatalogoActualizado }) {
  const { undo, redo, undoStack, redoStack } = useAppStore()
  const [vals,   setVals]   = useState({})
  const [dirty,  setDirty]  = useState(false)
  const [saving, setSaving] = useState(false)
  const [eps,      setEps]      = useState([])
  const [vinculos, setVinculos] = useState([])

  useEffect(() => {
    if (!item) return
    const tramo1 = item.tramos?.length >= 1 ? item.tramos[0] : null
    setVals({
      descripcion:             item.descripcion             ?? '',
      fecha:                   item.fecha                   ? item.fecha.slice(0, 10) : '',
      id_categoria:            item.id_categoria            ?? null,
      id_contraparte:          item.id_contraparte          ?? null,
      tipo:                    item.tipo                    ?? '',
      quien_pago:              item.quien_pago              ?? '',
      es_recurrente:           item.es_recurrente           ?? false,
      notas:                   item.notas                   ?? '',
      es_reembolsable:         item.es_reembolsable         ?? false,
      estado_reembolso:        item.estado_reembolso        ?? '',
      id_cuenta_origen_tramo1: tramo1?.id_cuenta_origen     ?? null,
    })
    setDirty(false)
    api.getEPs(item.id).then(d => setEps(d.items ?? [])).catch(() => setEps([]))
    api.getVinculos(item.id).then(d => setVinculos(d.items ?? [])).catch(() => setVinculos([]))
  }, [item?.id])

  // Filtra IDs sinteticos (__ep_N__) antes de enviar al backend
  function valsParaGuardar() {
    return Object.fromEntries(
      Object.entries(vals).filter(([, v]) => !String(v ?? '').startsWith('__ep_'))
    )
  }

  async function handleConfirmarEP(ep, fieldKey) {
    try {
      const res = await api.confirmarEP(item.id, ep.id)
      set(fieldKey, res.nuevo_id)
      setEps(prev => prev.filter(e => e.id !== ep.id))
      // El catalogo del padre (contrapartes/categorias/cuentas) todavia no conoce
      // la entidad recien creada -- sin esto, AutocompleteSelect no encuentra el
      // id en sus options y el campo se ve vacio pese a tener el valor seteado.
      onCatalogoActualizado?.(res.tipo, { id: res.nuevo_id, nombre: ep.valor_propuesto })
      toast.success(`Created: ${res.nuevo_id}`)
    } catch (e) {
      toast.error(e.response?.data?.detail ?? e.message)
    }
  }

  function set(key, value) {
    setVals(prev => ({ ...prev, [key]: value }))
    setDirty(true)
  }

  async function handleSaveAndConfirm() {
    setSaving(true)
    try {
      if (dirty) await onEditar(item.id, valsParaGuardar())
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

  const multiTramo = (item.tramos?.length ?? 0) > 1

  const catOpts    = (Array.isArray(categorias)  ? categorias  : []).map(c => ({ id: c.id, label: c.nombre }))
  const cpOpts     = (Array.isArray(contrapartes) ? contrapartes : []).map(c => ({ id: c.id, label: c.nombre }))
  const cuentaOpts = (Array.isArray(cuentas)      ? cuentas     : []).map(c => ({ id: c.id, label: c.nombre }))

  // Entidades potenciales pendientes para esta transaccion
  const epCp  = eps.find(e => e.tipo === 'contraparte')
  const epCat = eps.find(e => e.tipo === 'categoria')
  const epCta = eps.find(e => e.tipo === 'cuenta')

  // Inyecta la propuesta como opcion en el dropdown (con marcador __ep_)
  // proposed:true hace que AutocompleteSelect la muestre arriba de todo y en rojo
  const cpOptsConProp  = epCp  ? [...cpOpts,     { id: `__ep_${epCp.id}`,  label: `${epCp.valor_propuesto} (proposed)`,  proposed: true }] : cpOpts
  const catOptsConProp = epCat ? [...catOpts,     { id: `__ep_${epCat.id}`, label: `${epCat.valor_propuesto} (proposed)`, proposed: true }] : catOpts
  const ctaOptsConProp = epCta ? [...cuentaOpts,  { id: `__ep_${epCta.id}`, label: `${epCta.valor_propuesto} (proposed)`, proposed: true }] : cuentaOpts

  return (
    <div className="flex-1 flex flex-col overflow-hidden">

      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-100 bg-white flex-shrink-0">
        <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">
          {ORIGEN_LABEL[item.origen] ?? item.origen}
        </span>
        <div className="flex items-center gap-1">
          <button onClick={undo} disabled={!undoStack.length} title="Undo (Ctrl+Z)"
            className="p-1 rounded hover:bg-gray-100 disabled:opacity-25 text-gray-400 text-sm">↩</button>
          <button onClick={redo} disabled={!redoStack.length} title="Redo (Ctrl+Y)"
            className="p-1 rounded hover:bg-gray-100 disabled:opacity-25 text-gray-400 text-sm">↪</button>
          <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ml-1 ${COMPLETITUD_BADGE[item.completitud] ?? ''}`}>
            {item.completitud}
          </span>
        </div>
      </div>

      {/* Contenido -- grid 4 columnas */}
      <div className="flex-1 overflow-y-auto px-4 py-3">

        {item.completitud === 'minimo' && (
          <div className="bg-red-50 border border-red-100 text-red-600 text-xs rounded-lg px-3 py-1.5 mb-2">
            Minimal data -- please review all fields before confirming.
          </div>
        )}

        <div className="grid grid-cols-4 gap-x-2.5 gap-y-2">

          {/* Fila 1: Description (3 cols) | Amount readonly (1 col) */}
          <Field label="Description" cols={3}>
            <input type="text" value={vals.descripcion ?? ''} onChange={e => set('descripcion', e.target.value)}
              placeholder="Transaction description" className={INPUT} title={vals.descripcion} />
          </Field>
          <Field label="Amount">
            <div className={RO} title={fmt(item.monto, item.moneda)}>{fmt(item.monto, item.moneda)}</div>
          </Field>

          {/* Fila 2: Currency readonly | Date | Tipo | Quien Pago */}
          <Field label="Currency">
            <div className={RO}>{item.moneda ?? 'COP'}</div>
          </Field>
          <Field label="Date">
            <input type="date" value={vals.fecha ?? ''} onChange={e => set('fecha', e.target.value)}
              className={INPUT} />
          </Field>
          <Field label="Tipo">
            <select value={vals.tipo ?? ''} onChange={e => set('tipo', e.target.value)} className={SELECT}>
              <option value="">-- Select --</option>
              <option value="gasto">Gasto</option>
              <option value="ingreso">Ingreso</option>
              <option value="transferencia">Transferencia</option>
              <option value="ajuste">Ajuste</option>
            </select>
          </Field>
          <Field label="Quien Pago">
            <select value={vals.quien_pago ?? ''} onChange={e => set('quien_pago', e.target.value)} className={SELECT}>
              <option value="">-- Select --</option>
              <option value="GHR">GHR (Hernan)</option>
              <option value="MC">MC (Martha)</option>
              <option value="Unknown">Unknown</option>
            </select>
          </Field>

          {/* Fila 3: Counterpart (2 cols) | Paid With | Es Recurrente */}
          <Field label="Counterpart" cols={2} hasPending={!!epCp}>
            <div className="flex gap-1 min-w-0">
              <div className="flex-1 min-w-0">
                <AutocompleteSelect
                  value={vals.id_contraparte}
                  onChange={v => set('id_contraparte', v)}
                  options={cpOptsConProp}
                  placeholder="Search entity..."
                  proposedLabel={epCp?.valor_propuesto}
                />
              </div>
              {epCp && (
                <button onClick={() => handleConfirmarEP(epCp, 'id_contraparte')} title={`Confirm: ${epCp.valor_propuesto}`}
                  className="flex-shrink-0 w-[34px] h-[34px] flex items-center justify-center rounded-lg border border-red-300 bg-red-50 text-red-600 hover:bg-red-100 text-sm font-bold transition-colors">
                  ✓
                </button>
              )}
            </div>
          </Field>
          <Field label="Paid With" hasPending={!!epCta}>
            <div className="flex gap-1 min-w-0">
              <div className="flex-1 min-w-0">
                <AutocompleteSelect
                  value={vals.id_cuenta_origen_tramo1}
                  onChange={v => set('id_cuenta_origen_tramo1', v)}
                  options={ctaOptsConProp}
                  placeholder="Select account..."
                  proposedLabel={epCta?.valor_propuesto}
                />
              </div>
              {epCta && (
                <button onClick={() => handleConfirmarEP(epCta, 'id_cuenta_origen_tramo1')} title={`Confirm: ${epCta.valor_propuesto}`}
                  className="flex-shrink-0 w-[34px] h-[34px] flex items-center justify-center rounded-lg border border-red-300 bg-red-50 text-red-600 hover:bg-red-100 text-sm font-bold transition-colors">
                  ✓
                </button>
              )}
            </div>
          </Field>
          <Field label="Es Recurrente">
            <div className={CHECK}>
              <input type="checkbox" id="chk_recurrente" checked={!!vals.es_recurrente}
                onChange={e => set('es_recurrente', e.target.checked)}
                className="w-4 h-4 accent-primary-600 flex-shrink-0" />
              <label htmlFor="chk_recurrente" className="text-sm text-gray-700 cursor-pointer">
                {vals.es_recurrente ? 'Yes' : 'No'}
              </label>
            </div>
          </Field>

          {/* Aviso multi-tramo si aplica */}
          {multiTramo && (
            <div className="col-span-4 -mt-1">
              <p className="text-xs text-amber-600 bg-amber-50 border border-amber-100 rounded px-2 py-1">
                Multi-leg transaction ({item.tramos.length} legs) -- editing account of leg 1 only
              </p>
            </div>
          )}

          {/* Fila 4: Category (2 cols) | Es Reembolsable | Estado Reembolso */}
          <Field label="Category" cols={2} hasPending={!!epCat}>
            <div className="flex gap-1 min-w-0">
              <div className="flex-1 min-w-0">
                <AutocompleteSelect
                  value={vals.id_categoria}
                  onChange={v => set('id_categoria', v)}
                  options={catOptsConProp}
                  placeholder="Search category..."
                  proposedLabel={epCat?.valor_propuesto}
                />
              </div>
              {epCat && (
                <button onClick={() => handleConfirmarEP(epCat, 'id_categoria')} title={`Confirm: ${epCat.valor_propuesto}`}
                  className="flex-shrink-0 w-[34px] h-[34px] flex items-center justify-center rounded-lg border border-red-300 bg-red-50 text-red-600 hover:bg-red-100 text-sm font-bold transition-colors">
                  ✓
                </button>
              )}
            </div>
          </Field>
          <Field label="Es Reembolsable">
            <div className={CHECK}>
              <input type="checkbox" id="chk_reembolsable" checked={!!vals.es_reembolsable}
                onChange={e => set('es_reembolsable', e.target.checked)}
                className="w-4 h-4 accent-primary-600 flex-shrink-0" />
              <label htmlFor="chk_reembolsable" className="text-sm text-gray-700 cursor-pointer">
                {vals.es_reembolsable ? 'Yes' : 'No'}
              </label>
            </div>
          </Field>
          <Field label="Estado Reembolso">
            <select value={vals.estado_reembolso ?? ''} onChange={e => set('estado_reembolso', e.target.value)} className={SELECT}>
              <option value="">-- N/A --</option>
              <option value="pendiente">Pendiente</option>
              <option value="solicitado">Solicitado</option>
              <option value="recibido">Recibido</option>
            </select>
          </Field>

          {/* Fila 5: Source readonly | Confidence readonly | Notas (2 cols) */}
          <Field label="Source">
            <div className={RO} title={ORIGEN_LABEL[item.origen] ?? item.origen}>
              {ORIGEN_LABEL[item.origen] ?? item.origen ?? '-'}
            </div>
          </Field>
          <Field label="Confidence">
            <div className={RO}>
              {item.confianza != null ? `${Math.round(item.confianza * 100)}%` : '-'}
            </div>
          </Field>
          <Field label="Notas" cols={2}>
            <textarea value={vals.notas ?? ''} onChange={e => set('notas', e.target.value)}
              placeholder="Notes..." rows={1}
              className="w-full px-2.5 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-primary-400 resize-none h-[34px]" />
          </Field>

          {/* Fila 6: Attachments reales desde tabla vinculos */}
          <Field label="Attachments" cols={4}>
            <AttachmentList vinculos={vinculos} />
          </Field>

        </div>
      </div>

      {/* Acciones */}
      <div className="flex gap-2 px-4 py-2.5 border-t border-gray-100 bg-white flex-shrink-0">
        <button onClick={handleSaveAndConfirm} disabled={saving}
          className="flex-1 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors">
          {saving ? 'Saving...' : dirty ? 'Save & Confirm' : 'Confirm'}
        </button>
        <button onClick={() => onDescartar(item.id)}
          className="px-4 py-2 text-sm font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
          Discard
        </button>
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
      </div>

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
