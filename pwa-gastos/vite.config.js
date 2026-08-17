import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig(({ command, isPreview }) => ({
  // "command" es 'serve' tanto para "vite dev" como para "vite preview" --
  // hay que usar "isPreview" para distinguirlos. El build real (GitHub
  // Pages) y "vite preview" (que sirve ese mismo build) necesitan el
  // mismo base; solo el dev server sirve desde la raiz.
  base: command === 'build' || isPreview ? '/finanzas-mcghr/' : '/',
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
