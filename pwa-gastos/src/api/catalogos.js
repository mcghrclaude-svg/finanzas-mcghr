import { db } from '../db/db'
import { getAccessToken, findChildByName, downloadItemContent } from './graphClient'

const CACHE_KEY = 'catalogos'
const VACIO = { categorias: [], medios_de_pago: [], monedas: [] }

export async function getCatalogosCache() {
  const row = await db.catalogosCache.get(CACHE_KEY)
  return row?.data ?? VACIO
}

async function setCatalogosCache(data) {
  await db.catalogosCache.put({ key: CACHE_KEY, data, actualizadoEn: new Date().toISOString() })
}

// Descarga catalogos.json desde la carpeta de catalogos configurada y la
// cachea en IndexedDB. Si falla (sin conexion, carpeta sin configurar,
// archivo inexistente), devuelve la ultima version cacheada.
export async function sincronizarCatalogos(account, carpetaCatalogos) {
  if (!carpetaCatalogos) return getCatalogosCache()

  try {
    const token = await getAccessToken(account)
    const item = await findChildByName(token, carpetaCatalogos.driveId, carpetaCatalogos.itemId, 'catalogos.json')
    if (!item) throw new Error('catalogos.json no existe en la carpeta configurada')

    const res = await downloadItemContent(token, carpetaCatalogos.driveId, item.id)
    const data = await res.json()
    await setCatalogosCache(data)
    return data
  } catch (err) {
    console.warn('No se pudo descargar catalogos.json, usando cache local:', err)
    return getCatalogosCache()
  }
}

// Solo para pruebas en dev/desktop sin backend real: carga el fixture
// servido desde public/sample-data/.
export async function cargarCatalogosDeEjemplo() {
  const res = await fetch(`${import.meta.env.BASE_URL}sample-data/catalogos.sample.json`)
  const data = await res.json()
  await setCatalogosCache(data)
  return data
}
