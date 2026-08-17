# CITA-018 -- Base path de Vite para GitHub Pages: condicional por comando, no por PROD

**Frecuencia:** 1 vez detectada (sesion 2026-08-16, pwa-gastos, deploy a GitHub Pages)
**Nivel:** 3-CONTEXTO

**Error:**
La PWA se publica en GitHub Pages bajo una subruta
(`https://mcghrclaude-svg.github.io/finanzas-mcghr/`), lo que requiere
`base: '/finanzas-mcghr/'` en la config de Vite -- pero solo para el build
que efectivamente se sirve desde ahi. Dos problemas relacionados, no uno
solo:

1. El criterio ingenuo de usar `base` condicional solo por `command === 'build'`
   deja afuera a `vite preview`, que sirve ese mismo build de produccion
   localmente (para probarlo antes de deployar) y tambien necesita la
   subruta -- `vite dev` (servidor de desarrollo con hot reload) es el unico
   caso que debe usar `/`. La distincion correcta es `command === 'build' || isPreview`,
   no simplemente `command === 'build'`.
2. `import.meta.env.BASE_URL` (que ya refleja el `base` resuelto) no se puede
   usar directo para calcular el `redirectUri` de MSAL: siempre trae una
   barra final (`/finanzas-mcghr/`), y Azure exige match exacto contra el
   Redirect URI registrado en el App Registration -- si ese registro no
   tiene la barra final, el login falla. Hay que calcularlo aparte segun
   `import.meta.env.PROD` (`pwa-gastos/src/auth/msalConfig.js`).

**Resolucion:**
`pwa-gastos/vite.config.js`: `base: command === 'build' || isPreview ? '/finanzas-mcghr/' : '/'`.
`msalConfig.js`: `redirectUri` calculado a mano
(`window.location.origin + '/finanzas-mcghr/'` en `PROD`, `window.location.origin`
en dev), no derivado de `BASE_URL`.

**Prevencion:**
En cualquier Vite app que se publique bajo una subruta (GitHub Pages,
subpath de un dominio), verificar el comportamiento de `base` para los tres
comandos (`dev`, `build`, `preview`) por separado, no asumir que
`command === 'build'` cubre todos los casos que sirven el build de
produccion. Si algun valor externo (OAuth redirect URI, URLs absolutas)
necesita coincidir exactamente con el origen + base, calcularlo a mano en
vez de concatenar `BASE_URL` directamente -- revisar si trae o no barra
final antes de asumirlo.

**Senal de alarma para Hernan:**
Si `npm run preview` en `pwa-gastos/` muestra la pantalla en blanco o con
assets rotos (mientras que `npm run dev` funciona bien), es este problema
de `base`. Si el login con Microsoft falla solo en el deploy publicado (y
funciona en local), revisar que el Redirect URI en Azure Portal coincida
caracter por caracter (incluida la barra final) con lo que genera
`msalConfig.js`.
