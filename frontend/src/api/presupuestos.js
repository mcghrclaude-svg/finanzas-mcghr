import client from './client'

export const presupuestosApi = {
  listar: (params) => client.get('/presupuestos', { params }),
  ejecucionMes: (anio, mes) => client.get(`/presupuestos/${anio}/${mes}`),
  proyeccion: (anio, mes) => client.get(`/presupuestos/${anio}/${mes}/proyeccion`),
  benchmark: (categoria) => client.get(`/presupuestos/benchmark/${categoria}`),
  crear: (data) => client.post('/presupuestos', data),
  editar: (anio, mes, categoria, data) => client.put(`/presupuestos/${anio}/${mes}/${categoria}`, data),
  eliminar: (anio, mes, categoria) => client.delete(`/presupuestos/${anio}/${mes}/${categoria}`),
}
