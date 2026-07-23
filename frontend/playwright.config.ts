import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig, devices } from "@playwright/test";

const frontendDirectory = path.dirname(fileURLToPath(import.meta.url));
const repositoryRoot = path.resolve(frontendDirectory, "..");
const port = Number(process.env.PRINTORA_E2E_PORT ?? "18069");
const baseURL = `http://127.0.0.1:${port}`;
const dataDirectory =
  process.env.PRINTORA_E2E_DATA_DIR ??
  path.join(repositoryRoot, ".artifacts", "e2e", "data");
const artifactDirectory =
  process.env.PRINTORA_E2E_ARTIFACT_DIR ??
  path.join(repositoryRoot, ".artifacts", "e2e");
const distDirectory =
  process.env.PRINTORA_E2E_DIST_DIR ??
  path.join(artifactDirectory, "dist");

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  expect: { timeout: 8_000 },
  fullyParallel: false,
  workers: 1,
  repeatEach: Number(process.env.PRINTORA_E2E_REPEAT_EACH ?? "1"),
  retries: 0,
  forbidOnly: true,
  outputDir: path.join(artifactDirectory, "test-results"),
  reporter: [
    ["line"],
    ["json", { outputFile: path.join(artifactDirectory, "results.json") }],
    ["html", { outputFolder: path.join(artifactDirectory, "html"), open: "never" }],
  ],
  use: {
    baseURL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "desktop-chromium",
      use: { ...devices["Desktop Chrome"], colorScheme: "dark" },
    },
    {
      name: "mobile-chromium",
      use: { ...devices["Pixel 7"], colorScheme: "light" },
    },
  ],
  webServer: {
    command: [
      "cd ../backend",
      "&&",
      "uv run uvicorn app.main:app",
      "--host 127.0.0.1",
      `--port ${port}`,
    ].join(" "),
    url: `${baseURL}/health`,
    timeout: 120_000,
    reuseExistingServer: false,
    env: {
      ...process.env,
      PRINTORA_DATA_DIR: dataDirectory,
      PRINTORA_FRONTEND_DIST_DIR: distDirectory,
      PRINTORA_HOST_AUDIT_MODE: "disabled",
      PRINTORA_RELEASE_SOURCE_MODE: "disabled",
      PRINTORA_FIRMWARE_BUILD_MODE: "disabled",
      PRINTORA_PAYMENT_MODE: "sandbox",
      PRINTORA_PAYMENT_WEBHOOK_SECRET: ["e2e", "synthetic", "webhook"].join("-"),
    },
  },
});
