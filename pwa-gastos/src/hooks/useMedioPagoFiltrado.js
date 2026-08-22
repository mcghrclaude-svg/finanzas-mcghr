import { useEffect } from 'react'

// GHR ve GHR + Ambos, MC ve MC + Ambos.
export function filtrarMediosPorUsuario(mediosDePago, usuario) {
  return mediosDePago.filter((m) => m.propietario === usuario || m.propietario === 'Ambos')
}

// Compartido entre NuevoGasto (usuario = "quien realizo el gasto") y
// Configuracion (usuario = "usuario de este dispositivo"): filtra el
// catalogo de medios de pago por propietario y, si el medio de pago ya
// seleccionado deja de ser valido al cambiar de usuario, lo resetea a
// null (lo mantiene si su propietario es "Ambos"). No auto-selecciona
// ningun default nuevo. No toca la seleccion mientras el catalogo
// todavia no cargo (lista vacia).
export function useMedioPagoFiltrado(mediosDePago, usuario, idMedioPago, setIdMedioPago) {
  useEffect(() => {
    if (!idMedioPago || mediosDePago.length === 0) return
    const actual = mediosDePago.find((m) => m.id === idMedioPago)
    const sigueValido = actual && (actual.propietario === usuario || actual.propietario === 'Ambos')
    if (!sigueValido) setIdMedioPago(null)
  }, [usuario, mediosDePago])

  return filtrarMediosPorUsuario(mediosDePago, usuario)
}
