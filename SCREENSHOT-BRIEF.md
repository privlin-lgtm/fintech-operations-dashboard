# Brief — portfolio screenshots and walkthrough

Written 2026-09-08 by a planning session. Portfolio polish, **not feature work**.

## Why this repo, and why now

This is one of four employer-facing portfolio pieces (with `genpay-api`,
`document-archive-digitalization-pipeline` and
`digital-banking-operations-command-center`). 26 commits, CI, and — unusually —
`CASE_STUDY.md` is already written.

**But it has no images at all.** The case study describes screens nobody can
see. Of the twelve projects in the portfolio only two carry any images, and a
reader deciding in thirty seconds has nothing to look at. That is what this fixes.

## Goal

1. `docs/screenshots/` holding 4–6 PNGs of the strongest screens.
2. Embedded in **both** `README.md` (near the top) **and `CASE_STUDY.md`**, placed
   next to the sections that describe them. The case study is the better document
   and it is currently all prose.
3. One 60–90 second **silent** walkthrough (MP4 or animated GIF) in `docs/`,
   linked from both.
4. A re-runnable capture script.

## Approach

Backend is FastAPI + SQLAlchemy + Postgres with Alembic; frontend is React +
TypeScript + Vite (`npm run dev`).

**Two things already exist here — use them, do not rebuild them:**

- `backend/scripts/seed_e2e.py` — the seed. Screenshots must show a populated
  system: real-looking customers, transactions, cases and alerts, not empty states.
- `frontend/playwright.config.ts` and `frontend/e2e/` — Playwright is already
  configured. Extend that setup rather than adding a second one. Put the capture
  script alongside the existing e2e tests.

Bring up Postgres, `alembic upgrade head`, run the seed, start backend and
frontend, then capture.

- Fixed viewport, **1440x900**.
- Pick light or dark and hold it across every shot. Say which and why.
- Wait for network idle and for data to actually render.
- Name files by content (`case-detail.png`), never by number.

**Suggested screens**, from the case study's own description:

1. Customer search
2. Transaction lookup / monitoring
3. Case management — likely the strongest screen
4. Alerting
5. Reporting
6. Something showing RBAC or the audit trail, if there is a screen for it — the
   case study leans on both and they are the parts most demos skip

For the walkthrough: one continuous path, ideally search a customer, open a
transaction, raise or work a case. No narration, no burned-in captions.

## Definition of done

- Screenshots committed; README and CASE_STUDY both render them
- Walkthrough recorded and linked
- Capture script runs from a clean checkout and reproduces the same images
- Nothing committed over ~2MB per file

## Boundaries

- **Do not change application behaviour, styling, or seed data to make the shots
  look better.** If a screen looks bad, stop and say so — that is Paul's call.
- **Do not push.** Commit locally; he wants to look first.
- Do not rewrite the case study's prose. Add images next to the relevant
  sections; leave the words alone.
- Do not touch `backend/app` or `frontend/src` except to read them.

## Report back with

The file list, and **one line per screenshot saying why that screen earned a
slot**. If something would not run, say what and why rather than quietly
substituting a weaker screen.
