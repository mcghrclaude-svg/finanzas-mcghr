import { InteractionRequiredAuthError } from '@azure/msal-browser'
import db from '../db/db'

// Diagnostico de errores de acquireTokenSilent: hoy se pierden en un
// console.warn generico y no alcanza para saber por que la sesion de
// OneDrive se corta a las pocas horas.
export async function logAuthError(err, contexto) {
  const registro = {
    timestamp: new Date().toISOString(),
    contexto,
    errorCode: err?.errorCode ?? null,
    subError: err?.subError ?? null,
    errorMessage: err?.errorMessage ?? err?.message ?? null,
    esInteractionRequired: err instanceof InteractionRequiredAuthError,
    nombre: err?.name ?? null,
  }

  console.warn(`[authLog] ${contexto}:`, registro)

  try {
    await db.logSync.add(registro)
  } catch (dbErr) {
    console.warn('[authLog] no se pudo guardar en logSync:', dbErr)
  }
}
