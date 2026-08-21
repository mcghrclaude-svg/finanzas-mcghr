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

// Descarga catalogos.json desde la subcarpeta Catalogos/ de la raiz
// configurada y la cachea en IndexedDB. Si falla (sin conexion, raiz sin
// configurar, archivo inexistente), devuelve la ultima version cacheada.
export async function sincronizarCatalogos(account, carpetaRaiz) {
  if (!carpetaRaiz) return getCatalogosCache()

  try {
    const token = await getAccessToken(account)
    const carpetaCatalogos = await findChildByName(token, carpetaRaiz.driveId, carpetaRaiz.itemId, 'Catalogos')
    if (!carpetaCatalogos) throw new Error('La carpeta Catalogos no existe todavia bajo la raiz configurada')

    const item = await findChildByName(token, carpetaRaiz.driveId, carpetaCatalogos.id, 'catalogos.json')
    if (!item) throw new Error('catalogos.json no existe en la carpeta Catalogos')

    const res = await downloadItemContent(token, carpetaRaiz.driveId, item.id)
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
