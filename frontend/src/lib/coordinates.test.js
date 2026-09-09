import { describe, expect, it } from 'vitest'

import { engagementOrigin, toScenePoint } from './coordinates'

describe('simulation coordinate mapping', () => {
  it('maps z-up metres to y-up kilometres', () => {
    expect(
      toScenePoint({ x: 2000, y: -1000, z: 3500 }, { x: 1000, y: 0 }),
    ).toEqual([1, 3.5, 1])
  })

  it('centres the first horizontal engagement geometry', () => {
    const origin = engagementOrigin({
      pursuer: { position_m: { x: 0, y: 200, z: 3000 } },
      target: { position_m: { x: 6000, y: 1000, z: 3200 } },
    })

    expect(origin).toEqual({ x: 3000, y: 600 })
  })
})
