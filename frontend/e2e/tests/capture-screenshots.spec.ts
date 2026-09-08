import fs from 'node:fs'
import path from 'node:path'
import { execFileSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

import { test } from '@playwright/test'

import { AlertsPage } from '../pages/alerts.page'
import { CasesPage } from '../pages/cases.page'
import { CustomersPage } from '../pages/customers.page'
import { AppShell, LoginPage } from '../pages/login.page'
import { ReportsPage } from '../pages/reports.page'
import { TransactionsPage } from '../pages/transactions.page'
import { seedData } from '../seed-data'

// Portfolio screenshot + walkthrough capture for docs/. Not a regression
// test: skipped in CI, run manually with
//   npx playwright test capture-screenshots
// against a seeded fintech_ops_e2e database (see SCREENSHOT-BRIEF.md).
test.skip(Boolean(process.env.CI), 'manual portfolio capture script, not part of the CI e2e run')

test.use({ viewport: { width: 1440, height: 900 } })

const e2eDir = path.dirname(fileURLToPath(import.meta.url).replace(/tests[/\\]?$/, ''))
const projectRoot = path.resolve(e2eDir, '../../..')
const docsDir = path.join(projectRoot, 'docs')
const screenshotsDir = path.join(docsDir, 'screenshots')

fs.mkdirSync(screenshotsDir, { recursive: true })

async function shoot(page: import('@playwright/test').Page, name: string) {
  await page.waitForLoadState('networkidle')
  await page.screenshot({ path: path.join(screenshotsDir, `${name}.png`) })
}

// LoginPage.signIn assumes a logged-out session (GuestRoute redirects /login
// back to / for an authenticated user). Sign out first when switching personas.
async function switchUser(
  page: import('@playwright/test').Page,
  login: LoginPage,
  email: string,
  password: string,
) {
  const signOut = page.getByRole('button', { name: 'Sign out' })
  if (await signOut.isVisible().catch(() => false)) {
    await signOut.click()
    await page.waitForURL('/login')
  }
  await login.signIn(email, password)
}

test('capture portfolio screenshots', async ({ page }) => {
  const login = new LoginPage(page)
  const app = new AppShell(page)

  // 1. Customer search — the analyst persona, mid-search.
  await switchUser(page, login, seedData.users.analyst.email, seedData.password)
  await app.navigateTo('Customers')
  const customers = new CustomersPage(page)
  await customers.search('Meridian')
  await page.getByRole('link', { name: seedData.customers.search.name }).waitFor()
  await shoot(page, 'customer-search')

  // 2. Transaction detail — flagged wire transfer with a risk score.
  await app.navigateTo('Transactions')
  const transactions = new TransactionsPage(page)
  await transactions.openTransaction(seedData.transaction.amountLabel)
  await page.getByText(seedData.transaction.counterparty).waitFor()
  await shoot(page, 'transaction-detail')

  // 3. Case detail — the strongest screen: SLA, priority, reassign form.
  // Sign in as team lead so the reassign-case action (team_lead/admin only) is visible.
  await switchUser(page, login, seedData.users.team_lead.email, seedData.password)
  const cases = new CasesPage(page)
  await cases.openCaseById(seedData.caseForAssign.id)
  await page.getByRole('heading', { name: seedData.caseForAssign.caseNumber }).waitFor()
  await shoot(page, 'case-detail')

  // 4. Alert detail — critical sanctions-match triage, pre-resolution.
  await switchUser(page, login, seedData.users.investigator.email, seedData.password)
  const alerts = new AlertsPage(page)
  await alerts.openAlertById(seedData.alert.id)
  await page.getByText(seedData.alert.reason).waitFor()
  await shoot(page, 'alert-detail')

  // 5. Reports — populated results grid for a generated report.
  await switchUser(page, login, seedData.users.team_lead.email, seedData.password)
  await app.navigateTo('Reports')
  const reports = new ReportsPage(page)
  await reports.openReport('Transaction volume')
  await reports.expectResults()
  await shoot(page, 'report-transaction-volume')

  // 6. Operations dashboard — overview landing screen.
  // No dedicated audit-trail/RBAC screen exists in the app (the audit log is
  // backend-only); the reassign action gated to team_lead/admin on the case
  // detail screen above is the closest visible RBAC signal.
  await page.goto('/')
  await page.getByRole('main').getByRole('heading', { name: 'Operations dashboard' }).waitFor()
  await shoot(page, 'operations-dashboard')
})

test('record portfolio walkthrough', async ({ browser }) => {
  test.setTimeout(120_000)
  const videoDir = path.join(docsDir, '_walkthrough-tmp')
  fs.mkdirSync(videoDir, { recursive: true })

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    recordVideo: { dir: videoDir, size: { width: 1440, height: 900 } },
  })
  const page = await context.newPage()

  const app = new AppShell(page)

  // One continuous path, paced for a ~70s silent walkthrough: sign in,
  // search a customer, open a transaction, then work a case.
  await page.goto('/login')
  await page.getByTestId('login-email').pressSequentially(seedData.users.investigator.email, { delay: 60 })
  await page.waitForTimeout(300)
  await page.getByTestId('login-password').pressSequentially(seedData.password, { delay: 60 })
  await page.waitForTimeout(400)
  await page.getByTestId('login-submit').click()
  await page.waitForURL('/')
  await page.getByText('Welcome back').waitFor()
  await page.waitForTimeout(5000)

  await app.navigateTo('Customers')
  await page.waitForTimeout(2500)
  const customers = new CustomersPage(page)
  await page.getByTestId('customer-search-query').pressSequentially('Meridian', { delay: 110 })
  await page.waitForTimeout(500)
  await page.getByRole('button', { name: 'Apply filters' }).click()
  await page.getByRole('link', { name: seedData.customers.search.name }).waitFor()
  await page.waitForTimeout(3500)
  await customers.openCustomer(seedData.customers.search.name)
  await page.getByRole('heading', { name: seedData.customers.search.name }).waitFor()
  await page.waitForTimeout(8000)

  await app.navigateTo('Transactions')
  await page.waitForTimeout(2500)
  const transactions = new TransactionsPage(page)
  await transactions.openTransaction(seedData.transaction.amountLabel)
  await page.getByText(seedData.transaction.counterparty).waitFor()
  await page.waitForTimeout(9000)

  await app.navigateTo('Cases')
  await page.waitForTimeout(2500)
  await page.getByRole('link', { name: seedData.caseForAssign.caseNumber }).click()
  await page.getByRole('heading', { name: seedData.caseForAssign.caseNumber }).waitFor()
  await page.waitForTimeout(4000)
  await page.mouse.wheel(0, 400)
  await page.waitForTimeout(11000)

  const videoPath = await page.video()?.path()
  await context.close()

  if (!videoPath || !fs.existsSync(videoPath)) {
    throw new Error('Playwright did not produce a walkthrough video')
  }

  const mp4Path = path.join(docsDir, 'walkthrough.mp4')
  execFileSync('ffmpeg', [
    '-y',
    '-i', videoPath,
    '-vf', 'scale=1280:-2,fps=12',
    '-c:v', 'libx264',
    '-crf', '30',
    '-preset', 'slower',
    '-an',
    mp4Path,
  ])

  fs.rmSync(videoDir, { recursive: true, force: true })

  const { size } = fs.statSync(mp4Path)
  console.log(`walkthrough.mp4 written: ${(size / 1024 / 1024).toFixed(2)} MB`)
})
