/**
 * modules/Catalogos/index.jsx — Version A
 * Cambios vs version anterior:
 *   - ID eliminado de la tabla (no se muestra al usuario)
 *   - ID eliminado del formulario (se autogenera como slug del nombre)
 *   - Tipo "Gobierno" agregado en Contrapartes
 *   - Titulo del modal corregido (genero)
 */
import { useState, useEffect, useCallback } from 'react'
import toast from 'react-hot-toast'
import { catalogosApi } from '@/api/catalogos'
import useAppStore from '@/store/useAppStore'
import { useUndo } from '@/hooks/useUndo'
import CategoriaTree from './CategoriaTree'
import TablaGenerica from './TablaGenerica'
import ModalForm from './ModalForm'
import ModalConfirm from './ModalConfirm'
import { generarSlugUnico, buildTree, CAMPOS_CATEGORIAS } from './categoriaConfig'

// Opciones del dropdown de Currency en el formulario de Cuentas -- catalogo
// real de Moneda (solo activas), no una lista fija. extra = { items, monedasActivas }.
function opcionesMoneda(values, extra) {
  return (extra?.monedasActivas ?? []).map(m => ({ value: m.id, label: `${m.id} - ${m.nombre}` }))
}

// ── Configuracion ─────────────────────────────────────────────────────────────

const SECCIONES = [
  { id: 'categorias',   label: 'Categories', icon: '🏷️' },
  { id: 'cuentas',      label: 'Accounts',   icon: '🏦' },
  { id: 'contrapartes', label: 'Entities',   icon: '🏢' },
  { id: 'personas',     label: 'People',     icon: '👤' },
  { id: 'monedas',      label: 'Currencies', icon: '💱' },
  { id: 'pendientes',   label: 'Pending',    icon: '⏳' },
]

const COLUMNAS = {
  cuentas: [
    { key: 'nombre', label: 'Name' },
    { key: 'tipo',   label: 'Type',     badge: true },
    { key: 'banco',  label: 'Bank' },
    { key: 'moneda', label: 'Currency', badge: true },
    { key: 'activa', label: 'Status',   estado: true },
  ],
  contrapartes: [
    { key: 'nombre', label: 'Name' },
    { key: 'tipo',   label: 'Type',   badge: true },
    { key: 'activa', label: 'Status', estado: true },
  ],
  personas: [
    { key: 'nombre', label: 'Name' },
    { key: 'alias',  label: 'Alias',  mono: true },
    { key: 'activa', label: 'Status', estado: true },
  ],
  monedas: [
    { key: 'id',      label: 'Code',   mono: true },
    { key: 'nombre',  label: 'Name' },
    { key: 'simbolo', label: 'Symbol', mono: true },
    { key: 'activa',  label: 'Status', estado: true },
  ],
}

const CAMPOS = {
  categorias: CAMPOS_CATEGORIAS,
  cuentas: [
    { key: 'nombre', label: 'Name',     type: 'text',   required: true },
    { key: 'tipo',   label: 'Type',     type: 'select',
      options: [
        { value: 'CC',        label: 'Checking account' },
        { value: 'TC',        label: 'Credit card' },
        { value: 'AHORRO',    label: 'Savings' },
        { value: 'INVERSION', label: 'Investment' },
        { value: 'EFECTIVO',  label: 'Cash' },
        { value: 'OTRO',      label: 'Other' },
      ]
    },
    { key: 'banco',  label: 'Bank',     type: 'text' },
    { key: 'moneda', label: 'Currency', type: 'select', hint: 'Optional -- leave blank for multi-currency accounts (e.g. credit cards)',
      emptyLabel: '-- No currency (multi-currency account) --',
      options: opcionesMoneda,
    },
    { key: 'propietario', label: 'Owner', type: 'select', required: true,
      options: [
        { value: 'GHR',   label: 'GHR' },
        { value: 'MC',    label: 'MC' },
        { value: 'Ambos', label: 'Both' },
      ]
    },
    { key: 'visible_pwa', label: 'Visible in PWA', type: 'checkbox' },
  ],
  contrapartes: [
    { key: 'nombre', label: 'Name', type: 'text', required: true },
    { key: 'tipo',   label: 'Type', type: 'select',
      options: [
        { value: 'COMERCIO', label: 'Commerce' },
        { value: 'BANCO',    label: 'Bank' },
        { value: 'GOBIERNO', label: 'Government' },
        { value: 'PERSONA',  label: 'Person' },
        { value: 'ENTIDAD',  label: 'Entity' },
      ]
    },
  ],
  personas: [
    { key: 'nombre', label: 'Name',  type: 'text', required: true },
    { key: 'alias',  label: 'Alias', type: 'text', hint: 'Nickname or initials' },
  ],
  monedas: [
    { key: 'codigo',  label: 'Code',   type: 'text', required: true, upper: true, lock_on_edit: true,
      hint: 'ISO 4217, e.g. COP, USD' },
    { key: 'nombre',  label: 'Name',   type: 'text', required: true, hint: 'e.g. Colombian Peso' },
    { key: 'simbolo', label: 'Symbol', type: 'text', hint: 'e.g. $' },
  ],
}

