import type { Page } from '@playwright/test'

export class ReportsPage {
  constructor(private readonly page: Page) {}

  async openReport(label: string) {
    await this.page.getByRole('link', { name: label }).click()
  }

  async expectResults() {
    await this.page.getByRole('heading', { name: 'Results' }).waitFor()
    await this.page.getByRole('columnheader', { name: 'Group' }).waitFor()
  }

  async exportCsv() {
    const downloadPromise = this.page.waitForEvent('download')
    await this.page.getByTestId('export-csv').click()
    return downloadPromise
  }
}
