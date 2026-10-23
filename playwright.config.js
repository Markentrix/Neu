// Browser-Tests: baut die Website und liefert website-fertig/ mit einer Attrappe der Portal-Schnittstelle auf Port 8099 aus.
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
    { name: "mobil", use: { ...devices["Pixel 7"] } },
  ],
  webServer: {
    command: "python3 build/build.py --quiet && node tests/portal-mock.js",
    url: "http://127.0.0.1:8099/",
    reuseExistingServer: false,
    timeout: 60000,
  },
});
