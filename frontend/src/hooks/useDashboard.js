/**
 * useDashboard — hook principal del dashboard.
 *
 * En modo mock (VITE_USE_MOCK=true o API no disponible), retorna datos de dashboardMock.js.
 * Para conectar al API real, descomentar las llamadas a apiClient y eliminar el fallback mock.
 *
 * Contrato del API:
 *   GET /api/v1/dashboard/resumen?anio=2026&mes=6   → RESUMEN_MOCK shape
 *   GET /api/v1/presupuestos/ejecucion?anio=2026&mes=6 → EJECUCION_MOCK shape
 */

import { useState, useEffect, useCallback } from 'react'
import {
  RESUMEN_MOCK,
  EJECUCION_MOCK,
  INGRESOS_MOCK,
  OBLIGACIONES_MOCK,
} from '../mock/dashboardMock'

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true' || import.meta.env.DEV

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
        // Simular latencia de red para ver estados de carga
        await new Promise(r => setTimeout(r, 300))
        setResumen(RESUMEN_MOCK)
        setEjecucion(EJECUCION_MOCK)
        setIngresos(INGRESOS_MOCK)
        setObligaciones(OBLIGACIONES_MOCK)
      } else {
        // TODO: reemplazar con llamadas reales cuando los endpoints estén listos (issues #14 #15)
        // const [res, ejec] = await Promise.all([
        //   apiClient.get(`/dashboard/resumen?anio=${anio}&mes=${mes}`),
        //   apiClient.get(`/presupuestos/ejecucion?anio=${anio}&mes=${mes}`),
        // ])
        // setResumen(res.data)
        // setEjecucion(ejec.data)
        throw new Error('API no configurada — activar VITE_USE_MOCK=true')
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

/** Helpers de formato reutilizables */
export function formatCOP(n) {
  if (n == null) return '—'
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000)     return `$${(n / 1_000).toFixed(0)}k`
  return `$${n}`
}

export function nivelRiesgoMeta(nivel) {
  switch (nivel) {
    case 'critico': return { label: 'Crítico', colorClass: 'risk-critico', barClass: 'bar-red',    pctClass: 'pct-red' }
    case 'alto':    return { label: 'Alto',    colorClass: 'risk-alto',    barClass: 'bar-yellow', pctClass: 'pct-yellow' }
    case 'ok':      return { label: 'OK',      colorClass: 'risk-ok',      barClass: 'bar-green',  pctClass: 'pct-green' }
    case 'fijo':    return { label: 'Fijo',    colorClass: 'risk-fijo',    barClass: 'bar-green',  pctClass: 'pct-green' }
    default:        return { label: '',        colorClass: '',             barClass: 'bar-green',  pctClass: 'pct-green' }
  }
}
