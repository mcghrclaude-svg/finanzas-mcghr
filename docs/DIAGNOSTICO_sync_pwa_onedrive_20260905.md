# Diagnostico: gastos de la PWA movil no llegan a produccion desde 2026-08-23

Documento preparado para llevar a otra sesion de Claude y pedir ayuda a
resolver el problema. Se separa explicitamente que es **dato duro
verificado**, que es **lo que el usuario reporto**, y que es
**deduccion/hipotesis** de Claude (no verificada con fuente externa en
esta sesion).

Repositorio: https://github.com/mcghrclaude-svg/finanzas-mcghr
(privado; el enlace solo es util para quien ya tiene acceso)

---

## 1. Sintoma reportado por el usuario

- En la hoja de transacciones de produccion (backend de escritorio) solo
  se ven registros hasta el 22-23 de agosto de 2026.
- El usuario asegura haber seguido registrando gastos con la PWA movil
  (iPhone) desde esa fecha en adelante, y esos gastos no aparecen.

## 2. Datos duros verificados en esta sesion

Todo lo de esta seccion se obtuvo leyendo archivos y la base de datos
real directamente, sin modificar nada (consultas de solo lectura).

### 2.1 Base de datos de produccion

Archivo: `C:/Users/ghriz/OneDrive/Finanzas MCGHR/Prod/finanzas.db`

```sql
SELECT MAX(fecha), COUNT(*) FROM transacciones;
-- resultado: ('2026-08-23', 14)   -- 14 transacciones ese dia, ninguna despues
```

### 2.2 Configuracion de carpetas de import (`config_pwa_import`)

```
raices = [
  "C:\\Users\\ghriz\\OneDrive\\App Finanzas Familia",
  "C:\\Users\\ghriz\\OneDrive\\Finanzas MCGHR\\Prod"
]
```

Ambas carpetas raiz tienen subcarpetas `pendientes/` y `procesados/`.
Al inspeccionarlas:

- `pendientes/` esta **vacia** en ambas raices (al momento del chequeo).
- `procesados/` en `Finanzas MCGHR\Prod` tiene 16 archivos, el mas
  reciente con fecha de contenido **2026-08-23** (`gasto_20260823T211344051Z.json`).
- `procesados/` en `App Finanzas Familia` esta **vacia** (nunca proceso nada).

Conclusion de este punto: no hay ningun archivo JSON de gasto, en
ninguna de las dos carpetas configuradas, con fecha posterior al 23/08.
No es que se hayan quedado "atascados sin procesar" -- **nunca llegaron
a OneDrive**.

### 2.3 Tarea programada de Windows que importa esos JSON a la DB

`schtasks /Query /TN "FinanzasMCGHR_ImportPWA" /V /FO LIST`

Datos relevantes:
```
Task To Run:      C:\Users\ghriz\finanzas-mcghr\scripts\_run_import_pwa.bat
Logon Mode:       Interactive only
Schedule:         cada 10 minutos
Last Result:      0 (exito)
```

Historial de corridas (`log_ejecuciones_mobile`, tabla en la misma DB):

```
id  fecha_inicio                        archivos_leidos  nuevas  duplicados  errores
26  2026-08-22T22:50:02Z                0                0       0           0
27  2026-09-03T16:54:59Z                0                0       0           0   <- primera corrida tras el hueco
28  2026-09-03T17:10:02Z                10               10      0           0   <- proceso el backlog de Aug 23
29  2026-09-03T17:20:08Z                0                0       0           0
30  2026-09-03T20:04:14Z                0                0       0           0
```

**Hallazgo:** hay un hueco de ~11 dias (2026-08-22 22:50 -> 2026-09-03
16:54) donde la tarea programada no corrio ninguna vez, pese a estar
configurada cada 10 minutos. Es coherente con que la tarea es "Logon
Mode: Interactive only" (requiere sesion de Windows iniciada) y la PC
no estuvo con sesion activa en ese lapso.

Cuando la tarea volvio a correr (17:10:02), proceso 10 archivos -- pero
esos 10 archivos ya estaban ahi desde el 23/08 (backlog viejo), no son
gastos nuevos. Ver tabla `archivos_mobile_procesados`: los 10
`fecha_archivo` son todos del 23/08, y `fecha_procesado` es del
03/09 -- es decir, se procesaron recien hoy pero fueron *creados* el 23/08.

### 2.4 Codigo de la PWA (`pwa-gastos/`) que sube los gastos a OneDrive

Archivo `pwa-gastos/src/utils/sync.js`:

- Cada gasto se guarda primero en IndexedDB local del celular
  (`db.gastosPendientes`), **siempre**, independientemente de si la
  subida a OneDrive despues funciona o no.
