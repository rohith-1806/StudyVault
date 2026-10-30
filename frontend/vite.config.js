import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const backendTarget = env.VITE_BACKEND_URL || env.BACKEND_URL || 'http://127.0.0.1:5000'

  return {
    plugins: [react()],
    server: {
      port: 5173,
      host: '0.0.0.0',
      allowedHosts: [
        'gag-thrive-parsley.ngrok-free.dev',
      ],
      proxy: {
        '/api': {
          target: backendTarget,
          changeOrigin: true,
          secure: false,
          configure: (proxy, _options) => {
            proxy.on('error', (err, req, res) => {
              if (err.code === 'ECONNREFUSED') {
                console.warn(`[vite proxy] Backend unreachable at ${backendTarget} for ${req.url} (ECONNREFUSED)`);
              } else {
                console.warn(`[vite proxy] Proxy warning for ${req.url}:`, err.message);
              }
              if (res && !res.headersSent && typeof res.writeHead === 'function') {
                res.writeHead(503, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({
                  error: 'Backend service is currently unavailable. Please ensure the Flask backend server is running.',
                  code: 'BACKEND_UNAVAILABLE'
                }));
              }
            });
          },
        },
      },
    },
  }
})
