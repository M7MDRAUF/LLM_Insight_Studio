import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright configuration for LLM Insight Studio.
 * Smoke tests run against the running Next.js dev server (port 3000).
 * The API backend is expected at http://localhost:8000.
 *
 * To run: npx playwright test
 * CI: set BASE_URL env var to override the default.
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  retries: 0,
  workers: 1,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: process.env.BASE_URL ?? "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  // Start Next.js dev server automatically when running e2e tests.
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: true,
    timeout: 60_000,
  },
});
