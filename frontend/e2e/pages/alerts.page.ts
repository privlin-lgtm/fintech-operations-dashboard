import type { Page } from '@playwright/test'

export class AlertsPage {
  constructor(private readonly page: Page) {}

  async openAlert(reasonSnippet: string) {
    await this.page.getByRole('link', { name: /sanctions match/i }).click()
    await this.page.getByText(reasonSnippet).waitFor()
  }

  async openAlertById(alertId: string) {
    await this.page.goto(`/alerts/${alertId}`)
  }

  async resolve(reason: string) {
    await this.page.getByTestId('resolve-alert-reason').fill(reason)
    await this.page.getByRole('button', { name: 'Resolve alert' }).click()
  }
}
