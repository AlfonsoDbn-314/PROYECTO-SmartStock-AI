import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Proxy /api → backend FastAPI (http://localhost:8000), reescribiendo el prefijo.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8080",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
