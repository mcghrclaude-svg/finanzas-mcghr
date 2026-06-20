import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import toast from 'react-hot-toast'

// ─── API helpers ─────────────────────────────────────────────────────────────

const inboxApi = {
  listar: (params) => apiClient.get('/inbox/', { params }).then(r => r.data),
  stats: () => apiClient.get('/inbox/stats').then(r => r.data),
  detalle: (id) => apiClient.get(`/inbox/${id}`).then(r => r.data),
  editar: (id, data) => apiClient.patch(`/inbox/${id}`, data).then(r => r.data),
  confirmar: (id, data) => apiClient.post(`/inbox/${id}/confirmar`, data).then(r => r.data),
  descartar: (id) => apiClient.post(`/inbox/${id}/descartar`).then(r => r.data),
  confirmarLote: (ids) => apiClient.post('/inbox/confirmar-lote', { ids }).then(r => r.data),
}

// ─── Helpers de formato ──────────────────────────────────────────────────────

function formatCOP(monto) {
  if (monto == null) return '—'
  return new Intl.NumberFormat('es-CO', {
    style: 'currency', currency: 'COP', minimumFractionDigits: 0,
  }).format(monto)
}

function formatFecha(fecha) {
  if (!fecha) return '—'
  return new Date(fecha).toLocaleDateString('es-CO', {
    day: 'numeric', month: 'short', year: 'numeric',
  })
}

// ─── Badge de confianza ───────────────────────────────────────────────────────

function BadgeConfianza({ confianza }) {
  if (confianza == null) return null
  const pct = Math.round(confianza * 100)
  if (confianza >= 0.85) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
        ✓ {pct}%
      </span>
    )
  }
  if (confianza >= 0.60) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
        ~ {pct}%
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-rose-100 px-2 py-0.5 text-xs font-medium text-rose-700">
      ! {pct}%
    </span>
  )
}

// ─── Badge de origen ─────────────────────────────────────────────────────────

function BadgeOrigen({ origen }) {
  const map = {
    email:  { label: 'Email',  cls: 'bg-blue-100 text-blue-700' },
    pdf:    { label: 'PDF',    cls: 'bg-purple-100 text-purple-700' },
    mobile: { label: 'Movil',  cls: 'bg-cyan-100 text-cyan-700' },
    manual: { label: 'Manual', cls: 'bg-gray-100 text-gray-600' },
  }
  const { label, cls } = map[origen] || { label: origen, cls: 'bg-gray-100 text-gray-600' }
  return (
    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>
      {label}
    </span>
  )
}

// ─── Panel lateral de edicion ─────────────────────────────────────────────────

function PanelEdicion({ item, catalogoCategorias, onConfirmar, onCerrar }) {
  const [categoria, setCategoria] = useState(item.id_categoria || '')
  const [descripcion, setDescripcion] = useState(item.descripcion || '')
  const [esReembolsable, setEsReembolsable] = useState(item.es_reembolsable || false)
  const [notas, setNotas] = useState(item.notas || '')

  function handleConfirmar() {
    onConfirmar({
      id_categoria: categoria || undefined,
      notas: notas || undefined,
    })
  }

  return (
    <div className="w-80 shrink-0 border-l border-slate-200 bg-white p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-800">Editar y confirmar</h3>
        <button
          onClick={onCerrar}
          className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
        >
          ✕
        </button>
      </div>

      <div className="flex flex-col gap-1">
        <span className="text-xs font-medium text-slate-500">Monto</span>
        <span className="text-base font-semibold text-slate-800">
          {formatCOP(item.monto)}
        </span>
        <span className="text-xs text-slate-400">{formatFecha(item.fecha)}</span>
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-xs font-medium text-slate-500">Descripcion</label>
        <input
          className="rounded-md border border-slate-200 px-3 py-1.5 text-sm text-slate-700 focus:border-primary-500 focus:outline-none"
          value={descripcion}
          onChange={e => setDescripcion(e.target.value)}
        />
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-xs font-medium text-slate-500">Categoria</label>
        <select
          className="rounded-md border border-slate-200 px-3 py-1.5 text-sm text-slate-700 focus:border-primary-500 focus:outline-none"
          value={categoria}
          onChange={e => setCategoria(e.target.value)}
        >
          <option value="">Sin asignar</option>
          {catalogoCategorias.map(c => (
            <option key={c.id} value={c.id}>{c.nombre}</option>
          ))}
        </select>
      </div>

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="reembolsable"
          checked={esReembolsable}
          onChange={e => setEsReembolsable(e.target.checked)}
          className="h-4 w-4 rounded border-slate-300 text-primary-600"
        />
        <label htmlFor="reembolsable" className="text-sm text-slate-600">
          Es reembolsable
        </label>
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-xs font-medium text-slate-500">Notas</label>
        <textarea
          className="rounded-md border border-slate-200 px-3 py-1.5 text-sm text-slate-700 focus:border-primary-500 focus:outline-none"
          rows={2}
          value={notas}
          onChange={e => setNotas(e.target.value)}
        />
      </div>

      <div className="mt-auto flex gap-2">
        <button
          onClick={handleConfirmar}
          className="flex-1 rounded-md bg-primary-600 px-3 py-2 text-sm font-medium text-white hover:bg-primary-700"
        >
          Confirmar
        </button>
        <button
          onClick={onCerrar}
          className="rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-600 hover:bg-slate-50"
        >
          Cancelar
        </button>
      </div>
    </div>
  )
}

