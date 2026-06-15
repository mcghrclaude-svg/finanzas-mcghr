import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig(({ mode }) => {
  const apiPort = mode === 'test' ? 8001 : mode === 'staging' ? 8003 : 8000

  return {
    plugins: [
      react(),
      VitePWA({
        registerType: 'autoUpdate',
        includeAssets: ['favicon.ico', 'apple-touch-icon.png'],
        manifest: {
          name: 'Finanzas MCGHR',
          short_name: 'Finanzas',
          description: 'Gestión financiera familiar MCGHR',
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
          // Cache de assets estáticos; API requests NO se cachean
          globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
          runtimeCaching: [],
        },
      }),
    ],
    server: {
      proxy: {
        '/api': {
          target: `http://localhost:${apiPort}`,
          changeOrigin: true,
        },
      },
    },
    resolve: {
      alias: { '@': '/src' },
    },
  }
})
