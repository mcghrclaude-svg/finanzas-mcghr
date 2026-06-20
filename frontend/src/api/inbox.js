import { apiClient } from './client'

export const inboxApi = {
  listar: (params) =>
    apiClient.get('/inbox/', { params }).then(r => r.data),

  stats: () =>
    apiClient.get('/inbox/stats').then(r => r.data),

  detalle: (id) =>
    apiClient.get(`/inbox/${id}`).then(r => r.data),

  editar: (id, data) =>
    apiClient.patch(`/inbox/${id}`, data).then(r => r.data),

  confirmar: (id, data = {}) =>
    apiClient.post(`/inbox/${id}/confirmar`, data).then(r => r.data),

  descartar: (id) =>
    apiClient.post(`/inbox/${id}/descartar`).then(r => r.data),

  confirmarLote: (ids) =>
    apiClient.post('/inbox/confirmar-lote', { ids }).then(r => r.data),
}

export default inboxApi
