import { useEffect, useState } from 'react'
import { useMsal, useIsAuthenticated } from '@azure/msal-react'
import { useSettingsStore } from '../store/settingsStore'
import {
  getResumenCategoriasCache,
  sincronizarResumenCategorias,
  cargarResumenCategoriasDeEjemplo,
} from '../api/resumenCategorias'

const VACIO = { mes: null, total: null, categorias: [] }

// Mismo patron que useCatalogos: cache primero (instantaneo), refresco
// desde OneDrive en background si hay sesion y carpeta raiz configurada.
export function useResumenCategorias() {
  const { accounts } = useMsal()
  const isAuthenticated = useIsAuthenticated()
  const account = accounts[0]
  const { carpetaRaiz } = useSettingsStore()
  const [resumen, setResumen] = useState(VACIO)

  useEffect(() => {
    (async () => {
      const cache = await getResumenCategoriasCache()
      setResumen(cache)
      if (isAuthenticated && carpetaRaiz) {
        const fresh = await sincronizarResumenCategorias(account, carpetaRaiz)
        setResumen(fresh)
      }
    })()
  }, [isAuthenticated, carpetaRaiz, account])

  async function cargarEjemplo() {
    const data = await cargarResumenCategoriasDeEjemplo()
    setResumen(data)
  }

  return { resumen, cargarEjemplo }
}
