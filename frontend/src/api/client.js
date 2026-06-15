/**
 * Cliente HTTP centralizado (axios).
 * Todos los módulos importan este cliente — nunca axios directo.
 *
 * Interceptor de respuesta:
 *   - Errores RFC 7807 se convierten a instancias de ApiError
 *   - Toast automático para errores 5xx
 *   - 404 no genera toast (manejado por el módulo)
 */

import axios from 'axios'
import toast from 'react-hot-toast'

export class ApiError extends Error {
  constructor(status, title, detail) {
    super(detail || title)
    this.status = status
    this.title = title
    this.detail = detail
  }
}

const client = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  timeout: 15_000,
})

client.interceptors.response.use(
  res => res.data,
  err => {
    const { response } = err
    if (!response) {
      toast.error('Sin conexión con el servidor')
      return Promise.reject(new ApiError(0, 'Network Error'))
    }
    const { status, data } = response
    const apiErr = new ApiError(status, data?.title ?? 'Error', data?.detail)
    if (status >= 500) {
      toast.error(`Error del servidor (${status})`)
    }
    return Promise.reject(apiErr)
  }
)

export default client
