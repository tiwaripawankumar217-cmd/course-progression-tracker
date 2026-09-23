import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: './',
  server: {
    port: 5173,
    proxy: {
      '/progress': 'http://127.0.0.1:8000',
      '/curriculum': 'http://127.0.0.1:8000',
      '/analyze': 'http://127.0.0.1:8000',
      '/lecture': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
    },
  },
  build: {
    outDir: 'dist',
  },
});
