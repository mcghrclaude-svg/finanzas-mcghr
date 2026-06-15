/**
 * useDashboard — hook principal del dashboard.
 *
 * Modos:
 *   VITE_USE_MOCK=true (default dev) → datos mock
 *   VITE_USE_MOCK=false              → API real
 *
 * Escenario mock (solo activo cuando VITE_USE_MOCK=true):
 *   VITE_MOCK_SCENARIO=con_historial  (default) → riesgo calculado, línea punteada
 *   VITE_MOCK_SCENARIO=sin_historial             → primer mes, sin histórico
 *
 * Para cambiar:
 *   echo "VITE_MOCK_SCENARIO=sin_historial" >> .env.dev && npm run dev
 */

import { useState, useEffect, useCallback } from 'react'
import {
  RESUMEN_MOCK,
  EJECUCION_CON_HISTORIAL,
  EJECUCION_SIN_HISTORIAL,
  INGRESOS_MOCK,
  OBLIGACIONES_MOCK,
} from '../mock/dashboardMock'
import apiClient from '../api/client'

const USE_MOCK    = import.meta.env.VITE_USE_MOCK !== 'false'
const SCENARIO    = import.meta.env.VITE_MOCK_SCENARIO || 'con_historial'
const MOCK_EJEC   = SCENARIO === 'sin_historial' ? EJECUCION_SIN_HISTORIAL : EJECUCION_CON_HISTORIAL

export function useDashboard(anio, mes) {
  const [resumen,      setResumen]      = useState(null)
  const [ejecucion,    setEjecucion]    = useState(null)
  const [ingresos,     setIngresos]     = useState([])
  const [obligaciones, setObligaciones] = useState([])
  const [loading,      setLoading]      = useState(true)
  const [error,        setError]        = useState(null)

  const cargar = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      if (USE_MOCK) {
        await new Promise(r => setTimeout(r, 200))
        setResumen(RESUMEN_MOCK)
        setEjecucion(MOCK_EJEC)
        setIngresos(INGRESOS_MOCK)
        setObligaciones(OBLIGACIONES_MOCK)
      } else {
        const [resRes, ejecRes] = await Promise.all([
          apiClient.get(`/dashboard/resumen?anio=${anio}&mes=${mes}`),
          apiClient.get(`/presupuestos/ejecucion?anio=${anio}&mes=${mes}`),
        ])
        setResumen(resRes.data)
        setEjecucion(ejecRes.data)
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
  if (n >= 1_000)     return `$${(n / 1_000).toFixed(0)}k`
  return `$${n}`
}

/**
 * Metadata de nivel de riesgo para clases CSS y etiquetas.
 * Incluye 'sin_datos': barra gris, sin badge de color.
 */
export function nivelRiesgoMeta(nivel) {
  switch (nivel) {
    case 'critico':   return { barClass: 'bar-red',    pctClass: 'pct-red',    badgeClass: 'risk-critico' }
    case 'alto':      return { barClass: 'bar-yellow', pctClass: 'pct-yellow', badgeClass: 'risk-alto'    }
    case 'ok':        return { barClass: 'bar-green',  pctClass: 'pct-green',  badgeClass: 'risk-ok'      }
    case 'fijo':      return { barClass: 'bar-green',  pctClass: 'pct-green',  badgeClass: 'risk-fijo'    }
    case 'sin_datos': return { barClass: 'bar-neutral',pctClass: 'pct-neutral',badgeClass: 'risk-sin-datos' }
    default:          return { barClass: 'bar-neutral',pctClass: 'pct-neutral',badgeClass: 'risk-sin-datos' }
  }
}
