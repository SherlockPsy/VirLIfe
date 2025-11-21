import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true
  },
  preview: {
    // Use Railway's PORT environment variable, fallback to 3000
    port: parseInt(process.env.PORT || '3000', 10),
    host: true,
    strictPort: false, // Allow port fallback if PORT is not available
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
})

