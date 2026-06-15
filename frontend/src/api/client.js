/**
 * apiClient — axios instance configurada para la API de Finanzas MCGHR.
 *
 * Base URL: VITE_API_URL (default: http://localhost:8000)
 * Manejo de errores RFC 7807 (detail field de FastAPI).
 */

import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  timeout: 10_000,
  headers: { 'Content-Type': 'application/json' },
})

// Interceptor de respuesta: normaliza errores FastAPI
apiClient.interceptors.response.use(
  res => res,
  err => {
    const detail = err.response?.data?.detail
    const msg = Array.isArray(detail)
      ? detail.map(d => d.msg).join(', ')
      : (detail ?? err.message ?? 'Error desconocido')
    return Promise.reject(new Error(msg))
  }
)

export default apiClient
