/**
 * api/catalogos.js
 * Llamadas a /api/v1/catalogos — espeja el patron de api/client.js del repo.
 */
import client from './client'

const BASE = '/catalogos'

// ── Categorias ────────────────────────────────────────────────────────────────
export const catalogosApi = {
  // Categorias
  getCategorias: (params = {}) =>
    client.get(`${BASE}/categorias`, { params }).then(r => r.data),

  getCategoria: (id) =>
    client.get(`${BASE}/categorias/${id}`).then(r => r.data),

  crearCategoria: (data) =>
    client.post(`${BASE}/categorias`, data).then(r => r.data),

  editarCategoria: (id, data) =>
    client.patch(`${BASE}/categorias/${id}`, data).then(r => r.data),

  inactivarCategoria: (id) =>
    client.delete(`${BASE}/categorias/${id}`).then(r => r.data),

  // Cuentas
  getCuentas: (params = {}) =>
    client.get(`${BASE}/cuentas`, { params }).then(r => r.data),

  getCuenta: (id) =>
    client.get(`${BASE}/cuentas/${id}`).then(r => r.data),

  crearCuenta: (data) =>
    client.post(`${BASE}/cuentas`, data).then(r => r.data),

  editarCuenta: (id, data) =>
    client.patch(`${BASE}/cuentas/${id}`, data).then(r => r.data),

  inactivarCuenta: (id) =>
    client.delete(`${BASE}/cuentas/${id}`).then(r => r.data),

  // Contrapartes
  getContrapartes: (params = {}) =>
    client.get(`${BASE}/contrapartes`, { params }).then(r => r.data),

  getContraparte: (id) =>
    client.get(`${BASE}/contrapartes/${id}`).then(r => r.data),

  crearContraparte: (data) =>
    client.post(`${BASE}/contrapartes`, data).then(r => r.data),

  editarContraparte: (id, data) =>
    client.patch(`${BASE}/contrapartes/${id}`, data).then(r => r.data),

  inactivarContraparte: (id) =>
    client.delete(`${BASE}/contrapartes/${id}`).then(r => r.data),

  // Personas
  getPersonas: (params = {}) =>
    client.get(`${BASE}/personas`, { params }).then(r => r.data),

  getPersona: (id) =>
    client.get(`${BASE}/personas/${id}`).then(r => r.data),

  crearPersona: (data) =>
    client.post(`${BASE}/personas`, data).then(r => r.data),

  editarPersona: (id, data) =>
    client.patch(`${BASE}/personas/${id}`, data).then(r => r.data),

  inactivarPersona: (id) =>
    client.delete(`${BASE}/personas/${id}`).then(r => r.data),
}
