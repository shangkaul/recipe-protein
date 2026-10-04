import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['icon-192.png', 'icon-512.png'],
      manifest: {
        name: 'Protein Pantry',
        short_name: 'Protein Pantry',
        description: 'Find practical higher-protein meals from ingredients you already have.',
        theme_color: '#315c49',
        background_color: '#f5f4ef',
        display: 'standalone',
        start_url: '/',
        icons: [
          { src: '/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: '/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        navigateFallback: '/index.html',
        runtimeCaching: [{
          urlPattern: /^https:\/\/theunitools\.com\/recipes\//,
          handler: 'CacheFirst',
          options: { cacheName: 'recipe-photos', expiration: { maxEntries: 40, maxAgeSeconds: 604800 } },
        }],
      },
    }),
  ],
  server: {
    proxy: { '/api': 'http://127.0.0.1:5001' },
  },
})