const API = {
  categorias:   { listar: (p) => catalogosApi.getCategorias(p),   crear: catalogosApi.crearCategoria,   editar: catalogosApi.editarCategoria,   inactivar: catalogosApi.inactivarCategoria   },
  cuentas:      { listar: (p) => catalogosApi.getCuentas(p),      crear: catalogosApi.crearCuenta,      editar: catalogosApi.editarCuenta,      inactivar: catalogosApi.inactivarCuenta      },
  contrapartes: { listar: (p) => catalogosApi.getContrapartes(p), crear: catalogosApi.crearContraparte, editar: catalogosApi.editarContraparte, inactivar: catalogosApi.inactivarContraparte },
  personas:     { listar: (p) => catalogosApi.getPersonas(p),     crear: catalogosApi.crearPersona,     editar: catalogosApi.editarPersona,     inactivar: catalogosApi.inactivarPersona     },
  monedas:      { listar: (p) => catalogosApi.getMonedas(p),      crear: catalogosApi.crearMoneda,      editar: catalogosApi.editarMoneda,      inactivar: catalogosApi.inactivarMoneda      },
}

const SINGULAR = {
  categorias: 'Category', cuentas: 'Account',
  contrapartes: 'Entity', personas: 'Person', monedas: 'Currency',
}

const TIPO_LABEL = { contraparte: 'Entity', cuenta: 'Account', categoria: 'Category' }
const TIPO_BADGE = {
  contraparte: 'bg-blue-100 text-blue-700',
  cuenta:      'bg-purple-100 text-purple-700',
  categoria:   'bg-green-100 text-green-700',
}

// ── PendingList ───────────────────────────────────────────────────────────────

