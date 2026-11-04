import fs from 'node:fs'
import path from 'node:path'
import { execFileSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

import { test, type Page } from '@playwright/test'

import { AppShell, LoginPage } from '../pages/login.page'
import { ReportsPage } from '../pages/reports.page'
import { TransactionsPage } from '../pages/transactions.page'

// Portfolio screenshot + walkthrough capture for docs/. Not a regression
// test: skipped in CI, and it only runs against the demo dataset
// (backend/scripts/seed_demo.py), never the e2e test fixture.
//
//   bash:        E2E_SEED=demo npx playwright test capture-screenshots
//   PowerShell:  $env:E2E_SEED='demo'; npx playwright test capture-screenshots
//
// E2E_SEED=demo makes global-setup migrate and seed a fintech_ops_demo
// database and points the backend at it. Stop any backend already running
// on port 8000 first: Playwright reuses it, and it would be on the wrong
// database.
test.skip(Boolean(process.env.CI), 'manual portfolio capture script, not part of the CI e2e run')
test.skip(
  process.env.E2E_SEED !== 'demo',
  'portfolio capture needs the demo dataset: run with E2E_SEED=demo',
)

type DemoSeedData = {
  password: string
  users: Record<
    'team_lead' | 'investigator' | 'investigator_2' | 'analyst' | 'compliance',
    { id: string; email: string; name: string }
  >
  customerSearch: { query: string; name: string; id: string }
  transaction: { id: string; counterparty: string; amountLabel: string }
  case: { id: string; caseNumber: string }
  triageCase: { id: string; caseNumber: string }
  alert: { id: string; reason: string }
}

const e2eDir = path.dirname(fileURLToPath(import.meta.url).replace(/tests[/\\]?$/, ''))
const projectRoot = path.resolve(e2eDir, '../../..')
const docsDir = path.join(projectRoot, 'docs')
const screenshotsDir = path.join(docsDir, 'screenshots')
const demoSeedPath = path.resolve(e2eDir, '..', '.demo-seed-data.json')

function loadDemoSeed(): DemoSeedData {
  return JSON.parse(fs.readFileSync(demoSeedPath, 'utf-8')) as DemoSeedData
}

test.use({ viewport: { width: 1440, height: 900 } })

const VIEWPORT = { width: 1440, height: 900 }
// Shots taller than this are cut, at a table-row boundary when there is one,
// so a long queue reads as "first screen of the list" rather than a poster.
const MAX_SHOT_HEIGHT = 960
const BOTTOM_PADDING = 24

// Every shot starts at the top of the page. The image is cropped to the
// bottom of the rendered content (main column or sidebar, whichever is
// taller) so short screens don't ship half a frame of empty background.
async function shoot(page: Page, name: string) {
  await page.waitForLoadState('networkidle')
  await page.evaluate(() => window.scrollTo(0, 0))
  await page.waitForTimeout(250)
  const crop = await page.evaluate((limit) => {
    const main = document.querySelector('main')
    const bottoms = [main, document.querySelector('aside')]
      .filter((el): el is Element => el !== null)
      .map((el) => {
        // main is a flex-1 column, so measure its children, not the box.
        const target = el === main ? Array.from(el.children) : [el]
        return Math.max(...target.map((child) => child.getBoundingClientRect().bottom))
      })
    const bottom = Math.ceil(Math.max(...bottoms) + window.scrollY)
    if (bottom <= limit) return { bottom, cutAtRow: false }
    const rowBottoms = Array.from(document.querySelectorAll('main tr'))
      .map((row) => Math.ceil(row.getBoundingClientRect().bottom + window.scrollY))
      .filter((rowBottom) => rowBottom <= limit)
    return rowBottoms.length > 0
      ? { bottom: Math.max(...rowBottoms), cutAtRow: true }
      : { bottom: limit, cutAtRow: false }
  }, MAX_SHOT_HEIGHT - BOTTOM_PADDING)
  // No padding under a cut row, or the next row peeks in.
  const height = crop.cutAtRow
    ? crop.bottom
    : Math.min(Math.max(crop.bottom + BOTTOM_PADDING, 300), MAX_SHOT_HEIGHT)
  await page.screenshot({
    path: path.join(screenshotsDir, `${name}.png`),
    fullPage: height > VIEWPORT.height,
    clip: { x: 0, y: 0, width: VIEWPORT.width, height },
  })
}

test('capture portfolio screenshots', async ({ page }) => {
  const seed = loadDemoSeed()
  fs.mkdirSync(screenshotsDir, { recursive: true })
  const login = new LoginPage(page)
  const app = new AppShell(page)

  // Every still is taken as the team lead: the one persona that can see
  // every screen, including Reports.
  await login.signIn(seed.users.team_lead.email, seed.password)

  // 1. Operations dashboard — the landing screen.
  await page.getByRole('main').getByRole('heading', { name: 'Operations dashboard' }).waitFor()
  await page.getByText('Cases closed today').waitFor()
  await shoot(page, 'operations-dashboard')

  // 2. Customer search — filtered to the high-risk book.
  await app.navigateTo('Customers')
  await page.getByLabel('Risk tier').selectOption('high')
  await page.getByRole('button', { name: 'Apply filters' }).click()
  await page.waitForLoadState('networkidle')
  await page.getByRole('table').waitFor()
  await shoot(page, 'customer-search')

  // 3. Transaction detail — the flagged outbound wire behind the AML case.
  await page.goto(`/transactions/${seed.transaction.id}`)
  await page.getByText(seed.transaction.counterparty).waitFor()
  await shoot(page, 'transaction-detail')

  // 4. Case queue. (Case detail is not shot: it renders the owner as a raw
  // user UUID, a UI decision left to Paul — see the PR.)
  await app.navigateTo('Cases')
  await page.getByRole('link', { name: seed.case.caseNumber }).waitFor()
  await shoot(page, 'case-queue')

  // 5. Alert queue. (Alert detail likewise renders the assignee as a UUID.)
  await app.navigateTo('Alerts')
  await page.getByRole('table').waitFor()
  await shoot(page, 'alert-queue')

  // 6. Reports — transaction volume grouped by channel over the seeded history.
  await app.navigateTo('Reports')
  await new ReportsPage(page).openReport('Transaction volume')
  const url = new URL(page.url())
  url.searchParams.set('group_by', 'channel')
  await page.goto(url.pathname + url.search)
  await new ReportsPage(page).expectResults()
  await page.getByRole('cell', { name: 'wire', exact: false }).first().waitFor()
  await shoot(page, 'report-transaction-volume')
})

test('record portfolio walkthrough', async ({ browser }) => {
  test.setTimeout(150_000)
  const seed = loadDemoSeed()
  const videoDir = path.join(docsDir, '_walkthrough-tmp')
  fs.mkdirSync(videoDir, { recursive: true })

  const context = await browser.newContext({
    viewport: VIEWPORT,
    recordVideo: { dir: videoDir, size: VIEWPORT },
  })
  const page = await context.newPage()
  const app = new AppShell(page)

  // One continuous path, paced for a ~65s silent walkthrough: an
  // investigator signs in, checks the alert queue, finds a customer, opens
  // the flagged wire, then picks up a new case from the queue and adds a
  // triage note. The case is a new, unassigned one on purpose: case detail
  // renders an assigned owner as a raw user UUID (left for Paul to decide).
  await page.goto('/login')
  await page.getByTestId('login-email').pressSequentially(seed.users.investigator.email, { delay: 50 })
  await page.waitForTimeout(300)
  await page.getByTestId('login-password').pressSequentially(seed.password, { delay: 50 })
  await page.waitForTimeout(400)
  await page.getByTestId('login-submit').click()
  await page.waitForURL('/')
  await page.getByText('Welcome back').waitFor()
  await page.waitForTimeout(5000)

  await app.navigateTo('Alerts')
  await page.getByRole('table').waitFor()
  await page.waitForTimeout(5000)

  await app.navigateTo('Customers')
  await page.waitForTimeout(2000)
  await page
    .getByTestId('customer-search-query')
    .pressSequentially(seed.customerSearch.query, { delay: 110 })
  await page.waitForTimeout(500)
  await page.getByRole('button', { name: 'Apply filters' }).click()
  await page.getByRole('link', { name: seed.customerSearch.name }).waitFor()
  await page.waitForTimeout(3000)
  await page.getByRole('link', { name: seed.customerSearch.name }).click()
  await page.getByRole('heading', { name: seed.customerSearch.name }).waitFor()
  await page.waitForTimeout(7000)

  await app.navigateTo('Transactions')
  await page.waitForTimeout(2500)
  await new TransactionsPage(page).openTransaction(seed.transaction.amountLabel)
  await page.getByText(seed.transaction.counterparty).waitFor()
  await page.waitForTimeout(8000)

  await app.navigateTo('Cases')
  await page.getByRole('link', { name: seed.case.caseNumber }).waitFor()
  await page.waitForTimeout(2500)
  await page.getByLabel('Status').selectOption('new')
  await page.waitForTimeout(800)
  await page.getByRole('button', { name: 'Apply filters' }).click()
  await page.getByRole('link', { name: seed.triageCase.caseNumber }).waitFor()
  await page.waitForTimeout(3000)
  await page.getByRole('link', { name: seed.triageCase.caseNumber }).click()
  await page.getByRole('heading', { name: seed.triageCase.caseNumber }).waitFor()
  await page.waitForTimeout(5000)

  const note = page.getByPlaceholder('What did you find, or what happened next?')
  await note.scrollIntoViewIfNeeded()
  await page.waitForTimeout(1500)
  await note.pressSequentially(
    'Pulled 30-day card history: three disputed payments at one merchant. Requesting merchant details.',
    { delay: 35 },
  )
  await page.waitForTimeout(800)
  await page.getByRole('button', { name: 'Add note' }).click()
  await page.getByText('Requesting merchant details.').first().waitFor()
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }))
  await page.waitForTimeout(8000)

  const videoPath = await page.video()?.path()
  await context.close()

  if (!videoPath || !fs.existsSync(videoPath)) {
    throw new Error('Playwright did not produce a walkthrough video')
  }

  const mp4Path = path.join(docsDir, 'walkthrough.mp4')
  execFileSync('ffmpeg', [
    '-y',
    '-loglevel', 'error',
    // Skip the blank frame before the login page first paints.
    '-ss', '0.8',
    '-i', videoPath,
    '-vf', 'scale=1280:-2,fps=12',
    '-c:v', 'libx264',
    '-crf', '30',
    '-preset', 'slower',
    '-pix_fmt', 'yuv420p',
    '-movflags', '+faststart',
    '-an',
    mp4Path,
  ])

  fs.rmSync(videoDir, { recursive: true, force: true })

  const { size } = fs.statSync(mp4Path)
  console.log(`walkthrough.mp4 written: ${(size / 1024 / 1024).toFixed(2)} MB`)
})
