import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    chunkSizeWarningLimit: 1900,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) {
            return undefined;
          }
          if (
            id.includes("/react/") ||
            id.includes("/react-dom/") ||
            id.includes("/scheduler/")
          ) {
            return "react-vendor";
          }
          if (id.includes("/lucide-react/")) {
            return "icons";
          }
          return undefined;
        },
      },
    },
  },
  server: {
    port: 5178,
    proxy: {
      "/api": "http://127.0.0.1:8069",
      "/health": "http://127.0.0.1:8069"
    }
  }
});
