import { execSync } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const rootDir = path.dirname(fileURLToPath(import.meta.url))
const projectRoot = path.resolve(rootDir, '../..')
const backendDir = path.join(projectRoot, 'backend')
const python =
  process.platform === 'win32'
    ? path.join(backendDir, '.venv', 'Scripts', 'python.exe')
    : path.join(backendDir, '.venv', 'bin', 'python')

// E2E_SEED=demo switches the run to the portfolio demo dataset
// (backend/scripts/seed_demo.py, its own fintech_ops_demo database) for the
// screenshot capture. Anything else keeps the deterministic test fixture.
const useDemoSeed = process.env.E2E_SEED === 'demo'

const databaseUrl =
  process.env.E2E_DATABASE_URL ??
  (useDemoSeed
    ? 'postgresql+asyncpg://postgres:postgres@localhost:5432/fintech_ops_demo'
    : 'postgresql+asyncpg://postgres:postgres@localhost:5432/fintech_ops_e2e')

export default async function globalSetup() {
  const alembic = process.platform === 'win32' ? 'alembic.exe' : 'alembic'
  const alembicBin = path.join(backendDir, '.venv', process.platform === 'win32' ? 'Scripts' : 'bin', alembic)

  execSync(`"${alembicBin}" upgrade head`, {
    cwd: backendDir,
    env: { ...process.env, DATABASE_URL: databaseUrl },
    stdio: 'inherit',
  })

  execSync(`"${python}" scripts/${useDemoSeed ? 'seed_demo.py' : 'seed_e2e.py'}`, {
    cwd: backendDir,
    env: { ...process.env, DATABASE_URL: databaseUrl },
    stdio: 'inherit',
  })
}
