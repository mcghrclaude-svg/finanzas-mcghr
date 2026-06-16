/**
 * modules/Catalogos/index.jsx
 *
 * Gestion de datos maestros: categorias, cuentas, contrapartes, personas.
 * Stack: Tailwind CSS + react-hot-toast (igual que el resto del repo).
 * Ruta: /catalogos/* (declarada en App.jsx)
 */
import { useState, useEffect, useCallback } from 'react'
import toast from 'react-hot-toast'
import { catalogosApi } from '@/api/catalogos'
import CategoriaTree from './CategoriaTree'
import TablaGenerica from './TablaGenerica'
import ModalForm from './ModalForm'
import ModalConfirm from './ModalConfirm'

// ── Configuracion de secciones ────────────────────────────────────────────────
const SECCIONES = [
  { id: 'categorias',   label: 'Categorias',   icon: '🏷️' },
  { id: 'cuentas',      label: 'Cuentas',      icon: '🏦' },
  { id: 'contrapartes', label: 'Contrapartes', icon: '🏢' },
  { id: 'personas',     label: 'Personas',     icon: '👤' },
]

const COLUMNAS = {
  cuentas: [
    { key: 'id',     label: 'ID' },
    { key: 'nombre', label: 'Nombre' },
    { key: 'tipo',   label: 'Tipo' },
    { key: 'banco',  label: 'Banco' },
    { key: 'moneda', label: 'Moneda' },
    { key: 'activa', label: 'Estado', render: v => v
        ? <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">Activa</span>
        : <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-500">Inactiva</span>
    },
  ],
  contrapartes: [
    { key: 'id',     label: 'ID' },
    { key: 'nombre', label: 'Nombre' },
    { key: 'tipo',   label: 'Tipo' },
    { key: 'activa', label: 'Estado', render: v => v
        ? <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">Activa</span>
        : <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-500">Inactiva</span>
    },
  ],
  personas: [
    { key: 'id',     label: 'ID' },
    { key: 'nombre', label: 'Nombre' },
    { key: 'alias',  label: 'Alias' },
    { key: 'activa', label: 'Estado', render: v => v
        ? <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">Activa</span>
        : <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-500">Inactiva</span>
    },
  ],
}

