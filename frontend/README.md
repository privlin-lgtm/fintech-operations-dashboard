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
