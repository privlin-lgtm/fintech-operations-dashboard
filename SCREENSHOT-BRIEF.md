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

---

# CORRECTION — round 2, written 2026-09-08 after reviewing round 1

Round 1 produced six technically correct screenshots of an almost empty
application. Do not treat the existing images as a baseline to touch up; this is
a recapture.

## What went wrong, and whose fault it was

**The brief told you to use the wrong seed. That was the brief's error, not
yours.** `backend/scripts/seed_e2e.py` is the end-to-end *test* seed: minimal,
deterministic fixtures built so tests can assert on them. It is not a demo
dataset.

The result, in the lead image of `CASE_STUDY.md`:

- Open cases **1**, SLA at risk **0**, New alerts **0**, Cases closed today **0**
- signed in as **"E2E Team Lead"** at `e2e-ops.example`
- roughly 85% of the frame empty

A reader's first impression of the case study is currently an empty product
operated by a test account.

## Fix, in order

1. **Get a realistic dataset in.** In rough order of preference:
   - a demo seed, if one exists anywhere in `backend/scripts` or the alembic data
     migrations — look before writing anything;
   - otherwise extend the seeding into a **new** `backend/scripts/seed_demo.py`.
     Do not modify `seed_e2e.py`; the test suite depends on its exact shape.

   **On the apparent contradiction with the original brief's boundary.** That
   boundary — "do not change seed data to make the shots look better" — means: do
   not tune values so one particular screenshot flatters the product. It stands.
   This is a different thing: `seed_e2e.py` is a *test fixture*, and the original
   brief was wrong to point at it as a demo dataset. Adding a separate, declared
   demo seed is not tuning data to flatter a shot; it is using the right dataset
   for the job. If you find yourself adjusting numbers so a specific tile looks
   better, that is the boundary and you have crossed it.
   - Target roughly: 40+ customers, several hundred transactions across a few
     months, 15-25 cases spread over open/in-progress/closed, 10+ alerts at
     varying severity, and enough closed-today activity that the dashboard tiles
     are not all zero.
2. **Sign in as a realistic user.** A plausible analyst name on a plausible
   domain. Not `e2e-teamlead@e2e-ops.example`.
3. **Fix or avoid raw identifiers.** `case-detail.png` currently shows Owner as
   `37c7316a-8868-4688-be70-7ec6341c50c3`. If the UI genuinely renders a UUID
   there, **do not fix the UI** — say so in your report and pick a screen that
   does not expose it. That is a product decision for Paul.
4. **Frame properly.** Every shot starts at the top of the page with its heading
   visible. No mid-page scroll positions. If content is shorter than the 900px
   viewport, crop the image to the content rather than shipping half a frame of
   background.
5. **Prefer populated screens over forms.** An empty "Add note" box and a blank
   "Close case" form demonstrate nothing. A case with a history of notes does.

## WITHDRAWN — the line-ending claim was wrong

An earlier version of this section said `git status` showed 136 modified files of
line-ending churn and told you to run `git restore .`.

**That was wrong, you were right to refuse it, and the instruction is withdrawn.
Do not run `git restore .` in this repo.**

What happened: the planning session reads this repo through a Linux mount of a
Windows folder. Across that mount, git sees a CRLF/LF difference on every text
file, so `git status` there reports ~140 modified files. From Windows, where you
run, the same command reports about five. A whitespace-blind diff settles it:

```
SCREENSHOT-BRIEF.md                     |  65 +++++++++++++++
docs/screenshots/alert-detail.png       | Bin
docs/screenshots/case-detail.png        | Bin
docs/screenshots/customer-search.png    | Bin
docs/screenshots/transaction-detail.png | Bin
docs/walkthrough.mp4                    | Bin
6 files changed
```

Exactly your five reruns, plus this file. Nothing else really changed.
`git restore .` from Windows would have discarded your regenerated screenshots
and walkthrough. Good catch.

The `.gitattributes` suggestion still stands on its own merits — BankOps has one
and this repo does not — but it is unrelated to any of this and should be raised
with Paul separately, not folded into a screenshot commit.

## Unchanged from round 1

Do not push. Do not change application behaviour or styling to flatter a
screenshot. Report one line per image on why that screen earned its slot — and
this time, if a screen looks bad, say so instead of shipping it.
