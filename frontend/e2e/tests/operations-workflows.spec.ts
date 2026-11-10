import { test, expect } from '@playwright/test'

import { AlertsPage } from '../pages/alerts.page'
import { CaseClosePage, CasesPage, CustomerCasePage } from '../pages/cases.page'
import { CustomersPage } from '../pages/customers.page'
import { AppShell, LoginPage } from '../pages/login.page'
import { ReportsPage } from '../pages/reports.page'
import { TransactionsPage } from '../pages/transactions.page'
import { seedData } from '../seed-data'

test.describe('Fintech operations desk', () => {
  test('login', async ({ page }) => {
    const login = new LoginPage(page)
    const investigator = seedData.users.investigator

    await login.signIn(investigator.email, seedData.password)

    await expect(page.getByText('Welcome back')).toBeVisible()
    await expect(page.getByText(investigator.email)).toBeVisible()
    await expect(page.getByRole('main').getByRole('heading', { name: 'Operations dashboard' })).toBeVisible()
  })

  test('session survives a page reload', async ({ page }) => {
    // Regression coverage: the frontend used to store the refresh token in
    // localStorage and never survived past the access token's lifetime once
    // the backend moved to an httpOnly refresh cookie. A reload is the
    // simplest real-browser way to force the app to re-bootstrap its
    // session from nothing but that cookie, with no JS-visible state at all.
    const login = new LoginPage(page)
    const investigator = seedData.users.investigator

    await login.signIn(investigator.email, seedData.password)
    await expect(page.getByText(investigator.email)).toBeVisible()

    await page.reload()

    await expect(page.getByRole('main').getByRole('heading', { name: 'Operations dashboard' })).toBeVisible()
    await expect(page.getByText(investigator.email)).toBeVisible()
    await expect(page).toHaveURL('/')
  })

  test('header role label and full-height sidebar', async ({ page }) => {
    const login = new LoginPage(page)

    await login.signIn(seedData.users.team_lead.email, seedData.password)

    await expect(page.getByRole('banner').getByText('Team lead', { exact: true })).toBeVisible()

    const viewport = page.viewportSize()
    const sidebar = await page.getByTestId('app-sidebar').boundingBox()
    expect(viewport).not.toBeNull()
    expect(sidebar).not.toBeNull()
    expect(sidebar!.y).toBe(0)
    expect(sidebar!.height).toBeGreaterThanOrEqual(viewport!.height)
  })

  test('search customer', async ({ page }) => {
    const login = new LoginPage(page)
    const app = new AppShell(page)
    const customers = new CustomersPage(page)

    await login.signIn(seedData.users.analyst.email, seedData.password)
    await app.navigateTo('Customers')

    await customers.search('Meridian')
    await expect(page.getByRole('link', { name: seedData.customers.search.name })).toBeVisible()

    await customers.openCustomer(seedData.customers.search.name)
    await expect(page.getByRole('heading', { name: seedData.customers.search.name })).toBeVisible()
    await expect(page.getByText('Risk: High')).toBeVisible()
  })

  test('view transaction', async ({ page }) => {
    const login = new LoginPage(page)
    const app = new AppShell(page)
    const transactions = new TransactionsPage(page)

    await login.signIn(seedData.users.analyst.email, seedData.password)
    await app.navigateTo('Transactions')

    await transactions.openTransaction(seedData.transaction.amountLabel)
    await expect(page.getByRole('heading', { name: seedData.transaction.amountLabel })).toBeVisible()
    await expect(page.getByText(seedData.transaction.counterparty)).toBeVisible()
    await expect(page.getByText('**** 8821')).toBeVisible()
  })

  test('open case', async ({ page }) => {
    const login = new LoginPage(page)
    const customerCases = new CustomerCasePage(page)

    await login.signIn(seedData.users.investigator.email, seedData.password)
    await page.goto(`/customers/${seedData.customers.openCase.id}`)

    await customerCases.openCase('High')
    await expect(page).toHaveURL(/\/cases\//)
    await expect(page.getByTestId('case-type')).toHaveText('Fraud case')
    await expect(page.getByText('High', { exact: true })).toBeVisible()
  })

  test('closed case shows its resolution in plain words', async ({ page }) => {
    const login = new LoginPage(page)
    const customerCases = new CustomerCasePage(page)

    await login.signIn(seedData.users.investigator.email, seedData.password)
    await page.goto(`/customers/${seedData.customers.openCase.id}`)
    await customerCases.openCase('Medium')
    await expect(page).toHaveURL(/\/cases\//)

    await new CaseClosePage(page).close('activity_explained', 'Documents reconcile with the activity.')

    await expect(page.getByTestId('case-resolution')).toHaveText('Activity explained')
  })

  test('assign case', async ({ page }) => {
    const login = new LoginPage(page)
    const cases = new CasesPage(page)
    const analystId = seedData.users.analyst.id

    await login.signIn(seedData.users.team_lead.email, seedData.password)
    await cases.openCaseById(seedData.caseForAssign.id)

    await expect(page.getByRole('heading', { name: seedData.caseForAssign.caseNumber })).toBeVisible()
    // The new owner is picked by name (seed_e2e.py names each user "E2E <Role>");
    // nobody types a user id any more.
    await cases.reassign('E2E Analyst (Analyst)', 'Card fraud specialist coverage for E2E handoff')

    const owner = page.getByTestId('case-owner')
    await expect(owner).toHaveText('E2E Analyst')
    await expect(owner).not.toContainText(analystId)
  })

  test('a 422 from reassign shows a message instead of crashing the case page', async ({ page }) => {
    // Regression: FastAPI's 422 sends `detail` as an array of {loc, msg}. The
    // form used to render that array as a React child and white-screen the page.
    const login = new LoginPage(page)
    const cases = new CasesPage(page)

    await page.route('**/api/v1/cases/*/reassign', (route) =>
      route.fulfill({
        status: 422,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: [
            {
              type: 'uuid_parsing',
              loc: ['body', 'owner_id'],
              msg: 'Input should be a valid UUID',
              input: 'not-a-uuid',
            },
          ],
        }),
      }),
    )

    await login.signIn(seedData.users.team_lead.email, seedData.password)
    await cases.openCaseById(seedData.caseForAssign.id)
    await cases.reassign('E2E Team Lead (Team lead)', 'Checking the error path')

    await expect(page.getByText('Owner id: Input should be a valid UUID')).toBeVisible()
    await expect(page.getByRole('heading', { name: seedData.caseForAssign.caseNumber })).toBeVisible()
    await expect(page.getByTestId('reassign-case-submit')).toBeVisible()
  })

  test('assign alert by name', async ({ page, request }) => {
    const login = new LoginPage(page)
    const alerts = new AlertsPage(page)
    const investigator = seedData.users.investigator

    // A fresh "new" alert, so the Assign form is on screen. seed_e2e.py
    // deletes every alert on its E2E customers at the start of each run.
    // `request` is its own context, so this API sign-in leaves no refresh
    // cookie in the browser (which would skip the login page below).
    const tokenResponse = await request.post('/api/v1/auth/login', {
      data: { email: investigator.email, password: seedData.password },
    })
    expect(tokenResponse.ok()).toBeTruthy()
    const { access_token: accessToken } = (await tokenResponse.json()) as { access_token: string }
    const created = await request.post('/api/v1/alerts', {
      headers: { Authorization: `Bearer ${accessToken}` },
      data: {
        customer_id: seedData.customers.alert.id,
        alert_type: 'velocity',
        severity: 'medium',
        triggering_reason: 'E2E assign-by-name check: burst of card payments',
      },
    })
    expect(created.status()).toBe(201)
    const { id: alertId } = (await created.json()) as { id: string }

    await login.signIn(investigator.email, seedData.password)
    await alerts.openAlertById(alertId)
    await expect(page.getByTestId('alert-assignee')).toHaveText('Unassigned')

    await alerts.assign('E2E Analyst (Analyst)')

    await expect(page.getByTestId('alert-assignee')).toHaveText('E2E Analyst')
    await expect(page.getByText('Assigned', { exact: true })).toBeVisible()
  })

  test('resolve alert', async ({ page }) => {
    const login = new LoginPage(page)
    const alerts = new AlertsPage(page)

    await login.signIn(seedData.users.investigator.email, seedData.password)
    await alerts.openAlertById(seedData.alert.id)

    await expect(page.getByText(seedData.alert.reason)).toBeVisible()
    await expect(page.getByTestId('alert-assignee')).toHaveText('E2E Investigator')
    await alerts.resolve('False positive — beneficiary cleared against OFAC SDN list')

    await expect(page.getByText('Resolved', { exact: true })).toBeVisible()
    await expect(page.getByText('False positive — beneficiary cleared against OFAC SDN list')).toBeVisible()
  })

  test('generate report', async ({ page }) => {
    const login = new LoginPage(page)
    const app = new AppShell(page)
    const reports = new ReportsPage(page)

    await login.signIn(seedData.users.team_lead.email, seedData.password)
    await app.navigateTo('Reports')
    await reports.openReport('Transaction volume')
    await reports.expectResults()

    const download = await reports.exportCsv()
    expect(download.suggestedFilename()).toMatch(/transactions.*\.csv$/i)
  })
})
