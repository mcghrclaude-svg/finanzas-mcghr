/**
 * colorCategoria — color estable por id_categoria.
 *
 * El backend no asigna color por categoría (eso vive en la config local de
 * la PWA, coloresCategorias en su settingsStore) -- acá se deriva uno
 * determinístico a partir del id, compartido por todos los widgets del Home
 * que necesitan pintar categorías (CategoriaBullet, GastoPorCategoriaPie).
 */
const PALETTE = ['#D85A30', '#378ADD', '#1D9E75', '#D4537E', '#534AB7', '#888780', '#C08A2E', '#2E9BB0']

export function colorDeterministico(id) {
  let hash = 0
  for (let i = 0; i < id.length; i++) hash = (hash * 31 + id.charCodeAt(i)) >>> 0
  return PALETTE[hash % PALETTE.length]
}
