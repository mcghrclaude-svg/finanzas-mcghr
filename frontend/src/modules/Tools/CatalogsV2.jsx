/**
 * modules/Tools/CatalogsV2.jsx -- pagina de editor de categorias en arbol (estilo regedt32).
 * Ruteada aparte, item propio de Settings (junto a Catalogs, Backup, Tools). Solo dev.
 * Reusa ModalForm y la config de categorias del modulo Catalogos.
 */
import { useState, useEffect, useMemo } from 'react'
import toast from 'react-hot-toast'
import { catalogosApi } from '@/api/catalogos'
import ModalForm from '../Catalogos/ModalForm'
import { generarSlugUnico, CAMPOS_CATEGORIAS } from '../Catalogos/categoriaConfig'

function buildTree(items) {
  const byId = new Map(items.map(i => [i.id, { ...i, hijos: [] }]))
  const roots = []
  for (const item of byId.values()) {
    if (item.id_padre && byId.has(item.id_padre)) {
      byId.get(item.id_padre).hijos.push(item)
    } else {
      roots.push(item)
    }
  }
  const porNombre = (a, b) => a.nombre.localeCompare(b.nombre)
  for (const item of byId.values()) item.hijos.sort(porNombre)
  roots.sort(porNombre)
  return roots
}

function TreeNode({ node, depth, selectedId, expanded, onSelect, onToggle, onAddChild, onDelete }) {
  const hasKids = node.hijos.length > 0
  const isOpen = expanded[node.id] === true
  const isSelected = selectedId === node.id
  const hijosActivos = node.hijos.filter(h => h.activa !== false).length
  const puedeAgregarHija = node.nivel < 3
  const puedeInactivar = node.activa === false || hijosActivos === 0

  return (
    <div>
      <div
        onClick={() => onSelect(node)}
        className={`flex items-center gap-1 pr-1 py-1 rounded cursor-pointer group text-sm ${
          isSelected ? 'bg-primary-100 text-primary-800' : 'hover:bg-gray-100 text-gray-700'
        }`}
        style={{ paddingLeft: `${depth * 16 + 4}px` }}
      >
        {hasKids ? (
          <button
            onClick={e => { e.stopPropagation(); onToggle(node.id) }}
            className="w-4 h-4 flex items-center justify-center text-xs text-gray-400 flex-shrink-0"
          >
            {isOpen ? '▾' : '▸'}
          </button>
        ) : (
          <span className="w-4 flex-shrink-0" />
        )}
        <span className={`truncate ${node.activa === false ? 'line-through text-gray-400' : ''}`}>
          {node.nombre}
        </span>
        <span className="flex-1" />
        <div className="flex gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
          <button
            onClick={e => { e.stopPropagation(); onAddChild(node) }}
            disabled={!puedeAgregarHija}
            title={puedeAgregarHija ? 'Agregar categoria hija' : 'Nivel maximo alcanzado'}
            className="p-0.5 rounded text-gray-400 hover:text-primary-600 hover:bg-primary-50 disabled:opacity-30 disabled:hover:bg-transparent disabled:hover:text-gray-400 text-xs"
          >➕</button>
          <button
            onClick={e => { e.stopPropagation(); onDelete(node) }}
            disabled={!puedeInactivar}
            title={puedeInactivar ? (node.activa !== false ? 'Inactivar categoria' : 'Activar categoria') : 'Tiene categorias hijas activas'}
            className="p-0.5 rounded text-gray-400 hover:text-danger-500 hover:bg-danger-100 disabled:opacity-30 disabled:hover:bg-transparent disabled:hover:text-gray-400 text-xs"
          >🗑</button>
        </div>
      </div>
      {hasKids && isOpen && node.hijos.map(hijo => (
        <TreeNode
          key={hijo.id}
          node={hijo}
          depth={depth + 1}
          selectedId={selectedId}
          expanded={expanded}
          onSelect={onSelect}
          onToggle={onToggle}
          onAddChild={onAddChild}
          onDelete={onDelete}
        />
      ))}
    </div>
  )
}

