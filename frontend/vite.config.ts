import { sentryVitePlugin } from '@sentry/vite-plugin';
import tailwindcss from '@tailwindcss/vite';
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
    watch:
      process.env.VITE_USE_POLLING === 'true'
        ? {
            ignored: ['**/volumes/**'],
            usePolling: true,
            interval: 1000,
          }
        : {
            ignored: ['**/volumes/**'],
          },
  },
  plugins: [
    tailwindcss(),
    react(),
    sentryVitePlugin({
      authToken: process.env.SENTRY_AUTH_TOKEN,
      org: 'fabslab',
      project: 'thd-bubble',
    }),
  ].filter(Boolean),
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    sourcemap: true, // Source map generation must be turned on
  },
}));
