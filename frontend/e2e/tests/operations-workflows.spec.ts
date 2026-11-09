import { test, expect } from '@playwright/test'

import { AlertsPage } from '../pages/alerts.page'
import { CasesPage, CustomerCasePage } from '../pages/cases.page'
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
    await expect(page.getByText('fraud case', { exact: false })).toBeVisible()
    await expect(page.getByText('High', { exact: true })).toBeVisible()
  })

  test('assign case', async ({ page }) => {
    const login = new LoginPage(page)
    const cases = new CasesPage(page)
    const analystId = seedData.users.analyst.id

    await login.signIn(seedData.users.team_lead.email, seedData.password)
    await cases.openCaseById(seedData.caseForAssign.id)

    await expect(page.getByRole('heading', { name: seedData.caseForAssign.caseNumber })).toBeVisible()
    await cases.reassign(analystId, 'Card fraud specialist coverage for E2E handoff')

    // The owner reads as the analyst's display name (seed_e2e.py names each
    // user "E2E <Role>"), not the raw user id that was typed into the form.
    const owner = page.getByTestId('case-owner')
    await expect(owner).toHaveText('E2E Analyst')
    await expect(owner).not.toContainText(analystId)
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