// ─── Fila de item del inbox ───────────────────────────────────────────────────

function InboxRow({ item, onConfirmar, onDescartar, onEditar, seleccionado }) {
  return (
    <div className={`rounded-lg border bg-white p-4 transition-shadow hover:shadow-sm ${
      seleccionado ? 'border-primary-300 ring-1 ring-primary-200' : 'border-slate-200'
    }`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex flex-col gap-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <BadgeOrigen origen={item.origen} />
            <BadgeConfianza confianza={item.confianza} />
            {item.nombre_categoria && (
              <span className="text-xs text-slate-500">{item.nombre_categoria}</span>
            )}
          </div>
          <p className="text-sm font-medium text-slate-800 truncate">
            {item.descripcion || item.nombre_contraparte || 'Sin descripcion'}
          </p>
          <p className="text-xs text-slate-400">{formatFecha(item.fecha)}</p>
        </div>

        <div className="text-right shrink-0">
          <p className="text-base font-semibold text-slate-800">
            {formatCOP(item.monto)}
          </p>
          <p className="text-xs text-slate-400">{item.moneda}</p>
        </div>
      </div>

      <div className="mt-3 flex items-center gap-2">
        {item.confianza >= 0.60 && (
          <button
            onClick={() => onConfirmar(item.id, {})}
            className="rounded-md bg-green-600 px-3 py-1 text-xs font-medium text-white hover:bg-green-700"
          >
            Confirmar
          </button>
        )}
        <button
          onClick={() => onEditar(item)}
          className="rounded-md border border-slate-200 px-3 py-1 text-xs text-slate-600 hover:bg-slate-50"
        >
          {item.confianza < 0.60 ? 'Revisar y confirmar' : 'Editar'}
        </button>
        <button
          onClick={() => onDescartar(item.id)}
          className="ml-auto rounded-md px-3 py-1 text-xs text-rose-500 hover:bg-rose-50"
        >
          Descartar
        </button>
      </div>
    </div>
  )
}

// ─── Componente principal ────────────────────────────────────────────────────

export default function Inbox() {
  const qc = useQueryClient()
  const [filtroOrigen, setFiltroOrigen] = useState('')
  const [itemEditando, setItemEditando] = useState(null)
  const [seleccionados, setSeleccionados] = useState([])

  const { data: stats } = useQuery({
    queryKey: ['inbox-stats'],
    queryFn: inboxApi.stats,
    refetchInterval: 30_000,
  })

  const { data, isLoading } = useQuery({
    queryKey: ['inbox', filtroOrigen],
    queryFn: () => inboxApi.listar(filtroOrigen ? { origen: filtroOrigen } : {}),
  })

  const { data: catalogoCats } = useQuery({
    queryKey: ['catalogos-categorias'],
    queryFn: () => apiClient.get('/catalogos/categorias').then(r => r.data.items || []),
  })

  const mutConfirmar = useMutation({
    mutationFn: ({ id, body }) => inboxApi.confirmar(id, body),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ['inbox'] })
      qc.invalidateQueries({ queryKey: ['inbox-stats'] })
      toast.success(res.regla_creada ? 'Confirmado y regla guardada' : 'Confirmado')
      setItemEditando(null)
    },
    onError: (e) => toast.error(e.message),
  })

  const mutDescartar = useMutation({
    mutationFn: (id) => inboxApi.descartar(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['inbox'] })
      qc.invalidateQueries({ queryKey: ['inbox-stats'] })
      toast.success('Descartado')
    },
    onError: (e) => toast.error(e.message),
  })

  const mutLote = useMutation({
    mutationFn: (ids) => inboxApi.confirmarLote(ids),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ['inbox'] })
      qc.invalidateQueries({ queryKey: ['inbox-stats'] })
      toast.success(`${res.confirmados} transacciones confirmadas`)
      setSeleccionados([])
    },
    onError: (e) => toast.error(e.message),
  })

  const items = data?.items || []
  const altaPrioridad = items.filter(i => i.confianza < 0.60)
  const paraRevisar = items.filter(i => i.confianza >= 0.60 && i.confianza < 0.85)
  const listos = items.filter(i => i.confianza >= 0.85)

  function handleConfirmar(id, body) {
    mutConfirmar.mutate({ id, body })
  }

  function handleConfirmarLote() {
    const ids = listos.map(i => i.id)
    if (ids.length === 0) return
    mutLote.mutate(ids)
  }

  return (
    <div className="flex h-full gap-0">
      {/* Lista principal */}
      <div className="flex-1 overflow-y-auto px-1">
        {/* Header */}
        <div className="mb-5 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-slate-800">Inbox</h1>
            {stats && (
              <p className="text-sm text-slate-500">
                {stats.pendientes} pendientes
                {stats.alta_prioridad > 0 && (
                  <span className="ml-1 text-rose-500">
                    · {stats.alta_prioridad} requieren atencion
                  </span>
                )}
              </p>
            )}
          </div>

          {/* Filtros de origen */}
          <div className="flex gap-1">
            {['', 'email', 'pdf', 'mobile', 'manual'].map(o => (
              <button
                key={o}
                onClick={() => setFiltroOrigen(o)}
                className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                  filtroOrigen === o
                    ? 'bg-primary-600 text-white'
                    : 'border border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                {o === '' ? 'Todos' : o.charAt(0).toUpperCase() + o.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {isLoading && (
          <p className="text-sm text-slate-400">Cargando...</p>
        )}

        {!isLoading && items.length === 0 && (
          <div className="rounded-lg border border-dashed border-slate-200 p-10 text-center">
            <p className="text-sm text-slate-400">No hay transacciones pendientes.</p>
          </div>
        )}

        {/* Seccion alta prioridad */}
        {altaPrioridad.length > 0 && (
          <section className="mb-6">
            <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-rose-500">
              Alta prioridad — requieren atencion ({altaPrioridad.length})
            </h2>
            <div className="flex flex-col gap-2">
              {altaPrioridad.map(item => (
                <InboxRow
                  key={item.id}
                  item={item}
                  onConfirmar={handleConfirmar}
                  onDescartar={(id) => mutDescartar.mutate(id)}
                  onEditar={setItemEditando}
                  seleccionado={itemEditando?.id === item.id}
                />
              ))}
            </div>
          </section>
        )}

        {/* Seccion para revisar */}
        {paraRevisar.length > 0 && (
          <section className="mb-6">
            <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-amber-600">
              Para revisar ({paraRevisar.length})
            </h2>
            <div className="flex flex-col gap-2">
              {paraRevisar.map(item => (
                <InboxRow
                  key={item.id}
                  item={item}
                  onConfirmar={handleConfirmar}
                  onDescartar={(id) => mutDescartar.mutate(id)}
                  onEditar={setItemEditando}
                  seleccionado={itemEditando?.id === item.id}
                />
              ))}
            </div>
          </section>
        )}

        {/* Seccion listos */}
        {listos.length > 0 && (
          <section className="mb-6">
            <div className="mb-2 flex items-center justify-between">
              <h2 className="text-xs font-semibold uppercase tracking-wide text-green-600">
                Listos para confirmar ({listos.length})
              </h2>
              <button
                onClick={handleConfirmarLote}
                disabled={mutLote.isPending}
                className="rounded-md bg-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-green-700 disabled:opacity-50"
              >
                Confirmar todos ({listos.length})
              </button>
            </div>
            <div className="flex flex-col gap-2">
              {listos.map(item => (
                <InboxRow
                  key={item.id}
                  item={item}
                  onConfirmar={handleConfirmar}
                  onDescartar={(id) => mutDescartar.mutate(id)}
                  onEditar={setItemEditando}
                  seleccionado={itemEditando?.id === item.id}
                />
              ))}
            </div>
          </section>
        )}
      </div>

      {/* Panel lateral de edicion */}
      {itemEditando && (
        <PanelEdicion
          item={itemEditando}
          catalogoCategorias={catalogoCats || []}
          onConfirmar={(body) => handleConfirmar(itemEditando.id, body)}
          onCerrar={() => setItemEditando(null)}
        />
      )}
    </div>
  )
}
