/**
 * useDashboard — hook principal del dashboard.
 *
 * Modo mock (VITE_USE_MOCK=true, default en dev):
 *   Retorna datos de dashboardMock.js sin llamar al backend.
 *   Útil para desarrollo de UI antes de que los endpoints estén listos.
 *
 * Modo API (VITE_USE_MOCK=false):
 *   Llama a:
 *     GET /api/v1/dashboard/resumen?anio=&mes=
 *     GET /api/v1/presupuestos/ejecucion?anio=&mes=
 *   Los datos de ingresos y obligaciones se obtienen de los endpoints
 *   correspondientes (a implementar como parte de los módulos futuros).
 *
 * Para cambiar de mock a real: VITE_USE_MOCK=false en .env.dev
 */

import { useState, useEffect, useCallback } from 'react'
import {
  RESUMEN_MOCK,
  EJECUCION_MOCK,
  INGRESOS_MOCK,
  OBLIGACIONES_MOCK,
} from '../mock/dashboardMock'
import apiClient from '../api/client'

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false'

export function useDashboard(anio, mes) {
  const [resumen, setResumen] = useState(null)
  const [ejecucion, setEjecucion] = useState(null)
  const [ingresos, setIngresos] = useState([])
  const [obligaciones, setObligaciones] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const cargar = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      if (USE_MOCK) {
        await new Promise(r => setTimeout(r, 200))
        setResumen(RESUMEN_MOCK)
        setEjecucion(EJECUCION_MOCK)
        setIngresos(INGRESOS_MOCK)
        setObligaciones(OBLIGACIONES_MOCK)
      } else {
        const [resRes, ejecRes] = await Promise.all([
          apiClient.get(`/dashboard/resumen?anio=${anio}&mes=${mes}`),
          apiClient.get(`/presupuestos/ejecucion?anio=${anio}&mes=${mes}`),
        ])
        setResumen(resRes.data)
        setEjecucion(ejecRes.data)
        // Ingresos y obligaciones: mock hasta que esos endpoints estén listos
        setIngresos(INGRESOS_MOCK)
        setObligaciones(OBLIGACIONES_MOCK)
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [anio, mes])

  useEffect(() => { cargar() }, [cargar])

  return { resumen, ejecucion, ingresos, obligaciones, loading, error, refetch: cargar }
}

/** Formatea un número en pesos colombianos abreviado */
export function formatCOP(n) {
  if (n == null) return '—'
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}k`
  return `$${n}`
}

/** Metadata de nivel de riesgo para clases CSS y etiquetas */
export function nivelRiesgoMeta(nivel) {
  switch (nivel) {
    case 'critico': return { barClass: 'bar-red',    pctClass: 'pct-red',    badgeClass: 'risk-critico' }
    case 'alto':    return { barClass: 'bar-yellow', pctClass: 'pct-yellow', badgeClass: 'risk-alto' }
    case 'ok':      return { barClass: 'bar-green',  pctClass: 'pct-green',  badgeClass: 'risk-ok' }
    case 'fijo':    return { barClass: 'bar-green',  pctClass: 'pct-green',  badgeClass: 'risk-fijo' }
    default:        return { barClass: 'bar-green',  pctClass: 'pct-green',  badgeClass: 'risk-ok' }
  }
}
