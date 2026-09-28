/**
 * api/homeConfig.js
 * Llamadas a /api/v1/home-config -- preferencia de que widgets se ven en el
 * Home (banner de insight, Evolucion patrimonio, Ask Claude). Vive en el
 * backend, no en localStorage, para que sea la misma configuracion sin
 * importar el dispositivo. Espeja el patron de api/pwaConfig.js.
 */
import client from './client'

const BASE = '/home-config'

export const homeConfigApi = {
  obtener: () =>
    client.get(BASE).then(r => r.data),

  actualizar: (data) =>
    client.patch(BASE, data).then(r => r.data),
}
