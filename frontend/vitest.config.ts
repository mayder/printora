import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    alias: {
      "@sindarius/gcodeviewer": fileURLToPath(
        new URL("./tests/stubs/gcodeviewer.ts", import.meta.url),
      ),
    },
  },
  test: {
    environment: "jsdom",
    include: ["tests/unit/**/*.test.ts"],
    setupFiles: ["tests/setup.ts"],
    coverage: {
      provider: "istanbul",
      include: ["src/**/*.{ts,tsx}"],
      exclude: [
        "src/**/*.d.ts",
        "src/types/**",
        "src/screens/ScreenProps.ts",
      ],
      reporter: ["text", "json-summary", "lcov"],
      reportsDirectory: process.env.PRINTORA_COVERAGE_DIR ?? "coverage",
      thresholds: {
        statements: 1.7,
        branches: 1.5,
        functions: 1.0,
        lines: 1.7,
        "src/services/http.ts": {
          statements: 80,
          branches: 75,
          functions: 90,
          lines: 80,
        },
        "src/components/monitoring/gcodePreview.ts": {
          statements: 92,
          branches: 80,
          functions: 100,
          lines: 100,
        },
        "src/utils/sequentialPoll.ts": {
          statements: 100,
          branches: 65,
          functions: 100,
          lines: 100,
        },
      },
    },
  },
});
