# CITA-014 -- Widget OneDrive File Picker v8 no viable para cuentas personales

**Frecuencia:** 1 vez detectada (sesion 2026-08-09, pwa-gastos, selector de carpetas de Configuracion)
**Nivel:** 3-CONTEXTO

**Error:**
Se intento integrar el widget oficial "OneDrive File Picker v8" de Microsoft (iframe +
postMessage/MessageChannel) siguiendo la documentacion publica
(https://learn.microsoft.com/en-us/onedrive/developer/controls/file-pickers/), pero la
integracion fallo en una cadena de problemas distintos, cada uno con un sintoma
diferente, antes de llegar a un bloqueo real de la plataforma:

1. El `<form>` que lanza el picker se armaba y enviaba (`form.submit()`) en el mismo
   tick sincronico del `useEffect` en que se montaba el iframe, asignando `iframe.name`
   imperativamente en ese mismo momento. El navegador no llegaba a registrar ese
   contexto de navegacion nombrado antes del submit, y en vez de fallar abria una
   pestana nueva con el `target` como nombre -- comportamiento estandar del navegador
   ante un `target` de formulario sin contexto de navegacion valido, no un error
   explicito. Fix: `name={iframeName}` directo en el JSX del `<iframe>` (disponible
   desde el primer render via `useState` lazy), nunca asignado imperativamente despues
   del mount.
2. La URL del endpoint documentada en la guia general de Microsoft Learn
   (`{baseUrl}/_layouts/15/FilePicker.aspx`) da 404 real en `onedrive.live.com`
   (confirmado en la pestana Network, no un fallo de aplicacion) -- esa ruta es para
   SharePoint/tenant. La URL real que carga el picker de consumidor es
   `onedrive.live.com/picker/v8.0/index.html`. Ademas, el JSON de opciones
   (`filePicker`) y el `locale` van en la query string de la URL del `action`, no en
   un input hidden -- al reves de lo que parecia sugerir un primer intento de fix.
3. Al usar iframe (no popup), el widget exige un input oculto `access_token` en el
   body del POST. La documentacion indica pedir ese token con scope de la API
   SharePoint (`OneDrive.ReadWrite`/`AllSites.Read`/`MyFiles.Read`/`MyFiles.Write`),
   un recurso distinto del token de Graph que ya usa el resto de la app. Al agregar
   esos permisos en el App Registration de Azure y pedir el token, la respuesta fue
   `AADSTS9002332`: esa API de SharePoint esta bloqueada explicitamente para cuentas
   personales bajo `/consumers` -- solo funciona con cuentas corporativas/Azure AD.
   Confirmado por el mensaje de error oficial de Microsoft, no una suposicion.

**Resolucion:**
Se abandono el widget oficial y se reemplazo por un selector de carpetas propio sobre
Graph API directa (`GET /me/drive` + `GET /drives/{driveId}/items/{itemId}/children`,
navegacion con breadcrumb), usando el mismo token de Graph (`Files.ReadWrite.All`) que
ya usa el resto de la app. Ver ADR-014 para el detalle de la decision.

**Prevencion:**
Antes de integrar el OneDrive File Picker v8 (o un widget similar de Microsoft) para
una app de cuenta personal/consumidor:
- Verificar el bloqueo AADSTS9002332 (API de SharePoint no disponible para cuentas
  `/consumers`) ANTES de invertir tiempo en el flujo de iframe -- es un bloqueo de
  plataforma, no de configuracion
- Si el caso de uso es solo "elegir una carpeta" (no buscar/subir archivos con la UI
  rica del widget), un selector propio sobre Graph API directa es mas simple y evita
  esta clase entera de problemas
- No confiar en la URL de endpoint de la documentacion general de Microsoft Learn sin
  verificar en la pestana Network -- la doc mezcla el caso SharePoint/tenant con el de
  consumidor sin distinguir claramente cual URL corresponde a cual

**Senal de alarma para Hernan:**
Si aparece un error `AADSTS9002332` al pedir un token, es este bloqueo especifico (API
no disponible para cuentas personales) -- no es un problema de permisos mal
configurados, ningun scope adicional lo resuelve.
