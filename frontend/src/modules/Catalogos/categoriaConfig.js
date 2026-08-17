/**
 * categoriaConfig.js -- configuracion de categorias del editor de Catalogos
 * (unico consumidor: vista jerarquica en arbol, buscador de padre, campos).
 */

export function generarSlug(nombre) {
  return nombre
    .toUpperCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')  // quitar tildes
    .replace(/[^A-Z0-9\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-')
    .slice(0, 20)
}

export function generarSlugUnico(nombre, existentes = []) {
  const base = generarSlug(nombre)
  if (!existentes.includes(base)) return base
  let i = 2
  while (existentes.includes(`${base}-${i}`)) i++
  return `${base}-${i}`
}

// Convierte la lista plana de categorias (con id_padre) en arbol anidado (hijos).
export function buildTree(items) {
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

// Aplana el arbol en filas {id, nivel, activa, ruta} con la ruta completa
// anidada (ej: "Finanzas / Inversiones / Aportes recurrentes"). Recorrido DFS
// pre-order: agrupa cada familia, que es el orden que se quiere mostrar en el buscador.
export function buildRutas(items) {
  const arbol = buildTree(items)
  const filas = []
  function recorrer(nodos, rutaPadre) {
    for (const nodo of nodos) {
      const ruta = rutaPadre ? `${rutaPadre} / ${nodo.nombre}` : nodo.nombre
      filas.push({ id: nodo.id, nivel: nodo.nivel, activa: nodo.activa, ruta })
      if (nodo.hijos.length) recorrer(nodo.hijos, ruta)
    }
  }
  recorrer(arbol, '')
  return filas
}

// Jerarquia de categorias limitada a 3 niveles (ver docs/functional_spec.md).
// Las de nivel maximo no pueden tener hijos, por lo que no son opcion de padre.
export const NIVEL_MAXIMO = 3

// Opciones del buscador de categoria padre: todas las categorias activas que
// todavia admiten hijos (mas la actualmente seleccionada, aunque este inactiva,
// para que el campo bloqueado en edicion no quede en blanco).
// extra = { items, monedasActivas } -- items es la lista de la seccion activa
// (categorias, en este caso).
function opcionesCategoriaPadre(values, extra) {
  return buildRutas(extra?.items ?? [])
    .filter(c => (c.nivel < NIVEL_MAXIMO && c.activa !== false) || c.id === values.id_padre)
    .map(c => ({ value: c.id, label: c.ruta }))
}

export const CAMPOS_CATEGORIAS = [
  { key: 'nombre',           label: 'Name',          type: 'text',   required: true,
    noSlash: true, hint: "'/' is not allowed and gets replaced with '-'" },
  { key: 'id_padre',         label: 'Parent category', type: 'buscador', lock_on_edit: true,
    emptyLabel: '— No parent (creates a level 1 category) —',
    placeholder: 'Search by name...',
    hint: 'Leave empty for a top-level category',
    options: opcionesCategoriaPadre },
  { key: 'tipo_patron_gasto',label: 'Spending pattern', type: 'select', required: true,
    options: [
      { value: 'fijo_unico',          label: 'Fixed one-time (rent, loan payment)' },
      { value: 'fijo_recurrente',     label: 'Fixed recurring (subscriptions)' },
      { value: 'variable_frecuente',  label: 'Variable frequent (groceries, delivery)' },
      { value: 'variable_esporadico', label: 'Variable sporadic (health, travel)' },
    ]
  },
]
