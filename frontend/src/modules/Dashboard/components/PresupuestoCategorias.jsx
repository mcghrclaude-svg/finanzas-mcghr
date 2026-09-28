/**
 * PresupuestoCategorias — widget "Presupuesto por categoría" del Home.
 * Etiquetas al estilo PWA (ver CategoriaBullet) ordenadas por nivel de
 * riesgo (igual que ya devuelve /presupuestos/ejecucion), con drill-down a
 * subcategorías: al hacer click en una categoría con hijos, este widget --
 * y solo este widget -- muestra sus subcategorías, con "← Atrás" para volver.
 */
import { useState } from 'react'
import CategoriaBullet from './CategoriaBullet'

export default function PresupuestoCategorias({ ejecucion, categoriasConHijos, cargarSubcategorias }) {
  const [pila, setPila] = useState([]) // [{id, nombre}] -- ultimo = nivel actual
  const [items, setItems] = useState(null) // null = usar ejecucion.items (nivel top)
  const [cargando, setCargando] = useState(false)

  const nivelActual = pila.length > 0 ? pila[pila.length - 1] : null
  const itemsMostrados = nivelActual ? (items ?? []) : (ejecucion?.items ?? [])

  async function drill(item) {
    setCargando(true)
    try {
      const hijos = await cargarSubcategorias(item.id_categoria)
      setPila(p => [...p, { id: item.id_categoria, nombre: item.nombre }])
      setItems(hijos)
    } finally {
      setCargando(false)
    }
  }

  async function volver() {
    const nuevaPila = pila.slice(0, -1)
    if (nuevaPila.length === 0) {
      setPila([])
      setItems(null)
      return
    }
    setCargando(true)
    try {
      const padre = nuevaPila[nuevaPila.length - 1]
      const hijos = await cargarSubcategorias(padre.id)
      setPila(nuevaPila)
      setItems(hijos)
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="card bg-white border border-gray-200 rounded-xl p-4">
      <div className="flex items-center justify-between mb-3 min-h-[20px]">
        {nivelActual ? (
          <div className="flex items-center gap-2 text-sm">
            <button onClick={volver} className="text-primary-600 hover:text-primary-700 font-medium">
              ← Atrás
            </button>
            <span className="text-gray-700 font-medium">{nivelActual.nombre}</span>
          </div>
        ) : (
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Presupuesto por categoría
          </h2>
        )}
      </div>

      {cargando ? (
        <div className="py-8 text-center text-xs text-gray-400">Cargando...</div>
      ) : itemsMostrados.length === 0 ? (
        <div className="py-8 text-center text-xs text-gray-400 italic">
          Sin subcategorías para mostrar.
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-x-6 gap-y-3">
          {itemsMostrados.map(item => (
            <CategoriaBullet
              key={item.id_categoria}
              item={item}
              tieneHijos={categoriasConHijos.has(item.id_categoria)}
              onDrill={() => drill(item)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
