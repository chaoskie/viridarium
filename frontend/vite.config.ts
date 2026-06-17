import process from "node:process";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// /api is proxied to the FastAPI backend during development (E1 walking skeleton).
const BACKEND_URL = "http://localhost:8000";
// The Playwright acceptance suite serves this build via `vite preview` and runs the
// backend on a dedicated port (E2E_BACKEND_PORT, default 8799 - never 8000, so a
// stray `vite preview` can't silently proxy onto a dev backend).
const PREVIEW_BACKEND_URL = `http://localhost:${process.env.E2E_BACKEND_PORT ?? "8799"}`;

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    proxy: {
      "/api": {
        target: BACKEND_URL,
        changeOrigin: true,
      },
    },
  },
  // `vite preview` serves the production build for the Playwright acceptance suite
  // (TEST-009); mirror the dev `/api` proxy so the built app reaches the backend.
  preview: {
    proxy: {
      "/api": {
        target: PREVIEW_BACKEND_URL,
        changeOrigin: true,
      },
    },
  },
  build: {
    // FE-007 bundle budget: fail the build if a chunk grows past the budget.
    chunkSizeWarningLimit: 300,
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
    css: true,
    include: ["src/**/*.test.{ts,tsx}"],
  },
});