// ── Campos de formulario por seccion ─────────────────────────────────────────
const CAMPOS = {
  categorias: [
    { key: 'id',               label: 'ID',               type: 'text',   required: true, hint: 'Ej: VIDA-REST. Mayusculas, sin espacios', disabled_on_edit: true },
    { key: 'nombre',           label: 'Nombre',           type: 'text',   required: true },
    { key: 'nivel',            label: 'Nivel',            type: 'select', required: true,
      options: [{ value: 1, label: 'Nivel 1 (raiz)' }, { value: 2, label: 'Nivel 2' }, { value: 3, label: 'Nivel 3' }],
      disabled_on_edit: true },
    { key: 'id_padre',         label: 'Categoria padre',  type: 'text',   hint: 'ID de la categoria padre (opcional)', disabled_on_edit: true },
    { key: 'tipo_patron_gasto',label: 'Patron de gasto',  type: 'select', required: true,
      options: [
        { value: 'fijo_unico',           label: 'Fijo unico (arriendo, cuota)' },
        { value: 'fijo_recurrente',      label: 'Fijo recurrente (suscripciones)' },
        { value: 'variable_frecuente',   label: 'Variable frecuente (mercado, Rappi)' },
        { value: 'variable_esporadico',  label: 'Variable esporadico (salud, viajes)' },
      ]
    },
  ],
  cuentas: [
    { key: 'id',     label: 'ID',     type: 'text',   required: true, hint: 'Ej: BCO-CC-GHR', disabled_on_edit: true },
    { key: 'nombre', label: 'Nombre', type: 'text',   required: true },
    { key: 'tipo',   label: 'Tipo',   type: 'select',
      options: [
        { value: 'CC',        label: 'Cuenta corriente' },
        { value: 'TC',        label: 'Tarjeta credito' },
        { value: 'AHORRO',    label: 'Ahorro' },
        { value: 'INVERSION', label: 'Inversion' },
        { value: 'EFECTIVO',  label: 'Efectivo' },
        { value: 'OTRO',      label: 'Otro' },
      ]
    },
    { key: 'banco',  label: 'Banco',  type: 'text' },
    { key: 'moneda', label: 'Moneda', type: 'select',
      options: [
        { value: 'COP', label: 'COP - Peso colombiano' },
        { value: 'USD', label: 'USD - Dolar' },
        { value: 'ARS', label: 'ARS - Peso argentino' },
        { value: 'EUR', label: 'EUR - Euro' },
      ]
    },
  ],
  contrapartes: [
    { key: 'id',     label: 'ID',     type: 'text',   required: true, hint: 'Ej: RAPPI, NETFLIX', disabled_on_edit: true },
    { key: 'nombre', label: 'Nombre', type: 'text',   required: true },
    { key: 'tipo',   label: 'Tipo',   type: 'select',
      options: [
        { value: 'COMERCIO', label: 'Comercio' },
        { value: 'BANCO',    label: 'Banco' },
        { value: 'PERSONA',  label: 'Persona' },
        { value: 'ENTIDAD',  label: 'Entidad' },
      ]
    },
  ],
  personas: [
    { key: 'id',     label: 'ID',    type: 'text', required: true, hint: 'Ej: GHR, MC', disabled_on_edit: true },
    { key: 'nombre', label: 'Nombre',type: 'text', required: true },
    { key: 'alias',  label: 'Alias', type: 'text', hint: 'Apodo o iniciales' },
  ],
}

// ── API por seccion ───────────────────────────────────────────────────────────
const API = {
  categorias:   { listar: (p) => catalogosApi.getCategorias(p),   crear: catalogosApi.crearCategoria,   editar: catalogosApi.editarCategoria,   inactivar: catalogosApi.inactivarCategoria   },
  cuentas:      { listar: (p) => catalogosApi.getCuentas(p),      crear: catalogosApi.crearCuenta,      editar: catalogosApi.editarCuenta,      inactivar: catalogosApi.inactivarCuenta      },
  contrapartes: { listar: (p) => catalogosApi.getContrapartes(p), crear: catalogosApi.crearContraparte, editar: catalogosApi.editarContraparte, inactivar: catalogosApi.inactivarContraparte },
  personas:     { listar: (p) => catalogosApi.getPersonas(p),     crear: catalogosApi.crearPersona,     editar: catalogosApi.editarPersona,     inactivar: catalogosApi.inactivarPersona     },
}

