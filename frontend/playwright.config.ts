import { defineConfig, devices } from "@playwright/test";

const edgeChannel = process.platform === "win32" ? { channel: "msedge" as const } : {};

export default defineConfig({
  testDir: "./src/tests/e2e",
  timeout: 30_000,
  expect: {
    timeout: 7_000,
  },
  fullyParallel: false,
  reporter: [["list"]],
  use: {
    baseURL: "http://127.0.0.1:5173",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: {
    command: "npm run dev -- --host 127.0.0.1 --port 5173",
    url: "http://127.0.0.1:5173",
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
  },
  projects: [
    {
      name: "desktop",
      use: {
        ...devices["Desktop Chrome"],
        ...edgeChannel,
      },
    },
    {
      name: "mobile",
      use: {
        ...devices["Pixel 5"],
        ...edgeChannel,
      },
    },
  ],
});
