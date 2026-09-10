import { useMemo, useState } from 'react'
import ColorPickerPopover from './ColorPickerPopover'

// Mismo armado de arbol que CategoriaTreeSelect (agrupar por id_padre),
// pero esto no es un selector con dropdown -- se muestra siempre
// expandible inline, con un checkbox de visibilidad y un color por fila
// en vez de "elegir una sola opcion".
function construirArbol(options) {
  const hijosPorPadre = new Map()
  for (const opt of options) {
    const padre = opt.id_padre ?? null
    if (!hijosPorPadre.has(padre)) hijosPorPadre.set(padre, [])
    hijosPorPadre.get(padre).push(opt)
  }
  function armarNodos(idPadre) {
    return (hijosPorPadre.get(idPadre) ?? []).map((opt) => ({ ...opt, hijos: armarNodos(opt.id) }))
  }
  return armarNodos(null)
}

const COLOR_DEFAULT = '#14b8a6'

function Fila({ nodo, profundidad, ocultas, onToggleOculta, colores, onSetColor, expandidos, toggleExpandido, popoverAbierto, setPopoverAbierto }) {
  const esHoja = nodo.hijos.length === 0
  const estaExpandido = expandidos.has(nodo.id)
  const visible = !ocultas.includes(nodo.id)
  const color = colores[nodo.id] ?? COLOR_DEFAULT

  return (
    <div>
      <div
        className="flex items-center gap-2 py-2 rounded-lg hover:bg-gray-50"
        style={{ paddingLeft: `${8 + profundidad * 20}px`, paddingRight: '8px' }}
      >
        {!esHoja ? (
          <button
            type="button"
            onClick={() => toggleExpandido(nodo.id)}
            className="w-5 shrink-0 text-gray-400"
          >
            {estaExpandido ? '▾' : '▸'}
          </button>
        ) : (
          <span className="w-5 shrink-0" />
        )}

        <span className={`flex-1 min-w-0 truncate text-sm ${visible ? 'text-gray-900' : 'text-gray-400'}`}>
          {nodo.etiqueta}
        </span>

        <input
          type="checkbox"
          checked={visible}
          onChange={() => onToggleOculta(nodo.id)}
          className="w-[18px] h-[18px] shrink-0 rounded accent-violet-600 cursor-pointer"
        />

        <div className="relative shrink-0">
          <button
            type="button"
            disabled={!visible}
            title={visible ? 'Cambiar color de la barra' : 'Activá el checkbox para elegir color'}
            onClick={() => setPopoverAbierto(popoverAbierto === nodo.id ? null : nodo.id)}
            className={`w-[22px] h-[22px] rounded-full ${visible ? '' : 'border-2 border-dashed border-gray-300 bg-gray-100'}`}
            style={visible ? { background: color, boxShadow: '0 0 0 1px rgba(0,0,0,0.08)' } : undefined}
          />
          {popoverAbierto === nodo.id && (
            <ColorPickerPopover
              value={color}
              onChange={(nuevoColor) => onSetColor(nodo.id, nuevoColor)}
              onClose={() => setPopoverAbierto(null)}
            />
          )}
        </div>
      </div>

      {!esHoja && estaExpandido && (
        <div>
          {nodo.hijos.map((hijo) => (
            <Fila
              key={hijo.id}
              nodo={hijo}
              profundidad={profundidad + 1}
              ocultas={ocultas}
              onToggleOculta={onToggleOculta}
              colores={colores}
              onSetColor={onSetColor}
              expandidos={expandidos}
              toggleExpandido={toggleExpandido}
              popoverAbierto={popoverAbierto}
              setPopoverAbierto={setPopoverAbierto}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default function CategoriaVisibilidadTree({ categorias, ocultas, onToggleOculta, colores, onSetColor }) {
  const arbol = useMemo(() => construirArbol(categorias), [categorias])
  const [expandidos, setExpandidos] = useState(() => new Set())
  const [popoverAbierto, setPopoverAbierto] = useState(null)

  function toggleExpandido(id) {
    setExpandidos((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  if (arbol.length === 0) {
    return <p className="text-sm text-gray-500 px-2 py-1">No hay categorias cargadas todavia.</p>
  }

  return (
    <div>
      <div className="flex items-center gap-2 px-2 pb-2 text-[0.68rem] font-bold uppercase tracking-wide text-gray-500">
        <span className="flex-1">Categoría</span>
        <span className="w-[18px] text-center shrink-0">Ver</span>
        <span className="w-[22px] text-center shrink-0">Color</span>
      </div>
      <div className="divide-y divide-gray-100">
        {arbol.map((nodo) => (
          <Fila
            key={nodo.id}
            nodo={nodo}
            profundidad={0}
            ocultas={ocultas}
            onToggleOculta={onToggleOculta}
            colores={colores}
            onSetColor={onSetColor}
            expandidos={expandidos}
            toggleExpandido={toggleExpandido}
            popoverAbierto={popoverAbierto}
            setPopoverAbierto={setPopoverAbierto}
          />
        ))}
      </div>
    </div>
  )
}