- Recien despues intenta subir el JSON (y la foto si tiene) a OneDrive
  via Microsoft Graph API (`uploadFile`, en
  `pwa-gastos/src/api/graphClient.js`), usando un token obtenido con
  `getAccessToken(account)`.
- Si la subida falla por cualquier motivo, el registro **se queda** en
  `gastosPendientes` (no se borra) para reintentar despues. El error se
  loguea con `console.warn` -- no hay ningun aviso visible al usuario en
  ese momento.

Archivo `pwa-gastos/src/modules/NuevoGasto/index.jsx` (lineas ~103-113):

```js
await db.gastosPendientes.add(registro)
setGuardado(true)   // el usuario ve "Guardado" aunque la subida falle

if (isAuthenticated) {
  syncPendientes(account).catch((err) => console.warn('Sync en background fallo:', err))
}
```

Confirmado: `syncPendientes` **solo** se dispara automaticamente en dos
casos: (a) justo despues de guardar un gasto nuevo, o (b) cuando el
usuario entra manualmente a la pantalla "Gastos sin Replicar" y toca
"Sincronizar ahora". No hay ningun sync automatico al simplemente abrir
la app.

### 2.5 Configuracion de MSAL (autenticacion Microsoft) en la PWA

Archivo `pwa-gastos/src/auth/msalConfig.js`:

```js
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

export const loginRequest = {
  scopes: ['Files.ReadWrite.All'],
}
```

- `authority: consumers` -> son cuentas Microsoft personales (MSA), no
  Azure AD corporativo.
- `cacheLocation: 'localStorage'` (no `sessionStorage`, que se perderia
  al cerrar la app).
- Scope pedido: `Files.ReadWrite.All`. `offline_access`/`openid`/`profile`
  los agrega MSAL.js automaticamente (comentario propio en el archivo).

### 2.6 Screenshot del usuario (evidencia directa del error, 2026-09-05 08:17)

Pantalla "Gastos sin Replicar" mostrando:

```
Error al sincronizar: InteractionRequiredAuthError: login_required:
Silent authentication was denied. The user must first sign in and if
needed grant the client application access to the scope
'Files.ReadWrite.All openid profile offline_access'.
```

Con 2 gastos pendientes visibles, fechados **2026-09-05** (MERCADO
25.000 COP, CARRO 1.480.000 COP).

## 3. Lo que el usuario reporto (no verificado por Claude, pero tomado
como cierto)

- La primera vez que vio el error de sincronizacion, cerro sesion y
  volvio a conectarse desde la pantalla de Configuracion, y ahi si pudo
  sincronizar manualmente desde "Gastos sin Replicar".
- Al dia siguiente, volvio a aparecer el mismo error
  (`InteractionRequiredAuthError: login_required`), sin haber hecho
  ningun cambio de su lado.
- Este patron (falla -> reconectar manualmente -> funciona por un rato
  -> vuelve a fallar al dia siguiente) es consistente y repetido, no un
  evento aislado.

## 4. Deduccion de Claude (hipotesis, NO verificada con fuente externa
en esta sesion -- no se hizo web search)

Con la evidencia de las secciones 2 y 3, la cadena causal que arma
Claude es:

1. El usuario guarda un gasto -> se guarda bien en el celular -> la app
   intenta `acquireTokenSilent` para renovar el token de Microsoft y
   subir el archivo.
2. El token de acceso obtenido en el login interactivo tiene vida corta
   (tipicamente ~1 hora en el ecosistema Microsoft identity platform).
   Mientras es valido, todo sincroniza bien -- coincide con que el
   usuario logro sincronizar manualmente justo despues de reconectar.
3. Pasado ese lapso (al dia siguiente), el token de acceso ya vencio.
   `acquireTokenSilent` de MSAL.js, cuando no hay token de acceso
   vigente en cache, intenta renovar via un **iframe oculto** contra
   `login.microsoftonline.com` con `prompt=none` (SSO silencioso).
4. **Hipotesis central, no verificada aca:** ese iframe de renovacion
   silenciosa depende de las cookies de sesion de `login.microsoftonline.com`,
   y tanto (a) el modo standalone de una PWA agregada a la pantalla de
   inicio en iOS, como (b) el Intelligent Tracking Prevention (ITP) de
   Safari/WebKit, son conocidos por bloquear o particionar cookies de
   iframes de terceros -- lo que haria fallar sistematicamente ese SSO
   silencioso y produciria justo el error
   `InteractionRequiredAuthError: login_required`.
5. Esto explicaria por que el fallo es reproducible dia a dia (vida del
   token de acceso) y no un evento raro.

**Esto es conocimiento general de Claude sobre MSAL.js/Azure AD/Safari
ITP, no confirmado con documentacion oficial ni busqueda web dentro de
esta sesion.** Antes de asumirlo como causa raiz confirmada, valdria la
pena que la proxima sesion:

