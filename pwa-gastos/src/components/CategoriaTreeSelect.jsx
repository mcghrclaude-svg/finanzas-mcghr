import { useEffect, useMemo, useState } from 'react'

// Selector de categoria en arbol (nivel 1/2/3). No reemplaza a Combobox,
// que sigue usandose para Medio de pago -- este es especifico para
// Categoria porque necesita jerarquia (agrupar por id_padre) en vez de
// una lista plana con busqueda simple.
//
// options: lista plana [{ id, etiqueta, nivel, id_padre }] tal como la
// exporta pwa_export_service.py en catalogos.json.

function construirArbol(options) {
  const hijosPorPadre = new Map()
  for (const opt of options) {
    const padre = opt.id_padre ?? null
    if (!hijosPorPadre.has(padre)) hijosPorPadre.set(padre, [])
    hijosPorPadre.get(padre).push(opt)
  }

  function armarNodos(idPadre) {
    return (hijosPorPadre.get(idPadre) ?? []).map((opt) => ({
      ...opt,
      hijos: armarNodos(opt.id),
    }))
  }

  return armarNodos(null)
}

export default function CategoriaTreeSelect({ options, value, onChange, placeholder }) {
  const [abierto, setAbierto] = useState(false)
  const [query, setQuery] = useState('')
  // Expansion manual (clicks del usuario) -- sobrevive a que se escriba
  // o borre el buscador, a diferencia de la expansion forzada por busqueda.
  const [expandidos, setExpandidos] = useState(() => new Set())

  const arbol = useMemo(() => construirArbol(options), [options])
  const porId = useMemo(() => new Map(options.map((o) => [o.id, o])), [options])
  const seleccionada = value ? porId.get(value) ?? null : null

  // Modo edicion: si "value" ya viene precargado, arranca expandido hasta
  // mostrar el branch completo de la categoria seleccionada.
  useEffect(() => {
    if (!value) return
    setExpandidos((prev) => {
      const next = new Set(prev)
      let actual = porId.get(value)
      while (actual?.id_padre) {
        next.add(actual.id_padre)
        actual = porId.get(actual.id_padre)
      }
      return next
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps -- solo al cambiar value/catalogo, no en cada render
  }, [value, porId])

  function toggleExpandido(id) {
    setExpandidos((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  // Expansion forzada por busqueda: derivada, nunca toca "expandidos".
  // Al borrar el texto vuelve a vacio sola y reaparece el estado manual.
  const queryNorm = query.trim().toLowerCase()
  const forzadosPorBusqueda = useMemo(() => {
    const forzados = new Set()
    if (!queryNorm) return forzados
    for (const opt of options) {
      if (opt.nivel > 1 && opt.etiqueta.toLowerCase().includes(queryNorm)) {
        let actual = opt
        while (actual?.id_padre) {
          forzados.add(actual.id_padre)
          actual = porId.get(actual.id_padre)
        }
      }
    }
    return forzados
  }, [queryNorm, options, porId])

  function seleccionar(opt) {
    onChange(opt.id)
    setAbierto(false)
    setQuery('')
  }

  function renderNodo(nodo, profundidad) {
    const esHoja = nodo.hijos.length === 0
    const estaExpandido = expandidos.has(nodo.id) || forzadosPorBusqueda.has(nodo.id)
    const matchea = queryNorm && nodo.etiqueta.toLowerCase().includes(queryNorm)

    return (
      <div key={nodo.id}>
        <button
          type="button"
          onClick={() => (esHoja ? seleccionar(nodo) : toggleExpandido(nodo.id))}
          className={`w-full flex items-center gap-1 text-left px-3 py-2 text-sm hover:bg-gray-50 ${
            matchea ? 'bg-yellow-100' : ''
          }`}
          style={{ paddingLeft: `${12 + profundidad * 16}px` }}
        >
          {!esHoja && (
            <span className="text-gray-400 w-4 shrink-0">{estaExpandido ? '▾' : '▸'}</span>
          )}
          {esHoja && <span className="w-4 shrink-0" />}
          <span className="text-gray-900">{nodo.etiqueta}</span>
        </button>
        {!esHoja && estaExpandido && (
          <div>{nodo.hijos.map((hijo) => renderNodo(hijo, profundidad + 1))}</div>
        )}
      </div>
    )
  }

  return (
    <div className="relative">
      <label className="block text-sm font-medium text-gray-700 mb-1">Categoria</label>
      <button
        type="button"
        onClick={() => setAbierto((a) => !a)}
        className="w-full rounded-lg border border-gray-300 py-2 px-3 text-base text-left focus:border-blue-500 focus:ring-blue-500 bg-white"
      >
        {seleccionada ? (
          <span className="text-gray-900">{seleccionada.etiqueta}</span>
        ) : (
          <span className="text-gray-400">{placeholder ?? 'Seleccionar...'}</span>
        )}
      </button>

      {abierto && (
        <div className="absolute z-10 mt-1 w-full rounded-lg bg-white shadow-lg border border-gray-200">
          <div className="p-2 border-b border-gray-100">
            <input
              autoFocus
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Buscar categoria..."
              className="w-full rounded-lg border border-gray-300 py-2 px-3 text-sm focus:border-blue-500 focus:ring-blue-500"
            />
          </div>
          <div className="max-h-56 overflow-auto py-1">
            {arbol.length === 0 ? (
              <div className="px-3 py-2 text-sm text-gray-500">Sin categorias</div>
            ) : (
              arbol.map((nodo) => renderNodo(nodo, 0))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
