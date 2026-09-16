import { describe, expect, it } from 'vitest'

import { trialAppearance } from './trialAppearance'

describe('trialAppearance', () => {
  it('makes misses stand out over hits', () => {
    const miss = trialAppearance({ success: false })
    const hit = trialAppearance({ success: true })

    expect(miss.opacity).toBeGreaterThan(hit.opacity)
    expect(hit.color).toBe('#f4f5f7')
    expect(miss.color).toBe('#ff5238')
  })
})
