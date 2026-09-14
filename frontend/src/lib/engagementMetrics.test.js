import { describe, expect, it } from 'vitest'

import { engagementMetrics } from './engagementMetrics'

describe('engagementMetrics', () => {
  it('computes closing velocity and time-to-go from relative kinematics', () => {
    const metrics = engagementMetrics({
      time_s: 1,
      range_m: 1000,
      pursuer: {
        position_m: { x: 0, y: 0, z: 0 },
        velocity_m_s: { x: 700, y: 0, z: 0 },
      },
      target: {
        position_m: { x: 1000, y: 0, z: 0 },
        velocity_m_s: { x: 0, y: 0, z: 0 },
      },
    })

    expect(metrics.closingTxt).toBe('700 m/s')
    expect(metrics.tgoTxt).toBe('1.43 s')
    expect(metrics.rangeTxt).toBe('1.000 km')
  })

  it('prefers streamed achieved lateral accel for the g-load readout', () => {
    const metrics = engagementMetrics({
      time_s: 1,
      range_m: 1000,
      pursuer: {
        position_m: { x: 0, y: 0, z: 0 },
        velocity_m_s: { x: 700, y: 0, z: 0 },
      },
      target: {
        position_m: { x: 1000, y: 0, z: 0 },
        velocity_m_s: { x: 0, y: 0, z: 0 },
      },
      pursuer_accel_achieved_m_s2: { x: 0, y: 98.0665, z: 0 },
    })

    expect(metrics.gTxt).toBe('10.0 G')
  })

  it('scales g-load fraction to the scenario g-limit', () => {
    const frame = {
      time_s: 1,
      pursuer: {
        position_m: { x: 0, y: 0, z: 0 },
        velocity_m_s: { x: 700, y: 0, z: 0 },
      },
      target: {
        position_m: { x: 1000, y: 0, z: 0 },
        velocity_m_s: { x: 0, y: 0, z: 0 },
      },
      pursuer_accel_achieved_m_s2: { x: 0, y: 98.0665, z: 0 },
    }

    expect(engagementMetrics(frame).gFrac).toBeCloseTo(0.4)
    expect(engagementMetrics(frame, null, null, 10).gFrac).toBeCloseTo(1)
  })
})
