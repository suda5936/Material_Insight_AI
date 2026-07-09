import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The backend runs on http://localhost:8000 (uvicorn default). API calls to
// /api are proxied there in dev so the browser stays same-origin.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // 저장소 루트의 demo/ 폴더를 ?raw로 import 할 수 있도록 상위 접근 허용.
    fs: { allow: [".."] },
    proxy: {
      "/api": {
        target: process.env.VITE_API_TARGET ?? "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