function PendingList({ onReload }) {
  const [items,   setItems]   = useState([])
  const [loading, setLoading] = useState(false)
  const [working, setWorking] = useState(null)

  async function cargar() {
    setLoading(true)
    try {
      const data = await catalogosApi.getPendientes()
      setItems(data.items ?? [])
    } catch (e) {
      toast.error('Error loading pending: ' + (e.response?.data?.detail ?? e.message))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { cargar() }, [])

  async function handleConfirmar(id) {
    setWorking(id)
    try {
      const res = await catalogosApi.confirmarPendiente(id)
      toast.success(`Created: ${res.nuevo_id}`)
      cargar()
      onReload()
    } catch (e) {
      toast.error(e.response?.data?.detail ?? e.message)
    } finally {
      setWorking(null)
    }
  }

  async function handleDescartar(id) {
    setWorking(id)
    try {
      await catalogosApi.descartarPendiente(id)
      toast.success('Discarded')
      cargar()
    } catch (e) {
      toast.error(e.response?.data?.detail ?? e.message)
    } finally {
      setWorking(null)
    }
  }

  if (loading) return (
    <div className="flex items-center justify-center py-20 text-gray-400 text-sm gap-2">
      <span className="animate-spin">⏳</span> Loading...
    </div>
  )

  if (items.length === 0) return (
    <div className="flex flex-col items-center justify-center py-20 text-gray-400 gap-2">
      <p className="text-sm font-medium text-gray-600">No pending proposals</p>
      <p className="text-xs">The ETL will add entries here when it finds unknown catalog values.</p>
    </div>
  )

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 mb-1">
        <p className="text-xs text-gray-500 flex-shrink-0">{items.length} pending proposal{items.length !== 1 ? 's' : ''}</p>
        <div className="w-px h-5 bg-gray-200" />
        {/* Placeholder sin funcionalidad todavia -- no hay estructura de busqueda
            para propuestas pendientes (ver pedido del usuario). */}
        <input
          type="text"
          placeholder="Search pending..."
          disabled
          title="Not available yet"
          className="flex-1 min-w-36 max-w-xs px-3 py-1.5 text-xs border border-gray-200 rounded bg-gray-50 text-gray-400 cursor-not-allowed"
        />
        <div className="flex-1" />
        <button onClick={cargar} className="px-3 py-1.5 text-xs text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50 flex-shrink-0">
          ↻ Refresh
        </button>
      </div>
      {items.map(ep => (
        <div key={ep.id} className="bg-white border border-gray-200 rounded-xl px-4 py-3 flex items-center gap-4">
          <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-semibold flex-shrink-0 ${TIPO_BADGE[ep.tipo] ?? 'bg-gray-100 text-gray-600'}`}>
            {TIPO_LABEL[ep.tipo] ?? ep.tipo}
          </span>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">{ep.valor_propuesto}</p>
            <p className="text-xs text-gray-400 truncate mt-0.5">
              {ep.trx_fecha ? ep.trx_fecha.slice(0, 10) : ''}{ep.trx_descripcion ? ` · ${ep.trx_descripcion}` : ''}
            </p>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <button
              onClick={() => handleConfirmar(ep.id)}
              disabled={working === ep.id}
              className="px-3 py-1.5 text-xs font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
            >
              {working === ep.id ? '...' : 'Confirm'}
            </button>
            <button
              onClick={() => handleDescartar(ep.id)}
              disabled={working === ep.id}
              className="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
            >
              Discard
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}

// ── Componente ────────────────────────────────────────────────────────────────

export default function Catalogos() {
  const [seccion,   setSeccion]   = useState('categorias')
  const [items,     setItems]     = useState([])
  const [loading,   setLoading]   = useState(false)
  const [busqueda,  setBusqueda]  = useState('')
  const [modal,     setModal]     = useState(null)
  const [formVals,  setFormVals]  = useState({})
  const [guardando, setGuardando] = useState(false)
  const [monedasActivas, setMonedasActivas] = useState([])
  // 'total' | 'activas' | 'inactivas' -- filtro por estado, clickeable desde
  // las 3 etiquetas del toolbar. Categorias arranca en 'activas' (no tiene
  // sentido presupuestar/editar algo dado de baja); el resto arranca
  // mostrando todo, igual que antes.
  const [filtroEstado, setFiltroEstado] = useState('activas')
  const [ordenAsc, setOrdenAsc] = useState(true)

  const { undo, redo, undoStack, redoStack } = useAppStore()
  const { ejecutar } = useUndo()

  // Se recarga junto con la seccion activa (cambio de tab, guardar, inactivar)
  // en vez de una sola vez al montar -- si no, queda obsoleta apenas alguien
  // activa/inactiva una moneda y el dropdown de Currency en Cuentas sigue
  // mostrando datos viejos.
  const cargar = useCallback(async () => {
    if (seccion === 'pendientes') return
    setLoading(true)
    try {
      const [data, monedasData] = await Promise.all([
        API[seccion].listar({ solo_activas: false }),
        catalogosApi.getMonedas({ solo_activas: true }),
      ])
      setItems(Array.isArray(data) ? data : data.items ?? [])
      setMonedasActivas(monedasData.items ?? [])
    } catch (e) {
      toast.error('Error loading: ' + (e.response?.data?.detail ?? e.message))
    } finally {
      setLoading(false)
    }
  }, [seccion])

  useEffect(() => {
    cargar()
    setBusqueda('')
    setFiltroEstado(seccion === 'categorias' ? 'activas' : 'total')
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seccion])

  const itemsFiltrados = items
    .filter(item => {
      const q = busqueda.toLowerCase()
      return !q || Object.values(item).some(v => String(v ?? '').toLowerCase().includes(q))
    })
    .filter(item => {
      if (filtroEstado === 'activas') return item.activa !== false
      if (filtroEstado === 'inactivas') return item.activa === false
      return true
    })
    .sort((a, b) => ordenAsc
      ? String(a.nombre ?? '').localeCompare(String(b.nombre ?? ''))
      : String(b.nombre ?? '').localeCompare(String(a.nombre ?? '')))

  const total    = items.length
  const activos  = items.filter(i => i.activa !== false).length
  const inactivos = total - activos

  function abrirCrear() {
    setFormVals({ tipo_patron_gasto: 'variable_frecuente', moneda: 'COP', tipo: 'COMERCIO', propietario: 'Ambos', visible_pwa: true })
    setModal({ tipo: 'form', item: null })
  }

  function abrirEditar(item) {
    // Monedas: el campo visible del formulario es "codigo", no "id".
    setFormVals(seccion === 'monedas' ? { ...item, codigo: item.id } : { ...item })
    setModal({ tipo: 'form', item })
  }

  function abrirConfirmar(item) {
    setModal({ tipo: 'confirm', item })
  }

  async function handleGuardar() {
    setGuardando(true)
    try {
      if (modal.item) {
        if (seccion === 'categorias') {
          // Snapshot para poder volver atras -- el PATCH real ya viaja con
          // formVals (los valores nuevos) via la accion.
          const anterior = {
            nombre: modal.item.nombre,
            id_padre: modal.item.id_padre,
            tipo_patron_gasto: modal.item.tipo_patron_gasto,
          }
          await ejecutar({
            descripcion: `Editar categoria "${modal.item.nombre}"`,
            accion: () => catalogosApi.editarCategoria(modal.item.id, formVals),
            deshacer: () => catalogosApi.editarCategoria(modal.item.id, anterior),
          })
        } else {
          await API[seccion].editar(modal.item.id, formVals)
        }
        toast.success('Updated successfully')
      } else if (seccion === 'monedas') {
        // El codigo lo escribe el usuario -- no se autogenera como slug.
        await API[seccion].crear(formVals)
        toast.success('Created successfully')
      } else {
        // Autogenerar ID como slug del nombre
        const existingIds = items.map(i => i.id)
        const autoId = generarSlugUnico(formVals.nombre || 'ITEM', existingIds)
        // Categorias: el nivel se deriva del padre elegido, no es un campo visible.
        const derivados = seccion === 'categorias'
          ? { nivel: (items.find(i => i.id === formVals.id_padre)?.nivel ?? 0) + 1 }
          : {}
        const payload = { ...formVals, id: autoId, ...derivados }
        if (seccion === 'categorias') {
          // Deshacer una creacion no puede volver a hacer POST (el id ya
          // existe) -- el equivalente es inactivarla; rehacer la reactiva
          // con el mismo toggle (DELETE /categorias/{id} alterna activa).
          await ejecutar({
            descripcion: `Crear categoria "${formVals.nombre}"`,
            accion: () => catalogosApi.crearCategoria(payload),
            deshacer: () => catalogosApi.inactivarCategoria(autoId),
            rehacer: () => catalogosApi.inactivarCategoria(autoId),
          })
        } else {
          await API[seccion].crear(payload)
        }
        toast.success('Created successfully')
      }
      setModal(null)
      cargar()
    } catch (e) {
      toast.error(e.response?.data?.detail ?? e.message)
    } finally {
      setGuardando(false)
    }
  }

  async function handleInactivar() {
    setGuardando(true)
    try {
      if (seccion === 'categorias') {
        // inactivarCategoria alterna activa -- el mismo toggle sirve de
        // deshacer (y de rehacer, por defecto, via useUndo).
        await ejecutar({
          descripcion: modal.item.activa !== false
            ? `Inactivar categoria "${modal.item.nombre}"`
            : `Activar categoria "${modal.item.nombre}"`,
          accion: () => catalogosApi.inactivarCategoria(modal.item.id),
          deshacer: () => catalogosApi.inactivarCategoria(modal.item.id),
        })
      } else {
        await API[seccion].inactivar(modal.item.id)
      }
      toast.success(modal.item.activa !== false ? 'Deactivated' : 'Activated')
      setModal(null)
      cargar()
    } catch (e) {
      toast.error(e.response?.data?.detail ?? e.message)
    } finally {
      setGuardando(false)
    }
  }

  const meta = SECCIONES.find(s => s.id === seccion)

  return (
    <div className="space-y-6">

      {/* Encabezado */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">{meta?.icon} {meta?.label}</h1>
          <p className="text-sm text-gray-500 mt-0.5">Master data management</p>
        </div>
        {seccion !== 'pendientes' && (
          <button
            onClick={abrirCrear}
            className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
          >
            Add New
          </button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200">
        {SECCIONES.map(s => (
          <button
            key={s.id}
            onClick={() => setSeccion(s.id)}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px ${
              seccion === s.id
                ? 'border-primary-600 text-primary-700'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            {s.icon} {s.label}
          </button>
        ))}
      </div>

      {/* Toolbar -- mismo formato que Transacciones (sort, search, estado, undo/redo/reload).
          Sin rango de fechas ni filtros de Source/People: no aplican a un catalogo.
          Oculto en Pending, que no tiene ni estados ni orden todavia. */}
      {seccion !== 'pendientes' && (
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => setOrdenAsc(a => !a)}
            title={ordenAsc ? 'Sorted A-Z -- click for Z-A' : 'Sorted Z-A -- click for A-Z'}
            className="flex items-center gap-1 text-xs border border-gray-200 rounded px-2.5 py-1.5 text-gray-600 hover:bg-gray-50"
          >
            <span>{ordenAsc ? '↑' : '↓'}</span> Name
          </button>

          <div className="w-px h-5 bg-gray-200" />

          <div className="relative flex-1 min-w-36 max-w-xs">
            <input
              type="text"
              placeholder={`Search ${(meta?.label ?? '').toLowerCase()}...`}
              value={busqueda}
              onChange={e => setBusqueda(e.target.value)}
              className="w-full px-3 py-1.5 text-xs border border-gray-200 rounded focus:outline-none focus:border-primary-400"
            />
          </div>

          <div className="w-px h-5 bg-gray-200" />

          <div className="flex items-center gap-1.5">
            {[
              { key: 'total',     label: 'Total',    value: total,     color: 'text-gray-900' },
              { key: 'activas',   label: 'Active',   value: activos,   color: 'text-success-500' },
              { key: 'inactivas', label: 'Inactive', value: inactivos, color: 'text-gray-400' },
            ].map(s => (
              <button
                key={s.key}
                onClick={() => setFiltroEstado(s.key)}
                className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-xs transition-colors ${
                  filtroEstado === s.key ? 'bg-primary-50 border-primary-300' : 'bg-white border-gray-200 hover:bg-gray-50'
                }`}
              >
                <span className="font-semibold text-gray-400 uppercase tracking-wider text-[10px]">{s.label}</span>
                <span className={`font-bold ${s.color}`}>{s.value}</span>
              </button>
            ))}
          </div>

          <div className="w-px h-5 bg-gray-200" />

          <div className="flex items-center gap-1">
            <button onClick={undo} disabled={!undoStack.length} title="Undo (Ctrl+Z)"
              className="p-1.5 rounded hover:bg-gray-100 disabled:opacity-25 text-gray-400 text-sm">↩</button>
            <button onClick={redo} disabled={!redoStack.length} title="Redo (Ctrl+Y)"
              className="p-1.5 rounded hover:bg-gray-100 disabled:opacity-25 text-gray-400 text-sm">↪</button>
            <button onClick={cargar} title="Refresh"
              className="p-1.5 rounded hover:bg-gray-100 text-gray-400 text-sm">↻</button>
          </div>
        </div>
      )}

      {/* Contenido */}
      {seccion === 'pendientes' ? (
        <PendingList onReload={cargar} />
      ) : loading ? (
        <div className="flex items-center justify-center py-20 text-gray-400 text-sm gap-2">
          <span className="animate-spin">⏳</span> Loading...
        </div>
      ) : seccion === 'categorias' ? (
        <CategoriaTree
          items={buildTree(itemsFiltrados, ordenAsc)}
          onEditar={abrirEditar}
          onInactivar={abrirConfirmar}
        />
      ) : (
        <TablaGenerica columnas={COLUMNAS[seccion] ?? []} items={itemsFiltrados} onEditar={abrirEditar} onInactivar={abrirConfirmar} />
      )}

      {/* Modal form */}
      {modal?.tipo === 'form' && (
        <ModalForm
          titulo={`${modal.item ? 'Edit' : 'New'} ${SINGULAR[seccion]}`}
          campos={CAMPOS[seccion] ?? []}
          values={formVals}
          onChange={(k, v) => setFormVals(prev => ({ ...prev, [k]: v }))}
          isEdit={!!modal.item}
          onClose={() => setModal(null)}
          onGuardar={handleGuardar}
          guardando={guardando}
          extra={{ items, monedasActivas }}
          onInactivar={seccion === 'categorias' ? () => setModal({ tipo: 'confirm', item: modal.item }) : undefined}
        />
      )}

      {/* Modal confirmacion */}
      {modal?.tipo === 'confirm' && (
        <ModalConfirm item={modal.item} onClose={() => setModal(null)} onConfirmar={handleInactivar} guardando={guardando} />
      )}
    </div>
  )
}
