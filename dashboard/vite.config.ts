import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: Number(process.env.FRONTEND_PORT) || 3000,
    proxy: {
      '/api': {
        configure(proxy) { proxy.on('proxyReq', (upstream, req, res) => { req.once('aborted', () => upstream.destroy()); res.once('close', () => { if (!('writableEnded' in res) || !res.writableEnded) upstream.destroy(); }); }); },
        target: process.env.API_URL || `http://127.0.0.1:${process.env.BACKEND_PORT || 8000}`,
        changeOrigin: true,
      },
    },
  },
})
