import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

import '@testing-library/jest-dom/vitest'

// Testing Library's automatic afterEach(cleanup) only registers itself when
// it detects vitest's `globals: true` mode. This config deliberately avoids
// globals (explicit imports in every test file instead), so cleanup has to
// be wired up by hand — otherwise DOM from one test leaks into the next.
afterEach(() => {
  cleanup()
})
