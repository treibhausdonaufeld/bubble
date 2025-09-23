
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import dotenv from 'dotenv'
import path from 'path'
import { defineConfig } from 'vite'

// Load environment variables
dotenv.config({ path: './frontend/environments/.env.development' })

export default defineConfig({
  root: './frontend',
  base: '/static/',
  server: {
    port: 5173,
    host: '127.0.0.1',
    cors: true
  },
  plugins: [
    react(),
    tailwindcss()
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './frontend'),
      'images': path.resolve(__dirname, './frontend/src/images'),
    },
    extensions: ['.js', '.jsx', '.ts', '.tsx'],
  },
  build: {
    outDir: path.resolve(__dirname, './assets'),
    assetsDir: 'productionAssets',
    emptyOutDir: true, // Empty the output directory before build
    manifest: "manifest.json",
    rollupOptions: {
      input: {
        mainAssets: './main.tsx',
      },
    },
    sourcemap: true, // Generate source maps for development
  },
  define: {
    'process.env': JSON.stringify(process.env),
  },
})
