import react from '@vitejs/plugin-react-swc';
import path from 'path';
import { defineConfig } from 'vite';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: '::',
    port: 8080,
    allowedHosts: ['fabian-local-dev.treibhausdonaufeld.at'],
    // Proxy API requests to Django backend
    proxy: {
      '/api/ws/': {
        target: process.env.VITE_PROXY_URL || 'http://localhost:8000',
        changeOrigin: false,
        ws: true,
        secure: false,
      },
      '^/(api|static|admin|accounts|media)/.*': {
        target: process.env.VITE_PROXY_URL || 'http://localhost:8000',
        changeOrigin: false,
        secure: false,
      },
    },

    // Prevent watching Docker-mounted DB/storage volumes that can’t be watched (EINVAL)
    watch: {
      ignored: ['**/volumes/**'],
      // If issues persist in certain environments, enable polling:
      // usePolling: true,
      // interval: 1000,
    },
  },
  plugins: [react()].filter(Boolean),
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
}));
