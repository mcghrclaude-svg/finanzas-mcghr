/**
 * presupuestoUtils.js -- funciones puras para el arbol de presupuesto.
 * "hoja" = categoria sin sub-categorias propias: es la unica editable
 * directamente. El monto de una categoria con hijos es siempre la suma de
 * sus hojas descendientes (nunca un valor propio).
 */

export function construirArbol(categorias) {
  const porPadre = new Map()
  for (const cat of categorias) {
    const clave = cat.id_padre ?? null
    const lista = porPadre.get(clave) ?? []
    lista.push(cat)
    porPadre.set(clave, lista)
  }
  function armar(cat) {
    const hijos = (porPadre.get(cat.id) ?? []).map(armar)
    return { id: cat.id, nombre: cat.nombre, nivel: cat.nivel, hijos }
  }
  return (porPadre.get(null) ?? []).map(armar)
}

export function esHoja(nodo) {
  return !nodo.hijos || nodo.hijos.length === 0
}

export function hojasDe(nodo) {
  if (esHoja(nodo)) return [nodo]
  return nodo.hijos.flatMap(hojasDe)
}

export function calcularTotal(nodo, valores) {
  return hojasDe(nodo).reduce((acc, h) => acc + (valores[h.id] ?? 0), 0)
}

export function contarFaltantes(nodo, valores) {
  const hojas = hojasDe(nodo)
  const faltantes = hojas.filter(h => valores[h.id] == null).length
  return { total: hojas.length, faltantes }
}

export function fmt(v) {
  if (v == null) return ''
  return '$' + Math.round(v).toLocaleString('es-CO')
}

export function fmtCompacto(v) {
  if (v == null) return '-'
  const a = Math.abs(v)
  if (a >= 1_000_000) return `$${Math.round(a / 1_000_000)}M`
  if (a >= 1_000) return `$${Math.round(a / 1_000)}K`
  return `$${Math.round(a)}`
}
