import { useEffect, useState } from 'react'
import { useMsal, useIsAuthenticated } from '@azure/msal-react'
import { useSettingsStore } from '../store/settingsStore'
import { getCatalogosCache, sincronizarCatalogos, cargarCatalogosDeEjemplo } from '../api/catalogos'

const VACIO = { categorias: [], medios_de_pago: [], monedas: [] }

// Compartido entre NuevoGasto (combobox de categoria/moneda/medio de pago)
// y Configuracion (combobox de moneda/medio de pago por default): cache
// primero (instantaneo), refresco desde OneDrive en background si hay
// sesion y carpeta de catalogos configurada.
export function useCatalogos() {
  const { accounts } = useMsal()
  const isAuthenticated = useIsAuthenticated()
  const account = accounts[0]
  const { carpetaCatalogos } = useSettingsStore()
  const [catalogos, setCatalogos] = useState(VACIO)

  useEffect(() => {
    (async () => {
      const cache = await getCatalogosCache()
      setCatalogos(cache)
      if (isAuthenticated && carpetaCatalogos) {
        const fresh = await sincronizarCatalogos(account, carpetaCatalogos)
        setCatalogos(fresh)
      }
    })()
  }, [isAuthenticated, carpetaCatalogos, account])

  async function cargarEjemplo() {
    const data = await cargarCatalogosDeEjemplo()
    setCatalogos(data)
  }

  return { catalogos, cargarEjemplo }
}
