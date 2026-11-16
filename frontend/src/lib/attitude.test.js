import { describe, expect, it } from 'vitest'
import { Vector3 } from 'three'

import { attitudeQuaternion, liftUp } from './attitude'

const JET_FORWARD = new Vector3(0, 0, 1)
const JET_UP = new Vector3(0, 1, 0)
const angleBetween = (a, b) => new Vector3(...a).angleTo(new Vector3(...b))
const bodyUp = (q) => JET_UP.clone().applyQuaternion(q).toArray()

describe('liftUp', () => {
  it('is level in straight flight', () => {
    expect(liftUp([240, 0, 0], [240, 0, 0], 0.04)[1]).toBeCloseTo(1)
  })

  it('banks into a hard turn, but never past about 60 degrees', () => {
    // 9 g sideways pull, scene -Z, flying along +X
    const dt = 0.04
    const up = liftUp([240, 0, -9 * 9.80665 * dt], [240, 0, 0], dt)
    const bank = angleBetween(up, [0, 1, 0])
    expect(up[2]).toBeLessThan(0) // tilts toward the centre of the turn
    expect(bank).toBeGreaterThan(0.6)
    expect(bank).toBeLessThan((60 * Math.PI) / 180)
  })

  it('stays continuous around a full loop: no frame-to-frame snap', () => {
    let previous = null
    for (let step = 0; step <= 400; step += 1) {
      const theta = (step / 400) * 2 * Math.PI
      const v = (angle) => [240 * Math.cos(angle), 240 * Math.sin(angle), 0]
      const up = liftUp(v(theta), v(theta - 0.02), 0.04)
      if (previous) expect(angleBetween(up, previous)).toBeLessThan(0.15)
      previous = up
    }
  })
})

describe('attitudeQuaternion', () => {
  // Evading targets fly along scene -Z: the exact opposite of the jet model's nose.
  // A shortest-arc rotation is unstable there and rolls the jet over for no reason.
  const dirs = (n) =>
    Array.from({ length: n }, (_, i) => {
      const yaw = (i - n / 2) * 0.004
      return [Math.sin(yaw) * 240, 0.002 * 240, -Math.cos(yaw) * 240] // passes 0.002 rad from the opposite heading
    })

  it('the old shortest-arc attitude flips near the opposite heading (what we are fixing)', () => {
    const ups = dirs(40).map((d) => bodyUp(attitudeQuaternion(JET_FORWARD, null, d, null)))
    const worst = Math.max(...ups.slice(1).map((u, i) => angleBetween(u, ups[i])))
    expect(worst).toBeGreaterThan(1)
  })

  it('level flight stays upright and smooth through that heading', () => {
    const ups = dirs(40).map((d) => bodyUp(attitudeQuaternion(JET_FORWARD, JET_UP, d, liftUp(d, d, 0.04))))
    const worst = Math.max(...ups.slice(1).map((u, i) => angleBetween(u, ups[i])))
    expect(worst).toBeLessThan(0.05)
    expect(ups[20][1]).toBeGreaterThan(0.99)
  })
})
