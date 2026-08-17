/**
 * api/pwaConfig.js
 * Llamadas a /api/v1/pwa-config -- espeja el patron de api/catalogos.js.
 */
import client from './client'

const BASE = '/pwa-config'

export const pwaConfigApi = {
  obtener: () =>
    client.get(BASE).then(r => r.data),

  actualizar: (data) =>
    client.put(BASE, data).then(r => r.data),

  toggle: (habilitado) =>
    client.post(`${BASE}/toggle`, { habilitado }).then(r => r.data),

  historial: (limit = 20) =>
    client.get(`${BASE}/historial`, { params: { limit } }).then(r => r.data),

  browseFolders: (path = '') =>
    client.get(`${BASE}/browse-folders`, { params: { path } }).then(r => r.data),
}
