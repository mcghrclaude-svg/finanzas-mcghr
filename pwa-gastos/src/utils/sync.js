import { db } from '../db/db'
import { useSettingsStore } from '../store/settingsStore'
import { getAccessToken, ensureFolder, uploadFile } from '../api/graphClient'

// Sube todos los gastos pendientes de IndexedDB a OneDrive. Por cada uno:
// sube el JSON y, si tiene foto, la imagen; si ambas subidas tienen exito
// borra el registro local. Si falla cualquier paso, el registro queda
// intacto para reintentar en la proxima sincronizacion.
export async function syncPendientes(account) {
  const { carpetaGastos } = useSettingsStore.getState()
  if (!carpetaGastos) return { subidos: 0, fallidos: 0, motivo: 'sin-carpeta-configurada' }
  if (!account) return { subidos: 0, fallidos: 0, motivo: 'sin-sesion' }

  const pendientes = await db.gastosPendientes.toArray()
  if (pendientes.length === 0) return { subidos: 0, fallidos: 0 }

  const token = await getAccessToken(account)
  const pendientesFolder = await ensureFolder(token, carpetaGastos.driveId, carpetaGastos.itemId, 'pendientes')

  let subidos = 0
  let fallidos = 0

  for (const gasto of pendientes) {
    try {
      if (gasto.imagenBlob && gasto.imagenNombre) {
        await uploadFile(token, carpetaGastos.driveId, pendientesFolder.id, gasto.imagenNombre, gasto.imagenBlob)
      }

      const payload = {
        id: gasto.id,
        fecha: gasto.fecha,
        id_categoria: gasto.id_categoria,
        monto: gasto.monto,
        id_moneda: gasto.id_moneda,
        id_medio_pago: gasto.id_medio_pago,
        quien: gasto.quien,
        imagen: gasto.imagenNombre ?? null,
        creado_en: gasto.creadoEn,
      }
      const jsonBlob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
      const nombreJson = `${gasto.archivoBase ?? `gasto_${gasto.id}`}.json`
      await uploadFile(token, carpetaGastos.driveId, pendientesFolder.id, nombreJson, jsonBlob)

      await db.gastosPendientes.delete(gasto.localId)
      subidos += 1
    } catch (err) {
      console.warn(`No se pudo subir el gasto ${gasto.id}:`, err)
      fallidos += 1
    }
  }

  return { subidos, fallidos }
}
