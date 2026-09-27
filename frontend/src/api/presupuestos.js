/**
 * api/presupuestos.js
 * Llamadas a /api/v1/presupuestos -- espeja el patron de api/catalogos.js del repo.
 */
import client from './client'

const BASE = '/presupuestos'

export const presupuestosApi = {
  listar: (anio, mes) =>
    client.get(BASE, { params: { anio, mes } }).then(r => r.data),

  resumenPorCategoria: (anio, mes) =>
    client.get(`${BASE}/resumen-por-categoria`, { params: { anio, mes } }).then(r => r.data),

  guardarBatch: (anio, mes, items, idPeriodo = null) =>
    client.post(`${BASE}/batch`, {
      anio, mes, id_periodo: idPeriodo,
      items: items.map(({ idCategoria, monto }) => ({
        id_categoria: idCategoria,
        monto_presupuestado: monto,
      })),
    }).then(r => r.data),

  eliminar: (anio, mes, idCategoria) =>
    client.delete(`${BASE}/${anio}/${mes}/${idCategoria}`),

  benchmark: (idCategoria) =>
    client.get(`${BASE}/benchmark/${idCategoria}`).then(r => r.data),

  ejecucion: (anio, mes) =>
    client.get(`${BASE}/ejecucion`, { params: { anio, mes } }).then(r => r.data),
}
