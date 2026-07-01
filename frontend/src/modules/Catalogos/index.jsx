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
import CategoriaTree from './CategoriaTree'
import TablaGenerica from './TablaGenerica'
import ModalForm from './ModalForm'
import ModalConfirm from './ModalConfirm'

// ── Helpers ───────────────────────────────────────────────────────────────────

function generarSlug(nombre) {
  return nombre
    .toUpperCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')  // quitar tildes
    .replace(/[^A-Z0-9\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-')
    .slice(0, 20)
}

function generarSlugUnico(nombre, existentes = []) {
  const base = generarSlug(nombre)
  if (!existentes.includes(base)) return base
  let i = 2
  while (existentes.includes(`${base}-${i}`)) i++
  return `${base}-${i}`
}

// ── Configuracion ─────────────────────────────────────────────────────────────

const SECCIONES = [
  { id: 'categorias',   label: 'Categories', icon: '🏷️' },
  { id: 'cuentas',      label: 'Accounts',   icon: '🏦' },
  { id: 'contrapartes', label: 'Entities',   icon: '🏢' },
  { id: 'personas',     label: 'People',     icon: '👤' },
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
}

const CAMPOS = {
  categorias: [
    { key: 'nombre',           label: 'Name',          type: 'text',   required: true },
    { key: 'nivel',            label: 'Level',         type: 'select', required: true, lock_on_edit: true,
      options: [{ value: 1, label: 'Level 1 (root)' }, { value: 2, label: 'Level 2' }, { value: 3, label: 'Level 3' }] },
    { key: 'id_padre',         label: 'Parent category', type: 'text', hint: 'ID of parent (leave empty for level 1)', lock_on_edit: true },
    { key: 'tipo_patron_gasto',label: 'Spending pattern', type: 'select', required: true,
      options: [
        { value: 'fijo_unico',          label: 'Fixed one-time (rent, loan payment)' },
        { value: 'fijo_recurrente',     label: 'Fixed recurring (subscriptions)' },
        { value: 'variable_frecuente',  label: 'Variable frequent (groceries, delivery)' },
        { value: 'variable_esporadico', label: 'Variable sporadic (health, travel)' },
      ]
    },
  ],
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
    { key: 'moneda', label: 'Currency', type: 'select',
      options: [
        { value: 'COP', label: 'COP — Colombian Peso' },
        { value: 'USD', label: 'USD — US Dollar' },
        { value: 'ARS', label: 'ARS — Argentine Peso' },
        { value: 'EUR', label: 'EUR — Euro' },
      ]
    },
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
}

const API = {
  categorias:   { listar: (p) => catalogosApi.getCategorias(p),   crear: catalogosApi.crearCategoria,   editar: catalogosApi.editarCategoria,   inactivar: catalogosApi.inactivarCategoria   },
  cuentas:      { listar: (p) => catalogosApi.getCuentas(p),      crear: catalogosApi.crearCuenta,      editar: catalogosApi.editarCuenta,      inactivar: catalogosApi.inactivarCuenta      },
  contrapartes: { listar: (p) => catalogosApi.getContrapartes(p), crear: catalogosApi.crearContraparte, editar: catalogosApi.editarContraparte, inactivar: catalogosApi.inactivarContraparte },
  personas:     { listar: (p) => catalogosApi.getPersonas(p),     crear: catalogosApi.crearPersona,     editar: catalogosApi.editarPersona,     inactivar: catalogosApi.inactivarPersona     },
}

const SINGULAR = {
  categorias: 'Category', cuentas: 'Account',
  contrapartes: 'Entity', personas: 'Person',
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
      <div className="flex items-center justify-between mb-1">
        <p className="text-xs text-gray-500">{items.length} pending proposal{items.length !== 1 ? 's' : ''}</p>
        <button onClick={cargar} className="px-3 py-1.5 text-xs text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50">
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

  const cargar = useCallback(async () => {
    if (seccion === 'pendientes') return
    setLoading(true)
    try {
      const data = await API[seccion].listar({ solo_activas: false })
      setItems(Array.isArray(data) ? data : data.items ?? [])
    } catch (e) {
      toast.error('Error loading: ' + (e.response?.data?.detail ?? e.message))
    } finally {
      setLoading(false)
    }
  }, [seccion])

  useEffect(() => { cargar(); setBusqueda('') }, [cargar])

  const itemsFiltrados = items.filter(item => {
    const q = busqueda.toLowerCase()
    return !q || Object.values(item).some(v => String(v ?? '').toLowerCase().includes(q))
  })

  const total    = items.length
  const activos  = items.filter(i => i.activa !== false).length
  const inactivos = total - activos

  function abrirCrear() {
    setFormVals({ nivel: 1, tipo_patron_gasto: 'variable_frecuente', moneda: 'COP', tipo: 'COMERCIO' })
    setModal({ tipo: 'form', item: null })
  }

  function abrirEditar(item) {
    setFormVals({ ...item })
    setModal({ tipo: 'form', item })
  }

  function abrirConfirmar(item) {
    setModal({ tipo: 'confirm', item })
  }

  async function handleGuardar() {
    setGuardando(true)
    try {
      if (modal.item) {
        await API[seccion].editar(modal.item.id, formVals)
        toast.success('Updated successfully')
      } else {
        // Autogenerar ID como slug del nombre
        const existingIds = items.map(i => i.id)
        const autoId = generarSlugUnico(formVals.nombre || 'ITEM', existingIds)
        await API[seccion].crear({ ...formVals, id: autoId })
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
      await API[seccion].inactivar(modal.item.id)
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
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors"
          >
            + New
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

      {/* Stats -- oculto en pestana Pending */}
      {seccion !== 'pendientes' && (
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: 'Total',    value: total,    color: 'text-gray-900' },
            { label: 'Active',   value: activos,  color: 'text-success-500' },
            { label: 'Inactive', value: inactivos,color: 'text-gray-400' },
          ].map(s => (
            <div key={s.label} className="bg-white border border-gray-200 rounded-xl p-4">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">{s.label}</p>
              <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Busqueda -- oculto en categorias y pending */}
      {seccion !== 'categorias' && seccion !== 'pendientes' && (
        <div className="flex items-center gap-3">
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">🔍</span>
            <input
              type="text"
              placeholder="Search..."
              value={busqueda}
              onChange={e => setBusqueda(e.target.value)}
              className="pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-primary-400 bg-white w-64"
            />
          </div>
          <button onClick={cargar} className="px-3 py-2 text-sm text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50">
            ↻
          </button>
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
        <CategoriaTree items={itemsFiltrados} onEditar={abrirEditar} onInactivar={abrirConfirmar} />
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
        />
      )}

      {/* Modal confirmacion */}
      {modal?.tipo === 'confirm' && (
        <ModalConfirm item={modal.item} onClose={() => setModal(null)} onConfirmar={handleInactivar} guardando={guardando} />
      )}
    </div>
  )
}
