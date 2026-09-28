/**
 * useDashboard — hook principal del Home (variante D).
 *
 * Todo el Home usa mes calendario (no periodo financiero de salario) --
 * mismo criterio que la PWA -- para que KPIs, la torta de gasto por
 * categoria y el presupuesto por categoria sean consistentes entre si.
 * El periodo financiero (PeriodoFinanciero, dia_acreditacion_salario) sigue
 * existiendo para Budget Mgmt, que no lo usa este hook.
 *
 * Modos:
 *   VITE_USE_MOCK=true (default dev) → datos mock
 *   VITE_USE_MOCK=false              → API real
 */

import { useState, useEffect, useCallback } from 'react'
import {
  RESUMEN_MOCK,
  INGRESOS_MOCK,
  OBLIGACIONES_MOCK,
  INBOX_STATS_MOCK,
  HOME_CONFIG_MOCK,
  TRANSACCIONES_RECIENTES_MOCK,
  PATRIMONIO_MOCK,
  PATRIMONIO_HISTORICO_MOCK,
  RESUMEN_CATEGORIAS_MOCK,
} from '../mock/dashboardMock'
import apiClient from '../api/client'
import { presupuestosApi } from '../api/presupuestos'
import { transaccionesApi } from '../api/transacciones'
import { inversionesApi } from '../api/inversiones'
import { homeConfigApi } from '../api/homeConfig'
import { catalogosApi } from '../api/catalogos'

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false'

export function useDashboard(anio, mes) {
  const [resumen,               setResumen]               = useState(null)
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
        setIngresos(INGRESOS_MOCK)
        setObligaciones(OBLIGACIONES_MOCK)
        setInboxStats(INBOX_STATS_MOCK)
        setHomeConfig(HOME_CONFIG_MOCK)
        setTransaccionesRecientes(TRANSACCIONES_RECIENTES_MOCK.items)
        setPatrimonio(PATRIMONIO_MOCK)
        setPatrimonioHistorico(PATRIMONIO_HISTORICO_MOCK)
        setResumenCategorias(RESUMEN_CATEGORIAS_MOCK)
        setCategoriasConHijos(new Set(
          RESUMEN_CATEGORIAS_MOCK.filter(c => c.id_padre).map(c => c.id_padre)
        ))
      } else {
        const [
          resRes, statsRes, configRes, trxRes, patrRes, patrHistRes, categoriasRes, resumenCatRes,
        ] = await Promise.all([
          apiClient.get(`/dashboard/resumen?anio=${anio}&mes=${mes}`),
          apiClient.get('/inbox/stats'),
          homeConfigApi.obtener(),
          transaccionesApi.listar({ estado: 'confirmado', limit: 8 }),
          inversionesApi.patrimonio(),
          inversionesApi.patrimonioHistorico(6),
          catalogosApi.getCategorias({ solo_activas: true }),
          presupuestosApi.resumenPorCategoria(anio, mes),
        ])
        setResumen(resRes.data)
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

  const actualizarHomeConfig = useCallback(async (cambios) => {
    if (USE_MOCK) {
      setHomeConfig(prev => ({ ...prev, ...cambios }))
      return
    }
    const nuevo = await homeConfigApi.actualizar(cambios)
    setHomeConfig(nuevo)
  }, [])

  return {
    resumen, ingresos, obligaciones,
    inboxStats, homeConfig, transaccionesRecientes, patrimonio, patrimonioHistorico,
    categoriasConHijos, resumenCategorias,
    loading, error, refetch: cargar,
    actualizarHomeConfig,
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
