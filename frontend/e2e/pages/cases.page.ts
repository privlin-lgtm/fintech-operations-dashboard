import type { Page } from '@playwright/test'

export class CasesPage {
  constructor(private readonly page: Page) {}

  async openCase(caseNumber: string) {
    await this.page.getByRole('link', { name: caseNumber }).click()
  }

  async openCaseById(caseId: string) {
    await this.page.goto(`/cases/${caseId}`)
  }

  /** ownerLabel is the picker option, e.g. "E2E Analyst (Analyst)". */
  async reassign(ownerLabel: string, reason: string) {
    await this.page.getByTestId('reassign-case-owner').selectOption({ label: ownerLabel })
    await this.page.getByTestId('reassign-case-reason').fill(reason)
    await this.page.getByTestId('reassign-case-submit').click()
  }
}

export class CustomerCasePage {
  constructor(private readonly page: Page) {}

  async openCase(priorityLabel = 'High') {
    await this.page.getByTestId('open-case-form').getByLabel('Priority').selectOption(priorityLabel)
    await this.page.getByRole('button', { name: 'Open case' }).click()
  }
}

export class CaseClosePage {
  constructor(private readonly page: Page) {}

  async close(resolutionCode: string, summary: string) {
    await this.page.getByLabel('Resolution code').fill(resolutionCode)
    await this.page.getByLabel('Closing summary').fill(summary)
    await this.page.getByRole('button', { name: 'Close case' }).click()
  }
}
