import { msalInstance, loginRequest } from '../auth/msalConfig'
import { logAuthError } from '../utils/authLog'

const GRAPH_BASE = 'https://graph.microsoft.com/v1.0'

export async function getAccessToken(account) {
  try {
    const result = await msalInstance.acquireTokenSilent({ ...loginRequest, account })
    return result.accessToken
  } catch (err) {
    await logAuthError(err, 'graphClient.getAccessToken')
    throw err
  }
}

async function graphFetch(token, path, options = {}) {
  const res = await fetch(`${GRAPH_BASE}${path}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  })
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`Graph API ${res.status} en ${path}: ${body}`)
  }
  return res
}

// Id del drive personal del usuario logueado -- lo necesita el selector de
// carpetas propio para armar las mismas llamadas /drives/{driveId}/... que
// usa el resto de la app (ensureFolder, uploadFile, downloadItemContent).
export async function getMyDriveId(token) {
  const res = await graphFetch(token, '/me/drive?$select=id')
  const data = await res.json()
  return data.id
}

export async function listChildren(token, driveId, itemId) {
  const res = await graphFetch(token, `/drives/${driveId}/items/${itemId}/children?$select=id,name,folder`)
  const data = await res.json()
  return data.value ?? []
}

// Idempotente: si ya existe una carpeta con ese nombre bajo el padre, la reusa.
export async function ensureFolder(token, driveId, parentId, name) {
  const children = await listChildren(token, driveId, parentId)
  const existing = children.find((c) => c.folder && c.name === name)
  if (existing) return { id: existing.id, name: existing.name }

  const res = await graphFetch(token, `/drives/${driveId}/items/${parentId}/children`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name,
      folder: {},
      '@microsoft.graph.conflictBehavior': 'rename',
    }),
  })
  const created = await res.json()
  return { id: created.id, name: created.name }
}

// Subida simple (archivos chicos, no hace falta upload session).
export async function uploadFile(token, driveId, parentId, filename, blob) {
  const res = await graphFetch(
    token,
    `/drives/${driveId}/items/${parentId}:/${encodeURIComponent(filename)}:/content`,
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/octet-stream' },
      body: blob,
    }
  )
  return res.json()
}

export async function findChildByName(token, driveId, parentId, name) {
  const children = await listChildren(token, driveId, parentId)
  return children.find((c) => c.name === name) ?? null
}

export async function downloadItemContent(token, driveId, itemId) {
  const res = await graphFetch(token, `/drives/${driveId}/items/${itemId}/content`)
  return res
}
