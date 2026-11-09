import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig, devices } from '@playwright/test'

const frontendDir = path.dirname(fileURLToPath(import.meta.url))
const projectRoot = path.resolve(frontendDir, '..')
const backendDir = path.join(projectRoot, 'backend')

const pythonBin =
  process.platform === 'win32'
    ? path.join(backendDir, '.venv', 'Scripts', 'python.exe')
    : path.join(backendDir, '.venv', 'bin', 'python')

// Keep in step with e2e/global-setup.ts: E2E_SEED=demo points the backend at
// the demo database the screenshot capture runs against.
const e2eDatabaseUrl =
  process.env.E2E_DATABASE_URL ??
  (process.env.E2E_SEED === 'demo'
    ? 'postgresql+asyncpg://postgres:postgres@localhost:5432/fintech_ops_demo'
    : 'postgresql+asyncpg://postgres:postgres@localhost:5432/fintech_ops_e2e')

export default defineConfig({
  testDir: './e2e/tests',
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [['list'], ['html', { open: 'never' }]],
  timeout: 60_000,
  expect: { timeout: 10_000 },
  globalSetup: './e2e/global-setup.ts',
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      command: `"${pythonBin}" -m uvicorn app.main:app --host 127.0.0.1 --port 8000`,
      cwd: backendDir,
      url: 'http://127.0.0.1:8000/health',
      reuseExistingServer: !process.env.CI,
      env: {
        ...process.env,
        DATABASE_URL: e2eDatabaseUrl,
        DEBUG: 'true',
        APP_ENV: 'development',
        JWT_SECRET_KEY: process.env.JWT_SECRET_KEY ?? 'e2e-test-secret-key-minimum-32-characters',
      },
    },
    {
      command: 'npm run dev -- --host 127.0.0.1 --port 5173',
      cwd: frontendDir,
      url: 'http://127.0.0.1:5173',
      reuseExistingServer: !process.env.CI,
    },
  ],
})
