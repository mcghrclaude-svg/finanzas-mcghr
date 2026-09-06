import { db } from '../db/db'
import { getAccessToken, findChildByName, downloadItemContent } from './graphClient'

const CACHE_KEY = 'resumenCategorias'
const VACIO = { mes: null, total: null, categorias: [] }

export async function getResumenCategoriasCache() {
  const row = await db.catalogosCache.get(CACHE_KEY)
  return row?.data ?? VACIO
}

async function setResumenCategoriasCache(data) {
  await db.catalogosCache.put({ key: CACHE_KEY, data, actualizadoEn: new Date().toISOString() })
}

// Descarga resumen_categorias.json desde la subcarpeta Resumen/ de la raiz
// configurada y la cachea en IndexedDB -- mismo patron offline-first que
// catalogos.js. La PWA no llama al backend por HTTP directo (ver
// docs/architecture.md, decision de Jun 2026): el resumen de presupuesto
// por categoria se exporta a este archivo desde pwa_export_service.py.
export async function sincronizarResumenCategorias(account, carpetaRaiz) {
  if (!carpetaRaiz) return getResumenCategoriasCache()

  try {
    const token = await getAccessToken(account)
    const carpetaResumen = await findChildByName(token, carpetaRaiz.driveId, carpetaRaiz.itemId, 'Resumen')
    if (!carpetaResumen) throw new Error('La carpeta Resumen no existe todavia bajo la raiz configurada')

    const item = await findChildByName(token, carpetaRaiz.driveId, carpetaResumen.id, 'resumen_categorias.json')
    if (!item) throw new Error('resumen_categorias.json no existe en la carpeta Resumen')

    const res = await downloadItemContent(token, carpetaRaiz.driveId, item.id)
    const data = await res.json()
    await setResumenCategoriasCache(data)
    return data
  } catch (err) {
    console.warn('No se pudo descargar resumen_categorias.json, usando cache local:', err)
    return getResumenCategoriasCache()
  }
}

// Solo para pruebas en dev/desktop sin backend real: carga el fixture
// servido desde public/sample-data/.
export async function cargarResumenCategoriasDeEjemplo() {
  const res = await fetch(`${import.meta.env.BASE_URL}sample-data/resumen_categorias.sample.json`)
  const data = await res.json()
  await setResumenCategoriasCache(data)
  return data
}
