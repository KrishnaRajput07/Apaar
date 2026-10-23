import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: true,
    port: 5173,
    // Allow camera: localhost is treated as secure context by browsers.
    // If accessing from another device on LAN, need HTTPS.
    // Uncomment below for HTTPS (self-signed):
    // https: { key: '', cert: '' },
  },
})
