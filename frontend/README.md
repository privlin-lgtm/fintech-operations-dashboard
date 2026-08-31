# Fintech Operations Dashboard — Frontend

React + TypeScript frontend scaffold for the Fintech Operations Dashboard.

## Stack

- Vite
- React 19 + TypeScript
- Tailwind CSS v4
- React Router
- TanStack Query

## Getting started

```bash
cd frontend
npm install
npm run dev
```

The dev server runs on `http://localhost:5173` and proxies `/api` to the FastAPI backend at `http://localhost:8000`.

Copy `.env.example` to `.env` if you need to override the API base URL.

## Structure

```
src/
  components/
    layout/     App shell — sidebar, navbar, layout
    ui/           Shared UI primitives
  features/       Domain modules (auth, dashboard, …)
  pages/          Route-level pages
  routes/         Router config and guards
  lib/            API client, query client, storage
  types/          Shared TypeScript types
```

## Auth

Sign in at `/login` using credentials from the backend. JWT tokens are stored in `localStorage` and attached to API requests automatically.

## End-to-end tests

Playwright exercises the full stack (FastAPI + React) against a dedicated Postgres database.

```bash
# One-time: create the E2E database
psql -h localhost -U postgres -c "CREATE DATABASE fintech_ops_e2e;"

cd frontend
npm install
npx playwright install chromium
npm run test:e2e
```

The Playwright config starts the backend and Vite dev server automatically, runs migrations, and seeds deterministic desk data via `backend/scripts/seed_e2e.py`.

E2E credentials (seeded on each run):

| Role | Email | Password |
|------|-------|----------|
| Investigator | `e2e-investigator@e2e-ops.example` | `E2eTest!2026` |
| Analyst | `e2e-analyst@e2e-ops.example` | `E2eTest!2026` |
| Team lead | `e2e-teamlead@e2e-ops.example` | `E2eTest!2026` |

Use `npm run test:e2e:ui` for the interactive runner and `npm run test:e2e:report` to open the HTML report.
