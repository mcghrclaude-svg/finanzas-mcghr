import React from 'react'
import ReactDOM from 'react-dom/client'
import { MsalProvider } from '@azure/msal-react'
import { msalInstance } from './auth/msalConfig'
import App from './App'
import './index.css'

// msal-browser v3 exige initialize() antes de cualquier otra llamada, y
// handleRedirectPromise() completa el login luego de loginRedirect(). Va
// en una IIFE async (no top-level await) porque el target de build incluye
// Safari 14 (iOS), que no soporta top-level await.
async function bootstrap() {
  await msalInstance.initialize()
  await msalInstance.handleRedirectPromise().catch((err) => {
    console.error('Error completando el login redirect:', err)
  })

  // Solo en dev: permite debuggear MSAL a mano desde la consola (probar
  // scopes distintos, inspeccionar cuentas/cache) sin tener que redesplegar.
  if (import.meta.env.DEV) {
    window.msalInstance = msalInstance
  }

  const accounts = msalInstance.getAllAccounts()
  if (accounts.length > 0) {
    msalInstance.setActiveAccount(accounts[0])
  }

  ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
      <MsalProvider instance={msalInstance}>
        <App />
      </MsalProvider>
    </React.StrictMode>
  )
}

bootstrap()
