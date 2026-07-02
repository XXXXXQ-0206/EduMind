import path from "node:path";
import type { IncomingMessage } from "node:http";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const apiPaths = [
  "/auth",
  "/chat",
  "/chats",
  "/files",
  "/quiz",
  "/quizzes",
  "/wrongbook",
  "/paper",
  "/papers",
  "/lesson-plan",
  "/lesson-plans",
  "/slides",
  "/smartnotes",
  "/podcast",
  "/podcasts",
  "/tasks",
];

function apiProxy() {
  return Object.fromEntries(
    apiPaths.map((route) => [
      route,
      {
        target: "http://localhost:5000",
        changeOrigin: true,
        bypass: (req: IncomingMessage & { headers: { accept?: string } }) => {
          if (req.headers.accept?.includes("text/html")) return req.url;
        },
      },
    ]),
  );
}

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      ...apiProxy(),
      "/ws": {
        target: "ws://localhost:5000",
        ws: true,
      },
    },
  },
  preview: {
    proxy: {
      ...apiProxy(),
      "/ws": {
        target: "ws://localhost:5000",
        ws: true,
      },
    },
  },
});
