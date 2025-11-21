import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
  // Exclude test files from build
  build: {
    rollupOptions: {
      external: ['vitest', '@testing-library/react', '@testing-library/jest-dom'],
    },
  },
})

