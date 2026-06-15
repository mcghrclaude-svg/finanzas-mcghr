/**
 * Intercepta el evento `beforeunload` del navegador cuando hay cambios
 * sin guardar. Muestra el diálogo nativo del browser.
 * No requiere render visible — solo efecto.
 */

import { useEffect } from 'react'
import useAppStore from '@/store/useAppStore'

export default function AlertaSinGuardar() {
  const hayCambios = useAppStore(s => s.hayCambiosSinGuardar)

  useEffect(() => {
    if (!hayCambios) return

    const handler = (e) => {
      e.preventDefault()
      e.returnValue = '' // requerido por algunos navegadores
    }

    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [hayCambios])

  return null
}
