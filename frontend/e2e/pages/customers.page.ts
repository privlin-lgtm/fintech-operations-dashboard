import type { Page } from '@playwright/test'

export class CustomersPage {
  constructor(private readonly page: Page) {}

  async search(query: string) {
    await this.page.getByTestId('customer-search-query').fill(query)
    await this.page.getByRole('button', { name: 'Apply filters' }).click()
  }

  async openCustomer(name: string) {
    await this.page.getByRole('link', { name }).click()
  }
}