// ── Componente principal ──────────────────────────────────────────────────────
export default function Catalogos() {
  const [seccion,   setSeccion]   = useState('categorias')
  const [items,     setItems]     = useState([])
  const [loading,   setLoading]   = useState(false)
  const [busqueda,  setBusqueda]  = useState('')
  const [modal,     setModal]     = useState(null)  // null | { tipo: 'form'|'confirm', item? }
  const [formVals,  setFormVals]  = useState({})
  const [guardando, setGuardando] = useState(false)

  const cargar = useCallback(async () => {
    setLoading(true)
    try {
      const data = await API[seccion].listar({ solo_activas: false })
      setItems(Array.isArray(data) ? data : data.items ?? [])
    } catch (e) {
      toast.error('Error al cargar: ' + (e.response?.data?.detail ?? e.message))
    } finally {
      setLoading(false)
    }
  }, [seccion])

  useEffect(() => { cargar(); setBusqueda('') }, [cargar])

  // Filtrado por busqueda
  const itemsFiltrados = items.filter(item => {
    const q = busqueda.toLowerCase()
    return !q || Object.values(item).some(v => String(v ?? '').toLowerCase().includes(q))
  })

  // Totales
  const total    = items.length
  const activos  = items.filter(i => i.activa !== false).length
  const inactivos = total - activos

  // ── Handlers ──────────────────────────────────────────────────────────────
  function abrirCrear() {
    setFormVals({ nivel: 1, tipo_patron_gasto: 'variable_frecuente', moneda: 'COP' })
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
        toast.success('Actualizado correctamente')
      } else {
        await API[seccion].crear(formVals)
        toast.success('Creado correctamente')
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
      toast.success(modal.item.activa ? 'Inactivado' : 'Activado')
      setModal(null)
      cargar()
    } catch (e) {
      toast.error(e.response?.data?.detail ?? e.message)
    } finally {
      setGuardando(false)
    }
  }

  const metaSeccion = SECCIONES.find(s => s.id === seccion)

  return (
    <div className="flex h-full">

      {/* Nav lateral */}
      <aside className="w-48 flex-shrink-0 border-r border-gray-200 bg-white py-4">
        <p className="px-4 mb-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
          Catalogos
        </p>
        {SECCIONES.map(s => (
          <button
            key={s.id}
            onClick={() => setSeccion(s.id)}
            className={`w-full flex items-center gap-2 px-4 py-2.5 text-sm transition-colors text-left ${
              seccion === s.id
                ? 'bg-primary-50 text-primary-700 font-medium'
                : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            <span>{s.icon}</span>
            {s.label}
          </button>
        ))}
      </aside>

      {/* Contenido */}
      <div className="flex-1 flex flex-col overflow-hidden">

        {/* Topbar */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-white flex-shrink-0">
          <div>
            <h1 className="text-lg font-semibold text-gray-900">
              {metaSeccion?.icon} {metaSeccion?.label}
            </h1>
          </div>
          <button
            onClick={abrirCrear}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors"
          >
            + Nuevo
          </button>
        </div>

        {/* Stats */}
        <div className="flex gap-4 px-6 py-3 border-b border-gray-100 bg-gray-50 flex-shrink-0">
          {[
            { label: 'Total',     value: total,    color: 'text-gray-900' },
            { label: 'Activos',   value: activos,  color: 'text-green-600' },
            { label: 'Inactivos', value: inactivos,color: 'text-gray-400' },
          ].map(s => (
            <div key={s.label} className="flex items-center gap-2">
              <span className={`text-xl font-bold ${s.color}`}>{s.value}</span>
              <span className="text-xs text-gray-500">{s.label}</span>
            </div>
          ))}
        </div>

        {/* Busqueda */}
        {seccion !== 'categorias' && (
          <div className="px-6 py-3 border-b border-gray-100 flex-shrink-0">
            <input
              type="text"
              placeholder="Buscar..."
              value={busqueda}
              onChange={e => setBusqueda(e.target.value)}
              className="w-72 px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-primary-400"
            />
          </div>
        )}

        {/* Tabla o arbol */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center py-20 text-gray-400 text-sm">
              Cargando...
            </div>
          ) : seccion === 'categorias' ? (
            <CategoriaTree
              items={itemsFiltrados}
              onEditar={abrirEditar}
              onInactivar={abrirConfirmar}
            />
          ) : (
            <TablaGenerica
              columnas={COLUMNAS[seccion] ?? []}
              items={itemsFiltrados}
              onEditar={abrirEditar}
              onInactivar={abrirConfirmar}
            />
          )}
        </div>
      </div>

      {/* Modal form */}
      {modal?.tipo === 'form' && (
        <ModalForm
          titulo={modal.item ? `Editar ${metaSeccion?.label?.slice(0,-1)}` : `Nuevo en ${metaSeccion?.label}`}
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
        <ModalConfirm
          item={modal.item}
          onClose={() => setModal(null)}
          onConfirmar={handleInactivar}
          guardando={guardando}
        />
      )}
    </div>
  )
}
