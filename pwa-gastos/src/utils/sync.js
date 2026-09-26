import { db } from '../db/db'
import { useSettingsStore } from '../store/settingsStore'
import { getAccessToken, ensureFolder, uploadFile } from '../api/graphClient'

const DIAS_RETENCION_SINCRONIZADOS = 7

function tieneMasDeXDias(fechaISO, dias) {
  const limite = new Date()
  limite.setDate(limite.getDate() - dias)
  return new Date(fechaISO) < limite
}

// Sube todos los gastos no sincronizados de IndexedDB a OneDrive. Por cada
// uno: sube el JSON y, si tiene foto, la imagen; si ambas subidas tienen
// exito el registro pasa a estado='sincronizado' (nunca se borra en el
// momento). Si falla, queda en estado='error' con el motivo en
// ultimoError, para reintentar en la proxima sincronizacion.
//
// Ademas purga (borra local) los registros ya sincronizados con mas de
// 7 dias de antiguedad -- nunca los que estan en 'pendiente' o 'error',
// sin importar la fecha.
export async function syncPendientes(account) {
  const { carpetaRaiz } = useSettingsStore.getState()

  const sincronizadosViejos = await db.gastos.where('estado').equals('sincronizado').toArray()
  for (const g of sincronizadosViejos) {
    if (tieneMasDeXDias(g.fecha, DIAS_RETENCION_SINCRONIZADOS)) {
      await db.gastos.delete(g.localId)
    }
  }

  if (!carpetaRaiz) return { subidos: 0, fallidos: 0, motivo: 'sin-carpeta-configurada' }
  if (!account) return { subidos: 0, fallidos: 0, motivo: 'sin-sesion' }

  const pendientes = await db.gastos.where('estado').notEqual('sincronizado').toArray()
  if (pendientes.length === 0) return { subidos: 0, fallidos: 0 }

  const token = await getAccessToken(account)
  const pendientesFolder = await ensureFolder(token, carpetaRaiz.driveId, carpetaRaiz.itemId, 'pendientes')

  let subidos = 0
  let fallidos = 0

  for (const gasto of pendientes) {
    try {
      if (gasto.imagenBlob && gasto.imagenNombre) {
        await uploadFile(token, carpetaRaiz.driveId, pendientesFolder.id, gasto.imagenNombre, gasto.imagenBlob)
      }

      const payload = {
        id: gasto.id,
        fecha: gasto.fecha,
        id_categoria: gasto.id_categoria,
        monto: gasto.monto,
        id_moneda: gasto.id_moneda,
        id_medio_pago: gasto.id_medio_pago,
        quien: gasto.quien,
        es_reembolsable: gasto.es_reembolsable ?? false,
        comentarios: gasto.comentarios ?? null,
        imagen: gasto.imagenNombre ?? null,
        creado_en: gasto.creadoEn,
      }
      const jsonBlob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
      const nombreJson = `${gasto.archivoBase ?? `gasto_${gasto.id}`}.json`
      await uploadFile(token, carpetaRaiz.driveId, pendientesFolder.id, nombreJson, jsonBlob)

      await db.gastos.update(gasto.localId, {
        estado: 'sincronizado',
        ultimoIntentoEn: new Date().toISOString(),
        ultimoError: null,
      })
      subidos += 1
    } catch (err) {
      console.warn(`No se pudo subir el gasto ${gasto.id}:`, err)
      await db.gastos.update(gasto.localId, {
        estado: 'error',
        ultimoIntentoEn: new Date().toISOString(),
        ultimoError: String(err?.message ?? err),
      })
      fallidos += 1
    }
  }

  return { subidos, fallidos }
}