function DetailPanel({ node, onEditar }) {
  if (!node) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-gray-400 p-4">
        Selecciona una categoria del arbol
      </div>
    )
  }
  return (
    <div className="p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-semibold text-gray-900">{node.nombre}</h3>
        <button
          onClick={() => onEditar(node)}
          className="p-1.5 rounded text-gray-400 hover:text-gray-700 hover:bg-gray-100 text-sm"
          title="Editar"
        >✏️</button>
      </div>
      <dl className="text-sm space-y-2">
        <div className="flex justify-between items-center border-b border-gray-100 pb-1.5">
          <dt className="text-gray-400">ID</dt>
          <dd><code className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded font-mono">{node.id}</code></dd>
        </div>
        <div className="flex justify-between items-center border-b border-gray-100 pb-1.5">
          <dt className="text-gray-400">Nivel</dt>
          <dd className="text-gray-900">{node.nivel}</dd>
        </div>
        <div className="flex justify-between items-center border-b border-gray-100 pb-1.5">
          <dt className="text-gray-400">Categoria padre</dt>
          <dd><code className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded font-mono">{node.id_padre ?? '—'}</code></dd>
        </div>
        <div className="flex justify-between items-center border-b border-gray-100 pb-1.5">
          <dt className="text-gray-400">Patron de gasto</dt>
          <dd className="text-gray-900">{node.tipo_patron_gasto ?? '—'}</dd>
        </div>
        <div className="flex justify-between items-center">
          <dt className="text-gray-400">Estado</dt>
          <dd>
            <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${node.activa !== false ? 'bg-success-100 text-success-500' : 'bg-gray-100 text-gray-400'}`}>
              {node.activa !== false ? 'Activa' : 'Inactiva'}
            </span>
          </dd>
        </div>
      </dl>
    </div>
  )
}

export default function CatalogsV2() {
  const [items,      setItems]      = useState([])
  const [loading,     setLoading]    = useState(false)
  const [expanded,    setExpanded]   = useState({})
  const [selectedId,  setSelectedId] = useState(null)
  const [modal,       setModal]      = useState(null)
  const [formVals,    setFormVals]   = useState({})
  const [guardando,   setGuardando]  = useState(false)

  async function cargar() {
    setLoading(true)
    try {
      const data = await catalogosApi.getCategorias({ solo_activas: false })
      setItems(data.items ?? [])
    } catch (e) {
      toast.error('Error loading categories: ' + (e.response?.data?.detail ?? e.message))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { cargar() }, [])

  const tree = useMemo(() => buildTree(items), [items])
  const selected = items.find(i => i.id === selectedId) ?? null

  function onToggle(id) {
    setExpanded(prev => ({ ...prev, [id]: prev[id] === true ? false : true }))
  }

  function abrirEditar(item) {
    setFormVals({ ...item })
    setModal({ item })
  }

  function abrirAgregarHija(padre) {
    setFormVals({ nivel: padre.nivel + 1, id_padre: padre.id, tipo_patron_gasto: 'variable_frecuente' })
    setModal({ item: null })
  }

  async function handleDelete(node) {
    try {
      await catalogosApi.inactivarCategoria(node.id)
      toast.success(node.activa !== false ? 'Categoria inactivada' : 'Categoria activada')
      if (selectedId === node.id) setSelectedId(null)
      cargar()
    } catch (e) {
      toast.error(e.response?.data?.detail ?? e.message)
    }
  }

  async function handleGuardar() {
    setGuardando(true)
    try {
      if (modal.item) {
        await catalogosApi.editarCategoria(modal.item.id, formVals)
        toast.success('Categoria actualizada')
      } else {
        const existingIds = items.map(i => i.id)
        const autoId = generarSlugUnico(formVals.nombre || 'CATEGORIA', existingIds)
        await catalogosApi.crearCategoria({ ...formVals, id: autoId })
        setSelectedId(autoId)
        toast.success('Categoria creada')
      }
      setModal(null)
      cargar()
    } catch (e) {
      toast.error(e.response?.data?.detail ?? e.message)
    } finally {
      setGuardando(false)
    }
  }

  return (
    <div className="h-full flex flex-col space-y-4">
      <div className="flex-shrink-0">
        <h1 className="text-xl font-semibold text-gray-900">🌳 Catalogs V2</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Editor alternativo de categorias en formato arbol. Solo categorias por ahora.
        </p>
      </div>

      <div className="flex-1 min-h-0 flex border border-gray-200 rounded-xl overflow-hidden">
        <div className="w-64 flex-shrink-0 border-r border-gray-200 bg-gray-50 overflow-y-auto p-2">
          {loading ? (
            <p className="text-xs text-gray-400 p-2">Cargando...</p>
          ) : tree.length === 0 ? (
            <p className="text-xs text-gray-400 p-2">Sin categorias.</p>
          ) : (
            tree.map(root => (
              <TreeNode
                key={root.id}
                node={root}
                depth={0}
                selectedId={selectedId}
                expanded={expanded}
                onSelect={n => setSelectedId(n.id)}
                onToggle={onToggle}
                onAddChild={abrirAgregarHija}
                onDelete={handleDelete}
              />
            ))
          )}
        </div>
        <div className="flex-1 bg-white overflow-y-auto">
          <DetailPanel node={selected} onEditar={abrirEditar} />
        </div>
      </div>

      {modal && (
        <ModalForm
          titulo={modal.item ? 'Edit Category' : 'New Category'}
          campos={CAMPOS_CATEGORIAS}
          values={formVals}
          onChange={(k, v) => setFormVals(prev => ({ ...prev, [k]: v }))}
          isEdit={!!modal.item}
          onClose={() => setModal(null)}
          onGuardar={handleGuardar}
          guardando={guardando}
        />
      )}
    </div>
  )
}
