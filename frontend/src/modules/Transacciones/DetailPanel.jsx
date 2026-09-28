/**
 * modules/Transacciones/DetailPanel.jsx
 *
 * Extraido de index.jsx para poder reusarse embebido en el widget "Ultimas
 * transacciones" del Home (variante D) sin cambiar el comportamiento de la
 * pantalla de Transacciones -- ver plan aprobado en la sesion de diseno.
 *
 * Prop `modo`:
 *   'inbox'    (default, comportamiento original) -- barra de acciones
 *              Confirm/Discard, para la cola de revision del inbox.
 *   'edicion'  -- barra de acciones Guardar/Cancelar, para editar una
 *              transaccion ya confirmada sin salir de donde se la abrio
 *              (ej. el widget de Home). Solo requiere `onEditar` y
 *              `onCerrar`; `onConfirmar`/`onDescartar` no se usan.
 */
import { useState, useEffect, useRef } from 'react'
import toast from 'react-hot-toast'
import useAppStore from '@/store/useAppStore'
import {
  api, fmt, INPUT, SELECT, RO, CHECK, Field,
  AutocompleteSelect, AttachmentList, COMPLETITUD_BADGE, ORIGEN_LABEL,
} from './shared'

export default function DetailPanel({
  item, categorias, contrapartes, cuentas,
  onConfirmar, onDescartar, onEditar, onCatalogoActualizado, onRecargar,
  modo = 'inbox', onCerrar,
}) {
  const { undo, redo, undoStack, redoStack } = useAppStore()
  const [vals,   setVals]   = useState({})
  const [dirty,  setDirty]  = useState(false)
  const [saving, setSaving] = useState(false)
  const [eps,      setEps]      = useState([])
  const [vinculos, setVinculos] = useState([])
  const [cargandoDetalle, setCargandoDetalle] = useState(false)
  const selectedIdRef = useRef(null)

  function valsDesde(fuente) {
    const tramo1 = fuente.tramos?.length >= 1 ? fuente.tramos[0] : null
    return {
      descripcion:             fuente.descripcion             ?? '',
      fecha:                   fuente.fecha                   ? fuente.fecha.slice(0, 10) : '',
      id_categoria:            fuente.id_categoria            ?? null,
      id_contraparte:          fuente.id_contraparte          ?? null,
      tipo:                    fuente.tipo                    ?? '',
      quien_pago:              fuente.quien_pago              ?? '',
      es_recurrente:           fuente.es_recurrente           ?? false,
      notas:                   fuente.notas                   ?? '',
      es_reembolsable:         fuente.es_reembolsable         ?? false,
      estado_reembolso:        fuente.estado_reembolso        ?? '',
      id_cuenta_origen_tramo1: tramo1?.id_cuenta_origen       ?? null,
    }
  }

  useEffect(() => {
    if (!item) return
    selectedIdRef.current = item.id

    // Inicializa con lo que ya tenemos (el summary de la lista) para que la
    // pantalla no arranque vacia; luego se completa con el detalle completo
    // (quien_pago, tramos) que el summary no trae -- Issue: bug quien/medio pago.
    setVals(valsDesde(item))
    setDirty(false)
    setCargandoDetalle(true)

    api.getDetalle(item.id)
      .then(detalle => {
        if (selectedIdRef.current !== item.id) return
        setVals(valsDesde({ ...item, ...detalle }))
      })
      .catch(() => {
        // El summary ya quedo cargado como fallback; los campos que solo trae
        // el detalle (quien_pago, tramos) se quedan en su estado vacio.
      })
      .finally(() => {
        if (selectedIdRef.current === item.id) setCargandoDetalle(false)
      })

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
      // El backend confirma tambien las EPs "hermanas" (mismo tipo+valor) de otras
      // transacciones, pero el array `items` del padre queda desactualizado -- sin
      // este refresh, al renavegar (a esta tx u otra con el mismo valor propuesto)
      // el campo se ve vacio porque se re-inicializa desde el item stale (Issue #47).
      onRecargar?.()
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

  async function handleGuardarEdicion() {
    setSaving(true)
    try {
      await onEditar(item.id, valsParaGuardar())
      onCerrar?.()
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
          {cargandoDetalle && <span className="ml-2 text-gray-300 normal-case">loading details...</span>}
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

      {/* Acciones -- Confirm/Discard en la cola de inbox, Save/Cancel al
          editar una transaccion ya confirmada (Home) */}
      <div className="flex gap-2 px-4 py-2.5 border-t border-gray-100 bg-white flex-shrink-0">
        {modo === 'edicion' ? (
          <>
            <button onClick={handleGuardarEdicion} disabled={saving}
              className="flex-1 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors">
              {saving ? 'Saving...' : 'Save changes'}
            </button>
            <button onClick={() => onCerrar?.()} disabled={saving}
              className="px-4 py-2 text-sm font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors">
              Cancel
            </button>
          </>
        ) : (
          <>
            <button onClick={handleSaveAndConfirm} disabled={saving}
              className="flex-1 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors">
              {saving ? 'Saving...' : dirty ? 'Save & Confirm' : 'Confirm'}
            </button>
            <button onClick={() => onDescartar(item.id)}
              className="px-4 py-2 text-sm font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
              Discard
            </button>
          </>
        )}
      </div>
    </div>
  )
}
