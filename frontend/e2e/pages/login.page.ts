import type { Locator, Page } from '@playwright/test'

export class LoginPage {
  readonly email: Locator
  readonly password: Locator
  readonly submit: Locator

  constructor(private readonly page: Page) {
    this.email = page.getByTestId('login-email')
    this.password = page.getByTestId('login-password')
    this.submit = page.getByTestId('login-submit')
  }

  async goto() {
    await this.page.goto('/login')
  }

  async signIn(email: string, password: string) {
    await this.goto()
    await this.email.fill(email)
    await this.password.fill(password)
    await this.submit.click()
    await this.page.waitForURL('/')
    await this.page.getByText('Welcome back').waitFor()
  }
}

export class AppShell {
  constructor(private readonly page: Page) {}

  async navigateTo(label: 'Customers' | 'Transactions' | 'Cases' | 'Alerts' | 'Reports') {
    await this.page.getByRole('link', { name: label, exact: true }).click()
  }
}