- Busque en la documentacion oficial de Microsoft identity platform
  (`learn.microsoft.com`, seccion MSAL.js / "acquireTokenSilent" /
  "Single-page application" / "iOS Safari" / "ITP") y en los issues del
  repo `AzureAD/microsoft-authentication-library-for-js` en GitHub,
  filtrando por `login_required` + `iOS` + `standalone` + `Safari ITP`.
- Confirme si el registro de la app en Azure Portal es tipo
  "Single-page application" (SPA, con PKCE) o "Public client / native",
  ya que el comportamiento de refresh token difiere entre ambos.
- Idealmente, capture el `errorCode`/`subError` exacto de MSAL en cada
  fallo (hoy el codigo solo hace `console.warn`, se pierde el detalle) --
  eso permitiria distinguir "refresh token vencido/revocado" de
  "storage borrado por iOS" de "bloqueo de iframe por ITP", que tienen
  fixes distintos.

## 5. Otro hallazgo relacionado (contexto, probablemente no vinculado)

Existe un issue abierto en el repo,
https://github.com/mcghrclaude-svg/finanzas-mcghr/issues/51 ("BUG C:
rubber-band iOS tapa titulo/contenido detras de status bar / Dynamic
Island"), con 2 intentos de fix el 2026-08-22 que tocaron el layout
global de `pwa-gastos` (`body`/`#root`, `position:fixed`/`absolute`).
Es la misma fecha en que arranca el problema de sync. Claude revizo el
codigo y **no encontro relacion tecnica directa** entre esos cambios de
layout y la logica de MSAL/sync -- se menciona solo por la coincidencia
de fecha, para que quien retome esto pueda descartarlo (o confirmarlo)
con mas contexto.

## 6. Opciones de fix identificadas (ninguna implementada todavia)

Ordenadas de menor a mayor esfuerzo/impacto:

**A. Visibilizar el fallo cuando ocurre (bajo esfuerzo)**
Hoy el error queda en `console.warn`, invisible salvo que el usuario
entre a "Gastos sin Replicar". Agregar un badge/contador en el Home
(`db.gastosPendientes.count()`) tipo "3 gastos sin sincronizar -- tocá
para reconectar". No arregla la causa, pero evita enterarse dias
despues.

**B. Reautenticacion proactiva al abrir la app (esfuerzo medio)**
Chequear el token al montar `App.jsx`. Si `acquireTokenSilent` tira
`InteractionRequiredAuthError`, disparar el login interactivo ahi mismo
(mientras el usuario tiene el celular en la mano abriendo la app), en
vez de esperar a que falle en medio de guardar un gasto.

**C. Diagnostico mas fino del error real (bajo esfuerzo, hacer antes
que B/D/E)**
Loguear (a un log visible en la app, no solo consola) el
`errorCode`/`subError` exacto de cada fallo silencioso. Sin este dato
no se puede saber con certeza si la causa es la del punto 4 (ITP/iframe)
u otra (ej. refresh token realmente vencido/revocado, storage de iOS
borrado, bug de MSAL version puntual, etc).

**D. Sync tambien al abrir la app, no solo al guardar un gasto (bajo
esfuerzo)**
Hoy `syncPendientes` solo se dispara al agregar un gasto nuevo. Si el
usuario no vuelve a abrir "Nuevo Gasto" en varios dias, los pendientes
previos nunca se reintentan solos. Correrlo tambien al montar la app.

**E. Sacar la dependencia de MSAL del camino critico (esfuerzo alto,
rearquitectura)**
En vez de que el celular suba el JSON directo a OneDrive con un token
delegado del usuario (que expira), mandar el gasto a un backend propio
por una API, y que sea el backend el que escriba a OneDrive/DB con
credenciales de aplicacion (no ligadas a la sesion del usuario en el
celular). Elimina el problema de raiz, pero es un cambio de arquitectura
grande.

**Recomendacion de Claude:** A + D primero (rapidos, bajo riesgo, cortan
la mayor parte del dolor), C en paralelo para confirmar la causa real
antes de invertir en B o E.

## 7. Archivos de codigo relevantes (rutas locales en el repo)

- `pwa-gastos/src/utils/sync.js`
- `pwa-gastos/src/modules/NuevoGasto/index.jsx`
- `pwa-gastos/src/modules/GastosPendientes/index.jsx`
- `pwa-gastos/src/auth/msalConfig.js`
- `pwa-gastos/src/api/graphClient.js`
- `scripts/import_pwa_gastos.py`
- `.env.prod` (raiz del repo -- no versionado, contiene rutas reales)

## 8. Lo que NO se toco en esta sesion

Todo el analisis fue de solo lectura: consultas SQL `SELECT`, lectura de
archivos y carpetas, `git log`, `schtasks /Query`, `gh issue view`. No
se modifico codigo, no se escribio en la base de datos de produccion, no
se movieron ni borraron archivos.
