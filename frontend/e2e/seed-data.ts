import { readFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

export type E2ESeedData = {
  password: string
  users: Record<
    'investigator' | 'analyst' | 'team_lead',
    { id: string; email: string; role: string }
  >
  customers: {
    search: { id: string; name: string }
    openCase: { id: string; name: string }
    assignCase: { id: string; name: string }
    alert: { id: string; name: string }
  }
  transaction: {
    id: string
    counterparty: string
    amountLabel: string
  }
  caseForAssign: {
    id: string
    caseNumber: string
  }
  alert: {
    id: string
    reason: string
  }
}

const seedPath = path.join(path.dirname(fileURLToPath(import.meta.url)), '.seed-data.json')

export function loadSeedData(): E2ESeedData {
  return JSON.parse(readFileSync(seedPath, 'utf-8')) as E2ESeedData
}

export const seedData = loadSeedData()
