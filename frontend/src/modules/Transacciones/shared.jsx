/**
 * modules/Transacciones/shared.jsx
 *
 * Piezas compartidas entre index.jsx (la pantalla de Transacciones) y
 * DetailPanel.jsx (extraido para poder reusarse embebido en el widget
 * "Ultimas transacciones" del Home) -- api client, helpers de formato,
 * inputs reutilizables y los subcomponentes que arma el panel de detalle
 * (AutocompleteSelect, AttachmentList).
 */
import { useState, useEffect, useRef } from 'react'
import client from '@/api/client'

// -- Constantes ----------------------------------------------------------
export const COMPLETITUD_DOT = {
  minimo:   'bg-red-500',
  parcial:  'bg-yellow-500',
  completo: 'bg-green-500',
}
export const COMPLETITUD_BADGE = {
  minimo:   'bg-red-100 text-red-600',
  parcial:  'bg-yellow-100 text-yellow-700',
  completo: 'bg-green-100 text-green-700',
}
export const ORIGEN_LABEL = {
  email: 'Mail', pdf: 'PDF / Extractos', mobile: 'Mobile', manual: 'Manual',
}
export const TIPO_VINCULO_BADGE = {
  factura:  'bg-blue-100 text-blue-700',
  extracto: 'bg-purple-100 text-purple-700',
}

// -- API -------------------------------------------------------------------
// El detalle/edicion (getDetalle, editar, confirmar, descartar, EPs, vinculos)
// vive en /inbox/*, no en /transacciones/* -- ese router ya cubria todas las
// transacciones (no solo las pendientes) antes de que /transacciones/
// existiera de verdad, y esta pantalla sigue apoyada en el.
export const api = {
  listar:               (p) => client.get('/inbox/', { params: p }).then(r => r.data),
  confirmar:            (id) => client.post(`/inbox/${id}/confirmar`).then(r => r.data),
  descartar:            (id) => client.post(`/inbox/${id}/descartar`).then(r => r.data),
  editar:               (id, data) => client.patch(`/inbox/${id}`, data).then(r => r.data),
  getCategorias:        () => client.get('/catalogos/categorias?solo_activas=true').then(r => r.data),
  getContrapartes:      () => client.get('/catalogos/contrapartes?solo_activas=true').then(r => r.data),
  getCuentas:           () => client.get('/catalogos/cuentas?solo_activas=true').then(r => r.data),
  getDetalle:           (id) => client.get(`/inbox/${id}`).then(r => r.data),
  getEPs:               (id) => client.get(`/inbox/${id}/entidades-potenciales`).then(r => r.data),
  confirmarEP:          (trxId, epId) => client.post(`/inbox/${trxId}/entidades-potenciales/${epId}/confirmar`).then(r => r.data),
  getVinculos:          (id) => client.get(`/inbox/${id}/vinculos`).then(r => r.data),
}

// -- Helpers de formato ------------------------------------------------------
export function fmt(monto, moneda = 'COP') {
  if (monto == null) return '-'
  return new Intl.NumberFormat('es-CO', {
    style: 'currency', currency: moneda, maximumFractionDigits: 0,
  }).format(monto)
}

export function fmtFecha(f) {
  if (!f) return '-'
  return new Date(f).toLocaleDateString('es-CO', {
    day: '2-digit', month: 'short', year: '2-digit',
  })
}

// -- Clases de input reutilizables ------------------------------------------
export const INPUT  = "w-full px-2.5 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-primary-400 h-[34px]"
export const SELECT = "w-full px-2.5 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-primary-400 bg-white h-[34px]"
export const RO     = "px-2.5 py-1.5 text-sm text-gray-500 bg-gray-50 border border-gray-200 rounded-lg truncate h-[34px] overflow-hidden"
export const CHECK  = "flex items-center gap-2 px-2.5 border border-gray-200 rounded-lg bg-white h-[34px]"

// -- Field helper ------------------------------------------------------------
export function Field({ label, children, cols = 1, hasPending = false }) {
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

// -- AutocompleteSelect -------------------------------------------------------
export function AutocompleteSelect({ value, onChange, options = [], placeholder = 'Select...', proposedLabel = null }) {
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

// -- AttachmentList -----------------------------------------------------------
export function AttachmentModal({ preview, onClose }) {
  // 'checking' | 'ok' | 'missing' -- evita mostrar el JSON crudo del error
  // 404 del backend cuando el documento no existe en disco (issue #43)
  const [status, setStatus] = useState('checking')

  useEffect(() => {
    function onKey(e) { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])

  useEffect(() => {
    // El endpoint solo soporta GET (HEAD devuelve 405), asi que el chequeo
    // de existencia usa GET -- el navegador reutiliza la respuesta cacheada
    // (Etag/Last-Modified) para el <img>/<iframe> que se renderiza despues.
    let cancelado = false
    setStatus('checking')
    fetch(preview.url)
      .then(res => { if (!cancelado) setStatus(res.ok ? 'ok' : 'missing') })
      .catch(() => { if (!cancelado) setStatus('missing') })
    return () => { cancelado = true }
  }, [preview.url])

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
          {status === 'checking' && (
            <span className="text-xs text-gray-400">Loading...</span>
          )}
          {status === 'missing' && (
            <span className="text-xs text-gray-400 italic">Archivo no disponible</span>
          )}
          {status === 'ok' && preview.isImage && (
            <img src={preview.url} alt={preview.nombre} className="max-w-full max-h-full object-contain"
              onError={() => setStatus('missing')} />
          )}
          {status === 'ok' && preview.isPdf && (
            <iframe src={preview.url} title={preview.nombre} className="w-full h-full min-h-[70vh]" />
          )}
        </div>
      </div>
    </div>
  )
}

export function AttachmentList({ vinculos = [] }) {
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
            <div className="flex items-center gap-2 px-2 py-1 bg-gray-50">
              <span className={`inline-flex px-1.5 py-0.5 rounded text-xs font-semibold ${TIPO_VINCULO_BADGE[v.tipo_vinculo] ?? 'bg-gray-100 text-gray-600'}`}>
                {v.tipo_vinculo}
              </span>
              <span className="text-xs text-gray-600 truncate flex-1" title={nombre}>{nombre}</span>
              <BtnExpand />
            </div>
          </div>
        )
      })}
      {preview && <AttachmentModal preview={preview} onClose={() => setPreview(null)} />}
    </div>
  )
}
