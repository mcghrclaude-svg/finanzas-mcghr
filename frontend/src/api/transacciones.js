import client from './client'

export const transaccionesApi = {
  listar: (params) => client.get('/transacciones', { params }),
  obtener: (id) => client.get(`/transacciones/${id}`),
  crear: (data) => client.post('/transacciones', data),
  editar: (id, data) => client.patch(`/transacciones/${id}`, data),
  confirmar: (id) => client.post(`/transacciones/${id}/confirmar`),
  descartar: (id) => client.post(`/transacciones/${id}/descartar`),
  anular: (id) => client.delete(`/transacciones/${id}`),
  inbox: (params) => client.get('/inbox', { params }),
}
