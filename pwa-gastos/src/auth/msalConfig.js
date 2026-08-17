import { PublicClientApplication } from '@azure/msal-browser'

// BASE_URL siempre trae '/' al final; Azure exige match exacto contra el
// Redirect URI registrado (http://localhost:5173 sin barra en dev), asi
// que el redirectUri se calcula a mano en vez de usar import.meta.env.BASE_URL.
const redirectUri = import.meta.env.PROD
  ? window.location.origin + '/finanzas-mcghr/'
  : window.location.origin

export const msalConfig = {
  auth: {
    clientId: import.meta.env.VITE_MSAL_CLIENT_ID,
    authority: 'https://login.microsoftonline.com/consumers',
    redirectUri,
  },
  cache: {
    cacheLocation: 'localStorage',
    storeAuthStateInCookie: false,
  },
}

// offline_access ya lo pide MSAL.js automaticamente en cada login junto
// con openid/profile/email; declararlo a mano puede devolver un error de
// la plataforma de identidad.
export const loginRequest = {
  scopes: ['Files.ReadWrite.All'],
}

export const msalInstance = new PublicClientApplication(msalConfig)

// El picker de OneDrive corre sobre recursos de SharePoint/OneDrive, no
// Graph -- no se puede reusar el token de Files.ReadWrite.All. Este helper
// pide un token para cualquier scope puntual (ej. el resource que manda el
// propio picker en el comando "authenticate").
export async function acquireToken(account, scopes) {
  const result = await msalInstance.acquireTokenSilent({ scopes, account })
  return result.accessToken
}
