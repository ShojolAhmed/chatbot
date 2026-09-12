import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // During local development, proxy /api to the backend so the frontend
    // can call same-origin `/api/chat` without CORS configuration.
    // Adjust the target to match your backend's dev server, or set
    // VITE_API_BASE_URL instead if the backend lives on a different origin.
    proxy: {
      '/api': {
        target: process.env.VITE_DEV_PROXY_TARGET || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
