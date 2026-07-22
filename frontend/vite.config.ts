import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    // Allow LAN / public tunnel (http://11gv92qt74799.vicp.fun -> 10.0.0.110:28)
    allowedHosts: ['11gv92qt74799.vicp.fun', '10.0.0.110', 'localhost', '127.0.0.1'],
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
        // Streaming chat survives public-tunnel latency.
        proxyTimeout: 600000,
        timeout: 600000,
      },
    },
  },
})
