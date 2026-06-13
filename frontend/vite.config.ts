import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        // Split heavy map libraries into dedicated chunks so the main bundle
        // stays well under the 500 kB Vite warning threshold.
        manualChunks(id) {
          if (id.includes('maplibre-gl')) return 'vendor-maplibre';
          if (id.includes('mapbox-gl')) return 'vendor-mapbox';
          if (id.includes('framer-motion')) return 'vendor-motion';
        },
      },
    },
  },
})
