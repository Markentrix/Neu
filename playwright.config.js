// Browser-Tests: startet den echten ElbDetail-Server mit Testdaten auf Port 8099.
const { defineConfig, devices } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "tests",
  testMatch: /.*\.spec\.js/,
  timeout: 30000,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: "http://127.0.0.1:8099",
    launchOptions: process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {},
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"], viewport: { width: 1366, height: 900 } } },
    { name: "mobil", use: { ...devices["Pixel 7"] }, testIgnore: /admin/ },
  ],
  webServer: {
    command: "bash tests/e2e-server.sh",
    url: "http://127.0.0.1:8099/api/health",
    reuseExistingServer: false,
    timeout: 60000,
  },
});
