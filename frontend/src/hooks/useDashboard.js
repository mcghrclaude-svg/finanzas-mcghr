/**
 * useDashboard — hook principal del Home (variante D).
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
  INBOX_STATS_MOCK,
  HOME_CONFIG_MOCK,
  TRANSACCIONES_RECIENTES_MOCK,
  PATRIMONIO_MOCK,
  PATRIMONIO_HISTORICO_MOCK,
  SUBCATEGORIAS_MOCK,
  RESUMEN_CATEGORIAS_MOCK,
} from '../mock/dashboardMock'
import apiClient from '../api/client'
import { presupuestosApi } from '../api/presupuestos'
import { transaccionesApi } from '../api/transacciones'
import { inversionesApi } from '../api/inversiones'
import { homeConfigApi } from '../api/homeConfig'
import { catalogosApi } from '../api/catalogos'

const USE_MOCK    = import.meta.env.VITE_USE_MOCK !== 'false'
const SCENARIO    = import.meta.env.VITE_MOCK_SCENARIO || 'con_historial'
const MOCK_EJEC   = SCENARIO === 'sin_historial' ? EJECUCION_SIN_HISTORIAL : EJECUCION_CON_HISTORIAL

export function useDashboard(anio, mes) {
  const [resumen,               setResumen]               = useState(null)
  const [ejecucion,             setEjecucion]              = useState(null)
  const [ingresos,              setIngresos]               = useState([])
  const [obligaciones,          setObligaciones]           = useState([])
  const [inboxStats,            setInboxStats]             = useState(null)
  const [homeConfig,            setHomeConfig]             = useState(null)
  const [transaccionesRecientes, setTransaccionesRecientes] = useState([])
  const [patrimonio,            setPatrimonio]             = useState(null)
  const [patrimonioHistorico,   setPatrimonioHistorico]    = useState(null)
  const [categoriasConHijos,    setCategoriasConHijos]     = useState(new Set())
  const [resumenCategorias,     setResumenCategorias]      = useState([])
  const [loading,               setLoading]                = useState(true)
  const [error,                 setError]                  = useState(null)

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
        setInboxStats(INBOX_STATS_MOCK)
        setHomeConfig(HOME_CONFIG_MOCK)
        setTransaccionesRecientes(TRANSACCIONES_RECIENTES_MOCK.items)
        setPatrimonio(PATRIMONIO_MOCK)
        setPatrimonioHistorico(PATRIMONIO_HISTORICO_MOCK)
        setCategoriasConHijos(new Set(Object.keys(SUBCATEGORIAS_MOCK)))
        setResumenCategorias(RESUMEN_CATEGORIAS_MOCK)
      } else {
        const [
          resRes, ejecRes, statsRes, configRes, trxRes, patrRes, patrHistRes, categoriasRes, resumenCatRes,
        ] = await Promise.all([
          apiClient.get(`/dashboard/resumen?anio=${anio}&mes=${mes}`),
          presupuestosApi.ejecucion(anio, mes),
          apiClient.get('/inbox/stats'),
          homeConfigApi.obtener(),
          transaccionesApi.listar({ estado: 'confirmado', limit: 8 }),
          inversionesApi.patrimonio(),
          inversionesApi.patrimonioHistorico(6),
          catalogosApi.getCategorias({ solo_activas: true }),
          presupuestosApi.resumenPorCategoria(anio, mes),
        ])
        setResumen(resRes.data)
        setEjecucion(ejecRes)
        setIngresos(INGRESOS_MOCK)
        setObligaciones(OBLIGACIONES_MOCK)
        setInboxStats(statsRes.data)
        setHomeConfig(configRes)
        setTransaccionesRecientes(trxRes.data.items ?? [])
        setPatrimonio(patrRes)
        setPatrimonioHistorico(patrHistRes)
        setResumenCategorias(resumenCatRes.categorias ?? [])

        const listaCategorias = Array.isArray(categoriasRes) ? categoriasRes : (categoriasRes?.items ?? [])
        const conHijos = new Set(
          listaCategorias.filter(c => c.id_padre).map(c => c.id_padre)
        )
        setCategoriasConHijos(conHijos)
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [anio, mes])

  useEffect(() => { cargar() }, [cargar])

  // Drill-down a subcategorias: on-demand, no se precarga con el resto.
  const cargarSubcategorias = useCallback(async (idCategoria) => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 120))
      return SUBCATEGORIAS_MOCK[idCategoria]?.items ?? []
    }
    const data = await presupuestosApi.ejecucionSubcategorias(idCategoria, anio, mes)
    return data.items ?? []
  }, [anio, mes])

  const actualizarHomeConfig = useCallback(async (cambios) => {
    if (USE_MOCK) {
      setHomeConfig(prev => ({ ...prev, ...cambios }))
      return
    }
    const nuevo = await homeConfigApi.actualizar(cambios)
    setHomeConfig(nuevo)
  }, [])

  return {
    resumen, ejecucion, ingresos, obligaciones,
    inboxStats, homeConfig, transaccionesRecientes, patrimonio, patrimonioHistorico,
    categoriasConHijos, resumenCategorias,
    loading, error, refetch: cargar,
    cargarSubcategorias, actualizarHomeConfig,
  }
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
