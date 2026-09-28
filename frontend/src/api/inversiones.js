/**
 * api/inversiones.js
 * Llamadas a /api/v1/inversiones -- espeja el patron de api/presupuestos.js.
 */
import client from './client'

const BASE = '/inversiones'

export const inversionesApi = {
  patrimonio: (fecha = null) =>
    client.get(`${BASE}/patrimonio`, { params: fecha ? { fecha } : {} }).then(r => r.data),

  patrimonioHistorico: (meses = 12) =>
    client.get(`${BASE}/patrimonio/historico`, { params: { meses } }).then(r => r.data),
}
