import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import { execSync } from 'node:child_process'

// Hash corto del commit actual, para mostrar en pantalla y poder
// confirmar desde el celular si una actualizacion ya llego. Si git no
// esta disponible (build fuera de un checkout) cae a 'dev'.
function commitHash() {
  try {
    return execSync('git rev-parse --short HEAD').toString().trim()
  } catch {
    return 'dev'
  }
}

// Fecha/hora del commit actual en ISO 8601 (con el offset propio del
// autor) -- se normaliza a America/Bogota recien al mostrarla en
// pantalla (Home/index.jsx), no aca.
function commitDate() {
  try {
    return execSync('git log -1 --format=%cI').toString().trim()
  } catch {
    return ''
  }
}

export default defineConfig(({ command, isPreview }) => ({
  // "command" es 'serve' tanto para "vite dev" como para "vite preview" --
  // hay que usar "isPreview" para distinguirlos. El build real (GitHub
  // Pages) y "vite preview" (que sirve ese mismo build) necesitan el
  // mismo base; solo el dev server sirve desde la raiz.
  base: command === 'build' || isPreview ? '/finanzas-mcghr/' : '/',
  define: {
    __APP_VERSION__: JSON.stringify(commitHash()),
    __APP_BUILD_DATE__: JSON.stringify(commitDate()),
  },
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['apple-touch-icon.png'],
      manifest: {
        name: 'Gastos MCGHR',
        short_name: 'Gastos',
        description: 'Captura rapida de gastos personales',
        theme_color: '#1e40af',
        background_color: '#ffffff',
        display: 'standalone',
        orientation: 'portrait-primary',
        icons: [
          { src: 'pwa-192x192.png', sizes: '192x192', type: 'image/png' },
          { src: 'pwa-512x512.png', sizes: '512x512', type: 'image/png' },
        ],
      },
      workbox: {
        // Cache de assets estaticos; llamadas a Graph API NO se cachean
        globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
        runtimeCaching: [],
      },
    }),
  ],
  resolve: {
    alias: { '@': '/src' },
  },
}))
