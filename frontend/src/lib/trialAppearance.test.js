import { describe, expect, it } from 'vitest'

import { trialAppearance } from './trialAppearance'

describe('trialAppearance', () => {
  it('fades early trials and highlights later successes', () => {
    const earlyMiss = trialAppearance({ success: false }, 0, 5)
    const lateHit = trialAppearance({ success: true }, 4, 5)

    expect(earlyMiss.opacity).toBeLessThan(lateHit.opacity)
    expect(lateHit.color).toBe('#7dffb3')
    expect(earlyMiss.color).toBe('#ff8aa8')
  })
})
