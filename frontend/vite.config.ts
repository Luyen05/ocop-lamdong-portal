import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    // Khi phát triển, robots.txt và sitemap.xml do backend sinh (giống Nginx ở môi trường thật).
    proxy: {
      '/robots.txt': process.env.VITE_BACKEND_ORIGIN ?? 'http://localhost:8000',
      '/sitemap.xml': process.env.VITE_BACKEND_ORIGIN ?? 'http://localhost:8000',
    },
  },
})

