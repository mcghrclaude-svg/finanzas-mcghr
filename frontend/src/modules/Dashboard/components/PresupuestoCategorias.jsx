/**
 * PresupuestoCategorias — widget "Presupuesto por categoría" del Home.
 * Etiquetas al estilo PWA (ver CategoriaBullet), con drill-down local a
 * subcategorías (sin ida y vuelta al backend, la lista ya trae todos los
 * niveles): al hacer click en una categoría con hijos, este widget -- y
 * solo este widget -- muestra sus subcategorías, con "← Atrás" para volver.
 *
 * Fuente: /presupuestos/resumen-por-categoria (mes calendario), la misma
 * que usa "Gasto por categoría" -- navegación independiente entre los dos
 * widgets, pero mismos datos y mismo mes.
 */
import { useState, useMemo } from 'react'
import CategoriaBullet from './CategoriaBullet'

export default function PresupuestoCategorias({ resumenCategorias, categoriasConHijos }) {
  const [pila, setPila] = useState([]) // [{id, nombre}] -- ultimo = nivel actual
  const nivelActual = pila.length > 0 ? pila[pila.length - 1] : null

  const items = useMemo(() => {
    const lista = resumenCategorias ?? []
    return nivelActual
      ? lista.filter(c => c.id_padre === nivelActual.id)
      : lista.filter(c => c.nivel === 1)
  }, [resumenCategorias, nivelActual])

  function drill(item) {
    if (!categoriasConHijos.has(item.id_categoria)) return
    setPila(p => [...p, { id: item.id_categoria, nombre: item.nombre }])
  }

  function volver() {
    setPila(p => p.slice(0, -1))
  }

  return (
    <div className="card bg-white border border-gray-200 rounded-xl p-3">
      <div className="flex items-center justify-between mb-2 min-h-[18px]">
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

      {items.length === 0 ? (
        <div className="py-8 text-center text-xs text-gray-400 italic">
          Sin subcategorías para mostrar.
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-x-6 gap-y-2">
          {items.map(item => (
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
