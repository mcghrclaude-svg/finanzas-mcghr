/**
 * categoriaConfig.js -- configuracion de categorias compartida entre
 * Catalogos (vista clasica) y Tools/CatalogsV2 (arbol).
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

export const CAMPOS_CATEGORIAS = [
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
]
