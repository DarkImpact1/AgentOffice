import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
    allowedHosts: ['localhost', '.onrender.com', '.railway.app', '.vercel.app'],
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/ws': {
        target: process.env.VITE_API_URL?.replace('https', 'wss') || 'ws://localhost:8000',
        ws: true,
      },
    },
  },
  preview: {
    port: 3000,
    host: true,
    allowedHosts: ['localhost', '.onrender.com', '.railway.app', '.vercel.app'],
  },
  define: {
    'import.meta.env.VITE_API_URL': JSON.stringify(process.env.VITE_API_URL || 'http://localhost:8000'),
  },
})
