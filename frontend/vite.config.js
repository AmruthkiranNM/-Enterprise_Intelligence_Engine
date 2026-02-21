import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
    plugins: [react()],
    server: {
        port: 5173,
        open: true,
        proxy: {
            "/analyze-domain": "http://localhost:8000",
            "/analyze-region": "http://localhost:8000",
        },
    },
});
