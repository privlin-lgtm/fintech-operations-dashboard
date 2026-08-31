import type { Page } from '@playwright/test'

export class TransactionsPage {
  constructor(private readonly page: Page) {}

  async openTransaction(amountLabel: string) {
    await this.page.getByRole('link', { name: amountLabel }).click()
  }
}
